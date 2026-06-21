"""
🌸 若曦V2 - 硅基流动客户端

支持硅基流动API，92+模型
OpenAI兼容接口

环境变量:
- SILICONFLOW_KEY: 硅基流动 API密钥

API文档: https://docs.siliconflow.cn/

更新日志:
- 2026-07-13: 初始版本
"""
import asyncio
import aiohttp
import os
import time
from typing import AsyncGenerator, Dict, List, Optional

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider
from core.ai.router.route_config import (
    SILICONFLOW_MODELS,
    ModelInfo,
    TaskType,
)


class SiliconFlowClient(BaseModel):
    """
    硅基流动 API 客户端
    
    特性:
    - 92+模型支持
    - OpenAI兼容接口
    - 流式/非流式调用
    - 健康检查
    - 速率限制 (约120 req/min)
    """
    
    BASE_URL = "https://api.siliconflow.cn/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "deepseek-ai/DeepSeek-V3",
    ) -> None:
        """
        初始化硅基流动客户端
        
        Args:
            api_key: 硅基流动 API密钥
            model_name: 默认模型ID
        """
        self._api_key = api_key or os.getenv("SILICONFLOW_KEY")
        
        if not self._api_key:
            raise ValueError(
                "SiliconFlow API key not found. Set SILICONFLOW_KEY environment variable."
            )
        
        super().__init__(self._api_key, model_name, ModelProvider.SILICONFLOW)
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
            
            # 硅基流动限制约120 req/min
            max_rpm = 120
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
        硅基流动对话
        
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
            raise Exception("SiliconFlow rate limit exceeded")
        
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
                    raise Exception(f"SiliconFlow API error {resp.status}: {error_text}")
                
                data = await resp.json()
                latency_ms = int((time.time() - start_time) * 1000)
                
                self._is_healthy = True
                
                return ModelResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=target_model,
                    provider=ModelProvider.SILICONFLOW,
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
        硅基流动流式对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            model_id: 模型ID（可选）
            
        Yields:
            文本片段
        """
        if not await self._check_rate_limit():
            raise Exception("SiliconFlow rate limit exceeded")
        
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
                        raise Exception(f"SiliconFlow API error {resp.status}: {error_text}")
                    
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
        import time
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
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            模型ID列表
        """
        return list(SILICONFLOW_MODELS.keys())
    
    def select_model_for_task(self, task_type: TaskType) -> str:
        """
        根据任务类型选择最佳模型
        
        Args:
            task_type: 任务类型
            
        Returns:
            模型ID
        """
        # 任务类型到模型的映射
        task_model_map = {
            TaskType.CODING: "Qwen/Qwen2.5-Coder-32B-Instruct",
            TaskType.REASONING: "deepseek-ai/DeepSeek-V3",
            TaskType.GENERAL: "deepseek-ai/DeepSeek-V3",
        }
        
        return task_model_map.get(task_type, "deepseek-ai/DeepSeek-V3")
    
    def format_messages(self, messages: List[Message]) -> List[Dict]:
        """
        格式化消息为API格式
        """
        return [{"role": m.role, "content": m.content} for m in messages]
