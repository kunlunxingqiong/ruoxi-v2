"""
🌸 若曦V2 缓存管理器
多级缓存策略：内存 + Redis + 磁盘
"""
import hashlib
import json
import pickle
import asyncio
from typing import Any, Optional, Dict, List, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
import time

try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from core.config_manager import config
from core.log_manager import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 3600  # 默认1小时
    max_size: int = 1000  # 最大条目数
    namespace: str = "ruoxi"


class MemoryCache:
    """
    内存缓存 (LRU策略)
    
    特点:
    - 本地内存存储
    - 自动过期
    - 线程/协程安全
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            item = self._cache.get(key)
            
            if item is None:
                self._misses += 1
                return None
            
            # 检查过期
            if datetime.utcnow() > item['expires_at']:
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return item['value']
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ):
        """设置缓存值"""
        async with self._lock:
            # 检查容量
            if len(self._cache) >= self._max_size and key not in self._cache:
                # LRU淘汰
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k]['accessed_at']
                )
                del self._cache[oldest_key]
            
            now = datetime.utcnow()
            self._cache[key] = {
                'value': value,
                'expires_at': now + timedelta(seconds=ttl),
                'created_at': now,
                'accessed_at': now
            }
    
    async def delete(self, key: str):
        """删除缓存"""
        async with self._lock:
            self._cache.pop(key, None)
    
    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2)
        }


class RedisCache:
    """
    Redis缓存
    
    特点:
    - 分布式缓存
    - 持久化
    - 高性能
    """
    
    def __init__(self):
        self._client = None
        self._available = False
        self._namespace = config.get("cache.redis_namespace", "ruoxi")
        
        if REDIS_AVAILABLE:
            try:
                self._init_client()
            except Exception as e:
                logger.warning(f"⚠️ Redis初始化失败: {e}")
        else:
            logger.info("📦 redis未安装，使用内存缓存")
    
    def _init_client(self):
        """初始化Redis客户端"""
        redis_url = config.get("cache.redis_url", "redis://localhost:6379/0")
        # 异步初始化在调用时
        self._available = True
    
    def _get_key(self, key: str) -> str:
        """添加命名空间"""
        return f"{self._namespace}:{key}"
    
    async def _get_client(self):
        """获取Redis连接"""
        if not self._available:
            return None
        
        if self._client is None:
            try:
                redis_url = config.get("cache.redis_url", "redis://localhost:6379/0")
                self._client = await aioredis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.error(f"🔴 Redis连接失败: {e}")
                return None
        
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        client = await self._get_client()
        if not client:
            return None
        
        try:
            data = await client.get(self._get_key(key))
            if data:
                return pickle.loads(data.encode())
            return None
        except Exception as e:
            logger.warning(f"⚠️ Redis get失败: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ):
        """设置缓存"""
        client = await self._get_client()
        if not client:
            return
        
        try:
            serialized = pickle.dumps(value)
            await client.setex(
                self._get_key(key),
                ttl,
                serialized
            )
        except Exception as e:
            logger.warning(f"⚠️ Redis set失败: {e}")
    
    async def delete(self, key: str):
        """删除缓存"""
        client = await self._get_client()
        if not client:
            return
        
        try:
            await client.delete(self._get_key(key))
        except Exception as e:
            logger.warning(f"⚠️ Redis delete失败: {e}")
    
    async def clear(self):
        """清空缓存 (慎用)"""
        client = await self._get_client()
        if not client:
            return
        
        try:
            # 只清空命名空间内的键
            pattern = f"{self._namespace}:*"
            async for key in client.scan_iter(match=pattern):
                await client.delete(key)
        except Exception as e:
            logger.warning(f"⚠️ Redis clear失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "available": self._available,
            "namespace": self._namespace
        }


class CacheManager:
    """
    缓存管理器
    
    多级缓存策略:
    1. L1: 内存缓存 (最快)
    2. L2: Redis缓存 (分布式)
    3. L3: 磁盘缓存 (持久化)
    
    读取顺序: L1 → L2 → L3 → 数据源
    写入顺序: 数据源 → L1 + L2 + L3 (异步)
    """
    
    def __init__(self):
        self.l1_cache = MemoryCache(max_size=1000)  # 内存
        self.l2_cache = RedisCache()  # Redis
        
        # 磁盘缓存目录
        self._disk_cache_dir = Path(
            config.get("system.data_dir", "data")
        ) / "cache"
        self._disk_cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "disk_hits": 0,
            "misses": 0
        }
        
        logger.info("✅ 缓存管理器初始化完成 (L1内存 + L2Redis)")
    
    def _get_disk_path(self, key: str) -> Path:
        """获取磁盘缓存路径"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self._disk_cache_dir / f"{safe_key}.cache"
    
    def _get_disk(self, key: str) -> Optional[Any]:
        """从磁盘获取缓存"""
        path = self._get_disk_path(key)
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                    
                    # 检查过期
                    if datetime.utcnow() < data['expires_at']:
                        return data['value']
                    else:
                        path.unlink()  # 删除过期文件
            except Exception:
                pass
        return None
    
    def _set_disk(self, key: str, value: Any, ttl: int):
        """写入磁盘缓存"""
        path = self._get_disk_path(key)
        try:
            data = {
                'value': value,
                'expires_at': datetime.utcnow() + timedelta(seconds=ttl),
                'created_at': datetime.utcnow()
            }
            with open(path, 'wb') as f:
                pickle.dump(data, f)
        except Exception:
            pass
    
    async def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取缓存值
        
        多级缓存读取顺序:
        1. 内存缓存 (L1)
        2. Redis缓存 (L2)
        3. 磁盘缓存 (L3)
        """
        # L1: 内存
        value = await self.l1_cache.get(key)
        if value is not None:
            self._stats["l1_hits"] += 1
            return value
        
        # L2: Redis
        value = await self.l2_cache.get(key)
        if value is not None:
            self._stats["l2_hits"] += 1
            # 回填L1
            await self.l1_cache.set(key, value)
            return value
        
        # L3: 磁盘
        value = self._get_disk(key)
        if value is not None:
            self._stats["disk_hits"] += 1
            # 回填L1和L2
            await self.l1_cache.set(key, value)
            await self.l2_cache.set(key, value)
            return value
        
        self._stats["misses"] += 1
        return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        levels: List[int] = None
    ):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
            levels: 写入哪些级别 [1, 2, 3] 默认全部
        """
        levels = levels or [1, 2, 3]
        
        # L1: 内存
        if 1 in levels:
            await self.l1_cache.set(key, value, ttl)
        
        # L2: Redis (异步)
        if 2 in levels:
            asyncio.create_task(self.l2_cache.set(key, value, ttl))
        
        # L3: 磁盘 (异步)
        if 3 in levels:
            asyncio.create_task(
                asyncio.to_thread(self._set_disk, key, value, ttl)
            )
    
    async def delete(self, key: str):
        """删除所有级别的缓存"""
        await self.l1_cache.delete(key)
        await self.l2_cache.delete(key)
        
        # 磁盘
        path = self._get_disk_path(key)
        if path.exists():
            path.unlink()
    
    async def clear(self):
        """清空所有缓存"""
        await self.l1_cache.clear()
        await self.l2_cache.clear()
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total_hits = sum([
            self._stats["l1_hits"],
            self._stats["l2_hits"],
            self._stats["disk_hits"]
        ])
        total = total_hits + self._stats["misses"]
        
        return {
            **self._stats,
            "l1_stats": self.l1_cache.get_stats(),
            "l2_stats": self.l2_cache.get_stats(),
            "total_hits": total_hits,
            "total_requests": total,
            "hit_rate": round(total_hits / total, 2) if total > 0 else 0
        }


# 全局缓存管理器实例
cache_manager = CacheManager()


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    key_builder: Callable = None
):
    """
    缓存装饰器
    
    使用方式:
    @cached(ttl=3600, key_prefix="user")
    async def get_user(user_id: str) -> User:
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认键格式: prefix:func_name:args_hash
                args_str = str(args) + str(sorted(kwargs.items()))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:16]
                cache_key = f"{key_prefix}:{func.__name__}:{args_hash}"
            
            # 尝试获取缓存
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 写入缓存
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def ai_response_cached(ttl: int = 300):
    """AI响应专用缓存装饰器 (短时间缓存)"""
    return cached(
        ttl=ttl,
        key_prefix="ai",
        key_builder=lambda *args, **kwargs: f"ai:{hashlib.sha256(str(args).encode()).hexdigest()[:32]}"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 缓存管理器")
    print("=" * 60)
    
    print("\n【多级缓存】")
    print("  L1: 内存缓存 (LRU, 最快)")
    print("  L2: Redis缓存 (分布式)")
    print("  L3: 磁盘缓存 (持久化)")
    
    print("\n【使用示例】")
    print("  @cached(ttl=3600)")
    print("  async def expensive_function(x):")
    print("      return x * 2")
    
    print("\n【统计】")
    print(f"  {cache_manager.get_stats()}")
    
    print("\n" + "=" * 60)
    print("✅ 缓存管理器就绪")
    print("=" * 60)
