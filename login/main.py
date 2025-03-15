from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from login.database import async_session
from login.models import User
from login.schema import LoginForm, Token
import bcrypt as bc
import jwt
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # 允许前端的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法（包括 OPTIONS）
    allow_headers=["*"],  # 允许所有头部
)

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
        secret_key = os.getenv("SECRET_KEY")
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return {"access_token": token, "token_type": "bearer"}