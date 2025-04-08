import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.register import router as register_router
from backend.login import router as login_router
from backend.shops import router as shops_router
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


app = FastAPI(docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(register_router, prefix="/auth", tags=["auth"])
app.include_router(login_router, prefix="/auth", tags=["auth"])
app.include_router(shops_router, prefix="/api", tags=["shops"])


@app.on_event("startup")
async def startup():
    # 自动运行 Alembic 迁移
    subprocess.run(["alembic", "upgrade", "head"])
    await init_db()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    全局异常处理器，用于捕获服务器内部错误。

    Args:
        request (Request): 请求对象。
        exc (Exception): 异常对象。

    Returns:
        JSONResponse: 包含错误信息的 JSON 响应。
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )