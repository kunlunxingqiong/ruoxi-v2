"""
🌸 若曦V2 - API限流器
保护系统免受过载和滥用
"""
from typing import Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from functools import wraps


class RateLimitStrategy(Enum):
    """限流策略"""
    FIXED_WINDOW = "fixed_window"      # 固定窗口
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口
    TOKEN_BUCKET = "token_bucket"      # 令牌桶
    LEAKY_BUCKET = "leaky_bucket"      # 漏桶


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests: int          # 请求次数
    window_seconds: int    # 时间窗口
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst: int = 0         # 突发容量 (令牌桶用)


class RateLimitExceeded(Exception):
    """限流异常"""
    def __init__(self, retry_after: int, message: str = "请求过于频繁"):
        self.retry_after = retry_after
        self.message = message
        super().__init__(message)


class SlidingWindowCounter:
    """滑动窗口计数器"""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.requests: Dict[str, list] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, limit: int) -> Tuple[bool, int]:
        """
        检查是否允许请求
        
        Returns:
            (是否允许, 剩余请求数, 重试时间)
        """
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_size)
            
            # 清理过期请求
            if key in self.requests:
                self.requests[key] = [
                    ts for ts in self.requests[key]
                    if ts > window_start
                ]
            else:
                self.requests[key] = []
            
            # 检查限制
            current_count = len(self.requests[key])
            
            if current_count >= limit:
                # 计算重试时间
                oldest = min(self.requests[key])
                retry_after = int((oldest + timedelta(seconds=self.window_size) - now).total_seconds())
                return False, 0, max(1, retry_after)
            
            # 记录请求
            self.requests[key].append(now)
            
            remaining = limit - current_count - 1
            return True, remaining, 0
    
    async def get_stats(self, key: str) -> Dict:
        """获取统计信息"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_size)
        
        if key not in self.requests:
            return {'current': 0, 'remaining': 'N/A'}
        
        current = len([
            ts for ts in self.requests[key]
            if ts > window_start
        ])
        
        return {'current': current}


class TokenBucket:
    """令牌桶限流器"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate           # 令牌产生速率 (每秒)
        self.capacity = capacity   # 桶容量
        self.tokens: Dict[str, float] = {}
        self.last_update: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> Tuple[bool, int, int]:
        """检查是否允许请求"""
        async with self._lock:
            now = datetime.utcnow()
            
            # 初始化
            if key not in self.tokens:
                self.tokens[key] = self.capacity
                self.last_update[key] = now
            
            # 补充令牌
            elapsed = (now - self.last_update[key]).total_seconds()
            self.tokens[key] = min(
                self.capacity,
                self.tokens[key] + elapsed * self.rate
            )
            self.last_update[key] = now
            
            # 检查是否有令牌
            if self.tokens[key] >= 1:
                self.tokens[key] -= 1
                remaining = int(self.tokens[key])
                return True, remaining, 0
            else:
                # 计算等待时间
                wait_time = int((1 - self.tokens[key]) / self.rate) + 1
                return False, 0, wait_time


class RateLimiter:
    """
    API限流器
    
    功能:
    - 多策略限流 (滑动窗口/令牌桶)
    - 按用户/端点/IP限流
    - 自动 headers 设置
    - 限流告警
    """
    
    def __init__(self):
        self._sliding_window = SlidingWindowCounter()
        self._token_buckets: Dict[str, TokenBucket] = {}
        self._configs: Dict[str, RateLimitConfig] = {}
    
    def configure(
        self,
        name: str,
        requests: int,
        window_seconds: int,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
        burst: int = 0
    ):
        """配置限流规则"""
        self._configs[name] = RateLimitConfig(
            requests=requests,
            window_seconds=window_seconds,
            strategy=strategy,
            burst=burst
        )
        
        # 初始化令牌桶
        if strategy == RateLimitStrategy.TOKEN_BUCKET:
            self._token_buckets[name] = TokenBucket(
                rate=requests / window_seconds,
                capacity=burst or requests
            )
    
    async def check(
        self,
        config_name: str,
        key: str
    ) -> Tuple[bool, Dict]:
        """
        检查限流
        
        Returns:
            (是否允许, 响应头信息)
        """
        if config_name not in self._configs:
            return True, {}
        
        config = self._configs[config_name]
        
        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            allowed, remaining, retry_after = await self._sliding_window.is_allowed(
                f"{config_name}:{key}",
                config.requests
            )
            
            headers = {
                'X-RateLimit-Limit': str(config.requests),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Window': str(config.window_seconds)
            }
            
            if not allowed:
                headers['Retry-After'] = str(retry_after)
                raise RateLimitExceeded(retry_after)
            
            return True, headers
        
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            bucket = self._token_buckets.get(config_name)
            if bucket:
                allowed, remaining, wait_time = await bucket.is_allowed(key)
                
                headers = {
                    'X-RateLimit-Limit': str(config.requests),
                    'X-RateLimit-Remaining': str(remaining)
                }
                
                if not allowed:
                    raise RateLimitExceeded(wait_time)
                
                return True, headers
        
        return True, {}
    
    def limit(
        self,
        config_name: str,
        key_func: Optional[Callable] = None
    ):
        """
        限流装饰器
        
        使用示例:
            @rate_limiter.limit("api", lambda req: req.client.host)
            async def api_endpoint(request):
                return {"data": "ok"}
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 提取key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = "global"
                
                # 检查限流
                allowed, headers = await self.check(config_name, key)
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 添加限流头
                if isinstance(result, dict) and 'headers' not in result:
                    result['headers'] = headers
                
                return result
            
            return async_wrapper
        return decorator
    
    def get_stats(self) -> Dict:
        """获取限流统计"""
        return {
            'configs': {
                name: {
                    'requests': config.requests,
                    'window': config.window_seconds,
                    'strategy': config.strategy.value
                }
                for name, config in self._configs.items()
            },
            'active_buckets': len(self._token_buckets)
        }


# 预定义的限流策略
DEFAULT_LIMITS = {
    'health_check': RateLimitConfig(
        requests=10,
        window_seconds=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ),
    'chat': RateLimitConfig(
        requests=30,
        window_seconds=60,
        strategy=RateLimitStrategy.TOKEN_BUCKET,
        burst=5
    ),
    'api_general': RateLimitConfig(
        requests=100,
        window_seconds=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    ),
    'auth': RateLimitConfig(
        requests=5,
        window_seconds=60,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )
}

# 全局限流器
rate_limiter = RateLimiter()

# 初始化默认配置
for name, config in DEFAULT_LIMITS.items():
    rate_limiter.configure(
        name=name,
        requests=config.requests,
        window_seconds=config.window_seconds,
        strategy=config.strategy,
        burst=config.burst
    )
