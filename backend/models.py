from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
import datetime
import enum


Base = declarative_base()

# 枚举类型定义
class DiscountType(enum.Enum):
    deduction = "deduction"  # 减固定金额（如满100减20）
    fixed_amount = "fixed_amount"  # 减到固定金额（如15元内免单）
    discount = "discount"  # 折扣券（如9折）

class ExpiryType(enum.Enum):
    fixed_date = "fixed_date"  # 固定截止日期
    valid_days = "valid_days"  # 领取后有效天数
    unlimited = "unlimited"  # 无限期

class CouponStatus(enum.Enum):
    unused = "unused"  # 未使用
    used = "used"  # 已使用
    expired = "expired"  # 已过期

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(100))
    invitation_code = Column(String(6), unique=True, nullable=False)  # 新增
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Shop(Base):
    __tablename__ = 'shops'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, unique=True)
    category = Column(String(50))
    rating = Column(Float)
    price_range = Column(String(20))
    avg_cost = Column(Float)
    name_pinyin = Column(String(100), index=True)
    category_pinyin = Column(String(50), index=True)
    address = Column(String(200))
    phone = Column(String(20))
    business_hours = Column(String(50))
    image_url = Column(String(255), nullable=True)

class SearchHistory(Base):
    __tablename__ = 'search_history'
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=True)
    searched_at = Column(DateTime, default=datetime.datetime.utcnow)

class ShopImage(Base):
    __tablename__ = 'shop_images'
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    image_url = Column(String(255), nullable=False)

class Package(Base):
    __tablename__ = 'packages'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    contents = Column(String(255), nullable=False)  # 例如 "汉堡*2+可乐*2"
    sales = Column(Integer, default=0)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)

class Coupon(Base):
    __tablename__ = 'coupons'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Float, nullable=False)  # 折扣值：如 20（减20元）、15（免单最高15元）、0.9（9折）
    min_spend = Column(Float, default=0)  # 使用门槛，如 100（满100可用）
    max_discount = Column(Float, nullable=True)  # 最大抵扣金额
    category = Column(String(50), nullable=True)  # 适用品类
    shop_restriction = Column(String(100), nullable=True)  # 适用店铺
    expiry_type = Column(Enum(ExpiryType), nullable=True)  # 失效类型
    expiry_date = Column(DateTime, nullable=True)  # 固定截止日期
    valid_days = Column(Integer, nullable=True)  # 有效天数
    total_quantity = Column(Integer, nullable=True)  # 发放总量
    remaining_quantity = Column(Integer, nullable=True)  # 剩余数量
    per_user_limit = Column(Integer, nullable=True)  # 每人限领张数

class UserCoupon(Base):
    __tablename__ = 'user_coupons'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    coupon_id = Column(Integer, ForeignKey('coupons.id'), nullable=False)
    status = Column(Enum(CouponStatus), default=CouponStatus.unused)
    claimed_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    package_id = Column(Integer, ForeignKey('packages.id'), nullable=False)
    voucher_code = Column(String(16), unique=True, nullable=False)
    coupon_id = Column(Integer, ForeignKey('coupons.id'), nullable=True)
    order_amount = Column(Float, nullable=False)  # 优惠后金额
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ---------------- 邀请码相关 ---------------- #
class InvitationRecord(Base):
    __tablename__ = 'invitation_records'
    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    invited_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    amount = Column(Float, nullable=False)
    order_time = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, default=True)

#review相关模型
class Review(Base):
    """
    点评模型
    """
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)   # 点评人
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)   # 被点评商户
    content = Column(String, nullable=False)                            # 点评内容
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 一对多：一个点评可拥有多条回复
    replies = relationship(
        "ReviewReply",
        back_populates="review",
        cascade="all, delete-orphan",
    )


class ReviewReply(Base):
    """
    回复模型（支持无限嵌套）
    """
    __tablename__ = "review_replies"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)      # 所属点评
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)          # 回复人
    content = Column(String, nullable=False)                                   # 回复内容
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    parent_reply_id = Column(Integer, ForeignKey("review_replies.id"))         # 父回复，可为空

    # 关联：所属点评
    review = relationship("Review", back_populates="replies")
    # 关联：父回复（自关联）
    parent_reply = relationship("ReviewReply", remote_side=[id])
    # 关联：子回复列表（自关联）
    replies = relationship("ReviewReply")
