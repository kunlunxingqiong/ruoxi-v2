"""
🌸 若曦V2 - Groq客户端
支持超快推理模型调用
"""
import aiohttp
import time
import random
from typing import AsyncGenerator, Dict, List, Optional

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider
from core.ai.router.route_config import (
    GROQ_MODELS,
    ModelInfo,
    ProviderPriority,
    TaskType,
)


class GroqClient(BaseModel):
    """
    Groq API客户端
    
    特点: 超快推理速度，免费额度充足
    
    免费模型:
    - llama-3.3-70b-versatile: 128K上下文
    - llama-3.1-8b-instant: 128K上下文
    - mixtral-8x7b-32768: 32K上下文
    - gemma2-9b-it: 8K上下文
    
    官网: https://console.groq.com/
    API文档: https://console.groq.com/docs
    """
    
    BASE_URL = "https://api.groq.com/openai/v1"
    
    # 免费层速率限制
    FREE_RATE_LIMIT_RPM = 30        # 每分钟30请求
    FREE_RATE_LIMIT_TPM = 15000      # 每分钟15000 tokens
    
    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = None
    ) -> None:
        """
        初始化Groq客户端
        
        Args:
            api_key: Groq API密钥
            model_name: 模型名称，默认使用 llama-3.3-70b-versatile
        """
        if model_name is None:
            model_name = "llama-3.3-70b-versatile"
        
        super().__init__(api_key, model_name, ModelProvider.GROQ)
        self.base_url = self.BASE_URL
        
        # 速率限制跟踪
        self._requests_this_minute: int = 0
        self._tokens_this_minute: int = 0
        self._minute_reset_timestamp: float = 0
        
        # 健康状态跟踪
        self._health_status: bool = True
        self._consecutive_failures: int = 0
        
        # 负载均衡索引
        self._round_robin_index: int = 0
    
    def _reset_minute_counts(self) -> None:
        """重置分钟计数器"""
        current_time = time.time()
        if current_time >= self._minute_reset_timestamp:
            self._requests_this_minute = 0
            self._tokens_this_minute = 0
            self._minute_reset_timestamp = current_time + 60
    
    def _check_rate_limit(
        self,
        estimated_tokens: int = 0
    ) -> bool:
        """
        检查速率限制
        
        Args:
            estimated_tokens: 预估使用的token数
            
        Returns:
            是否可以继续请求
        """
        self._reset_minute_counts()
        
        # 检查每分钟请求限制
        if self._requests_this_minute >= self.FREE_RATE_LIMIT_RPM:
            return False
        
        # 检查每分钟token限制
        if self._tokens_this_minute + estimated_tokens > self.FREE_RATE_LIMIT_TPM:
            return False
        
        return True
    
    def _increment_usage(self, token_count: int) -> None:
        """增加使用计数"""
        self._reset_minute_counts()
        self._requests_this_minute += 1
        self._tokens_this_minute += token_count
    
    def select_model_for_task(self, task_type: TaskType) -> str:
        """
        根据任务类型选择最佳模型
        
        Args:
            task_type: 任务类型
            
        Returns:
            模型名称
        """
        # 获取适合任务的模型
        models = [
            m for m in GROQ_MODELS.values()
            if task_type in m.task_types
            and self._health_status
        ]
        
        if not models:
            return "llama-3.3-70b-versatile"
        
        # 根据任务类型优先选择
        if task_type == TaskType.CODING:
            for m in models:
                if "mixtral" in m.model_id or "llama-3.3" in m.model_id:
                    return m.model_id
        elif task_type == TaskType.FAST_RESPONSE:
            for m in models:
                if "8b" in m.model_id or "gemma" in m.model_id:
                    return m.model_id
        
        return models[0].model_id
    
    def get_available_models(self) -> List[str]:
        """获取当前可用的模型列表"""
        self._reset_minute_counts()
        
        available = []
        for model_id in GROQ_MODELS.keys():
            if self._check_rate_limit(1000):  # 假设每次1000 tokens
                available.append(model_id)
        
        return available
    
    def get_model_info(self, model_id: Optional[str] = None) -> Optional[ModelInfo]:
        """获取模型信息"""
        if model_id is None:
            model_id = self.model_name
        return GROQ_MODELS.get(model_id)
    
    async def discover_models(self) -> List[Dict]:
        """
        调用 /v1/models 接口获取可用模型列表
        
        Returns:
            模型信息列表
        """
        try:
            url = f"{self.base_url}/models"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
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
                            "context_length": model.get("context_window", 8192),
                            "description": model.get("name", ""),
                        })
                    return models
        except Exception:
            return []
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> ModelResponse:
        """
        调用Groq模型进行对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数 (0-1)
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            ModelResponse对象
        """
        start_time = time.time()
        
        # 预估token使用量
        estimated_tokens = sum(len(m.content) // 4 for m in messages) + max_tokens
        if not self._check_rate_limit(estimated_tokens):
            raise Exception("Rate limit exceeded for Groq")
        
        formatted_messages = self._format_messages(messages)
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        
                        self._consecutive_failures += 1
                        if self._consecutive_failures >= 3:
                            self._health_status = False
                        
                        raise Exception(
                            f"Groq API错误: {response.status} - {error_text}"
                        )
                    
                    # 成功
                    self._consecutive_failures = 0
                    self._health_status = True
                    
                    result = await response.json()
                    
                    content = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    model_used = result.get("model", self.model_name)
                    
                    # 更新使用统计
                    tokens_used = usage.get("total_tokens", max_tokens)
                    self._increment_usage(tokens_used)
                    
                    latency = int((time.time() - start_time) * 1000)
                    
                    return ModelResponse(
                        content=content,
                        model=model_used,
                        provider=self.provider,
                        usage=usage,
                        latency_ms=latency
                    )
                    
        except aiohttp.ClientError as e:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self._health_status = False
            raise Exception(f"Groq连接错误: {str(e)}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Groq流式输出
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            文本片段
        """
        estimated_tokens = sum(len(m.content) // 4 for m in messages) + max_tokens
        if not self._check_rate_limit(estimated_tokens):
            raise Exception("Rate limit exceeded for Groq")
        
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
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Groq API错误: {response.status} - {error_text}"
                        )
                    
                    total_tokens = 0
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if not line or line.startswith(':') or line == 'data: [DONE]':
                            continue
                        
                        if line.startswith('data:'):
                            try:
                                import json
                                data = json.loads(line[5:].strip())
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        content = delta["content"]
                                        total_tokens += len(content) // 4
                                        yield content
                                        
                                if "usage" in data:
                                    total_tokens = data["usage"].get("total_tokens", total_tokens)
                            except json.JSONDecodeError:
                                continue
                    
                    self._increment_usage(total_tokens)
                                
        except aiohttp.ClientError as e:
            raise Exception(f"Groq连接错误: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        检查Groq服务状态
        
        Returns:
            服务是否可用
        """
        try:
            url = f"{self.base_url}/models"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self._health_status = True
                        return True
                    else:
                        self._health_status = False
                        return False
                        
        except Exception:
            self._health_status = False
            return False
    
    def get_info(self) -> Dict:
        """获取模型信息"""
        info = super().get_info()
        model_info = self.get_model_info()
        
        self._reset_minute_counts()
        
        info.update({
            "rate_limit": f"{self.FREE_RATE_LIMIT_RPM} RPM / {self.FREE_RATE_LIMIT_TPM} TPM",
            "available_models": list(GROQ_MODELS.keys()),
            "features": ["text", "超快推理"],
            "auth_type": "Bearer Token",
            "cost": "免费",
            "minute_usage": {
                "requests": self._requests_this_minute,
                "tokens": self._tokens_this_minute,
            },
        })
        
        if model_info:
            info["description"] = model_info.description
            info["max_tokens"] = model_info.max_tokens
            info["context_window"] = model_info.context_window
        
        return info
    
    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        self._reset_minute_counts()
        
        stats = {
            "rate_limit": {
                "rpm": self.FREE_RATE_LIMIT_RPM,
                "tpm": self.FREE_RATE_LIMIT_TPM,
            },
            "current_minute": {
                "requests": self._requests_this_minute,
                "tokens": self._tokens_this_minute,
                "rpm_remaining": self.FREE_RATE_LIMIT_RPM - self._requests_this_minute,
                "tpm_remaining": self.FREE_RATE_LIMIT_TPM - self._tokens_this_minute,
            },
            "models": {},
        }
        
        for model_id, model_info in GROQ_MODELS.items():
            stats["models"][model_id] = {
                "description": model_info.description,
                "healthy": self._health_status,
            }
        
        return stats
