#!/bin/bash

# 运行 Alembic 迁移
alembic upgrade head

# 启动服务器
uvicorn backend.main:app --reload
