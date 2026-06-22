"""
🌸 若曦V2 - WebSocket连接管理器
实时健康监控与通知推送
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知类型"""

    HEALTH_ALERT = "health_alert"  # 健康警报
    MEDICATION_REMINDER = "medication_reminder"  # 用药提醒
    GOAL_ACHIEVED = "goal_achieved"  # 目标达成
    APPOINTMENT = "appointment"  # 预约提醒
    SYNC_COMPLETE = "sync_complete"  # 同步完成
    SYSTEM = "system"  # 系统通知


class AlertSeverity(str, Enum):
    """警报严重程度"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class WebSocketManager:
    """
    WebSocket连接管理器

    管理用户WebSocket连接，提供实时通知推送功能
    - 用户级连接管理
    - 广播/单播/组播消息
    - 健康数据实时监控
    - 异常自动触发通知
    """

    def __init__(self):
        # 用户连接映射: user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # 连接元数据: websocket -> metadata
        self.connection_metadata: Dict[WebSocket, dict] = {}

        # 回调注册表
        self.on_connect_callbacks: List[Callable] = []
        self.on_disconnect_callbacks: List[Callable] = []
        self.on_message_callbacks: List[Callable] = []

        # 健康监控阈值
        self.health_thresholds = {
            "blood_pressure": {
                "crisis_systolic": 180,
                "crisis_diastolic": 120,
                "high_systolic": 140,
                "high_diastolic": 90,
            },
            "glucose": {
                "severe_hypo": 3.9,  # mmol/L
                "hypo": 3.9,
                "hyper": 11.1,
                "severe_hyper": 16.7,
            },
            "heart_rate": {
                "bradycardia": 50,
                "tachycardia": 120,
                "critical_low": 40,
                "critical_high": 150,
            },
        }

    async def connect(
        self, websocket: WebSocket, user_id: int, client_info: dict = None
    ):
        """
        建立WebSocket连接

        Args:
            websocket: WebSocket对象
            user_id: 用户ID
            client_info: 客户端信息（设备类型、版本等）
        """
        await websocket.accept()

        # 添加到用户连接集合
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

        # 存储连接元数据
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "client_info": client_info or {},
            "last_ping": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"用户 {user_id} WebSocket连接建立，当前连接数: {len(self.active_connections[user_id])}"
        )

        # 触发连接回调
        for callback in self.on_connect_callbacks:
            try:
                await callback(user_id, websocket, client_info)
            except Exception as e:
                logger.error(f"连接回调执行失败: {e}")

        # 发送连接成功消息
        await self.send_to_user(
            user_id,
            {
                "type": "connection_established",
                "data": {
                    "message": "WebSocket连接成功",
                    "timestamp": datetime.utcnow().isoformat(),
                    "connection_id": id(websocket),
                },
            },
        )

    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        断开WebSocket连接

        Args:
            websocket: WebSocket对象
            user_id: 用户ID
        """
        # 从集合中移除
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # 如果用户没有连接了，清理用户条目
            if len(self.active_connections[user_id]) == 0:
                del self.active_connections[user_id]

        # 清理元数据
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(f"用户 {user_id} WebSocket连接断开")

        # 触发断开回调
        for callback in self.on_disconnect_callbacks:
            try:
                callback(user_id, websocket)
            except Exception as e:
                logger.error(f"断开回调执行失败: {e}")

    async def send_to_user(self, user_id: int, message: dict):
        """
        向指定用户发送消息

        Args:
            user_id: 用户ID
            message: 消息内容
        """
        if user_id not in self.active_connections:
            return False

        disconnected = set()

        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"发送消息失败: {e}")
                disconnected.add(websocket)

        # 清理断开的连接
        for websocket in disconnected:
            self.disconnect(websocket, user_id)

        return len(disconnected) < len(self.active_connections.get(user_id, set()))

    async def broadcast(self, message: dict, exclude_user: int = None):
        """
        广播消息给所有连接用户

        Args:
            message: 消息内容
            exclude_user: 排除的用户ID
        """
        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            for websocket in list(connections):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"广播消息失败: {e}")
                    self.disconnect(websocket, user_id)

    async def send_alert(
        self,
        user_id: int,
        alert_type: NotificationType,
        severity: AlertSeverity,
        title: str,
        message: str,
        data: dict = None,
        actions: List[dict] = None,
    ):
        """
        发送警报通知

        Args:
            user_id: 用户ID
            alert_type: 警报类型
            severity: 严重程度
            title: 标题
            message: 消息内容
            data: 附加数据
            actions: 可操作按钮
        """
        notification = {
            "type": "notification",
            "notification_type": alert_type.value,
            "severity": severity.value,
            "title": title,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {},
            "actions": actions or [],
        }

        await self.send_to_user(user_id, notification)
        logger.info(f"发送{severity.value}级别通知给用户 {user_id}: {title}")

    async def check_health_alert(
        self, user_id: int, record_type: str, values: dict
    ) -> Optional[dict]:
        """
        检查健康数据并触发相应警报

        Args:
            user_id: 用户ID
            record_type: 记录类型 (blood_pressure, glucose, heart_rate)
            values: 数值字典

        Returns:
            如果有警报，返回警报详情
        """
        alert = None

        if record_type == "blood_pressure":
            systolic = values.get("systolic", 0)
            diastolic = values.get("diastolic", 0)
            thresholds = self.health_thresholds["blood_pressure"]

            # 血压危机
            if (
                systolic >= thresholds["crisis_systolic"]
                or diastolic >= thresholds["crisis_diastolic"]
            ):
                alert = {
                    "type": NotificationType.HEALTH_ALERT,
                    "severity": AlertSeverity.EMERGENCY,
                    "title": "🚨 血压危机警告",
                    "message": f"您的血压达到危机水平：{systolic}/{diastolic} mmHg，请立即就医！",
                    "data": {
                        "systolic": systolic,
                        "diastolic": diastolic,
                        "category": "crisis",
                        "recommendation": "请立即就医或拨打急救电话",
                    },
                    "actions": [
                        {"label": "查看详情", "action": "view_record"},
                        {"label": "呼叫紧急联系人", "action": "call_emergency"},
                    ],
                }
            # 高血压
            elif (
                systolic >= thresholds["high_systolic"]
                or diastolic >= thresholds["high_diastolic"]
            ):
                alert = {
                    "type": NotificationType.HEALTH_ALERT,
                    "severity": AlertSeverity.WARNING,
                    "title": "⚠️ 血压升高提醒",
                    "message": f"您的血压偏高：{systolic}/{diastolic} mmHg，请注意休息和监测。",
                    "data": {
                        "systolic": systolic,
                        "diastolic": diastolic,
                        "category": "stage1",
                    },
                    "actions": [
                        {"label": "记录详情", "action": "view_record"},
                        {"label": "查看建议", "action": "view_tips"},
                    ],
                }

        elif record_type == "glucose":
            glucose = values.get("value", 0)
            thresholds = self.health_thresholds["glucose"]

            # 严重低血糖
            if glucose < thresholds["severe_hypo"]:
                alert = {
                    "type": NotificationType.HEALTH_ALERT,
                    "severity": AlertSeverity.EMERGENCY,
                    "title": "🚨 低血糖警告",
                    "message": f"您的血糖过低：{glucose} mmol/L，请立即补充糖分！",
                    "data": {
                        "glucose": glucose,
                        "category": "severe_hypo",
                        "recommendation": "请立即摄入15g快速吸收碳水（如糖果、果汁）",
                    },
                    "actions": [
                        {"label": "记录处理", "action": "record_treatment"},
                        {"label": "呼叫帮助", "action": "call_emergency"},
                    ],
                }
            # 高血糖
            elif glucose > thresholds["severe_hyper"]:
                alert = {
                    "type": NotificationType.HEALTH_ALERT,
                    "severity": AlertSeverity.CRITICAL,
                    "title": "⚠️ 高血糖警告",
                    "message": f"您的血糖过高：{glucose} mmol/L，请关注血糖控制。",
                    "data": {"glucose": glucose, "category": "severe_hyper"},
                    "actions": [
                        {"label": "查看详情", "action": "view_record"},
                        {"label": "联系医生", "action": "contact_doctor"},
                    ],
                }

        elif record_type == "heart_rate":
            hr = values.get("bpm", 0)
            activity = values.get("activity", "unknown")
            thresholds = self.health_thresholds["heart_rate"]

            # 静息心率异常
            if activity == "resting":
                if hr < thresholds["critical_low"]:
                    alert = {
                        "type": NotificationType.HEALTH_ALERT,
                        "severity": AlertSeverity.CRITICAL,
                        "title": "🚨 心率过缓警告",
                        "message": f"您的静息心率过低：{hr} bpm，请关注心脏健康。",
                        "data": {"hr": hr, "activity": activity},
                    }
                elif hr > thresholds["tachycardia"]:
                    alert = {
                        "type": NotificationType.HEALTH_ALERT,
                        "severity": AlertSeverity.WARNING,
                        "title": "⚠️ 心率过快提醒",
                        "message": f"您的静息心率偏高：{hr} bpm，请注意休息。",
                        "data": {"hr": hr, "activity": activity},
                    }

        if alert and user_id in self.active_connections:
            await self.send_alert(user_id, **alert)
            return alert

        return None

    async def send_medication_reminder(
        self,
        user_id: int,
        medication_name: str,
        dosage: str,
        reminder_time: str,
        medication_id: int,
    ):
        """
        发送用药提醒

        Args:
            user_id: 用户ID
            medication_name: 药物名称
            dosage: 剂量
            reminder_time: 提醒时间
            medication_id: 药物ID
        """
        await self.send_alert(
            user_id=user_id,
            alert_type=NotificationType.MEDICATION_REMINDER,
            severity=AlertSeverity.INFO,
            title=f"💊 用药提醒：{medication_name}",
            message=f"该服用 {medication_name} {dosage} 了",
            data={
                "medication_id": medication_id,
                "medication_name": medication_name,
                "dosage": dosage,
                "scheduled_time": reminder_time,
            },
            actions=[
                {"label": "✅ 已服药", "action": f"take_medication:{medication_id}"},
                {"label": "⏭️ 跳过", "action": f"skip_medication:{medication_id}"},
                {"label": "⏰ 稍后提醒", "action": f"snooze:{medication_id}"},
            ],
        )

    async def send_goal_achievement(
        self, user_id: int, goal_type: str, achievement: dict
    ):
        """
        发送目标达成祝贺

        Args:
            user_id: 用户ID
            goal_type: 目标类型
            achievement: 成就详情
        """
        goal_names = {
            "weight_loss": "减重目标",
            "blood_pressure": "血压控制目标",
            "glucose": "血糖控制目标",
            "sleep": "睡眠目标",
            "exercise": "运动目标",
            "medication": "用药依从性目标",
        }

        await self.send_alert(
            user_id=user_id,
            alert_type=NotificationType.GOAL_ACHIEVED,
            severity=AlertSeverity.INFO,
            title=f'🎉 {goal_names.get(goal_type, "目标")}达成！',
            message=achievement.get("message", "恭喜你达成了设定的目标！"),
            data=achievement,
            actions=[
                {"label": "查看详情", "action": "view_goal"},
                {"label": "分享", "action": "share_achievement"},
            ],
        )

    def get_user_connection_count(self, user_id: int) -> int:
        """获取用户连接数"""
        return len(self.active_connections.get(user_id, set()))

    def get_all_connection_stats(self) -> dict:
        """获取所有连接统计"""
        return {
            "total_users": len(self.active_connections),
            "total_connections": sum(
                len(conns) for conns in self.active_connections.values()
            ),
            "users_online": list(self.active_connections.keys()),
        }

    def register_callback(self, event: str, callback: Callable):
        """注册事件回调"""
        if event == "connect":
            self.on_connect_callbacks.append(callback)
        elif event == "disconnect":
            self.on_disconnect_callbacks.append(callback)
        elif event == "message":
            self.on_message_callbacks.append(callback)

    async def handle_client_message(
        self, user_id: int, websocket: WebSocket, message: dict
    ):
        """
        处理客户端消息

        Args:
            user_id: 用户ID
            websocket: WebSocket对象
            message: 消息内容
        """
        msg_type = message.get("type")

        if msg_type == "ping":
            await websocket.send_json(
                {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
            )
            # 更新最后ping时间
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket][
                    "last_ping"
                ] = datetime.utcnow().isoformat()

        elif msg_type == "subscribe":
            # 订阅特定频道
            channels = message.get("channels", [])
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["subscribed_channels"] = channels
            await websocket.send_json({"type": "subscribed", "channels": channels})

        elif msg_type == "mark_read":
            # 标记通知已读
            notification_id = message.get("notification_id")
            await websocket.send_json(
                {"type": "marked_read", "notification_id": notification_id}
            )

        # 触发消息回调
        for callback in self.on_message_callbacks:
            try:
                await callback(user_id, websocket, message)
            except Exception as e:
                logger.error(f"消息回调执行失败: {e}")


# 单例实例
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """获取WebSocket管理器单例"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def reset_websocket_manager():
    """重置WebSocket管理器（测试用）"""
    global _websocket_manager
    _websocket_manager = None
