from pydantic import BaseModel
from datetime import datetime
from backend.models import DiscountType, ExpiryType, CouponStatus

class LoginForm(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Shop(BaseModel):
    id: int
    name: str
    category: str
    rating: float
    price_range: str
    avg_cost: float
    name_pinyin: str
    category_pinyin: str
    address: str
    phone: str
    business_hours: str
    image_url: str | None

    class Config:
        from_attributes = True

class Package(BaseModel):
    id: int
    title: str
    price: float
    description: str | None
    contents: str
    sales: int

    class Config:
        from_attributes = True

# ---------------- 订单相关 ---------------- #
class Order(BaseModel):
    """
    订单列表/详情返回的公共字段
    """
    package_title: str
    created_at: datetime
    shop_name: str
    order_id: int # 订单 ID
    voucher_code: str | None = None  # 仅在详情页返回

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """
    创建订单时客户端提交的请求体
    """
    package_id: int
    coupon_id: int | None = None  # 可选：使用的优惠券


class OrderCreated(BaseModel):
    """
    创建订单成功后返回的数据
    """
    id: int               # 订单 ID
    voucher_code: str     # 随机生成的 16 位券码
    order_amount: float   # 优惠后的实付金额
    created_at: datetime  # 下单时间


# ---------------- 优惠券相关 ---------------- #
class Coupon(BaseModel):
    """
    优惠券基本字段（与 Coupon ORM 映射）
    """
    id: int
    name: str
    description: str | None = None
    discount_type: str
    discount_value: float
    min_spend: float
    max_discount: float | None = None
    category: str | None = None
    shop_restriction: str | None = None
    expiry_date: datetime | None = None
    total_quantity: int | None = None
    remaining_quantity: int | None = None
    per_user_limit: int | None = None

    class Config:
        from_attributes = True


class UserCouponInfo(BaseModel):
    """
    用户卡包中单张券的信息（含状态）
    """
    id: int
    status: str               # unused / used / expired
    expires_at: datetime | None = None
    coupon: Coupon            # 嵌套优惠券基本信息

    class Config:
        from_attributes = True


class CouponListResponse(BaseModel):
    """
    /user/coupons 返回的结构：按状态分类
    """
    unused: list[UserCouponInfo]
    used: list[UserCouponInfo]
    expired: list[UserCouponInfo]