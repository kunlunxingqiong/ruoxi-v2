"""
🌸 若曦V2 - 智谱GLM-4模型适配器
支持 glm-4-flash (免费), glm-4-air, glm-4-plus
"""

import time
from typing import AsyncGenerator, List

import aiohttp
import jwt

from core.ai.models.base_model import BaseModel, Message, ModelProvider, ModelResponse


def generate_token(api_key: str) -> str:
    """
    生成智谱API访问令牌

    智谱使用JWT鉴权，需要用API Key的secret部分签名生成token

    Args:
        api_key: API密钥，格式为 "id.secret"

    Returns:
        JWT访问令牌
    """
    api_key_parts = api_key.split(".")
    if len(api_key_parts) != 2:
        raise ValueError("Invalid API key format. Expected 'id.secret'")

    api_key_id, secret = api_key_parts
    payload = {
        "api_key": api_key_id,
        "exp": int(round(time.time())) + 3600,
        "timestamp": int(round(time.time())),
    }
    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


class ZhipuModel(BaseModel):
    """
    智谱GLM-4模型适配器

    免费额度:
    - glm-4-flash: 100万Tokens/月 (免费)
    - glm-4-air: 100万Tokens/月
    - glm-4-plus: 10万Tokens/月

    官网: https://open.bigmodel.cn/
    API文档: https://open.bigmodel.cn/dev/api
    """

    AVAILABLE_MODELS = [
        "glm-4-flash",  # 免费模型
        "glm-4-air",  # 高性价比
        "glm-4-airx",  # 增强版
        "glm-4-plus",  # 旗舰模型
    ]

    def __init__(self, api_key: str, model_name: str = "glm-4-flash") -> None:
        """
        初始化智谱模型

        Args:
            api_key: 智谱API密钥（格式：id.secret）
            model_name: 模型名称，默认 glm-4-flash
        """
        super().__init__(api_key, model_name, ModelProvider.ZHIPU)
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self._token: str | None = None
        self._token_expires_at: float = 0

    def _get_token(self) -> str:
        """
        获取访问令牌，带缓存

        Returns:
            JWT访问令牌
        """
        # 检查token是否过期（提前5分钟刷新）
        if self._token and time.time() < (self._token_expires_at - 300):
            return self._token

        self._token = generate_token(self.api_key)
        self._token_expires_at = time.time() + 3600  # token有效期1小时
        return self._token

    def _format_messages(self, messages: List[Message]) -> List[dict]:
        """
        格式化消息为智谱API格式

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
        调用智谱GLM-4模型进行对话

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

        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"智谱API错误: {response.status} - {error_text}")

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
        智谱GLM-4流式输出

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

        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
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
        检查智谱服务状态

        Returns:
            服务是否可用
        """
        try:
            url = f"{self.base_url}/models"
            token = self._get_token()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers={"Authorization": f"Bearer {token}"}
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
                "rate_limit": "100万Tokens/月 (glm-4-flash免费)",
                "available_models": self.AVAILABLE_MODELS,
                "features": ["text", "function_calling", "vision"],
                "auth_type": "JWT Bearer Token",
                "cost": "部分模型免费",
            }
        )
        return info
