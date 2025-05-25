from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Dict, Any
from backend.database import get_db
from backend.models import Package, Order, Coupon, UserCoupon, CouponStatus, Shop, User
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
            # UserCoupon.id 是唯一的
            # UserCoupon.coupon_id 可能重复
            select(UserCoupon, Coupon).join(Coupon, UserCoupon.coupon_id == Coupon.id).where(
                UserCoupon.user_id == user_id,
                UserCoupon.id == order_data.coupon_id,
                UserCoupon.status == CouponStatus.unused
            )
        )
        data = result.first()
        if not data:
            raise HTTPException(status_code=400, detail="该优惠券不可用或已使用")

        user_coupon, coupon = data

        # --- 新增验证开始 ---
        # 1. 检查优惠券库存
        if coupon.remaining_quantity and coupon.remaining_quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="优惠券已被领完，请选择其他优惠"
            )

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
                raise HTTPException(
                    status_code=400,
                    detail=f"您已超过该优惠券的限用次数（{coupon.per_user_limit}次）"
                )

        if coupon.min_spend and package.price < coupon.min_spend:
            raise HTTPException(status_code=400, detail="最低消费金额未满足")
    
        # 检查是否过期
        if user_coupon.expires_at and datetime.utcnow() > user_coupon.expires_at:
            user_coupon.status = CouponStatus.expired

            await db.commit()
            raise HTTPException(status_code=400, detail="该优惠券已过期")


        # 获取店铺信息
        shop = await db.get(Shop, package.shop_id)

        if coupon.shop_restriction and shop and shop.name != coupon.shop_restriction:
            raise HTTPException(status_code=400, detail="该商户不可使用此优惠券")

        if coupon.category and shop and shop.category != coupon.category:
            raise HTTPException(status_code=400, detail="该商户不符合此类别")


        # 校验通过后，应用优惠券的折扣逻辑（策略模式）
        from backend.coupon_strategies import get_coupon_strategy
        strategy = get_coupon_strategy(coupon.discount_type)
        final_price = strategy.apply_discount(package.price, coupon)


    # 邀请码校验
    inviter = None
    if order_data.invitation_code:
        inviter_result = await db.execute(
            select(User).where(User.invitation_code == order_data.invitation_code)
        )
        inviter = inviter_result.scalar()
        if not inviter or inviter.id == user_id:
            raise HTTPException(status_code=400, detail="无效的邀请码")
        order_count = await db.execute(
            select(func.count()).where(Order.user_id == user_id)
        )
        if order_count.scalar() > 0:
            raise HTTPException(status_code=400, detail="仅首次下单可使用邀请码")
        if final_price <= 10:
            raise HTTPException(status_code=400, detail="订单金额需超过10元")


    # 生成16位数字券码，确保唯一（此处略去数据库唯一性检测逻辑）
    import random, string
    voucher_code = ''.join(random.choices(string.digits, k=16))

    # 创建订单
    new_order = Order(
        user_id=user_id,
        package_id=package.id,
        voucher_code=voucher_code,
        coupon_id=order_data.coupon_id or None,
        order_amount=final_price,
        invitation_code=order_data.invitation_code
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    # 邀请记录（在订单创建后调用）
    if order_data.invitation_code and inviter:
        from backend.invitation import record_invitation
        try:
            await record_invitation(db, order=new_order, inviter_id=inviter.id, invited_user_id=user_id)
        except Exception as e:
            # 记录日志，但不影响订单创建
            print(f"Failed to record invitation: {str(e)}")

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
