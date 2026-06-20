"""
🌸 若曦V2 健康记录API
健康管理功能，记录和分析健康数据
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from core.log_manager import get_logger
from core.exceptions import ValidationException

logger = get_logger(__name__)

router = APIRouter()


class HealthRecordCreate(BaseModel):
    """创建健康记录请求"""
    user_id: str = Field(..., description="用户ID")
    record_type: str = Field(..., description="记录类型")
    # blood_pressure: 血压 {"systolic": 120, "diastolic": 80, "pulse": 72}
    # blood_glucose: 血糖 {"value": 5.6, "unit": "mmol/L", "time": "空腹"}
    # weight: 体重 {"value": 65.5, "unit": "kg", "bmi": 22.3}
    # sleep: 睡眠 {"duration": 7.5, "quality": "good"}
    # exercise: 运动 {"steps": 8000, "calories": 300}
    # medication: 用药 {"name": "维生素C", "dose": "1片", "time": "08:00"}
    data: Dict[str, Any] = Field(..., description="记录数据")
    recorded_at: Optional[str] = Field(default=None, description="记录时间ISO格式")
    notes: Optional[str] = Field(default=None, description="备注")


class HealthRecordResponse(BaseModel):
    """健康记录响应"""
    id: str
    user_id: str
    record_type: str
    data: Dict[str, Any]
    recorded_at: str
    analysis: Optional[str] = None
    suggestions: List[str] = []


class BloodPressureReading(BaseModel):
    """血压读数"""
    systolic: int = Field(..., ge=70, le=250, description="收缩压 mmHg")
    diastolic: int = Field(..., ge=40, le=150, description="舒张压 mmHg")
    pulse: Optional[int] = Field(default=None, ge=40, le=200, description="脉搏")


class WeightReading(BaseModel):
    """体重读数"""
    value: float = Field(..., gt=0, description="体重值")
    unit: str = Field(default="kg", description="单位")
    bmi: Optional[float] = Field(default=None, description="BMI指数")


class SleepReading(BaseModel):
    """睡眠读数"""
    duration: float = Field(..., gt=0, le=24, description="睡眠时长小时")
    quality: str = Field(default="normal", description="睡眠质量: poor/normal/good/excellent")
    bed_time: Optional[str] = None
    wake_time: Optional[str] = None


# 内存存储
health_records_db: Dict[str, Dict] = {}
record_counter = 0


def _generate_record_id() -> str:
    """生成记录ID"""
    global record_counter
    record_counter += 1
    return f"hr_{record_counter:06d}"


def _analyze_blood_pressure(data: Dict) -> Dict[str, Any]:
    """分析血压数据"""
    systolic = data.get("systolic", 0)
    diastolic = data.get("diastolic", 0)
    
    # ACC/AHA 2017标准
    if systolic < 120 and diastolic < 80:
        category = "正常"
        color = "green"
    elif 120 <= systolic < 130 and diastolic < 80:
        category = "高值血压"
        color = "yellow"
    elif (130 <= systolic < 140) or (80 <= diastolic < 90):
        category = "1级高血压"
        color = "orange"
    elif systolic >= 140 or diastolic >= 90:
        category = "2级高血压"
        color = "red"
    else:
        category = "未知"
        color = "gray"
    
    return {
        "category": category,
        "color": color,
        "suggestion": f"血压{classification_to_text(category)}，建议{'保持' if color == 'green' else '关注'}"
    }


def classification_to_text(category: str) -> str:
    """分类转文本"""
    mapping = {
        "正常": "正常",
        "高值血压": "偏高",
        "1级高血压": "轻度升高",
        "2级高血压": "显著升高"
    }
    return mapping.get(category, category)


@router.post("/", response_model=HealthRecordResponse)
async def create_health_record(record: HealthRecordCreate):
    """
    创建健康记录
    
    记录血压、体重、睡眠、运动等健康数据
    
    **请求示例 - 血压:**
    ```json
    {
        "user_id": "user_001",
        "record_type": "blood_pressure",
        "data": {
            "systolic": 120,
            "diastolic": 80,
            "pulse": 72
        },
        "notes": "早晨测量"
    }
    ```
    """
    global record_counter
    
    # 验证记录类型
    valid_types = ["blood_pressure", "blood_glucose", "weight", "sleep", "exercise", "medication", "checkup"]
    if record.record_type not in valid_types:
        raise ValidationException(f"无效的记录类型，必须是: {', '.join(valid_types)}")
    
    record_id = _generate_record_id()
    
    # 若曦的AI分析
    analysis = ""
    suggestions = []
    
    if record.record_type == "blood_pressure":
        result = _analyze_blood_pressure(record.data)
        analysis = f"血压分类: {result['category']}"
        suggestions.append(result['suggestion'])
    elif record.record_type == "weight":
        bmi = record.data.get("bmi", 0)
        if bmi:
            if bmi < 18.5:
                analysis = "体重偏轻"
                suggestions.append("建议适当增加营养")
            elif 18.5 <= bmi < 24:
                analysis = "体重正常"
                suggestions.append("继续保持")
            elif 24 <= bmi < 28:
                analysis = "超重"
                suggestions.append("建议控制饮食，增加运动")
            else:
                analysis = "肥胖"
                suggestions.append("建议咨询医生制定减重计划")
    elif record.record_type == "sleep":
        duration = record.data.get("duration", 0)
        if duration < 6:
            analysis = "睡眠不足"
            suggestions.append("建议每晚保证7-8小时睡眠")
        elif duration > 10:
            analysis = "睡眠过长"
            suggestions.append("建议规律作息")
        else:
            analysis = "睡眠正常"
    
    # 保存记录
    recorded_time = datetime.fromisoformat(record.recorded_at) if record.recorded_at else datetime.utcnow()
    
    health_records_db[record_id] = {
        "id": record_id,
        "user_id": record.user_id,
        "record_type": record.record_type,
        "data": record.data,
        "recorded_at": recorded_time,
        "analysis": analysis,
        "suggestions": suggestions,
        "notes": record.notes,
        "created_at": datetime.utcnow()
    }
    
    logger.info(f"🏥 健康记录创建 | {record_id} | 类型: {record.record_type} | 用户: {record.user_id}")
    
    rec = health_records_db[record_id]
    return HealthRecordResponse(
        id=rec["id"],
        user_id=rec["user_id"],
        record_type=rec["record_type"],
        data=rec["data"],
        recorded_at=rec["recorded_at"].isoformat(),
        analysis=rec["analysis"],
        suggestions=rec["suggestions"]
    )


@router.get("/", response_model=List[HealthRecordResponse])
async def list_health_records(
    user_id: str = Query(..., description="用户ID"),
    record_type: Optional[str] = Query(None, description="筛选记录类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=100)
):
    """获取健康记录列表"""
    # 筛选用户记录
    user_records = [rec for rec in health_records_db.values() if rec["user_id"] == user_id]
    
    # 按类型筛选
    if record_type:
        user_records = [rec for rec in user_records if rec["record_type"] == record_type]
    
    # 按日期筛选
    if start_date:
        start = datetime.fromisoformat(start_date)
        user_records = [rec for rec in user_records if rec["recorded_at"] >= start]
    
    if end_date:
        end = datetime.fromisoformat(end_date + "T23:59:59")
        user_records = [rec for rec in user_records if rec["recorded_at"] <= end]
    
    # 按时间倒序
    user_records.sort(key=lambda x: x["recorded_at"], reverse=True)
    
    # 限制数量
    user_records = user_records[:limit]
    
    return [
        HealthRecordResponse(
            id=rec["id"],
            user_id=rec["user_id"],
            record_type=rec["record_type"],
            data=rec["data"],
            recorded_at=rec["recorded_at"].isoformat(),
            analysis=rec.get("analysis"),
            suggestions=rec.get("suggestions", [])
        )
        for rec in user_records
    ]


@router.get("/trends/{user_id}")
async def get_health_trends(
    user_id: str,
    record_type: str = Query(..., description="记录类型"),
    days: int = Query(30, ge=7, le=365)
):
    """
    获取健康趋势
    
    分析一段时间内的健康数据变化
    """
    # 筛选指定类型的记录
    records = [
        rec for rec in health_records_db.values()
        if rec["user_id"] == user_id and rec["record_type"] == record_type
    ]
    
    if not records:
        return {
            "user_id": user_id,
            "record_type": record_type,
            "days": days,
            "data_points": 0,
            "trend": "无数据"
        }
    
    # 按时间排序
    records.sort(key=lambda x: x["recorded_at"])
    
    # 提取数值（不同类型不同逻辑）
    values = []
    for rec in records:
        if record_type == "blood_pressure":
            # 取平均值或收缩压
            val = rec["data"].get("systolic", 0)
        elif record_type == "weight":
            val = rec["data"].get("value", 0)
        elif record_type == "sleep":
            val = rec["data"].get("duration", 0)
        elif record_type == "exercise":
            val = rec["data"].get("steps", 0)
        else:
            val = 0
        
        if val:
            values.append(val)
    
    import statistics
    
    return {
        "user_id": user_id,
        "record_type": record_type,
        "days": days,
        "data_points": len(values),
        "current": values[-1] if values else None,
        "average": round(statistics.mean(values), 2) if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "trend": "上升" if len(values) >= 2 and values[-1] > values[0] else "下降" if len(values) >= 2 and values[-1] < values[0] else "平稳"
    }


@router.get("/summary/{user_id}")
async def get_health_summary(user_id: str):
    """
    获取健康总结
    
    若曦为用户生成的健康概况
    """
    user_records = [rec for rec in health_records_db.values() if rec["user_id"] == user_id]
    
    if not user_records:
        return {
            "user_id": user_id,
            "status": "无健康记录",
            "message": "还没有记录健康数据呢，开始记录吧~"
        }
    
    # 统计各类型
    type_counts = {}
    for rec in user_records:
        t = rec["record_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # 最近分析
    recent_analyses = [
        rec["analysis"] for rec in sorted(user_records, key=lambda x: x["recorded_at"], reverse=True)[:5]
        if rec.get("analysis")
    ]
    
    return {
        "user_id": user_id,
        "status": "有记录" if user_records else "无记录",
        "total_records": len(user_records),
        "record_types": type_counts,
        "recent_analyses": recent_analyses,
        "message": f"已记录{len(user_records)}条健康数据，继续加油哦~"
    }


@router.delete("/{record_id}")
async def delete_health_record(record_id: str):
    """删除健康记录"""
    if record_id not in health_records_db:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    del health_records_db[record_id]
    logger.info(f"🗑️ 健康记录删除: {record_id}")
    
    return {"success": True, "message": "记录已删除"}
