import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.register import router as register_router
from backend.login import router as login_router
from backend.shops import router as shops_router
from backend.filter_sort import router as filter_sort_router
from backend.orders import router as orders_router
from backend.coupons import router as coupons_router
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
app.include_router(filter_sort_router, prefix="/api", tags=["filter_sort"])
app.include_router(orders_router,   prefix="/api",  tags=["orders"])
app.include_router(coupons_router,  prefix="/api",  tags=["coupons"])


@app.on_event("startup")
async def startup():
    # 自动运行 Alembic 迁移
    subprocess.run(["alembic", "upgrade", "head"])
    print("Starting database initialization...")
    await init_db()
    print("Database initialization completed.")

    # 通过观察者模式注册监听
    from backend.order_observers import (
        register_observer,
        PackageSalesObserver,
        CouponUsageObserver
    )
    register_observer(PackageSalesObserver())  # 订单创建后更新销量
    register_observer(CouponUsageObserver())   # 订单创建后更新券状态

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