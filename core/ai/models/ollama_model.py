"""
🌸 若曦V2 - Ollama模型适配器
本地LLM运行，完全免费，隐私优先
"""

import time
from typing import AsyncGenerator, List

import aiohttp

from core.ai.models.base_model import BaseModel, Message, ModelProvider, ModelResponse


class OllamaModel(BaseModel):
    """
    Ollama本地模型适配器

    特点:
    - 完全本地运行，无需联网
    - 完全免费，无请求限制
    - 极致隐私，数据不出本地
    - 支持主流开源模型

    官网: https://ollama.com/

    支持的模型:
    - llama3.3, llama3.1, llama3
    - qwen2.5 (通义千问)
    - deepseek-r1
    - mistral, mixtral
    - phi4
    """

    AVAILABLE_MODELS = [
        "llama3.3",
        "llama3.1",
        "llama3",
        "qwen2.5",
        "qwen2.5:14b",
        "deepseek-r1",
        "mistral",
        "mixtral",
        "phi4",
    ]

    def __init__(
        self,
        model_name: str = "qwen2.5",
        base_url: str = "http://localhost:11434",
        api_key: str = "",
    ):
        # Ollama不需要API key，但需要兼容基类接口
        super().__init__(api_key or "local", model_name, ModelProvider.OLLAMA)
        self.base_url = base_url

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """转换消息格式"""
        converted = []
        for msg in messages:
            # Ollama使用user/assistant/system角色
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
        调用本地Ollama模型

        API文档: https://github.com/ollama/ollama/blob/main/docs/api.md
        """
        start_time = time.time()

        converted_messages = self._convert_messages(messages)

        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": converted_messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama错误: {response.status} - {error_text}")

                result = await response.json()

                content = result["message"]["content"]

                # 获取使用统计
                stats = result.get("prompt_eval_count", 0), result.get("eval_count", 0)
                usage = {
                    "prompt_tokens": stats[0],
                    "completion_tokens": stats[1],
                    "total_tokens": sum(stats),
                }

                latency = int((time.time() - start_time) * 1000)

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
        """Ollama流式输出"""
        converted_messages = self._convert_messages(messages)

        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": converted_messages,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                async for line in response.content:
                    try:
                        import json

                        data = json.loads(line.decode("utf-8"))

                        # 检查是否完成
                        if data.get("done", False):
                            break

                        # 提取内容
                        message = data.get("message", {})
                        if "content" in message:
                            yield message["content"]

                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass

    async def health_check(self) -> bool:
        """检查Ollama服务状态"""
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False

    async def pull_model(self, model_name: str) -> bool:
        """拉取模型"""
        try:
            url = f"{self.base_url}/api/pull"
            payload = {"name": model_name}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    # 拉取是异步的，立即返回
                    return response.status == 200
        except Exception as e:
            print(f"拉取模型失败: {e}")
            return False

    async def list_local_models(self) -> List[dict]:
        """列出本地可用模型"""
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("models", [])
        except Exception:
            pass
        return []

    def get_info(self) -> dict:
        """获取模型信息"""
        info = super().get_info()
        info.update(
            {
                "rate_limit": "无限制",
                "available_models": self.AVAILABLE_MODELS,
                "features": ["text", "local", "privacy", "offline"],
                "requirements": "本地GPU/CPU",
                "cost": "永久免费",
            }
        )
        return info

    def is_local(self) -> bool:
        """是否为本地模型"""
        return True
