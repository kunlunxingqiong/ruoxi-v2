"""
🌸 若曦V2 - AI路由器模块 (角色匹配模式 + 动态模型发现)

支持9个Provider、400+模型、4个团队成员角色路由
"""

from core.ai.router.route_config import (
    AgentRole,
    ROLE_DEFAULT_MODELS,
    ROLE_FALLBACK_CHAINS,
    PROVIDER_CONFIGS,
    get_role_model,
    get_role_fallback_chain,
)

from core.ai.router.model_registry import (
    ModelRegistry,
    DiscoveredModel,
    model_registry,
)

__all__ = [
    "AgentRole",
    "ROLE_DEFAULT_MODELS",
    "ROLE_FALLBACK_CHAINS",
    "PROVIDER_CONFIGS",
    "get_role_model",
    "get_role_fallback_chain",
    "ModelRegistry",
    "DiscoveredModel",
    "model_registry",
]
