from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from backend.database import get_db
from backend.models import (
    Coupon, UserCoupon, CouponStatus,
    DiscountType, ExpiryType, Package, Shop
)
from backend.schema import (
    CouponListResponse, UserCouponInfo, Coupon as CouponSchema,
    NewUserCouponResponse, NewUserCouponDTO
)
from backend.login import get_current_user
from backend.coupon_factory import CouponFactory

router = APIRouter()

# ------------------------- 新人券发放 ------------------------- #
@router.get("/coupons/new_user/available", response_model=NewUserCouponResponse)
async def list_new_user_coupons(
        db: AsyncSession = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取可供新用户选择的优惠券列表
    - 返回三种类型的新人券供用户选择
    - 检查用户是否有资格领取（未使用过点评购买过团购套餐的用户）
    - 同一用户只能领取一张新人券（三选一）
    """
    user_id = current_user["id"]

    # 检查用户是否已领取过新人券
    result = await db.execute(select(func.count(UserCoupon.id)).where(
        UserCoupon.user_id == user_id,
        UserCoupon.coupon_id.in_(
            select(Coupon.id).where(
                Coupon.name.in_(["新人KFC9折券", "新人奶茶免单券", "新人100元优惠券"])
            )
        )
    ))
    count = result.scalar() or 0
    if count > 0:
        raise HTTPException(status_code=400, detail="您已领取过新人优惠券")

    # 检查用户是否已购买过团购套餐（这里需根据实际业务逻辑补充）
    # TODO: 添加检查用户是否使用过"小众点评"购买过团购套餐的逻辑

    # 获取或创建三种新人券定义
    coupons = []
    
    # 1. KFC 9折券
    kfc_coupon = await get_or_create_coupon(
        db, 
        name="新人KFC9折券",
        description="满10元可用、整单9折券、仅限KFC南区店使用",
        discount_type=DiscountType.discount,
        discount_value=0.9,
        min_spend=10.0,
        shop_restriction="KFC南区店",
        expiry_type=ExpiryType.valid_days,
        valid_days=7,
        total_quantity=10000,
        per_user_limit=1
    )
    coupons.append(format_new_user_coupon(kfc_coupon, "kfc"))
    
    # 2. 奶茶免单券
    milk_tea_coupon = await get_or_create_coupon(
        db,
        name="新人奶茶免单券",
        description="无门槛免单券、最高抵扣15元、适用品类：奶茶",
        discount_type=DiscountType.deduction,
        discount_value=15.0,
        min_spend=0,
        max_discount=15.0,
        category="奶茶",
        expiry_type=ExpiryType.valid_days,
        valid_days=7,
        total_quantity=100,
        per_user_limit=1
    )
    coupons.append(format_new_user_coupon(milk_tea_coupon, "milk_tea"))
    
    # 3. 100元优惠券
    discount_coupon = await get_or_create_coupon(
        db,
        name="新人100元优惠券",
        description="满200减100元券、全品类通用",
        discount_type=DiscountType.deduction,
        discount_value=100.0,
        min_spend=200.0,
        expiry_type=ExpiryType.valid_days,
        valid_days=1,
        total_quantity=1,
        per_user_limit=1
    )
    coupons.append(format_new_user_coupon(discount_coupon, "discount"))

    await db.commit()
    return NewUserCouponResponse(eligible=True, coupons=coupons)


@router.post("/coupons/new_user/claim/{coupon_type}")
async def claim_new_user_coupon(
        coupon_type: Literal["kfc", "milk_tea", "discount"],
        db: AsyncSession = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    用户领取指定类型的新人优惠券
    - coupon_type: 用户选择的优惠券类型（kfc, milk_tea, discount）
    - 确保用户有资格领取且未领取过任何新人券
    - 创建用户优惠券记录并扣减库存
    """
    user_id = current_user["id"]
    
    # 检查用户是否已领取过新人券
    result = await db.execute(select(func.count(UserCoupon.id)).where(
        UserCoupon.user_id == user_id,
        UserCoupon.coupon_id.in_(
            select(Coupon.id).where(
                Coupon.name.in_(["新人KFC9折券", "新人奶茶免单券", "新人100元优惠券"])
            )
        )
    ))
    count = result.scalar() or 0
    if count > 0:
        raise HTTPException(status_code=400, detail="您已领取过新人优惠券")
    
    # 检查用户是否已购买过团购套餐（这里需根据实际业务逻辑补充）
    # TODO: 添加检查用户是否使用过"小众点评"购买过团购套餐的逻辑
    
    # 根据用户选择的类型获取对应优惠券
    coupon_name = None
    if coupon_type == "kfc":
        coupon_name = "新人KFC9折券"
    elif coupon_type == "milk_tea":
        coupon_name = "新人奶茶免单券"
    elif coupon_type == "discount":
        coupon_name = "新人100元优惠券"
    else:
        raise HTTPException(status_code=400, detail="无效的优惠券类型")
    
    # 查询优惠券
    result = await db.execute(select(Coupon).where(Coupon.name == coupon_name))
    coupon = result.scalars().first()
    
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    
    # 为用户创建 UserCoupon 记录（工厂内部包含校验和库存扣减）
    try:
        user_coupon = await CouponFactory.create_user_coupon(coupon, user_id, db)
        await db.commit()
        return {
            "message": f"成功领取{coupon.name}",
            "coupon_id": user_coupon.id,
            "expires_at": user_coupon.expires_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Helper function to get or create coupon definitions
async def get_or_create_coupon(
        db: AsyncSession,
        name: str,
        description: str,
        discount_type: DiscountType,
        discount_value: float,
        min_spend: float = 0,
        max_discount: float = None,
        category: str = None,
        shop_restriction: str = None,
        expiry_type: ExpiryType = None,
        expiry_date: datetime = None,
        valid_days: int = None,
        total_quantity: int = None,
        per_user_limit: int = 1) -> Coupon:
    """
    获取或创建优惠券定义
    如果不存在则创建，存在则返回已有优惠券
    """
    result = await db.execute(select(Coupon).where(Coupon.name == name))
    coupon = result.scalars().first()
    
    if not coupon:
        coupon = CouponFactory.create_coupon(
            name=name,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_spend=min_spend,
            max_discount=max_discount,
            category=category,
            shop_restriction=shop_restriction,
            expiry_type=expiry_type,
            expiry_date=expiry_date,
            valid_days=valid_days,
            total_quantity=total_quantity,
            remaining_quantity=total_quantity,
            per_user_limit=per_user_limit
        )
        db.add(coupon)
        await db.flush()  # 刷新获取 coupon.id
    
    return coupon


# Helper function to format coupon for response
def format_new_user_coupon(coupon: Coupon, coupon_type: str) -> NewUserCouponDTO:
    """Format coupon for new user response"""
    remaining = "已发完" if coupon.remaining_quantity == 0 else f"剩余{coupon.remaining_quantity}张"
    
    return NewUserCouponDTO(
        id=coupon.id,
        type=coupon_type,
        name=coupon.name,
        description=coupon.description,
        discount_type=coupon.discount_type.value,
        discount_value=coupon.discount_value,
        min_spend=coupon.min_spend,
        max_discount=coupon.max_discount,
        category=coupon.category,
        shop_restriction=coupon.shop_restriction,
        valid_days=coupon.valid_days,
        remaining=remaining
    )


# ------------------------- 普通券领取 ------------------------- #
@router.post("/coupons/{coupon_id}/claim")
async def claim_coupon(
        coupon_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    用户领取指定 ID 的优惠券
    """
    user_id = current_user["id"]
    coupon = await db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")

    try:
        await CouponFactory.create_user_coupon(coupon, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"message": "优惠券领取成功"}

# ------------------------- 奖励券发放 ------------------------- #
async def issue_coupon(
    db: AsyncSession,
    user_id: int,
    coupon_type: Literal["invitation", "review"],
    discount_value: float,
    max_discount: float | None = None,
    min_spend: float = 0.0,
    expiry_days: int = 7
) -> Dict[str, Any]:
    """
    统一发放优惠券逻辑
    - coupon_type: "invitation" 或 "review"
    - discount_value: 折扣金额或折扣比例
    - max_discount: 最大抵扣金额（可选）
    - min_spend: 使用门槛（默认0）
    - expiry_days: 有效天数（默认7天）
    """
    try:
        # 定义优惠券参数
        name = f"{coupon_type.capitalize()}奖励券"
        description = f"无门槛{coupon_type}奖励券"
        discount_type = DiscountType.fixed_amount if max_discount else DiscountType.discount
        expiry_date = datetime.utcnow() + timedelta(days=expiry_days)

        # 创建优惠券
        coupon = Coupon(
            name=name,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_spend=min_spend,
            max_discount=max_discount,
            expiry_date=expiry_date,
            total_quantity=1,
            remaining_quantity=1,
            per_user_limit=1,
            category="invitation" if coupon_type == "invitation" else "review",
        )
        db.add(coupon)
        await db.commit()
        await db.refresh(coupon)
        print(f"Coupon created: {coupon}")


        # 发放给用户
        user_coupon = UserCoupon(
            user_id=user_id,
            coupon_id=coupon.id,
            status=CouponStatus.unused,
            expires_at=expiry_date
        )
        db.add(user_coupon)
        await db.commit()
        print(f"User coupon issued: {user_coupon}")


        return {
            "message": f"成功发放{coupon_type}奖励券",
            "coupon_id": user_coupon.id,
            "expires_at": user_coupon.expires_at
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"发放奖励券失败: {str(e)}")

# ------------------------- 用户卡包（按状态分类） ------------------------- #
@router.get("/user/coupons", response_model=CouponListResponse)
async def list_user_coupons(
        db: AsyncSession = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取当前用户的全部优惠券，按状态分为：unused / used / expired
    """
    user_id = current_user["id"]
    result = await db.execute(
        select(UserCoupon, Coupon)
        .join(Coupon, UserCoupon.coupon_id == Coupon.id)
        .where(UserCoupon.user_id == user_id)
    )
    records = result.all()

    now = datetime.utcnow()
    unused: List[UserCouponInfo] = []
    used: List[UserCouponInfo] = []
    expired: List[UserCouponInfo] = []
    status_changed = False  # 标记是否有券被动过期

    for user_coupon, coupon in records:
        status = user_coupon.status

        # 检查是否已过期：若未使用且已到期，则更新状态为 expired
        if status == CouponStatus.unused and user_coupon.expires_at and user_coupon.expires_at < now:
            user_coupon.status = CouponStatus.expired
            status = CouponStatus.expired
            status_changed = True

        # 构造返回结构
        coupon_vo = CouponSchema.from_orm(coupon)
        info = UserCouponInfo(
            id=user_coupon.id,
            status=status.value,
            expires_at=user_coupon.expires_at,
            coupon=coupon_vo
        )

        if status == CouponStatus.unused:
            unused.append(info)
        elif status == CouponStatus.used:
            used.append(info)
        else:  # expired
            expired.append(info)

    # 若有状态变化，提交数据库
    if status_changed:
        await db.commit()

    return CouponListResponse(unused=unused, used=used, expired=expired)

# ------------------------- 获取可用优惠券 ------------------------- #
@router.get("/user/coupons/available", response_model=List[UserCouponInfo])
async def get_available_coupons(
        package_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    根据套餐 ID 获取当前用户可用的优惠券（按业务规则过滤）
    """
    user_id = current_user["id"]

    # 查询套餐及其店铺信息
    package = await db.get(Package, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    shop = await db.get(Shop, package.shop_id)

    # 查询用户未使用的券
    result = await db.execute(
        select(UserCoupon, Coupon)
        .join(Coupon, UserCoupon.coupon_id == Coupon.id)
        .where(UserCoupon.user_id == user_id, UserCoupon.status == CouponStatus.unused)
    )
    records = result.all()

    now = datetime.utcnow()
    available: List[UserCouponInfo] = []
    status_changed = False

    for user_coupon, coupon in records:
        # 过滤已过期
        if user_coupon.expires_at and user_coupon.expires_at < now:
            user_coupon.status = CouponStatus.expired
            status_changed = True
            continue

        # 使用门槛
        if coupon.min_spend and package.price < coupon.min_spend:
            continue
        # 店铺限制
        if coupon.shop_restriction and shop and shop.name != coupon.shop_restriction:
            continue
        # 品类限制
        if coupon.category and shop and shop.category != coupon.category:
            continue

        # --- 新增验证 ---
        # 1. 检查优惠券库存
        if coupon.remaining_quantity and coupon.remaining_quantity <= 0:
            continue

        # 2. 检查用户使用限制
        if coupon.per_user_limit:
            used_count = await db.execute(
                select(func.count(UserCoupon.id))
                .where(
                    UserCoupon.user_id == user_id,
                    UserCoupon.coupon_id == coupon.id,
                    UserCoupon.status == CouponStatus.used
                )
            )
            if (used_count.scalar() or 0) >= coupon.per_user_limit:
                continue

        # 满足条件，加入可用列表
        coupon_vo = CouponSchema.from_orm(coupon)
        available.append(
            UserCouponInfo(
                id=user_coupon.id,
                status=CouponStatus.unused.value,
                expires_at=user_coupon.expires_at,
                coupon=coupon_vo
            )
        )

    if status_changed:
        await db.commit()

    return available
