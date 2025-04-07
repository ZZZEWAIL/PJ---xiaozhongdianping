import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

# 本地数据库连接字符串
DATABASE_URL = "mysql+aiomysql://testuser:testpassword@127.0.0.1:3306/testdb"

async def test_connection():
    # 创建异步引擎
    engine = create_async_engine(
        DATABASE_URL,
        echo=True
    )
    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("Database connection successful!")
            print("Result:", result.scalar())
    except Exception as e:
        print("Database connection failed:", e)
    finally:
        await engine.dispose()

asyncio.run(test_connection())