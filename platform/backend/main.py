"""
🌸 若曦V2 FastAPI 主入口
若曦的Web服务大脑，提供RESTful API接口
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from contextlib import asynccontextmanager

from api.health import router as health_router

# 导入API路由
from api.v1 import router as v1_router
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from middleware.monitoring import MonitoringMiddleware, get_prometheus_metrics

# 导入中间件
from middleware.rate_limit import RateLimitMiddleware
from websocket.chat_ws import websocket_endpoint

# 导入核心模块
from core.config_manager import config
from core.database_models import db
from core.exceptions import GlobalExceptionHandler, RuoxiException
from core.log_manager import get_logger

# 获取日志器
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时执行初始化，关闭时执行清理
    """
    # 启动
    logger.info("🌸 若曦V2 服务启动中...")

    # 初始化数据库
    try:
        db.create_tables()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ 数据库初始化警告: {e}")

    # 加载配置
    logger.info(
        f"📊 配置加载完成: {config.get('app.name')} v{config.get('app.version')}"
    )
    logger.info(f"🔧 环境: {config.get('app.debug') and '开发' or '生产'}")

    yield

    # 关闭
    logger.info("🌸 若曦V2 服务关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title=config.get("app.name", "若曦V2"),
    description=config.get("app.description", "AI医生朋友 - 带有记忆系统和健康提醒"),
    version=config.get("app.version", "2.0.0"),
    docs_url="/docs" if config.get("app.debug") else None,
    redoc_url="/redoc" if config.get("app.debug") else None,
    openapi_url="/openapi.json" if config.get("app.debug") else None,
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("api.cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限流中间件 (保护API)
app.add_middleware(RateLimitMiddleware)

# 监控中间件 (指标收集)
app.add_middleware(MonitoringMiddleware)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    error_response = GlobalExceptionHandler.handle_exception(exc)

    # 记录错误
    logger.error(
        f"请求异常: {request.url.path} - {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": error_response.get("error_code"),
            "error_message": error_response.get("message"),
        },
    )

    # 如果是RuoxiException，提取状态码
    status_code = 500
    if isinstance(exc, RuoxiException):
        if exc.error_code.code >= 2000 and exc.error_code.code < 3000:
            status_code = 503  # AI服务问题
        elif exc.error_code.code >= 4000:
            status_code = 503  # 数据库问题

    return JSONResponse(status_code=status_code, content=error_response)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    import time

    start_time = time.time()

    # 记录请求开始
    logger.info(
        f"📥 请求 {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )

    # 处理请求
    response = await call_next(request)

    # 计算响应时间
    process_time = (time.time() - start_time) * 1000  # 毫秒

    # 记录请求结束
    logger.info(
        f"📤 响应 {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": process_time,
        },
    )

    # 添加响应头
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    response.headers["X-Ruoxi-Version"] = config.get("app.version")

    return response


# 注册路由
app.include_router(health_router)  # 健康检查 (无版本前缀)
app.include_router(v1_router, prefix="/api/v1")  # v1 API


# Prometheus指标端点 (用于监控)
@app.get("/metrics")
async def metrics():
    """
    Prometheus监控指标

    返回格式化的监控数据，供Grafana等工具使用
    """
    return get_prometheus_metrics()


# WebSocket路由 - 实时通信
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket实时聊天端点

    支持流式AI响应和实时通知
    """
    await websocket_endpoint(websocket, session_id)


# 根路由
@app.get("/")
async def root():
    """根路由 - 服务信息"""
    return {
        "name": config.get("app.name"),
        "version": config.get("app.version"),
        "description": config.get("app.description"),
        "status": "running",
        "docs": "/docs" if config.get("app.debug") else None,
        "health": "/health",
        "websocket": "/ws/chat/{session_id}",
    }


if __name__ == "__main__":
    import uvicorn

    # 从配置获取端口
    port = config.get("api.port", 8000)
    host = "0.0.0.0" if not config.get("app.debug") else "127.0.0.1"

    print("=" * 60)
    print("🌸 若曦V2 API 服务启动")
    print("=" * 60)
    print(f"服务地址: http://{host}:{port}")
    print(f"文档地址: http://{host}:{port}/docs")
    print(f"健康检查: http://{host}:{port}/health")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=config.get("app.debug", False),
        log_level="info",
    )
