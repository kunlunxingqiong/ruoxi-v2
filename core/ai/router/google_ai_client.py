"""
🌸 若曦V2 - Google AI Studio客户端
支持Gemini系列模型调用
"""
import aiohttp
import time
from typing import AsyncGenerator, Dict, List, Optional, Union

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider
from core.ai.router.route_config import (
    GOOGLE_AI_MODELS,
    ModelInfo,
    ProviderPriority,
    TaskType,
)


class GoogleAIClient(BaseModel):
    """
    Google AI Studio (Gemini) API客户端
    
    免费额度:
    - Gemini 2.0 Flash: 每天150万token
    - Gemini 1.5 Flash: 每天150万token
    - Gemini 1.5 Pro: 每天500万token
    - Gemma 3: 每天150万token
    
    官网: https://aistudio.google.com/
    API文档: https://ai.google.dev/api/rest
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = None
    ) -> None:
        """
        初始化Google AI客户端
        
        Args:
            api_key: Google AI Studio API密钥
            model_name: 模型名称，默认使用 gemini-1.5-flash
        """
        if model_name is None:
            model_name = "gemini-1.5-flash"
        
        super().__init__(api_key, model_name, ModelProvider.GEMINI)
        self.base_url = self.BASE_URL
        
        # 速率限制跟踪
        self._daily_token_usage: int = 0
        self._daily_reset_timestamp: float = 0
        self._requests_this_minute: int = 0
        self._minute_reset_timestamp: float = 0
        
        # 健康状态跟踪
        self._health_status: bool = True
        self._consecutive_failures: int = 0
    
    def _reset_daily_counts(self) -> None:
        """重置每日计数器"""
        current_time = time.time()
        if current_time >= self._daily_reset_timestamp:
            self._daily_token_usage = 0
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
        seconds_until_midnight = 86400 - (now % 86400)
        return now + seconds_until_midnight
    
    def _check_rate_limit(
        self,
        estimated_tokens: int = 0,
        model_id: Optional[str] = None
    ) -> bool:
        """
        检查速率限制
        
        Args:
            estimated_tokens: 预估使用的token数
            model_id: 模型ID
            
        Returns:
            是否可以继续请求
        """
        self._reset_daily_counts()
        self._reset_minute_counts()
        
        if model_id is None:
            model_id = self.model_name
        
        model_info = GOOGLE_AI_MODELS.get(model_id)
        if model_info is None:
            return True
        
        # 检查每日token限制 (转换为字符粗略估算)
        # 1 token ≈ 4 字符
        estimated_chars = estimated_tokens * 4
        daily_limit_chars = (model_info.daily_limit or 1500000) * 4
        
        if self._daily_token_usage + estimated_chars > daily_limit_chars:
            return False
        
        # 检查每分钟限制
        if self._requests_this_minute >= model_info.rate_limit_rpm:
            return False
        
        return True
    
    def _increment_usage(self, token_count: int) -> None:
        """增加使用计数"""
        self._reset_daily_counts()
        self._reset_minute_counts()
        
        # 1 token ≈ 4 字符
        self._daily_token_usage += token_count * 4
        self._requests_this_minute += 1
    
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
            m for m in GOOGLE_AI_MODELS.values()
            if task_type in m.task_types
            and self._health_status
        ]
        
        if not models:
            return "gemini-1.5-flash"
        
        # 根据任务类型优先选择
        if task_type == TaskType.FAST_RESPONSE:
            return "gemini-2.0-flash-exp"
        elif task_type == TaskType.VISION:
            for m in models:
                if m.supports_vision:
                    return m.model_id
        elif task_type == TaskType.LONG_TEXT:
            for m in models:
                if m.context_window >= 1000000:
                    return m.model_id
        
        return models[0].model_id
    
    def get_available_models(self) -> List[str]:
        """获取当前可用的模型列表"""
        self._reset_daily_counts()
        
        available = []
        for model_id, model_info in GOOGLE_AI_MODELS.items():
            daily_limit_chars = (model_info.daily_limit or 1500000) * 4
            remaining_chars = daily_limit_chars - self._daily_token_usage
            
            if remaining_chars > 0:
                available.append(model_id)
        
        return available
    
    def get_model_info(self, model_id: Optional[str] = None) -> Optional[ModelInfo]:
        """获取模型信息"""
        if model_id is None:
            model_id = self.model_name
        return GOOGLE_AI_MODELS.get(model_id)
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 8192,
        stream: bool = False
    ) -> ModelResponse:
        """
        调用Gemini模型进行对话
        
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
            raise Exception("Rate limit exceeded for Google AI")
        
        # 转换消息格式
        contents = self._convert_messages(messages)
        
        url = (
            f"{self.base_url}/models/{self.model_name}:generateContent"
            f"?key={self.api_key}"
        )
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                if stream:
                    payload["stream"] = True
                    url = (
                        f"{self.base_url}/models/{self.model_name}:streamGenerateContent"
                        f"?key={self.api_key}&alt=sse"
                    )
                
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        
                        self._consecutive_failures += 1
                        if self._consecutive_failures >= 3:
                            self._health_status = False
                        
                        raise Exception(
                            f"Google AI API错误: {response.status} - {error_text}"
                        )
                    
                    # 成功
                    self._consecutive_failures = 0
                    self._health_status = True
                    
                    result = await response.json()
                    
                    # 解析响应
                    if stream:
                        content = ""
                        usage = {}
                        for item in result:
                            if "candidates" in item:
                                candidate = item["candidates"][0]
                                if "content" in candidate:
                                    parts = candidate["content"].get("parts", [])
                                    for part in parts:
                                        if "text" in part:
                                            content += part["text"]
                                if "usageMetadata" in item:
                                    usage = item["usageMetadata"]
                    else:
                        candidate = result["candidates"][0]
                        parts = candidate["content"]["parts"]
                        content = "".join(p.get("text", "") for p in parts)
                        usage = result.get("usageMetadata", {})
                    
                    # 估算实际使用的token
                    tokens_used = usage.get("totalTokenCount", len(content) // 4)
                    self._increment_usage(tokens_used)
                    
                    latency = int((time.time() - start_time) * 1000)
                    
                    return ModelResponse(
                        content=content,
                        model=self.model_name,
                        provider=self.provider,
                        usage=usage,
                        latency_ms=latency
                    )
                    
        except aiohttp.ClientError as e:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                self._health_status = False
            raise Exception(f"Google AI连接错误: {str(e)}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 8192
    ) -> AsyncGenerator[str, None]:
        """
        Gemini流式输出
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            文本片段
        """
        estimated_tokens = sum(len(m.content) // 4 for m in messages) + max_tokens
        if not self._check_rate_limit(estimated_tokens):
            raise Exception("Rate limit exceeded for Google AI")
        
        contents = self._convert_messages(messages)
        
        url = (
            f"{self.base_url}/models/{self.model_name}:streamGenerateContent"
            f"?key={self.api_key}&alt=sse"
        )
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Google AI API错误: {response.status} - {error_text}"
                        )
                    
                    self._increment_usage(max_tokens)
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data:'):
                            try:
                                import json
                                data = json.loads(line[5:].strip())
                                if "candidates" in data:
                                    candidate = data["candidates"][0]
                                    if "content" in candidate:
                                        parts = candidate["content"].get("parts", [])
                                        for part in parts:
                                            if "text" in part:
                                                yield part["text"]
                            except json.JSONDecodeError:
                                continue
                                
        except aiohttp.ClientError as e:
            raise Exception(f"Google AI连接错误: {str(e)}")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """
        转换消息格式为Gemini格式
        
        Args:
            messages: 消息列表
            
        Returns:
            Gemini格式的contents
        """
        contents = []
        
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            
            content: Dict[str, Union[str, List]] = {
                "role": role,
                "parts": [{"text": msg.content}]
            }
            contents.append(content)
        
        return contents
    
    async def health_check(self) -> bool:
        """
        检查Google AI服务状态
        
        Returns:
            服务是否可用
        """
        try:
            url = (
                f"{self.base_url}/models?key={self.api_key}"
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
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
        
        self._reset_daily_counts()
        
        info.update({
            "rate_limit": "每天150万-500万token",
            "available_models": list(GOOGLE_AI_MODELS.keys()),
            "features": ["text", "vision", "function_calling"],
            "auth_type": "API Key",
            "cost": "免费",
            "daily_usage_chars": self._daily_token_usage,
        })
        
        if model_info:
            info["description"] = model_info.description
            info["max_tokens"] = model_info.max_tokens
            info["context_window"] = model_info.context_window
            info["supports_vision"] = model_info.supports_vision
        
        return info
    
    def get_usage_stats(self) -> Dict:
        """获取使用统计"""
        self._reset_daily_counts()
        
        stats = {}
        for model_id, model_info in GOOGLE_AI_MODELS.items():
            daily_limit_chars = (model_info.daily_limit or 1500000) * 4
            
            stats[model_id] = {
                "description": model_info.description,
                "daily_limit_chars": daily_limit_chars,
                "used_chars": self._daily_token_usage if model_id == self.model_name else 0,
                "remaining_chars": max(0, daily_limit_chars - self._daily_token_usage),
                "usage_percent": (
                    self._daily_token_usage / daily_limit_chars * 100
                    if model_id == self.model_name and daily_limit_chars > 0 else 0
                ),
                "healthy": self._health_status,
            }
        
        return stats
