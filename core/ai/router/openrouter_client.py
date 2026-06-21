"""
🌸 若曦V2 - OpenRouter客户端
支持23个免费模型的统一调用
"""
import aiohttp
import time
import random
from typing import AsyncGenerator, Dict, List, Optional

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider
from core.ai.router.route_config import (
    OPENROUTER_FREE_MODELS,
    ModelInfo,
    ProviderPriority,
    TaskType,
    get_models_for_task,
)


class OpenRouterClient(BaseModel):
    """
    OpenRouter API客户端
    
    支持23个免费模型的统一调用，包括:
    - DeepSeek V4 Flash
    - Kimi K2.6
    - Qwen3 系列
    - Llama 3.3 70B
    - Nemotron 120B
    - Gemma 4 31B
    - GLM-4.5 Air
    - 等等
    
    官网: https://openrouter.ai/
    API文档: https://openrouter.ai/docs
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    # 请求头标识
    DEFAULT_HEADERS = {
        "HTTP-Referer": "https://github.com/kunlunxingqiong/ruoxi-v2",
        "X-Title": "Ruoxi-V2 AI Assistant"
    }
    
    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = None,
        app_id: Optional[str] = None  # OpenRouter App ID (可选)
    ) -> None:
        """
        初始化OpenRouter客户端
        
        Args:
            api_key: OpenRouter API密钥
            model_name: 模型名称，默认使用 deepseek/deepseek-v4-flash:free
            app_id: OpenRouter应用ID (可选)
        """
        if model_name is None:
            model_name = "deepseek/deepseek-v4-flash:free"
        
        super().__init__(api_key, model_name, ModelProvider.OPENROUTER)
        self.base_url = self.BASE_URL
        self.app_id = app_id
        
        # 速率限制跟踪
        self._daily_requests: Dict[str, int] = {}  # model_id -> count
        self._daily_reset_timestamp: float = 0
        self._requests_this_minute: int = 0
        self._minute_reset_timestamp: float = 0
        
        # 健康状态跟踪
        self._health_status: Dict[str, bool] = {}
        self._consecutive_failures: Dict[str, int] = {}
    
    def _reset_daily_counts(self) -> None:
        """重置每日计数器"""
        current_time = time.time()
        if current_time >= self._daily_reset_timestamp:
            self._daily_requests.clear()
            # 重置到第二天 UTC 0点
            self._daily_reset_timestamp = self._get_next_utc_midnight()
    
    def _reset_minute_counts(self) -> None:
        """重置分钟计数器"""
        current_time = time.time()
        if current_time >= self._minute_reset_timestamp:
            self._requests_this_minute = 0
            self._minute_reset_timestamp = current_time + 60
    
    def _get_next_utc_midnight(self) -> float:
        """获取下一个UTC午夜时间戳"""
        now = time.time()
        # 距离下一个UTC午夜秒数
        seconds_until_midnight = 86400 - (now % 86400)
        return now + seconds_until_midnight
    
    def _check_rate_limit(self, model_id: str) -> bool:
        """
        检查速率限制
        
        Args:
            model_id: 模型ID
            
        Returns:
            是否可以继续请求
        """
        self._reset_daily_counts()
        self._reset_minute_counts()
        
        # 获取模型信息
        model_info = OPENROUTER_FREE_MODELS.get(model_id)
        if model_info is None:
            return True
        
        # 检查每日限制
        daily_count = self._daily_requests.get(model_id, 0)
        if model_info.daily_limit and daily_count >= model_info.daily_limit:
            return False
        
        # 检查每分钟限制
        if self._requests_this_minute >= model_info.rate_limit_rpm:
            return False
        
        return True
    
    def _increment_request_count(self, model_id: str) -> None:
        """增加请求计数"""
        self._reset_daily_counts()
        self._reset_minute_counts()
        
        self._daily_requests[model_id] = self._daily_requests.get(model_id, 0) + 1
        self._requests_this_minute += 1
    
    def select_model_for_task(self, task_type: TaskType) -> str:
        """
        根据任务类型选择最佳模型
        
        Args:
            task_type: 任务类型
            
        Returns:
            模型ID
        """
        models = get_models_for_task(task_type)
        
        # 过滤可用的免费模型
        available_models = [
            m for m in models
            if m.provider == ProviderPriority.OPENROUTER
            and self._check_rate_limit(m.model_id)
            and self._health_status.get(m.model_id, True)
        ]
        
        if not available_models:
            # 如果没有可用的，回退到默认模型
            return "deepseek/deepseek-v4-flash:free"
        
        # 随机选择一个（负载均衡）
        return random.choice(available_models).model_id
    
    def get_available_models(self) -> List[str]:
        """获取当前可用的模型列表"""
        self._reset_daily_counts()
        
        available = []
        for model_id, model_info in OPENROUTER_FREE_MODELS.items():
            if self._check_rate_limit(model_id):
                daily_count = self._daily_requests.get(model_id, 0)
                remaining = (model_info.daily_limit or 0) - daily_count
                if remaining > 0:
                    available.append(model_id)
        
        return available
    
    def get_model_info(self, model_id: Optional[str] = None) -> Optional[ModelInfo]:
        """获取模型信息"""
        if model_id is None:
            model_id = self.model_name
        return OPENROUTER_FREE_MODELS.get(model_id)
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> ModelResponse:
        """
        调用OpenRouter模型进行对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数 (0-1)
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            ModelResponse对象
        """
        start_time = time.time()
        
        # 检查速率限制
        if not self._check_rate_limit(self.model_name):
            raise Exception(f"Rate limit exceeded for model {self.model_name}")
        
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
            "Content-Type": "application/json",
            **self.DEFAULT_HEADERS
        }
        
        if self.app_id:
            headers["OpenRouter-App-Id"] = self.app_id
        
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
                        
                        # 更新健康状态
                        self._consecutive_failures[self.model_name] = \
                            self._consecutive_failures.get(self.model_name, 0) + 1
                        
                        if self._consecutive_failures[self.model_name] >= 3:
                            self._health_status[self.model_name] = False
                        
                        raise Exception(
                            f"OpenRouter API错误: {response.status} - {error_text}"
                        )
                    
                    result = await response.json()
                    
                    # 成功，重置失败计数
                    self._consecutive_failures[self.model_name] = 0
                    self._health_status[self.model_name] = True
                    
                    # 增加请求计数
                    self._increment_request_count(self.model_name)
                    
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
                    
        except aiohttp.ClientError as e:
            self._consecutive_failures[self.model_name] = \
                self._consecutive_failures.get(self.model_name, 0) + 1
            if self._consecutive_failures[self.model_name] >= 3:
                self._health_status[self.model_name] = False
            raise Exception(f"OpenRouter连接错误: {str(e)}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        OpenRouter流式输出
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            文本片段
        """
        if not self._check_rate_limit(self.model_name):
            raise Exception(f"Rate limit exceeded for model {self.model_name}")
        
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
            "Content-Type": "application/json",
            **self.DEFAULT_HEADERS
        }
        
        if self.app_id:
            headers["OpenRouter-App-Id"] = self.app_id
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"OpenRouter API错误: {response.status} - {error_text}"
                        )
                    
                    # 增加请求计数
                    self._increment_request_count(self.model_name)
                    
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
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                                
        except aiohttp.ClientError as e:
            raise Exception(f"OpenRouter连接错误: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        检查OpenRouter服务状态
        
        Returns:
            服务是否可用
        """
        try:
            url = f"{self.base_url}/models"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                **self.DEFAULT_HEADERS
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self._health_status[self.model_name] = True
                        return True
                    else:
                        self._health_status[self.model_name] = False
                        return False
                        
        except Exception:
            self._health_status[self.model_name] = False
            return False
    
    def get_info(self) -> Dict:
        """获取模型信息"""
        info = super().get_info()
        model_info = self.get_model_info()
        
        info.update({
            "rate_limit": "50-1000次/天（免费模型）",
            "available_models": list(OPENROUTER_FREE_MODELS.keys()),
            "features": ["text", "function_calling", "vision(部分模型)"],
            "auth_type": "Bearer Token",
            "cost": "部分模型免费",
            "daily_usage": self._daily_requests,
        })
        
        if model_info:
            info["description"] = model_info.description
            info["max_tokens"] = model_info.max_tokens
            info["context_window"] = model_info.context_window
        
        return info
    
    def get_usage_stats(self) -> Dict[str, Dict]:
        """获取使用统计"""
        self._reset_daily_counts()
        
        stats = {}
        for model_id, model_info in OPENROUTER_FREE_MODELS.items():
            count = self._daily_requests.get(model_id, 0)
            daily_limit = model_info.daily_limit or 0
            
            stats[model_id] = {
                "used_today": count,
                "daily_limit": daily_limit,
                "remaining": max(0, daily_limit - count),
                "usage_percent": (count / daily_limit * 100) if daily_limit > 0 else 0,
                "healthy": self._health_status.get(model_id, True),
            }
        
        return stats
