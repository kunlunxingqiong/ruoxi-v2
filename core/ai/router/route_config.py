"""
🌸 若曦V2 - 路由配置模块
定义模型路由策略、任务类型映射和免费额度跟踪配置
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


class ProviderPriority(Enum):
    """Provider优先级（数值越小优先级越高）"""
    # 免费模型 - 最高优先级
    OPENROUTER = 1      # 23个免费模型
    GOOGLE_AI = 2       # Gemini系列
    GROQ = 3            # 超快免费推理
    CLOUDFLARE = 4      # Workers AI
    
    # 付费模型 - 最低优先级（仅fallback）
    SILICONFLOW = 10    # 硅基流动（备用）
    ZHIPU = 11          # 智谱（OpenRouter有免费版）
    MOONSHOT = 12       # 月之暗面
    DASHSCOPE = 13      # 阿里百炼
    DEEPSEEK = 14       # DeepSeek


@dataclass
class ModelInfo:
    """模型信息"""
    model_id: str                          # 模型标识符
    provider: ProviderPriority             # 提供商优先级
    provider_name: str                     # 提供商名称
    task_types: Set[TaskType]              # 支持的任务类型
    is_free: bool = True                   # 是否免费
    max_tokens: int = 8192                 # 最大输出token
    context_window: int = 128000           # 上下文窗口
    supports_streaming: bool = True        # 支持流式输出
    supports_vision: bool = False          # 支持视觉
    daily_limit: Optional[int] = None       # 每日调用限制
    rate_limit_rpm: int = 60               # 每分钟请求限制
    description: str = ""                  # 模型描述


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
    "google/gemma-4-31b-it:free": ModelInfo(
        model_id="google/gemma-4-31b-it:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=4096,
        context_window=32000,
        daily_limit=100,
        description="Gemma 4 31B 免费版"
    ),
    "z-ai/glm-4.5-air:free": ModelInfo(
        model_id="z-ai/glm-4.5-air:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.CODING},
        is_free=True,
        max_tokens=4096,
        context_window=128000,
        daily_limit=100,
        description="GLM-4.5 Air 免费版"
    ),
    "openai/gpt-oss-120b:free": ModelInfo(
        model_id="openai/gpt-oss-120b:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.REASONING},
        is_free=True,
        max_tokens=4096,
        context_window=32000,
        daily_limit=50,
        description="GPT-OSS 120B 免费版"
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
    "minimax/minimax-m2.5:free": ModelInfo(
        model_id="minimax/minimax-m2.5:free",
        provider=ProviderPriority.OPENROUTER,
        provider_name="OpenRouter",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=4096,
        context_window=100000,
        daily_limit=100,
        description="MiniMax M2.5 免费版"
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
        daily_limit=1500,  # 每天150万token
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
    "gemini-1.5-flash": ModelInfo(
        model_id="gemini-1.5-flash",
        provider=ProviderPriority.GOOGLE_AI,
        provider_name="Google AI Studio",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE, TaskType.CODING, TaskType.VISION},
        is_free=True,
        max_tokens=8192,
        context_window=1000000,
        supports_vision=True,
        daily_limit=1500,
        rate_limit_rpm=1000,
        description="Gemini 1.5 Flash"
    ),
    "gemini-1.5-pro": ModelInfo(
        model_id="gemini-1.5-pro",
        provider=ProviderPriority.GOOGLE_AI,
        provider_name="Google AI Studio",
        task_types={TaskType.GENERAL, TaskType.REASONING, TaskType.LONG_TEXT, TaskType.VISION},
        is_free=True,
        max_tokens=8192,
        context_window=2000000,
        supports_vision=True,
        daily_limit=500,
        rate_limit_rpm=100,
        description="Gemini 1.5 Pro"
    ),
    "gemma-3-27b-it": ModelInfo(
        model_id="gemma-3-27b-it",
        provider=ProviderPriority.GOOGLE_AI,
        provider_name="Google AI Studio",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=8192,
        context_window=32000,
        daily_limit=1500,
        description="Gemma 3 27B"
    ),
}

# Groq 模型
GROQ_MODELS: Dict[str, ModelInfo] = {
    "llama-3.3-70b-versatile": ModelInfo(
        model_id="llama-3.3-70b-versatile",
        provider=ProviderPriority.GROQ,
        provider_name="Groq",
        task_types={TaskType.GENERAL, TaskType.CODING, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=8192,
        context_window=128000,
        rate_limit_rpm=30,
        description="Llama 3.3 70B 超快版"
    ),
    "llama-3.1-8b-instant": ModelInfo(
        model_id="llama-3.1-8b-instant",
        provider=ProviderPriority.GROQ,
        provider_name="Groq",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=8192,
        context_window=128000,
        rate_limit_rpm=30,
        description="Llama 3.1 8B 极速版"
    ),
    "mixtral-8x7b-32768": ModelInfo(
        model_id="mixtral-8x7b-32768",
        provider=ProviderPriority.GROQ,
        provider_name="Groq",
        task_types={TaskType.GENERAL, TaskType.CODING},
        is_free=True,
        max_tokens=32768,
        context_window=32000,
        rate_limit_rpm=30,
        description="Mixtral 8x7B"
    ),
    "gemma2-9b-it": ModelInfo(
        model_id="gemma2-9b-it",
        provider=ProviderPriority.GROQ,
        provider_name="Groq",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=8192,
        context_window=8000,
        rate_limit_rpm=30,
        description="Gemma 2 9B"
    ),
}

# Cloudflare Workers AI 模型
CLOUDFLARE_MODELS: Dict[str, ModelInfo] = {
    "@cf/meta/llama-3.1-8b-instruct": ModelInfo(
        model_id="@cf/meta/llama-3.1-8b-instruct",
        provider=ProviderPriority.CLOUDFLARE,
        provider_name="Cloudflare Workers AI",
        task_types={TaskType.GENERAL, TaskType.FAST_RESPONSE},
        is_free=True,
        max_tokens=4096,
        context_window=128000,
        daily_limit=10000,
        rate_limit_rpm=60,
        description="Llama 3.1 8B Cloudflare版"
    ),
    "@cf/mistral/mistral-7b-instruct-v0.1": ModelInfo(
        model_id="@cf/mistral/mistral-7b-instruct-v0.1",
        provider=ProviderPriority.CLOUDFLARE,
        provider_name="Cloudflare Workers AI",
        task_types={TaskType.GENERAL},
        is_free=True,
        max_tokens=4096,
        context_window=32000,
        daily_limit=10000,
        rate_limit_rpm=60,
        description="Mistral 7B Cloudflare版"
    ),
    "@cf/deepseek-ai/deepseek-coder-33b-instruct": ModelInfo(
        model_id="@cf/deepseek-ai/deepseek-coder-33b-instruct",
        provider=ProviderPriority.CLOUDFLARE,
        provider_name="Cloudflare Workers AI",
        task_types={TaskType.CODING},
        is_free=True,
        max_tokens=4096,
        context_window=32000,
        daily_limit=10000,
        rate_limit_rpm=60,
        description="DeepSeek Coder 33B"
    ),
}

# 任务类型到模型的默认映射
TASK_MODEL_MAPPING: Dict[TaskType, List[str]] = {
    TaskType.GENERAL: [
        "deepseek/deepseek-v4-flash:free",
        "gemini-1.5-flash",
        "llama-3.3-70b-versatile",
        "@cf/meta/llama-3.1-8b-instruct",
    ],
    TaskType.CODING: [
        "qwen/qwen3-coder:free",
        "deepseek/deepseek-v4-flash:free",
        "llama-3.3-70b-versatile",
        "@cf/deepseek-ai/deepseek-coder-33b-instruct",
    ],
    TaskType.REASONING: [
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "gemini-1.5-pro",
    ],
    TaskType.LONG_TEXT: [
        "moonshotai/kimi-k2.6:free",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
    TaskType.FAST_RESPONSE: [
        "gemini-2.0-flash-exp",
        "gemma-3-27b-it",
        "gemma2-9b-it",
        "minimax/minimax-m2.5:free",
    ],
    TaskType.VISION: [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
    TaskType.CREATIVE: [
        "deepseek/deepseek-v4-flash:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "gemini-1.5-flash",
    ],
}


@dataclass
class RouteConfig:
    """路由配置"""
    # 优先级策略
    enable_free_first: bool = True          # 优先使用免费模型
    enable_provider_fallback: bool = True    # Provider降级
    enable_model_fallback: bool = True       # 同Provider内模型降级
    
    # 负载均衡策略
    load_balance_strategy: str = "round_robin"  # round_robin, random, weighted
    
    # 健康检查
    health_check_interval: int = 300       # 健康检查间隔(秒)
    health_check_timeout: int = 10         # 健康检查超时(秒)
    unhealthy_threshold: int = 3           # 连续失败次数阈值
    
    # 速率限制
    enable_rate_limit: bool = True         # 启用速率限制跟踪
    daily_limit_warning: float = 0.8        # 发出警告的阈值比例
    
    # 超时配置
    request_timeout: int = 120             # 请求超时(秒)
    stream_timeout: int = 300              # 流式请求超时(秒)
    
    # 重试配置
    max_retries: int = 3                   # 最大重试次数
    retry_delay: float = 1.0                # 重试延迟(秒)


# 默认路由配置
DEFAULT_ROUTE_CONFIG = RouteConfig()


# 所有可用模型注册表
ALL_MODELS: Dict[str, ModelInfo] = {}
ALL_MODELS.update(OPENROUTER_FREE_MODELS)
ALL_MODELS.update(GOOGLE_AI_MODELS)
ALL_MODELS.update(GROQ_MODELS)
ALL_MODELS.update(CLOUDFLARE_MODELS)


def get_models_for_task(
    task_type: TaskType,
    config: Optional[RouteConfig] = None
) -> List[ModelInfo]:
    """
    获取适合指定任务类型的模型列表
    
    Args:
        task_type: 任务类型
        config: 路由配置
        
    Returns:
        按优先级排序的模型列表
    """
    if config is None:
        config = DEFAULT_ROUTE_CONFIG
    
    # 获取任务对应的模型ID列表
    model_ids = TASK_MODEL_MAPPING.get(task_type, TASK_MODEL_MAPPING[TaskType.GENERAL])
    
    # 过滤并排序
    models = []
    for model_id in model_ids:
        if model_id in ALL_MODELS:
            model_info = ALL_MODELS[model_id]
            if config.enable_free_first and not model_info.is_free:
                continue
            models.append(model_info)
    
    # 按优先级排序
    models.sort(key=lambda m: m.provider.value)
    
    return models


def get_all_free_models() -> List[ModelInfo]:
    """获取所有免费模型"""
    return [m for m in ALL_MODELS.values() if m.is_free]


def get_provider_models(provider: ProviderPriority) -> List[ModelInfo]:
    """获取指定Provider的所有模型"""
    return [m for m in ALL_MODELS.values() if m.provider == provider]
