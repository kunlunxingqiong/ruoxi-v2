"""
🌸 若曦V2 - AI路由器模块

提供多模型智能路由功能:
- Fallback降级链: 优先免费模型，自动降级
- 负载均衡: 同优先级内轮询/随机
- 健康检查: 定期检测Provider可用性
- 智能路由: 根据任务类型自动选模型
- 速率限制: 跟踪每个Provider调用计数
"""

from core.ai.router.route_config import (
    # 配置
    RouteConfig,
    DEFAULT_ROUTE_CONFIG,
    # 任务类型
    TaskType,
    # Provider优先级
    ProviderPriority,
    # 模型信息
    ModelInfo,
    # 辅助函数
    get_models_for_task,
    get_all_free_models,
    get_provider_models,
    # 模型注册表
    ALL_MODELS,
    OPENROUTER_FREE_MODELS,
    GOOGLE_AI_MODELS,
    GROQ_MODELS,
    CLOUDFLARE_MODELS,
)

from core.ai.router.model_router import (
    ModelRouter,
    HealthStatus,
    get_router,
    reset_router,
)

from core.ai.router.openrouter_client import OpenRouterClient
from core.ai.router.google_ai_client import GoogleAIClient
from core.ai.router.groq_client import GroqClient


__all__ = [
    # 配置
    "RouteConfig",
    "DEFAULT_ROUTE_CONFIG",
    # 任务类型
    "TaskType",
    # Provider优先级
    "ProviderPriority",
    # 模型信息
    "ModelInfo",
    # 辅助函数
    "get_models_for_task",
    "get_all_free_models",
    "get_provider_models",
    # 模型注册表
    "ALL_MODELS",
    "OPENROUTER_FREE_MODELS",
    "GOOGLE_AI_MODELS",
    "GROQ_MODELS",
    "CLOUDFLARE_MODELS",
    # 路由器
    "ModelRouter",
    "HealthStatus",
    "get_router",
    "reset_router",
    # 客户端
    "OpenRouterClient",
    "GoogleAIClient",
    "GroqClient",
]
