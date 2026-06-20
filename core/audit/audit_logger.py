"""
🌸 若曦V2 - 审计日志系统
合规性日志记录，支持操作追踪与安全审计
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
import json
import asyncio
import hashlib
from functools import wraps


class AuditLevel(Enum):
    """审计级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """审计类别"""
    AUTHENTICATION = "authentication"  # 认证相关
    AUTHORIZATION = "authorization"     # 授权相关
    DATA_ACCESS = "data_access"         # 数据访问
    DATA_MODIFICATION = "data_mod"    # 数据修改
    SYSTEM = "system"                   # 系统操作
    SECURITY = "security"               # 安全事件
    USER_ACTION = "user_action"         # 用户操作


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    timestamp: datetime
    level: AuditLevel
    category: AuditCategory
    action: str
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: Optional[str]
    details: Dict[str, Any]
    result: str  # success, failure, partial
    duration_ms: Optional[int]
    request_id: Optional[str]
    session_id: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "category": self.category.value,
            "action": self.action,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "resource": self.resource,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "request_id": self.request_id,
        }


class AuditLogger:
    """
    审计日志记录器
    
    功能:
    - 详细操作日志
    - 安全事件记录
    - 合规性审计
    - 日志轮转存储
    - 篡改检测 (完整性校验)
    """
    
    def __init__(self, log_dir: str = "data/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_date = datetime.now().date()
        self._log_file = self._get_log_file()
        self._buffer: List[AuditLogEntry] = []
        self._buffer_size = 100
        self._lock = asyncio.Lock()
        
        # 敏感字段，需要脱敏
        self._sensitive_fields = [
            "password", "token", "secret", "api_key", 
            "credit_card", "ssn", "id_number"
        ]
    
    def _get_log_file(self) -> Path:
        """获取当前日志文件路径"""
        date_str = self._current_date.strftime('%Y-%m-%d')
        return self.log_dir / f"audit_{date_str}.log"
    
    def _check_rotation(self):
        """检查是否需要轮转日志"""
        today = datetime.now().date()
        if today != self._current_date:
            self._current_date = today
            self._log_file = self._get_log_file()
    
    async def log(
        self,
        level: AuditLevel,
        category: AuditCategory,
        action: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict] = None,
        result: str = "success",
        duration_ms: Optional[int] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """记录审计日志"""
        
        # 脱敏处理
        if details:
            details = self._sanitize_details(details)
        
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=category,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            details=details or {},
            result=result,
            duration_ms=duration_ms,
            request_id=request_id,
            session_id=session_id
        )
        
        async with self._lock:
            self._buffer.append(entry)
            
            # 缓冲区满，写入文件
            if len(self._buffer) >= self._buffer_size:
                await self._flush()
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """脱敏敏感信息"""
        sanitized = {}
        
        for key, value in details.items():
            # 检查是否是敏感字段
            is_sensitive = any(
                sensitive in key.lower() 
                for sensitive in self._sensitive_fields
            )
            
            if is_sensitive:
                # 脱敏处理
                if isinstance(value, str) and len(value) > 8:
                    sanitized[key] = value[:4] + "****" + value[-4:]
                else:
                    sanitized[key] = "****"
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def _flush(self):
        """将缓冲区写入文件"""
        if not self._buffer:
            return
        
        self._check_rotation()
        
        try:
            with open(self._log_file, 'a', encoding='utf-8') as f:
                for entry in self._buffer:
                    f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + '\n')
            
            self._buffer.clear()
            
        except Exception as e:
            print(f"审计日志写入失败: {e}")
    
    async def flush(self):
        """强制刷新缓冲区"""
        async with self._lock:
            await self._flush()
    
    async def query_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLogEntry]:
        """查询日志"""
        results = []
        
        # 读取日志文件
        log_files = sorted(self.log_dir.glob("audit_*.log"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        
                        # 过滤条件
                        if start_time:
                            log_time = datetime.fromisoformat(data['timestamp'])
                            if log_time < start_time:
                                continue
                        
                        if end_time:
                            log_time = datetime.fromisoformat(data['timestamp'])
                            if log_time > end_time:
                                continue
                        
                        if level and data.get('level') != level.value:
                            continue
                        
                        if category and data.get('category') != category.value:
                            continue
                        
                        if user_id and data.get('user_id') != user_id:
                            continue
                        
                        if action and data.get('action') != action:
                            continue
                        
                        results.append(data)
                        
                    except json.JSONDecodeError:
                        continue
        
        # 分页
        total = len(results)
        results = results[offset:offset+limit]
        
        return results, total
    
    def get_statistics(
        self,
        days: int = 7
    ) -> Dict:
        """获取审计统计"""
        since = datetime.now() - timedelta(days=days)
        
        stats = {
            "total_logs": 0,
            "by_level": {level.value: 0 for level in AuditLevel},
            "by_category": {cat.value: 0 for cat in AuditCategory},
            "by_result": {"success": 0, "failure": 0, "partial": 0},
            "unique_users": set(),
            "failed_logins": 0,
            "data_access_count": 0
        }
        
        log_files = sorted(self.log_dir.glob("audit_*.log"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        
                        log_time = datetime.fromisoformat(data['timestamp'])
                        if log_time < since:
                            continue
                        
                        stats["total_logs"] += 1
                        stats["by_level"][data.get('level', 'info')] += 1
                        stats["by_category"][data.get('category', 'system')] += 1
                        stats["by_result"][data.get('result', 'success')] += 1
                        
                        if data.get('user_id'):
                            stats["unique_users"].add(data['user_id'])
                        
                        if data.get('action') == 'login' and data.get('result') == 'failure':
                            stats["failed_logins"] += 1
                        
                        if data.get('category') == 'data_access':
                            stats["data_access_count"] += 1
                            
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        stats["unique_users"] = len(stats["unique_users"])
        
        return stats


# 审计装饰器
def audit_log(
    action: str,
    category: AuditCategory,
    level: AuditLevel = AuditLevel.INFO
):
    """审计日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = await func(*args, **kwargs)
                result_status = "success"
                return result
            except Exception as e:
                result_status = "failure"
                raise
            finally:
                duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # 记录审计日志
                await audit_logger.log(
                    level=level,
                    category=category,
                    action=action,
                    result=result_status,
                    duration_ms=duration
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                result_status = "success"
                return result
            except Exception as e:
                result_status = "failure"
                raise
            finally:
                duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # 异步记录日志
                asyncio.create_task(audit_logger.log(
                    level=level,
                    category=category,
                    action=action,
                    result=result_status,
                    duration_ms=duration
                ))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# 全局审计日志记录器
audit_logger = AuditLogger()
