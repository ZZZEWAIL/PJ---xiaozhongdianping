import asyncio
from login_module.database import engine, Base
from login_module.models import User  # 确保导入模型

async def create_tables():
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")

asyncio.run(create_tables())