from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from login.database import init_db
from login.register import router as register_router  # 引入 register.py 中的路由
from login.login import router as login_router  # 引入 login.py 中的路由

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # 允许前端端口
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法，包括 OPTIONS 和 POST
    allow_headers=["*"],  # 允许所有头部
)

# 将登录功能和注册功能路由添加到应用中
app.include_router(register_router, prefix="/auth", tags=["auth"])
app.include_router(login_router, prefix="/auth", tags=["auth"])

# 启动时调用数据库初始化
@app.on_event("startup")
async def startup():
    await init_db()