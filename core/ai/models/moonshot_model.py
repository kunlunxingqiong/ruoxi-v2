"""
🌸 若曦V2 - 月之暗面Moonshot模型适配器
支持 moonshot-v1-8k, moonshot-v1-32k, moonshot-v1-128k
"""
import aiohttp
import time
from typing import AsyncGenerator, List

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider


class MoonshotModel(BaseModel):
    """
    月之暗面Moonshot模型适配器
    
    支持模型 (上下文长度):
    - moonshot-v1-8k: 8K上下文
    - moonshot-v1-32k: 32K上下文
    - moonshot-v1-128k: 128K上下文
    
    官网: https://platform.moonshot.cn/
    API文档: https://platform.moonshot.cn/docs
    """
    
    AVAILABLE_MODELS = [
        "moonshot-v1-8k",    # 8K上下文
        "moonshot-v1-32k",   # 32K上下文
        "moonshot-v1-128k",  # 128K上下文 (支持超长对话)
    ]
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "moonshot-v1-8k"
    ) -> None:
        """
        初始化Moonshot模型
        
        Args:
            api_key: Moonshot API密钥
            model_name: 模型名称，默认 moonshot-v1-8k
        """
        super().__init__(api_key, model_name, ModelProvider.MOONSHOT)
        self.base_url = "https://api.moonshot.cn/v1"
    
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
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        return formatted
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> ModelResponse:
        """
        调用Moonshot模型进行对话
        
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
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Moonshot API错误: {response.status} - {error_text}")
                
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
                    latency_ms=latency
                )
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Moonshot流式输出
        
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
            "stream": True
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers
            ) as response:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    # 跳过空行和SSE格式头
                    if not line or line.startswith(':') or line == 'data: [DONE]':
                        continue
                    
                    if line.startswith('data:'):
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
        检查Moonshot服务状态
        
        Returns:
            服务是否可用
        """
        try:
            url = f"{self.base_url}/models"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"}
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
        info.update({
            "rate_limit": "根据订阅等级",
            "available_models": self.AVAILABLE_MODELS,
            "features": ["text", "long_context", "function_calling"],
            "context_length": "8K/32K/128K",
            "cost": "付费模型"
        })
        return info
