from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Dict, Any
from backend.database import get_db
from backend.models import Package, Order, Coupon, UserCoupon, CouponStatus, Shop
from backend.schema import OrderCreate, OrderCreated
from backend.login import get_current_user

router = APIRouter()

@router.post("/orders", response_model=OrderCreated)
async def create_order(order_data: OrderCreate,
                       db: AsyncSession = Depends(get_db),
                       current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    创建订单接口：用户发起下单，可选择使用优惠券（每笔订单限用一张券）。
    """
    user_id = current_user["id"]

    # 查询套餐是否存在
    package = await db.get(Package, order_data.package_id)
    if not package:
        raise HTTPException(status_code=404, detail="未找到指定套餐")

    final_price = package.price  # 默认价格为套餐原价

    # 如果用户选择了优惠券
    if order_data.coupon_id:
        # 查询用户优惠券和对应的券定义
        result = await db.execute(
            select(UserCoupon, Coupon).join(Coupon, UserCoupon.coupon_id == Coupon.id).where(
                UserCoupon.user_id == user_id,
                UserCoupon.coupon_id == order_data.coupon_id,
                UserCoupon.status == CouponStatus.unused
            )
        )
        data = result.first()
        if not data:
            raise HTTPException(status_code=400, detail="该优惠券不可用或已使用")

        user_coupon, coupon = data

        # 校验：最低消费门槛
        if coupon.min_spend and package.price < coupon.min_spend:
            raise HTTPException(status_code=400, detail="不满足使用该券的最低消费金额")

        # 校验：有效期（若过期，标记并拒绝使用）
        if user_coupon.expires_at and datetime.utcnow() > user_coupon.expires_at:
            user_coupon.status = CouponStatus.expired
            await db.commit()
            raise HTTPException(status_code=400, detail="该优惠券已过期")

        # 校验：门店/品类限制
        shop = await db.get(Shop, package.shop_id)
        if coupon.shop_restriction and shop and shop.name != coupon.shop_restriction:
            raise HTTPException(status_code=400, detail="该优惠券不适用于此门店")
        if coupon.category and shop and shop.category != coupon.category:
            raise HTTPException(status_code=400, detail="该优惠券不适用于此品类")

        # 使用策略模式，应用对应的折扣逻辑
        from backend.coupon_strategies import get_coupon_strategy
        strategy = get_coupon_strategy(coupon.discount_type)
        final_price = strategy.apply_discount(package.price, coupon)

    # 生成16位数字券码，确保唯一（此处略去数据库唯一性检测逻辑）
    import random, string
    voucher_code = ''.join(random.choices(string.digits, k=16))

    # 创建订单
    new_order = Order(
        user_id=user_id,
        package_id=package.id,
        voucher_code=voucher_code,
        coupon_id=order_data.coupon_id or None,
        order_amount=final_price
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    # 使用观察者模式通知其他模块（如：更新销量、标记优惠券已使用）
    from backend.order_observers import notify_order_created
    await notify_order_created(new_order, db)

    # 返回订单信息
    return {
        "id": new_order.id,
        "voucher_code": new_order.voucher_code,
        "order_amount": new_order.order_amount,
        "created_at": new_order.created_at
    }
