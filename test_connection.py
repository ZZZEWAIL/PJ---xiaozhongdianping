import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://root:Aa8629473%40@localhost:3306/xiaozhongdianping"

async def test_connection():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(result.fetchone())
    await engine.dispose()

asyncio.run(test_connection())