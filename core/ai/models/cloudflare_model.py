"""
🌸 若曦V2 - Cloudflare Workers AI 模型客户端
免费，每天1万次
"""

import time
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from core.ai.models.base_model import BaseModel, Message, ModelProvider, ModelResponse


class CloudflareModel(BaseModel):
    """Cloudflare Workers AI 模型客户端"""

    def __init__(self, api_key: str, model_name: str, account_id: str = ""):
        super().__init__(api_key, model_name, ModelProvider.CLOUDFLARE)
        self.account_id = account_id
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai"
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
        # Cloudflare格式: {"messages": [...]}
        payload = {
            "messages": self.format_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        start = time.time()
        # Cloudflare API: POST /v1/chat/completions 或 /run/{model}
        response = await self._client.post(f"/v1/chat/completions", json=payload)
        latency = int((time.time() - start) * 1000)

        if response.status_code != 200:
            raise Exception(
                f"Cloudflare API错误 {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        # Cloudflare返回格式可能不同
        if "result" in data:
            content = data["result"].get("response", str(data["result"]))
        elif "choices" in data:
            content = data["choices"][0]["message"]["content"]
        else:
            content = str(data)

        return ModelResponse(
            content=content,
            model=self.model_name,
            provider=ModelProvider.CLOUDFLARE,
            latency_ms=latency,
        )

    async def chat_stream(
        self, messages: List[Message], temperature: float = 0.7, max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        payload = {
            "messages": self.format_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        async with self._client.stream(
            "POST", "/v1/chat/completions", json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    import json

                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("result", {}).get("response", "")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError):
                        continue

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/models/search")
            return response.status_code == 200
        except Exception:
            return False

    @classmethod
    def discover_models(
        cls, api_key: str, base_url: Optional[str] = None
    ) -> List[Dict]:
        # Cloudflare需要account_id，不方便动态发现
        # 返回已知模型列表
        return [
            {
                "id": "@cf/meta/llama-3.1-8b-instruct",
                "name": "Llama 3.1 8B",
                "provider": "cloudflare",
            },
            {
                "id": "@cf/meta/llama-3.2-1b-instruct",
                "name": "Llama 3.2 1B",
                "provider": "cloudflare",
            },
            {
                "id": "@cf/meta/llama-3.2-3b-instruct",
                "name": "Llama 3.2 3B",
                "provider": "cloudflare",
            },
            {
                "id": "@cf/mistral/mistral-7b-instruct",
                "name": "Mistral 7B",
                "provider": "cloudflare",
            },
            {
                "id": "@cf/deepseek-ai/deepseek-math-7b-instruct",
                "name": "DeepSeek Math 7B",
                "provider": "cloudflare",
            },
            {
                "id": "@cf/deepseek-ai/deepseek-coder-6.7b-instruct",
                "name": "DeepSeek Coder 6.7B",
                "provider": "cloudflare",
            },
        ]
