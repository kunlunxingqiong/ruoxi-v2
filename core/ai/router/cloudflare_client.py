"""
🌸 若曦V2 - Cloudflare Workers AI 客户端

支持 Cloudflare Workers AI 模型
无发现API，使用静态模型列表

环境变量:
- CLOUDFLARE_ACCOUNT_ID: Cloudflare Account ID
- CLOUDFLARE_API_TOKEN: Cloudflare API Token

API文档: https://developers.cloudflare.com/workers-ai/

更新日志:
- 2026-07-13: 初始版本
"""
import asyncio
import aiohttp
import os
import time
from typing import AsyncGenerator, Dict, List, Optional

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider


# Cloudflare Workers AI 静态模型列表
CLOUDFLARE_MODELS: Dict[str, Dict] = {
    "@cf/meta/llama-3-8b-instruct": {
        "name": "Llama 3 8B Instruct",
        "context_length": 8192,
        "description": "Meta Llama 3 8B Instruction Tuned"
    },
    "@cf/meta/llama-3-70b-instruct": {
        "name": "Llama 3 70B Instruct",
        "context_length": 8192,
        "description": "Meta Llama 3 70B Instruction Tuned"
    },
    "@cf/meta/llama-3.1-8b-instruct": {
        "name": "Llama 3.1 8B Instruct",
        "context_length": 128000,
        "description": "Meta Llama 3.1 8B Instruction Tuned"
    },
    "@cf/meta/llama-3.1-70b-instruct": {
        "name": "Llama 3.1 70B Instruct",
        "context_length": 128000,
        "description": "Meta Llama 3.1 70B Instruction Tuned"
    },
    "@cf/mistral/mistral-7b-instruct-v0.2": {
        "name": "Mistral 7B Instruct v0.2",
        "context_length": 32768,
        "description": "Mistral 7B Instruction Tuned v0.2"
    },
    "@cf/mistral/mixtral-8x7b-instruct-v0.1": {
        "name": "Mixtral 8x7B Instruct",
        "context_length": 32768,
        "description": "Mixtral 8x7B MoE Instruction Tuned"
    },
    "@cf/qwen/qwen2-7b-instruct": {
        "name": "Qwen2 7B Instruct",
        "context_length": 32768,
        "description": "Qwen2 7B Instruction Tuned"
    },
    "@cf/qwen/qwen2.5-7b-instruct": {
        "name": "Qwen2.5 7B Instruct",
        "context_length": 32768,
        "description": "Qwen2.5 7B Instruction Tuned"
    },
    "@cf/qwen/qwen2.5-32b-instruct": {
        "name": "Qwen2.5 32B Instruct",
        "context_length": 32768,
        "description": "Qwen2.5 32B Instruction Tuned"
    },
    "@cf/google/gemma-2b-it": {
        "name": "Gemma 2B IT",
        "context_length": 8192,
        "description": "Google Gemma 2B Instruction Tuned"
    },
    "@cf/google/gemma-7b-it": {
        "name": "Gemma 7B IT",
        "context_length": 8192,
        "description": "Google Gemma 7B Instruction Tuned"
    },
    "@cf/deepseek-ai/deepseek-coder-6.7b-instruct": {
        "name": "DeepSeek Coder 6.7B",
        "context_length": 16384,
        "description": "DeepSeek Coder Instruction Tuned"
    },
    "@cf/tiiuae/falcon-7b-instruct": {
        "name": "Falcon 7B Instruct",
        "context_length": 2048,
        "description": "TII Falcon 7B Instruction Tuned"
    },
    "@cf/thebloke/neural-chat-7b-v3-1-awq": {
        "name": "Neural Chat 7B v3.1",
        "context_length": 4096,
        "description": "Neural Chat 7B v3.1 AWQ"
    },
    # 嵌入模型
    "@cf/baai/bge-base-en-v1.5": {
        "name": "BGE Base EN v1.5",
        "context_length": 512,
        "description": "BAAI BGE Base English Embedding"
    },
    "@cf/baai/bge-large-en-v1.5": {
        "name": "BGE Large EN v1.5",
        "context_length": 512,
        "description": "BAAI BGE Large English Embedding"
    },
    # 自动增强模型
    "@cf/autonomous-agent/gemma-2b": {
        "name": "Gemma 2B Agent",
        "context_length": 8192,
        "description": "Gemma 2B for Autonomous Agent"
    },
}


class CloudflareClient(BaseModel):
    """
    Cloudflare Workers AI 客户端

    特性:
    - 静态模型列表（约20+模型）
    - OpenAI兼容接口
    - 免费额度充足
    - 无发现API
    - 流式/非流式调用
    - 健康检查
    """

    BASE_URL = "https://api.cloudflare.com/client/v4"

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        model_name: str = "@cf/meta/llama-3-8b-instruct",
    ) -> None:
        """
        初始化 Cloudflare 客户端

        Args:
            account_id: Cloudflare Account ID
            api_token: Cloudflare API Token
            model_name: 默认模型ID
        """
        self._account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self._api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN")

        if not self._account_id or not self._api_token:
            raise ValueError(
                "Cloudflare credentials not found. Set CLOUDFLARE_ACCOUNT_ID and "
                "CLOUDFLARE_API_TOKEN environment variables."
            )

        super().__init__(self._api_token, model_name, ModelProvider.CLOUDFLARE)
        self.base_url = f"{self.BASE_URL}/accounts/{self._account_id}/ai"

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

            # Cloudflare Workers AI 限制约1000 req/min
            max_rpm = 1000
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
        Cloudflare Workers AI 对话

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
            raise Exception("Cloudflare rate limit exceeded")

        start_time = time.time()
        await self._increment_request()

        target_model = model_id or self.model_name
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/run/{target_model}",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    self._is_healthy = False
                    raise Exception(f"Cloudflare API error {resp.status}: {error_text}")

                data = await resp.json()
                latency_ms = int((time.time() - start_time) * 1000)

                self._is_healthy = True

                return ModelResponse(
                    content=data["response"],
                    model=target_model,
                    provider=ModelProvider.CLOUDFLARE,
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
        Cloudflare Workers AI 流式对话

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            model_id: 模型ID（可选）

        Yields:
            文本片段
        """
        if not await self._check_rate_limit():
            raise Exception("Cloudflare rate limit exceeded")

        start_time = time.time()
        await self._increment_request()

        target_model = model_id or self.model_name
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messages": self.format_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/v1/run/{target_model}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        self._is_healthy = False
                        raise Exception(f"Cloudflare API error {resp.status}: {error_text}")

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
                                if "response" in data:
                                    yield data["response"]
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
            headers = {"Authorization": f"Bearer {self._api_token}"}
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

    def discover_models(self) -> List[Dict]:
        """
        Cloudflare 无发现API，返回静态模型列表

        Returns:
            静态模型信息列表
        """
        models = []
        for model_id, info in CLOUDFLARE_MODELS.items():
            models.append({
                "id": model_id,
                "name": info["name"],
                "context_length": info.get("context_length", 8192),
                "description": info.get("description", ""),
            })
        return models

    def format_messages(self, messages: List[Message]) -> List[Dict]:
        """
        格式化消息为API格式
        """
        return [{"role": m.role, "content": m.content} for m in messages]

    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型ID列表
        """
        return list(CLOUDFLARE_MODELS.keys())
