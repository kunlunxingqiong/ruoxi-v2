"""
🌸 若曦V2 - 个人健康仪表盘API
聚合展示用户健康数据概览
"""

from platform.backend.core_auth.jwt_auth import get_current_user
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from models.database import get_db
from sqlalchemy.orm import Session

from core.services.dashboard_service import DashboardService, get_dashboard_data
from core.services.user_preference_service import (
    NotificationPreferenceService,
    UserPreferenceService,
    get_user_preferences,
    update_user_preferences,
)

router = APIRouter(prefix="/dashboard", tags=["个人仪表盘"])
prefs_router = APIRouter(prefix="/preferences", tags=["用户偏好设置"])


# ==================== 仪表盘 API ====================


@router.get("/")
async def get_dashboard(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取个人健康仪表盘

    返回完整的仪表盘数据，包括:
    - 用户摘要和健康评分
    - 今日概览
    - 今日任务（用药、打卡）
    - 近期健康趋势
    - 目标进度
    - 最近记录
    - 健康警报
    - AI健康洞察
    """
    try:
        data = get_dashboard_data(db, current_user.user_id)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘失败: {str(e)}")


@router.get("/today")
async def get_today_summary(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取今日摘要"""
    try:
        service = DashboardService(db, current_user.user_id)
        summary = service.get_today_summary()
        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取今日摘要失败: {str(e)}")


@router.get("/quick-actions")
async def get_quick_actions(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取快捷操作列表"""
    try:
        service = DashboardService(db, current_user.user_id)
        actions = service.get_quick_actions()
        return {"success": True, "actions": actions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取快捷操作失败: {str(e)}")


@router.get("/weekly-stats")
async def get_weekly_stats(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取本周统计"""
    try:
        service = DashboardService(db, current_user.user_id)
        stats = service.get_weekly_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取周统计失败: {str(e)}")


@router.get("/tasks")
async def get_today_tasks(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取今日待办任务"""
    try:
        service = DashboardService(db, current_user.user_id)
        # 从dashboard数据中提取任务
        dashboard = service.get_dashboard_data()
        return {
            "success": True,
            "tasks": dashboard.get("today_tasks", []),
            "completion_rate": dashboard.get("today_overview", {}).get(
                "completion_status"
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")


@router.get("/health-score")
async def get_health_score(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取健康评分"""
    try:
        service = DashboardService(db, current_user.user_id)
        dashboard = service.get_dashboard_data()
        return {
            "success": True,
            "health_score": dashboard.get("user_summary", {}).get("health_score"),
            "streak_days": dashboard.get("user_summary", {}).get("streak_days"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取健康评分失败: {str(e)}")


# ==================== 偏好设置 API ====================


@prefs_router.get("/")
async def get_preferences(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取用户偏好设置

    返回所有偏好设置（合并默认值和用户自定义设置）
    """
    try:
        prefs = get_user_preferences(db, current_user.user_id)
        return {"success": True, "preferences": prefs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取偏好设置失败: {str(e)}")


@prefs_router.get("/{key}")
async def get_single_preference(
    key: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取单个偏好设置"""
    try:
        service = UserPreferenceService(db, current_user.user_id)
        value = service.get_preference(key)
        return {"success": True, "key": key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取偏好失败: {str(e)}")


@prefs_router.post("/")
async def set_preferences(
    prefs: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    设置多个偏好

    示例请求:
    ```json
    {
        "theme": "dark",
        "language": "zh-CN",
        "data_display_days": 14
    }
    ```
    """
    try:
        results = update_user_preferences(db, current_user.user_id, prefs)
        return {"success": all(results.values()), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置偏好失败: {str(e)}")


@prefs_router.put("/{key}")
async def set_single_preference(
    key: str,
    value: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    设置单个偏好

    示例请求:
    ```json
    {"value": "dark"}
    ```
    """
    try:
        service = UserPreferenceService(db, current_user.user_id)
        success = service.set_preference(key, value.get("value"))
        return {"success": success, "key": key, "value": value.get("value")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置偏好失败: {str(e)}")


@prefs_router.delete("/{key}")
async def reset_preference(
    key: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """重置单个偏好为默认值"""
    try:
        service = UserPreferenceService(db, current_user.user_id)
        success = service.reset_preference(key)
        return {"success": success, "message": f"偏好 {key} 已重置为默认值"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置偏好失败: {str(e)}")


@prefs_router.post("/reset-all")
async def reset_all_preferences(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """重置所有偏好为默认值"""
    try:
        service = UserPreferenceService(db, current_user.user_id)
        success = service.reset_all_preferences()
        return {"success": success, "message": "所有偏好已重置为默认值"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置偏好失败: {str(e)}")


# ==================== 通知设置 API ====================


@prefs_router.get("/notifications")
async def get_notification_settings(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取通知设置"""
    try:
        service = NotificationPreferenceService(db, current_user.user_id)
        settings = service.get_notification_settings()
        return {"success": True, "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取通知设置失败: {str(e)}")


@prefs_router.put("/notifications")
async def update_notification_settings(
    settings: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    更新通知设置

    示例请求:
    ```json
    {
        "enable_email": true,
        "enable_push": true,
        "medication_reminder": true,
        "quiet_hours_start": "22:00"
    }
    ```
    """
    try:
        service = NotificationPreferenceService(db, current_user.user_id)
        success = service.update_notification_settings(settings)
        return {"success": success, "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新通知设置失败: {str(e)}")


# ==================== 快捷偏好 API ====================


@prefs_router.get("/theme")
async def get_theme(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取主题设置"""
    service = UserPreferenceService(db, current_user.user_id)
    return {"success": True, "theme": service.get_theme()}


@prefs_router.put("/theme")
async def set_theme(
    theme: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """设置主题"""
    service = UserPreferenceService(db, current_user.user_id)
    success = service.set_theme(theme.get("theme", "light"))
    return {"success": success, "theme": theme.get("theme")}


@prefs_router.get("/dashboard-cards")
async def get_dashboard_cards(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取仪表板卡片配置"""
    service = UserPreferenceService(db, current_user.user_id)
    return {"success": True, "cards": service.get_dashboard_cards()}


@prefs_router.put("/dashboard-cards")
async def set_dashboard_cards(
    cards: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """设置仪表板卡片配置"""
    service = UserPreferenceService(db, current_user.user_id)
    success = service.set_dashboard_cards(cards.get("cards", []))
    return {"success": success, "cards": cards.get("cards", [])}
