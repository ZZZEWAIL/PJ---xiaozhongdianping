from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.future import select
from login_module.database import async_session
from login_module.models import User
from login_module.schema import LoginForm, Token
import bcrypt as bc
import jwt
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import os

load_dotenv()  # 加载环境变量

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

async def get_db():
    async with async_session() as session:
        yield session

@app.post("/login")
async def login(form: LoginForm, db: AsyncSession = Depends(get_db)):
    async with db as session:
        result = await session.execute(select(User).where(User.username == form.username))
        user = result.scalar()
        if not user:
            print("User not found")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not bc.checkpw(form.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            print("Invalid password")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        payload = {
            "username": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        secret_key = os.getenv("SECRET_KEY")  # 从环境变量中获取密钥
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return {"access_token": token, "token_type": "bearer"}