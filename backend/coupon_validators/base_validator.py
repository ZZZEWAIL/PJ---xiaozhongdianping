# backend/coupon_validators/base_validator.py
from abc import ABC, abstractmethod
from backend.models import Coupon, UserCoupon, Package, Shop

class BaseCouponValidator(ABC):
    """优惠券校验器基类，定义统一的校验接口"""
    @abstractmethod
    def validate(self, coupon: Coupon, user_coupon: UserCoupon, 
                 package: Package, shop: Shop) -> None:
        """
        校验优惠券是否符合特定规则。
        如果校验失败应直接抛出 HTTPException。
        """
        pass
