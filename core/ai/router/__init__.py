"""
🌸 若曦V2 - AI路由器模块 (角色匹配模式)

提供多模型智能路由功能:
- 角色匹配路由: 根据团队成员角色自动选择对应模型
- Fallback降级链: 主力模型 → 备用模型 → 全局fallback
- 负载均衡: NVIDIA双key轮询
- 健康检查: 定期检测Provider可用性
- 智能路由: 按角色或任务类型自动选模型
- 速率限制: 跟踪每个Provider调用计数

支持的团队成员角色:
- 🌸 若曦 (RUOXI): 总管+编程
- 🩺 阿芙 (AFU): AI医生
- 🔍 小研 (RESEARCHER): 深度调研
- 💻 小码 (CODER): 代码任务

更新日志:
- 2026-07-13: 角色匹配模式，NVIDIA NIM和硅基流动支持
"""

from core.ai.router.route_config import (
    # 角色枚举 (新增)
    AgentRole,
    # 配置
    RouteConfig,
    DEFAULT_ROUTE_CONFIG,
    # 任务类型
    TaskType,
    # Provider优先级
    ProviderPriority,
    # 模型信息
    ModelInfo,
    RoleModelConfig,
    # 辅助函数
    get_models_for_task,
    get_all_free_models,
    get_provider_models,
    get_role_config,
    get_default_role_chain,
    # 模型注册表
    ALL_MODELS,
    NVIDIA_MODELS,
    SILICONFLOW_MODELS,
    OPENROUTER_FREE_MODELS,
    GOOGLE_AI_MODELS,
    GROQ_MODELS,
    ROLE_MODEL_CONFIGS,
)

from core.ai.router.model_router import (
    ModelRouter,
    HealthStatus,
    RouteRequest,
    RouteResult,
    get_router,
    reset_router,
)

# 客户端 (新增NVIDIA和硅基流动)
from core.ai.router.openrouter_client import OpenRouterClient
from core.ai.router.google_ai_client import GoogleAIClient
from core.ai.router.groq_client import GroqClient
from core.ai.router.nvidia_client import NVIDIAClient
from core.ai.router.siliconflow_client import SiliconFlowClient


__all__ = [
    # 角色枚举 (新增)
    "AgentRole",
    # 配置
    "RouteConfig",
    "DEFAULT_ROUTE_CONFIG",
    # 任务类型
    "TaskType",
    # Provider优先级
    "ProviderPriority",
    # 模型信息
    "ModelInfo",
    "RoleModelConfig",
    # 辅助函数
    "get_models_for_task",
    "get_all_free_models",
    "get_provider_models",
    "get_role_config",
    "get_default_role_chain",
    # 模型注册表
    "ALL_MODELS",
    "NVIDIA_MODELS",
    "SILICONFLOW_MODELS",
    "OPENROUTER_FREE_MODELS",
    "GOOGLE_AI_MODELS",
    "GROQ_MODELS",
    "ROLE_MODEL_CONFIGS",
    # 路由器
    "ModelRouter",
    "HealthStatus",
    "RouteRequest",
    "RouteResult",
    "get_router",
    "reset_router",
    # 客户端
    "OpenRouterClient",
    "GoogleAIClient",
    "GroqClient",
    "NVIDIAClient",      # 新增
    "SiliconFlowClient", # 新增
]
