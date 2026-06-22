"""
🌸 若曦V2 - 通知API
通知管理端点
"""

from datetime import datetime
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.notification.notification_service import (
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    RuoxiNotificationTemplates,
    notification_service,
)

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("/")
async def get_notifications(
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    """获取用户通知列表"""
    notifications = notification_service.get_user_notifications(
        user_id=current_user.user_id, unread_only=unread_only, limit=limit
    )

    return {
        "success": True,
        "notifications": [
            {
                "id": n.id,
                "type": n.type.value,
                "priority": n.priority.value,
                "title": n.title,
                "content": n.content,
                "data": n.data,
                "channels": [c.value for c in n.channels],
                "created_at": n.created_at.isoformat(),
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "is_read": n.read_at is not None,
            }
            for n in notifications
        ],
        "total": len(notifications),
        "unread_count": notification_service.get_unread_count(current_user.user_id),
    }


@router.get("/unread-count")
async def get_unread_count(current_user=Depends(get_current_user)):
    """获取未读通知数量"""
    count = notification_service.get_unread_count(current_user.user_id)

    return {"success": True, "unread_count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str, current_user=Depends(get_current_user)):
    """标记通知为已读"""
    success = await notification_service.mark_as_read(
        user_id=current_user.user_id, notification_id=notification_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")

    return {"success": True, "message": "已标记为已读"}


@router.post("/read-all")
async def mark_all_as_read(current_user=Depends(get_current_user)):
    """标记所有通知为已读"""
    count = await notification_service.mark_all_as_read(current_user.user_id)

    return {"success": True, "marked_count": count}


@router.post("/create")
async def create_notification(
    type: str,
    title: str,
    content: str,
    priority: str = "medium",
    channels: Optional[List[str]] = None,
    target_user_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """
    创建通知 (管理员功能)

    可用于发送系统公告或测试通知
    """
    # 解析枚举
    try:
        notif_type = NotificationType(type)
        notif_priority = NotificationPriority[priority.upper()]
        notif_channels = [NotificationChannel(c) for c in (channels or ["in_app"])]
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=f"无效参数: {e}")

    # 目标用户
    user_id = target_user_id or current_user.user_id

    # 创建通知
    notification = await notification_service.create_notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        content=content,
        priority=notif_priority,
        channels=notif_channels,
    )

    # 发送通知
    results = await notification_service.send_notification(notification)

    return {
        "success": True,
        "notification_id": notification.id,
        "sent_results": {k.value: v for k, v in results.items()},
    }


@router.post("/test/medication")
async def test_medication_notification(current_user=Depends(get_current_user)):
    """测试用药提醒通知"""
    title, content, priority = RuoxiNotificationTemplates.medication_reminder(
        "维生素C", "1片"
    )

    notification = await notification_service.create_notification(
        user_id=current_user.user_id,
        type=NotificationType.MEDICATION_REMINDER,
        title=title,
        content=content,
        priority=priority,
        channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP],
    )

    results = await notification_service.send_notification(notification)

    return {
        "success": True,
        "message": "用药提醒测试已发送",
        "notification_id": notification.id,
    }


@router.post("/test/emotion")
async def test_emotion_notification(current_user=Depends(get_current_user)):
    """测试情绪打卡通知"""
    title, content, priority = RuoxiNotificationTemplates.emotion_checkin()

    notification = await notification_service.create_notification(
        user_id=current_user.user_id,
        type=NotificationType.EMOTION_CHECK,
        title=title,
        content=content,
        priority=priority,
        channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP],
    )

    results = await notification_service.send_notification(notification)

    return {
        "success": True,
        "message": "情绪打卡提醒已发送",
        "notification_id": notification.id,
    }


@router.post("/test/health-alert")
async def test_health_alert(current_user=Depends(get_current_user)):
    """测试健康告警通知"""
    title, content, priority = RuoxiNotificationTemplates.health_alert(
        "血压", "150/95", "偏高"
    )

    notification = await notification_service.create_notification(
        user_id=current_user.user_id,
        type=NotificationType.HEALTH_ALERT,
        title=title,
        content=content,
        priority=priority,
        channels=[
            NotificationChannel.WEBSOCKET,
            NotificationChannel.PUSH,
            NotificationChannel.IN_APP,
        ],
    )

    results = await notification_service.send_notification(notification)

    return {
        "success": True,
        "message": "健康告警已发送",
        "notification_id": notification.id,
    }


@router.get("/stats")
async def get_notification_stats(current_user=Depends(get_current_user)):
    """获取通知统计"""
    stats = notification_service.get_stats()
    user_unread = notification_service.get_unread_count(current_user.user_id)

    return {"success": True, "global_stats": stats, "user_unread": user_unread}


@router.get("/templates")
async def get_notification_templates(current_user=Depends(get_current_user)):
    """获取若曦通知模板"""
    return {
        "success": True,
        "templates": {
            "medication": {"name": "用药提醒", "description": "定时提醒用户服药"},
            "emotion": {"name": "情绪打卡", "description": "提醒用户记录心情"},
            "health_alert": {"name": "健康告警", "description": "异常指标提醒"},
            "daily_summary": {"name": "每日摘要", "description": "每日健康数据汇总"},
        },
    }
