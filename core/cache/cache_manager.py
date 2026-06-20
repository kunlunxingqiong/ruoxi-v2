"""
🌸 若曦V2 - 缓存管理器
多层缓存策略，提升系统性能
"""
from typing import Optional, Any, Dict, List, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from functools import wraps
import asyncio


class CacheLevel(Enum):
    """缓存层级"""
    MEMORY = "memory"      # 进程内存 (最快)
    REDIS = "redis"        # Redis (分布式)
    DISK = "disk"          # 本地磁盘 (持久化)


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"            # 最近最少使用
    TTL = "ttl"            # 过期时间
    LFU = "lfu"            # 最不经常使用


@dataclass
class CacheConfig:
    """缓存配置"""
    level: CacheLevel
    ttl_seconds: int = 300
    max_size: int = 1000
    strategy: CacheStrategy = CacheStrategy.TTL


class MemoryCache:
    """进程内存缓存"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict] = {}
        self._max_size = max_size
        self._access_count: Dict[str, int] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # 检查过期
        if entry.get('expires_at'):
            if datetime.utcnow() > entry['expires_at']:
                del self._cache[key]
                return None
        
        # 更新访问计数
        self._access_count[key] = self._access_count.get(key, 0) + 1
        
        return entry['value']
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """设置缓存值"""
        # 检查容量，LRU淘汰
        if len(self._cache) >= self._max_size and key not in self._cache:
            # 找到最少访问的key
            if self._access_count:
                lru_key = min(self._access_count, key=self._access_count.get)
                del self._cache[lru_key]
                del self._access_count[lru_key]
        
        expires_at = None
        if ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
        
        self._access_count[key] = self._access_count.get(key, 0) + 1
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_count:
                del self._access_count[key]
            return True
        return False
    
    async def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_count.clear()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = len(self._cache)
        expired = sum(
            1 for entry in self._cache.values()
            if entry.get('expires_at') and datetime.utcnow() > entry['expires_at']
        )
        
        return {
            'total_keys': total,
            'expired_keys': expired,
            'active_keys': total - expired,
            'max_size': self._max_size,
            'hit_rate': 'N/A'  # 需要外部统计
        }


class CacheManager:
    """
    缓存管理器
    
    功能:
    - 多层缓存 (Memory -> Redis)
    - 自动缓存装饰器
    - 缓存预热
    - 统计监控
    """
    
    def __init__(self):
        self._memory = MemoryCache(max_size=1000)
        self._redis = None  # 初始化时连接
        self._stats = {
            'hits': 0,
            'misses': 0
        }
    
    async def initialize(self, redis_url: Optional[str] = None):
        """初始化Redis连接"""
        if redis_url:
            try:
                import aioredis
                self._redis = await aioredis.from_url(redis_url)
            except Exception as e:
                print(f"Redis连接失败: {e}，将使用内存缓存")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存key"""
        key_data = f"{prefix}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(
        self,
        key: str,
        level: CacheLevel = CacheLevel.MEMORY
    ) -> Optional[Any]:
        """
        获取缓存
        
        策略: 先查内存，再查Redis
        """
        value = await self._memory.get(key)
        
        if value is not None:
            self._stats['hits'] += 1
            return value
        
        # 查Redis
        if self._redis and level in [CacheLevel.REDIS, CacheLevel.MEMORY]:
            try:
                raw = await self._redis.get(key)
                if raw:
                    value = json.loads(raw)
                    # 回填内存缓存
                    await self._memory.set(key, value)
                    self._stats['hits'] += 1
                    return value
            except Exception as e:
                print(f"Redis查询失败: {e}")
        
        self._stats['misses'] += 1
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        level: CacheLevel = CacheLevel.MEMORY
    ):
        """设置缓存"""
        # 内存缓存
        await self._memory.set(key, value, ttl)
        
        # Redis缓存
        if self._redis and level in [CacheLevel.REDIS, CacheLevel.MEMORY]:
            try:
                await self._redis.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
            except Exception as e:
                print(f"Redis设置失败: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        await self._memory.delete(key)
        
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass
    
    async def clear(self, level: Optional[CacheLevel] = None):
        """清空缓存"""
        if level is None or level == CacheLevel.MEMORY:
            await self._memory.clear()
        
        if self._redis and (level is None or level == CacheLevel.REDIS):
            try:
                await self._redis.flushdb()
            except Exception:
                pass
    
    def cached(
        self,
        ttl: int = 300,
        key_prefix: str = "",
        level: CacheLevel = CacheLevel.MEMORY
    ):
        """
        缓存装饰器
        
        使用示例:
            @cache_manager.cached(ttl=60, key_prefix="user")
            async def get_user(user_id: str):
                return await db.get_user(user_id)
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存key
                cache_key = self._generate_key(
                    key_prefix or func.__name__,
                    *args,
                    **kwargs
                )
                
                # 尝试获取缓存
                cached = await self.get(cache_key, level)
                if cached is not None:
                    return cached
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 设置缓存
                await self.set(cache_key, result, ttl, level)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 同步函数不缓存，直接执行
                return func(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    async def warm_up(self, data: Dict[str, Any], ttl: int = 3600):
        """
        缓存预热
        
        启动时预加载热点数据
        """
        for key, value in data.items():
            await self.set(key, value, ttl)
        
        print(f"🌸 缓存预热完成: {len(data)} 条数据")
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total if total > 0 else 0
        
        return {
            'memory': self._memory.get_stats(),
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': f"{hit_rate:.2%}",
            'redis_connected': self._redis is not None
        }
    
    async def health_check(self) -> bool:
        """缓存健康检查"""
        try:
            test_key = "health_check"
            await self.set(test_key, "ok", 10)
            value = await self.get(test_key)
            return value == "ok"
        except Exception:
            return False


# 全局缓存管理器
cache_manager = CacheManager()
