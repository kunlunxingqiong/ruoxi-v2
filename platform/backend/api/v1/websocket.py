"""
🌸 若曦V2 - WebSocket实时通信API
提供实时健康监控和通知推送
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json
import logging

from core.services.websocket_manager import (
    get_websocket_manager, 
    WebSocketManager,
    NotificationType,
    AlertSeverity
)
from platform.backend.core_auth.jwt_auth import get_current_user, get_current_user_ws


router = APIRouter(tags=["WebSocket实时通信"])
logger = logging.getLogger(__name__)


# ==================== WebSocket 端点 ====================

@router.websocket("/ws/health")
async def health_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
    device_type: Optional[str] = Query(None, description="设备类型 (web/ios/android)"),
    app_version: Optional[str] = Query(None, description="应用版本")
):
    """
    健康数据实时WebSocket连接
    
    建立实时连接后，服务端将推送：
    - 健康数据异常警报（血压危机、低血糖等）
    - 用药提醒通知
    - 目标达成祝贺
    - 同步完成通知
    
    客户端消息类型：
    - ping: 心跳检测
    - subscribe: 订阅频道
    - mark_read: 标记已读
    
    Args:
        token: JWT认证令牌（必填）
        device_type: 设备类型
        app_version: 应用版本
    """
    # 验证token获取用户信息
    try:
        current_user = await get_current_user_ws(token)
        user_id = current_user.user_id
    except Exception as e:
        logger.warning(f"WebSocket认证失败: {e}")
        await websocket.close(code=4001, reason="认证失败")
        return
    
    # 获取管理器
    manager = get_websocket_manager()
    
    # 客户端信息
    client_info = {
        'device_type': device_type or 'unknown',
        'app_version': app_version or 'unknown',
        'user_agent': 'websocket'
    }
    
    # 建立连接
    await manager.connect(websocket, user_id, client_info)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await manager.handle_client_message(user_id, websocket, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/notifications")
async def notification_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT认证令牌"),
    device_type: Optional[str] = Query(None, description="设备类型")
):
    """
    通知专用WebSocket连接
    
    专门用于接收各类通知（不接收健康数据流）
    适合移动端后台连接
    
    Args:
        token: JWT认证令牌
        device_type: 设备类型
    """
    try:
        current_user = await get_current_user_ws(token)
        user_id = current_user.user_id
    except Exception as e:
        await websocket.close(code=4001, reason="认证失败")
        return
    
    manager = get_websocket_manager()
    client_info = {
        'device_type': device_type or 'unknown',
        'channel': 'notifications_only'
    }
    
    await manager.connect(websocket, user_id, client_info)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await manager.handle_client_message(user_id, websocket, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"通知WebSocket错误: {e}")
        manager.disconnect(websocket, user_id)


# ==================== HTTP API 端点 ====================

@router.get("/websocket/status")
async def get_websocket_status():
    """
    获取WebSocket连接状态统计
    
    返回当前在线用户数和连接统计
    """
    manager = get_websocket_manager()
    stats = manager.get_all_connection_stats()
    
    return {
        "success": True,
        "status": "running",
        "stats": stats,
        "health_thresholds": manager.health_thresholds
    }


@router.post("/websocket/test/alert/{user_id}")
async def send_test_alert(
    user_id: int,
    alert_type: str = "health_alert",
    severity: str = "warning",
    title: str = "测试通知",
    message: str = "这是一条测试通知消息"
):
    """
    发送测试警报（开发/测试用）
    
    向指定用户发送测试通知
    
    Args:
        user_id: 目标用户ID
        alert_type: 警报类型
        severity: 严重程度
        title: 标题
        message: 消息内容
    """
    manager = get_websocket_manager()
    
    await manager.send_alert(
        user_id=user_id,
        alert_type=NotificationType(alert_type),
        severity=AlertSeverity(severity),
        title=title,
        message=message,
        data={"test": True, "timestamp": str(__import__('datetime').datetime.utcnow())},
        actions=[
            {"label": "查看详情", "action": "view_details"},
            {"label": "忽略", "action": "dismiss"}
        ]
    )
    
    return {
        "success": True,
        "message": f"测试通知已发送给用户 {user_id}",
        "user_connections": manager.get_user_connection_count(user_id)
    }


@router.post("/websocket/broadcast")
async def broadcast_message(
    message: str,
    exclude_user: Optional[int] = None
):
    """
    广播消息（管理员用）
    
    向所有在线用户广播系统消息
    
    Args:
        message: 消息内容
        exclude_user: 排除的用户ID
    """
    manager = get_websocket_manager()
    
    await manager.broadcast({
        "type": "system_broadcast",
        "title": "系统公告",
        "message": message,
        "timestamp": str(__import__('datetime').datetime.utcnow().isoformat())
    }, exclude_user=exclude_user)
    
    stats = manager.get_all_connection_stats()
    
    return {
        "success": True,
        "message": f"广播已发送给 {stats['total_users']} 个用户",
        "stats": stats
    }


@router.get("/websocket/thresholds")
async def get_health_thresholds():
    """
    获取健康监控阈值配置
    
    返回触发实时警报的阈值设置
    """
    manager = get_websocket_manager()
    
    return {
        "success": True,
        "thresholds": manager.health_thresholds,
        "descriptions": {
            "blood_pressure": {
                "crisis_systolic": "收缩压危机阈值 (≥180 触发紧急警报)",
                "crisis_diastolic": "舒张压危机阈值 (≥120 触发紧急警报)",
                "high_systolic": "收缩压高阈值 (≥140)",
                "high_diastolic": "舒张压高阈值 (≥90)"
            },
            "glucose": {
                "severe_hypo": "严重低血糖阈值 (<3.9 mmol/L)",
                "hypo": "低血糖阈值 (<3.9 mmol/L)",
                "hyper": "高血糖阈值 (>11.1 mmol/L)",
                "severe_hyper": "严重高血糖阈值 (>16.7 mmol/L)"
            },
            "heart_rate": {
                "bradycardia": "心动过缓阈值 (<50 bpm)",
                "tachycardia": "心动过速阈值 (>120 bpm)",
                "critical_low": "严重心动过缓 (<40 bpm)",
                "critical_high": "严重心动过速 (>150 bpm)"
            }
        }
    }


@router.put("/websocket/thresholds/{metric}")
async def update_health_threshold(
    metric: str,
    thresholds: dict
):
    """
    更新健康监控阈值（高级用户/管理员用）
    
    自定义警报触发阈值
    
    Args:
        metric: 指标类型 (blood_pressure/glucose/heart_rate)
        thresholds: 新的阈值配置
    """
    manager = get_websocket_manager()
    
    if metric not in manager.health_thresholds:
        return {
            "success": False,
            "error": f"不支持的指标类型: {metric}"
        }
    
    # 更新阈值
    manager.health_thresholds[metric].update(thresholds)
    
    return {
        "success": True,
        "message": f"{metric} 阈值已更新",
        "updated_thresholds": manager.health_thresholds[metric]
    }


# ==================== 前端集成辅助 ====================

@router.get("/websocket/client-config")
async def get_client_websocket_config():
    """
    获取WebSocket客户端配置
    
    返回前端连接所需的配置信息
    """
    return {
        "success": True,
        "config": {
            "endpoints": {
                "health": "/ws/health",
                "notifications": "/ws/notifications"
            },
            "reconnect": {
                "enabled": True,
                "max_attempts": 5,
                "initial_delay_ms": 1000,
                "max_delay_ms": 30000,
                "backoff_multiplier": 2
            },
            "heartbeat": {
                "enabled": True,
                "interval_ms": 30000,
                "timeout_ms": 10000
            },
            "message_types": {
                "client_to_server": ["ping", "subscribe", "mark_read", "ack"],
                "server_to_client": [
                    "connection_established",
                    "notification",
                    "pong",
                    "subscribed",
                    "marked_read",
                    "error",
                    "system_broadcast"
                ]
            },
            "notification_types": [t.value for t in NotificationType],
            "severity_levels": [s.value for s in AlertSeverity]
        }
    }


# ==================== 健康数据实时监控集成 ====================

async def monitor_health_record(
    user_id: int,
    record_type: str,
    values: dict
):
    """
    监控健康记录并触发警报
    
    在健康记录创建/更新时调用，实时检查异常并推送通知
    
    Args:
        user_id: 用户ID
        record_type: 记录类型
        values: 记录数值
    """
    manager = get_websocket_manager()
    
    # 检查是否有连接
    if manager.get_user_connection_count(user_id) == 0:
        # 用户不在线，可记录待推送或发送推送通知
        logger.info(f"用户 {user_id} 不在线，警报将通过推送服务发送")
        return None
    
    # 检查并发送警报
    alert = await manager.check_health_alert(user_id, record_type, values)
    
    return alert


async def send_medication_reminder_ws(
    user_id: int,
    medication_name: str,
    dosage: str,
    reminder_time: str,
    medication_id: int
):
    """
    通过WebSocket发送用药提醒
    
    Args:
        user_id: 用户ID
        medication_name: 药物名称
        dosage: 剂量
        reminder_time: 提醒时间
        medication_id: 药物ID
    """
    manager = get_websocket_manager()
    
    if manager.get_user_connection_count(user_id) > 0:
        await manager.send_medication_reminder(
            user_id, medication_name, dosage, reminder_time, medication_id
        )
        return True
    
    return False
