"""
🌸 若曦V2 - 智谱直连客户端

支持智谱 GLM API，6+模型
OpenAI兼容接口

环境变量:
- ZHIPU_API_KEY: 智谱 API密钥

API文档: https://open.bigmodel.cn/dev/

更新日志:
- 2026-07-13: 初始版本
"""
import asyncio
import aiohttp
import os
import time
from typing import AsyncGenerator, Dict, List, Optional

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider


class ZhipuClient(BaseModel):
    """
    智谱 GLM API 客户端

    特性:
    - 6+模型支持 (GLM-4/GLM-4V/GLM-3等)
    - OpenAI兼容接口
    - 多模态支持
    - 流式/非流式调用
    - 健康检查
    - 速率限制
    """

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "glm-4-flash",
    ) -> None:
        """
        初始化智谱客户端

        Args:
            api_key: 智谱 API密钥
            model_name: 默认模型ID
        """
        self._api_key = api_key or os.getenv("ZHIPU_API_KEY")

        if not self._api_key:
            raise ValueError(
                "Zhipu API key not found. Set ZHIPU_API_KEY environment variable."
            )

        super().__init__(self._api_key, model_name, ModelProvider.ZHIPU)
        self.base_url = self.BASE_URL

        # 速率限制跟踪
        self._request_count = 0
        self._last_reset_time = time.time()
        self._lock = asyncio.Lock()

        # 健康状态
        self._is_healthy = True
        self._last_health_check = 0.0
        self._health_check_interval = 60

    async def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        async with self._lock:
            current_time = time.time()

            # 每分钟重置
            if current_time - self._last_reset_time >= 60:
                self._request_count = 0
                self._last_reset_time = current_time

            # 智谱限制约60 req/min
            max_rpm = 60
            return self._request_count < max_rpm

    async def _increment_request(self) -> None:
        """增加请求计数"""
        async with self._lock:
            self._request_count += 1

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
        model_id: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        智谱对话

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            model_id: 模型ID（可选，默认使用初始化时的model_name）

        Returns:
            ModelResponse对象
        """
        if not await self._check_rate_limit():
            raise Exception("Zhipu rate limit exceeded")

        start_time = time.time()
        await self._increment_request()

        target_model = model_id or self.model_name
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": target_model,
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    self._is_healthy = False
                    raise Exception(f"Zhipu API error {resp.status}: {error_text}")

                data = await resp.json()
                latency_ms = int((time.time() - start_time) * 1000)

                self._is_healthy = True

                return ModelResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=target_model,
                    provider=ModelProvider.ZHIPU,
                    usage=data.get("usage"),
                    latency_ms=latency_ms
                )

    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        model_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        智谱流式对话

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            model_id: 模型ID（可选）

        Yields:
            文本片段
        """
        if not await self._check_rate_limit():
            raise Exception("Zhipu rate limit exceeded")

        start_time = time.time()
        await self._increment_request()

        target_model = model_id or self.model_name
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": target_model,
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self._is_healthy = False
                        raise Exception(f"Zhipu API error {resp.status}: {error_text}")

                    self._is_healthy = True

                    async for line in resp.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                            except Exception:
                                pass

            except aiohttp.ClientError as e:
                self._is_healthy = False
                raise

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        current_time = time.time()

        # 缓存60秒
        if current_time - self._last_health_check < self._health_check_interval:
            return self._is_healthy

        self._last_health_check = current_time

        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    self._is_healthy = (resp.status == 200)
                    return self._is_healthy
        except Exception:
            self._is_healthy = False
            return False

    async def discover_models(self) -> List[Dict]:
        """
        调用 /v1/models 接口获取可用模型列表

        Returns:
            模型信息列表
        """
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return data.get("data", [])
        except Exception:
            return []

    def format_messages(self, messages: List[Message]) -> List[Dict]:
        """
        格式化消息为API格式
        """
        return [{"role": m.role, "content": m.content} for m in messages]
