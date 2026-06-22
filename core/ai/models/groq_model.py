"""
🌸 若曦V2 - Groq模型适配器
Groq Cloud - 免费高速LLM推理
"""

import time
from typing import AsyncGenerator, List

import aiohttp

from core.ai.models.base_model import BaseModel, Message, ModelProvider, ModelResponse


class GroqModel(BaseModel):
    """
    Groq模型适配器

    免费额度:
    - 14,400 请求/天
    - Llama3/DeepSeek等高速运行

    官网: https://groq.com/
    """

    AVAILABLE_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "deepseek-r1-distill-llama-70b",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        super().__init__(api_key, model_name, ModelProvider.GROQ)
        self.base_url = "https://api.groq.com/openai/v1"

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """转换消息格式为标准OpenAI格式"""
        converted = []
        for msg in messages:
            # Groq不支持system角色，合并到user中
            if msg.role == "system":
                converted.append(
                    {"role": "user", "content": f"[系统指令] {msg.content}"}
                )
            else:
                converted.append({"role": msg.role, "content": msg.content})
        return converted

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> ModelResponse:
        """
        调用Groq模型

        API文档: https://console.groq.com/docs/openai
        """
        start_time = time.time()

        converted_messages = self._convert_messages(messages)

        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model_name,
            "messages": converted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Groq API错误: {response.status} - {error_text}")

                result = await response.json()

                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})

                latency = int((time.time() - start_time) * 1000)

                # Groq以超高速度著称，通常<100ms响应
                return ModelResponse(
                    content=content,
                    model=self.model_name,
                    provider=self.provider,
                    usage=usage,
                    latency_ms=latency,
                )

    async def chat_stream(
        self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """Groq流式输出"""
        converted_messages = self._convert_messages(messages)

        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model_name,
            "messages": converted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data:"):
                        try:
                            import json

                            data = json.loads(line[5:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            pass

    async def health_check(self) -> bool:
        """检查Groq服务状态"""
        try:
            url = f"{self.base_url}/models"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    def get_info(self) -> dict:
        """获取模型信息"""
        info = super().get_info()
        info.update(
            {
                "rate_limit": "14,400 requests/day (免费)",
                "available_models": self.AVAILABLE_MODELS,
                "features": ["text", "high_speed", "low_latency"],
                "speed": "~100 tokens/sec",
                "cost": "永久免费",
            }
        )
        return info
