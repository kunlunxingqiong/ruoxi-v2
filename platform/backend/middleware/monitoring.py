"""
🌸 若曦V2 监控中间件
Prometheus指标收集与性能监控
"""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware

from core.config_manager import config
from core.log_manager import get_logger

logger = get_logger(__name__)

# 尝试导入Prometheus客户端
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("📦 prometheus-client未安装，使用简化监控")


class MetricsCollector:
    """
    指标收集器

    收集以下指标:
    - 请求总数 (按方法和路径)
    - 请求延迟 (按路径)
    - 响应状态码分布
    - 活跃请求数
    - AI调用统计
    """

    def __init__(self):
        self.enabled = config.get("monitoring.enabled", True) and PROMETHEUS_AVAILABLE

        if self.enabled:
            # HTTP请求指标
            self.http_requests_total = Counter(
                "ruoxi_http_requests_total",
                "HTTP请求总数",
                ["method", "path", "status_code"],
            )

            self.http_request_duration_seconds = Histogram(
                "ruoxi_http_request_duration_seconds",
                "HTTP请求处理时间",
                ["method", "path"],
                buckets=[
                    0.005,
                    0.01,
                    0.025,
                    0.05,
                    0.075,
                    0.1,
                    0.25,
                    0.5,
                    0.75,
                    1.0,
                    2.5,
                    5.0,
                    7.5,
                    10.0,
                    15.0,
                ],
            )

            self.http_requests_active = Gauge(
                "ruoxi_http_requests_active", "当前活跃请求数"
            )

            # AI调用指标
            self.ai_requests_total = Counter(
                "ruoxi_ai_requests_total", "AI调用总数", ["model", "provider", "status"]
            )

            self.ai_request_duration_seconds = Histogram(
                "ruoxi_ai_request_duration_seconds",
                "AI请求处理时间",
                ["model"],
                buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0, 30.0],
            )

            self.ai_tokens_total = Counter(
                "ruoxi_ai_tokens_total",
                "AI Token总数",
                ["model", "type"],  # type: input/output
            )

            # 业务指标
            self.chat_messages_total = Counter(
                "ruoxi_chat_messages_total",
                "聊天消息总数",
                ["user_type"],  # new/returning
            )

            self.memory_operations_total = Counter(
                "ruoxi_memory_operations_total",
                "记忆操作总数",
                ["operation"],  # add/search/retrieve
            )

            self.active_sessions = Gauge("ruoxi_active_sessions", "活跃会话数")

            # 系统信息
            self.app_info = Info("ruoxi_app", "应用信息")

            # 设置应用信息
            self.app_info.info(
                {
                    "version": config.get("app.version", "1.0.0"),
                    "name": config.get("app.name", "ruoxi-v2"),
                    "environment": config.get_environment(),
                }
            )

            logger.info("✅ Prometheus指标收集器初始化完成")
        else:
            # 简化版：只记录计数
            self._counters = {}
            logger.info("📊 简化监控模式")

    def record_http_request(
        self, method: str, path: str, status_code: int, duration: float
    ):
        """记录HTTP请求"""
        if self.enabled:
            self.http_requests_total.labels(
                method=method, path=path, status_code=str(status_code)
            ).inc()

            self.http_request_duration_seconds.labels(method=method, path=path).observe(
                duration
            )
        else:
            # 简化计数
            key = f"{method}_{path}_{status_code}"
            self._counters[key] = self._counters.get(key, 0) + 1

    def record_ai_request(
        self,
        model: str,
        provider: str,
        status: str,
        duration: float,
        tokens_input: int = 0,
        tokens_output: int = 0,
    ):
        """记录AI调用"""
        if self.enabled:
            self.ai_requests_total.labels(
                model=model, provider=provider, status=status
            ).inc()

            self.ai_request_duration_seconds.labels(model=model).observe(duration)

            if tokens_input:
                self.ai_tokens_total.labels(model=model, type="input").inc(tokens_input)

            if tokens_output:
                self.ai_tokens_total.labels(model=model, type="output").inc(
                    tokens_output
                )

    def inc_active_requests(self):
        """增加活跃请求计数"""
        if self.enabled:
            self.http_requests_active.inc()

    def dec_active_requests(self):
        """减少活跃请求计数"""
        if self.enabled:
            self.http_requests_active.dec()

    def get_stats(self) -> dict:
        """获取统计信息"""
        if self.enabled:
            return {"mode": "prometheus", "enabled": True}
        else:
            return {"mode": "simple", "counters": len(self._counters), "enabled": False}


# 全局指标收集器
metrics = MetricsCollector()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    监控中间件

    自动收集所有HTTP请求的指标
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并收集指标"""
        # 开始计时
        start_time = time.time()

        # 增加活跃请求
        metrics.inc_active_requests()

        try:
            # 处理请求
            response = await call_next(request)

            # 计算耗时
            duration = time.time() - start_time

            # 记录指标
            metrics.record_http_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
            )

            # 添加自定义响应头
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            return response

        except Exception as e:
            # 错误也记录
            duration = time.time() - start_time
            metrics.record_http_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration=duration,
            )
            raise

        finally:
            # 减少活跃请求
            metrics.dec_active_requests()


def get_prometheus_metrics():
    """获取Prometheus格式指标 (用于/metrics端点)"""
    if PROMETHEUS_AVAILABLE:
        from starlette.responses import Response

        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    else:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {
                "mode": "simple",
                "note": "prometheus-client未安装，使用基础监控",
                "counters": metrics._counters if hasattr(metrics, "_counters") else {},
            }
        )


# AI调用装饰器 (用于自动收集AI指标)
def ai_metrics_decorator(func):
    """
    AI函数指标装饰器

    使用方式:
    @ai_metrics_decorator
    async def generate_ai_response(...):
        ...
    """

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        model = kwargs.get("model", "unknown")
        provider = kwargs.get("provider", "unknown")

        try:
            result = await func(*args, **kwargs)

            # 记录成功指标
            metrics.record_ai_request(
                model=model,
                provider=provider,
                status="success",
                duration=time.time() - start_time,
                tokens_input=getattr(result, "tokens_input", 0),
                tokens_output=getattr(result, "tokens_output", 0),
            )

            return result

        except Exception as e:
            # 记录失败指标
            metrics.record_ai_request(
                model=model,
                provider=provider,
                status="error",
                duration=time.time() - start_time,
            )
            raise

    return wrapper


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 监控中间件")
    print("=" * 60)

    print("\n【功能】")
    print("  - HTTP请求指标 (数量/延迟/状态码)")
    print("  - AI调用指标 (模型/Token/延迟)")
    print("  - 业务指标 (聊天/记忆)")
    print("  - 系统指标 (活跃请求/会话)")

    print("\n【可用性】")
    print(f"  Prometheus: {'✅' if PROMETHEUS_AVAILABLE else '❌'}")
    print(f"  监控模式: {'完整' if metrics.enabled else '简化'}")

    print("\n【端点】")
    print("  GET /metrics - Prometheus格式指标")
    print("  响应头: X-Response-Time - 响应时间")

    print("\n【Grafana Dashboard建议】")
    print("  - 请求QPS / 延迟P99 / 错误率")
    print("  - AI调用分布 / Token消耗")
    print("  - 业务指标趋势")

    print("\n" + "=" * 60)
