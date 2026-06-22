"""
🌸 若曦V2 - 可视化API
提供健康数据可视化图表接口
"""

from datetime import datetime
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from core.scheduler.task_scheduler import (
    TaskType,
    ruoxi_reminder_callback,
    task_scheduler,
)
from core.visualization.health_charts import chart_generator

router = APIRouter(prefix="/visualization", tags=["可视化"])


@router.get("/charts/blood-pressure")
async def get_bp_chart(days: int = 7, current_user=Depends(get_current_user)):
    """获取血压趋势图表数据"""
    # TODO: 从数据库获取真实数据
    mock_data = [
        {
            "systolic": 118,
            "diastolic": 78,
            "timestamp": (datetime.utcnow() - datetime.timedelta(days=i)).isoformat(),
        }
        for i in range(days, 0, -1)
    ]

    chart_data = chart_generator.generate_bp_chart_data(mock_data, days)

    return {
        "success": True,
        "data": chart_data,
        "chart_type": "blood_pressure",
        "days": days,
    }


@router.get("/charts/blood-glucose")
async def get_glucose_chart(days: int = 7, current_user=Depends(get_current_user)):
    """获取血糖趋势图表数据"""
    mock_data = [
        {
            "value": 5.2 + (i % 3) * 0.3,
            "timestamp": (datetime.utcnow() - datetime.timedelta(days=i)).isoformat(),
        }
        for i in range(days, 0, -1)
    ]

    chart_data = chart_generator.generate_glucose_chart_data(mock_data, days)

    return {
        "success": True,
        "data": chart_data,
        "chart_type": "blood_glucose",
        "days": days,
    }


@router.get("/charts/sleep")
async def get_sleep_chart(days: int = 7, current_user=Depends(get_current_user)):
    """获取睡眠趋势图表数据"""
    mock_data = [
        {
            "duration_hours": 7 + (i % 3) * 0.5,
            "efficiency": 85 + (i % 2) * 5,
            "timestamp": (datetime.utcnow() - datetime.timedelta(days=i)).isoformat(),
        }
        for i in range(days, 0, -1)
    ]

    chart_data = chart_generator.generate_sleep_chart_data(mock_data, days)

    return {"success": True, "data": chart_data, "chart_type": "sleep", "days": days}


@router.get("/charts/emotion")
async def get_emotion_chart(days: int = 30, current_user=Depends(get_current_user)):
    """获取情绪分布图表数据"""
    mock_data = {"happy": 12, "calm": 8, "tired": 5, "anxious": 3, "sad": 2}

    chart_data = chart_generator.generate_emotion_chart_data(mock_data)

    return {"success": True, "data": chart_data, "chart_type": "emotion", "days": days}


@router.get("/dashboard/comprehensive")
async def get_comprehensive_dashboard(
    days: int = 7, current_user=Depends(get_current_user)
):
    """获取综合健康仪表盘"""
    health_data = {
        "blood_pressure": [
            {
                "systolic": 118,
                "diastolic": 78,
                "timestamp": (
                    datetime.utcnow() - datetime.timedelta(days=i)
                ).isoformat(),
            }
            for i in range(days, 0, -1)
        ],
        "blood_glucose": [
            {
                "value": 5.2 + (i % 3) * 0.3,
                "timestamp": (
                    datetime.utcnow() - datetime.timedelta(days=i)
                ).isoformat(),
            }
            for i in range(days, 0, -1)
        ],
        "sleep": [
            {
                "duration_hours": 7 + (i % 3) * 0.5,
                "efficiency": 85 + (i % 2) * 5,
                "timestamp": (
                    datetime.utcnow() - datetime.timedelta(days=i)
                ).isoformat(),
            }
            for i in range(days, 0, -1)
        ],
    }

    emotion_data = {
        "emotion_summary": {"happy": 12, "calm": 8, "tired": 5, "anxious": 3, "sad": 2}
    }

    dashboard = chart_generator.generate_comprehensive_dashboard(
        health_data, emotion_data
    )

    return {
        "success": True,
        "data": dashboard,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ========== 任务调度API ==========


@router.post("/scheduler/tasks")
async def create_task(
    name: str, cron: str, task_type: str, current_user=Depends(get_current_user)
):
    """创建定时任务"""
    try:
        task_id = task_scheduler.add_task(
            name=name,
            task_type=TaskType[task_type],
            cron_expression=cron,
            callback=ruoxi_reminder_callback,
            user_id=current_user.user_id,
        )

        return {
            "success": True,
            "task_id": task_id,
            "message": f"任务 '{name}' 创建成功",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scheduler/tasks")
async def list_tasks(current_user=Depends(get_current_user)):
    """获取用户任务列表"""
    tasks = task_scheduler.get_task_list(user_id=current_user.user_id)

    return {
        "success": True,
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "type": t.task_type.name,
                "cron": t.cron_expression,
                "enabled": t.enabled,
                "next_run": t.next_run.isoformat() if t.next_run else None,
                "run_count": t.run_count,
            }
            for t in tasks
        ],
        "total": len(tasks),
    }


@router.delete("/scheduler/tasks/{task_id}")
async def delete_task(task_id: str, current_user=Depends(get_current_user)):
    """删除定时任务"""
    success = task_scheduler.remove_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {"success": True, "message": "任务已删除"}


@router.post("/scheduler/tasks/{task_id}/enable")
async def enable_task(task_id: str, current_user=Depends(get_current_user)):
    """启用定时任务"""
    success = task_scheduler.enable_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {"success": True, "message": "任务已启用"}


@router.post("/scheduler/tasks/{task_id}/disable")
async def disable_task(task_id: str, current_user=Depends(get_current_user)):
    """禁用定时任务"""
    success = task_scheduler.disable_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {"success": True, "message": "任务已禁用"}


@router.get("/scheduler/stats")
async def get_scheduler_stats(current_user=Depends(get_current_user)):
    """获取调度器统计"""
    stats = task_scheduler.get_task_stats()

    return {"success": True, "stats": stats}
