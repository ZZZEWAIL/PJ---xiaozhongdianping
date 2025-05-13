# backend/coupon_validators/threshold_validator.py
from fastapi import HTTPException
from backend.models import Coupon, UserCoupon, Package, Shop
from backend.coupon_validators.base_validator import BaseCouponValidator

class ThresholdValidator(BaseCouponValidator):
    """校验是否满足优惠券的最低消费金额门槛"""
    def validate(self, coupon: Coupon, user_coupon: UserCoupon, 
                 package: Package, shop: Shop) -> None:
        if coupon.min_spend and package.price < coupon.min_spend:
            raise HTTPException(status_code=400, detail="不满足使用该券的最低消费金额")
