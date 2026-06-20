"""
🌸 若曦V2 异常处理单元测试
目标: 验证错误码和异常类功能
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))

from exceptions import (
    ErrorCode,
    RuoxiException,
    AIException,
    AITimeoutException,
    MemoryException,
    DatabaseException,
    APIException,
    ValidationException,
    GlobalExceptionHandler,
)


class TestErrorCode:
    """错误码枚举测试"""
    
    def test_error_code_values(self):
        """测试错误码值正确性"""
        assert ErrorCode.SUCCESS.code == 0
        assert ErrorCode.UNKNOWN_ERROR.code == 1000
        assert ErrorCode.INVALID_PARAMETER.code == 1001
        assert ErrorCode.AI_MODEL_ERROR.code == 2000
        assert ErrorCode.MEMORY_NOT_FOUND.code == 3000
        assert ErrorCode.DB_CONNECTION_ERROR.code == 4000
    
    def test_error_code_messages(self):
        """测试错误码消息"""
        assert ErrorCode.SUCCESS.message == "成功"
        assert ErrorCode.UNKNOWN_ERROR.message == "未知错误"
        assert "参数" in ErrorCode.INVALID_PARAMETER.message


class TestRuoxiException:
    """自定义异常基类测试"""
    
    def test_default_exception(self):
        """测试默认异常创建"""
        exc = RuoxiException()
        assert exc.error_code == ErrorCode.UNKNOWN_ERROR
        assert exc.message == "未知错误"
        assert exc.details == {}
    
    def test_custom_exception(self):
        """测试自定义异常"""
        exc = RuoxiException(
            error_code=ErrorCode.AI_MODEL_ERROR,
            message="模型调用失败",
            details={"model": "gemini", "timeout": 30}
        )
        assert exc.error_code == ErrorCode.AI_MODEL_ERROR
        assert exc.message == "模型调用失败"
        assert exc.details["model"] == "gemini"
    
    def test_to_dict(self):
        """测试转换为字典"""
        exc = RuoxiException(
            error_code=ErrorCode.INVALID_PARAMETER,
            message="参数错误",
            details={"field": "name"}
        )
        
        result = exc.to_dict()
        assert result["success"] is False
        assert result["error_code"] == 1001
        assert result["message"] == "参数错误"
        assert result["details"]["field"] == "name"
    
    def test_str_representation(self):
        """测试字符串表示"""
        exc = RuoxiException(ErrorCode.AI_MODEL_ERROR, "模型错误")
        assert "[2000]" in str(exc)
        assert "模型错误" in str(exc)


class TestSpecificExceptions:
    """具体异常类测试"""
    
    def test_ai_exception(self):
        """测试AI异常"""
        exc = AIException("模型超时", {"model": "gpt"})
        assert exc.error_code == ErrorCode.AI_MODEL_ERROR
        assert "模型超时" in exc.message
    
    def test_ai_timeout_exception(self):
        """测试AI超时异常"""
        exc = AITimeoutException()
        assert exc.error_code == ErrorCode.AI_TIMEOUT
    
    def test_memory_exception(self):
        """测试记忆异常"""
        exc = MemoryException("记忆加载失败")
        assert exc.error_code == ErrorCode.MEMORY_SAVE_FAILED
    
    def test_database_exception(self):
        """测试数据库异常"""
        exc = DatabaseException("连接失败")
        assert exc.error_code == ErrorCode.DB_CONNECTION_ERROR
    
    def test_api_exception(self):
        """测试API异常"""
        exc = APIException("请求失败", {"status": 500})
        assert exc.error_c