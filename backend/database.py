from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.future import select
from urllib.parse import quote_plus
from backend.models import Base, Shop
from dotenv import load_dotenv
import os

load_dotenv()
password = os.getenv("DATABASE_PASSWORD")
SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://avnadmin:{password}@xiaozhongdianping-xiaozhongdianping.h.aivencloud.com:14983/defaultdb"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async with async_session() as session:
            with open("sql/init_data.sql", "r") as file:
                sql_script = file.read()
            sql_statements = []
            for line in sql_script.splitlines():
                line = line.strip()
                if line and not line.startswith("--"):
                    sql_statements.append(line)
            sql_script = " ".join(sql_statements)
            sql_statements = sql_script.split(";")

            for statement in sql_statements:
                statement = statement.strip()
                if statement:
                    await session.execute(text(statement))
            await session.commit()

async def get_db():
    async with async_session() as session:
        yield session