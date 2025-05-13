# backend/coupon_validators/expiry_validator.py
from datetime import datetime
from fastapi import HTTPException
from backend.models import Coupon, CouponStatus, UserCoupon, Package, Shop
from backend.coupon_validators.base_validator import BaseCouponValidator

class ExpiryValidator(BaseCouponValidator):
    """校验优惠券是否已过期"""
    def validate(self, coupon: Coupon, user_coupon: UserCoupon, 
                 package: Package, shop: Shop) -> None:
        if user_coupon.expires_at and datetime.utcnow() > user_coupon.expires_at:
            user_coupon.status = CouponStatus.expired
            raise HTTPException(status_code=400, detail="该优惠券已过期")
