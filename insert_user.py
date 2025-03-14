# This script inserts test users into the database. Run when adding new test data.

import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker
from login.database import engine, async_session
from login.models import User
import bcrypt as bc

async def insert_user():
    async with async_session() as session:
        async with session.begin():
            # 创建用户
            salt = bc.gensalt().decode('utf-8')
            password_hash = bc.hashpw("111".encode('utf-8'), salt.encode('utf-8'))
            user = User(username="Ada", password_hash=password_hash.decode('utf-8'))
            session.add(user)
        await session.commit()

asyncio.run(insert_user())