"""
🌸 若曦V2 - 性能监控指标
系统性能监控和指标收集
"""

import asyncio
import os
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import psutil


@dataclass
class MetricValue:
    """指标值"""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    指标收集器

    收集:
    - API响应时间
    - 请求速率
    - 错误率
    - 系统资源使用
    """

    def __init__(self, retention_minutes: int = 60):
        self._metrics: Dict[str, deque] = {}
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._retention = retention_minutes
        self._lock = asyncio.Lock()

    async def record(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """记录指标值"""
        async with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=10000)

            self._metrics[name].append(
                MetricValue(
                    timestamp=datetime.utcnow(), value=value, labels=labels or {}
                )
            )

    async def increment(self, name: str, value: int = 1):
        """增加计数器"""
        async with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    async def set_gauge(self, name: str, value: float):
        """设置仪表盘值"""
        async with self._lock:
            self._gauges[name] = value

    def timeit(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        耗时装饰器

        使用示例:
            @metrics.timeit("api_request", {"endpoint": "/chat"})
            async def handle_chat(request):
                ...
        """

        def decorator(func: Callable):
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    return await func(*args, **kwargs)
                finally:
                    elapsed = time.time() - start
                    asyncio.create_task(self.record(name, elapsed * 1000, labels))

            def sync_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.time() - start
                    asyncio.create_task(self.record(name, elapsed * 1000, labels))

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    def get_stats(self, name: str, minutes: int = 5) -> Dict:
        """获取指标统计"""
        if name not in self._metrics:
            return {}

        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        values = [m.value for m in self._metrics[name] if m.timestamp > cutoff]

        if not values:
            return {"count": 0}

        values.sort()

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": values[len(values) // 2],
            "p95": values[int(len(values) * 0.95)] if len(values) > 20 else max(values),
            "p99": (
                values[int(len(values) * 0.99)] if len(values) > 100 else max(values)
            ),
        }

    def get_all_stats(self) -> Dict:
        """获取所有指标统计"""
        return {
            "metrics": {name: self.get_stats(name) for name in self._metrics.keys()},
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }

    async def collect_system_metrics(self):
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        await self.set_gauge("system_cpu_percent", cpu_percent)

        # 内存使用
        memory = psutil.virtual_memory()
        await self.set_gauge("system_memory_percent", memory.percent)
        await self.set_gauge("system_memory_used_gb", memory.used / (1024**3))

        # 磁盘使用
        disk = psutil.disk_usage("/")
        await self.set_gauge("system_disk_percent", disk.percent)

        # 进程信息
        process = psutil.Process(os.getpid())
        await self.set_gauge("process_memory_mb", process.memory_info().rss / (1024**2))
        await self.set_gauge("process_cpu_percent", process.cpu_percent())

    async def start_monitoring(self, interval: int = 60):
        """启动系统监控循环"""
        while True:
            try:
                await self.collect_system_metrics()
            except Exception as e:
                print(f"系统监控错误: {e}")

            await asyncio.sleep(interval)


class APIMetrics:
    """API指标专用收集器"""

    def __init__(self):
        self.collector = MetricsCollector()

    async def record_request(
        self, endpoint: str, method: str, status_code: int, duration_ms: float
    ):
        """记录API请求指标"""
        labels = {"endpoint": endpoint, "method": method, "status": str(status_code)}

        # 记录响应时间
        await self.collector.record("api_response_time", duration_ms, labels)

        # 记录请求总数
        await self.collector.increment("api_requests_total", 1)

        # 记录状态码
        await self.collector.increment(f"api_status_{status_code}", 1)

    def get_api_summary(self) -> Dict:
        """获取API汇总统计"""
        response_stats = self.collector.get_stats("api_response_time", minutes=60)

        total_requests = self.collector._counters.get("api_requests_total", 0)

        # 计算错误率
        error_count = sum(
            count
            for name, count in self.collector._counters.items()
            if name.startswith("api_status_5") or name.startswith("api_status_4")
        )

        error_rate = error_count / total_requests if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "response_time": response_stats,
            "error_rate": f"{error_rate:.2%}",
            "error_count": error_count,
        }


# 全局指标收集器
metrics_collector = MetricsCollector()
api_metrics = APIMetrics()
