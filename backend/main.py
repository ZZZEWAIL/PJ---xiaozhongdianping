from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.register import router as register_router  # 更新导入
from backend.login import router as login_router  # 更新导入
from backend.filter_sort import router as filter_sort_router

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 将登录功能和注册功能路由添加到应用中
app.include_router(register_router, prefix="/auth", tags=["auth"])
app.include_router(login_router, prefix="/auth", tags=["auth"])
app.include_router(filter_sort_router, prefix="/business", tags=["business"])

# 启动时调用数据库初始化
@app.on_event("startup")
async def startup():
    await init_db()