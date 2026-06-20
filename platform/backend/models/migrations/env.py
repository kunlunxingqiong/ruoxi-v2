"""
🌸 若曦V2 - Alembic 迁移环境配置
数据库迁移环境设置
"""

from logging.config import fileConfig
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from sqlalchemy import engine_from_config, pool
from alembic import context

# 导入模型基类和所有模型
from models.database import Base
from models.database import (
    User, BloodPressureRecord, GlucoseRecord, WeightRecord,
    SleepRecord, HeartRateRecord, Medication, MedicationLog,
    HealthGoal, ChatMessage, Memory, Notification
)

# 这是Alembic配置对象
config = context.config

# 解释配置文件中的Python日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
# 这是模型元的'Alembic支持版本'
target_metadata = Base.metadata

# 从环境变量获取数据库URL
def get_url():
    import os
    return os.getenv("DATABASE_URL", "postgresql://ruoxi:ruoxi@localhost:5432/ruoxi")


def run_migrations_offline() -> None:
    """以离线模式运行迁移"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """以在线模式运行迁移"""
    # 覆盖配置中的sqlalchemy.url
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 比较列类型
            compare_server_default=True,  # 比较默认值
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
