"""
🌸 若曦V2 - 健康分析API
基于健康服务层提供的高级分析端点
"""

from datetime import date
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import Optional

from fastapi import APIRouter, Depends, Query
from models.database import get_db
from sqlalchemy.orm import Session

from core.services.health_service import HealthService

router = APIRouter(prefix="/analysis", tags=["健康分析"])


@router.get("/blood-pressure/statistics")
async def get_bp_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取血压统计分析

    返回平均、最大、最小、标准差等统计指标
    """
    service = HealthService(db)
    stats = service.get_bp_statistics(
        user_id=current_user.user_id, start_date=start_date, end_date=end_date
    )
    return {"success": True, "statistics": stats}


@router.get("/blood-pressure/morning-surge")
async def get_morning_surge(
    days: int = Query(7, ge=3, le=30),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    检测晨峰血压 (Morning Surge)

    晨间血压高于其他时段20mmHg以上定义为晨峰
    """
    service = HealthService(db)
    result = service.get_morning_bp_surge(user_id=current_user.user_id, days=days)
    return {"success": True, "morning_surge": result}


@router.get("/glucose/trends")
async def get_glucose_trends(
    days: int = Query(30, ge=7, le=90),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取血糖趋势分析

    按时段统计、控制率、趋势方向
    """
    service = HealthService(db)
    trends = service.get_glucose_trends(user_id=current_user.user_id, days=days)
    return {"success": True, "trends": trends}


@router.get("/weight/progress")
async def get_weight_progress(
    goal_weight: Optional[float] = Query(None, description="目标体重kg"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取体重进度

    计算从开始到当前的体重变化，距离目标的差距
    """
    service = HealthService(db)
    progress = service.calculate_weight_progress(
        user_id=current_user.user_id, goal_weight=goal_weight
    )
    return {"success": True, "progress": progress}


@router.get("/sleep/quality-score")
async def get_sleep_quality_score(
    days: int = Query(7, ge=3, le=30),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    计算睡眠质量评分

    基于时长、自评、深睡比例、醒来次数综合评分 (0-100)
    """
    service = HealthService(db)
    score = service.get_sleep_quality_score(user_id=current_user.user_id, days=days)
    return {"success": True, "sleep_analysis": score}


@router.get("/heart-rate/hrv")
async def get_hrv_analysis(
    days: int = Query(7, ge=5, le=30),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取心率变异性分析

    HRV是心脏健康和自主神经功能的重要指标
    """
    service = HealthService(db)
    hrv = service.get_heart_rate_variability(user_id=current_user.user_id, days=days)
    return {"success": True, "hrv": hrv}


@router.get("/overall-score")
async def get_overall_health_score(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取综合健康评分

    基于血压、血糖、体重、睡眠、心率计算0-100的综合评分
    """
    service = HealthService(db)
    score = service.get_health_score(user_id=current_user.user_id)
    return {"success": True, "health_score": score}


@router.get("/weekly-report")
async def get_weekly_report(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    生成周健康报告

    汇总过去7天的所有健康数据和分析
    """
    service = HealthService(db)
    report = service.generate_weekly_report(user_id=current_user.user_id)
    return {"success": True, "weekly_report": report}
