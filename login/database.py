# 使用云数据库
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

# # 使用 Aiven 提供的 Service URI
# SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://avnadmin:AVNS_KxXI48LMviHdSHRmELj@xiaozhongdianping-xiaozhongdianping.h.aivencloud.com:14983/defaultdb"

# engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
# async_session = async_sessionmaker(engine, expire_on_commit=False)

# Base = declarative_base()

# 使用本地数据库
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
from login.models import Base  # 确保导入 User 模型
from dotenv import load_dotenv
import os

# MySQL 连接
load_dotenv()
password = os.getenv("DATABASE_PASSWORD")
SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://avnadmin:{password}@xiaozhongdianping-xiaozhongdianping.h.aivencloud.com:14983/defaultdb"

# 创建异步数据库引擎
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 创建会话
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# 初始化数据库
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with async_session() as session:
        yield session
