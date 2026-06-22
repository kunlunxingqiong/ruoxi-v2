"""
🌸 若曦V2 - 通知服务
多渠道消息推送系统
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class NotificationChannel(Enum):
    """通知渠道"""

    WEBSOCKET = "websocket"  # WebSocket实时推送
    EMAIL = "email"  # 邮件
    PUSH = "push"  # 推送通知 (FCM/APNs)
    SMS = "sms"  # 短信
    IN_APP = "in_app"  # 应用内通知


class NotificationPriority(Enum):
    """通知优先级"""

    CRITICAL = 1  # 紧急 (健康告警)
    HIGH = 2  # 重要 (预约提醒)
    MEDIUM = 3  # 一般 (每日摘要)
    LOW = 4  # 低优先级 (营销)


class NotificationType(Enum):
    """通知类型"""

    HEALTH_ALERT = "health_alert"  # 健康告警
    MEDICATION_REMINDER = "medication"  # 用药提醒
    APPOINTMENT = "appointment"  # 预约提醒
    EMOTION_CHECK = "emotion"  # 情绪打卡
    SYSTEM = "system"  # 系统通知
    CHAT = "chat"  # 聊天消息


@dataclass
class Notification:
    """通知对象"""

    id: str
    user_id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    content: str
    channels: List[NotificationChannel]
    data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    sent_channels: List[NotificationChannel] = None

    def __post_init__(self):
        if self.sent_channels is None:
            self.sent_channels = []


class NotificationService:
    """
    通知服务

    功能:
    - 多渠道消息推送
    - 通知优先级管理
    - 批量发送
    - 已读追踪
    - 通知历史
    """

    def __init__(self, data_dir: str = "data/notifications"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._handlers: Dict[NotificationChannel, callable] = {
            NotificationChannel.WEBSOCKET: self._send_websocket,
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.PUSH: self._send_push,
            NotificationChannel.SMS: self._send_sms,
            NotificationChannel.IN_APP: self._send_in_app,
        }

        # 通知历史存储
        self._notifications: Dict[str, List[Notification]] = {}

        # 加载历史
        self._load_history()

    def _load_history(self):
        """加载通知历史"""
        history_file = self.data_dir / "history.json"
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 简化加载，实际需要反序列化
                    print(f"🌸 加载 {len(data)} 条通知历史")
            except Exception as e:
                print(f"加载通知历史失败: {e}")

    def _save_history(self):
        """保存通知历史"""
        history_file = self.data_dir / "history.json"
        try:
            data = {}
            for user_id, notifications in self._notifications.items():
                data[user_id] = [
                    {
                        "id": n.id,
                        "type": n.type.value,
                        "title": n.title,
                        "content": n.content,
                        "created_at": n.created_at.isoformat(),
                        "read_at": n.read_at.isoformat() if n.read_at else None,
                    }
                    for n in notifications[-100:]  # 保留最近100条
                ]

            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存通知历史失败: {e}")

    async def create_notification(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        content: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: Optional[List[NotificationChannel]] = None,
        data: Optional[Dict] = None,
        expires_minutes: Optional[int] = None,
    ) -> Notification:
        """
        创建新通知

        Args:
            user_id: 用户ID
            type: 通知类型
            title: 标题
            content: 内容
            priority: 优先级
            channels: 推送渠道，None则使用默认
            data: 附加数据
            expires_minutes: 过期时间（分钟）
        """
        import uuid

        # 默认渠道
        if channels is None:
            channels = [NotificationChannel.IN_APP]
            if priority in [NotificationPriority.CRITICAL, NotificationPriority.HIGH]:
                channels.extend(
                    [NotificationChannel.WEBSOCKET, NotificationChannel.PUSH]
                )

        expires_at = None
        if expires_minutes:
            expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)

        notification = Notification(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            type=type,
            priority=priority,
            title=title,
            content=content,
            channels=channels,
            data=data or {},
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )

        # 保存到历史
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        self._notifications[user_id].append(notification)

        # 限制历史数量
        if len(self._notifications[user_id]) > 1000:
            self._notifications[user_id] = self._notifications[user_id][-1000:]

        return notification

    async def send_notification(
        self, notification: Notification
    ) -> Dict[NotificationChannel, bool]:
        """发送通知到所有渠道"""
        results = {}

        for channel in notification.channels:
            handler = self._handlers.get(channel)
            if handler:
                try:
                    success = await handler(notification)
                    results[channel] = success
                    if success:
                        notification.sent_channels.append(channel)
                except Exception as e:
                    print(f"发送通知失败 {channel.value}: {e}")
                    results[channel] = False
            else:
                results[channel] = False

        # 保存历史
        self._save_history()

        return results

    async def _send_websocket(self, notification: Notification) -> bool:
        """通过WebSocket发送"""
        try:
            from core.websocket.connection_manager import connection_manager

            message = {
                "type": "notification",
                "notification": {
                    "id": notification.id,
                    "type": notification.type.value,
                    "priority": notification.priority.value,
                    "title": notification.title,
                    "content": notification.content,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                },
            }

            sent = await connection_manager.send_to_user(notification.user_id, message)

            return sent > 0
        except Exception as e:
            print(f"WebSocket发送失败: {e}")
            return False

    async def _send_email(self, notification: Notification) -> bool:
        """通过邮件发送"""
        # TODO: 集成邮件服务 (SendGrid/AWS SES/自建SMTP)
        print(f"📧 [邮件] 发送给 {notification.user_id}: {notification.title}")
        return True

    async def _send_push(self, notification: Notification) -> bool:
        """通过推送通知发送 (FCM/APNs)"""
        # TODO: 集成Firebase Cloud Messaging 或 APNs
        print(f"📱 [推送] 发送给 {notification.user_id}: {notification.title}")
        return True

    async def _send_sms(self, notification: Notification) -> bool:
        """通过短信发送"""
        # 仅紧急通知使用
        if notification.priority != NotificationPriority.CRITICAL:
            return False

        # TODO: 集成短信服务 (Twilio/阿里云短信)
        print(f"📲 [短信] 发送给 {notification.user_id}: {notification.title}")
        return True

    async def _send_in_app(self, notification: Notification) -> bool:
        """应用内通知 (已存储，客户端拉取)"""
        # 应用内通知通过存储实现，客户端通过API拉取
        return True

    async def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """标记通知为已读"""
        if user_id not in self._notifications:
            return False

        for notification in self._notifications[user_id]:
            if notification.id == notification_id:
                notification.read_at = datetime.utcnow()
                self._save_history()
                return True

        return False

    async def mark_all_as_read(self, user_id: str) -> int:
        """标记用户所有通知为已读"""
        if user_id not in self._notifications:
            return 0

        count = 0
        now = datetime.utcnow()

        for notification in self._notifications[user_id]:
            if notification.read_at is None:
                notification.read_at = now
                count += 1

        if count > 0:
            self._save_history()

        return count

    def get_user_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> List[Notification]:
        """获取用户通知列表"""
        if user_id not in self._notifications:
            return []

        notifications = self._notifications[user_id]

        # 过滤未读
        if unread_only:
            notifications = [n for n in notifications if n.read_at is None]

        # 按时间倒序
        notifications = sorted(notifications, key=lambda n: n.created_at, reverse=True)

        return notifications[:limit]

    def get_unread_count(self, user_id: str) -> int:
        """获取用户未读通知数"""
        if user_id not in self._notifications:
            return 0

        return sum(1 for n in self._notifications[user_id] if n.read_at is None)

    async def send_bulk_notifications(
        self,
        user_ids: List[str],
        type: NotificationType,
        title: str,
        content: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
    ) -> Dict[str, Dict]:
        """
        批量发送通知

        用于群发系统公告或活动通知
        """
        results = {}

        for user_id in user_ids:
            notification = await self.create_notification(
                user_id=user_id,
                type=type,
                title=title,
                content=content,
                priority=priority,
            )

            sent_results = await self.send_notification(notification)
            results[user_id] = {
                "notification_id": notification.id,
                "channels": {k.value: v for k, v in sent_results.items()},
            }

        return results

    def get_stats(self) -> Dict:
        """获取通知统计"""
        total_users = len(self._notifications)
        total_notifications = sum(len(n) for n in self._notifications.values())
        total_unread = sum(
            sum(1 for n in notifications if n.read_at is None)
            for notifications in self._notifications.values()
        )

        return {
            "total_users": total_users,
            "total_notifications": total_notifications,
            "total_unread": total_unread,
            "read_rate": (
                f"{(total_notifications - total_unread) / total_notifications:.1%}"
                if total_notifications > 0
                else "N/A"
            ),
        }


# 若曦专属通知模板
class RuoxiNotificationTemplates:
    """若曦专属通知模板"""

    @staticmethod
    def medication_reminder(medication_name: str, dosage: str) -> tuple:
        """用药提醒"""
        return (
            f"💊 该吃药啦 - {medication_name}",
            f"到时间了，记得服用 {medication_name} {dosage}。曦曦帮你记着呢~",
            NotificationPriority.HIGH,
        )

    @staticmethod
    def health_alert(metric: str, value: str, status: str) -> tuple:
        """健康告警"""
        return (
            f"⚠️ 健康提醒 - {metric}异常",
            f"你的{metric}显示{value}，状态为{status}。需要关注一下哦，曦曦有点担心...",
            NotificationPriority.CRITICAL,
        )

    @staticmethod
    def emotion_checkin() -> tuple:
        """情绪打卡提醒"""
        return (
            "🌸 今天过得怎么样？",
            "曦曦想听听你今天的心情，来打个卡吧~",
            NotificationPriority.MEDIUM,
        )

    @staticmethod
    def daily_summary() -> tuple:
        """每日健康摘要"""
        return (
            "📊 今日健康摘要",
            "来看看今天的健康数据汇总吧，曦曦为你整理好了~",
            NotificationPriority.LOW,
        )


# 全局通知服务实例
notification_service = NotificationService()
