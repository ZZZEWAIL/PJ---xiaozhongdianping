# 测试代码 test\_review\.py

```python
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

```

## 单元测试：API 接口部分

### test\_create\_review\_success

* **输入场景**: 提交有效的点评内容到存在的商户ID（如 `/shops/1/reviews`），模拟当前用户已登录（使用 DummySession 模拟数据库会话，预设商户查询返回对象）。
* **期望结果**: 接口返回状态码 201，响应 JSON 包含新建点评的内容，与提交内容相同。
* **使用 Mock**: 利用 `DummySession` 模拟数据库 `Session`，覆盖依赖 `get_db` 返回该模拟会话；覆盖 `get_current_user` 返回虚拟用户，绕过认证。
* **断言点**:

  1. 响应 `status_code` 为 201。
  2. 响应 JSON 中的 `content` 字段等于提交的 `"Test review content"`。
  3. `DummySession` 的 `added` 属性不为空且 `committed` 为 True，表示逻辑对数据库执行了 `add` 和 `commit` 操作。
  4. `DummySession.added`（新建的 Review 对象）的 `shop_id` 等于请求路径中的商户ID 1，`user_id` 等于模拟登录用户的 ID。
  5. 响应 JSON 中包含新点评的 `id` 字段（由 DummySession.refresh 模拟赋值），并且值为预期的 100。

### test\_create\_review\_empty\_content

* **输入场景**: 提交空字符串内容的点评请求（`content` 为空），商户存在（模拟返回有效 Shop 对象）。
* **期望结果**: 接口返回状态码 400（请求无效），提示点评内容不能为空。
* **使用 Mock**: 使用 DummySession 模拟数据库会话并返回存在的商户，确保错误源于内容为空。覆盖 `get_db` 依赖，当前用户依然用虚拟用户。
* **断言点**:

  1. 响应 `status_code` 为 400。
  2. DummySession 的 `added` 仍为 None，`committed` 为 False，表示由于内容校验未通过，未对数据库执行新增或提交操作。
  3. 响应 JSON 中包含 `detail` 错误信息字段（预期其中提及内容为空的原因）。

### test\_create\_review\_shop\_not\_found

* **输入场景**: 提交有效内容的点评请求，但针对不存在的商户ID（如 `/shops/999/reviews`）。
* **期望结果**: 接口返回状态码 404，表示商户不存在。
* **使用 Mock**: DummySession 模拟数据库会话，预设商户查询结果为 None（找不到商户）。覆盖 `get_db`，模拟当前用户登录。
* **断言点**:

  1. 响应 `status_code` 为 404。
  2. DummySession 的 `added` 为 None，`committed` 为 False，表示逻辑因商户不存在直接终止，未进行数据库写操作。
  3. 响应 JSON 中 `detail` 字段包含错误信息（预期为商户不存在的提示）。

### test\_reply\_review\_success

* **输入场景**: 提交对指定点评ID的回复（如 `/reviews/5/reply`），内容有效，假设要回复的原点评存在。
* **期望结果**: 接口返回状态码 201，响应 JSON 包含新回复的内容。
* **使用 Mock**: DummySession 模拟数据库，预设查询 Review(ID=5) 返回一个虚拟父点评对象；覆盖 `get_db`，模拟当前用户已登录。
* **断言点**:

  1. 响应 `status_code` 为 201。
  2. 响应 JSON 中 `content` 等于提交的 `"Reply content"`。
  3. DummySession 记录到有新 Review 对象通过 `add` 添加，且 `commit` 已调用，表示回复已写入数据库（模拟）。
  4. 新增回复对象的 `parent_id` 等于被回复的点评ID（5），`shop_id` 等于父点评所属商户ID（如 1）。DummySession 捕获的 `added` 对象验证了这两个字段。
  5. 响应 JSON 如包含 `parent_id` 字段，则其值应为 5，验证响应结构与关联正确。

### test\_reply\_review\_empty\_content

* **输入场景**: 对存在的点评提交回复，但内容为空字符串。
* **期望结果**: 接口返回状态码 400，表示回复内容无效/为空。
* **使用 Mock**: DummySession 模拟数据库，预设父点评查询返回有效对象，以确保错误由内容为空触发；覆盖 `get_db`，使用虚拟当前用户。
* **断言点**:

  1. 响应 `status_code` 为 400。
  2. DummySession `added` 仍为 None，`committed` 为 False，说明由于回复内容不符合要求，未执行数据库新增操作。
  3. 响应 JSON 中包含 `detail` 错误说明（应指明回复内容为空的问题）。

### test\_reply\_review\_not\_found

* **输入场景**: 提交回复给不存在的点评ID（如 `/reviews/999/reply`），内容有效。
* **期望结果**: 接口返回状态码 404，表示要回复的原点评不存在。
* **使用 Mock**: DummySession 模拟数据库，预设查询 Review(ID=999) 返回 None；覆盖 `get_db` 依赖，模拟用户已登录。
* **断言点**:

  1. 响应 `status_code` 为 404。
  2. DummySession 未记录任何新增对象（`added` 为 None），且未调用 `commit`（为 False），表示逻辑在发现父点评不存在时已中止。
  3. 响应 JSON 的 `detail` 提示资源不存在（点评不存在）。

### test\_get\_reviews\_success

* **输入场景**: 获取某商户的所有点评及回复（如 `/shops/1/reviews`），假定该商户存在且有点评数据。
* **期望结果**: 接口返回状态码 200，响应 JSON 为点评列表，包括嵌套的回复列表结构。
* **使用 Mock**: DummySession 模拟数据库会话，预设商户查询返回有效对象。使用 `unittest.mock.patch` 临时替换 `build_reply_tree` 函数，使其返回预定义的嵌套结构数据（例如一个点评下有一个回复），以隔离测试逻辑。
* **断言点**:

  1. 响应 `status_code` 为 200。
  2. 响应 JSON 数据类型为列表（`list`），长度符合预期（测试中预期1个点评）。
  3. 校验返回的第一个点评的字段：`id` 应为预设的 1，`content` 匹配预设内容 `"Review1"`。
  4. 该点评包含 `replies` 字段且类型为列表，长度为 1，表示有一条回复。
  5. 回复项的内容结构正确：`id` 为预设的 2，`content` 为 `"Reply1"`，且其 `replies` 为空列表（长度 0，表示没有下级回复）。
  6. 确认 `build_reply_tree` 在请求处理中被调用一次（通过 `mocked_build.assert_called_once()`），确保业务逻辑按预期构建了回复树。

### test\_get\_reviews\_shop\_not\_found

* **输入场景**: 获取不存在商户ID的点评列表（如 `/shops/999/reviews`）。
* **期望结果**: 接口返回状态码 404，表示商户不存在，请求无法处理。
* **使用 Mock**: DummySession 模拟数据库会话，预设商户查询返回 None；使用 `patch` 替换 `build_reply_tree` 来监控其调用（不需要实际返回值，因为不应被调用）。
* **断言点**:

  1. 响应 `status_code` 为 404。
  2. 响应 JSON 中包含 `detail` 字段提示商户不存在。
  3. 确认 `build_reply_tree` **未被调用**（`assert_not_called`），表示业务逻辑在发现商户不存在后直接返回404，没有继续查询点评或构建回复结构。

## 单元测试：业务逻辑函数部分

### test\_get\_shop\_by\_id\_found

* **测试场景**: 调用 `get_shop_by_id(session, 1)`，模拟数据库 Session 在查询 ID=1 时找到商户对象。
* **期望结果**: 函数返回对应的商户对象。
* **使用 Mock**: 使用 `MagicMock` 模拟 `session` 对象，将其 `query().filter().first()` 方法链配置为返回预设的 `dummy_shop` 对象。
* **断言点**:

  1. 函数返回值即为预设的 `dummy_shop`，与模拟查询结果一致。
  2. 验证 `session.query` 被正确调用了一次，且参数是商户模型 `Shop`；`filter` 和 `first` 方法也各被调用一次。这确保函数按预期构造并执行了数据库查询。

### test\_get\_shop\_by\_id\_not\_found

* **测试场景**: 调用 `get_shop_by_id(session, 999)`，模拟数据库查询无结果返回。
* **期望结果**: 函数返回 None，表示找不到商户。
* **使用 Mock**: 同样使用 MagicMock 模拟 Session，将 `first()` 返回值设为 None。
* **断言点**:

  1. 函数返回值为 None，符合未查询到商户的预期。
  2. 验证 `session.query` 对 `Shop` 的调用及后续 `filter`、`first` 方法各调用一次，确保查询逻辑正确执行。

### test\_create\_review\_logic\_success

* **测试场景**: 调用业务逻辑函数 `create_review(session, user, shop, content)` 创建新点评（顶级点评，没有父节点）。
* **期望结果**: 函数返回新创建的 Review 对象，内容和关联正确设置，并已提交保存。
* **使用 Mock**: 使用 DummySession 模拟 Session，以捕获对数据库的调用；提供虚拟的 User 和 Shop 对象作为参数。
* **断言点**:

  1. 函数调用后 DummySession 的 `committed` 为 True，`added` 不为空，表示函数执行了 `session.add` 和 `session.commit`。
  2. 返回的 Review 对象的 `content` 属性等于传入的 `"Logic test review"`。
  3. 返回对象的 `shop_id` 或其 `shop` 属性的 id 等于传入的商户对象 ID，`user_id` 或 `user` 属性的 id 等于传入用户对象 ID，确保外键关联正确。
  4. 返回的 Review 对象具有 `id` 属性（DummySession.refresh 模拟赋值），且值为 100，表示逻辑刷新了新对象的 ID。

### test\_create\_review\_logic\_with\_parent

* **测试场景**: 调用 `create_review(session, user, shop, content, parent=parent_review)` 创建一条针对已有点评的回复（带父节点）。
* **期望结果**: 函数返回新创建的回复 Review 对象，其内容正确，父关联建立，已提交保存。
* **使用 Mock**: DummySession 模拟数据库 Session，提供虚拟 User、Shop，以及一个已有的父 Review 对象作为参数。
* **断言点**:

  1. 函数执行后 DummySession 的 `committed` 为 True，表示进行了提交操作，新回复已写入（模拟）。
  2. 返回的回复对象存在且 DummySession `added` 非空，指向该对象。
  3. 返回回复的 `content` 等于传入的 `"Reply via logic"`。
  4. 父子关系正确：如果模型有 `parent_id` 字段，则新回复的 `parent_id` 等于父点评的 ID；如果通过关系属性设置，则新回复对象的 `parent` 引用即为传入的父对象（本测试用 `hasattr` 判断并分别断言）。
  5. 新回复的 `shop_id` 与传入商户 ID 一致，`user_id` 与传入用户 ID 一致，确保回复归属正确。
  6. 新回复对象应已分配 `id`（DummySession.refresh 模拟），预期为 100。

### test\_build\_reply\_tree\_no\_replies

* **测试场景**: 调用 `build_reply_tree(reviews)` 方法，传入一个只有单条点评且无任何回复的列表。
* **期望结果**: 返回的结果列表应与输入相同（只有该点评），并且由于没有子回复，该点评的回复列表应为空。
* **使用 Mock**: 不涉及外部依赖，直接使用构造的 DummyReviewObj 列表作为输入。
* **断言点**:

  1. 函数返回列表长度为 1，与输入点评数一致。
  2. 返回的唯一元素 `id` 应为 1（与输入点评的 id 相同）。
  3. 因没有子回复，该元素应没有任何子节点：如果函数实现为给每个点评添加 `replies` 属性，则此属性应存在且长度为 0；如未添加该属性（无子回复不创建列表），也视为符合预期。

### test\_build\_reply\_tree\_nested

* **测试场景**: 调用 `build_reply_tree(reviews)` 构建多层嵌套的回复树。传入的列表包含一条根点评以及多条嵌套回复：

  * `id=1` 为根点评；
  * `id=2` 和 `id=3` 的点评以 `parent_id=1` 表示是对根点评的回复；
  * `id=4` 的点评以 `parent_id=2` 表示是对编号2点评的二级回复。
* **期望结果**: 函数返回仅包含根点评的列表结构，根点评的 `replies` 列表下包含两个回复（ID 2 和 3），其中 ID 2 的回复对象下再嵌套一个子回复（ID 4），ID 3 无子回复。
* **使用 Mock**: 无需外部依赖，直接使用 DummyReviewObj 构造模拟数据列表。
* **断言点**:

  1. 返回列表长度为 1，只包含根节点点评（id=1）。
  2. 根点评对象有 `replies` 属性，列表长度为 2，对应两个一级回复。
  3. 验证一级回复顺序和内容：`replies[0].id == 2`, `replies[1].id == 3`，与输入列表中顺序一致。
  4. 对于 `id=2` 的回复对象，存在 `replies` 属性且长度为 1，里面的唯一元素 `id == 4`（正确挂载了二级回复）。
  5. 对于 `id=3` 的回复对象，如存在 `replies` 属性则其长度为 0，表示没有子回复（若函数对无子回复未创建该属性也可接受）。

## 集成测试：完整流程验证

### test\_integration\_full\_flow

* **测试场景**: 在一个内存 SQLite 数据库上模拟完整使用流程：

  1. **注册**新用户；
  2. **登录**获取认证 Token；
  3. **创建商户**条目；
  4. **创建点评**（针对该商户的评论）；
  5. **回复点评**（对刚创建的点评发表两条回复）；
  6. **获取商户所有点评及回复**，验证最终结构。
* **环境配置**: 集成测试使用 `setUpClass` 建立内存数据库，并通过 `app.dependency_overrides` 覆盖 `get_db` 依赖为该测试数据库会话；不使用用户依赖覆盖，以真实认证流程获取 token。
* **期望结果**: 每个步骤均返回成功状态码，其输出内容和关系符合预期。
* **断言点**:

  1. **注册**: POST `/register` 返回 200或201（成功创建）。本测试仅验证状态码为成功，不深入检查返回内容（假定注册接口返回新用户信息或成功消息）。
  2. **登录**: POST `/login` 返回 200，响应包含 `access_token` 字段及 `token_type=="bearer"`。提取该令牌用于后续授权。
  3. **创建商户**: POST `/shops`（携带认证头）返回 200或201，响应 JSON 包含新建商户的 `id` 字段以及提交的名称等信息。断言返回商户名称与提交一致，记录商户ID供后续使用。
  4. **创建点评**: POST `/shops/{shop_id}/reviews` 返回 200或201，响应 JSON 中 `content` 等于提交内容 `"This shop is great!"`。如响应包含 `shop_id` 字段，则应等于前一步创建的商户ID，确保点评关联正确。记录点评ID。
  5. **回复点评**: 连续两次 POST `/reviews/{review_id}/reply` 提交不同内容的回复，均应返回 200或201。断言每次响应的 `content` 分别为提交的 `"Absolutely agree!"` 和 `"Another perspective."`。如响应包含 `parent_id` 字段，则应等于所回复的点评ID。记录两条回复的 ID。
  6. **获取全部点评**: GET `/shops/{shop_id}/reviews` 返回 200，响应为该商户的点评列表（JSON 数组）。断言仅有一条顶级点评（我们创建的点评），其内容和 ID 与之前一致。

     * 顶级点评对象包含 `replies` 列表字段。
     * `replies` 列表长度为 2，对应我们发布的两条回复。检查回复列表顺序与发布顺序一致（假设按时间先后排列，先发布的回复应排在前）。
     * 验证回复内容和 ID：第一条回复 `id == reply_id1` 且 `content` 为 `"Absolutely agree!"`，第二条 `id == reply_id2` 且 `content` 为 `"Another perspective."`。
     * 每条回复对象都包含自己的 `replies` 字段且为空列表（长度为0），表示没有进一步的嵌套回复。
  7. **字段类型验证**: 进一步检查返回 JSON 结构中关键字段类型正确：

     * 点评和回复的 `id` 应为整数类型；
     * `content` 为字符串类型；
     * `replies` 为列表类型（顶级点评的 replies 和每个回复对象的 replies 均应是列表，即使为空）。
* **综合验证**: 该集成测试贯穿整个应用流程，在真实数据库环境中验证了各接口的交互和数据联动，确保最终获取的嵌套回复结构与预期一致。
