"""
优惠券折扣计算策略模块（策略模式）。
包含适用于不同优惠券类型的策略类。
"""
from abc import ABC, abstractmethod
from backend.models import Coupon, DiscountType

class BaseCouponStrategy(ABC):
    """优惠券折扣策略的抽象基类。"""
    
    @abstractmethod
    def apply_discount(self, original_price: float, coupon: Coupon) -> float:
        """
        根据原价和优惠券信息计算折扣后的最终价格。
        """
        pass

class DeductionStrategy(BaseCouponStrategy):
    """固定金额减免策略（如满减券）。"""
    
    def apply_discount(self, original_price: float, coupon: Coupon) -> float:
        # 从原价中减去固定金额，确保最终价格不低于 0。
        discount_amount = coupon.discount_value
        final_price = original_price - discount_amount
        if final_price < 0:
            final_price = 0.0
        return final_price

class FixedAmountStrategy(BaseCouponStrategy):
    """减至固定金额策略（如免单券、固定价格券）。"""
    
    def apply_discount(self, original_price: float, coupon: Coupon) -> float:
        # 计算应减金额（原价-目标价）
        discount_amount = original_price - coupon.discount_value
    
        # 应用最大折扣限制
        if coupon.max_discount is not None:
            discount_amount = min(discount_amount, coupon.max_discount)
    
        # 确保最终价格不低于0
        final_price = original_price - discount_amount
        return max(final_price, 0.0)

class DiscountPercentageStrategy(BaseCouponStrategy):
    """按折扣比例进行折扣的策略（如 9 折券）。"""
    
    def apply_discount(self, original_price: float, coupon: Coupon) -> float:
        # 按照折扣系数进行计算（例如 0.9 表示打 9 折）
        discounted_price = original_price * coupon.discount_value
        if coupon.max_discount is not None:
            # 如果优惠金额超过最大优惠限制，则限制其上限
            full_discount = original_price - discounted_price
            if full_discount > coupon.max_discount:
                discounted_price = original_price - coupon.max_discount
        # 四舍五入保留两位小数，确保金额格式统一
        return round(discounted_price, 2)

def get_coupon_strategy(discount_type: DiscountType) -> BaseCouponStrategy:
    """
    根据优惠券的折扣类型返回对应的折扣策略对象（工厂方法）。
    """
    if discount_type == DiscountType.deduction:
        return DeductionStrategy()
    elif discount_type == DiscountType.fixed_amount:
        return FixedAmountStrategy()
    elif discount_type == DiscountType.discount:
        return DiscountPercentageStrategy()
    else:
        # 默认策略为固定减免（可根据需求修改）
        return DeductionStrategy()
