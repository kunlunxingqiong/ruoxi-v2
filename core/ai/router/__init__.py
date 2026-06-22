"""
🌸 若曦V2 - AI路由器模块 (角色匹配模式 + 动态模型发现)

提供多模型智能路由功能:
- 角色匹配路由: 根据团队成员角色自动选择对应模型
- 动态模型发现: 启动时从各Provider发现400+模型
- Fallback降级链: 主力模型 → 备用模型 → 全局fallback → 动态模型池
- 负载均衡: NVIDIA双key轮询
- 健康检查: 定期检测Provider可用性
- 智能路由: 按角色或任务类型自动选模型

支持的团队成员角色:
- 🌸 若曦 (RUOXI): 总管+编程
- 🩺 阿芙 (AFU): AI医生
- 🔍 小研 (RESEARCHER): 深度调研
- 💻 小码 (CODER): 代码任务

支持的Provider (9个):
- NVIDIA NIM (117+模型)
- 硅基流动 (92+模型)
- OpenRouter (23个免费模型)
- Google AI / Gemini
- Groq
- 月之暗面 / Moonshot
- 智谱 / GLM
- 阿里百炼 (200+模型)
- Cloudflare Workers AI

更新日志:
- 2026-07-13: 新增动态模型发现，model_registry.py，4个新Provider客户端
"""

from core.ai.router.route_config import (
    # 角色枚举
    AgentRole,
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
    # 核心模型注册表
    CORE_MODELS,
    ALL_MODELS,
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

from core.ai.router.model_registry import (
    ModelRegistry,
    DiscoveredModel,
    get_registry,
    reset_registry,
)

# 客户端
from core.ai.router.openrouter_client import OpenRouterClient
from core.ai.router.google_ai_client import GoogleAIClient
from core.ai.router.groq_client import GroqClient
from core.ai.router.nvidia_client import NVIDIAClient
from core.ai.router.siliconflow_client import SiliconFlowClient
from core.ai.router.moonshot_client import MoonshotClient
from core.ai.router.zhipu_client import ZhipuClient
from core.ai.router.dashscope_client import DashscopeClient
from core.ai.router.cloudflare_client import CloudflareClient


__all__ = [
    # 角色枚举
    "AgentRole",
    # 任务类型
    "TaskType",
    # Provider优先级
    "ProviderPriority",
    # 模型信息
    "ModelInfo",
    "RoleModelConfig",
    "DiscoveredModel",
    # 辅助函数
    "get_models_for_task",
    "get_all_free_models",
    "get_provider_models",
    "get_role_config",
    "get_default_role_chain",
    # 核心模型注册表
    "CORE_MODELS",
    "ALL_MODELS",
    "ROLE_MODEL_CONFIGS",
    # 路由器
    "ModelRouter",
    "HealthStatus",
    "RouteRequest",
    "RouteResult",
    "get_router",
    "reset_router",
    # 模型注册中心
    "ModelRegistry",
    "get_registry",
    "reset_registry",
    # 客户端
    "OpenRouterClient",
    "GoogleAIClient",
    "GroqClient",
    "NVIDIAClient",
    "SiliconFlowClient",
    "MoonshotClient",
    "ZhipuClient",
    "DashscopeClient",
    "CloudflareClient",
]
