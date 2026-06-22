"""
🌸 若曦V2 异常处理框架 V2
增强的错误处理和优雅降级
"""

from enum import Enum
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class ErrorCode(Enum):
    """错误码枚举 V2"""

    # 通用错误 (1000-1999)
    SUCCESS = 0
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    AUTHENTICATION_ERROR = 1002
    NOT_FOUND = 1004
    FORBIDDEN = 1003
    RATE_LIMIT_ERROR = 1029

    # AI服务错误 (2000-2999)
    AI_SERVICE_ERROR = 2000
    AI_TIMEOUT = 2001
    AI_RATE_LIMIT = 2002
    AI_ALL_MODELS_FAILED = 2003
    AI_INVALID_RESPONSE = 2004

    # 数据库错误 (3000-3999)
    DATABASE_ERROR = 3000
    DB_CONNECTION_ERROR = 3001
    DB_QUERY_ERROR = 3002
    DB_INTEGRITY_ERROR = 3003

    # 缓存错误 (4000-4999)
    CACHE_ERROR = 4000
    CACHE_CONNECTION_ERROR = 4001
    CACHE_SERIALIZATION_ERROR = 4002

    # 业务逻辑错误 (5000-5999)
    BUSINESS_ERROR = 5000
    INSUFFICIENT_BALANCE = 5001
    RESOURCE_UNAVAILABLE = 5002
    OPERATION_FAILED = 5003

    # 外部服务错误 (6000-6999)
    EXTERNAL_SERVICE_ERROR = 6000
    NETWORK_ERROR = 6001
    THIRD_PARTY_ERROR = 6002


class RuoxiException(Exception):
    """
    若曦异常基类 V2

    Attributes:
        error_code: 错误码
        message: 错误消息
        details: 详细错误信息
        suggestion: 用户建议
        retryable: 是否可重试
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict] = None,
        suggestion: Optional[str] = None,
        retryable: bool = False,
        http_status_code: int = 500,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.suggestion = suggestion
        self.retryable = retryable
        self.http_status_code = http_status_code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "retryable": self.retryable,
            "http_status": self.http_status_code,
        }

        if self.details:
            result["details"] = self.details

        if self.suggestion:
            result["suggestion"] = self.suggestion

        return result


# ========== 具体异常类 ==========


class ValidationException(RuoxiException):
    """数据验证异常"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details,
            suggestion="请检查输入数据格式",
            retryable=False,
            http_status_code=400,
        )


class AuthenticationError(RuoxiException):
    """认证异常"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            suggestion="请重新登录或检查Token",
            retryable=False,
            http_status_code=401,
        )


class NotFoundException(RuoxiException):
    """资源未找到异常"""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} '{identifier}' 未找到",
            error_code=ErrorCode.NOT_FOUND,
            suggestion=f"请检查{resource}标识是否正确",
            retryable=False,
            http_status_code=404,
        )


class RateLimitException(RuoxiException):
    """限流异常"""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="请求过于频繁，请稍后再试",
            error_code=ErrorCode.RATE_LIMIT_ERROR,
            details={"retry_after": retry_after},
            suggestion=f"请等待{retry_after}秒后重试",
            retryable=True,
            http_status_code=429,
        )


class AIException(RuoxiException):
    """AI服务异常"""

    def __init__(
        self,
        message: str = "AI服务暂时不可用",
        error_code: ErrorCode = ErrorCode.AI_SERVICE_ERROR,
        details: Optional[Dict] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            suggestion="AI服务繁忙，请稍后重试",
            retryable=True,
            http_status_code=503,
        )


class AITimeoutException(AIException):
    """AI请求超时"""

    def __init__(self, timeout: float = 30.0):
        super().__init__(
            message=f"AI响应超时 ({timeout}秒)",
            error_code=ErrorCode.AI_TIMEOUT,
            details={"timeout": timeout},
            suggestion="请稍后重试或简化请求",
            retryable=True,
            http_status_code=504,
        )


class AIAllModelsFailedException(AIException):
    """所有AI模型都失败"""

    def __init__(self, tried_models: list):
        super().__init__(
            message="所有AI模型均不可用",
            error_code=ErrorCode.AI_ALL_MODELS_FAILED,
            details={"tried_models": tried_models},
            suggestion="系统繁忙，请稍后重试或联系管理员",
            retryable=True,
            http_status_code=503,
        )


class DatabaseException(RuoxiException):
    """数据库异常"""

    def __init__(
        self,
        message: str = "数据库操作失败",
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            suggestion="数据操作失败，请稍后重试",
            retryable=True,
            http_status_code=500,
        )


class CacheException(RuoxiException):
    """缓存异常"""

    def __init__(self, message: str = "缓存操作失败"):
        super().__init__(
            message=message,
            error_code=ErrorCode.CACHE_ERROR,
            suggestion="缓存服务异常，系统将继续运行但性能可能降低",
            retryable=True,
            http_status_code=500,
        )


class ExternalServiceException(RuoxiException):
    """外部服务异常"""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service}服务异常: {message}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            suggestion=f"{service}服务暂时不可用，请稍后重试",
            retryable=True,
            http_status_code=502,
        )


class MemoryException(RuoxiException):
    """记忆系统异常"""

    def __init__(self, message: str = "记忆操作失败"):
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_ERROR,
            suggestion="记忆功能暂时不可用，对话仍可继续",
            retryable=False,
            http_status_code=500,
        )


# ========== 全局异常处理器 ==========


class GlobalExceptionHandler:
    """全局异常处理器 V2"""

    @staticmethod
    def handle_exception(exc: Exception) -> Dict[str, Any]:
        """
        统一处理所有异常

        Returns:
            标准化的错误响应
        """
        if isinstance(exc, RuoxiException):
            # 若曦自定义异常
            return exc.to_dict()

        # Python内置异常映射
        exception_mapping = {
            "ValueError": (ErrorCode.VALIDATION_ERROR, 400),
            "TypeError": (ErrorCode.VALIDATION_ERROR, 400),
            "KeyError": (ErrorCode.NOT_FOUND, 404),
            "IndexError": (ErrorCode.NOT_FOUND, 404),
            "ConnectionError": (ErrorCode.NETWORK_ERROR, 503),
            "TimeoutError": (ErrorCode.AI_TIMEOUT, 504),
        }

        exc_type = type(exc).__name__
        error_code, http_status = exception_mapping.get(
            exc_type, (ErrorCode.UNKNOWN_ERROR, 500)
        )

        return {
            "error_code": error_code.value,
            "error_name": error_code.name,
            "message": str(exc) or "未知错误",
            "retryable": http_status >= 500,
            "http_status": http_status,
            "type": exc_type,
        }

    @staticmethod
    def create_error_response(
        exc: Exception, include_traceback: bool = False
    ) -> JSONResponse:
        """创建FastAPI错误响应"""
        error_dict = GlobalExceptionHandler.handle_exception(exc)
        http_status = error_dict.get("http_status", 500)

        # 生产环境不暴露详细信息
        if not include_traceback:
            error_dict.pop("details", None)

        # 添加友好的用户消息
        error_dict["friendly_message"] = GlobalExceptionHandler._get_friendly_message(
            error_dict
        )

        return JSONResponse(status_code=http_status, content=error_dict)

    @staticmethod
    def _get_friendly_message(error_dict: Dict) -> str:
        """获取用户友好的错误消息"""
        code = error_dict.get("error_name", "UNKNOWN_ERROR")

        friendly_messages = {
            "VALIDATION_ERROR": "输入数据有问题，请检查一下~ 🌸",
            "AUTHENTICATION_ERROR": "登录好像过期了，重新登录一下吧~ 💜",
            "NOT_FOUND": "找不到你要的东西，是不是地址错了？👀",
            "RATE_LIMIT_ERROR": "太热情啦！稍微等一下再试~ ⏳",
            "AI_SERVICE_ERROR": "若曦的大脑有点累，让我休息一下~ 🤖",
            "AI_TIMEOUT": "若曦想得太久啦，再试一次好吗？💭",
            "DATABASE_ERROR": "数据小精灵出错了，正在修复中~ 🗄️",
            "CACHE_ERROR": "记忆有点混乱，但不影响聊天~ 💭",
            "EXTERNAL_SERVICE_ERROR": "外部服务有点问题，稍后再试~ 🌐",
            "UNKNOWN_ERROR": "发生了一点小意外，但 hazırlanıyor~ 🌸",
        }

        return friendly_messages.get(
            code, error_dict.get("message", "出了点小问题，请稍后重试~ 🌸")
        )


# ========== 错误恢复策略 ==========


class ErrorRecovery:
    """错误恢复策略"""

    @staticmethod
    def with_fallback(fallback_value: Any = None, max_retries: int = 3):
        """
        带降级的装饰器

        使用方式:
        @ErrorRecovery.with_fallback(fallback_value={"error": "服务降级"})
        async def critical_function():
            ...
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                retries = 0
                last_error = None

                while retries < max_retries:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        retries += 1
                        if retries < max_retries:
                            # 指数退避
                            await __import__("asyncio").sleep(2**retries)

                # 所有重试都失败，返回降级值
                return fallback_value

            return wrapper

        return decorator

    @staticmethod
    def circuit_breaker(threshold: int = 5, timeout: int = 60):
        """
        熔断器装饰器 (简化版)

        连续失败threshold次后，进入熔断状态timeout秒
        """
        # 状态存储
        failures = {}

        def decorator(func):
            async def wrapper(*args, **kwargs):
                func_name = func.__name__

                # 检查熔断状态
                if func_name in failures:
                    failure_info = failures[func_name]
                    if failure_info["count"] >= threshold:
                        if (
                            __import__("time").time() - failure_info["last_time"]
                            < timeout
                        ):
                            raise RuoxiException(
                                "服务暂时不可用(熔断)",
                                ErrorCode.SERVICE_UNAVAILABLE,
                                suggestion="服务繁忙，请稍后重试",
                            )
                        else:
                            # 熔断时间过期，重置
                            del failures[func_name]

                try:
                    result = await func(*args, **kwargs)
                    # 成功，清除失败记录
                    if func_name in failures:
                        del failures[func_name]
                    return result

                except Exception as e:
                    # 记录失败
                    if func_name not in failures:
                        failures[func_name] = {"count": 0, "last_time": 0}

                    failures[func_name]["count"] += 1
                    failures[func_name]["last_time"] = __import__("time").time()

                    raise

            return wrapper

        return decorator


# ========== 助手函数 ==========


def safe_execute(
    func, *args, default=None, ignore_exceptions: tuple = (Exception,), **kwargs
):
    """
    安全执行函数

    执行func，如果出错返回default值而不抛出异常

    使用方式:
    result = safe_execute(expensive_operation, default="默认值")
    """
    try:
        if __import__("asyncio").iscoroutinefunction(func):
            # 需要await，这里简化处理
            return default
        return func(*args, **kwargs)
    except ignore_exceptions:
        return default


if __name__ == "__main__":
    from core.log_manager import get_logger

    logger = get_logger(__name__)

    print("=" * 60)
    print("🌸 若曦V2 异常处理框架 V2")
    print("=" * 60)

    print("\n【错误分类】")
    for code in ErrorCode:
        print(f"  {code.value}: {code.name}")

    print("\n【异常类】")
    exceptions = [
        ValidationException("测试验证错误"),
        NotFoundException("用户", "123"),
        RateLimitException(60),
        AIException("AI服务错误"),
        AITimeoutException(30.0),
    ]

    for exc in exceptions:
        result = exc.to_dict()
        print(f"\n  {exc.__class__.__name__}:")
        print(f"    错误码: {result['error_code']}")
        print(f"    消息: {result['message']}")
        print(f"    HTTP状态: {result['http_status']}")
        print(f"    建议: {result.get('suggestion', '无')}")

    print("\n【全局处理器】")
    test_error = ValueError("测试错误")
    handled = GlobalExceptionHandler.handle_exception(test_error)
    print(f"  原始: ValueError")
    print(f"  处理后: {handled['error_name']}")
    print(f"  友好消息: {handled['message']}")

    print("\n" + "=" * 60)
    print("✅ 异常处理框架 V2 就绪")
    print("=" * 60)
