"""
🌸 若曦V2 - 提醒定时调度器
定时检查并发送用药、健康检查等提醒
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from models.database import get_db, User as UserModel, Notification
from core.services.medication_service import MedicationService


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReminderScheduler:
    """
    提醒调度器
    
    负责定时检查各类提醒并触发通知
    """
    
    def __init__(self):
        self.check_interval_seconds = 60  # 每分钟检查一次
        self.running = False
        self.callbacks: Dict[str, List[Callable]] = {
            "medication": [],
            "health_check": [],
            "goal": []
        }
    
    def register_callback(self, reminder_type: str, callback: Callable):
        """注册提醒回调函数"""
        if reminder_type not in self.callbacks:
            self.callbacks[reminder_type] = []
        self.callbacks[reminder_type].append(callback)
        logger.info(f"已注册 {reminder_type} 类型的提醒回调")
    
    async def start(self):
        """启动调度器"""
        self.running = True
        logger.info("🌸 提醒调度器已启动")
        
        while self.running:
            try:
                await self._check_all_reminders()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"提醒检查出错: {e}")
                await asyncio.sleep(self.check_interval_seconds)
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("提醒调度器已停止")
    
    async def _check_all_reminders(self):
        """检查所有类型的提醒"""
        # 获取数据库会话
        db = next(get_db())
        try:
            # 1. 检查用药提醒
            await self._check_medication_reminders(db)
            
            # 2. 检查健康检查提醒 (如定期复查)
            # await self._check_health_check_reminders(db)
            
            # 3. 检查目标提醒
            # await self._check_goal_reminders(db)
            
        finally:
            db.close()
    
    async def _check_medication_reminders(self, db: Session):
        """检查用药提醒"""
        try:
            # 获取所有活跃用户的ID
            active_users = db.query(UserModel.id).filter(
                UserModel.is_active == True
            ).all()
            
            for (user_id,) in active_users:
                service = MedicationService(db)
                due_medications = service.get_due_medications(
                    user_id=user_id,
                    check_time=datetime.now()
                )
                
                for item in due_medications:
                    med = item["medication"]
                    
                    # 创建通知记录
                    notification = self._create_notification(
                        db=db,
                        user_id=user_id,
                        title=f"💊 用药提醒: {med.name}",
                        body=f"该服用 {med.dosage} 了，{med.purpose or ''}",
                        notification_type="medication",
                        priority="high",
                        action_type="open_page",
                        action_data={"page": "/medications", "medication_id": med.id}
                    )
                    
                    # 触发回调
                    await self._trigger_callbacks("medication", {
                        "user_id": user_id,
                        "medication": {
                            "id": med.id,
                            "name": med.name,
                            "dosage": med.dosage,
                            "purpose": med.purpose,
                            "reminder_time": med.reminder_time
                        },
                        "is_overdue": item["is_overdue"],
                        "minutes_overdue": item["minutes_overdue"],
                        "notification_id": notification.id if notification else None
                    })
                    
                    logger.info(f"用药提醒已发送: 用户{user_id} - {med.name}")
        
        except Exception as e:
            logger.error(f"检查用药提醒时出错: {e}")
    
    def _create_notification(
        self,
        db: Session,
        user_id: int,
        title: str,
        body: str,
        notification_type: str,
        priority: str = "normal",
        action_type: Optional[str] = None,
        action_data: Optional[Dict] = None
    ) -> Optional[Notification]:
        """创建通知记录"""
        try:
            import json
            
            notification = Notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                priority=priority,
                is_read=False,
                action_type=action_type,
                action_data=json.dumps(action_data) if action_data else None
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            return notification
        except Exception as e:
            logger.error(f"创建通知记录失败: {e}")
            db.rollback()
            return None
    
    async def _trigger_callbacks(self, reminder_type: str, data: Dict[str, Any]):
        """触发该类型的所有回调"""
        callbacks = self.callbacks.get(reminder_type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")


# 单例模式
_reminder_scheduler: Optional[ReminderScheduler] = None


def get_reminder_scheduler() -> ReminderScheduler:
    """获取提醒调度器单例"""
    global _reminder_scheduler
    if _reminder_scheduler is None:
        _reminder_scheduler = ReminderScheduler()
    return _reminder_scheduler


# ==================== WebSocket实时通知回调 ====================

async def websocket_medication_reminder_callback(data: Dict[str, Any]):
    """
    WebSocket用药提醒回调
    
    通过WebSocket向在线用户实时推送用药提醒
    """
    try:
        # 延迟导入避免循环依赖
        from core.services.websocket_manager import get_websocket_manager
        
        manager = get_websocket_manager()
        user_id = data.get("user_id")
        med = data.get("medication", {})
        
        if not user_id or not med:
            return
        
        # 检查用户是否在线
        if manager.get_user_connection_count(user_id) > 0:
            await manager.send_medication_reminder(
                user_id=user_id,
                medication_name=med.get("name", "未知药物"),
                dosage=med.get("dosage", ""),
                reminder_time=med.get("reminder_time", ""),
                medication_id=med.get("id", 0)
            )
            logger.info(f"WebSocket用药提醒已发送给用户 {user_id}")
    except Exception as e:
        logger.error(f"WebSocket用药提醒发送失败: {e}")


# ==================== 示例回调实现 ====================

async def example_push_notification_callback(data: Dict[str, Any]):
    """
    示例：推送通知回调
    
    实际项目中可以接入：
    - 推送通知服务 (FCM, APNs)
    - 短信服务
    - 邮件服务
    - WebSocket实时通知
    """
    user_id = data.get("user_id")
    medication = data.get("medication", {})
    
    logger.info(f"📱 推送通知: 用户{user_id} - 服用 {medication.get('name')}")
    
    # 这里可以调用实际的推送服务
    # 例如：
    # await fcm_service.send_notification(
    #     user_id=user_id,
    #     title=f"用药提醒: {medication['name']}",
    #     body=f"该服用 {medication['dosage']} 了"
    # )


def example_log_callback(data: Dict[str, Any]):
    """示例：日志记录回调"""
    logger.info(f"📝 记录提醒日志: {data}")


# 调度器启动函数（用于在应用启动时调用）
async def start_reminder_scheduler():
    """启动提醒调度器"""
    scheduler = get_reminder_scheduler()
    
    # 注册回调
    scheduler.register_callback("medication", example_push_notification_callback)
    scheduler.register_callback("medication", example_log_callback)
    
    # 启动调度循环
    await scheduler.start()


def stop_reminder_scheduler():
    """停止提醒调度器"""
    scheduler = get_reminder_scheduler()
    scheduler.stop()
