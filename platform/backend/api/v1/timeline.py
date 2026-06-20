"""
🌸 若曦V2 - 健康时间线API
时间线数据查询端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from core.health_timeline.timeline_engine import (
    timeline_engine,
    TimeRange,
    ChartType
)
from platform.backend.core_auth.jwt_auth import get_current_user


router = APIRouter(prefix="/timeline", tags=["健康时间线"])


@router.get("/views")
async def get_available_views(
    current_user = Depends(get_current_user)
):
    """
    获取可用的时间线视图
    
    返回所有预设的图表视图配置
    """
    views = timeline_engine.get_available_views()
    
    return {
        "success": True,
        "views": views
    }


@router.get("/data/{view_id}")
async def get_timeline_data(
    view_id: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user = Depends(get_current_user)
):
    """
    获取时间线数据
    
    返回指定视图的时间序列数据、事件标记和统计摘要
    
    示例视图ID:
    - bp_weekly: 血压周趋势
    - bp_monthly: 血压月趋势
    - glucose_daily: 血糖记录
    - weight_trend: 体重趋势
    - sleep_heatmap: 睡眠热力图
    - heart_rate: 心率分析
    - steps_weekly: 步数统计
    """
    try:
        # 解析自定义日期范围
        custom_range = None
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                custom_range = (start, end)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
        
        # 获取时间线数据
        data = await timeline_engine.get_timeline_data(
            user_id=str(current_user.user_id),
            view_id=view_id,
            custom_range=custom_range
        )
        
        return {
            "success": True,
            "data": data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间线数据失败: {str(e)}")


@router.post("/compare")
async def compare_periods(
    series_id: str,
    period1_start: str = Query(..., description="时间段1开始 (YYYY-MM-DD)"),
    period1_end: str = Query(..., description="时间段1结束 (YYYY-MM-DD)"),
    period2_start: str = Query(..., description="时间段2开始 (YYYY-MM-DD)"),
    period2_end: str = Query(..., description="时间段2结束 (YYYY-MM-DD)"),
    current_user = Depends(get_current_user)
):
    """
    对比两个时间段的指标变化
    
    用于比较治疗前后、不同生活方式阶段的效果
    """
    try:
        period1 = (
            datetime.strptime(period1_start, "%Y-%m-%d"),
            datetime.strptime(period1_end, "%Y-%m-%d")
        )
        period2 = (
            datetime.strptime(period2_start, "%Y-%m-%d"),
            datetime.strptime(period2_end, "%Y-%m-%d")
        )
        
        result = await timeline_engine.compare_periods(
            user_id=str(current_user.user_id),
            series_id=series_id,
            period1=period1,
            period2=period2
        )
        
        return {
            "success": True,
            "comparison": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比分析失败: {str(e)}")


@router.get("/overview")
async def get_timeline_overview(
    days: int = Query(30, ge=7, le=365, description="天数范围"),
    current_user = Depends(get_current_user)
):
    """
    获取时间线概览
    
    返回多个关键指标的快速概览
    """
    end = datetime.now()
    start = end - timedelta(days=days)
    
    # 获取多个视图的摘要
    view_ids = ["bp_weekly", "glucose_daily", "weight_trend", "sleep_heatmap"]
    summaries = []
    
    for view_id in view_ids:
        try:
            data = await timeline_engine.get_timeline_data(
                user_id=str(current_user.user_id),
                view_id=view_id,
                custom_range=(start, end)
            )
            
            summaries.append({
                "view_id": view_id,
                "view_name": data["view"]["name"],
                "summary": data["summary"]
            })
        except:
            pass
    
    return {
        "success": True,
        "days": days,
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat()
        },
        "summaries": summaries
    }


@router.get("/events")
async def get_timeline_events(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    event_type: Optional[str] = Query(None, description="事件类型过滤"),
    importance: Optional[str] = Query(None, description="重要性过滤: low, normal, high, critical"),
    current_user = Depends(get_current_user)
):
    """
    获取时间线事件
    
    包括用药提醒、异常告警、体检记录等
    """
    from core.health_timeline.timeline_engine import TimelineEvent
    
    # 默认最近30天
    if not start_date:
        start = datetime.now() - timedelta(days=30)
    else:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    
    if not end_date:
        end = datetime.now()
    else:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 获取事件
    events = await timeline_engine._fetch_events(
        user_id=str(current_user.user_id),
        start_date=start,
        end_date=end
    )
    
    # 过滤
    if event_type:
        events = [e for e in events if e.type == event_type]
    if importance:
        events = [e for e in events if e.importance == importance]
    
    # 按时间排序
    events.sort(key=lambda x: x.timestamp, reverse=True)
    
    return {
        "success": True,
        "events": [e.to_dict() for e in events],
        "total": len(events),
        "filters": {
            "event_type": event_type,
            "importance": importance
        }
    }


@router.get("/trends/{metric}")
async def get_metric_trends(
    metric: str,
    period: str = Query("1m", description="时间周期: 1d, 1w, 1m, 3m, 6m, 1y"),
    current_user = Depends(get_current_user)
):
    """
    获取单项指标趋势
    
    简化的趋势API，用于单个指标分析
    """
    # 映射周期
    period_map = {
        "1d": (datetime.now() - timedelta(days=1), datetime.now()),
        "1w": (datetime.now() - timedelta(weeks=1), datetime.now()),
        "1m": (datetime.now() - timedelta(days=30), datetime.now()),
        "3m": (datetime.now() - timedelta(days=90), datetime.now()),
        "6m": (datetime.now() - timedelta(days=180), datetime.now()),
        "1y": (datetime.now() - timedelta(days=365), datetime.now())
    }
    
    if period not in period_map:
        raise HTTPException(status_code=400, detail="无效的时间周期")
    
    start, end = period_map[period]
    
    # 获取数据
    series = await timeline_engine._fetch_series_data(
        user_id=str(current_user.user_id),
        series_id=metric,
        start_date=start,
        end_date=end,
        aggregation="daily_avg"
    )
    
    if not series:
        raise HTTPException(status_code=404, detail="指标不存在或无数据")
    
    series.calculate_stats()
    
    # 计算趋势
    if len(series.data) >= 2:
        first_val = series.data[0].value
        last_val = series.data[-1].value
        change = last_val - first_val
        change_pct = (change / first_val * 100) if first_val != 0 else 0
        
        # 简单线性趋势判断
        trend = "stable"
        if abs(change_pct) > 5:
            trend = "increasing" if change > 0 else "decreasing"
    else:
        change = 0
        change_pct = 0
        trend = "stable"
    
    return {
        "success": True,
        "metric": metric,
        "metric_name": series.name,
        "unit": series.unit,
        "period": period,
        "time_range": {
            "start": start.isoformat(),
            "end": end.isoformat()
        },
        "statistics": {
            "latest": series.latest_value,
            "average": round(series.avg_value, 2) if series.avg_value else None,
            "min": series.min_value,
            "max": series.max_value,
            "data_points": len(series.data)
        },
        "trend": {
            "direction": trend,
            "change": round(change, 2),
            "change_percentage": round(change_pct, 1)
        },
        "data": [dp.to_dict() for dp in series.data]
    }
