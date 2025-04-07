from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from backend.database import get_db
from backend.models import Shop
from backend.schema import Shop as ShopSchema

router = APIRouter()

@router.get("/shops/search", response_model=list[ShopSchema])
async def search_shops(
    keyword: str,
    category: str | None = None,
    rating: float | None = Query(None, gt=0.0, le=5.0),
    avg_cost_min: float | None = Query(None, gt=0),
    avg_cost_max: float | None = Query(None, gt=0),
    sort_by: str = Query('default', regex="^(default|rating|avg_cost)$"),
    sort_order: str = Query('desc', regex="^(asc|desc)$"),
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword cannot be empty")
    
    query = select(Shop).where(Shop.name.ilike(f"%{keyword}%") | Shop.category.ilike(f"%{keyword}%"))
    
    # 筛选条件
    filters = []
    if category:
        filters.append(Shop.category == category)
    if rating:
        filters.append(Shop.rating >= rating)
    if avg_cost_min:
        filters.append(Shop.avg_cost >= avg_cost_min)
    if avg_cost_max:
        filters.append(Shop.avg_cost <= avg_cost_max)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 排序
    if sort_by == "rating":
        query = query.order_by(Shop.rating.desc() if sort_order == "desc" else Shop.rating.asc())
    elif sort_by == "avg_cost":
        query = query.order_by(Shop.avg_cost.asc() if sort_order == "asc" else Shop.avg_cost.desc())
    else:
        query = query.order_by(Shop.id.desc() if sort_order == "desc" else Shop.id.asc())
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    shops = result.scalars().all()
    return shops

@router.get("/shops/{shop_id}", response_model=ShopSchema)
async def get_shop_details(shop_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop