from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func
from sqlalchemy import Float
from backend.database import get_db
from backend.models import Shop, SearchHistory, ShopImage
from backend.schema import Shop as ShopSchema
from datetime import datetime
from sqlalchemy import delete
from pypinyin import pinyin, Style  # 新增：导入 pypinyin
from datetime import timezone, timedelta, time
from datetime import datetime
current_time = datetime.now(timezone(timedelta(hours=8)))

router = APIRouter()

# @router.get("/shops/search")
# async def search_shops(
#     keyword: str,
#     categories: list[str] = Query(None),
#     ratings: list[float] = Query(None),
#     category: str | None = None,
#     rating: float | None = Query(None, gt=0.0, le=5.0),
#     avg_cost_min: float | None = Query(None, gt=0),
#     avg_cost_max: float | None = Query(None, gt=0),
#     sort_by: str = Query('default', regex="^(default|rating|avg_cost)$"),
#     sort_order: str = Query('desc', regex="^(asc|desc)$"),
#     page: int = 1,
#     page_size: int = 10,
#     db: AsyncSession = Depends(get_db)
# ):
#     print(f"Received keyword: {keyword}")
#     # 检查是否已存在相同的搜索历史
#     existing_history = await db.execute(
#         select(SearchHistory).where(SearchHistory.keyword == keyword)
#     )
#     existing_history = existing_history.scalars().first()

#     if existing_history:
#         existing_history.searched_at = datetime.utcnow()
#         await db.commit()
#         await db.refresh(existing_history)  # 确保对象状态刷新
#     else:
#         new_history = SearchHistory(keyword=keyword)
#         db.add(new_history)
#         await db.commit()
#         await db.refresh(new_history)  # 确保对象状态刷新

#     # 将关键字转换为拼音（无音调）
#     keyword_pinyin_list = pinyin(keyword, style=Style.NORMAL)
#     keyword_pinyin = ' '.join([item[0] for item in keyword_pinyin_list])
#     print(f"Keyword pinyin: {keyword_pinyin}")

#     # 初始化查询：匹配名称、分类、名称拼音或分类拼音
#     query = select(Shop).where(
#         (Shop.name.ilike(f"%{keyword}%")) |
#         (Shop.category.ilike(f"%{keyword}%")) |
#         (Shop.name_pinyin.ilike(f"%{keyword_pinyin}%")) |
#         (Shop.category_pinyin.ilike(f"%{keyword_pinyin}%"))
#     )

#     # 应用筛选条件
#     if category:
#         query = query.where(Shop.category == category)
#     if rating:
#         query = query.where(Shop.rating >= rating)
#     if categories:
#         query = query.where(Shop.category.in_(categories))
#     if ratings:
#         print(f"Applying ratings filter: {ratings}")
#         if ratings:
#             query = query.where(Shop.rating >= ratings[0])
#     if avg_cost_min:
#         print(f"Applying avg_cost_min filter: {avg_cost_min}")
#         query = query.where(Shop.avg_cost >= avg_cost_min)
#     if avg_cost_max:
#         print(f"Applying avg_cost_max filter: {avg_cost_max}")
#         query = query.where(Shop.avg_cost <= avg_cost_max)

#     # 应用排序
#     print(f"Sorting parameters: sort_by={sort_by}, sort_order={sort_order}")
#     if sort_by == 'rating':
#         if sort_order == 'desc':
#             query = query.order_by(Shop.rating.desc())
#         else:
#             query = query.order_by(Shop.rating.asc())
#     elif sort_by == 'avg_cost':
#         if sort_order == 'desc':
#             query = query.order_by(Shop.avg_cost.desc())
#         else:
#             query = query.order_by(Shop.avg_cost.asc())
#     else:
#         if sort_order == 'desc':
#             query = query.order_by(Shop.id.desc())
#         else:
#             query = query.order_by(Shop.id.asc())

#     # 计算总数
#     count_query = query.with_only_columns(func.count()).order_by(None)
#     total = await db.scalar(count_query)

#     # 分页
#     query = query.offset((page - 1) * page_size).limit(page_size)
#     result = await db.execute(query)
#     shops = result.scalars().all()
#     print(f"Sorted shops: {[shop.name for shop in shops]}")

#     return {
#         "total": total,
#         "page": page,
#         "page_size": page_size,
#         "data": shops
#     }

def is_shop_open(business_hours: str, current_time: datetime) -> bool:
    """
    判断当前时间是否在营业时间内。
    business_hours 格式为 "HH:MM-HH:MM"，例如 "9:00-22:00"。
    """
    try:
        open_time_str, close_time_str = business_hours.split('-')
        open_hour, open_minute = map(int, open_time_str.split(':'))
        close_hour, close_minute = map(int, close_time_str.split(':'))
        
        open_time = time(open_hour, open_minute)
        close_time = time(close_hour, close_minute)
        current_time_only = time(current_time.hour, current_time.minute)
        
        # 处理跨天营业的情况（例如 22:00-2:00）
        if close_time < open_time:
            return current_time_only >= open_time or current_time_only <= close_time
        else:
            return open_time <= current_time_only <= close_time
    except Exception as e:
        print(f"Error parsing business hours '{business_hours}': {e}")
        return False

@router.get("/shops/search")
async def search_shops(
    keyword: str,
    categories: list[str] = Query(None),
    ratings: list[float] = Query(None),
    category: str | None = None,
    rating: float | None = Query(None, gt=0.0, le=5.0),
    avg_cost_min: float | None = Query(None, gt=0),
    avg_cost_max: float | None = Query(None, gt=0),
    is_open: bool | None = Query(None),  # 新增：营业中筛选条件
    sort_by: str = Query('default', regex="^(default|rating|avg_cost)$"),
    sort_order: str = Query('desc', regex="^(asc|desc)$"),
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    print(f"Received keyword: {keyword}")
    # 保存搜索历史
    existing_history = await db.execute(
        select(SearchHistory).where(SearchHistory.keyword == keyword)
    )
    existing_history = existing_history.scalars().first()

    if existing_history:
        existing_history.searched_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_history)
    else:
        new_history = SearchHistory(keyword=keyword)
        db.add(new_history)
        await db.commit()
        await db.refresh(new_history)

    keyword_pinyin_list = pinyin(keyword, style=Style.NORMAL)
    keyword_pinyin = ' '.join([item[0] for item in keyword_pinyin_list])
    print(f"Keyword pinyin: {keyword_pinyin}")

    # 初始化查询
    query = select(Shop).where(
        (Shop.name.ilike(f"%{keyword}%")) |
        (Shop.category.ilike(f"%{keyword}%")) |
        (Shop.name_pinyin.ilike(f"%{keyword_pinyin}%")) |
        (Shop.category_pinyin.ilike(f"%{keyword_pinyin}%"))
    )

    # 应用筛选条件
    if category:
        query = query.where(Shop.category == category)
    if rating:
        query = query.where(Shop.rating >= rating)
    if categories:
        query = query.where(Shop.category.in_(categories))
    if ratings:
        print(f"Applying ratings filter: {ratings}")
        if ratings:
            query = query.where(Shop.rating >= ratings[0])
    if avg_cost_min:
        print(f"Applying avg_cost_min filter: {avg_cost_min}")
        query = query.where(Shop.avg_cost >= avg_cost_min)
    if avg_cost_max:
        print(f"Applying avg_cost_max filter: {avg_cost_max}")
        query = query.where(Shop.avg_cost <= avg_cost_max)
    if is_open is True:  # 新增：营业中筛选
        print("Applying is_open filter")
        current_time = datetime.utcnow()  # 注意：可能需要调整为本地时间
        # 获取所有商家，逐个检查营业时间
        result = await db.execute(query)
        shops = result.scalars().all()
        open_shop_ids = [
            shop.id for shop in shops
            if is_shop_open(shop.business_hours, current_time)
        ]
        if open_shop_ids:
            query = query.where(Shop.id.in_(open_shop_ids))
        else:
            query = query.where(Shop.id == -1)  # 没有营业中的商家，返回空结果

    # 应用排序
    print(f"Sorting parameters: sort_by={sort_by}, sort_order={sort_order}")
    if sort_by == 'rating':
        if sort_order == 'desc':
            query = query.order_by(Shop.rating.desc())
        else:
            query = query.order_by(Shop.rating.asc())
    elif sort_by == 'avg_cost':
        if sort_order == 'desc':
            query = query.order_by(Shop.avg_cost.desc())
        else:
            query = query.order_by(Shop.avg_cost.asc())
    else:
        if sort_order == 'desc':
            query = query.order_by(Shop.id.desc())
        else:
            query = query.order_by(Shop.id.asc())

    # 计算总数
    count_query = query.with_only_columns(func.count()).order_by(None)
    total = await db.scalar(count_query)

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    shops = result.scalars().all()
    print(f"Sorted shops: {[shop.name for shop in shops]}")

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": shops
    }

@router.get("/shops/search/history", response_model=list[str])
async def get_search_history(
    limit: int = Query(10, ge=1, le=50),  # 添加 limit 参数
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SearchHistory.keyword)
        .order_by(SearchHistory.searched_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    return history

@router.delete("/shops/search/history")
async def clear_search_history(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(SearchHistory))
    await db.commit()
    return {"message": "Search history cleared"}

@router.get("/shops/{shop_id}")
async def get_shop_detail(
    shop_id: int,
    image_page: int = Query(1, ge=1),  # 图片分页参数
    image_page_size: int = Query(1, ge=1),  # 每页显示的图片数量
    db: AsyncSession = Depends(get_db)
):
    # 查询商家详情
    shop_query = select(Shop).where(Shop.id == shop_id)
    shop_result = await db.execute(shop_query)
    shop = shop_result.scalars().first()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # 查询关联的图片（分页）
    image_query = select(ShopImage).where(ShopImage.shop_id == shop_id)
    
    # 计算图片总数
    count_query = select(func.count()).select_from(image_query.subquery())
    total_images_result = await db.execute(count_query)
    total_images = total_images_result.scalar()

    # 应用分页
    image_query = image_query.offset((image_page - 1) * image_page_size).limit(image_page_size)
    image_result = await db.execute(image_query)
    images = image_result.scalars().all()

    # 返回商家详情和分页的图片
    return {
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "category": shop.category,
            "rating": shop.rating,
            "price_range": shop.price_range,
            "avg_cost": shop.avg_cost,
            "address": shop.address,
            "phone": shop.phone,
            "business_hours": shop.business_hours,
            "image_url": shop.image_url
        },
        "images": {
            "total": total_images,
            "page": image_page,
            "page_size": image_page_size,
            "data": [{"id": img.id, "image_url": img.image_url} for img in images]
        }
    }