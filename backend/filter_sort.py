from fastapi import APIRouter, Query, Depends
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from sqlalchemy.future import select
from backend.models import Shop  # 替换为 Shop 模型
from backend.schema import Shop as ShopSchema  # 导入 Pydantic 模型

router = APIRouter()

@router.get("/filter", response_model=list[ShopSchema])
async def filter_shops(
    rating: float = Query(None, gt=0.0, le=5.0),
    price_min: float = Query(None, gt=0),
    price_max: float = Query(None, gt=0),
    avg_spend_min: float = Query(None, gt=0),
    avg_spend_max: float = Query(None, gt=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(Shop)  # 使用 Shop 模型
    
    filters = []
    if rating:
        filters.append(Shop.rating >= rating)
    if price_min:
        # Shop 模型中没有 price 字段，使用 avg_cost 替代
        filters.append(Shop.avg_cost >= price_min)
    if price_max:
        filters.append(Shop.avg_cost <= price_max)
    if avg_spend_min:
        filters.append(Shop.avg_cost >= avg_spend_min)
    if avg_spend_max:
        filters.append(Shop.avg_cost <= avg_spend_max)

    if filters:
        query = query.filter(and_(*filters))

    result = await db.execute(query)
    shops = result.scalars().all()
    return shops

@router.get("/sort", response_model=list[ShopSchema])
async def sort_shops(
    sort_by: str = Query('default', regex="^(default|rating|avg_spend)$"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Shop)  # 使用 Shop 模型
    
    if sort_by == "rating":
        query = query.order_by(Shop.rating.desc())
    elif sort_by == "avg_spend":
        query = query.order_by(Shop.avg_cost.asc())  # avg_spend 替换为 avg_cost
    else:
        # Shop 模型中没有 created_at 字段，改为按 id 排序
        query = query.order_by(Shop.id.desc())
    
    result = await db.execute(query)
    shops = result.scalars().all()
    return shops