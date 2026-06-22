"""
🌸 若曦V2 - NVIDIA NIM 模型客户端
支持117+模型，双Key轮询负载均衡
"""

import asyncio
import time
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from core.ai.models.base_model import BaseModel, Message, ModelProvider, ModelResponse


class NVIDIAModel(BaseModel):
    """
    NVIDIA NIM 模型客户端

    特性:
    - 117+模型 (DeepSeek V4, Llama, Nemotron等)
    - 双Key轮询负载均衡
    - 兼容OpenAI API格式
    - 动态模型发现
    """

    # 双Key轮询
    API_KEYS: List[str] = []
    _key_index: int = 0

    def __init__(self, api_key: str, model_name: str, api_key_2: Optional[str] = None):
        super().__init__(api_key, model_name, ModelProvider.NVIDIA)
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        # 双Key
        NVIDIAModel.API_KEYS = [api_key]
        if api_key_2:
            NVIDIAModel.API_KEYS.append(api_key_2)

    def _get_next_key(self) -> str:
        """轮询获取下一个API Key"""
        if len(NVIDIAModel.API_KEYS) <= 1:
            return NVIDIAModel.API_KEYS[0]
        NVIDIAModel._key_index = (NVIDIAModel._key_index + 1) % len(
            NVIDIAModel.API_KEYS
        )
        return NVIDIAModel.API_KEYS[NVIDIAModel._key_index]

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> ModelResponse:
        key = self._get_next_key()
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model_name,
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        start = time.time()
        response = await self._client.post(
            "/chat/completions", json=payload, headers=headers
        )
        latency = int((time.time() - start) * 1000)

        if response.status_code != 200:
            raise Exception(
                f"NVIDIA API错误 {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return ModelResponse(
            content=content,
            model=self.model_name,
            provider=ModelProvider.NVIDIA,
            usage=data.get("usage"),
            latency_ms=latency,
        )

    async def chat_stream(
        self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        key = self._get_next_key()
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        payload = {
            "model": self.model_name,
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self._client.stream(
            "POST", "/chat/completions", json=payload, headers=headers
        ) as response:
            if response.status_code != 200:
                raise Exception(f"NVIDIA流式错误 {response.status_code}")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    import json

                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    async def health_check(self) -> bool:
        try:
            key = self._get_next_key()
            headers = {"Authorization": f"Bearer {key}"}
            response = await self._client.get("/models", headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    @classmethod
    def discover_models(
        cls, api_key: str, base_url: Optional[str] = None
    ) -> List[Dict]:
        """
        动态发现NVIDIA NIM可用模型
        同步方法，在启动时调用
        """
        import requests

        models = []
        try:
            resp = requests.get(
                "https://integrate.api.nvidia.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                for m in data.get("data", []):
                    models.append(
                        {
                            "id": m.get("id", ""),
                            "name": m.get("id", ""),
                            "owned_by": m.get("owned_by", "nvidia"),
                            "provider": "nvidia",
                        }
                    )
        except Exception as e:
            print(f"NVIDIA模型发现失败: {e}")
        return models
