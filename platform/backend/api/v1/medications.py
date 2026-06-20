"""
🌸 若曦V2 - 用药管理API
用药记录、提醒、依从性分析端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime

from platform.backend.core_auth.jwt_auth import get_current_user
from core.services.medication_service import MedicationService
from models.database import Medication, MedicationLog, get_db
from sqlalchemy.orm import Session


router = APIRouter(prefix="/medications", tags=["用药管理"])


# ==================== Pydantic 模型 ====================

class MedicationCreate(BaseModel):
    """创建用药模型"""
    name: str = Field(..., min_length=1, max_length=255, description="药物名称")
    dosage: str = Field(..., max_length=100, description="剂量，如「100mg」")
    frequency: str = Field(..., max_length=100, description="频次，如「每日1次」")
    purpose: Optional[str] = Field(None, max_length=255, description="用途")
    reminder_time: Optional[str] = Field(None, max_length=50, description="提醒时间，如「08:00」")
    reminder_enabled: bool = Field(True, description="是否启用提醒")
    start_date: Optional[date] = Field(default_factory=date.today)
    end_date: Optional[date] = Field(None, description="结束日期（可选）")


class MedicationUpdate(BaseModel):
    """更新用药模型"""
    name: Optional[str] = Field(None, max_length=255)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = Field(None, max_length=100)
    purpose: Optional[str] = Field(None, max_length=255)
    reminder_time: Optional[str] = Field(None, max_length=50)
    reminder_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    end_date: Optional[date] = None


class MedicationResponse(BaseModel):
    """用药响应模型"""
    id: int
    name: str
    dosage: str
    frequency: str
    purpose: Optional[str]
    reminder_time: Optional[str]
    reminder_enabled: bool
    is_active: bool
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MedicationLogCreate(BaseModel):
    """创建服药记录模型"""
    medication_id: int
    taken_at: Optional[datetime] = Field(default_factory=datetime.now)
    dosage_taken: Optional[str] = Field(None, max_length=100)
    note: Optional[str] = Field(None, max_length=500)


class MedicationSkipCreate(BaseModel):
    """创建跳药记录模型"""
    medication_id: int
    reason: Optional[str] = Field(None, max_length=500)
    skip_time: Optional[datetime] = Field(default_factory=datetime.now)


class ScheduleItem(BaseModel):
    """日程项"""
    medication_id: int
    name: str
    dosage: str
    frequency: str
    reminder_time: Optional[str]
    purpose: Optional[str]
    status: str  # pending, taken, skipped
    taken_at: Optional[str]
    log_id: Optional[int]


# ==================== API 端点 ====================

@router.get("", response_model=List[MedicationResponse])
async def list_medications(
    active_only: bool = Query(True, description="只显示活跃用药"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用药列表
    
    返回用户的所有用药记录
    """
    query = db.query(Medication).filter(Medication.user_id == current_user.user_id)
    
    if active_only:
        today = date.today()
        query = query.filter(
            Medication.is_active == True,
            Medication.start_date <= today,
            or_(
                Medication.end_date == None,
                Medication.end_date >= today
            )
        )
    
    medications = query.order_by(Medication.created_at.desc()).all()
    return medications


@router.post("", response_model=MedicationResponse)
async def create_medication(
    data: MedicationCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新用药记录
    
    添加新的用药信息并可选设置提醒
    """
    service = MedicationService(db)
    
    medication = service.create_medication(
        user_id=current_user.user_id,
        name=data.name,
        dosage=data.dosage,
        frequency=data.frequency,
        purpose=data.purpose,
        reminder_time=data.reminder_time,
        start_date=data.start_date,
        end_date=data.end_date
    )
    
    return medication


@router.get("/{medication_id}", response_model=MedicationResponse)
async def get_medication(
    medication_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个用药详情"""
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()
    
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    return medication


@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication(
    medication_id: int,
    data: MedicationUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用药信息"""
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()
    
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    update_data = data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(medication, field, value)
    
    # 如果设置了提醒时间，自动启用提醒
    if "reminder_time" in update_data and update_data["reminder_time"]:
        medication.reminder_enabled = True
    
    db.commit()
    db.refresh(medication)
    
    return medication


@router.delete("/{medication_id}")
async def delete_medication(
    medication_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除用药记录
    
    软删除，标记为不活跃
    """
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()
    
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    # 软删除
    medication.is_active = False
    medication.end_date = date.today()
    
    db.commit()
    
    return {
        "success": True,
        "message": "用药记录已停用",
        "medication_id": medication_id
    }


# ==================== 服药记录API ====================

@router.post("/{medication_id}/take")
async def record_medication_taken(
    medication_id: int,
    data: Optional[MedicationLogCreate] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    记录服药
    
    标记药物为已服用
    """
    # 检查用药是否存在且属于当前用户
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()
    
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    service = MedicationService(db)
    
    log_data = data or MedicationLogCreate(medication_id=medication_id)
    
    log = service.record_medication_taken(
        medication_id=medication_id,
        user_id=current_user.user_id,
        taken_at=log_data.taken_at,
        dosage_taken=log_data.dosage_taken,
        note=log_data.note
    )
    
    return {
        "success": True,
        "message": "服药记录已添加",
        "log_id": log.id,
        "taken_at": log.taken_at.isoformat()
    }


@router.post("/{medication_id}/skip")
async def record_medication_skipped(
    medication_id: int,
    data: Optional[MedicationSkipCreate] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    记录跳过服药
    
    记录未服药的原因
    """
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()
    
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    service = MedicationService(db)
    
    skip_data = data or MedicationSkipCreate(medication_id=medication_id)
    
    log = service.record_medication_skipped(
        medication_id=medication_id,
        user_id=current_user.user_id,
        reason=skip_data.reason,
        skip_time=skip_data.skip_time
    )
    
    return {
        "success": True,
        "message": "跳过记录已添加",
        "log_id": log.id,
        "skip_reason": skip_data.reason
    }


@router.get("/{medication_id}/history")
async def get_medication_history(
    medication_id: int,
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用药历史记录
    
    返回过去N天的服药/跳过记录
    """
    medication = db.query(Medication).filter(
        Medication.id == medication_id,
        Medication.user_id == current_user.user_id
    ).first()
    
    if not medication:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    
    from datetime import timedelta
    start_date = datetime.now() - timedelta(days=days)
    
    logs = db.query(MedicationLog).filter(
        MedicationLog.medication_id == medication_id,
        MedicationLog.taken_at >= start_date
    ).order_by(MedicationLog.taken_at.desc()).all()
    
    return {
        "success": True,
        "medication_name": medication.name,
        "total_records": len(logs),
        "taken_count": sum(1 for log in logs if not log.skipped),
        "skipped_count": sum(1 for log in logs if log.skipped),
        "history": [
            {
                "id": log.id,
                "taken_at": log.taken_at.isoformat(),
                "skipped": log.skipped,
                "skip_reason": log.skip_reason,
                "dosage_taken": log.dosage_taken,
                "note": log.note
            }
            for log in logs
        ]
    }


# ==================== 计划与提醒API ====================

@router.get("/schedule/today")
async def get_today_schedule(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取今日用药计划
    
    返回今日所有用药及状态
    """
    service = MedicationService(db)
    schedule = service.get_medication_schedule(
        user_id=current_user.user_id,
        target_date=date.today()
    )
    
    # 按状态分类
    pending = [s for s in schedule if s["status"] == "pending"]
    taken = [s for s in schedule if s["status"] == "taken"]
    skipped = [s for s in schedule if s["status"] == "skipped"]
    
    # 计算应该已经服药但未服的数量（过期）
    overdue = sum(1 for s in pending if s["reminder_time"] and 
                  datetime.now().time() > datetime.strptime(s["reminder_time"], "%H:%M").time())
    
    return {
        "success": True,
        "date": date.today().isoformat(),
        "summary": {
            "total": len(schedule),
            "pending": len(pending),
            "taken": len(taken),
            "skipped": len(skipped),
            "overdue": overdue,
            "completion_rate": round(len(taken) / len(schedule) * 100, 1) if schedule else 0
        },
        "schedule": schedule
    }


@router.get("/schedule/{target_date}")
async def get_schedule_by_date(
    target_date: date,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定日期的用药计划"""
    service = MedicationService(db)
    schedule = service.get_medication_schedule(
        user_id=current_user.user_id,
        target_date=target_date
    )
    
    return {
        "success": True,
        "date": target_date.isoformat(),
        "total": len(schedule),
        "schedule": schedule
    }


@router.get("/reminders/due")
async def get_due_reminders(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前应提醒的用药
    
    在提醒时间窗口内（±15分钟）且今天未记录的用药
    """
    service = MedicationService(db)
    due = service.get_due_medications(
        user_id=current_user.user_id,
        check_time=datetime.now()
    )
    
    return {
        "success": True,
        "current_time": datetime.now().isoformat(),
        "due_count": len(due),
        "due_medications": [
            {
                "id": item["medication"].id,
                "name": item["medication"].name,
                "dosage": item["medication"].dosage,
                "reminder_time": item["medication"].reminder_time,
                "is_overdue": item["is_overdue"],
                "minutes_until": item["minutes_until"],
                "minutes_overdue": item["minutes_overdue"]
            }
            for item in due
        ]
    }


# ==================== 依从性分析API ====================

@router.get("/adherence/summary")
async def get_adherence_summary(
    medication_id: Optional[int] = Query(None, description="指定用药ID，不传则统计全部"),
    days: int = Query(30, ge=7, le=90),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用药依从性摘要
    
    计算在指定天数内的服药依从性
    """
    service = MedicationService(db)
    adherence = service.get_medication_adherence(
        user_id=current_user.user_id,
        medication_id=medication_id,
        days=days
    )
    
    return {
        "success": True,
        "medication_id": medication_id,
        "adherence": adherence
    }


@router.get("/adherence/missed")
async def get_missed_doses(
    days: int = Query(7, ge=1, le=30),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取漏服记录
    
    检测过去N天内应该服药但未服的记录
    """
    service = MedicationService(db)
    missed = service.detect_missed_doses(
        user_id=current_user.user_id,
        days=days
    )
    
    return {
        "success": True,
        "period_days": days,
        "missed_count": len(missed),
        "missed_doses": missed
    }


# ==================== 综合摘要API ====================

@router.get("/summary")
async def get_medication_summary(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用药综合摘要
    
    汇总所有用药相关的统计信息
    """
    service = MedicationService(db)
    summary = service.get_medication_summary(user_id=current_user.user_id)
    
    return {
        "success": True,
        "summary": summary
    }


@router.get("/report")
async def generate_medication_report(
    days: int = Query(30, ge=7, le=90),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成用药报告
    
    返回详细的用药统计和分析报告
    """
    service = MedicationService(db)
    report = service.generate_medication_report(
        user_id=current_user.user_id,
        days=days
    )
    
    return {
        "success": True,
        "report": report
    }


# 导入or_函数
from sqlalchemy import or_
