"""
🌸 若曦V2 数据库模型设计
使用SQLAlchemy ORM，支持SQLite/PostgreSQL
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# 尝试导入SQLAlchemy
try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Column,
        DateTime,
        Float,
        ForeignKey,
        Index,
        Integer,
        String,
        Text,
        create_engine,
    )
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import declarative_base, relationship, sessionmaker

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

    # 创建模拟基类
    class FakeBase:
        def __init_subclass__(cls):
            pass

    declarative_base = lambda: FakeBase

from .config_manager import config

Base = declarative_base()


class User(Base):
    """
    用户表 - 若曦的使用者
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    nickname = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime)

    # 偏好设置 (JSON存储)
    preferences = Column(JSON, default=dict)

    # 关联
    conversations = relationship("Conversation", back_populates="user")
    memories = relationship("Memory", back_populates="user")
    health_records = relationship("HealthRecord", back_populates="user")


class Conversation(Base):
    """
    对话表 - 与若曦的聊天记录
    """

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(64), unique=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

    # 对话元信息
    title = Column(String(200), default="")  # 自动生成的话题
    message_count = Column(Integer, default=0)

    # 关联
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", order_by="Message.timestamp"
    )


class Message(Base):
    """
    消息表 - 单条聊天内容
    """

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer, ForeignKey("conversations.id"), nullable=False, index=True
    )

    # 消息内容
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # 若曦特有：情感分析
    emotion = Column(String(20), default="")  # 若曦回复时的情绪
    context_used = Column(Boolean, default=False)  # 是否使用了上下文

    # AI信息
    model_used = Column(String(50), default="")  # 使用的模型
    tokens_used = Column(Integer, default=0)  # Token消耗
    response_time = Column(Float, default=0.0)  # 响应时间(秒)

    # 关联
    conversation = relationship("Conversation", back_populates="messages")


class Memory(Base):
    """
    记忆表 - 若曦的长期记忆系统
    """

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 记忆类型
    memory_type = Column(String(30), nullable=False, index=True)  #
    # - 'fact': 事实记忆 (用户喜欢什么、职业等)
    # - 'event': 事件记忆 (今天做了什么、上次聊了什么)
    # - 'preference': 偏好记忆 (喜欢的颜色、食物等)
    # - 'emotion': 情感记忆 (之前的情绪状态)
    # - 'goal': 目标记忆 (健康目标、学习计划等)

    # 记忆内容
    content = Column(Text, nullable=False)
    summary = Column(String(500), default="")  # 简短摘要（用于快速检索）

    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 记忆重要性 (0-100，越高越重要)
    importance = Column(Float, default=50.0, index=True)

    # 关联
    user = relationship("User", back_populates="memories")

    # 索引：复合索引加速记忆检索
    __table_args__ = (
        Index("idx_memory_user_type", "user_id", "memory_type"),
        Index("idx_memory_importance", "user_id", "importance"),
    )


class HealthRecord(Base):
    """
    健康记录表 - 若曦的健康管理功能
    """

    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 记录类型
    record_type = Column(String(50), nullable=False, index=True)  #
    # - 'blood_pressure': 血压
    # - 'blood_glucose': 血糖
    # - 'weight': 体重
    # - 'sleep': 睡眠
    # - 'exercise': 运动
    # - 'medication': 用药
    # - 'checkup': 体检

    # 记录数据 (JSON存储，根据类型不同)
    data = Column(JSON, nullable=False)

    # 原始值举例:
    # blood_pressure: {"systolic": 120, "diastolic": 80, "pulse": 72}
    # weight: {"value": 65.5, "unit": "kg", "bmi": 22.3}
    # sleep: {"duration": 7.5, "quality": "good", "bed_time": "23:00"}

    # 记录时间
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 若曦的分析和建议
    analysis = Column(Text, default="")
    suggestions = Column(JSON, default=list)  # 建议列表

    # 关联
    user = relationship("User", back_populates="health_records")


class AIModelUsage(Base):
    """
    AI模型使用记录 - 成本追踪和优化
    """

    __tablename__ = "ai_model_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 使用的模型
    provider = Column(
        String(30), nullable=False
    )  # 'gemini', 'groq', 'together', 'ollama'
    model = Column(String(50), nullable=False)

    # 使用量
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # 成本 (美元)
    estimated_cost = Column(Float, default=0.0)

    # 响应时间
    response_time_ms = Column(Integer, default=0)

    # 结果
    success = Column(Boolean, default=True)
    error_message = Column(String(500), default="")

    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ========== 数据库管理器 ==========


class DatabaseManager:
    """
    数据库管理器 - 统一数据库操作
    """

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None and SQLALCHEMY_AVAILABLE:
            self._init_engine()

    def _init_engine(self):
        """初始化数据库引擎"""
        db_type = config.get("database.type", "sqlite")

        if db_type == "sqlite":
            db_path = config.get("database.path", "data/ruoxi.db")
            # 确保目录存在
            import os

            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self._engine = create_engine(f"sqlite:///{db_path}")
        elif db_type == "postgresql":
            # 生产环境使用PostgreSQL
            db_url = config.get("database.url")
            self._engine = create_engine(db_url)

        # 创建表
        Base.metadata.create_all(self._engine)

        # 创建会话工厂
        self._session_factory = sessionmaker(bind=self._engine)

    def get_session(self):
        """获取数据库会话"""
        if self._session_factory is None:
            return None
        return self._session_factory()

    def create_tables(self):
        """创建所有表"""
        if self._engine:
            Base.metadata.create_all(self._engine)


# 全局数据库实例
db = DatabaseManager()


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 数据库模型")
    print("=" * 60)

    if not SQLALCHEMY_AVAILABLE:
        print("\n⚠️ SQLAlchemy未安装，请先安装: pip install sqlalchemy")
        print("\n✅ 但模型设计已完成，可查看源码")
    else:
        print("\n【已定义模型】")
        print("  - User: 用户表")
        print("  - Conversation: 对话表")
        print("  - Message: 消息表")
        print("  - Memory: 记忆表")
        print("  - HealthRecord: 健康记录表")
        print("  - AIModelUsage: AI使用记录表")

        print("\n【创建数据库】")
        db.create_tables()
        print("  ✅ 表已创建")

        print("\n数据库路径:", config.get("database.path"))

    print("\n" + "=" * 60)
