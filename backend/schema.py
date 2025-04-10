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
    address: str
    phone: str
    business_hours: str
    image_url: str | None
    image_urls: list[str] = []  # 添加图片 URL 列表字段

    class Config:
        from_attributes = True