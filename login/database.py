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

# 处理特殊字符
password = quote_plus("Aa8629473@")

# MySQL 连接
SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://root:{password}@localhost:3306/xiaozhongdianping"

# 创建异步数据库引擎
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 创建会话
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# 初始化数据库
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
