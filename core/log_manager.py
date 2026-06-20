"""
🌸 若曦V2 日志管理系统
结构化日志输出，支持轮转和监控
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from .config_manager import config


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化为JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    COLORS = {
        'DEBUG': '\x1b[38;20m',     # 灰色
        'INFO': '\x1b[32;20m',       # 绿色
        'WARNING': '\x1b[33;20m',    # 黄色
        'ERROR': '\x1b[31;20m',      # 红色
        'CRITICAL': '\x1b[35;20m',   # 紫色
    }
    RESET = '\x1b[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """添加颜色"""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class LogManager:
    """统一日志管理器"""
    
    _initialized = False
    _logger: Optional[logging.Logger] = None
    
    @classmethod
    def initialize(cls):
        """初始化日志系统"""
        if cls._initialized:
            return
        
        # 获取配置
        log_level = config.get('log.level', 'INFO')
        log_format = config.get('log.format', 'text')
        log_max_size = config.get('log.max_size', '100MB')
        log_backup_count = config.get('log.backup_count', 7)
        
        # 解析日志大小
        max_bytes = cls._parse_size(log_max_size)
        
        # 创建日志目录
        log_dir = Path(__file__).parent.parent / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建logger
        logger = logging.getLogger("ruoxi")
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.handlers = []  # 清除现有处理器
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        
        if log_format == 'json':
            console_handler.setFormatter(JSONFormatter())
        else:
            colored_format = ColoredFormatter(
                '[%(asctime)s] %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(colored_format)
        
        logger.addHandler(console_handler)
        
        # 文件处理器 (轮转)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "ruoxi.log",
            maxBytes=max_bytes,
            backupCount=log_backup_count,
            encoding='utf-8'
        )
        
        # 文件始终使用JSON格式便于分析
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
        
        # 错误日志单独存储
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=max_bytes,
            backupCount=log_backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        logger.addHandler(error_handler)
        
        cls._logger = logger
        cls._initialized = True
        
        logger.info("🌸 日志系统初始化完成", extra={"service": "log_manager"})
    
    @classmethod
    def _parse_size(cls, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        multipliers = {
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(float(size_str[:-len(suffix)]) * multiplier)
        
        return int(size_str)
    
    @classmethod
    def get_logger(cls, name: str = "ruoxi") -> logging.Logger:
        """获取logger实例"""
        if not cls._initialized:
            cls.initialize()
        
        if name == "ruoxi":
            return cls._logger
        
        return logging.getLogger(name)
    
    @classmethod
    def log_api_request(cls, method: str, path: str, status_code: int, duration: float, **kwargs):
        """记录API请求日志"""
        logger = cls.get_logger()
        logger.info(
            f"API请求: {method} {path} - {status_code} ({duration:.2f}s)",
            extra={
                "type": "api_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration": duration,
                **kwargs
            }
        )
    
    @classmethod
    def log_ai_interaction(cls, model: str, tokens_used: int, duration: float, success: bool, **kwargs):
        """记录AI交互日志"""
        logger = cls.get_logger()
        status = "成功" if success else "失败"
        logger.info(
            f"AI交互{status}: {model}, tokens={tokens_used}, 耗时={duration:.2f}s",
            extra={
                "type": "ai_interaction",
                "model": model,
                "tokens_used": tokens_used,
                "duration": duration,
                "success": success,
                **kwargs
            }
        )
    
    @classmethod
    def log_memory_operation(cls, operation: str, memory_type: str, memory_id: Optional[str] = None, **kwargs):
        """记录记忆操作日志"""
        logger = cls.get_logger()
        logger.info(
            f"记忆操作: {operation} [{memory_type}]",
            extra={
                "type": "memory_operation",
                "operation": operation,
                "memory_type": memory_type,
                "memory_id": memory_id,
                **kwargs
            }
        )
    
    @classmethod
    def log_error(cls, error: Exception, context: Optional[Dict] = None):
        """记录错误日志"""
        logger = cls.get_logger()
        logger.error(
            f"错误: {str(error)}",
            exc_info=True,
            extra={
                "type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
            }
        )


# 便捷函数
def get_logger(name: str = "ruoxi") -> logging.Logger:
    """获取logger"""
    return LogManager.get_logger(name)


def log_api_request(method: str, path: str, status_code: int, duration: float, **kwargs):
    """记录API请求"""
    LogManager.log_api_request(method, path, status_code, duration, **kwargs)


def log_ai_interaction(model: str, tokens_used: int, duration: float, success: bool, **kwargs):
    """记录AI交互"""
    LogManager.log_ai_interaction(model, tokens_used, duration, success, **kwargs)


def log_memory_operation(operation: str, memory_type: str, memory_id: Optional[str] = None, **kwargs):
    """记录记忆操作"""
    LogManager.log_memory_operation(operation, memory_type, memory_id, **kwargs)


if __name__ == "__main__":
    # 测试日志系统
    print("=" * 60)
    print("🌸 若曦V2 日志管理系统测试")
    print("=" * 60)
    
    logger = get_logger()
    
    logger.debug("这是调试信息")
    logger.info("🌸 若曦V2启动成功")
    logger.warning("这是一个警告")
    logger.error("这是一个错误")
    
    # 结构化日志测试
    log_api_request("GET", "/api/health", 200, 0.15)
    log_ai_interaction("gemini-2.0-flash", 150, 2.3, True)
    log_memory_operation("保存", "长期记忆", "mem_001")
    
    print("\n✅ 日志系统测试完成")
    print("日志文件位置: data/logs/")
