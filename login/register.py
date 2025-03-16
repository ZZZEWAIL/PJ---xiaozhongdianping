import datetime
from fastapi import APIRouter, HTTPException, Depends
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import re
import bcrypt
from login.database import get_db  # 从 database.py 导入 get_db
from login.models import User
from login.schema import Token
from login.utils import generate_captcha  # 用于生成验证码
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# 用户注册请求体
class RegisterForm(BaseModel):
    username: str
    password: str
    captcha: str

# 用户名和密码格式验证
def validate_username(username: str):
    if not re.match("^[A-Za-z0-9_]{4,20}$", username):
        raise HTTPException(status_code=400, detail="Invalid username. It should only contain letters, numbers, and underscores, and be between 4 and 20 characters.")

def validate_password(password: str):
    if len(password) < 6 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long and contain both letters and numbers.")

# 注册 API
@router.post("/register", response_model=Token)
async def register(form: RegisterForm, db: AsyncSession = Depends(get_db)):
    # 校验用户名格式
    validate_username(form.username)

    # 校验密码格式
    validate_password(form.password)

    # 验证验证码
    captcha_text, _ = generate_captcha()  # 生成验证码
    if form.captcha != captcha_text:
        raise HTTPException(status_code=400, detail="Invalid captcha")

    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == form.username))
    existing_user = result.scalar()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # 加密密码
    password_hash = bcrypt.hashpw(form.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 创建新用户并保存到数据库
    new_user = User(username=form.username, password_hash=password_hash)
    db.add(new_user)
 