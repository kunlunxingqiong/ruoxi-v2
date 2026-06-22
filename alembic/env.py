"""
🌸 若曦V2 Alembic 环境配置
数据库迁移运行环境
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入模型
from core.database_models import Base
from core.database_models import config as app_config

# this is the Alembic Config object
config = context.config

# 从若曦配置获取数据库URL
db_url = app_config.get("database.url")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)
else:
    # 使用SQLite作为默认
    db_path = app_config.get("database.path", "data/ruoxi.db")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的MetaData对象
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移 (生成SQL脚本)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移 (直接操作数据库)"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
