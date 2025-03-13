# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

# SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://root:Aa8629473%40@localhost:3306/xiaozhongdianping"

# engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
# async_session = async_sessionmaker(engine, expire_on_commit=False)

# Base = declarative_base()

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 使用 Aiven 提供的 Service URI
SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://avnadmin:AVNS_KxXI48LMviHdSHRmELj@xiaozhongdianping-xiaozhongdianping.h.aivencloud.com:14983/defaultdb"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()