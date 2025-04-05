from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Business(Base):
    __tablename__ = 'businesses'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))  # 商家名称
    rating = Column(Float)  # 商家评分
    price = Column(Float)  # 商家价格
    avg_spend = Column(Float)  # 商家人均消费
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  # 商家创建时间