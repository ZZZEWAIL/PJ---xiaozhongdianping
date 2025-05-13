# backend/coupon_validators/category_validator.py
from fastapi import HTTPException
from backend.models import Coupon, UserCoupon, Package, Shop
from backend.coupon_validators.base_validator import BaseCouponValidator

class CategoryValidator(BaseCouponValidator):
    """校验优惠券是否适用于当前商品品类"""
    def validate(self, coupon: Coupon, user_coupon: UserCoupon, 
                 package: Package, shop: Shop) -> None:
        if coupon.category and shop.category != coupon.category:
            raise HTTPException(status_code=400, detail="该优惠券不适用于此品类")
