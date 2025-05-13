# backend/coupon_validators/shop_validator.py
from fastapi import HTTPException
from backend.models import Coupon, UserCoupon, Package, Shop
from backend.coupon_validators.base_validator import BaseCouponValidator

class ShopRestrictionValidator(BaseCouponValidator):
    """校验优惠券是否适用于当前店铺"""
    def validate(self, coupon: Coupon, user_coupon: UserCoupon, 
                 package: Package, shop: Shop) -> None:
        if coupon.shop_restriction and shop.name != coupon.shop_restriction:
            raise HTTPException(status_code=400, detail=f"该优惠券不适用于店铺 {shop.name}")
