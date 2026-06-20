"""
🌸 若曦V2 - 用户偏好设置服务
管理用户个性化设置和偏好
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import logging

from sqlalchemy.orm import Session
from models.database import UserPreference, NotificationSetting, User

logger = logging.getLogger(__name__)


@dataclass
class PreferenceDefaults:
    """默认偏好设置"""
    # 界面主题
    THEME = "light"
    
    # 语言
    LANGUAGE = "zh-CN"
    
    # 温度单位
    TEMPERATURE_UNIT = "celsius"
    
    # 数据展示
    DATA_DISPLAY_DAYS = 7
    CHART_TYPE = "line"
    
    # 通知偏好
    NOTIFICATION_EMAIL = True
    NOTIFICATION_PUSH = True
    NOTIFICATION_SMS = False
    
    # 健康提醒
    DAILY_SUMMARY_TIME = "08:00"
    WEEKLY_REPORT_DAY = "sunday"
    
    # 隐私设置
    SHARE_ANONYMOUS_DATA = False
    ALLOW_AI_ANALYSIS = True
    
    # 仪表板卡片
    DASHBOARD_CARDS = [
        "health_summary",
        "quick_actions", 
        "today_medications",
        "recent_records",
        "goal_progress",
        "ai_insights"
    ]


class UserPreferenceService:
    """
    用户偏好设置服务
    
    管理用户的个性化设置，包括:
    - 界面主题和语言
    - 通知偏好
    - 数据展示偏好
    - 隐私设置
    - 仪表板布局
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self._preferences: Optional[Dict[str, Any]] = None
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """获取所有偏好设置（合并默认值和用户设置）"""
        # 获取用户自定义设置
        user_prefs = self.db.query(UserPreference).filter(
            UserPreference.user_id == self.user_id
        ).all()
        
        # 转换为字典
        prefs_dict = {}
        for pref in user_prefs:
            prefs_dict[pref.key] = self._parse_value(pref.value, pref.type)
        
        # 合并默认值
        defaults = self._get_defaults()
        for key, value in defaults.items():
            if key not in prefs_dict:
                prefs_dict[key] = value
        
        return prefs_dict
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取单个偏好设置"""
        # 先查用户设置
        pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == self.user_id,
            UserPreference.key == key
        ).first()
        
        if pref:
            return self._parse_value(pref.value, pref.type)
        
        # 返回默认值
        defaults = self._get_defaults()
        return defaults.get(key, default)
    
    def set_preference(self, key: str, value: Any) -> bool:
        """设置单个偏好"""
        try:
            pref = self.db.query(UserPreference).filter(
                UserPreference.user_id == self.user_id,
                UserPreference.key == key
            ).first()
            
            value_type = self._detect_type(value)
            value_str = self._serialize_value(value)
            
            if pref:
                # 更新
                pref.value = value_str
                pref.type = value_type
                pref.updated_at = datetime.utcnow()
            else:
                # 新建
                pref = UserPreference(
                    user_id=self.user_id,
                    key=key,
                    value=value_str,
                    type=value_type
                )
                self.db.add(pref)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"设置偏好失败: {e}")
            return False
    
    def set_multiple_preferences(self, prefs: Dict[str, Any]) -> Dict[str, bool]:
        """批量设置偏好"""
        results = {}
        for key, value in prefs.items():
            results[key] = self.set_preference(key, value)
        return results
    
    def reset_preference(self, key: str) -> bool:
        """重置单个偏好为默认值"""
        try:
            pref = self.db.query(UserPreference).filter(
                UserPreference.user_id == self.user_id,
                UserPreference.key == key
            ).first()
            
            if pref:
                self.db.delete(pref)
                self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"重置偏好失败: {e}")
            return False
    
    def reset_all_preferences(self) -> bool:
        """重置所有偏好为默认值"""
        try:
            self.db.query(UserPreference).filter(
                UserPreference.user_id == self.user_id
            ).delete()
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"重置所有偏好失败: {e}")
            return False
    
    # ==================== 快捷方法 ====================
    
    def get_theme(self) -> str:
        """获取主题设置"""
        return self.get_preference("theme", PreferenceDefaults.THEME)
    
    def set_theme(self, theme: str) -> bool:
        """设置主题"""
        return self.set_preference("theme", theme)
    
    def get_language(self) -> str:
        """获取语言设置"""
        return self.get_preference("language", PreferenceDefaults.LANGUAGE)
    
    def get_dashboard_cards(self) -> List[str]:
        """获取仪表板卡片配置"""
        return self.get_preference("dashboard_cards", PreferenceDefaults.DASHBOARD_CARDS)
    
    def set_dashboard_cards(self, cards: List[str]) -> bool:
        """设置仪表板卡片配置"""
        return self.set_preference("dashboard_cards", cards)
    
    def get_notification_settings(self) -> Dict[str, bool]:
        """获取通知设置"""
        return {
            "email": self.get_preference("notification_email", PreferenceDefaults.NOTIFICATION_EMAIL),
            "push": self.get_preference("notification_push", PreferenceDefaults.NOTIFICATION_PUSH),
            "sms": self.get_preference("notification_sms", PreferenceDefaults.NOTIFICATION_SMS),
        }
    
    def get_data_display_days(self) -> int:
        """获取数据显示天数"""
        return self.get_preference("data_display_days", PreferenceDefaults.DATA_DISPLAY_DAYS)
    
    def get_daily_summary_time(self) -> str:
        """获取每日摘要推送时间"""
        return self.get_preference("daily_summary_time", PreferenceDefaults.DAILY_SUMMARY_TIME)
    
    def get_privacy_settings(self) -> Dict[str, bool]:
        """获取隐私设置"""
        return {
            "share_anonymous_data": self.get_preference("share_anonymous_data", PreferenceDefaults.SHARE_ANONYMOUS_DATA),
            "allow_ai_analysis": self.get_preference("allow_ai_analysis", PreferenceDefaults.ALLOW_AI_ANALYSIS),
        }
    
    # ==================== 辅助方法 ====================
    
    def _get_defaults(self) -> Dict[str, Any]:
        """获取所有默认值"""
        return {
            "theme": PreferenceDefaults.THEME,
            "language": PreferenceDefaults.LANGUAGE,
            "temperature_unit": PreferenceDefaults.TEMPERATURE_UNIT,
            "data_display_days": PreferenceDefaults.DATA_DISPLAY_DAYS,
            "chart_type": PreferenceDefaults.CHART_TYPE,
            "notification_email": PreferenceDefaults.NOTIFICATION_EMAIL,
            "notification_push": PreferenceDefaults.NOTIFICATION_PUSH,
            "notification_sms": PreferenceDefaults.NOTIFICATION_SMS,
            "daily_summary_time": PreferenceDefaults.DAILY_SUMMARY_TIME,
            "weekly_report_day": PreferenceDefaults.WEEKLY_REPORT_DAY,
            "share_anonymous_data": PreferenceDefaults.SHARE_ANONYMOUS_DATA,
            "allow_ai_analysis": PreferenceDefaults.ALLOW_AI_ANALYSIS,
            "dashboard_cards": PreferenceDefaults.DASHBOARD_CARDS,
        }
    
    def _parse_value(self, value: str, type: str) -> Any:
        """解析存储的值"""
        if type == "string":
            return value
        elif type == "integer":
            return int(value)
        elif type == "float":
            return float(value)
        elif type == "boolean":
            return value.lower() == "true"
        elif type == "json":
            return json.loads(value)
        return value
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值存储"""
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    
    def _detect_type(self, value: Any) -> str:
        """检测值类型"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (list, dict)):
            return "json"
        return "string"


class NotificationPreferenceService:
    """通知偏好设置服务"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """获取通知设置"""
        settings = self.db.query(NotificationSetting).filter(
            NotificationSetting.user_id == self.user_id
        ).first()
        
        if not settings:
            # 创建默认设置
            settings = NotificationSetting(
                user_id=self.user_id,
                enable_email=True,
                enable_push=True,
                enable_sms=False,
                medication_reminder=True,
                health_alert=True,
                daily_summary=True,
                weekly_report=True,
                quiet_hours_start="22:00",
                quiet_hours_end="08:00"
            )
            self.db.add(settings)
            self.db.commit()
        
        return {
            "enable_email": settings.enable_email,
            "enable_push": settings.enable_push,
            "enable_sms": settings.enable_sms,
            "medication_reminder": settings.medication_reminder,
            "health_alert": settings.health_alert,
            "daily_summary": settings.daily_summary,
            "weekly_report": settings.weekly_report,
            "quiet_hours_start": settings.quiet_hours_start,
            "quiet_hours_end": settings.quiet_hours_end,
        }
    
    def update_notification_settings(self, settings: Dict[str, Any]) -> bool:
        """更新通知设置"""
        try:
            notif_setting = self.db.query(NotificationSetting).filter(
                NotificationSetting.user_id == self.user_id
            ).first()
            
            if not notif_setting:
                notif_setting = NotificationSetting(user_id=self.user_id)
                self.db.add(notif_setting)
            
            # 更新字段
            for key, value in settings.items():
                if hasattr(notif_setting, key):
                    setattr(notif_setting, key, value)
            
            notif_setting.updated_at = datetime.utcnow()
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新通知设置失败: {e}")
            return False


# 便捷函数
def get_user_preferences(db: Session, user_id: int) -> Dict[str, Any]:
    """获取用户偏好便捷函数"""
    service = UserPreferenceService(db, user_id)
    return service.get_all_preferences()


def update_user_preferences(db: Session, user_id: int, 
                            prefs: Dict[str, Any]) -> Dict[str, bool]:
    """更新用户偏好便捷函数"""
    service = UserPreferenceService(db, user_id)
    return service.set_multiple_preferences(prefs)
