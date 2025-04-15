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

# 创建同步会话工厂（新增）
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def create_database():
    """检查并创建数据库（如果不存在）"""
    database_name = SQLALCHEMY_DATABASE_URL.split("/")[-1]
    with sync_engine.connect() as connection:
        # 使用 text() 包装 SQL 字符串
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database_name}"))
        connection.execute(text(f"USE {database_name}"))

async def init_db():
    """初始化数据库"""
    create_database()  # 确保数据库存在
    async with engine.begin() as conn:
        # 创建表
        await conn.run_sync(Base.metadata.create_all)

        # 执行 SQL 文件
        sql_file_path = os.path.join(os.path.dirname(__file__), "../sql/init_data.sql")
        with open(sql_file_path, "r", encoding="utf-8") as file:
            sql_script = file.read()
        
        # 分割 SQL 脚本并逐条执行
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:  # 跳过空语句
                await conn.execute(text(statement))  # 使用 text() 包装 SQL 语句

# 定义 get_db 方法
async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        yield session