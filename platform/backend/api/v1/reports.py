"""
🌸 若曦V2 - 健康报告API
生成和下载健康报告PDF
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Optional, Literal
from datetime import date, timedelta
from pydantic import BaseModel

from platform.backend.core_auth.jwt_auth import get_current_user
from models.database import get_db
from sqlalchemy.orm import Session

from core.services.pdf_report_service import (
    PDFReportService,
    ReportPeriod,
    generate_weekly_report,
    generate_monthly_report
)


router = APIRouter(prefix="/reports", tags=["健康报告"])


# ==================== 响应模型 ====================

class ReportGenerateRequest(BaseModel):
    """报告生成请求"""
    report_type: Literal["daily", "weekly", "monthly", "quarterly", "yearly", "custom"] = "weekly"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_charts: bool = True
    include_recommendations: bool = True


class ReportResponse(BaseModel):
    """报告响应"""
    success: bool
    report_id: str
    report_type: str
    generated_at: str
    download_url: str
    preview_data: Optional[dict] = None


# ==================== API 端点 ====================

@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成健康报告
    
    生成指定周期的健康报告PDF，支持多种时间维度
    
    - **daily**: 日报（近1天）
    - **weekly**: 周报（近7天）
    - **monthly**: 月报（近30天）
    - **quarterly**: 季报（近90天）
    - **yearly**: 年报（近365天）
    - **custom**: 自定义日期范围
    """
    # 确定日期范围
    if request.report_type == "daily":
        end = date.today()
        start = end
    elif request.report_type == "weekly":
        end = date.today()
        start = end - timedelta(days=6)
    elif request.report_type == "monthly":
        end = date.today()
        start = end - timedelta(days=29)
    elif request.report_type == "quarterly":
        end = date.today()
        start = end - timedelta(days=89)
    elif request.report_type == "yearly":
        end = date.today()
        start = end - timedelta(days=364)
    else:  # custom
        if not request.start_date or not request.end_date:
            raise HTTPException(status_code=400, detail="自定义报告需要提供开始和结束日期")
        start = request.start_date
        end = request.end_date
    
    # 验证日期
    if start > end:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
    
    days = (end - start).days + 1
    if days > 366:
        raise HTTPException(status_code=400, detail="报告周期不能超过1年")
    
    # 生成报告数据
    import time
    report_id = f"RPT-{current_user.user_id}-{int(time.time())}"
    
    service = PDFReportService(db, current_user.user_id)
    period = ReportPeriod(start, end)
    
    try:
        report_data = service.generate_health_report(
            period=period,
            report_type="comprehensive",
            include_charts=request.include_charts
        )
        
        # 这里应该异步生成PDF并存储
        # 简化返回报告数据预览
        return {
            "success": True,
            "report_id": report_id,
            "report_type": request.report_type,
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "days": days
            },
            "generated_at": __import__('datetime').datetime.utcnow().isoformat(),
            "download_url": f"/api/v1/reports/download/{report_id}",
            "preview": {
                "health_score": report_data.get("health_overview", {}).get("health_score"),
                "data_summary": report_data.get("health_overview", {}).get("data_summary"),
                "recommendations_count": len(report_data.get("recommendations", []))
            },
            "full_data": report_data  # 实际生产环境应该存储而不是直接返回
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@router.get("/weekly")
async def get_weekly_report(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取周报
    
    便捷接口，直接获取最近一周的健康报告
    """
    try:
        report_data = generate_weekly_report(db, current_user.user_id)
        return {
            "success": True,
            "report_type": "weekly",
            "data": report_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"周报生成失败: {str(e)}")


@router.get("/monthly")
async def get_monthly_report(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取月报
    
    便捷接口，直接获取最近一个月的健康报告
    """
    try:
        report_data = generate_monthly_report(db, current_user.user_id)
        return {
            "success": True,
            "report_type": "monthly",
            "data": report_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"月报生成失败: {str(e)}")


@router.get("/summary")
async def get_report_summary(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取健康数据摘要
    
    简洁的健康数据汇总，用于仪表盘展示
    """
    end = date.today()
    start = end - timedelta(days=days-1)
    
    service = PDFReportService(db, current_user.user_id)
    period = ReportPeriod(start, end)
    
    try:
        overview = service._generate_health_overview(period)
        user_summary = service._generate_user_summary()
        
        return {
            "success": True,
            "period": {
                "days": days,
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "user": {
                "display_name": user_summary.get("display_name"),
                "bmi": user_summary.get("bmi")
            },
            "health_score": overview.get("health_score"),
            "data_summary": overview.get("data_summary"),
            "trend": overview.get("health_trend")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {str(e)}")


@router.get("/health-score")
async def get_health_score(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前健康评分
    
    基于最近30天数据计算的综合健康评分 (0-100)
    """
    end = date.today()
    start = end - timedelta(days=29)
    
    service = PDFReportService(db, current_user.user_id)
    score = service._calculate_overall_score(ReportPeriod(start, end))
    
    return {
        "success": True,
        "score": score.get("overall"),
        "interpretation": score.get("interpretation"),
        "details": score.get("details"),
        "calculated_at": __import__('datetime').datetime.utcnow().isoformat()
    }


@router.get("/trends")
async def get_health_trends(
    metric: str = Query(..., description="指标类型: bp/glucose/weight/sleep/hr"),
    days: int = Query(30, ge=7, le=365, description="天数"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取健康趋势数据
    
    用于生成趋势图表的数据
    """
    from sqlalchemy import func
    
    end = date.today() + timedelta(days=1)
    start = end - timedelta(days=days)
    
    try:
        if metric == "bp":
            records = db.query(
                func.date(BloodPressureRecord.measured_at).label("date"),
                func.avg(BloodPressureRecord.systolic).label("systolic"),
                func.avg(BloodPressureRecord.diastolic).label("diastolic")
            ).filter(
                BloodPressureRecord.user_id == current_user.user_id,
                BloodPressureRecord.measured_at >= start,
                BloodPressureRecord.measured_at < end
            ).group_by(func.date(BloodPressureRecord.measured_at)).all()
            
            return {
                "success": True,
                "metric": "blood_pressure",
                "data": [
                    {
                        "date": str(r.date),
                        "systolic": round(r.systolic, 1),
                        "diastolic": round(r.diastolic, 1)
                    }
                    for r in records
                ]
            }
        
        elif metric == "weight":
            records = db.query(WeightRecord).filter(
                WeightRecord.user_id == current_user.user_id,
                WeightRecord.measured_at >= start,
                WeightRecord.measured_at < end
            ).order_by(WeightRecord.measured_at).all()
            
            return {
                "success": True,
                "metric": "weight",
                "data": [
                    {
                        "date": r.measured_at.strftime("%Y-%m-%d"),
                        "weight_kg": r.weight_kg,
                        "bmi": r.bmi
                    }
                    for r in records
                ]
            }
        
        elif metric == "glucose":
            records = db.query(GlucoseRecord).filter(
                GlucoseRecord.user_id == current_user.user_id,
                GlucoseRecord.measured_at >= start,
                GlucoseRecord.measured_at < end
            ).order_by(GlucoseRecord.measured_at).all()
            
            return {
                "success": True,
                "metric": "glucose",
                "data": [
                    {
                        "date": r.measured_at.strftime("%Y-%m-%d %H:%M"),
                        "value": r.value,
                        "meal_type": r.meal_type,
                        "is_normal": r.is_normal
                    }
                    for r in records
                ]
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的指标类型: {metric}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势数据获取失败: {str(e)}")


@router.get("/recommendations")
async def get_recommendations(
    days: int = Query(30, ge=1, le=90, description="基于天数"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取个性化健康建议
    
    基于近期健康数据生成个性化建议
    """
    end = date.today()
    start = end - timedelta(days=days-1)
    
    service = PDFReportService(db, current_user.user_id)
    recommendations = service._generate_recommendations(ReportPeriod(start, end))
    
    return {
        "success": True,
        "period_days": days,
        "recommendations": recommendations,
        "generated_at": __import__('datetime').datetime.utcnow().isoformat()
    }


# 导入需要的模型
from models.database import BloodPressureRecord, GlucoseRecord, WeightRecord
