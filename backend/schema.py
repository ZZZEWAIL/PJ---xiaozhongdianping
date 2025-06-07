from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
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
    invitation_code: str | None = None  # 新增


class OrderCreated(BaseModel):
    """
    创建订单成功后返回的数据
    """
    id: int               # 订单 ID
    voucher_code: str     # 随机生成的 16 位券码
    order_amount: float   # 优惠后的实付金额
    created_at: datetime  # 下单时间

class OrderListResponse(BaseModel):
    """
    用户订单列表响应，包含分页信息
    """
    page: int
    total_pages: int
    data: List[Order]


# ---------------- 优惠券相关 ---------------- #
class Coupon(BaseModel):
    """
    Coupon schema for API responses
    """
    id: int
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    min_spend: float = 0
    max_discount: Optional[float] = None
    category: Optional[str] = None 
    shop_restriction: Optional[str] = None
    expiry_type: Optional[str] = None
    expiry_date: Optional[datetime] = None
    valid_days: Optional[int] = None
    total_quantity: Optional[int] = None
    remaining_quantity: Optional[int] = None

    class Config:
        from_attributes = True


class UserCouponInfo(BaseModel):
    """
    User coupon info with status and expiry info
    """
    id: int
    status: str  # unused / used / expired
    expires_at: Optional[datetime] = None
    coupon: Coupon

    class Config:
        from_attributes = True


class CouponListResponse(BaseModel):
    """
    Response model for listing user coupons categorized by status
    """
    unused: List[UserCouponInfo]
    used: List[UserCouponInfo]
    expired: List[UserCouponInfo]


class NewUserCouponDTO(BaseModel):
    """
    DTO for new user coupons available for selection
    """
    id: int
    type: str  # kfc, milk_tea, or discount
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    min_spend: float = 0
    max_discount: Optional[float] = None
    category: Optional[str] = None
    shop_restriction: Optional[str] = None
    valid_days: Optional[int] = None
    remaining: str  # "剩余xxx张" or "已发完"


class NewUserCouponResponse(BaseModel):
    """
    Response model for new user coupon listing
    """
    eligible: bool  # Whether the user is eligible to claim a new user coupon
    coupons: List[NewUserCouponDTO] = []

class UserStatus(BaseModel):
    """
    Response model for user login status
    """
    id: int
    username: str

# ---------- review创建请求模型 ----------

class ReviewCreate(BaseModel):
    """
    创建点评时使用
    """
    content: str


class ReviewReplyCreate(BaseModel):
    """
    创建回复时使用
    """
    content: str
    parent_reply_id: Optional[int] = None


# ---------- review响应模型 ----------

class ReviewReplyResponse(BaseModel):
    """
    回复返回结构（支持递归嵌套）
    """
    id: int
    review_id: int
    user_id: int
    username: str  # 新增回复人用户名
    content: str
    created_at: datetime
    parent_reply_id: Optional[int] = None
    replies: List["ReviewReplyResponse"] = []  # 子回复列表

    class Config:
        orm_mode = True


ReviewReplyResponse.update_forward_refs()  # 处理自引用

class ReviewReward(BaseModel):
    """
    奖励券信息结构
    """
    coupon_name: str
    coupon_value: str
    expiry_days: int


class ReviewResponse(BaseModel):
    """
    点评返回结构
    """
    id: int
    user_id: int
    username: str  # 新增点评人用户名
    shop_id: int
    content: str
    created_at: datetime
    replies: List[ReviewReplyResponse] = []  # 根级回复列表
    reward: Optional[ReviewReward] = None  # 奖励券信息（可选）

    class Config:
        orm_mode = True

# ---------- invitation 相关模型 ----------
class InvitationCodeRequest(BaseModel):
    code: str

class RewardCoupon(BaseModel):
    id: int
    name: str
    value: float
    type: str
    description: Optional[str] = None
    issued_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: str