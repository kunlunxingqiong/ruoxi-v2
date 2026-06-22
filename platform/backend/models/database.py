"""
🌸 若曦V2 - 数据库模型
SQLAlchemy ORM模型定义
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.sql import func

# 创建基类
Base = declarative_base()


# ==================== 枚举类型 ====================


class UserRole(enum.Enum):
    """用户角色"""

    USER = "user"
    ADMIN = "admin"
    FAMILY = "family"  # 家庭成员


class BloodPressureCategory(enum.Enum):
    """血压分类"""

    NORMAL = "normal"  # 正常 <120/80
    ELEVATED = "elevated"  # 正常高值 120-129/<80
    STAGE1 = "stage1"  # 高血压1级 130-139/80-89
    STAGE2 = "stage2"  # 高血压2级 >=140/>=90
    CRISIS = "crisis"  # 高血压危象 >=180/>=120


class GlucoseMealType(enum.Enum):
    """血糖测量时段"""

    FASTING = "fasting"  # 空腹
    BEFORE_MEAL = "before_meal"  # 餐前
    AFTER_MEAL = "after_meal"  # 餐后2小时
    BEFORE_BED = "before_bed"  # 睡前
    RANDOM = "random"  # 随机


class Gender(enum.Enum):
    """性别"""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


# ==================== 核心模型 ====================


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)

    # 密码
    hashed_password = Column(String(255), nullable=False)

    # 基本信息
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    gender = Column(Enum(Gender), default=Gender.UNKNOWN)
    birth_date = Column(DateTime, nullable=True)

    # 健康档案
    height_cm = Column(Float, nullable=True)  # 身高厘米
    medical_history = Column(Text, nullable=True)  # 病史
    allergies = Column(Text, nullable=True)  # 过敏信息
    medications = Column(Text, nullable=True)  # 常用药物

    # 账户信息
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime, nullable=True)

    # AI偏好
    preferred_model = Column(String(50), default="gemini-2.0-flash")
    persona_enabled = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    blood_pressure_records = relationship(
        "BloodPressureRecord", back_populates="user", cascade="all, delete-orphan"
    )
    glucose_records = relationship(
        "GlucoseRecord", back_populates="user", cascade="all, delete-orphan"
    )
    weight_records = relationship(
        "WeightRecord", back_populates="user", cascade="all, delete-orphan"
    )
    sleep_records = relationship(
        "SleepRecord", back_populates="user", cascade="all, delete-orphan"
    )
    heart_rate_records = relationship(
        "HeartRateRecord", back_populates="user", cascade="all, delete-orphan"
    )
    medication_logs = relationship(
        "MedicationLog", back_populates="user", cascade="all, delete-orphan"
    )
    goals = relationship(
        "HealthGoal", back_populates="user", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatMessage", back_populates="user", cascade="all, delete-orphan"
    )
    memories = relationship(
        "Memory", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

    def to_dict(self) -> dict:
        """转换为字典（不含敏感信息）"""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
            "gender": self.gender.value if self.gender else None,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "height_cm": self.height_cm,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "preferred_model": self.preferred_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BloodPressureRecord(Base):
    """血压记录表"""

    __tablename__ = "blood_pressure_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 测量值
    systolic = Column(Integer, nullable=False)  # 收缩压
    diastolic = Column(Integer, nullable=False)  # 舒张压
    pulse = Column(Integer, nullable=True)  # 脉搏

    # 分类（自动计算）
    category = Column(Enum(BloodPressureCategory), nullable=True)

    # 测量信息
    measured_at = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)
    device_id = Column(String(100), nullable=True)  # 设备标识

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="blood_pressure_records")

    # 索引
    __table_args__ = (Index("idx_bp_user_measured", "user_id", "measured_at"),)

    def __repr__(self):
        return f"<BPRecord(user={self.user_id}, {self.systolic}/{self.diastolic})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "systolic": self.systolic,
            "diastolic": self.diastolic,
            "pulse": self.pulse,
            "category": self.category.value if self.category else None,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GlucoseRecord(Base):
    """血糖记录表"""

    __tablename__ = "glucose_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 测量值
    value = Column(Float, nullable=False)  # 血糖值
    unit = Column(String(10), default="mmol/L")  # 单位
    meal_type = Column(Enum(GlucoseMealType), nullable=False)

    # 参考范围判断
    is_normal = Column(Boolean, nullable=True)

    # 测量信息
    measured_at = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)

    # 关联用药
    medication_taken = Column(String(255), nullable=True)  # 是否服药及药名

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="glucose_records")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "value": self.value,
            "unit": self.unit,
            "meal_type": self.meal_type.value if self.meal_type else None,
            "is_normal": self.is_normal,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "note": self.note,
            "medication_taken": self.medication_taken,
        }


class WeightRecord(Base):
    """体重记录表"""

    __tablename__ = "weight_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 测量值
    weight_kg = Column(Float, nullable=False)
    bmi = Column(Float, nullable=True)  # 自动计算
    body_fat_percent = Column(Float, nullable=True)  # 体脂率
    muscle_mass_kg = Column(Float, nullable=True)  # 肌肉量

    # 测量信息
    measured_at = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="weight_records")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "weight_kg": self.weight_kg,
            "bmi": self.bmi,
            "body_fat_percent": self.body_fat_percent,
            "muscle_mass_kg": self.muscle_mass_kg,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "note": self.note,
        }


class SleepRecord(Base):
    """睡眠记录表"""

    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 时间
    bed_time = Column(DateTime, nullable=False)
    wake_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # 总时长

    # 质量
    sleep_quality = Column(Integer, nullable=True)  # 1-10评分
    deep_sleep_minutes = Column(Integer, nullable=True)
    light_sleep_minutes = Column(Integer, nullable=True)
    rem_sleep_minutes = Column(Integer, nullable=True)
    awake_times = Column(Integer, nullable=True)  # 醒来次数

    # 笔记
    note = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="sleep_records")

    def to_dict(self) -> dict:
        hours = self.duration_minutes / 60 if self.duration_minutes else 0
        return {
            "id": self.id,
            "bed_time": self.bed_time.isoformat() if self.bed_time else None,
            "wake_time": self.wake_time.isoformat() if self.wake_time else None,
            "duration_minutes": self.duration_minutes,
            "duration_hours": round(hours, 1),
            "sleep_quality": self.sleep_quality,
            "deep_sleep_minutes": self.deep_sleep_minutes,
            "light_sleep_minutes": self.light_sleep_minutes,
            "rem_sleep_minutes": self.rem_sleep_minutes,
            "awake_times": self.awake_times,
            "note": self.note,
        }


class HeartRateRecord(Base):
    """心率记录表"""

    __tablename__ = "heart_rate_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 测量值
    bpm = Column(Integer, nullable=False)  # 心率
    activity = Column(
        String(50), nullable=True
    )  # 活动状态: resting, walking, exercising

    # 测量信息
    measured_at = Column(DateTime, nullable=False)
    note = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="heart_rate_records")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "bpm": self.bpm,
            "activity": self.activity,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "note": self.note,
        }


class Medication(Base):
    """药物信息表"""

    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 药物信息
    name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)  # 剂量，如 "100mg"
    frequency = Column(String(100), nullable=True)  # 频次，如 "每日1次"
    purpose = Column(String(255), nullable=True)  # 用途

    # 提醒设置
    reminder_time = Column(String(50), nullable=True)  # 提醒时间，如 "08:00"
    reminder_enabled = Column(Boolean, default=True)

    # 状态
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User")
    logs = relationship("MedicationLog", back_populates="medication")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "purpose": self.purpose,
            "reminder_time": self.reminder_time,
            "reminder_enabled": self.reminder_enabled,
            "is_active": self.is_active,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
        }


class MedicationLog(Base):
    """用药记录表"""

    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)

    # 用药信息
    taken_at = Column(DateTime, nullable=False)
    dosage_taken = Column(String(100), nullable=True)  # 实际服用剂量
    skipped = Column(Boolean, default=False)  # 是否跳过
    skip_reason = Column(Text, nullable=True)  # 跳过原因
    note = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="medication_logs")
    medication = relationship("Medication", back_populates="logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "medication_id": self.medication_id,
            "medication_name": self.medication.name if self.medication else None,
            "taken_at": self.taken_at.isoformat() if self.taken_at else None,
            "dosage_taken": self.dosage_taken,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "note": self.note,
        }


class HealthGoal(Base):
    """健康目标表"""

    __tablename__ = "health_goals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 目标信息
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(
        String(50), nullable=False
    )  # weight, bp, glucose, sleep, exercise, etc.

    # 目标值
    target_value = Column(Float, nullable=True)
    target_unit = Column(String(50), nullable=True)
    current_value = Column(Float, nullable=True)

    # 时间
    start_date = Column(DateTime, nullable=False)
    target_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 状态
    status = Column(
        String(20), default="active"
    )  # active, completed, paused, abandoned
    progress_percent = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="goals")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "goal_type": self.goal_type,
            "target_value": self.target_value,
            "target_unit": self.target_unit,
            "current_value": self.current_value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


class ChatMessage(Base):
    """聊天消息表"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 消息内容
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # 元数据
    session_id = Column(String(100), nullable=True, index=True)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # 情绪信息
    emotion_detected = Column(String(50), nullable=True)
    emotion_score = Column(Float, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), index=True)

    # 关系
    user = relationship("User", back_populates="chat_messages")

    # 索引
    __table_args__ = (
        Index("idx_chat_user_session", "user_id", "session_id", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "session_id": self.session_id,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "emotion_detected": self.emotion_detected,
            "emotion_score": self.emotion_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Memory(Base):
    """AI记忆表"""

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 记忆内容
    content = Column(Text, nullable=False)
    memory_type = Column(
        String(50), default="general"
    )  # general, health, preference, fact
    importance = Column(Integer, default=5)  # 1-10

    # 来源
    source_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)

    # 时间
    created_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)

    # 关系
    user = relationship("User", back_populates="memories")
    source_message = relationship("ChatMessage")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "access_count": self.access_count,
        }


class Notification(Base):
    """通知表"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 通知内容
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(
        String(50), nullable=False
    )  # medication, health_alert, system, chat

    # 状态
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    # 优先级
    priority = Column(String(20), default="normal")  # low, normal, high, urgent

    # 操作
    action_type = Column(String(50), nullable=True)  # open_url, open_page, dismiss
    action_data = Column(Text, nullable=True)  # JSON字符串

    # 时间戳
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "priority": self.priority,
            "action_type": self.action_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ==================== 数据库工具函数 ====================


def get_db_url() -> str:
    """获取数据库连接URL"""
    import os

    # 优先从环境变量读取
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # 从分段配置构建
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ruoxi")
    user = os.getenv("POSTGRES_USER", "ruoxi")
    password = os.getenv("POSTGRES_PASSWORD", "")

    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def create_engine_instance():
    """创建数据库引擎"""
    db_url = get_db_url()
    return create_engine(
        db_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,  # 生产环境设为False
    )


def init_database():
    """初始化数据库（创建所有表）"""
    engine = create_engine_instance()
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")


def get_session_factory():
    """获取会话工厂"""
    engine = create_engine_instance()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 依赖注入函数（用于FastAPI）
def get_db():
    """获取数据库会话"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
