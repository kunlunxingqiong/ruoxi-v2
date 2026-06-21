"""
🌸 若曦V2 - 路由配置模块

定义模型路由策略、任务类型映射、团队成员角色配置和免费额度跟踪

更新日志:
- 2026-07-13: 添加 AgentRole 枚举、角色模型匹配配置、NVIDIA/硅基流动模型注册表
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


class TaskType(Enum):
    """任务类型枚举"""
    GENERAL = "general"           # 通用对话
    CODING = "coding"             # 代码生成/分析
    REASONING = "reasoning"       # 推理/分析
    LONG_TEXT = "long_text"       # 长文本处理
    FAST_RESPONSE = "fast_response"  # 快速响应
    VISION = "vision"             # 视觉理解
    CREATIVE = "creative"         # 创意写作


class AgentRole(Enum):
    """
    团队成员角色枚举
    
    用于角色匹配路由，每个角色绑定主力模型和备用模型
    """
    RUOXI = "ruoxi"       # 🌸 若曦 - 总管+编程 (NVIDIA deepseek-v4-pro / 硅基流动 deepseek-v3)
    AFU = "afu"           # 🩺 阿芙 - AI医生 (智谱 GLM-4 / NVIDIA qwen)
    RESEARCHER = "researcher"  # 🔍 小研 - 深度调研 (月之暗面 moonshot-v1-128k / NVIDIA deepseek-v4-pro)
    CODER = "coder"       # 💻 小码 - 代码任务 (NVIDIA deepseek-coder / 硅基流动 qwen-coder)


class ProviderPriority(Enum):
    """Provider优先级（数值越小优先级越高）"""
    # 企业级/强力模型 - 最高优先级
    NVIDIA = 1       # NVIDIA NIM (117+模型，企业级推理)
    SILICONFLOW = 2  # 硅基流动 (92+模型，深度推理)
    
    # 免费模型
    OPENROUTER = 10      # 23个免费模型
    GOOGLE_AI = 11       # Gemini系列
    GROQ = 12            # 超快免费推理
    CLOUDFLARE = 13      # Workers AI
    
    # 付费备用
    ZHIPU = 20           # 智谱 GLM
    MOONSHOT = 21       # 月之暗面
    DASHSCOPE = 22      # 阿里百炼
    DEEPSEEK = 23       # DeepSeek 官方


@dataclass
class ModelInfo:
    """模型信息"""
    model_id: str                          # 模型标识符
    provider: ProviderPriority              # 提供商优先级
    provider_name: str                     # 提供商名称
    task_types: Set[TaskType]              # 支持的任务类型
    is_free: bool = True                   # 是否免费
    max_tokens: int = 8192                 # 最大输出token
    context_window: int = 128000           # 上下文窗口
    supports_streaming: bool = True        # 支持流式输出
    supports_vision: bool = False          # 支持视觉
    daily_limit: Optional[int] = None       # 每日调用限制
    rate_limit_rpm: int = 60               # 每分钟请求限制
    description: str = ""                   # 模型描述


@dataclass
class RoleModelConfig:
    """角色模型配置"""
    role: AgentRole
    display_name: str                      # 显示名称 (如 "🌸 若曦")
    primary_provider: ProviderPriority      # 主力提供商
    primary_model: str                      # 主力模型ID
    fallback_provider: ProviderPriority      # 备用提供商
    fallback_model: str                    # 备用模型ID
    global_fallback_provider: ProviderPriority  # 全局降级提供商
    global_fallback_model: str             # 全局降级模型
    description: str = ""                   # 角色描述
    optimized_for: Set[TaskType] = field(default_factory=TaskType)  # 优化任务类型


# ============================================================================
# 角色模型配置表 - 团队成员与模型匹配
# ============================================================================

ROLE_MODEL_CONFIGS: Dict[AgentRole, RoleModelConfig] = {
    AgentRole.RUOXI: RoleModelConfig(
        role=AgentRole.RUOXI,
        display_name="🌸 若曦",
        primary_provider=ProviderPriority.NVIDIA,
        primary_model="deepseek-ai/deepseek-v4-pro",
        fallback_provider=ProviderPriority.SILICONFLOW,
        fallback_model="deepseek-ai/DeepSeek-V3",
        global_fallback_provider=ProviderPriority.OPENROUTER,
        global_fallback_model="deepseek/deepseek-v4-flash:free",
        description="总管+编程，推理强+编程好",
        optimized_for={TaskType.GENERAL, TaskType.CODING, TaskType.REASONING}
    ),
    AgentRole.AFU: RoleModelConfig(
        role=AgentRole.AFU,
        display_name="🩺 阿芙",
        primary_provider=ProviderPriority.ZHIPU,
        primary_model="glm-4-flash",
        fallback_provider=ProviderPriority.NVIDIA,
        fallback_model="qwen/qwen3-72b-instruct",
        global_fallback_provider=ProviderPriority.GOOGLE_AI,
        global_fallback_model="gemini-2.0-flash-exp",
        description="AI医生，中文医疗优秀",
        optimized_for={TaskType.GENERAL, TaskType.REASONING, TaskType.MEDICAL}
    ),
    AgentRole.RESEARCHER: RoleModelConfig(
        role=AgentRole.RESEARCHER,
        display_name="🔍 小研",
        primary_provider=ProviderPriority.MOONSHOT,
        primary_model="moonshot-v1-128k",
        fallback_provider=ProviderPriority.NVIDIA,
        fallback_model="deepseek-ai/deepseek-v4-pro",
        global_fallback_provider=ProviderPriority.OPENROUTER,
        global_fallback_model="moonshotai/kimi-k2.6:free",
        description="深度调研，128K长文本",
        optimized_for={TaskType.LONG_TEXT, TaskType.GENERAL, TaskType.REASONING}
    ),
    AgentRole.CODER: RoleModelConfig(
        role=AgentRole.CODER,
        display_name="💻 小码",
        primary_provider=ProviderPriority.NVIDIA,
        primary_model="deepseek-ai/deepseek-coder-v2",
        fallback_provider=ProviderPriority.SILICONFLOW,
        fallback_model="Qwen/Qwen2.5-Coder-32B-Instruct",
        global_fallback_provider=ProviderPriority.OPENROUTER,
        global_fallback_model="qwen/qwen3-coder:free",
        description="代码任务，代码专用模型",
        optimized_for={TaskType.CODING, TaskType.GENERAL}
    ),
}


# ============================================================================
# NVIDIA NIM 模型注册表 (117+模型)
# ============================================================================

NVIDIA_MODELS: Dict[str, ModelInfo] = {
    # 深度推理系列
    "deepseek-ai/deepseek-v4-pro": ModelInfo(
        model_id="deepseek-ai/deepseek-v4-pro",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.CODING},
        is_free=False,
        max_tokens=8192,
        context_window=64000,
        rate_limit_rpm=40,  # NVIDIA限制约40 req/min per key
        description="DeepSeek V4 Pro - 企业级深度推理"
    ),
    "deepseek-ai/deepseek-r1": ModelInfo(
        model_id="deepseek-ai/deepseek-r1",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.REASONING, TaskType.GENERAL},
        is_free=False,
        max_tokens=8192,
        context_window=64000,
        rate_limit_rpm=40,
        description="DeepSeek R1 - 深度推理模型"
    ),
    "deepseek-ai/deepseek-coder-v2": ModelInfo(
        model_id="deepseek-ai/deepseek-coder-v2",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.CODING, TaskType.GENERAL},
        is_free=False,
        max_tokens=8192,
        context_window=56000,
        rate_limit_rpm=40,
        description="DeepSeek Coder V2 - 专业代码模型"
    ),
    # Qwen系列
    "qwen/qwen3-next-80b-a3b-instruct": ModelInfo(
        model_id="qwen/qwen3-next-80b-a3b-instruct",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.CODING},
        is_free=False,
        max_tokens=4096,
        context_window=32000,
        rate_limit_rpm=40,
        description="Qwen3 80B A3B - 阿里通义千问"
    ),
    "qwen/qwen3-72b-instruct": ModelInfo(
        model_id="qwen/qwen3-72b-instruct",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.CODING},
        is_free=False,
        max_tokens=4096,
        context_window=32000,
        rate_limit_rpm=40,
        description="Qwen3 72B - 通义千问"
    ),
    "qwen/qwen3-coder": ModelInfo(
        model_id="qwen/qwen3-coder",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.CODING, TaskType.GENERAL},
        is_free=False,
        max_tokens=4096,
        context_window=32000,
        rate_limit_rpm=40,
        description="Qwen3 Coder - 编程专用"
    ),
    # NVIDIA 自有模型
    "nvidia/llama-3.3-nv-70b-instruct": ModelInfo(
        model_id="nvidia/llama-3.3-nv-70b-instruct",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.GENERAL, TaskType.REASONING},
        is_free=False,
        max_tokens=4096,
        context_window=128000,
        rate_limit_rpm=40,
        description="Llama 3.3 70B NV - NVIDIA优化版"
    ),
    "nvidia/nemotron-4-340b-instruct": ModelInfo(
        model_id="nvidia/nemotron-4-340b-instruct",
        provider=ProviderPriority.NVIDIA,
        provider_name="NVIDIA NIM",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.CODING},
        is_free=False,
        max_tokens=4096,
        context_window=4096,
        rate_limit_rpm=40,
        description="Nemotron 4 340B - NVIDIA大模型"
    ),
}


# ============================================================================
# 硅基流动模型注册表 (92+模型)
# ============================================================================

SILICONFLOW_MODELS: Dict[str, ModelInfo] = {
    # DeepSeek系列
    "deepseek-ai/DeepSeek-V3": ModelInfo(
        model_id="deepseek-ai/DeepSeek-V3",
        provider=ProviderPriority.SILICONFLOW,
        provider_name="硅基流动",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.CODING},
        is_free=False,
        max_tokens=4096,
        context_window=64000,
        rate_limit_rpm=120,
        description="DeepSeek V3 - 深度推理"
    ),
    "deepseek-ai/DeepSeek-R1": ModelInfo(
        model_id="deepseek-ai/DeepSeek-R1",
        provider=ProviderPriority.SILICONFLOW,
        provider_name="硅基流动",
        task_types={TaskType.REASONING, TaskType.GENERAL},
        is_free=False,
        max_tokens=4096,
        context_window=64000,
        rate_limit_rpm=120,
        description="DeepSeek R1 - 推理模型"
    ),
    # Qwen Coder系列
    "Qwen/Qwen2.5-Coder-32B-Instruct": ModelInfo(
        model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
        provider=ProviderPriority.SILICONFLOW,
        provider_name="硅基流动",
        task_types={TaskType.CODING, TaskType.GENERAL},
        is_free=False,
        max_tokens=4096,
        context_window=32000,
        rate_limit_rpm=120,
        description="Qwen2.5 Coder 32B - 编程专用"
    ),
    "Qwen/Qwen2.5-Coder-7B-Instruct": ModelInfo(
        model_id="Qwen/Qwen2.5-Coder-7B-Instruct",
        provider=ProviderPriority.SILICONFLOW,
        provider_name="硅基流动",
        task_types={TaskType.CODING, TaskType.GENERAL},
        is_free=False,
        max_tokens=2048,
        context_window=16000,
        rate_limit_rpm=120,
        description="Qwen2.5 Coder 7B - 轻量编程"
    ),
    # GLM系列
    "ZhipuAI/glm-4-flash": ModelInfo(
        model_id="ZhipuAI/glm-4-flash",
        provider=ProviderPriority.SILICONFLOW,
        provider_name="硅基流动",
        task_types={TaskType.GENERAL, TaskType.REASONING},
        is_free=False,
        max_tokens=4096,
        context_window=128000,
        rate_limit_rpm=120,
        description="GLM-4 Flash - 智谱快速版"
    ),
    "ZhipuAI/glm-4": ModelInfo(
        model_id="ZhipuAI/glm-4",
        provider=ProviderPriority.SILICONFLOW,
        provider_name="硅基流动",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.CODING},
        is_free=False,
        max_tokens=4096,
        context_window=128000,
        rate_limit_rpm=120,
        description="GLM-4 - 智谱完整版"
    ),
}


# ============================================================================
# 兼容旧版本的模型注册表
# ============================================================================

# OpenRouter 免费模型列表
OPENROUTER_FREE_MODELS: Dict[str, ModelInfo] = {
    "deepseek/deepseek-v4-flash:free": ModelInfo(
        model_id="deepseek/deepseek-v4-flash:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.CODING, TaskType.REASONING},
        is_free=True,
        max_tokens=8192,
        context_window=64000,
        daily_limit=500,
        description="DeepSeek V4 Flash 免费版"
    ),
    "moonshotai/kimi-k2.6:free": ModelInfo(
        model_id="moonshotai/kimi-k2.6:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.LONG_TEXT, TaskType.CODING},
        is_free=True,
        max_tokens=8192,
        context_window=128000,
        daily_limit=100,
        description="Kimi K2.6 免费版"
    ),
    "qwen/qwen3-next-80b-a3b-instruct:free": ModelInfo(
        model_id="qwen/qwen3-next-80b-a3b-instruct:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.CODING},
        is_free=True,
        max_tokens=4096,
        context_window=32000,
        daily_limit=50,
        description="Qwen3 80B 免费版"
    ),
    "qwen/qwen3-coder:free": ModelInfo(
        model_id="qwen/qwen3-coder:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.CODING, TaskType.GENERAL},
        is_free=True,
        max_tokens=4096,
        context_window=32000,
        daily_limit=100,
        description="Qwen3 Coder 免费版"
    ),
    "meta-llama/llama-3.3-70b-instruct:free": ModelInfo(
        model_id="meta-llama/llama-3.3-70b-instruct:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.CODING, TaskType.REASONING},
        is_free=True,
        max_tokens=4096,
        context_window=128000,
        daily_limit=100,
        description="Llama 3.3 70B 免费版"
    ),
    "nvidia/nemotron-3-super-120b-a12b:free": ModelInfo(
        model_id="nvidia/nemotron-3-super-120b-a12b:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.REASONING},
        is_free=True,
        max_tokens=4096,
        context_window=128000,
        daily_limit=50,
        description="NVIDIA Nemotron 120B 免费版"
    ),
}

# Google AI Studio 模型
GOOGLE_AI_MODELS: Dict[str, ModelInfo] = {
    "gemini-2.0-flash-exp": ModelInfo(
        model_id="gemini-2.0-flash-exp",
        provider=ProviderPriority.GOOGLE_AI,
        provider_name="Google AI Studio",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE, TaskType.CODING, TaskType.VISION},
        is_free=True,
        max_tokens=8192,
        context_window=1000000,
        supports_vision=True,
        daily_limit=1500,
        rate_limit_rpm=1000,
        description="Gemini 2.0 Flash 实验版"
    ),
    "gemini-1.5-flash-8b": ModelInfo(
        model_id="gemini-1.5-flash-8b",
        provider=ProviderPriority.GOOGLE_AI,
        provider_name="Google AI Studio",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE, TaskType.VISION},
        is_free=True,
        max_tokens=8192,
        context_window=128000,
        supports_vision=True,
        daily_limit=1500,
        rate_limit_rpm=1000,
        description="Gemini 1.5 Flash 8B"
    ),
}

# Groq 模型
GROQ_MODELS: Dict[str, ModelInfo] = {
    "llama-3.3-70b-specdec": ModelInfo(
        model_id="llama-3.3-70b-specdec",
        provider=ProviderPriority.GROQ,
        provider_name="Groq",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE, TaskType.CODING},
        is_free=True,
        max_tokens=8192,
        context_window=8192,
        rate_limit_rpm=30,
        description="Groq Llama 3.3 70B 极速版"
    ),
    "mixtral-8x7b-32768": ModelInfo(
        model_id="mixtral-8x7b-32768",
        provider=ProviderPriority.GROQ,
        provider_name="Groq",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=32768,
        context_window=32768,
        rate_limit_rpm=30,
        description="Groq Mixtral 8x7B"
    ),
}


# ============================================================================
# 合并所有模型注册表
# ============================================================================

ALL_MODELS: Dict[str, ModelInfo] = {}
ALL_MODELS.update(NVIDIA_MODELS)
ALL_MODELS.update(SILICONFLOW_MODELS)
ALL_MODELS.update(OPENROUTER_FREE_MODELS)
ALL_MODELS.update(GOOGLE_AI_MODELS)
ALL_MODELS.update(GROQ_MODELS)


# ============================================================================
# 辅助函数
# ============================================================================

def get_models_for_task(task_type: TaskType) -> List[str]:
    """
    获取支持特定任务类型的模型列表
    
    Args:
        task_type: 任务类型
        
    Returns:
        模型ID列表，按优先级排序
    """
    models = []
    for model_id, info in ALL_MODELS.items():
        if task_type in info.task_types:
            models.append(model_id)
    return models


def get_all_free_models() -> List[str]:
    """获取所有免费模型"""
    return [m for m, info in ALL_MODELS.items() if info.is_free]


def get_provider_models(provider: ProviderPriority) -> List[str]:
    """
    获取指定Provider的所有模型
    
    Args:
        provider: Provider优先级枚举
        
    Returns:
        模型ID列表
    """
    return [m for m, info in ALL_MODELS.items() if info.provider == provider]


def get_role_config(role: AgentRole) -> RoleModelConfig:
    """
    获取角色模型配置
    
    Args:
        role: 角色枚举
        
    Returns:
        角色模型配置
    """
    return ROLE_MODEL_CONFIGS.get(role)


def get_default_role_chain(role: AgentRole) -> List[tuple]:
    """
    获取角色的完整降级链
    
    Args:
        role: 角色枚举
        
    Returns:
        [(provider, model_id), ...] 降级链
    """
    config = ROLE_MODEL_CONFIGS.get(role)
    if not config:
        return []
    
    return [
        (config.primary_provider, config.primary_model),
        (config.fallback_provider, config.fallback_model),
        (config.global_fallback_provider, config.global_fallback_model),
    ]
