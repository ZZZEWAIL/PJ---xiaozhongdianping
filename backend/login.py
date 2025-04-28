# from fastapi import APIRouter, HTTPException, Depends, Response, Request
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from backend.database import get_db
# from backend.models import User
# from backend.schema import LoginForm
# import bcrypt
# import jwt
# import datetime
# import os
# from dotenv import load_dotenv

# load_dotenv()

# router = APIRouter()

# SECRET_KEY = os.getenv("SECRET_KEY")

# def get_current_user(request: Request):
#     token = request.cookies.get("access_token")
#     if not token:
#         print("No access token found")  # 添加日志
#         raise HTTPException(status_code=401, detail="Not authenticated")
    
#     try:
#         # 打印 SECRET_KEY 和 token
#         print(f"SECRET_KEY used for token verification: {SECRET_KEY}")
#         print(f"Token received: {token}")

#         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         # print(f"Token payload: {payload}")  # 添加日志
#         return payload["username"]
#     except jwt.ExpiredSignatureError:
#         # print("Token has expired")  # 添加日志
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.InvalidTokenError:
#         # print("Invalid token")  # 添加日志
#         raise HTTPException(status_code=401, detail="Invalid token")

# @router.post("/login")
# async def login(form: LoginForm, response: Response, db: AsyncSession = Depends(get_db)):
#     """
#     用户登录接口。

#     Args:
#         form (LoginForm): 包含用户名和密码的登录表单。
#         response (Response): FastAPI 的响应对象，用于设置 Cookie。
#         db (AsyncSession): 数据库会话对象。

#     Returns:
#         dict: 包含登录成功消息的字典。

#     Raises:
#         HTTPException: 如果用户名或密码无效，则抛出 401 错误。
#     """
#     async with db as session:
#         # 查询用户
#         result = await session.execute(select(User).where(User.username == form.username))
#         user = result.scalar()
#         if not user:
#             raise HTTPException(status_code=401, detail="Invalid username or password")
        
#         # 验证密码
#         if not bcrypt.checkpw(form.password.encode('utf-8'), user.password_hash.encode('utf-8')):
#             raise HTTPException(status_code=401, detail="Invalid username or password")
        
#         # 生成 JWT Token
#         payload = {
#             "username": user.username,
#             "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
#         }
#         token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

#         # # 打印 SECRET_KEY 和生成的 token
#         # print(f"SECRET_KEY used for token generation: {SECRET_KEY}")
#         # print(f"Generated token: {token}")
        
#         # 设置 HTTP-only Cookie
#         response.set_cookie(
#             key="access_token",
#             value=token,
#             httponly=True,  # 禁止通过 JavaScript 访问
#             secure=True,    # 在生产环境中启用 HTTPS
#             samesite="Strict",  # 防止跨站请求伪造 (CSRF)
#             max_age=1800    # 设置 Cookie 的有效期（30 分钟）
#         )
        
#         return {"message": "Login successful"}
    
# @router.post("/logout")
# async def logout(response: Response):
#     """
#     用户登出接口。

#     Args:
#         response (Response): FastAPI 的响应对象，用于清除 Cookie。

#     Returns:
#         dict: 包含登出成功消息的字典。
#     """
#     # 清除 access_token Cookie
#     response.delete_cookie("access_token")
#     return {"message": "Logged out successfully"}

# @router.get("/protected-endpoint")
# async def protected_endpoint(current_user: str = Depends(get_current_user)):
#     return {"username": current_user}

from fastapi import APIRouter, HTTPException, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.models import User
from backend.schema import LoginForm, Token
from typing import Dict
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, any]:
    token = request.cookies.get("access_token")
    if not token:
        print("No access token found in cookies")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        print(f"SECRET_KEY used for token verification: {SECRET_KEY}")
        print(f"Token received: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")  # sub 是字符串
        username: str = payload.get("username")
        print(f"Decoded payload: {payload}")
        if user_id is None or username is None:
            print("Token payload missing 'sub' or 'username'")
            raise HTTPException(status_code=401, detail="Invalid token")

        # 将 user_id 转换为整数
        try:
            user_id = int(user_id)
        except ValueError:
            print("Token 'sub' is not a valid integer")
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar()
        if not user:
            print(f"User with id {user_id} not found in database")
            raise HTTPException(status_code=401, detail="User not found")

        return {"id": user.id, "username": user.username}
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidSignatureError:
        print("Invalid signature")
        raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError as e:
        print(f"Invalid token error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
@router.post("/login", response_model=Token)
async def login(form: LoginForm, response: Response, db: AsyncSession = Depends(get_db)):
    async with db as session:
        result = await session.execute(select(User).where(User.username == form.username))
        user = result.scalar()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not bcrypt.checkpw(form.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        print(f"SECRET_KEY used for token generation: {SECRET_KEY}")
        payload = {
            "sub": str(user.id),  # 转换为字符串
            "username": user.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=1800,
            path="/"
        )
        
        return {"access_token": token, "token_type": "bearer"}
    
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/protected-endpoint")
async def protected_endpoint(current_user: Dict[str, any] = Depends(get_current_user)):
    return {"username": current_user["username"], "id": current_user["id"]}