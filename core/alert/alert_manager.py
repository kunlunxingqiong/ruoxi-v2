"""
🌸 若曦V2 - 告警管理器
智能监控和告警系统
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta
import asyncio
import json


class AlertSeverity(Enum):
    """告警级别"""
    CRITICAL = "critical"  # 严重 - 立即通知
    HIGH = "high"          # 高 - 5分钟内通知
    MEDIUM = "medium"      # 中 - 15分钟内通知
    LOW = "low"            # 低 - 每小时汇总
    INFO = "info"          # 信息 - 仅记录


class AlertChannel(Enum):
    """通知渠道"""
    CONSOLE = auto()
    EMAIL = auto()
    WEBHOOK = auto()
    SMS = auto()
    WECHAT = auto()
    DINGTALK = auto()


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    description: str
    condition: str  # Python表达式
    severity: AlertSeverity
    channels: List[AlertChannel]
    cooldown_minutes: int = 30  # 冷却时间
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class AlertEvent:
    """告警事件"""
    id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class HealthAlertContext:
    """健康告警上下文"""
    user_id: str
    metric_type: str
    current_value: float
    threshold: float
    trend: str  # "rising", "falling", "stable"
    duration_hours: int


class AlertManager:
    """
    告警管理器
    
    功能:
    - 规则引擎
    - 多渠道通知
    - 智能降噪
    - 告警升级
    """
    
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._events: List[AlertEvent] = []
        self._handlers: Dict[AlertChannel, List[Callable]] = {
            channel: [] for channel in AlertChannel
        }
        self._health_context: Dict[str, Any] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
    
    def add_rule(self, rule: AlertRule) -> str:
        """添加告警规则"""
        self._rules[rule.name] = rule
        return rule.name
    
    def remove_rule(self, name: str) -> bool:
        """移除告警规则"""
        if name in self._rules:
            del self._rules[name]
            return True
        return False
    
    def register_handler(
        self, 
        channel: AlertChannel, 
        handler: Callable[[AlertEvent], Any]
    ):
        """注册通知处理器"""
        self._handlers[channel].append(handler)
    
    async def check_health_alerts(self, user_id: str, health_data: Dict):
        """检查健康告警"""
        # 血压告警
        if "blood_pressure" in health_data:
            bp = health_data["blood_pressure"]
            systolic = bp.get("systolic", 0)
            diastolic = bp.get("diastolic", 0)
            
            # 严重高血压
            if systolic >= 180 or diastolic >= 110:
                await self._trigger_alert(
                    user_id=user_id,
                    rule_name="critical_hypertension",
                    severity=AlertSeverity.CRITICAL,
                    message=f"⚠️ 严重高血压警报！{systolic}/{diastolic} mmHg - 建议立即就医",
                    data={"systolic": systolic, "diastolic": diastolic}
                )
            # 高血压
            elif systolic >= 140 or diastolic >= 90:
                await self._trigger_alert(
                    user_id=user_id,
                    rule_name="high_blood_pressure",
                    severity=AlertSeverity.HIGH,
                    message=f"📊 血压偏高: {systolic}/{diastolic} mmHg",
                    data={"systolic": systolic, "diastolic": diastolic}
                )
        
        # 血糖告警
        if "blood_glucose" in health_data:
            glucose = health_data["blood_glucose"]
            
            if glucose >= 11.1:  # 糖尿病诊断标准
                await self._trigger_alert(
                    user_id=user_id,
                    rule_name="high_blood_glucose",
                    severity=AlertSeverity.HIGH,
                    message=f"🍬 血糖偏高: {glucose} mmol/L",
                    data={"glucose": glucose}
                )
        
        # 情绪危机告警
        if "emotion" in health_data:
            emotion = health_data["emotion"]
            if emotion in ["depressed", "suicidal_ideation"]:
                await self._trigger_alert(
                    user_id=user_id,
                    rule_name="emotional_crisis",
                    severity=AlertSeverity.CRITICAL,
                    message="💜 检测到情绪危机信号 - 若曦建议寻求专业心理援助",
                    data={"emotion": emotion},
                    channels=[AlertChannel.CONSOLE, AlertChannel.WEBHOOK]
                )
    
    async def _trigger_alert(
        self,
        user_id: str,
        rule_name: str,
        severity: AlertSeverity,
        message: str,
        data: Dict,
        channels: List[AlertChannel] = None
    ):
        """触发告警"""
        rule = self._rules.get(rule_name)
        
        if rule:
            # 检查冷却时间
            if rule.last_triggered:
                elapsed = datetime.utcnow() - rule.last_triggered
                if elapsed < timedelta(minutes=rule.cooldown_minutes):
                    return  # 冷却中
            
            rule.last_triggered = datetime.utcnow()
            rule.trigger_count += 1
            
            channels = channels or rule.channels
        
        # 创建告警事件
        event = AlertEvent(
            id=f"alert_{datetime.utcnow().timestamp()}_{user_id}",
            rule_name=rule_name,
            severity=severity,
            message=message,
            data={"user_id": user_id, **data},
            timestamp=datetime.utcnow()
        )
        
        self._events.append(event)
        
        # 发送通知
        await self._send_notifications(event, channels)
    
    async def _send_notifications(
        self, 
        event: AlertEvent, 
        channels: List[AlertChannel]
    ):
        """发送通知"""
        for channel in channels:
            handlers = self._handlers.get(channel, [])
            
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"通知发送失败 {channel}: {e}")
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[AlertEvent]:
        """获取活跃告警"""
        alerts = [e for e in self._events if not e.resolved]
        
        if severity:
            alerts = [e for e in alerts if e.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        for event in self._events:
            if event.id == alert_id:
                event.acknowledged = True
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for event in self._events:
            if event.id == alert_id:
                event.resolved = True
                return True
        return False
    
    def get_alert_stats(self, days: int = 7) -> Dict:
        """获取告警统计"""
        since = datetime.utcnow() - timedelta(days=days)
        recent = [e for e in self._events if e.timestamp > since]
        
        stats = {
            "total": len(recent),
            "by_severity": {},
            "by_rule": {},
            "acknowledged": sum(1 for e in recent if e.acknowledged),
            "resolved": sum(1 for e in recent if e.resolved),
        }
        
        for sev in AlertSeverity:
            stats["by_severity"][sev.value] = sum(
                1 for e in recent if e.severity == sev
            )
        
        for event in recent:
            stats["by_rule"][event.rule_name] = \
                stats["by_rule"].get(event.rule_name, 0) + 1
        
        return stats


# 预定义的健康告警规则
DEFAULT_HEALTH_RULES = [
    AlertRule(
        name="critical_hypertension",
        description="严重高血压警报",
        condition="systolic >= 180 or diastolic >= 110",
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.CONSOLE, AlertChannel.WEBHOOK],
        cooldown_minutes=60
    ),
    AlertRule(
        name="high_blood_pressure",
        description="血压偏高",
        condition="systolic >= 140 or diastolic >= 90",
        severity=AlertSeverity.HIGH,
        channels=[AlertChannel.CONSOLE],
        cooldown_minutes=240
    ),
    AlertRule(
        name="emotional_crisis",
        description="情绪危机检测",
        condition="emotion in ['depressed', 'suicidal_ideation']",
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.CONSOLE, AlertChannel.WEBHOOK, AlertChannel.SMS],
        cooldown_minutes=30
    ),
]

# 全局告警管理器
alert_manager = AlertManager()

# 注册默认规则
for rule in DEFAULT_HEALTH_RULES:
    alert_manager.add_rule(rule)
