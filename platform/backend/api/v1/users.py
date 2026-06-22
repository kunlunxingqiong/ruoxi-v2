"""
🌸 若曦V2 - 用户管理API
用户资料管理端点
"""

from datetime import date, datetime
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models.database import Gender
from models.database import User as UserModel
from models.database import get_db
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["用户管理"])


# ==================== Pydantic 模型 ====================


class UserProfileUpdate(BaseModel):
    """用户资料更新模型"""

    nickname: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    height_cm: Optional[float] = Field(None, gt=50, lt=300)
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nickname": "小明",
                "gender": "male",
                "birth_date": "1990-01-01",
                "height_cm": 175.5,
                "medical_history": "高血压病史5年",
                "allergies": "无已知过敏",
            }
        }


class UserSettingsUpdate(BaseModel):
    """用户设置更新模型"""

    preferred_model: Optional[str] = "gemini-2.0-flash"
    persona_enabled: Optional[bool] = True
    notification_enabled: Optional[bool] = True

    class Config:
        json_schema_extra = {
            "example": {
                "preferred_model": "llama-3.3-70b-versatile",
                "persona_enabled": True,
                "notification_enabled": True,
            }
        }


class UserProfileResponse(BaseModel):
    """用户资料响应"""

    id: int
    uuid: str
    username: str
    nickname: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    gender: Optional[str]
    birth_date: Optional[str]
    age: Optional[int]
    height_cm: Optional[float]
    medical_history: Optional[str]
    allergies: Optional[str]
    medications: Optional[str]
    preferred_model: str
    persona_enabled: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class HealthSummary(BaseModel):
    """健康数据摘要"""

    total_bp_records: int
    total_glucose_records: int
    total_weight_records: int
    total_sleep_records: int
    active_medications: int
    active_goals: int

    latest_bp: Optional[dict] = None
    latest_weight: Optional[dict] = None


# ==================== API 端点 ====================


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取当前用户资料

    返回用户的完整 profile 信息
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 计算年龄
    age = None
    if user.birth_date:
        today = date.today()
        age = (
            today.year
            - user.birth_date.year
            - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day))
        )

    return {
        "id": user.id,
        "uuid": user.uuid,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "gender": user.gender.value if user.gender else None,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "age": age,
        "height_cm": user.height_cm,
        "medical_history": user.medical_history,
        "allergies": user.allergies,
        "medications": user.medications,
        "preferred_model": user.preferred_model,
        "persona_enabled": user.persona_enabled,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.put("/me")
async def update_my_profile(
    profile: UserProfileUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新当前用户资料

    可以更新的字段：
    - nickname: 昵称
    - avatar_url: 头像URL
    - gender: 性别 (male/female/other/unknown)
    - birth_date: 出生日期
    - height_cm: 身高(cm)
    - medical_history: 病史
    - allergies: 过敏信息
    - medications: 常用药物
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    update_data = profile.dict(exclude_unset=True)

    # 处理枚举类型
    if "gender" in update_data and update_data["gender"]:
        try:
            update_data["gender"] = Gender(update_data["gender"])
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"无效的性别值: {update_data['gender']}"
            )

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "资料更新成功",
        "updated_fields": list(update_data.keys()),
    }


@router.get("/me/settings")
async def get_my_settings(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取用户设置
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "success": True,
        "settings": {
            "preferred_model": user.preferred_model,
            "persona_enabled": user.persona_enabled,
            "notification_enabled": True,  # 默认值
        },
    }


@router.put("/me/settings")
async def update_my_settings(
    settings: UserSettingsUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新用户设置

    可设置项：
    - preferred_model: 首选AI模型
    - persona_enabled: 是否启用若曦人设
    - notification_enabled: 是否启用通知
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = settings.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return {"success": True, "message": "设置更新成功", "settings": update_data}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传用户头像

    支持的格式：jpg, png, gif
    最大大小：5MB
    """
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, detail="不支持的文件格式，请上传 jpg, png 或 gif"
        )

    # 读取文件内容
    contents = await file.read()

    # 验证文件大小 (5MB)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大，最大支持5MB")

    # TODO: 实际上传图片到OSS/S3
    # 这里用模拟URL代替
    avatar_url = f"https://cdn.ruoxi.ai/avatar/{current_user.user_id}/{file.filename}"

    # 更新用户头像
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()
    user.avatar_url = avatar_url
    db.commit()

    return {"success": True, "message": "头像上传成功", "avatar_url": avatar_url}


@router.get("/me/health-summary")
async def get_health_summary(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取用户健康数据摘要

    返回各项健康数据的统计信息
    """
    from models.database import (
        BloodPressureRecord,
        GlucoseRecord,
        HealthGoal,
        Medication,
        WeightRecord,
    )

    user_id = current_user.user_id

    # 统计记录数量
    bp_count = (
        db.query(BloodPressureRecord)
        .filter(BloodPressureRecord.user_id == user_id)
        .count()
    )

    glucose_count = (
        db.query(GlucoseRecord).filter(GlucoseRecord.user_id == user_id).count()
    )

    weight_count = (
        db.query(WeightRecord).filter(WeightRecord.user_id == user_id).count()
    )

    active_meds = (
        db.query(Medication)
        .filter(Medication.user_id == user_id, Medication.is_active == True)
        .count()
    )

    active_goals = (
        db.query(HealthGoal)
        .filter(HealthGoal.user_id == user_id, HealthGoal.status == "active")
        .count()
    )

    # 获取最新记录
    latest_bp = (
        db.query(BloodPressureRecord)
        .filter(BloodPressureRecord.user_id == user_id)
        .order_by(BloodPressureRecord.measured_at.desc())
        .first()
    )

    latest_weight = (
        db.query(WeightRecord)
        .filter(WeightRecord.user_id == user_id)
        .order_by(WeightRecord.measured_at.desc())
        .first()
    )

    return {
        "success": True,
        "summary": {
            "total_bp_records": bp_count,
            "total_glucose_records": glucose_count,
            "total_weight_records": weight_count,
            "active_medications": active_meds,
            "active_goals": active_goals,
            "latest_bp": latest_bp.to_dict() if latest_bp else None,
            "latest_weight": latest_weight.to_dict() if latest_weight else None,
        },
    }


@router.delete("/me")
async def delete_my_account(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    注销账户

    删除用户及其所有相关数据
    此操作不可逆！
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 软删除：标记为不活跃
    user.is_active = False
    user.email = f"deleted_{user.id}_{user.email}" if user.email else None
    user.phone = f"deleted_{user.id}_{user.phone}" if user.phone else None
    db.commit()

    return {"success": True, "message": "账户已注销", "note": "60天后数据将被永久删除"}


# ==================== 管理端点 (仅管理员) ====================


@router.get("/list")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取用户列表 (仅管理员)
    """
    # 检查权限
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()
    if not user or user.role.value != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    users = db.query(UserModel).offset(skip).limit(limit).all()

    return {
        "success": True,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "email": u.email,
                "is_active": u.is_active,
                "role": u.role.value,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": db.query(UserModel).count(),
    }
