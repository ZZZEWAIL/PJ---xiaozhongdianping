from fastapi import APIRouter, HTTPException, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database import get_db
from backend.models import User
from backend.schema import LoginForm, Token, UserStatus
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
    finally:
        await db.commit()  # 提交事务
        await db.close()   # 关闭数据库连接
    
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
            samesite="Lax",  # 改为 Lax，确保跨域请求携带 Cookie
            max_age=1800,
            path="/",
        )

        await session.commit()  # 提交事务
        
        return {"access_token": token, "token_type": "bearer"}
    
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/status", response_model=UserStatus)
async def get_login_status(current_user: Dict[str, any] = Depends(get_current_user)):
    """
    Check user login status and return user information.

    Returns:
        UserStatus: Containing user ID and username.
    """
    return UserStatus(id=current_user["id"], username=current_user["username"])