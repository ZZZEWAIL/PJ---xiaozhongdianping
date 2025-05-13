# backend/coupon_validators/status_validator.py
from fastapi import HTTPException
from backend.models import Coupon, UserCoupon, Package, Shop, CouponStatus
from backend.coupon_validators.base_validator import BaseCouponValidator

class StatusValidator(BaseCouponValidator):
    """校验优惠券是否未被使用"""
    def validate(self, coupon: Coupon, user_coupon: UserCoupon, 
                 package: Package, shop: Shop) -> None:
        if user_coupon.status != CouponStatus.unused:
            raise HTTPException(status_code=400, detail="该优惠券不可用或已使用")
