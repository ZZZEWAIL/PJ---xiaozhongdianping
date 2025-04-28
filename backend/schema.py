from pydantic import BaseModel
from datetime import datetime

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

class Order(BaseModel):
    package_title: str
    created_at: datetime
    shop_name: str
    voucher_code: str | None = None  # 仅在订单详情中返回

    class Config:
        from_attributes = True