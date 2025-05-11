"""
优惠券工厂模块，用于创建优惠券对象（工厂模式）。
封装了创建过程中必填字段校验、默认值设定等初始化逻辑。
"""
from datetime import datetime, timedelta
from backend.models import Coupon, UserCoupon, DiscountType, ExpiryType, CouponStatus
from sqlalchemy.ext.asyncio import AsyncSession

class CouponFactory:
    @staticmethod
    def create_coupon(name: str,
                      discount_type: DiscountType,
                      discount_value: float,
                      description: str = None,
                      min_spend: float = 0,
                      max_discount: float = None,
                      category: str = None,
                      shop_restriction: str = None,
                      expiry_type: ExpiryType = None,
                      expiry_date: datetime = None,
                      valid_days: int = None,
                      total_quantity: int = None,
                      remaining_quantity: int = None,
                      per_user_limit: int = None) -> Coupon:
        """
        创建一个 Coupon 实例，并设置默认值和字段合法性校验。
        """
        # 检查必要字段是否填写
        if not name or discount_type is None or discount_value is None:
            raise ValueError("必须填写优惠券名称、折扣类型和折扣数值")
        if discount_value < 0:
            raise ValueError("折扣值不能为负数")
        # 折扣类型为百分比时，确保在 0 到 1 之间（如 0.9 表示 9 折）
        if discount_type == DiscountType.discount and not (0 < discount_value < 1):
            raise ValueError("折扣类型优惠券的折扣值必须在 0 和 1 之间")

        # 检查有效期字段是否合法
        if expiry_type == ExpiryType.fixed_date and expiry_date is None:
            raise ValueError("固定日期类型的券必须设置截止日期")
        if expiry_type == ExpiryType.valid_days and valid_days is None:
            raise ValueError("相对天数类型的券必须设置 valid_days")

        # 如果未指定有效期类型，则默认设置为无限期
        if expiry_type is None:
            expiry_type = ExpiryType.unlimited

        # 如果设置了总发放量但未设置剩余数量，则默认剩余数量等于总量
        if total_quantity is not None and remaining_quantity is None:
            remaining_quantity = total_quantity

        # 创建 Coupon 实例
        coupon = Coupon(
            name=name,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_spend=min_spend if min_spend is not None else 0,
            max_discount=max_discount,
            category=category,
            shop_restriction=shop_restriction,
            expiry_type=expiry_type,
            expiry_date=expiry_date,
            valid_days=valid_days,
            total_quantity=total_quantity,
            remaining_quantity=remaining_quantity,
            per_user_limit=per_user_limit
        )
        return coupon

    @staticmethod
    async def create_user_coupon(coupon: Coupon, user_id: int, db: AsyncSession) -> UserCoupon:
        """
        创建一张用户专属的优惠券记录，用于用户领取优惠券。
        该方法同时处理库存扣减、领取上限校验、有效期计算等逻辑。
        """
        # 检查是否还有库存
        if coupon.remaining_quantity is not None:
            if coupon.remaining_quantity <= 0:
                raise ValueError("该优惠券已发放完毕")

        # 检查是否超过用户限领数量
        from sqlalchemy import select, func
        from backend.models import UserCoupon  # 防止循环引用
        result = await db.execute(select(func.count(UserCoupon.id)).where(
            UserCoupon.user_id == user_id,
            UserCoupon.coupon_id == coupon.id,
            UserCoupon.status != CouponStatus.expired
        ))
        count = result.scalar() or 0
        if coupon.per_user_limit is not None and count >= coupon.per_user_limit:
            raise ValueError("该用户已达到最大领取次数")

        # 库存扣减
        if coupon.remaining_quantity is not None:
            coupon.remaining_quantity -= 1

        # 设置用户专属优惠券的过期时间
        expires_at = None
        if coupon.expiry_type == ExpiryType.fixed_date:
            expires_at = coupon.expiry_date
        elif coupon.expiry_type == ExpiryType.valid_days:
            expires_at = datetime.utcnow() + timedelta(days=coupon.valid_days or 0)

        # 创建用户优惠券记录
        user_coupon = UserCoupon(user_id=user_id, coupon_id=coupon.id,
                                 status=CouponStatus.unused, expires_at=expires_at)
        db.add(user_coupon)
        # 注意：数据库事务提交应由外部统一控制，以保证事务一致性
        return user_coupon
