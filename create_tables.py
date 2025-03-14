# This script creates database tables (e.g., users table). Run only when initializing or resetting the database.

import asyncio
from login.database import engine, Base

async def create_tables():
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")

asyncio.run(create_tables())