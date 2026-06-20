"""
🌸 若曦V2 异常处理模块
统一的错误码和友好的错误处理
"""
from typing import Dict, Any, Optional
from enum import Enum


class ErrorCode(Enum):
    """错误码枚举"""
    # 成功
    SUCCESS = (0, "成功")
    
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = (1000, "未知错误")
    INVALID_PARAMETER = (1001, "参数无效")
    MISSING_PARAMETER = (1002, "缺少必要参数")
    UNAUTHORIZED = (1003, "未授权访问")
    FORBIDDEN = (1004, "禁止访问")
    NOT_FOUND = (1005, "资源不存在")
    RATE_LIMITED = (1006, "请求频率超限")
    SERVICE_UNAVAILABLE = (1007, "服务暂时不可用")
    
    # AI相关错误 (2000-2999)
    AI_MODEL_ERROR = (2000, "AI模型调用失败")
    AI_TIMEOUT = (2001, "AI响应超时")
    AI_RATE_LIMITED = (2002, "AI接口频率限制")
    AI_INVALID_RESPONSE = (2003, "AI响应格式异常")
    AI_TOKEN_EXCEEDED = (2004, "Token超出限制")
    
    # 记忆相关错误 (3000-3999)
    MEMORY_NOT_FOUND = (3000, "记忆不存在")
    MEMORY_SAVE_FAILED = (3001, "记忆保存失败")
    MEMORY_LOAD_FAILED = (3002, "记忆加载失败")
    MEMORY_INDEX_ERROR = (3003, "记忆索引错误")
    
    # 数据库错误 (4000-4999)
    DB_CONNECTION_ERROR = (4000, "数据库连接失败")
    DB_QUERY_ERROR = (4001, "数据库查询错误")
    DB_INSERT_ERROR = (4002, "数据插入失败")
    DB_UPDATE_ERROR = (4003, "数据更新失败")
    
    # 外部服务错误 (5000-5999)
    API_REQUEST_FAILED = (5000, "API请求失败")
    API_RESPONSE_ERROR = (5001, "API响应异常")
    API_TIMEOUT = (5002, "API请求超时")
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class RuoxiException(Exception):
    """
    若曦自定义异常基类
    
    Attributes:
        error_code: 错误码
        message: 错误信息
        details: 详细错误信息
    """
    
    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message or error_code.message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于API响应）"""
        return {
            "success": False,
            "error_code": self.error_code.code,
            "message": self.message,
            "details": self.details,
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code.code}] {self.message}"


# 具体异常类
class ValidationException(RuoxiException):
    """参数验证异常"""
    def __init__(self, message: str = "参数验证失败", details: Optional[Dict] = None):
        super().__init__(ErrorCode.INVALID_PARAMETER, message, details)


class AIException(RuoxiException):
    """AI模型异常"""
    def __init__(self, message: str = "AI模型调用失败", details: Optional[Dict] = None):
        super().__init__(ErrorCode.AI_MODEL_ERROR, message, details)


class AITimeoutException(RuoxiException):
    """AI响应超时异常"""
    def __init__(self, message: str = "AI响应超时", details: Optional[Dict] = None):
        super().__init__(ErrorCode.AI_TIMEOUT, message, details)


class MemoryException(RuoxiException):
    """记忆操作异常"""
    def __init__(self, message: str = "记忆操作失败", details: Optional[Dict] = None):
        super().__init__(ErrorCode.MEMORY_SAVE_FAILED, message, details)


class DatabaseException(RuoxiException):
    """数据库异常"""
    def __init__(self, message: str = "数据库操作失败", details: Optional[Dict] = None):
        super().__init__(ErrorCode.DB_CONNECTION_ERROR, message, details)


class APIException(RuoxiException):
    """外部API异常"""
    def __init__(self, message: str = "API请求失败", details: Optional[Dict] = None):
        super().__init__(ErrorCode.API_REQUEST_FAILED, message, details)


# 全局异常处理器
class GlobalExceptionHandler:
    """全局异常处理器"""
    
    @staticmethod
    def handle_exception(exception: Exception) -> Dict[str, Any]:
        """处理异常并返回标准响应"""
        if isinstance(exception, RuoxiException):
            return exception.to_dict()
        
        # 处理Python内置异常
        if isinstance(exception, ValueError):
            return RuoxiException(
                ErrorCode.INVALID_PARAMETER,
                str(exception)
            ).to_dict()
        
        if isinstance(exception, KeyError):
            return RuoxiException(
                ErrorCode.MISSING_PARAMETER,
                f"缺少必要参数: {str(exception)}"
            ).to_dict()
        
        if isinstance(exception, TimeoutError):
            return RuoxiException(
                ErrorCode.AI_TIMEOUT,
                "操作超时"
            ).to_dict()
        
        # 未知异常
        return RuoxiException(
            ErrorCode.UNKNOWN_ERROR,
            f"服务器内部错误: {str(exception)}"
        ).to_dict()
    
    @staticmethod
    def wrap_async(func):
        """异步函数异常包装器装饰器"""
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                print(f"[Exception] {type(e).__name__}: {e}")
                return GlobalExceptionHandler.handle_exception(e)
        
        return wrapper
    
    @staticmethod
    def wrap_sync(func):
        """同步函数异常包装器装饰器"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"[Exception] {type(e).__name__}: {e}")
                return GlobalExceptionHandler.handle_exception(e)
        
        return wrapper


# 便捷装饰器
def safe_async(func):
    """安全的异步装饰器"""
    return GlobalExceptionHandler.wrap_async(func)


def safe_sync(func):
    """安全的同步装饰器"""
    return GlobalExceptionHandler.wrap_sync(func)


if __name__ == "__main__":
    # 测试异常处理
    print("=" * 60)
    print("🌸 若曦V2 异常处理模块测试")
    print("=" * 60)
    
    print("\n【错误码测试】")
    for code in ErrorCode:
        print(f"  {code.name}: {code.code} - {code.message}")
    
    print("\n【异常类测试】")
    
    # 创建异常
    ai_error = AIException("模型调用超时", {"model": "gemini", "timeout": 30})
    print(f"  AIException: {ai_error}")
    print(f"  Response: {ai_error.to_dict()}")
    
    # 全局异常处理
    print("\n【全局异常处理器测试】")
    error = GlobalExceptionHandler.handle_exception(ValueError("年龄必须是数字"))
    print(f"  ValueError -> {error}")
    
    print("\n✅ 异常处理模块测试完成")
