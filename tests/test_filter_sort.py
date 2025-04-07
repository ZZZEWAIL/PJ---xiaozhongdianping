import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from backend.main import app
from backend.models import Shop
from backend.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# 创建测试客户端
client = TestClient(app)

# 工厂函数生成 Shop 对象
def create_shop(id, name, category, rating, price_range, avg_cost):
    return Shop(
        id=id,
        name=name,
        category=category,
        rating=rating,
        price_range=price_range,
        avg_cost=avg_cost,
        address="北京市朝阳区",
        phone="1234567890",
        business_hours="10:00-22:00",
        image_url=None
    )

@pytest.fixture
def mock_db_session():
    # 使用 AsyncMock 模拟 AsyncSession
    mock_session = AsyncMock(AsyncSession)
    
    # 定义 mock_get_db，返回一个异步生成器
    async def mock_get_db():
        yield mock_session

    # 应用依赖覆盖
    app.dependency_overrides[get_db] = mock_get_db

    yield mock_session

    # 清理依赖覆盖
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_search_filter_shops(mock_db_session):
    # 模拟 execute -> scalars -> all 调用链
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [
        create_shop(1, "火锅大师", "火锅", 4.5, "￥50-100", 75.0),
        create_shop(2, "奶茶小屋", "奶茶", 4.0, "￥10-50", 20.0)
    ]
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    response = client.get("/api/shops/search?keyword=火锅&rating=4.0&avg_cost_min=20")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['name'] == "火锅大师"
    assert response.json()[1]['name'] == "奶茶小屋"

@pytest.mark.asyncio
async def test_search_filter_no_results(mock_db_session):
    # 模拟没有结果的情况
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    response = client.get("/api/shops/search?keyword=咖啡&rating=5.0&avg_cost_min=100")

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_search_filter_invalid_params(mock_db_session):
    # 测试无效参数
    response = client.get("/api/shops/search?keyword=火锅&rating=-1")

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_search_sort_shops(mock_db_session):
    # 模拟排序的情况
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [
        create_shop(1, "火锅大师", "火锅", 4.5, "￥50-100", 75.0),
        create_shop(2, "奶茶小屋", "奶茶", 4.0, "￥10-50", 20.0)
    ]
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    response = client.get("/api/shops/search?keyword=火锅&sort_by=rating&sort_order=desc")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['name'] == "火锅大师"
    assert response.json()[1]['name'] == "奶茶小屋"

@pytest.mark.asyncio
async def test_search_sort_default(mock_db_session):
    # 模拟默认排序的情况
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [
        create_shop(1, "火锅大师", "火锅", 4.5, "￥50-100", 75.0),
        create_shop(2, "奶茶小屋", "奶茶", 4.0, "￥10-50", 20.0)
    ]
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    response = client.get("/api/shops/search?keyword=火锅&sort_by=default&sort_order=desc")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]['name'] == "火锅大师"
    assert response.json()[1]['name'] == "奶茶小屋"