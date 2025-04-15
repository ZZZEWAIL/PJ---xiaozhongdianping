import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from alembic import context
from dotenv import load_dotenv
from backend.models import Base
from backend.database import DATABASE_URL_SYNC

# 加载环境变量
load_dotenv()

# 这是在 alembic.ini 中定义的配置
config = context.config

# 加载日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置数据库 URL（使用同步 URL）
config.set_main_option("sqlalchemy.url", DATABASE_URL_SYNC)

# 连接到数据库
connectable = engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)

# 运行迁移
with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        render_as_batch=True,  # 启用批量模式，适用于 MySQL
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()