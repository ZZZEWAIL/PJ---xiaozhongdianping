from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from login.database import get_db  # 从 database.py 导入 get_db
from login.models import User
from login.schema import LoginForm, Token
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# 登录 API
@router.post("/login", response_model=Token)
async def login(form: LoginForm, db: AsyncSession = Depends(get_db)):
    async with db as session:
        result = await session.execute(select(User).where(User.username == form.username))
        user = result.scalar()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not bcrypt.checkpw(form.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        payload = {
            "username": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        secret_key = os.getenv("SECRET_KEY")
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return {"access_token": token, "token_type": "bearer"}