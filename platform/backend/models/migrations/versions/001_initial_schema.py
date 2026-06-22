"""初始数据库结构

Revision ID: 001
Revises:
Create Date: 2026-06-21 05:08:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建枚举类型
    userrole = sa.Enum("USER", "ADMIN", "FAMILY", name="userrole")
    userrole.create(op.get_bind())

    bloodpressurecategory = sa.Enum(
        "NORMAL", "ELEVATED", "STAGE1", "STAGE2", "CRISIS", name="bloodpressurecategory"
    )
    bloodpressurecategory.create(op.get_bind())

    glucosemealtype = sa.Enum(
        "FASTING",
        "BEFORE_MEAL",
        "AFTER_MEAL",
        "BEFORE_BED",
        "RANDOM",
        name="glucosemealtype",
    )
    glucosemealtype.create(op.get_bind())

    gender = sa.Enum("MALE", "FEMALE", "OTHER", "UNKNOWN", name="gender")
    gender.create(op.get_bind())

    # 用户表
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("gender", gender, nullable=True),
        sa.Column("birth_date", sa.DateTime(), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("medical_history", sa.Text(), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("medications", sa.Text(), nullable=True),
        sa.Column("role", userrole, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("preferred_model", sa.String(length=50), nullable=True),
        sa.Column("persona_enabled", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # 血压记录表
    op.create_table(
        "blood_pressure_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("systolic", sa.Integer(), nullable=False),
        sa.Column("diastolic", sa.Integer(), nullable=False),
        sa.Column("pulse", sa.Integer(), nullable=True),
        sa.Column("category", bloodpressurecategory, nullable=True),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("device_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_bp_user_measured", "blood_pressure_records", ["user_id", "measured_at"]
    )

    # 血糖记录表
    op.create_table(
        "glucose_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=10), nullable=True),
        sa.Column("meal_type", glucosemealtype, nullable=False),
        sa.Column("is_normal", sa.Boolean(), nullable=True),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("medication_taken", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 体重记录表
    op.create_table(
        "weight_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("body_fat_percent", sa.Float(), nullable=True),
        sa.Column("muscle_mass_kg", sa.Float(), nullable=True),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 睡眠记录表
    op.create_table(
        "sleep_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bed_time", sa.DateTime(), nullable=False),
        sa.Column("wake_time", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("sleep_quality", sa.Integer(), nullable=True),
        sa.Column("deep_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("light_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("rem_sleep_minutes", sa.Integer(), nullable=True),
        sa.Column("awake_times", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 心率记录表
    op.create_table(
        "heart_rate_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bpm", sa.Integer(), nullable=False),
        sa.Column("activity", sa.String(length=50), nullable=True),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 药物信息表
    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("dosage", sa.String(length=100), nullable=True),
        sa.Column("frequency", sa.String(length=100), nullable=True),
        sa.Column("purpose", sa.String(length=255), nullable=True),
        sa.Column("reminder_time", sa.String(length=50), nullable=True),
        sa.Column("reminder_enabled", sa.Boolean(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 用药记录表
    op.create_table(
        "medication_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("medication_id", sa.Integer(), nullable=False),
        sa.Column("taken_at", sa.DateTime(), nullable=False),
        sa.Column("dosage_taken", sa.String(length=100), nullable=True),
        sa.Column("skipped", sa.Boolean(), nullable=True),
        sa.Column("skip_reason", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["medication_id"],
            ["medications.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 健康目标表
    op.create_table(
        "health_goals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal_type", sa.String(length=50), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("target_unit", sa.String(length=50), nullable=True),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("target_date", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 聊天消息表
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("model_used", sa.String(length=100), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("emotion_detected", sa.String(length=50), nullable=True),
        sa.Column("emotion_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_chat_user_session",
        "chat_messages",
        ["user_id", "session_id", "created_at"],
    )

    # AI记忆表
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("memory_type", sa.String(length=50), nullable=True),
        sa.Column("importance", sa.Integer(), nullable=True),
        sa.Column("source_message_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["chat_messages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 通知表
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("action_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # 删除表（反向顺序）
    op.drop_table("notifications")
    op.drop_table("memories")
    op.drop_index("idx_chat_user_session", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_table("health_goals")
    op.drop_table("medication_logs")
    op.drop_table("medications")
    op.drop_table("heart_rate_records")
    op.drop_table("sleep_records")
    op.drop_table("weight_records")
    op.drop_table("glucose_records")
    op.drop_index("ix_bp_user_measured", table_name="blood_pressure_records")
    op.drop_table("blood_pressure_records")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS gender")
    op.execute("DROP TYPE IF EXISTS glucosemealtype")
    op.execute("DROP TYPE IF EXISTS bloodpressurecategory")
    op.execute("DROP TYPE IF EXISTS userrole")
