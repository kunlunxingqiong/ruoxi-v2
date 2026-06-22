"""
🌸 若曦V2 - 阿里百炼DashScope模型适配器
支持通义千问系列: qwen-turbo, qwen-plus, qwen-max
"""

import time
from typing import AsyncGenerator, List

import aiohttp

from core.ai.models.base_model import BaseModel, Message, ModelProvider, ModelResponse


class DashscopeModel(BaseModel):
    """
    阿里百炼DashScope模型适配器

    支持模型:
    - qwen-turbo: 快速响应，高并发
    - qwen-plus: 高性能，平衡成本
    - qwen-max: 旗舰模型，最强能力

    官网: https://dashscope.console.aliyun.com/
    API文档: https://help.aliyun.com/zh/dashscope/
    """

    AVAILABLE_MODELS = [
        "qwen-turbo",  # 快速版
        "qwen-plus",  # 增强版
        "qwen-max",  # 旗舰版
        "qwen-max-longcontext",  # 长上下文版
    ]

    def __init__(self, api_key: str, model_name: str = "qwen-plus") -> None:
        """
        初始化DashScope模型

        Args:
            api_key: DashScope API密钥 (格式: Bearer sk-xxx)
            model_name: 模型名称，默认 qwen-plus
        """
        super().__init__(api_key, model_name, ModelProvider.DASHSCOPE)
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        # 清理API Key格式
        if self.api_key.startswith("Bearer "):
            self._bearer_key = self.api_key
        else:
            self._bearer_key = f"Bearer {self.api_key}"

    def _format_messages(self, messages: List[Message]) -> List[dict]:
        """
        格式化消息为OpenAI兼容格式

        Args:
            messages: 消息列表

        Returns:
            格式化后的消息列表
        """
        formatted = []
        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> ModelResponse:
        """
        调用通义千问模型进行对话

        Args:
            messages: 消息列表
            temperature: 温度参数 (0-1)
            max_tokens: 最大token数
            stream: 是否流式输出

        Returns:
            ModelResponse对象
        """
        start_time = time.time()

        formatted_messages = self._format_messages(messages)

        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": self._bearer_key,
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"DashScope API错误: {response.status} - {error_text}"
                    )

                result = await response.json()

                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                model_used = result.get("model", self.model_name)

                latency = int((time.time() - start_time) * 1000)

                return ModelResponse(
                    content=content,
                    model=model_used,
                    provider=self.provider,
                    usage=usage,
                    latency_ms=latency,
                )

    async def chat_stream(
        self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        通义千问流式输出

        使用Server-Sent Events (SSE) 格式

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            文本片段
        """
        formatted_messages = self._format_messages(messages)

        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        headers = {
            "Authorization": self._bearer_key,
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                async for line in response.content:
                    line = line.decode("utf-8").strip()

                    # 跳过空行和SSE格式头
                    if not line or line.startswith(":") or line == "data: [DONE]":
                        continue

                    if line.startswith("data:"):
                        try:
                            import json

                            data = json.loads(line[5:].strip())
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    async def health_check(self) -> bool:
        """
        检查DashScope服务状态

        Returns:
            服务是否可用
        """
        try:
            url = f"{self.base_url}/models"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers={"Authorization": self._bearer_key}
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    def get_info(self) -> dict:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        info = super().get_info()
        info.update(
            {
                "rate_limit": "根据订阅等级",
                "available_models": self.AVAILABLE_MODELS,
                "features": ["text", "vision", "function_calling", "long_context"],
                "auth_type": "Bearer Token (sk-xxx)",
                "cost": "付费模型",
            }
        )
        return info
