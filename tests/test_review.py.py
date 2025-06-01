import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from models import Shop, Review, User
import review
from review import create_review, build_reply_tree
from shops import get_shop_by_id
from database import get_db
from utils import get_current_user

# 虚拟会话类，用于模拟数据库操作以进行单元测试
class DummySession:
    def __init__(self):
        self.added = None
        self.committed = False
        self.model = None
        # 查询的预期结果
        self.expected_shop = None
        self.expected_review = None
        self.expected_reviews_list = None

    def query(self, model):
        # 记录正在查询的模型并返回自身以便链式调用
        self.model = model
        return self

    def filter(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        # 根据模型类型返回预设结果
        if self.model == Shop:
            return self.expected_shop
        if self.model == Review:
            return self.expected_review
        return None

    def all(self):
        if self.model == Review:
            # 返回预设的评论列表，如果未设置则返回空列表
            return self.expected_reviews_list if self.expected_reviews_list is not None else []
        return []

    def add(self, obj):
        # 捕获添加到会话的对象
        self.added = obj

    def commit(self):
        # 标记已调用提交
        self.committed = True

    def refresh(self, obj):
        # 模拟在提交后为对象分配 ID
        if hasattr(obj, "id") and obj.id is None:
            obj.id = 100

# 用于测试回复树逻辑的虚拟评论对象
class DummyReviewObj:
    def __init__(self, id, parent_id=None, content=""):
        self.id = id
        self.parent_id = parent_id
        self.content = content

class TestReviewAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 为所有 API 测试设置一个虚拟的当前用户
        cls.dummy_user = User(id=1, username="testuser")
        app.dependency_overrides[get_current_user] = lambda: cls.dummy_user

    def tearDown(self):
        # 在每个测试后移除数据库覆盖，以避免测试之间的干扰
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]

    def test_create_review_success(self):
        # 模拟向现有商店发布评论
        dummy_shop = Shop(id=1, name="Dummy Shop")
        dummy_session = DummySession()
        dummy_session.expected_shop = dummy_shop  # 商店存在
        # 覆盖 get_db 以使用虚拟会话
        def override_get_db():
            yield dummy_session
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        payload = {"content": "Test review content"}
        response = client.post("/shops/1/reviews", json=payload)
        # 期望 201 创建，并返回评论内容
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["content"], "Test review content")
        # 验证会话中已添加并提交了评论
        self.assertIsNotNone(dummy_session.added)
        self.assertTrue(dummy_session.committed)
        # 添加的评论应具有正确的 shop_id 和 user_id
        self.assertEqual(getattr(dummy_session.added, "shop_id", None), 1)
        self.assertEqual(getattr(dummy_session.added, "user_id", None), self.dummy_user.id)
        # 响应应包含由 DummySession.refresh 设置的新评论 ID
        self.assertIn("id", data)
        self.assertEqual(data["id"], 100)

    def test_create_review_empty_content(self):
        # 模拟发布为空内容的评论
        dummy_shop = Shop(id=1, name="Dummy Shop")
        dummy_session = DummySession()
        dummy_session.expected_shop = dummy_shop  # 商店存在，因此只有内容验证失败
        def override_get_db():
            yield dummy_session
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        payload = {"content": ""}  # 空内容
        response = client.post("/shops/1/reviews", json=payload)
        # 期望 400 错误请求，因为内容为空
        self.assertEqual(response.status_code, 400)
        data = response.json()
        # 不应添加或提交任何评论
        self.assertIsNone(dummy_session.added)
        self.assertFalse(dummy_session.committed)
        # 错误详情应指示内容问题
        self.assertIn("detail", data)

    def test_create_review_shop_not_found(self):
        # 模拟向不存在的商店发布评论
        dummy_session = DummySession()
        dummy_session.expected_shop = None  # 未找到商店
        def override_get_db():
            yield dummy_session
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        payload = {"content": "Valid content"}
        response = client.post("/shops/999/reviews", json=payload)
        # 当商店不存在时，期望 404 未找到
        self.assertEqual(response.status_code, 404)
        data = response.json()
        # 未添加或提交评论
        self.assertIsNone(dummy_session.added)
        self.assertFalse(dummy_session.committed)
        self.assertIn("detail", data)

    def test_reply_review_success(self):
        # 模拟回复现有评论
        dummy_parent = Review(id=5, content="Parent review", shop_id=1, user_id=2)
        dummy_session = DummySession()
        dummy_session.expected_review = dummy_parent  # 父级评论存在
        def override_get_db():
            yield dummy_session
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        payload = {"content": "Reply content"}
        response = client.post("/reviews/5/reply", json=payload)
        # 期望 201 创建，并返回回复内容
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["content"], "Reply content")
        # 应添加并提交新的回复
        self.assertIsNotNone(dummy_session.added)
        self.assertTrue(dummy_session.committed)
        # 新回复的 parent_id 应为目标评论的 ID
        self.assertEqual(getattr(dummy_session.added, "parent_id", None), 5)
        # 新回复的 shop_id 应与父级评论的 shop_id 匹配
        self.assertEqual(getattr(dummy_session.added, "shop_id", None), 1)
        # 如果响应包含 parent_id，则应与 5 匹配
        if "parent_id" in data:
            self.assertEqual(data["parent_id"], 5)

    def test_reply_review_empty_content(self):
        # 模拟向现有评论回复空内容
        dummy_parent = Review(id=5, content="Parent review", shop_id=1, user_id=2)
        dummy_session = DummySession()
        dummy_session.expected_review = dummy_parent  # 父级存在
        def override_get_db():
            yield dummy_session
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        payload = {"content": ""}  # 空回复内容
        response = client.post("/reviews/5/reply", json=payload)
        # 期望 400 错误请求，因为回复内容为空
        self.assertEqual(response.status_code, 400)
        data = response.json()
        # 未添加或提交回复
        self.assertIsNone(dummy_session.added)
        self.assertFalse(dummy_session.committed)
        self.assertIn("detail", data)

    def test_reply_review_not_found(self):
        # 模拟回复不存在的评论
        dummy_session = DummySession()
        dummy_session.expected_review = None  # 未找到父级评论
        def override_get_db():
            yield dummy_session
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        payload = {"content": "Some reply"}
        response = client.post("/reviews/999/reply", json=payload)
        # 当父级评论不存在时，期望 404 未找到
        self.assertEqual(response.status_code, 404)
        data = response.json()
        # 未添加或提交回复
        self.assertIsNone(dummy_session.added)
        self.assertFalse(dummy_session.committed)
        self.assertIn("detail", data)

    def test_get_reviews_success(self):
        # 模拟为具有现有评论和回复的商店获取评论
        dummy_shop = Shop(id=1, name="Dummy Shop")
        dummy_session = DummySession()
        dummy_session.expected_shop = dummy_shop
        dummy_session.expected_reviews_list = []  # 我们将覆盖树构建
        # 修补 build_reply_tree 以返回预设的嵌套结构
        with patch.object(review, 'build_reply_tree', return_value=[
            {"id": 1, "content": "Review1", "replies": [
                {"id": 2, "content": "Reply1", "replies": []}
            ]}
        ]) as mocked_build:
            def override_get_db():
                yield dummy_session
            app.dependency_overrides[get_db] = override_get_db

            client = TestClient(app)
            response = client.get("/shops/1/reviews")
            # 期望 200 OK 并返回嵌套的评论数据
            self.assertEqual(response.status_code, 200)
            data = response.json()
            # 验证返回数据的结构
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], 1)
            self.assertIn("replies", data[0])
            self.assertEqual(len(data[0]["replies"]), 1)
            self.assertEqual(data[0]["replies"][0]["id"], 2)
            self.assertEqual(data[0]["replies"][0]["content"], "Reply1")
            self.assertIsInstance(data[0]["replies"][0]["replies"], list)
            self.assertEqual(len(data[0]["replies"][0]["replies"]), 0)
            # 确保我们的修补 build_reply_tree 被调用一次
            mocked_build.assert_called_once()

    def test_get_reviews_shop_not_found(self):
        # 模拟为不存在的商店获取评论
        dummy_session = DummySession()
        dummy_session.expected_shop = None
        with patch.object(review, 'build_reply_tree') as mocked_build:
            def override_get_db():
                yield dummy_session
            app.dependency_overrides[get_db] = override_get_db

            client = TestClient(app)
            response = client.get("/shops/999/reviews")
            # 期望 404 未找到
            self.assertEqual(response.status_code, 404)
            data = response.json()
            self.assertIn("detail", data)
            # 当未找到商店时，不应调用 build_reply_tree
            mocked_build.assert_not_called()

class TestReviewLogic(unittest.TestCase):
    def test_get_shop_by_id_found(self):
        # 模拟 get_shop_by_id，当数据库中存在商店时
        dummy_shop = Shop(id=1, name="Dummy Shop")
        session = MagicMock()
        # 配置 session.query().filter().first() 链以返回 dummy_shop
        dummy_query = MagicMock()
        session.query.return_value = dummy_query
        dummy_query.filter.return_value = dummy_query
        dummy_query.first.return_value = dummy_shop

        result = get_shop_by_id(session, 1)
        # 期望获得 dummy_shop 对象
        self.assertIs(result, dummy_shop)
        # 验证查询是否正确调用
        session.query.assert_called_once_with(Shop)
        dummy_query.filter.assert_called_once()
        dummy_query.first.assert_called_once()

    def test_get_shop_by_id_not_found(self):
        # 模拟 get_shop_by_id，当未找到商店时
        session = MagicMock()
        dummy_query = MagicMock()
        session.query.return_value = dummy_query
        dummy_query.filter.return_value = dummy_query
        dummy_query.first.return_value = None

        result = get_shop_by_id(session, 999)
        # 当未找到商店时，期望返回 None
        self.assertIsNone(result)
        session.query.assert_called_once_with(Shop)
        dummy_query.filter.assert_called_once()
        dummy_query.first.assert_called_once()

    def test_create_review_logic_success(self):
        # 测试在没有父级的情况下创建新评论（逻辑函数）
        dummy_user = User(id=1, username="tester")
        dummy_shop = Shop(id=1, name="Dummy Shop")
        session = DummySession()
        content = "Logic test review"
        new_review = create_review(session, dummy_user, dummy_shop, content)
        # 会话应记录添加和提交操作
        self.assertTrue(session.committed)
        self.assertIsNotNone(session.added)
        # 返回的评论应具有正确的内容和关联
        self.assertEqual(new_review.content, content)
        self.assertEqual(getattr(new_review, "shop_id", None) or getattr(new_review, "shop", None).id, dummy_shop.id)
        self.assertEqual(getattr(new_review, "user_id", None) or getattr(new_review, "user", None).id, dummy_user.id)
        # 新评论应获得分配的 ID
        self.assertIsNotNone(new_review.id)
        self.assertEqual(new_review.id, 100)

    def test_create_review_logic_with_parent(self):
        # 测试创建具有父级（回复）的评论逻辑
        dummy_user = User(id=2, username="replyer")
        dummy_shop = Shop(id=1, name="Dummy Shop")
        parent_review = Review(id=50, content="Parent", shop_id=dummy_shop.id, user_id=1)
        session = DummySession()
        content = "Reply via logic"
        new_reply = create_review(session, dummy_user, dummy_shop, content, parent=parent_review)
        # 应已添加并提交回复
        self.assertTrue(session.committed)
        self.assertIsNotNone(session.added)
        # 检查内容和父级关联
        self.assertEqual(new_reply.content, content)
        if hasattr(new_reply, "parent_id"):
            self.assertEqual(new_reply.parent_id, parent_review.id)
        else:
            # 如果使用关系，则应设置 parent
            self.assertIs(new_reply.parent, parent_review)
        # 商店和用户应正确关联
        self.assertEqual(getattr(new_reply, "shop_id", None) or getattr(new_reply, "shop", None).id, dummy_shop.id)
        self.assertEqual(getattr(new_reply, "user_id", None) or getattr(new_reply, "user", None).id, dummy_user.id)
        # 刷新后新回复应具有 ID
        self.assertIsNotNone(new_reply.id)
        self.assertEqual(new_reply.id, 100)

    def test_build_reply_tree_no_replies(self):
        # 测试使用单个评论构建回复树（无回复）
        reviews = [DummyReviewObj(id=1, parent_id=None, content="Solo review")]
        result = build_reply_tree(reviews)
        # 应将单个评论作为顶级返回
        self.assertEqual(len(result), 1)
        top_review = result[0]
        self.assertEqual(top_review.id, 1)
        # 如果没有回复，则 'replies' 属性应为空或未设置
        if hasattr(top_review, "replies"):
            self.assertEqual(len(top_review.replies), 0)

    def test_build_reply_tree_nested(self):
        # 测试使用嵌套回复构建回复树
        r1 = DummyReviewObj(id=1, parent_id=None, content="Root")
        r2 = DummyReviewObj(id=2, parent_id=1, content="Child1")
        r3 = DummyReviewObj(id=3, parent_id=1, content="Child2")
        r4 = DummyReviewObj(id=4, parent_id=2, content="Grandchild")
        reviews = [r1, r2, r3, r4]
        result = build_reply_tree(reviews)
        # 只有一个顶级根
        self.assertEqual(len(result), 1)
        root = result[0]
        self.assertEqual(root.id, 1)
        # 根应有两个直接回复（ID 为 2 和 3）
        self.assertTrue(hasattr(root, "replies"))
        self.assertEqual(len(root.replies), 2)
        self.assertEqual(root.replies[0].id, 2)
        self.assertEqual(root.replies[1].id, 3)
        # ID=2 的回复应有一个子级（ID 为 4）
        child2 = root.replies[0]
        self.assertTrue(hasattr(child2, "replies"))
        self.assertEqual(len(child2.replies), 1)
        self.assertEqual(child2.replies[0].id, 4)
        # ID=3 的回复不应有子级
        child3 = root.replies[1]
        if hasattr(child3, "replies"):
            self.assertEqual(len(child3.replies), 0)

class TestReviewIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 清除任何依赖覆盖（特别是 get_current_user）
        app.dependency_overrides.pop(get_current_user, None)
        # 为集成测试设置内存 SQLite
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(bind=engine)
        from database import Base
        Base.metadata.create_all(engine)
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    def test_integration_full_flow(self):
        # 1. 注册新用户
        register_data = {"username": "integration_user", "password": "pass123", "email": "user@example.com"}
        res = self.client.post("/register", json=register_data)
        self.assertIn(res.status_code, (200, 201))
        # 2. 登录以获取令牌
        login_data = {"username": "integration_user", "password": "pass123"}
        res = self.client.post("/login", data=login_data)
        self.assertEqual(res.status_code, 200)
        login_resp = res.json()
        self.assertIn("access_token", login_resp)
        token = login_resp["access_token"]
        self.assertEqual(login_resp.get("token_type"), "bearer")
        headers = {"Authorization": f"Bearer {token}"}
        # 3. 创建新商店
        shop_data = {"name": "Integration Test Shop"}
        res = self.client.post("/shops", json=shop_data, headers=headers)
        self.assertIn(res.status_code, (200, 201))
        shop_resp = res.json()
        self.assertIn("id", shop_resp)
        shop_id = shop_resp["id"]
        self.assertEqual(shop_resp["name"], "Integration Test Shop")
        # 4. 为商店创建评论
        review_data = {"content": "This shop is great!"}
        res = self.client.post(f"/shops/{shop_id}/reviews", json=review_data, headers=headers)
        self.assertIn(res.status_code, (200, 201))
        review_resp = res.json()
        self.assertEqual(review_resp["content"], "This shop is great!")
        # 评论应关联到正确的商店
        if "shop_id" in review_resp:
            self.assertEqual(review_resp["shop_id"], shop_id)
        review_id = review_resp["id"]
        # 5. 向评论发布两个回复
        reply_data1 = {"content": "Absolutely agree!"}
        res = self.client.post(f"/reviews/{review_id}/reply", json=reply_data1, headers=headers)
        self.assertIn(res.status_code, (200, 201))
        reply1_resp = res.json()
        self.assertEqual(reply1_resp["content"], "Absolutely agree!")
        if "parent_id" in reply1_resp:
            self.assertEqual(reply1_resp["parent_id"], review_id)
        reply_id1 = reply1_resp["id"]
        reply_data2 = {"content": "Another perspective."}
        res = self.client.post(f"/reviews/{review_id}/reply", json=reply_data2, headers=headers)
        self.assertIn(res.status_code, (200, 201))
        reply2_resp = res.json()
        self.assertEqual(reply2_resp["content"], "Another perspective.")
        if "parent_id" in reply2_resp:
            self.assertEqual(reply2_resp["parent_id"], review_id)
        reply_id2 = reply2_resp["id"]
        # 6. 获取商店的所有评论（应包括评论及其回复）
        res = self.client.get(f"/shops/{shop_id}/reviews", headers=headers)
        self.assertEqual(res.status_code, 200)
        reviews_list = res.json()
        # 一个顶级评论（创建的那个）
        self.assertEqual(len(reviews_list), 1)
        top_review = reviews_list[0]
        self.assertEqual(top_review["id"], review_id)
        self.assertEqual(top_review["content"], "This shop is great!")
        # 验证回复列表和嵌套结构
        self.assertIn("replies", top_review)
        self.assertIsInstance(top_review["replies"], list)
        # 应该有两个回复
        self.assertEqual(len(top_review["replies"]), 2)
        first_reply = top_review["replies"][0]
        second_reply = top_review["replies"][1]
        self.assertEqual(first_reply["id"], reply_id1)
        self.assertEqual(first_reply["content"], "Absolutely agree!")
        self.assertEqual(second_reply["id"], reply_id2)
        self.assertEqual(second_reply["content"], "Another perspective.")
        # 每个回复应具有空的 replies 列表（没有进一步的嵌套回复）
        self.assertIn("replies", first_reply)
        self.assertEqual(len(first_reply["replies"]), 0)
        self.assertIn("replies", second_reply)
        self.assertEqual(len(second_reply["replies"]), 0)
        # 检查字段类型
        self.assertIsInstance(top_review["id"], int)
        self.assertIsInstance(top_review["content"], str)
        self.assertIsInstance(top_review["replies"], list)
        self.assertIsInstance(first_reply["id"], int)
        self.assertIsInstance(first_reply["content"], str)
        self.assertIsInstance(first_reply["replies"], list)
        self.assertIsInstance(second_reply["id"], int)
        self.assertIsInstance(second_reply["content"], str)
        self.assertIsInstance(second_reply["replies"], list)
