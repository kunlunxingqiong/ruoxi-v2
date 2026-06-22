"""
🌸 若曦V2 - 硅基流动模型客户端
支持92+模型，兼容OpenAI API格式
"""

import time
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from core.ai.models.base_model import BaseModel, Message, ModelProvider, ModelResponse


class SiliconFlowModel(BaseModel):
    """硅基流动模型客户端 (92+模型)"""

    def __init__(self, api_key: str, model_name: str):
        super().__init__(api_key, model_name, ModelProvider.SILICONFLOW)
        self.base_url = "https://api.siliconflow.cn/v1"
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> ModelResponse:
        payload = {
            "model": self.model_name,
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        start = time.time()
        response = await self._client.post("/chat/completions", json=payload)
        latency = int((time.time() - start) * 1000)

        if response.status_code != 200:
            raise Exception(
                f"硅基流动API错误 {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        return ModelResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.model_name,
            provider=ModelProvider.SILICONFLOW,
            usage=data.get("usage"),
            latency_ms=latency,
        )

    async def chat_stream(
        self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model_name,
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self._client.stream(
            "POST", "/chat/completions", json=payload
        ) as response:
            if response.status_code != 200:
                raise Exception(f"硅基流动流式错误 {response.status_code}")
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
            response = await self._client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    @classmethod
    def discover_models(
        cls, api_key: str, base_url: Optional[str] = None
    ) -> List[Dict]:
        import requests

        models = []
        try:
            resp = requests.get(
                "https://api.siliconflow.cn/v1/models",
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
                            "owned_by": m.get("owned_by", "siliconflow"),
                            "provider": "siliconflow",
                        }
                    )
        except Exception as e:
            print(f"硅基流动模型发现失败: {e}")
        return models
