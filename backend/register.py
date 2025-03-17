# import datetime
# from fastapi import APIRouter, HTTPException, Depends
# import jwt
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from pydantic import BaseModel
# import re
# import bcrypt
# from backend.database import get_db
# from backend.models import User
# from backend.schema import Token
# from backend.utils import generate_captcha
# import os
# from dotenv import load_dotenv

# load_dotenv()

# router = APIRouter()

# # 用户注册请求体
# class RegisterForm(BaseModel):
#     username: str
#     password: str
#     captcha: str

# # 用户名和密码格式验证
# def validate_username(username: str):
#     if not re.match("^[A-Za-z0-9_]{4,20}$", username):
#         raise HTTPException(status_code=400, detail="Invalid username. It should only contain letters, numbers, and underscores, and be between 4 and 20 characters.")

# def validate_password(password: str):
#     if len(password) < 6 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
#         raise HTTPException(status_code=400, detail="Password must be at least 6 characters long and contain both letters and numbers.")

# # 临时存储验证码（生产环境中应使用 Redis 或数据库）
# captcha_store = {}

# # 获取验证码端点
# @router.get("/captcha")
# async def get_captcha():
#     captcha_text, img_str = generate_captcha()
#     captcha_store['captcha'] = captcha_text  # 存储验证码
#     return {"captcha_image": f"data:image/png;base64,{img_str}"}

# @router.post("/register", response_model=Token)
# async def register(form: RegisterForm, db: AsyncSession = Depends(get_db)):
#     # 校验用户名格式
#     validate_username(form.username)

#     # 校验密码格式
#     validate_password(form.password)

#     # 验证验证码
#     if 'captcha' not in captcha_store or form.captcha.upper() != captcha_store['captcha'].upper():
#         raise HTTPException(status_code=400, detail="Invalid captcha")
#     del captcha_store['captcha']  # 使用后删除

#     # 检查用户名是否已存在
#     result = await db.execute(select(User).where(User.username == form.username))
#     existing_user = result.scalar()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already exists")

#     # 加密密码
#     password_hash = bcrypt.hashpw(form.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

#     # 创建新用户并保存到数据库
#     new_user = User(username=form.username, password_hash=password_hash)
#     db.add(new_user)
#     await db.commit()

#     # 生成 JWT 令牌
#     payload = {
#         "username": form.username,
#         "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
#     }
#     secret_key = os.getenv("SECRET_KEY")
#     token = jwt.encode(payload, secret_key, algorithm="HS256")

#     return {"access_token": token, "token_type": "bearer"}

import datetime
from fastapi import APIRouter, HTTPException, Depends
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import re
import bcrypt
from backend.database import get_db
from backend.models import User
from backend.schema import Token
from backend.utils import generate_captcha
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

class RegisterForm(BaseModel):
    username: str
    password: str
    captcha: str

def validate_username(username: str):
    if not re.match("^[A-Za-z0-9_]{4,20}$", username):
        raise HTTPException(status_code=400, detail="用户名无效。只能包含字母、数字和下划线，长度在 4 到 20 位之间。")

def validate_password(password: str):
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码长度必须至少 6 位。")
    if not re.search(r"[A-Za-z]", password):
        raise HTTPException(status_code=400, detail="密码必须包含字母。")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="密码必须包含数字。")

captcha_store = {}

@router.get("/captcha")
async def get_captcha():
    captcha_text, img_str = generate_captcha()
    captcha_store['captcha'] = captcha_text
    return {"captcha_image": f"data:image/png;base64,{img_str}"}

@router.post("/register", response_model=Token)
async def register(form: RegisterForm, db: AsyncSession = Depends(get_db)):
    validate_username(form.username)
    validate_password(form.password)

    if 'captcha' not in captcha_store or form.captcha.upper() != captcha_store['captcha'].upper():
        raise HTTPException(status_code=400, detail="验证码错误。")
    del captcha_store['captcha']

    result = await db.execute(select(User).where(User.username == form.username))
    existing_user = result.scalar()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在。")

    password_hash = bcrypt.hashpw(form.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(username=form.username, password_hash=password_hash)
    db.add(new_user)
    await db.commit()

    payload = {
        "username": form.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    secret_key = os.getenv("SECRET_KEY")
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    return {"access_token": token, "token_type": "bearer"}