from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, Float
from sqlalchemy import join
from backend.database import get_db
from backend.models import Shop, SearchHistory, ShopImage, Package, Order
from backend.schema import Shop as ShopSchema, Package as PackageSchema, Order as OrderSchema
from backend.login import get_current_user  # 导入 get_current_user
from datetime import datetime, timezone, timedelta, time
from sqlalchemy import delete
from pypinyin import pinyin, Style
from typing import List, Dict, Any

# 提取分页逻辑
async def paginate_query(
    db: AsyncSession,
    query,
    page: int,
    page_size: int,
    return_scalars: bool = True
) -> Dict[str, Any]:
    count_query = query.with_only_columns(func.count()).order_by(None)
    total = await db.scalar(count_query)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    if return_scalars:
        items = result.scalars().all()
    else:
        items = result.all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": items
    }

router = APIRouter()

def is_shop_open(business_hours: str, current_time: datetime) -> bool:
    try:
        open_time_str, close_time_str = business_hours.split('-')
        open_hour, open_minute = map(int, open_time_str.split(':'))
        close_hour, close_minute = map(int, close_time_str.split(':'))
        
        open_time = time(open_hour, open_minute)
        close_time = time(close_hour, close_minute)
        current_time_only = time(current_time.hour, current_time.minute)
        
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
    is_open: bool | None = Query(None),
    sort_by: str = Query('default', regex="^(default|rating|avg_cost)$"),
    sort_order: str = Query('desc', regex="^(asc|desc)$"),
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db)
):
    print(f"Received keyword: {keyword}")
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

    query = select(Shop).where(
        (Shop.name.ilike(f"%{keyword}%")) |
        (Shop.category.ilike(f"%{keyword}%")) |
        (Shop.name_pinyin.ilike(f"%{keyword_pinyin}%")) |
        (Shop.category_pinyin.ilike(f"%{keyword_pinyin}%"))
    )

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
    if is_open is True:
        print("Applying is_open filter")
        current_time = datetime.utcnow()
        result = await db.execute(query)
        shops = result.scalars().all()
        open_shop_ids = [
            shop.id for shop in shops
            if is_shop_open(shop.business_hours, current_time)
        ]
        if open_shop_ids:
            query = query.where(Shop.id.in_(open_shop_ids))
        else:
            query = query.where(Shop.id == -1)

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

    result = await paginate_query(db, query, page, page_size)
    shops = result["data"]

    shop_data = []
    current_time = datetime.utcnow()
    for shop in shops:
        image_query = select(ShopImage).where(ShopImage.shop_id == shop.id)
        image_result = await db.execute(image_query)
        images = image_result.scalars().all()
        image_urls = [image.image_url for image in images] if images else ["https://via.placeholder.com/150"]

        is_open_now = is_shop_open(shop.business_hours, current_time)

        shop_data.append({
            "id": shop.id,
            "name": shop.name,
            "category": shop.category,
            "rating": shop.rating,
            "price_range": shop.price_range,
            "avg_cost": shop.avg_cost,
            "name_pinyin": shop.name_pinyin,
            "category_pinyin": shop.category_pinyin,
            "address": shop.address,
            "phone": shop.phone,
            "business_hours": shop.business_hours,
            "image_urls": image_urls,
            "is_open": is_open_now
        })

    return {
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "data": shop_data
    }

@router.get("/shops/search/history", response_model=list[str])
async def get_search_history(
    limit: int = Query(10, ge=1, le=50),
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
    image_page: int = Query(1, ge=1),
    image_page_size: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    shop_query = select(Shop).where(Shop.id == shop_id)
    shop_result = await db.execute(shop_query)
    shop = shop_result.scalars().first()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    image_query = select(ShopImage).where(ShopImage.shop_id == shop_id)
    count_query = select(func.count()).select_from(image_query.subquery())
    total_images_result = await db.execute(count_query)
    total_images = total_images_result.scalar()

    image_query = image_query.offset((image_page - 1) * image_page_size).limit(image_page_size)
    image_result = await db.execute(image_query)
    images = image_result.scalars().all()

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

@router.get("/shops/{shop_id}/packages", response_model=List[PackageSchema])
async def get_shop_packages(
    shop_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(Package).where(Package.shop_id == shop_id)
    result = await db.execute(query)
    packages = result.scalars().all()

    if not packages:
        return []

    return packages

@router.get("/packages/{package_id}", response_model=PackageSchema)
async def get_package_detail(
    package_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(Package).where(Package.id == package_id)
    result = await db.execute(query)
    package = result.scalars().first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    return package

@router.get("/user/orders", response_model=Dict[str, Any])
async def get_user_orders(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    query = (
        select(Order, Package.title, Shop.name)
        .join(Package, Order.package_id == Package.id)
        .join(Shop, Package.shop_id == Shop.id)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )

    result = await paginate_query(db, query, page, page_size, return_scalars=False)
    orders = result["data"]

    order_data = [
        OrderSchema(
            package_title=order[1],
            created_at=order[0].created_at,
            shop_name=order[2],
            order_id=order[0].id
        )
        for order in orders
    ]

    return {
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "data": order_data
    }

@router.get("/orders/{order_id}", response_model=OrderSchema)
async def get_order_detail(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    query = (
        select(Order, Package.title, Shop.name)
        .join(Package, Order.package_id == Package.id)
        .join(Shop, Package.shop_id == Shop.id)
        .where(Order.id == order_id)
        .where(Order.user_id == user_id)
    )

    result = await db.execute(query)
    order = result.first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not authorized")

    return OrderSchema(
        package_title=order[1],
        created_at=order[0].created_at,
        shop_name=order[2],
        order_id=order[0].id,
        voucher_code=order[0].voucher_code
    )