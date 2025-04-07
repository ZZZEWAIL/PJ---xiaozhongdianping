# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from backend.database import init_db
# from backend.register import router as register_router
# from backend.login import router as login_router
# from backend.shops import router as shops_router

# app = FastAPI(docs_url="/docs", redoc_url="/redoc")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://127.0.0.1:5500"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(register_router, prefix="/auth", tags=["auth"])
# app.include_router(login_router, prefix="/auth", tags=["auth"])
# app.include_router(shops_router, prefix="/api", tags=["shops"])

# @app.on_event("startup")
# async def startup():
#     await init_db()

import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.register import router as register_router
from backend.login import router as login_router
from backend.shops import router as shops_router

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