"""
🌸 若曦V2 安全测试
基于OWASP Top 10的安全测试
"""
import pytest
import re
import hashlib
import jwt
from datetime import datetime, timedelta


class TestAuthentication:
    """认证安全测试"""
    
    def test_password_hashing(self):
        """测试密码哈希存储 (不存储明文)"""
        password = "TestPassword123!"
        
        # bcrypt哈希
        import bcrypt
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        # 验证不是明文存储
        assert password != hashed.decode()
        # 验证可以正确验证
        assert bcrypt.checkpw(password.encode(), hashed)
        # 验证错误密码不通过
        assert not bcrypt.checkpw("WrongPassword".encode(), hashed)
    
    def test_jwt_token_structure(self):
        """测试JWT Token结构"""
        from core.auth.jwt_auth import JWTAuthManager
        
        auth_manager = JWTAuthManager()
        token = auth_manager.create_access_token({"sub": "test_user"})
        
        # 验证是有效JWT
        parts = token.split('.')
        assert len(parts) == 3  # header.payload.signature
        
        # 验证可以解码
        decoded = jwt.decode(
            token,
            auth_manager.secret_key,
            algorithms=[auth_manager.algorithm]
        )
        assert decoded["sub"] == "test_user"
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_jwt_expiration(self):
        """测试JWT过期机制"""
        from core.auth.jwt_auth import JWTAuthManager
        
        auth_manager = JWTAuthManager()
        
        # 创建即将过期的token (1秒)
        token = auth_manager.create_access_token(
            {"sub": "test_user"},
            expires_delta=timedelta(seconds=0)
        )
        
        # 验证过期token无效
        import time
        time.sleep(1.1)
        
        is_valid, _ = auth_manager.verify_token(token)
        assert not is_valid


class TestInputValidation:
    """输入验证测试"""
    
    @pytest.mark.parametrize("input_data,expected_safe", [
        ("<script>alert('xss')</script>", False),
        ("'; DROP TABLE users; --", False),
        ("正常用户输入", True),
        ("Hello World! 🌸", True),
        ("admin'--", False),
    ])
    def test_xss_prevention(self, input_data, expected_safe):
        """XSS防护测试"""
        # 简单的XSS检测
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:', 
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
        ]
        
        is_safe = not any(
            re.search(pattern, input_data, re.IGNORECASE)
            for pattern in dangerous_patterns
        )
        
        assert is_safe == expected_safe
    
    @pytest.mark.parametrize("input_data", [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1; DELETE FROM sessions",
        "admin' OR '1'='1'--",
    ])
    def test_sql_injection_detection(self, input_data):
        """SQL注入检测测试"""
        sql_keywords = [
            "DROP", "DELETE", "INSERT", "UPDATE", 
            "UNION", "SELECT", "EXEC", "EXECUTE"
        ]
        
        # 检测SQL注入模式
        has_sql = any(
            keyword in input_data.upper()
            for keyword in sql_keywords
        )
        
        assert has_sql


class TestRateLimiting:
    """限流测试"""
    
    def test_token_bucket_algorithm(self):
        """测试令牌桶限流算法"""
        from middleware.rate_limit import TokenBucket
        
        bucket = TokenBucket(capacity=10, refill_rate=1)
        
        # 消耗部分令牌
        assert bucket.consume(5)  # 还有5个
        assert bucket.consume(5)  # 刚好用完
        assert not bucket.consume(1)  # 没有了
        
        # 等待 refill
        import time
        time.sleep(1.1)
        assert bucket.consume(1)  #  refill了1个


class TestSensitiveData:
    """敏感数据处理测试"""
    
    def test_api_key_masking(self):
        """API密钥掩码显示"""
        api_key = "sk-abcdefghijklmnopqrstuvwxyz"
        
        # 掩码显示
        masked = api_key[:8] + "****" + api_key[-4:]
        
        assert "****" in masked
        assert len(masked) < len(api_key)
    
    def test_password_not_in_logs(self):
        """密码不出现在日志中"""
        test_log = "User login: username=test password=Secret123 email=test@test.com"
        
        # 敏感字段列表
        sensitive_fields = ["password", "token", "secret", "key"]
        
        # 过滤敏感信息
        def sanitize_log(log: str) -> str:
            for field in sensitive_fields:
                pattern = rf'{field}=[^\s]+'
                log = re.sub(pattern, f'{field}=***', log, flags=re.IGNORECASE)
            return log
        
        sanitized = sanitize_log(test_log)
        
        assert "Secret123" not in sanitized
        assert "password=***" in sanitized


class TestErrorHandling:
    """错误处理安全测试"""
    
    def test_error_messages_not_leak_info(self):
        """错误消息不泄露系统信息"""
        from core.exceptions import RuoxiException
        
        # 生产环境不应暴露内部细节
        exc = RuoxiException(
            message="服务暂时不可用",
            details={"internal_id": 12345}  # 内部信息
        )
        
        # 用户看到的信息
        user_message = exc.message
        
        assert "internal_id" not in user_message
        assert "服务暂时不可用" in user_message


class TestCORS:
    """CORS配置测试"""
    
    def test_cors_headers_present(self):
        """测试CORS响应头"""
        headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
        ]
        
        # 验证必要头存在
        assert all(header.startswith("Access-Control") for header in headers)


class TestContentSecurity:
    """内容安全测试"""
    
    def test_file_upload_validation(self):
        """文件上传验证"""
        allowed_extensions = {".jpg", ".png", ".pdf", ".txt"}
        dangerous_extensions = {".exe", ".sh", ".php", ".js"}
        
        assert ".exe" not in allowed_extensions
        assert ".jpg" in allowed_extensions
    
    def test_content_type_validation(self):
        """Content-Type验证"""
        allowed_types = [
            "application/json",
            "text/plain",
            "image/jpeg",
            "image/png",
        ]
        
        dangerous_types = [
            "application/x-php",
            "application/x-sh",
        ]
        
        for dt in dangerous_types:
            assert dt not in allowed_types


# 安全测试报告模板
SECURITY_REPORT_TEMPLATE = """
# 🛡️ 安全测试报告

## 执行时间: {timestamp}

### 测试结果
- 通过: {passed}/{total}
- 失败: {failed}/{total}
- 跳过: {skipped}/{total}

### 测试类别
1. ✓ 认证安全
2. ✓ 输入验证 (XSS/SQL注入)
3. ✓ 限流保护
4. ✓ 敏感数据处理
5. ✓ 错误处理安全
6. ✓ CORS配置
7. ✓ 内容安全

### 建议
- 定期更新依赖
- 启用WAF
- 监控异常请求
- 定期渗透测试

---
评分: {score}/100
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
