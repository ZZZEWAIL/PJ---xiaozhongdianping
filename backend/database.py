from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from backend.models import Base
from dotenv import load_dotenv
import os
from sqlalchemy.sql import text

load_dotenv()

# 数据库连接字符串
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL_SYNC = SQLALCHEMY_DATABASE_URL.replace("+aiomysql", "+pymysql")

# 创建异步引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True
)

# 创建同步引擎（用于创建数据库和同步会话）
sync_engine = create_engine(DATABASE_URL_SYNC, echo=True)

# 创建异步会话工厂
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# 创建同步会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def create_database():
    """检查并创建数据库（如果不存在）"""
    database_name = SQLALCHEMY_DATABASE_URL.split("/")[-1]
    with sync_engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database_name}"))
        connection.execute(text(f"USE {database_name}"))

async def init_db():
    """初始化数据库"""
    create_database()
    print("Database created or already exists.")

    async with engine.begin() as conn:
        # 获取当前存在的表
        existing_tables = await conn.run_sync(lambda sync_conn: sync_conn.execute(
            text("SHOW TABLES;")
        ).fetchall())
        existing_tables = [table[0] for table in existing_tables]
        print(f"Existing tables before creation: {existing_tables}")

        # 创建所有表（仅创建不存在的表）
        await conn.run_sync(Base.metadata.create_all)
        print("Table creation completed.")

        # 再次检查表，确保创建成功
        existing_tables = await conn.run_sync(lambda sync_conn: sync_conn.execute(
            text("SHOW TABLES;")
        ).fetchall())
        existing_tables = [table[0] for table in existing_tables]
        print(f"Existing tables after creation: {existing_tables}")

# 定义 get_db 方法
async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        yield session

# 清理异步引擎（避免事件循环问题）
async def close_engine():
    """关闭异步引擎"""
    await engine.dispose()