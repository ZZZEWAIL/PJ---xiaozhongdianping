import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from backend.main import app
from backend.models import Business
from sqlalchemy.ext.asyncio import AsyncSession

# 创建一个测试客户端
client = TestClient(app)

# Mock 数据库会话和查询
@pytest.fixture
def mock_db_session():
    # 创建一个 MagicMock 对象作为数据库会话
    mock_session = MagicMock(AsyncSession)
    yield mock_session
    mock_session.close()

# 测试：正常的筛选请求
@pytest.mark.asyncio
async def test_filter_businesses(mock_db_session):
    # 模拟数据库查询的返回值
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
        Business(id=1, name="Restaurant A", rating=4.5, price=30, avg_spend=50),
        Business(id=2, name="Restaurant B", rating=4.0, price=20, avg_spend=40)
    ]

    # 发送请求到 API
    response = client.get("/business/filter?rating=4.0&price_min=20")

    # 断言返回的状态码和数据
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['name'] == "Restaurant A"
    assert response.json()[1]['name'] == "Restaurant B"

# 测试：筛选请求中没有符合条件的商家
@pytest.mark.asyncio
async def test_filter_no_results(mock_db_session):
    # 模拟数据库查询的返回值为空
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

    # 发送请求到 API
    response = client.get("/business/filter?rating=5.0&price_min=100")

    # 断言返回的状态码和空数据
    assert response.status_code == 200
    assert response.json() == []

# 测试：异常的筛选请求（传入无效的价格范围）
@pytest.mark.asyncio
async def test_filter_invalid_price_range(mock_db_session):
    # 发送请求到 API，传入不合理的价格范围
    response = client.get("/business/filter?price_min=-10&price_max=-5")

    # 断言返回的状态码
    assert response.status_code == 422  # FastAPI 会返回 422 错误（验证错误）

# 测试：正常的排序请求
@pytest.mark.asyncio
async def test_sort_businesses(mock_db_session):
    # 模拟数据库查询的返回值
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
        Business(id=1, name="Restaurant A", rating=4.5, price=30, avg_spend=50),
        Business(id=2, name="Restaurant B", rating=4.0, price=20, avg_spend=40)
    ]

    # 发送请求到 API，按评分排序
    response = client.get("/business/sort?sort_by=rating")

    # 断言返回的状态码和数据
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['name'] == "Restaurant A"
    assert response.json()[1]['name'] == "Restaurant B"

# 测试：默认排序请求
@pytest.mark.asyncio
async def test_sort_default(mock_db_session):
    # 模拟数据库查询的返回值
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
        Business(id=1, name="Restaurant A", rating=4.5, price=30, avg_spend=50),
        Business(id=2, name="Restaurant B", rating=4.0, price=20, avg_spend=40)
    ]

    # 发送请求到 API，使用默认排序（按创建时间）
    response = client.get("/business/sort?sort_by=default")

    # 断言返回的状态码和数据
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['name'] == "Restaurant A"
    assert response.json()[1]['name'] == "Restaurant B"
