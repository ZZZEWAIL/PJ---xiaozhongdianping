from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Dict, Any, List
from backend.database import get_db
from backend.models import (
    Coupon, UserCoupon, CouponStatus,
    DiscountType, ExpiryType, Package, Shop
)
from backend.schema import (
    CouponListResponse, UserCouponInfo, Coupon as CouponSchema
)
from backend.login import get_current_user
from backend.coupon_factory import CouponFactory

router = APIRouter()

# ------------------------- 新人券发放 ------------------------- #
@router.post("/coupons/new_user")
async def grant_new_user_coupons(
        db: AsyncSession = Depends(get_db),
        current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    新用户领取新人优惠券
    - 若系统尚未创建新人券定义，则先创建一张
    - 同一用户限领一次（由工厂方法内部校验）
    """
    user_id = current_user["id"]

    # 查询是否已有“新用户优惠券”定义
    result = await db.execute(select(Coupon).where(Coupon.name == "新用户优惠券"))
    coupon = result.scalars().first()

    if not coupon:
        # 若无定义则创建一张新人券（示例：无门槛减 10 元，30 天有效）
        coupon = CouponFactory.create_coupon(
            name="新用户优惠券",
            description="新用户专享满减券",
            discount_type=DiscountType.deduction,
            discount_value=10.0,
            min_spend=0,
            expiry_type=ExpiryType.valid_days,
            valid_days=30,
            total_quantity=1000,
            per_user_limit=1
        )
        db.add(coupon)
        await db.flush()  # 刷新获取 coupon.id

    # 为用户创建 UserCoupon 记录（工厂内部包含校验和库存扣减）
    try:
        await CouponFactory.create_user_coupon(coupon, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"message": "新人优惠券领取成功"}

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
