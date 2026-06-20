"""
🌸 若曦V2 - 健康记录管理API
血压、血糖、体重、睡眠、心率等健康数据的CRUD操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum

from platform.backend.core_auth.jwt_auth import get_current_user
from models.database import (
    get_db, User as UserModel,
    BloodPressureRecord, GlucoseRecord, WeightRecord,
    SleepRecord, HeartRateRecord, BloodPressureCategory, GlucoseMealType
)
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func


router = APIRouter(prefix="/health", tags=["健康记录"])


# ==================== 枚举和常量 ====================

class BPCategory(str, Enum):
    """血压分类"""
    NORMAL = "normal"
    ELEVATED = "elevated"
    STAGE1 = "stage1"
    STAGE2 = "stage2"
    CRISIS = "crisis"


class MealType(str, Enum):
    """血糖测量时段"""
    FASTING = "fasting"
    BEFORE_MEAL = "before_meal"
    AFTER_MEAL = "after_meal"
    BEFORE_BED = "before_bed"
    RANDOM = "random"


# ==================== 血压记录模型 ====================

class BloodPressureCreate(BaseModel):
    """血压记录创建模型"""
    systolic: int = Field(..., ge=70, le=300, description="收缩压 mmHg")
    diastolic: int = Field(..., ge=40, le=200, description="舒张压 mmHg")
    pulse: Optional[int] = Field(None, ge=30, le=250, description="脉搏 bpm")
    measured_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = Field(None, max_length=500)
    
    @validator('diastolic')
    def diastolic_less_than_systolic(cls, v, values):
        if 'systolic' in values and v >= values['systolic']:
            raise ValueError('舒张压必须小于收缩压')
        return v


class BloodPressureUpdate(BaseModel):
    """血压记录更新模型"""
    systolic: Optional[int] = Field(None, ge=70, le=300)
    diastolic: Optional[int] = Field(None, ge=40, le=200)
    pulse: Optional[int] = Field(None, ge=30, le=250)
    measured_at: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=500)


class BloodPressureResponse(BaseModel):
    """血压记录响应"""
    id: int
    systolic: int
    diastolic: int
    pulse: Optional[int]
    category: Optional[str]
    measured_at: datetime
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


def classify_bp(systolic: int, diastolic: int) -> str:
    """根据ACC/AHA 2017标准分类血压"""
    if systolic >= 180 or diastolic >= 120:
        return BPCategory.CRISIS
    elif systolic >= 140 or diastolic >= 90:
        return BPCategory.STAGE2
    elif systolic >= 130 or diastolic >= 80:
        return BPCategory.STAGE1
    elif systolic >= 120 and diastolic < 80:
        return BPCategory.ELEVATED
    else:
        return BPCategory.NORMAL


# ==================== 血糖记录模型 ====================

class GlucoseCreate(BaseModel):
    """血糖记录创建模型"""
    value: float = Field(..., ge=1.0, le=50.0, description="血糖值 mmol/L")
    meal_type: MealType = Field(..., description="测量时段")
    unit: str = Field(default="mmol/L", description="单位")
    measured_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = Field(None, max_length=500)
    medication_taken: Optional[str] = Field(None, max_length=255)


class GlucoseUpdate(BaseModel):
    """血糖记录更新模型"""
    value: Optional[float] = Field(None, ge=1.0, le=50.0)
    meal_type: Optional[MealType] = None
    measured_at: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=500)


class GlucoseResponse(BaseModel):
    """血糖记录响应"""
    id: int
    value: float
    unit: str
    meal_type: str
    is_normal: Optional[bool]
    measured_at: datetime
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


def check_glucose_normal(value: float, meal_type: str) -> bool:
    """检查血糖是否在正常范围"""
    # 根据ADA标准 (mmol/L)
    normal_ranges = {
        "fasting": (3.9, 5.6),
        "before_meal": (3.9, 5.6),
        "after_meal": (3.9, 7.8),
        "before_bed": (5.0, 7.8),
        "random": (3.9, 11.1)
    }
    low, high = normal_ranges.get(meal_type, (3.9, 11.1))
    return low <= value <= high


# ==================== 体重记录模型 ====================

class WeightCreate(BaseModel):
    """体重记录创建模型"""
    weight_kg: float = Field(..., ge=1.0, le=500.0, description="体重 kg")
    body_fat_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    muscle_mass_kg: Optional[float] = Field(None, ge=0.0, le=500.0)
    measured_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = Field(None, max_length=500)
    
    def calculate_bmi(self, height_cm: Optional[float]) -> Optional[float]:
        """根据身高计算BMI"""
        if height_cm and height_cm > 0:
            height_m = height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None


class WeightUpdate(BaseModel):
    """体重记录更新模型"""
    weight_kg: Optional[float] = Field(None, ge=1.0, le=500.0)
    body_fat_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    muscle_mass_kg: Optional[float] = Field(None, ge=0.0, le=500.0)
    measured_at: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=500)


class WeightResponse(BaseModel):
    """体重记录响应"""
    id: int
    weight_kg: float
    bmi: Optional[float]
    body_fat_percent: Optional[float]
    muscle_mass_kg: Optional[float]
    measured_at: datetime
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 睡眠记录模型 ====================

class SleepCreate(BaseModel):
    """睡眠记录创建模型"""
    bed_time: datetime = Field(..., description="上床时间")
    wake_time: datetime = Field(..., description="起床时间")
    sleep_quality: Optional[int] = Field(None, ge=1, le=10, description="睡眠质量 1-10")
    deep_sleep_minutes: Optional[int] = Field(None, ge=0, description="深睡时长分钟")
    light_sleep_minutes: Optional[int] = Field(None, ge=0, description="浅睡时长分钟")
    rem_sleep_minutes: Optional[int] = Field(None, ge=0, description="REM睡眠分钟")
    awake_times: Optional[int] = Field(None, ge=0, description="醒来次数")
    note: Optional[str] = Field(None, max_length=500)
    
    @validator('wake_time')
    def wake_after_bed(cls, v, values):
        if 'bed_time' in values and v <= values['bed_time']:
            raise ValueError('起床时间必须晚于上床时间')
        return v


class SleepUpdate(BaseModel):
    """睡眠记录更新模型"""
    bed_time: Optional[datetime] = None
    wake_time: Optional[datetime] = None
    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    note: Optional[str] = Field(None, max_length=500)


class SleepResponse(BaseModel):
    """睡眠记录响应"""
    id: int
    bed_time: datetime
    wake_time: datetime
    duration_minutes: int
    duration_hours: float
    sleep_quality: Optional[int]
    deep_sleep_minutes: Optional[int]
    light_sleep_minutes: Optional[int]
    rem_sleep_minutes: Optional[int]
    awake_times: Optional[int]
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 心率记录模型 ====================

class HeartRateCreate(BaseModel):
    """心率记录创建模型"""
    bpm: int = Field(..., ge=30, le=300, description="心率 bpm")
    activity: Optional[str] = Field("resting", description="活动状态: resting/walking/exercising")
    measured_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = Field(None, max_length=500)


class HeartRateUpdate(BaseModel):
    """心率记录更新模型"""
    bpm: Optional[int] = Field(None, ge=30, le=300)
    activity: Optional[str] = None
    measured_at: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=500)


class HeartRateResponse(BaseModel):
    """心率记录响应"""
    id: int
    bpm: int
    activity: Optional[str]
    measured_at: datetime
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 统一查询参数 ====================

class RecordQueryParams:
    """记录查询参数"""
    def __init__(
        self,
        start_date: Optional[date] = Query(None, description="开始日期"),
        end_date: Optional[date] = Query(None, description="结束日期"),
        limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
        offset: int = Query(0, ge=0, description="偏移量"),
        order_by: str = Query("measured_at", description="排序字段"),
        order: str = Query("desc", description="排序方向: asc/desc")
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.limit = limit
        self.offset = offset
        self.order_by = order_by
        self.order = order


# ==================== 血压记录API ====================

@router.post("/blood-pressure", response_model=BloodPressureResponse)
async def create_bp_record(
    data: BloodPressureCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建血压记录
    
    自动根据ACC/AHA 2017标准分类血压等级
    """
    # 分类血压
    category = classify_bp(data.systolic, data.diastolic)
    
    record = BloodPressureRecord(
        user_id=current_user.user_id,
        systolic=data.systolic,
        diastolic=data.diastolic,
        pulse=data.pulse,
        category=category,
        measured_at=data.measured_at,
        note=data.note
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # 如果是高血压危象，添加警告
    if category == BPCategory.CRISIS:
        # TODO: 创建紧急通知
        pass
    
    return record


@router.get("/blood-pressure", response_model=List[BloodPressureResponse])
async def list_bp_records(
    params: RecordQueryParams = Depends(),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取血压记录列表
    
    支持按日期范围筛选和分页
    """
    query = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.user_id == current_user.user_id
    )
    
    # 日期筛选
    if params.start_date:
        query = query.filter(BloodPressureRecord.measured_at >= params.start_date)
    if params.end_date:
        query = query.filter(BloodPressureRecord.measured_at <= params.end_date)
    
    # 排序
    order_column = getattr(BloodPressureRecord, params.order_by, BloodPressureRecord.measured_at)
    if params.order == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(order_column)
    
    records = query.offset(params.offset).limit(params.limit).all()
    return records


@router.get("/blood-pressure/{record_id}", response_model=BloodPressureResponse)
async def get_bp_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个血压记录"""
    record = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.id == record_id,
        BloodPressureRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return record


@router.put("/blood-pressure/{record_id}", response_model=BloodPressureResponse)
async def update_bp_record(
    record_id: int,
    data: BloodPressureUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新血压记录"""
    record = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.id == record_id,
        BloodPressureRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 更新字段
    update_data = data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(record, field, value)
    
    # 重新分类血压
    if 'systolic' in update_data or 'diastolic' in update_data:
        record.category = classify_bp(record.systolic, record.diastolic)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/blood-pressure/{record_id}")
async def delete_bp_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除血压记录"""
    record = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.id == record_id,
        BloodPressureRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    db.delete(record)
    db.commit()
    
    return {"success": True, "message": "记录已删除"}


@router.get("/blood-pressure/stats/latest")
async def get_latest_bp_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取最新血压统计"""
    # 最新记录
    latest = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.user_id == current_user.user_id
    ).order_by(desc(BloodPressureRecord.measured_at)).first()
    
    # 今日平均
    today = date.today()
    today_records = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.user_id == current_user.user_id,
        func.date(BloodPressureRecord.measured_at) == today
    ).all()
    
    today_avg = None
    if today_records:
        today_avg = {
            "systolic": round(sum(r.systolic for r in today_records) / len(today_records), 1),
            "diastolic": round(sum(r.diastolic for r in today_records) / len(today_records), 1),
            "count": len(today_records)
        }
    
    # 7天平均
    week_records = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.user_id == current_user.user_id,
        BloodPressureRecord.measured_at >= func.now() - func.interval('7 days')
    ).all()
    
    week_avg = None
    if week_records:
        week_avg = {
            "systolic": round(sum(r.systolic for r in week_records) / len(week_records), 1),
            "diastolic": round(sum(r.diastolic for r in week_records) / len(week_records), 1),
            "count": len(week_records)
        }
    
    return {
        "latest": latest.to_dict() if latest else None,
        "today_average": today_avg,
        "week_average": week_avg
    }


# ==================== 血糖记录API ====================

@router.post("/glucose", response_model=GlucoseResponse)
async def create_glucose_record(
    data: GlucoseCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建血糖记录"""
    is_normal = check_glucose_normal(data.value, data.meal_type)
    
    record = GlucoseRecord(
        user_id=current_user.user_id,
        value=data.value,
        unit=data.unit,
        meal_type=data.meal_type,
        is_normal=is_normal,
        measured_at=data.measured_at,
        note=data.note,
        medication_taken=data.medication_taken
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/glucose", response_model=List[GlucoseResponse])
async def list_glucose_records(
    meal_type: Optional[MealType] = Query(None, description="按时段筛选"),
    params: RecordQueryParams = Depends(),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取血糖记录列表"""
    query = db.query(GlucoseRecord).filter(
        GlucoseRecord.user_id == current_user.user_id
    )
    
    if meal_type:
        query = query.filter(GlucoseRecord.meal_type == meal_type)
    
    if params.start_date:
        query = query.filter(GlucoseRecord.measured_at >= params.start_date)
    if params.end_date:
        query = query.filter(GlucoseRecord.measured_at <= params.end_date)
    
    query = query.order_by(desc(GlucoseRecord.measured_at))
    records = query.offset(params.offset).limit(params.limit).all()
    return records


@router.get("/glucose/{record_id}", response_model=GlucoseResponse)
async def get_glucose_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个血糖记录"""
    record = db.query(GlucoseRecord).filter(
        GlucoseRecord.id == record_id,
        GlucoseRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return record


@router.put("/glucose/{record_id}", response_model=GlucoseResponse)
async def update_glucose_record(
    record_id: int,
    data: GlucoseUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新血糖记录"""
    record = db.query(GlucoseRecord).filter(
        GlucoseRecord.id == record_id,
        GlucoseRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    update_data = data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(record, field, value)
    
    # 重新检查正常范围
    if 'value' in update_data or 'meal_type' in update_data:
        record.is_normal = check_glucose_normal(record.value, record.meal_type)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/glucose/{record_id}")
async def delete_glucose_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除血糖记录"""
    record = db.query(GlucoseRecord).filter(
        GlucoseRecord.id == record_id,
        GlucoseRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "记录已删除"}


# ==================== 体重记录API ====================

@router.post("/weight", response_model=WeightResponse)
async def create_weight_record(
    data: WeightCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建体重记录"""
    # 获取用户身高计算BMI
    user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()
    bmi = data.calculate_bmi(user.height_cm if user else None)
    
    record = WeightRecord(
        user_id=current_user.user_id,
        weight_kg=data.weight_kg,
        bmi=bmi,
        body_fat_percent=data.body_fat_percent,
        muscle_mass_kg=data.muscle_mass_kg,
        measured_at=data.measured_at,
        note=data.note
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/weight", response_model=List[WeightResponse])
async def list_weight_records(
    params: RecordQueryParams = Depends(),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取体重记录列表"""
    query = db.query(WeightRecord).filter(
        WeightRecord.user_id == current_user.user_id
    )
    
    if params.start_date:
        query = query.filter(WeightRecord.measured_at >= params.start_date)
    if params.end_date:
        query = query.filter(WeightRecord.measured_at <= params.end_date)
    
    query = query.order_by(desc(WeightRecord.measured_at))
    records = query.offset(params.offset).limit(params.limit).all()
    return records


@router.get("/weight/{record_id}", response_model=WeightResponse)
async def get_weight_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单条体重记录"""
    record = db.query(WeightRecord).filter(
        WeightRecord.id == record_id,
        WeightRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return record


@router.put("/weight/{record_id}", response_model=WeightResponse)
async def update_weight_record(
    record_id: int,
    data: WeightUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新体重记录"""
    record = db.query(WeightRecord).filter(
        WeightRecord.id == record_id,
        WeightRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    update_data = data.dict(exclude_unset=True)
    
    # 如果体重改变，重新计算BMI
    if 'weight_kg' in update_data:
        user = db.query(UserModel).filter(UserModel.id == current_user.user_id).first()
        height_cm = user.height_cm if user else None
        if height_cm:
            height_m = height_cm / 100
            record.bmi = round(update_data['weight_kg'] / (height_m ** 2), 1)
    
    for field, value in update_data.items():
        if field != 'weight_kg':  # BMI已单独处理
            setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/weight/{record_id}")
async def delete_weight_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除体重记录"""
    record = db.query(WeightRecord).filter(
        WeightRecord.id == record_id,
        WeightRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "记录已删除"}


@router.get("/weight/stats/trend")
async def get_weight_trend(
    days: int = Query(30, ge=7, le=365, description="天数"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取体重趋势"""
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    records = db.query(WeightRecord).filter(
        WeightRecord.user_id == current_user.user_id,
        WeightRecord.measured_at >= start_date
    ).order_by(WeightRecord.measured_at).all()
    
    if not records or len(records) < 2:
        return {
            "trend": "insufficient_data",
            "change_kg": None,
            "records_count": len(records)
        }
    
    first_weight = records[0].weight_kg
    latest_weight = records[-1].weight_kg
    change = round(latest_weight - first_weight, 2)
    
    if change < -0.5:
        trend = "decreasing"
    elif change > 0.5:
        trend = "increasing"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "change_kg": change,
        "first_weight": first_weight,
        "latest_weight": latest_weight,
        "records_count": len(records),
        "period_days": days
    }


# ==================== 睡眠记录API ====================

@router.post("/sleep", response_model=SleepResponse)
async def create_sleep_record(
    data: SleepCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建睡眠记录"""
    duration = int((data.wake_time - data.bed_time).total_seconds() / 60)
    
    record = SleepRecord(
        user_id=current_user.user_id,
        bed_time=data.bed_time,
        wake_time=data.wake_time,
        duration_minutes=duration,
        sleep_quality=data.sleep_quality,
        deep_sleep_minutes=data.deep_sleep_minutes,
        light_sleep_minutes=data.light_sleep_minutes,
        rem_sleep_minutes=data.rem_sleep_minutes,
        awake_times=data.awake_times,
        note=data.note
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/sleep", response_model=List[SleepResponse])
async def list_sleep_records(
    params: RecordQueryParams = Depends(),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取睡眠记录列表"""
    query = db.query(SleepRecord).filter(
        SleepRecord.user_id == current_user.user_id
    )
    
    if params.start_date:
        query = query.filter(SleepRecord.bed_time >= params.start_date)
    if params.end_date:
        query = query.filter(SleepRecord.bed_time <= params.end_date)
    
    query = query.order_by(desc(SleepRecord.bed_time))
    records = query.offset(params.offset).limit(params.limit).all()
    return records


@router.get("/sleep/{record_id}", response_model=SleepResponse)
async def get_sleep_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单条睡眠记录"""
    record = db.query(SleepRecord).filter(
        SleepRecord.id == record_id,
        SleepRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return record


@router.put("/sleep/{record_id}", response_model=SleepResponse)
async def update_sleep_record(
    record_id: int,
    data: SleepUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新睡眠记录"""
    record = db.query(SleepRecord).filter(
        SleepRecord.id == record_id,
        SleepRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    update_data = data.dict(exclude_unset=True)
    
    # 如果时间改变，重新计算时长
    bed_time = update_data.get('bed_time', record.bed_time)
    wake_time = update_data.get('wake_time', record.wake_time)
    record.duration_minutes = int((wake_time - bed_time).total_seconds() / 60)
    
    for field, value in update_data.items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/sleep/{record_id}")
async def delete_sleep_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除睡眠记录"""
    record = db.query(SleepRecord).filter(
        SleepRecord.id == record_id,
        SleepRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "记录已删除"}


@router.get("/sleep/stats/summary")
async def get_sleep_summary(
    days: int = Query(7, ge=1, le=90),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取睡眠统计摘要"""
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    records = db.query(SleepRecord).filter(
        SleepRecord.user_id == current_user.user_id,
        SleepRecord.bed_time >= start_date
    ).all()
    
    if not records:
        return {
            "period_days": days,
            "records_count": 0,
            "average_duration_hours": None,
            "average_quality": None
        }
    
    avg_duration = sum(r.duration_minutes for r in records) / len(records) / 60
    avg_quality = sum(r.sleep_quality for r in records if r.sleep_quality) / len([r for r in records if r.sleep_quality]) if any(r.sleep_quality for r in records) else None
    
    return {
        "period_days": days,
        "records_count": len(records),
        "average_duration_hours": round(avg_duration, 1),
        "average_quality": round(avg_quality, 1) if avg_quality else None,
        "recommended_hours": 7.5,
        "sleep_debt_hours": max(0, round(7.5 * days - sum(r.duration_minutes for r in records) / 60, 1))
    }


# ==================== 心率记录API ====================

@router.post("/heart-rate", response_model=HeartRateResponse)
async def create_hr_record(
    data: HeartRateCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建心率记录"""
    record = HeartRateRecord(
        user_id=current_user.user_id,
        bpm=data.bpm,
        activity=data.activity,
        measured_at=data.measured_at,
        note=data.note
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/heart-rate", response_model=List[HeartRateResponse])
async def list_hr_records(
    activity: Optional[str] = Query(None, description="按活动状态筛选: resting/walking/exercising"),
    params: RecordQueryParams = Depends(),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取心率记录列表"""
    query = db.query(HeartRateRecord).filter(
        HeartRateRecord.user_id == current_user.user_id
    )
    
    if activity:
        query = query.filter(HeartRateRecord.activity == activity)
    
    if params.start_date:
        query = query.filter(HeartRateRecord.measured_at >= params.start_date)
    if params.end_date:
        query = query.filter(HeartRateRecord.measured_at <= params.end_date)
    
    query = query.order_by(desc(HeartRateRecord.measured_at))
    records = query.offset(params.offset).limit(params.limit).all()
    return records


@router.get("/heart-rate/{record_id}", response_model=HeartRateResponse)
async def get_hr_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单条心率记录"""
    record = db.query(HeartRateRecord).filter(
        HeartRateRecord.id == record_id,
        HeartRateRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    return record


@router.put("/heart-rate/{record_id}", response_model=HeartRateResponse)
async def update_hr_record(
    record_id: int,
    data: HeartRateUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新心率记录"""
    record = db.query(HeartRateRecord).filter(
        HeartRateRecord.id == record_id,
        HeartRateRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    update_data = data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    return record


@router.delete("/heart-rate/{record_id}")
async def delete_hr_record(
    record_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除心率记录"""
    record = db.query(HeartRateRecord).filter(
        HeartRateRecord.id == record_id,
        HeartRateRecord.user_id == current_user.user_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    db.delete(record)
    db.commit()
    return {"success": True, "message": "记录已删除"}


@router.get("/heart-rate/stats/resting")
async def get_resting_hr_stats(
    days: int = Query(30, ge=7, le=90),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取静息心率统计"""
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    resting_records = db.query(HeartRateRecord).filter(
        HeartRateRecord.user_id == current_user.user_id,
        HeartRateRecord.activity == "resting",
        HeartRateRecord.measured_at >= start_date
    ).all()
    
    if not resting_records:
        return {
            "period_days": days,
            "resting_records_count": 0,
            "average_resting_hr": None,
            "min_hr": None,
            "max_hr": None
        }
    
    hr_values = [r.bpm for r in resting_records]
    
    return {
        "period_days": days,
        "resting_records_count": len(resting_records),
        "average_resting_hr": round(sum(hr_values) / len(hr_values), 1),
        "min_hr": min(hr_values),
        "max_hr": max(hr_values),
        "healthy_range": {"min": 60, "max": 100},
        "athlete_range": {"min": 40, "max": 60}
    }


# ==================== 综合健康概览API ====================

@router.get("/overview")
async def get_health_overview(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取综合健康概览
    
    汇总所有健康指标的最新数据和统计
    """
    from datetime import datetime, timedelta
    
    user_id = current_user.user_id
    last_7_days = datetime.now() - timedelta(days=7)
    
    # 各项最新记录
    latest_bp = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.user_id == user_id
    ).order_by(desc(BloodPressureRecord.measured_at)).first()
    
    latest_glucose = db.query(GlucoseRecord).filter(
        GlucoseRecord.user_id == user_id
    ).order_by(desc(GlucoseRecord.measured_at)).first()
    
    latest_weight = db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id
    ).order_by(desc(WeightRecord.measured_at)).first()
    
    latest_sleep = db.query(SleepRecord).filter(
        SleepRecord.user_id == user_id
    ).order_by(desc(SleepRecord.bed_time)).first()
    
    latest_hr = db.query(HeartRateRecord).filter(
        HeartRateRecord.user_id == user_id
    ).order_by(desc(HeartRateRecord.measured_at)).first()
    
    # 7天统计
    bp_count_7d = db.query(BloodPressureRecord).filter(
        BloodPressureRecord.user_id == user_id,
        BloodPressureRecord.measured_at >= last_7_days
    ).count()
    
    glucose_count_7d = db.query(GlucoseRecord).filter(
        GlucoseRecord.user_id == user_id,
        GlucoseRecord.measured_at >= last_7_days
    ).count()
    
    return {
        "success": True,
        "latest_data": {
            "blood_pressure": latest_bp.to_dict() if latest_bp else None,
            "glucose": latest_glucose.to_dict() if latest_glucose else None,
            "weight": latest_weight.to_dict() if latest_weight else None,
            "sleep": latest_sleep.to_dict() if latest_sleep else None,
            "heart_rate": latest_hr.to_dict() if latest_hr else None
        },
        "this_week": {
            "bp_records": bp_count_7d,
            "glucose_records": glucose_count_7d,
            "days_tracked": len(set([
                latest_bp.measured_at.date() if latest_bp else None,
                latest_glucose.measured_at.date() if latest_glucose else None,
                latest_weight.measured_at.date() if latest_weight else None,
                latest_sleep.bed_time.date() if latest_sleep else None
            ]) - {None})
        },
        "data_completeness": {
            "has_bp_data": latest_bp is not None,
            "has_glucose_data": latest_glucose is not None,
            "has_weight_data": latest_weight is not None,
            "has_sleep_data": latest_sleep is not None,
            "has_hr_data": latest_hr is not None
        }
    }
