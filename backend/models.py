from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy import ForeignKey

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(100))
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
    address = Column(String(200))
    phone = Column(String(20))
    business_hours = Column(String(50))
    image_url = Column(String(255), nullable=True)

# 存储用户的搜索历史
class SearchHistory(Base):
    __tablename__ = 'search_history'
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=True)  # 可选：关联用户
    searched_at = Column(DateTime, default=datetime.datetime.utcnow)

class ShopImage(Base):
    __tablename__ = 'shop_images'
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    image_url = Column(String(255), nullable=False)