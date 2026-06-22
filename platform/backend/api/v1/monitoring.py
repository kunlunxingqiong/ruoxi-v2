"""
🌸 若曦V2 - 监控API
系统监控和健康检查端点
"""

from datetime import datetime
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from core.audit.audit_logger import AuditCategory, AuditLevel, audit_logger
from core.cache.cache_manager import cache_manager
from core.monitoring.metrics import api_metrics, metrics_collector
from core.rate_limit.rate_limiter import RateLimitExceeded, rate_limiter

router = APIRouter(prefix="/monitoring", tags=["监控"])


@router.get("/health")
async def health_check():
    """
    健康检查端点

    返回系统各组件健康状态
    """
    start_time = datetime.utcnow()

    # 检查各组件
    checks = {
        "api": True,
        "cache": await cache_manager.health_check(),
        "timestamp": datetime.utcnow().isoformat(),
    }

    # 计算响应时间
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "response_time_ms": round(duration, 2),
    }


@router.get("/ready")
async def readiness_check():
    """
    就绪检查

    K8s就绪探针使用
    """
    # TODO: 检查数据库、缓存等依赖
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    存活检查

    K8s存活探针使用
    """
    return {"alive": True}


@router.get("/metrics")
async def get_metrics(current_user=Depends(get_current_user)):
    """
    获取系统指标

    包括:
    - 性能指标 (响应时间、请求速率)
    - 系统资源 (CPU、内存、磁盘)
    - 缓存统计
    - 限流统计
    """
    # 系统指标
    system_metrics = metrics_collector.get_all_stats()

    # API指标
    api_summary = api_metrics.get_api_summary()

    # 缓存统计
    cache_stats = cache_manager.get_stats()

    # 限流统计
    rate_limit_stats = rate_limiter.get_stats()

    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
        "system": system_metrics,
        "api": api_summary,
        "cache": cache_stats,
        "rate_limit": rate_limit_stats,
    }


@router.get("/metrics/cache")
async def get_cache_metrics(current_user=Depends(get_current_user)):
    """获取缓存详细指标"""
    return {"success": True, "cache": cache_manager.get_stats()}


@router.get("/metrics/api")
async def get_api_metrics(
    endpoint: Optional[str] = None,
    minutes: int = 5,
    current_user=Depends(get_current_user),
):
    """
    获取API性能指标

    Args:
        endpoint: 指定端点，None则返回所有
        minutes: 统计时间范围(分钟)
    """
    stats = api_metrics.collector.get_stats("api_response_time", minutes)

    return {
        "success": True,
        "endpoint": endpoint or "all",
        "time_range_minutes": minutes,
        "stats": stats,
    }


@router.post("/metrics/collect")
async def trigger_metrics_collection(current_user=Depends(get_current_user)):
    """手动触发系统指标收集"""
    await metrics_collector.collect_system_metrics()

    return {
        "success": True,
        "message": "指标收集完成",
        "gauges": dict(metrics_collector._gauges),
    }


@router.get("/cache/stats")
async def get_cache_stats(current_user=Depends(get_current_user)):
    """获取缓存统计"""
    return {"success": True, "stats": cache_manager.get_stats()}


@router.post("/cache/clear")
async def clear_cache(
    level: Optional[str] = None, current_user=Depends(get_current_user)
):
    """清除缓存"""
    from core.cache.cache_manager import CacheLevel

    cache_level = None
    if level:
        try:
            cache_level = CacheLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的缓存级别")

    await cache_manager.clear(cache_level)

    # 记录审计日志
    await audit_logger.log(
        level=AuditLevel.WARNING,
        category=AuditCategory.SYSTEM,
        action="cache_clear",
        user_id=current_user.user_id,
        details={"level": level or "all"},
    )

    return {"success": True, "message": f"缓存已清除 (级别: {level or 'all'})"}


@router.get("/rate-limit/stats")
async def get_rate_limit_stats(current_user=Depends(get_current_user)):
    """获取限流统计"""
    return {"success": True, "stats": rate_limiter.get_stats()}


@router.post("/rate-limit/test")
async def test_rate_limit(
    config: str = "api_general", current_user=Depends(get_current_user)
):
    """
    测试限流功能

    用于验证限流配置是否生效
    """
    try:
        allowed, headers = await rate_limiter.check(config, str(current_user.user_id))

        return {"success": True, "allowed": allowed, "headers": headers}

    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail={"error": "Rate limit exceeded", "retry_after": e.retry_after},
            headers={"Retry-After": str(e.retry_after)},
        )


@router.get("/logs/recent")
async def get_recent_logs(lines: int = 100, current_user=Depends(get_current_user)):
    """获取最近日志"""
    # 这里简化处理，实际应该从日志文件或ELK获取
    return {"success": True, "lines": lines, "note": "请使用日志聚合系统查看完整日志"}


@router.get("/system/info")
async def get_system_info(current_user=Depends(get_current_user)):
    """获取系统信息"""
    import platform
    import sys

    return {
        "success": True,
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
        },
        "app": {
            "name": "若曦V2",
            "version": "2.0.0",
            "start_time": datetime.utcnow().isoformat(),
        },
    }


@router.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    指标收集中间件

    自动记录API请求指标
    """
    start_time = datetime.utcnow()

    # 执行请求
    response = await call_next(request)

    # 计算耗时
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000

    # 记录指标
    await api_metrics.record_request(
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration,
    )

    # 添加响应头
    if isinstance(response, Response):
        response.headers["X-Response-Time-Ms"] = str(round(duration, 2))

    return response
