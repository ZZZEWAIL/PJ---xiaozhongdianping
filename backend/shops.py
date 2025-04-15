from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from backend.database import get_db
from backend.models import Shop, SearchHistory, ShopImage
from backend.schema import Shop as ShopSchema
from datetime import datetime
from sqlalchemy import delete

router = APIRouter()

@router.get("/shops/search")
async def search_shops(
    keyword: str,
    categories: list[str] = Query(None),
    ratings: list[float] = Query(None),
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
    # 检查是否已存在相同的搜索历史
    existing_history = await db.execute(
        select(SearchHistory).where(SearchHistory.keyword == keyword)
    )
    existing_history = existing_history.scalars().first()

    if existing_history:
        existing_history.searched_at = datetime.utcnow()
        await db.commit()
    else:
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

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 排序
    if sort_by == "rating":
        query = query.order_by(Shop.rating.desc() if sort_order == "desc" else Shop.rating.asc())
    elif sort_by == "avg_cost":
        query = query.order_by(Shop.avg_cost.desc() if sort_order == "desc" else Shop.avg_cost.asc())
    else:
        query = query.order_by(Shop.id.desc() if sort_order == "desc" else Shop.id.asc())

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    shops = result.scalars().all()

    # 返回分页数据
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": shops
    }

@router.get("/shops/search/history", response_model=list[str])
async def get_search_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchHistory.keyword).order_by(SearchHistory.searched_at.desc()))
    history = result.scalars().all()
    return history

@router.delete("/shops/search/history")
async def clear_search_history(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(SearchHistory))
    await db.commit()
    return {"message": "Search history cleared"}