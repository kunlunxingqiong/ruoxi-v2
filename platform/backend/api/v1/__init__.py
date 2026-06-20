"""
🌸 若曦V2 API v1 路由集合
所有v1版本API的入口
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .chat import router as chat_router
from .chat_stream import router as chat_stream_router
from .memory import router as memory_router
from .health_records import router as health_router
from .health_analysis import router as health_analysis_router
from .emotion import router as emotion_router

# 创建v1路由器
router = APIRouter()

# 注册所有v1路由
router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(chat_router, prefix="/chat", tags=["聊天"])
router.include_router(chat_stream_router, prefix="/chat", tags=["聊天"])
router.include_router(memory_router, prefix="/memory", tags=["记忆"])
router.include_router(health_router, prefix="/health", tags=["健康记录"])
router.include_router(health_analysis_router, prefix="/health-ai", tags=["健康AI分析"])
router.include_router(emotion_router, prefix="/emotion", tags=["情感分析"])


@router.get("/")
async def v1_root():
    """v1 API根路径"""
    return {
        "version": "v1",
        "endpoints": [
            "/api/v1/auth",
            "/api/v1/chat",
            "/api/v1/memory",
            "/api/v1/health"
        ]
    }
