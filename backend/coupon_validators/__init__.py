# backend/coupon_validators/__init__.py
from backend.coupon_validators.expiry_validator import ExpiryValidator
from backend.coupon_validators.threshold_validator import ThresholdValidator
from backend.coupon_validators.shop_validator import ShopRestrictionValidator
from backend.coupon_validators.category_validator import CategoryValidator
from backend.coupon_validators.status_validator import StatusValidator

# 按顺序注册所有优惠券校验器
_coupon_validators = [
    StatusValidator(),
    ExpiryValidator(),
    ThresholdValidator(),
    ShopRestrictionValidator(),
    CategoryValidator(),
]

def run_coupon_validators(coupon, user_coupon, package, shop) -> None:
    """依次运行所有优惠券校验器，一旦有校验不通过则抛出异常终止"""
    for validator in _coupon_validators:
        validator.validate(coupon, user_coupon, package, shop)
