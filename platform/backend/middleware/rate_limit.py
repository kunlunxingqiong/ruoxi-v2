"""
🌸 若曦V2 请求限流中间件
防止API被滥用，保护服务稳定性
"""
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.log_manager import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    令牌桶限流算法实现
    
    特点:
    - 平滑限流，允许突发流量
    - 支持不同路径不同限制
    - 按客户端IP区分
    """
    
    def __init__(self):
        # 存储桶: {key: (tokens, last_update)}
        self.buckets: Dict[str, Tuple[float, float]] = {}
        
        # 默认配置: (容量, 每秒填充速率)
        self.default_limit = (100, 10)  # 容量100，每秒10个
        
        # 路径特定配置
        self.path_limits = {
            # 聊天接口限制较严格 (AI调用成本高)
            "/api/v1/chat/": (20, 2),      # 容量20，每秒2个
            "/api/v1/chat": (20, 2),
            # 健康检查限制宽松
            "/health": (1000, 100),         # 容量1000，每秒100个
            # 认证接口限制中等 (防暴力破解)
            "/api/v1/auth/login": (10, 0.5),  # 容量10，每2秒1个
            "/api/v1/auth/register": (5, 0.1),  # 容量5，每10秒1个
        }
    
    def _get_bucket_key(self, request: Request) -> str:
        """获取限流桶的key (基于IP和路径)"""
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        return f"{client_ip}:{path}"
    
    def _get_limit(self, path: str) -> Tuple[int, float]:
        """获取路径的限流配置"""
        for path_pattern, limit in self.path_limits.items():
            if path.startswith(path_pattern):
                return limit
        return self.default_limit
    
    def is_allowed(self, request: Request) -> Tuple[bool, Dict]:
        """
        检查请求是否被允许
        
        Returns:
            (allowed, info): 是否允许，及限流信息
        """
        key = self._get_bucket_key(request)
        path = request.url.path
        capacity, rate = self._get_limit(path)
        
        now = time.time()
        
        # 获取或创建桶
        if key not in self.buckets:
            self.buckets[key] = (capacity, now)
        
        tokens, last_update = self.buckets[key]
        
        # 计算应该添加的令牌数
        elapsed = now - last_update
        tokens = min(capacity, tokens + elapsed * rate)
        
        # 检查是否有足够的令牌
        if tokens >= 1:
            tokens -= 1
            self.buckets[key] = (tokens, now)
            
            return True, {
                "limit": capacity,
                "remaining": int(tokens),
                "reset_time": int(now + (capacity - tokens) / rate),
                "window": int(1 / rate) if rate > 0 else 0
            }
        else:
            self.buckets[key] = (tokens, now)
            
            # 计算需要等待的时间
            wait_time = (1 - tokens) / rate if rate > 0 else 60
            
            return False, {
                "limit": capacity,
                "remaining": 0,
                "retry_after": int(wait_time),
                "message": f"请求过于频繁，请{int(wait_time)}秒后重试"
            }
    
    def cleanup(self, max_age: int = 3600):
        """清理过期的桶数据"""
        now = time.time()
        expired_keys = [
            key for key, (tokens, last_update) in self.buckets.items()
            if now - last_update > max_age
        ]
        for key in expired_keys:
            del self.buckets[key]
        
        if expired_keys:
            logger.debug(f"清理了{len(expired_keys)}个过期限流桶")


# 全局限流器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求限流中间件
    
    自动为所有API请求添加限流保护
    """
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查限流
        allowed, info = rate_limiter.is_allowed(request)
        
        # 添加限流响应头
        headers = {
            "X-RateLimit-Limit": str(info.get("limit", 100)),
            "X-RateLimit-Remaining": str(info.get("remaining", 0)),
            "X-RateLimit-Reset": str(info.get("reset_time", 0)),
        }
        
        if not allowed:
            # 被限流了
            logger.warning(
                f"⛔ 限流触发 | {request.client.host} | {request.url.path}",
                extra={
                    "client_ip": request.client.host if request.client else None,
                    "path": request.url.path,
                    "retry_after": info.get("retry_after")
                }
            )
            
            return JSONResponse(
                status_code=429,
                headers={**headers, "Retry-After": str(info.get("retry_after", 60))},
                content={
                    "success": False,
                    "error_code": 1006,
                    "message": info.get("message", "请求过于频繁"),
                    "retry_after": info.get("retry_after", 60)
                }
            )
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加限流头到响应
        for header, value in headers.items():
            response.headers[header] = value
        
        return response


# 装饰器方式限流 (用于特定端点)
def rate_limit_by_ip(requests: int = 10, window: int = 60):
    """
    IP级别的限流装饰器
    
    Args:
        requests: 窗口期内允许的请求数
        window: 时间窗口（秒）
    """
    def decorator(func):
        # 存储请求记录: {ip: [(timestamp, count), ...]}
        request_log: Dict[str, list] = {}
        
        async def wrapper(*args, **kwargs):
            # 获取request对象
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                for v in kwargs.values():
                    if isinstance(v, Request):
                        request = v
                        break
            
            if request is None:
                return await func(*args, **kwargs)
            
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            
            # 清理旧记录
            if client_ip in request_log:
                request_log[client_ip] = [
                    (ts, cnt) for ts, cnt in request_log[client_ip]
                    if now - ts < window
                ]
            else:
                request_log[client_ip] = []
            
            # 计算当前窗口内的请求数
            current_count = sum(cnt for ts, cnt in request_log[client_ip])
            
            if current_count >= requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，请{window}秒后再试"
                )
            
            # 记录本次请求
            request_log[client_ip].append((now, 1))
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 限流中间件测试")
    print("=" * 60)
    
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    client = TestClient(app)
    
    print("\n【限流测试】发送10个请求...")
    for i in range(10):
        response = client.get("/test")
        remaining = response.headers.get("X-RateLimit-Remaining")
        print(f"  请求 {i+1}: 状态={response.status_code}, 剩余={remaining}")
    
    print("\n限速配置:")
    for path, (cap, rate) in rate_limiter.path_limits.items():
        print(f"  {path}: 容量={cap}, 速率={rate}/秒")
    
    print("\n" + "=" * 60)
