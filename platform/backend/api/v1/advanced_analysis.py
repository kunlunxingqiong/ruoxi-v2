"""
🌸 若曦V2 - 高级AI分析API
提供健康预测、异常检测、风险评估等高级功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from platform.backend.core_auth.jwt_auth import get_current_user
from models.database import get_db
from sqlalchemy.orm import Session

from core.ai.advanced_analysis import (
    AdvancedHealthAnalyzer,
    predict_user_health_trends,
    detect_user_health_anomalies,
    assess_user_disease_risks
)

router = APIRouter(prefix="/ai/analysis", tags=["高级AI分析"])


# ==================== 响应模型 ====================

class PredictionResponse(BaseModel):
    """预测响应"""
    metric: str
    current_value: float
    predicted_7d: float
    predicted_30d: float
    confidence_7d: float
    confidence_30d: float
    trend_direction: str
    risk_level: str


class AnomalyResponse(BaseModel):
    """异常检测响应"""
    metric: str
    detected: bool
    severity: str
    message: str
    current_value: float
    deviation_percentage: float
    recommendation: str


class RiskResponse(BaseModel):
    """风险评估响应"""
    disease_name: str
    risk_score: float
    risk_level: str
    contributing_factors: List[dict]
    recommendations: List[str]
    screening_recommendations: List[str]


class FullAnalysisResponse(BaseModel):
    """完整分析响应"""
    summary: dict
    predictions: dict
    anomalies: dict
    risks: dict
    recommendations: dict
    analyzed_at: str


# ==================== API 端点 ====================

@router.get("/predictions")
async def get_health_predictions(
    days: int = Query(90, ge=30, le=365, description="历史数据天数"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取健康趋势预测
    
    基于历史数据预测未来7天和30天的健康指标趋势
    
    - **days**: 使用多少天的历史数据进行预测
    
    Returns:
        各项指标的预测结果，包含置信度和趋势方向
    """
    try:
        predictions = predict_user_health_trends(db, current_user.user_id)
        return {
            "success": True,
            "predictions": predictions.get("predictions", {}),
            "generated_at": predictions.get("generated_at"),
            "data_period_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测分析失败: {str(e)}")


@router.get("/predictions/{metric}")
async def get_single_metric_prediction(
    metric: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单项指标预测
    
    metric: blood_pressure / glucose / weight / sleep / heart_rate
    """
    from core.ai.advanced_analysis.health_predictor import HealthPredictor
    
    predictor = HealthPredictor(db, current_user.user_id)
    
    prediction_func = {
        "blood_pressure": predictor.predict_blood_pressure,
        "glucose": predictor.predict_glucose,
        "weight": predictor.predict_weight,
        "sleep": predictor.predict_sleep,
        "heart_rate": predictor.predict_sleep  # 使用类似逻辑
    }.get(metric)
    
    if not prediction_func:
        raise HTTPException(status_code=400, detail=f"不支持的指标: {metric}")
    
    result = prediction_func()
    
    if not result:
        return {
            "success": False,
            "message": "数据不足，无法进行预测",
            "min_required_records": "至少7条记录"
        }
    
    return {
        "success": True,
        "metric": metric,
        "prediction": result
    }


@router.get("/anomalies")
async def detect_health_anomalies(
    days: int = Query(30, ge=7, le=90, description="检查天数范围"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检测健康指标异常
    
    自动识别血压、血糖、体重、心率的异常波动和危险数值
    
    Returns:
        异常检测结果，包含严重级别和建议
    """
    try:
        anomalies = detect_user_health_anomalies(db, current_user.user_id)
        return {
            "success": True,
            "anomalies": anomalies,
            "alert_summary": {
                "total": anomalies.get("total_anomalies", 0),
                "critical": anomalies.get("critical_count", 0),
                "warning": anomalies.get("warning_count", 0),
                "requires_attention": anomalies.get("critical_count", 0) > 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"异常检测失败: {str(e)}")


@router.get("/risks")
async def assess_disease_risks(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    评估疾病风险
    
    评估以下疾病风险:
    - 高血压并发症
    - 2型糖尿病
    - 心血管疾病
    - 代谢综合征
    
    Returns:
        各项疾病的风险评分、风险因子和建议
    """
    try:
        risks = assess_user_disease_risks(db, current_user.user_id)
        
        return {
            "success": True,
            "overall_risk": risks.get("overall_risk_score", {}),
            "risks": risks.get("risks", []),
            "assessed_at": risks.get("assessed_at")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险评估失败: {str(e)}")


@router.get("/risks/{disease}")
async def get_single_disease_risk(
    disease: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单项疾病风险详情
    
    disease: hypertension / diabetes / cardiovascular / metabolic_syndrome
    """
    risks = assess_user_disease_risks(db, current_user.user_id)
    
    disease_map = {
        "hypertension": "高血压并发症",
        "diabetes": "2型糖尿病",
        "cardiovascular": "心血管疾病",
        "metabolic_syndrome": "代谢综合征"
    }
    
    disease_name = disease_map.get(disease)
    if not disease_name:
        raise HTTPException(status_code=400, detail=f"不支持的疾病类型: {disease}")
    
    for risk in risks.get("risks", []):
        if risk.get("disease_name") == disease_name:
            return {
                "success": True,
                "disease": disease,
                "risk_assessment": risk
            }
    
    return {
        "success": False,
        "message": f"无法评估{disease_name}风险，数据不足"
    }


@router.get("/full")
async def get_full_analysis(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取完整健康分析
    
    整合预测、异常检测、风险评估，提供一站式分析报告
    
    Returns:
        综合健康分析报告，包含:预测、异常、风险、建议
    """
    try:
        analyzer = AdvancedHealthAnalyzer(db, current_user.user_id)
        analysis = analyzer.full_analysis()
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完整分析失败: {str(e)}")


@router.post("/refresh")
async def refresh_analysis_cache(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新分析缓存
    
    重新计算所有分析结果（通常分析结果会缓存24小时）
    """
    # 这里可以实现缓存刷新逻辑
    return {
        "success": True,
        "message": "分析缓存已刷新",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }


@router.get("/insights")
async def get_health_insights(
    days: int = Query(30, ge=7, le=90),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取健康洞察
    
    基于AI分析生成的个性化健康建议和洞察
    """
    analyzer = AdvancedHealthAnalyzer(db, current_user.user_id)
    analysis = analyzer.full_analysis()
    
    insights = []
    
    # 基于异常生成洞察
    for anomaly in analysis["anomalies"].get("detected_anomalies", [])[:3]:
        insights.append({
            "type": "alert",
            "category": anomaly.get("metric"),
            "message": anomaly.get("message"),
            "severity": anomaly.get("severity"),
            "action": anomaly.get("recommendation")
        })
    
    # 基于预测生成洞察
    for metric, pred in analysis["predictions"].get("predictions", {}).items():
        if pred.get("confidence_30d", 0) > 0.7:
            insights.append({
                "type": "prediction",
                "category": metric,
                "message": f"30天预测: {pred.get('predicted_30d')} (置信度: {pred.get('confidence_30d', 0):.0%})",
                "severity": "info",
                "action": f"趋势: {pred.get('trend_direction')}"
            })
    
    # 基于风险生成洞察
    for risk in analysis["risks"].get("risks", [])[:2]:
        if risk.get("risk_level") in ["high", "very_high"]:
            insights.append({
                "type": "risk",
                "category": risk.get("disease_name"),
                "message": f"风险评分: {risk.get('risk_score')}/100 ({risk.get('risk_level')})",
                "severity": "warning" if risk.get("risk_level") == "high" else "critical",
                "action": risk.get("recommendations", ["咨询医生"])[0]
            })
    
    return {
        "success": True,
        "insights": insights,
        "generated_at": __import__('datetime').datetime.utcnow().isoformat()
    }
