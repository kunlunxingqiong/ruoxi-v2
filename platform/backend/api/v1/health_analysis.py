"""
🌸 若曦V2 健康分析API
健康数据智能分析接口
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

from core.health.health_analyzer import health_analyzer, HealthAnalysisResult
from core.auth import get_current_user, UserAuth
from core.log_manager import get_logger

logger = get_logger(__name__)

router = APIRouter()


class HealthDataPoint(BaseModel):
    """健康数据点"""
    metric_type: str = Field(..., description="指标类型: blood_pressure/blood_glucose/sleep")
    value: Optional[float] = Field(default=None, description="数值")
    unit: str = Field(default="", description="单位")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    systolic: Optional[float] = Field(default=None, description="收缩压")
    diastolic: Optional[float] = Field(default=None, description="舒张压")
    notes: Optional[str] = Field(default=None, description="备注")


class AnalysisRequest(BaseModel):
    """分析请求"""
    metric_type: str = Field(..., description="指标类型")
    records: List[HealthDataPoint] = Field(default=[], description="历史记录")


class AnalysisResponse(BaseModel):
    """分析响应"""
    metric_type: str
    current_status: str
    trend: str
    risk_level: str
    suggestions: List[str]
    abnormal_flags: List[str]
    summary: str


class HealthReportRequest(BaseModel):
    """健康报告请求"""
    include_metrics: List[str] = Field(default=["blood_pressure", "blood_glucose", "sleep"])
    date_range_days: int = Field(default=30, description="数据时间范围")


@router.post("/analyze/{metric_type}", response_model=AnalysisResponse)
async def analyze_metric(
    metric_type: str,
    request: AnalysisRequest,
    user: UserAuth = Depends(get_current_user)
):
    """
    分析特定健康指标
    
    **支持的指标:**
    - `blood_pressure` - 血压
    - `blood_glucose` - 血糖
    - `sleep` - 睡眠
    
    **示例:**
    ```json
    {
        "records": [
            {"metric_type": "blood_pressure", "systolic": 120, "diastolic": 80, "timestamp": "2026-06-21T10:00:00"}
        ]
    }
    ```
    """
    # 转换为分析器格式
    from core.health.health_analyzer import HealthMetric
    
    metrics = [
        HealthMetric(
            metric_type=r.metric_type,
            value=r.value or 0,
            unit=r.unit,
            timestamp=datetime.fromisoformat(r.timestamp),
            systolic=r.systolic,
            diastolic=r.diastolic,
            notes=r.notes
        )
        for r in request.records
    ]
    
    # 分析
    if metric_type == "blood_pressure":
        result = health_analyzer.analyze_blood_pressure(metrics)
    elif metric_type == "blood_glucose":
        result = health_analyzer.analyze_blood_glucose(metrics)
    elif metric_type == "sleep":
        result = health_analyzer.analyze_sleep(metrics)
    else:
        result = HealthAnalysisResult(
            metric_type=metric_type,
            current_status="不支持",
            trend="未知",
            risk_level="未知",
            suggestions=["暂不支持此指标分析"],
            abnormal_flags=[],
            summary="该指标类型暂不支持自动分析。"
        )
    
    logger.info(f"💜 健康分析 | 用户: {user.user_id} | 指标: {metric_type}")
    
    return AnalysisResponse(
        metric_type=result.metric_type,
        current_status=result.current_status,
        trend=result.trend,
        risk_level=result.risk_level,
        suggestions=result.suggestions,
        abnormal_flags=result.abnormal_flags,
        summary=result.summary
    )


@router.post("/report")
async def generate_health_report(
    request: HealthReportRequest,
    user: UserAuth = Depends(get_current_user)
):
    """
    生成综合健康报告
    
    AI驱动的个性化健康报告
    """
    # TODO: 从数据库获取用户真实数据
    # 这里使用模拟数据
    from core.health.health_analyzer import HealthMetric
    
    mock_records = {
        "blood_pressure": [
            HealthMetric("blood_pressure", 0, "mmHg", datetime.now(), systolic=118, diastolic=76),
            HealthMetric("blood_pressure", 0, "mmHg", datetime.now(), systolic=125, diastolic=82),
            HealthMetric("blood_pressure", 0, "mmHg", datetime.now(), systolic=122, diastolic=78),
        ]
    }
    
    # 生成报告
    report = await health_analyzer.generate_health_report(
        user_id=user.user_id,
        health_records=mock_records
    )
    
    logger.info(f"📊 健康报告生成 | 用户: {user.user_id}")
    
    return {
        "user_id": user.user_id,
        "generated_at": datetime.utcnow().isoformat(),
        "report": report,
        "disclaimer": "此报告由AI生成，仅供参考，不能替代专业医疗建议。"
    }


@router.post("/ask")
async def ask_health_question(
    question: str,
    user: UserAuth = Depends(get_current_user)
):
    """
    健康问答
    
    向若曦咨询健康问题
    
    **注意:** AI回答仅供参考，不能替代专业医疗建议。
    
    **示例:**
    ```json
    {
        "question": "血压120/80正常吗？"
    }
    ```
    """
    # 模拟用户健康数据 (实际应从数据库获取)
    user_health = {
        "user_id": user.user_id,
        "recent_metrics": ["blood_pressure"],
        "known_conditions": []
    }
    
    answer = await health_analyzer.answer_health_question(
        question=question,
        user_health_data=user_health
    )
    
    logger.info(f"💬 健康问答 | 用户: {user.user_id} | 问题: {question[:30]}...")
    
    return {
        "question": question,
        "answer": answer,
        "disclaimer": "AI回答仅供参考，如有健康问题请咨询专业医生。",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/stats")
async def get_health_stats(user: UserAuth = Depends(get_current_user)):
    """获取用户健康统计概览"""
    # TODO: 从数据库获取真实统计
    
    return {
        "user_id": user.user_id,
        "metrics_tracked": ["blood_pressure"],  # 用户正在追踪的指标
        "record_count": {
            "blood_pressure": 15,
            "total": 15
        },
        "last_recorded": datetime.utcnow().isoformat(),
        "health_score": 85,  # 综合健康评分 0-100
        "high_risk_areas": []  # 高风险区域
    }
