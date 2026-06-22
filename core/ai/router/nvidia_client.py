"""
🌸 若曦V2 - NVIDIA NIM 客户端

支持NVIDIA NIM企业级推理API，117+模型
支持2把key轮询负载均衡

环境变量:
- NVIDIA_API_KEY: NVIDIA NIM API密钥 (主key)
- NVIDIA_API_KEY_2: NVIDIA NIM API密钥 (备用key，可选)

API文档: https://docs.nvidia.com/nim/live-sessions/

更新日志:
- 2026-07-13: 初始版本，2key轮询负载均衡
"""
import asyncio
import aiohttp
import os
from typing import AsyncGenerator, Dict, List, Optional

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider
from core.ai.router.route_config import (
    NVIDIA_MODELS,
    ModelInfo,
    TaskType,
)


class NVIDIAClient(BaseModel):
    """
    NVIDIA NIM API 客户端
    
    特性:
    - 117+模型支持
    - 2把key轮询负载均衡
    - 流式/非流式调用
    - 健康检查
    - 速率限制 (约40 req/min per key)
    - 动态模型发现
    """
    
    BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_key_2: Optional[str] = None,
        model_name: str = "deepseek-ai/deepseek-v4-pro",
    ) -> None:
        """
        初始化NVIDIA NIM客户端
        
        Args:
            api_key: NVIDIA NIM API密钥 (主key)
            api_key_2: NVIDIA NIM API密钥 (备用key，用于轮询负载均衡)
            model_name: 默认模型ID
        """
        self._api_keys: List[str] = []
        
        # 加载API keys
        key1 = api_key or os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_NIM_API_KEY")
        key2 = api_key_2 or os.getenv("NVIDIA_API_KEY_2")
        
        if key1:
            self._api_keys.append(key1)
        if key2:
            self._api_keys.append(key2)
        
        if not self._api_keys:
            raise ValueError(
                "NVIDIA API key not found. Set NVIDIA_API_KEY or NVIDIA_NIM_API_KEY environment variable."
            )
        
        # 轮询索引
        self._key_index = 0
        self._lock = asyncio.Lock()
        
        super().__init__(self._api_keys[0], model_name, ModelProvider.NVIDIA)
        self.base_url = self.BASE_URL
        
        # 速率限制跟踪 (per key)
        self._request_counts: Dict[int, int] = {i: 0 for i in range(len(self._api_keys))}
        self._last_reset_times: Dict[int, float] = {i: 0.0 for i in range(len(self._api_keys))}
        
        # 健康状态
        self._health_cache: Dict[int, bool] = {i: True for i in range(len(self._api_keys))}
        self._last_health_check: float = 0
        self._health_check_interval = 60  # 60秒缓存健康状态
    
    async def _get_next_key(self) -> tuple:
        """
        获取下一个可用的key（轮询负载均衡）
        
        Returns:
            (key_index, api_key)
        """
        async with self._lock:
            # 找到健康的key
            for _ in range(len(self._api_keys)):
                self._key_index = (self._key_index + 1) % len(self._api_keys)
                
                # 检查速率限制
                if self._check_rate_limit(self._key_index):
                    key = self._api_keys[self._key_index]
                    return self._key_index, key
            
            # 所有key都超限，等待重置
            await asyncio.sleep(1)
            self._reset_rate_limit(self._key_index)
            key = self._api_keys[self._key_index]
            return self._key_index, key
    
    def _check_rate_limit(self, key_index: int) -> bool:
        """检查指定key的速率限制"""
        import time
        current_time = time.time()
        
        # 每分钟重置
        if current_time - self._last_reset_times[key_index] >= 60:
            self._request_counts[key_index] = 0
            self._last_reset_times[key_index] = current_time
        
        # NVIDIA限制约40 req/min
        max_rpm = 40
        return self._request_counts[key_index] < max_rpm
    
    def _reset_rate_limit(self, key_index: int) -> None:
        """重置速率限制"""
        import time
        self._request_counts[key_index] = 0
        self._last_reset_times[key_index] = time.time()
    
    async def _increment_request(self, key_index: int) -> None:
        """增加请求计数"""
        async with self._lock:
            self._request_counts[key_index] += 1
    
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
        NVIDIA NIM 对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            model_id: 模型ID（可选，默认使用初始化时的model_name）
            
        Returns:
            ModelResponse对象
        """
        import time
        start_time = time.time()
        
        key_index, api_key = await self._get_next_key()
        await self._increment_request(key_index)
        
        target_model = model_id or self.model_name
        headers = {
            "Authorization": f"Bearer {api_key}",
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
                    # 标记key可能不健康
                    self._health_cache[key_index] = False
                    raise Exception(f"NVIDIA API error {resp.status}: {error_text}")
                
                data = await resp.json()
                latency_ms = int((time.time() - start_time) * 1000)
                
                return ModelResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=target_model,
                    provider=ModelProvider.NVIDIA,
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
        NVIDIA NIM 流式对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            model_id: 模型ID（可选）
            
        Yields:
            文本片段
        """
        import time
        start_time = time.time()
        
        key_index, api_key = await self._get_next_key()
        await self._increment_request(key_index)
        
        target_model = model_id or self.model_name
        headers = {
            "Authorization": f"Bearer {api_key}",
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
                        self._health_cache[key_index] = False
                        raise Exception(f"NVIDIA API error {resp.status}: {error_text}")
                    
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
                self._health_cache[key_index] = False
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
            return any(self._health_cache.values())
        
        self._last_health_check = current_time
        
        # 检查所有key
        for key_index, api_key in enumerate(self._api_keys):
            try:
                headers = {"Authorization": f"Bearer {api_key}"}
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/models",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        self._health_cache[key_index] = (resp.status == 200)
            except Exception:
                self._health_cache[key_index] = False
        
        return any(self._health_cache.values())
    
    async def discover_models(self) -> List[Dict]:
        """
        调用 /v1/models 接口获取可用模型列表
        
        Returns:
            模型信息列表
        """
        try:
            key_index, api_key = await self._get_next_key()
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    
                    models = []
                    for model in data.get("data", []):
                        models.append({
                            "id": model.get("id", ""),
                            "name": model.get("id", ""),
                            "context_length": model.get("context_length", 128000),
                            "description": model.get("description", ""),
                        })
                    return models
        except Exception:
            return []
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        
        Returns:
            模型ID列表
        """
        return list(NVIDIA_MODELS.keys())
    
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
            TaskType.CODING: "deepseek-ai/deepseek-coder-v2",
            TaskType.REASONING: "deepseek-ai/deepseek-v4-pro",
            TaskType.LONG_TEXT: "qwen/qwen3-next-80b-a3b-instruct",
            TaskType.GENERAL: "deepseek-ai/deepseek-v4-pro",
        }
        
        return task_model_map.get(task_type, "deepseek-ai/deepseek-v4-pro")
    
    def format_messages(self, messages: List[Message]) -> List[Dict]:
        """
        格式化消息为API格式
        """
        return [{"role": m.role, "content": m.content} for m in messages]
