from pydantic import BaseModel

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
    name_pinyin: str # 新增
    category_pinyin: str  # 新增
    address: str
    phone: str
    business_hours: str
    image_url: str | None

    class Config:
        from_attributes = True