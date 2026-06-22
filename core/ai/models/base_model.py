"""
🌸 若曦V2 - AI模型基类
定义统一模型接口，支持多模型切换和动态模型发现
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional


class ModelProvider(Enum):
    """模型提供商"""

    GEMINI = "gemini"  # Google Gemini (永久免费)
    GROQ = "groq"  # Groq云 (免费高速)
    OLLAMA = "ollama"  # 本地免费
    TOGETHER = "together"  # Together AI (免费额度)
    OPENROUTER = "openrouter"  # OpenRouter (免费模型)
    ZHIPU = "zhipu"  # 智谱GLM-4 (部分免费)
    DEEPSEEK = "deepseek"  # DeepSeek (深度推理)
    MOONSHOT = "moonshot"  # 月之暗面 (长上下文)
    DASHSCOPE = "dashscope"  # 阿里百炼 (通义千问)
    # 新增Provider (星穹 Claw-B 添加)
    NVIDIA = "nvidia"  # NVIDIA NIM (117+模型)
    SILICONFLOW = "siliconflow"  # 硅基流动 (92+模型)
    CLOUDFLARE = "cloudflare"  # Cloudflare Workers AI


@dataclass
class Message:
    """消息对象"""

    role: str  # system, user, assistant
    content: str


@dataclass
class ModelResponse:
    """模型响应"""

    content: str
    model: str
    provider: ModelProvider
    usage: Optional[Dict] = None
    latency_ms: Optional[int] = None


class BaseModel(ABC):
    """
    AI模型基类

    所有AI模型必须实现此接口，实现统一调用方式

    新增 (2026-06-22): discover_models() 类方法支持动态模型发现
    """

    def __init__(self, api_key: str, model_name: str, provider: ModelProvider):
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider
        self.base_url: Optional[str] = None

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> ModelResponse:
        """
        聊天对话

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出

        Returns:
            ModelResponse对象
        """
        pass

    @abstractmethod
    async def chat_stream(
        self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天

        生成文本片段流
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """检查模型健康状态"""
        pass

    def format_messages(self, messages: List[Message]) -> List[Dict]:
        """
        格式化消息为模型所需格式
        子类可覆盖
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def get_info(self) -> Dict:
        """获取模型信息"""
        return {
            "provider": self.provider.value,
            "model": self.model_name,
            "base_url": self.base_url,
        }

    @classmethod
    def discover_models(
        cls, api_key: str, base_url: Optional[str] = None
    ) -> List[Dict]:
        """
        动态发现该Provider可用的模型列表

        Args:
            api_key: API密钥
            base_url: API基础URL

        Returns:
            模型信息列表 [{"id": str, "name": str, "owned_by": str}]

        Note:
            默认实现返回空列表，子类可覆盖以支持动态发现
        """
        return []
