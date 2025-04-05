from fastapi import APIRouter, Query, Depends
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from sqlalchemy.future import select
from backend.models import Business  # 假设我们有一个Business模型来存储商家信息(简单建立了一个)

router = APIRouter()

@router.get("/filter")
async def filter_businesses(
    rating: float = Query(None, gt=0.0, le=5.0),  # 用户评分，默认为None，且评分范围0-5
    price_min: float = Query(None, gt=0),  # 用户选择的最低价格
    price_max: float = Query(None, gt=0),  # 用户选择的最高价格
    avg_spend_min: float = Query(None, gt=0),  # 用户选择的最低人均消费
    avg_spend_max: float = Query(None, gt=0),  # 用户选择的最高人均消费
    db: AsyncSession = Depends(get_db)
):
    query = select(Business)  # 初始查询，选择所有商家
    
    filters = []  # 存放筛选条件
    if rating:
        filters.append(Business.rating >= rating)  # 根据评分进行筛选
    if price_min:
        filters.append(Business.price >= price_min)  # 根据最低价格进行筛选
    if price_max:
        filters.append(Business.price <= price_max)  # 根据最高价格进行筛选
    if avg_spend_min:
        filters.append(Business.avg_spend >= avg_spend_min)  # 根据最低人均消费进行筛选
    if avg_spend_max:
        filters.append(Business.avg_spend <= avg_spend_max)  # 根据最高人均消费进行筛选

    if filters:  # 如果有筛选条件，则添加到查询中
        query = query.filter(and_(*filters))

    result = await db.execute(query)  # 执行查询
    businesses = result.scalars().all()  # 获取查询结果

    return businesses  # 返回商家列表

@router.get("/sort")
async def sort_businesses(
    sort_by: str = Query('default', regex="^(default|rating|avg_spend)$"),  # 默认按时间排序，其他选项为评分和人均消费
    db: AsyncSession = Depends(get_db)
):
    query = select(Business)  # 初始查询，选择所有商家
    
    # 根据排序方式选择不同的排序逻辑
    if sort_by == "rating":
        query = query.order_by(Business.rating.desc())  # 按评分降序排序
    elif sort_by == "avg_spend":
        query = query.order_by(Business.avg_spend.asc())  # 按人均消费升序排序
    else:
        query = query.order_by(Business.created_at.desc())  # 默认按创建时间降序排序
    
    result = await db.execute(query)  # 执行查询
    businesses = result.scalars().all()  # 获取查询结果

    return businesses  # 返回商家列表

