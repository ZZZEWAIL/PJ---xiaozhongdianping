from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.models import Base
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 本地数据库连接字符串
# SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://testuser:testpassword@127.0.0.1:3306/testdb"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 创建异步引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True
)

# 创建异步会话工厂
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# 初始化数据库（创建表）
async def init_db():
    async with engine.begin() as conn:
        # 使用 Base.metadata.create_all 创建所有表
        await conn.run_sync(Base.metadata.create_all)

# 获取数据库会话
async def get_db():
    async with async_session() as session:
        yield session