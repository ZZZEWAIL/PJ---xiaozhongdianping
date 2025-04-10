from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from backend.database import get_db
from backend.models import Shop, SearchHistory, ShopImage
from backend.schema import Shop as ShopSchema
from datetime import datetime


router = APIRouter()

@router.get("/shops/search", response_model=list[ShopSchema])
async def search_shops(
    keyword: str,
    categories: list[str] = Query(None),  # 支持多选类别
    ratings: list[float] = Query(None),  # 支持多选评分
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
    # 记录搜索历史
    new_history = SearchHistory(keyword=keyword)
    db.add(new_history)
    await db.commit()

    # 初始化查询
    query = select(Shop).where(Shop.name.ilike(f"%{keyword}%") | Shop.category.ilike(f"%{keyword}%"))

    # 初始化筛选条件
    filters = []

    # 处理类别筛选（支持单选和多选）
    if categories:
        filters.append(Shop.category.in_(categories))
    elif category:
        filters.append(Shop.category == category)

    # 处理评分筛选（支持单选和多选）
    if ratings:
        filters.append(Shop.rating.in_(ratings))
    elif rating:
        filters.append(Shop.rating >= rating)

    # 处理人均消费筛选
    if avg_cost_min:
        filters.append(Shop.avg_cost >= avg_cost_min)
    if avg_cost_max:
        filters.append(Shop.avg_cost <= avg_cost_max)

    # 应用筛选条件
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

@router.get("/shops/search/history", response_model=list[str])
async def get_search_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchHistory.keyword).order_by(SearchHistory.searched_at.desc()))
    history = result.scalars().all()
    return history

@router.get("/shops/{shop_id}", response_model=ShopSchema)
async def get_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.id == shop_id))
    shop = result.scalar()
    if not shop:
        raise HTTPException(status_code=404, detail="商家未找到")
    
    # 获取该商家的所有图片
    images_result = await db.execute(select(ShopImage).where(ShopImage.shop_id == shop_id))
    images = images_result.scalars().all()
    image_urls = [image.image_url for image in images]
    shop.image_urls = image_urls  # 假设 ShopSchema 中添加了 image_urls 字段
    return shop