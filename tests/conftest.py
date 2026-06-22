"""
🌸 若曦V2 - 测试配置
Pytest全局配置和fixtures
"""

import os
import tempfile
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# 确保测试环境先设置
os.environ["TESTING"] = "true"

from platform.backend.main import app

# 导入应用组件
from models.database import Base, get_db

# ==================== 数据库配置 ====================

# 内存SQLite数据库用于测试
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """测试用数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 替换应用的数据库依赖
app.dependency_overrides[get_db] = override_get_db


# ==================== Fixtures ====================


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """测试会话开始时创建数据库表"""
    Base.metadata.create_all(bind=engine)
    yield
    # 测试会话结束时清理
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """每个测试函数的数据库会话"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """FastAPI测试客户端"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """创建测试用户"""
    from models.database import User

    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password_here",
        display_name="测试用户",
        age=30,
        gender="male",
        height_cm=175,
        weight_kg=70,
        is_active=True,
        timezone="Asia/Shanghai",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """生成认证头"""
    from platform.backend.core_auth.jwt_auth import create_access_token

    token = create_access_token(
        data={"user_id": test_user.id, "username": test_user.username},
        expires_delta=timedelta(hours=1),
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_bp_records(db_session: Session, test_user):
    """创建测试血压记录"""
    from models.database import BloodPressureRecord

    records = [
        BloodPressureRecord(
            user_id=test_user.id,
            systolic=120,
            diastolic=80,
            pulse=75,
            category="normal",
            measured_at=datetime.utcnow() - timedelta(days=i),
        )
        for i in range(7)
    ]

    # 添加异常血压记录
    records.extend(
        [
            BloodPressureRecord(
                user_id=test_user.id,
                systolic=140,
                diastolic=90,
                pulse=80,
                category="stage1",
                measured_at=datetime.utcnow() - timedelta(days=10),
            ),
            BloodPressureRecord(
                user_id=test_user.id,
                systolic=185,
                diastolic=120,
                pulse=95,
                category="crisis",
                measured_at=datetime.utcnow() - timedelta(days=15),
            ),
        ]
    )

    db_session.add_all(records)
    db_session.commit()

    return records


@pytest.fixture(scope="function")
def test_glucose_records(db_session: Session, test_user):
    """创建测试血糖记录"""
    from models.database import GlucoseRecord

    records = [
        GlucoseRecord(
            user_id=test_user.id,
            value=5.5,
            unit="mmol/L",
            meal_type="fasting",
            is_normal=True,
            measured_at=datetime.utcnow() - timedelta(days=i),
        )
        for i in range(5)
    ]

    # 添加异常血糖
    records.append(
        GlucoseRecord(
            user_id=test_user.id,
            value=17.5,
            unit="mmol/L",
            meal_type="post_meal",
            is_normal=False,
            measured_at=datetime.utcnow() - timedelta(days=3),
        )
    )

    records.append(
        GlucoseRecord(
            user_id=test_user.id,
            value=3.2,
            unit="mmol/L",
            meal_type="fasting",
            is_normal=False,
            measured_at=datetime.utcnow() - timedelta(days=5),
        )
    )

    db_session.add_all(records)
    db_session.commit()

    return records


@pytest.fixture(scope="function")
def test_medication(db_session: Session, test_user):
    """创建测试用药"""
    from models.database import Medication

    medication = Medication(
        id=1,
        user_id=test_user.id,
        name="降压药",
        dosage="5mg",
        frequency="daily",
        purpose="高血压",
        is_active=True,
        reminder_enabled=True,
    )

    db_session.add(medication)
    db_session.commit()
    db_session.refresh(medication)

    return medication


@pytest.fixture(scope="function")
def test_sleep_records(db_session: Session, test_user):
    """创建测试睡眠记录"""
    from models.database import SleepRecord

    records = [
        SleepRecord(
            user_id=test_user.id,
            bed_time=datetime.utcnow().replace(hour=22, minute=30) - timedelta(days=i),
            wake_time=datetime.utcnow().replace(hour=6, minute=30)
            - timedelta(days=i - 1),
            duration_minutes=480,
            sleep_quality=85,
            sleep_efficiency=90,
        )
        for i in range(7)
    ]

    db_session.add_all(records)
    db_session.commit()

    return records


# ==================== 工具函数 ====================


@pytest.fixture
def assert_success_response():
    """断言成功响应"""

    def _assert(response, status_code: int = 200):
        assert (
            response.status_code == status_code
        ), f"Expected {status_code}, got {response.status_code}: {response.text}"
        data = response.json()
        assert (
            data.get("success") is True or "data" in data or "id" in data
        ), f"Unexpected response: {data}"
        return data

    return _assert


@pytest.fixture
def assert_error_response():
    """断言错误响应"""

    def _assert(response, status_code: int = 400):
        assert (
            response.status_code == status_code
        ), f"Expected {status_code}, got {response.status_code}: {response.text}"
        data = response.json()
        assert (
            "error" in data or "detail" in data
        ), f"Expected error in response: {data}"
        return data

    return _assert


# ==================== 参数化测试数据 ====================

VALID_BP_DATA = [
    {"systolic": 120, "diastolic": 80, "pulse": 75},
    {"systolic": 130, "diastolic": 85, "pulse": 78},
]

INVALID_BP_DATA = [
    ({"systolic": 300, "diastolic": 80}, "收缩压超出正常范围"),
    ({"systolic": 120, "diastolic": 200}, "舒张压超出正常范围"),
    ({"systolic": 120}, "缺少舒张压"),
    ({"diastolic": 80}, "缺少收缩压"),
]

VALID_GLUCOSE_DATA = [
    {"value": 5.5, "meal_type": "fasting"},
    {"value": 7.8, "meal_type": "post_meal"},
]

INVALID_GLUCOSE_DATA = [
    ({"value": 50}, "血糖值过高"),
    ({"value": 0.5}, "血糖值过低"),
    ({"meal_type": "fasting"}, "缺少血糖值"),
]
