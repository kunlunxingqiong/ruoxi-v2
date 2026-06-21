"""
🌸 若曦V2 - 多模型路由器
智能路由、负载均衡、故障转移、成本优化
"""
import asyncio
import os
import time
import random
from typing import AsyncGenerator, Dict, List, Optional, Set, Callable

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider
from core.ai.router.route_config import (
    RouteConfig,
    DEFAULT_ROUTE_CONFIG,
    TaskType,
    ProviderPriority,
    ModelInfo,
    ALL_MODELS,
    get_models_for_task,
    OPENROUTER_FREE_MODELS,
    GOOGLE_AI_MODELS,
    GROQ_MODELS,
    CLOUDFLARE_MODELS,
)
from core.ai.router.openrouter_client import OpenRouterClient
from core.ai.router.google_ai_client import GoogleAIClient
from core.ai.router.groq_client import GroqClient


class HealthStatus:
    """Provider健康状态"""
    
    def __init__(self) -> None:
        self._status: Dict[ProviderPriority, bool] = {}
        self._consecutive_failures: Dict[ProviderPriority, int] = {}
        self._last_check: Dict[ProviderPriority, float] = {}
    
    def set_healthy(self, provider: ProviderPriority, healthy: bool) -> None:
        """设置健康状态"""
        self._status[provider] = healthy
        if healthy:
            self._consecutive_failures[provider] = 0
        else:
            self._consecutive_failures[provider] = \
                self._consecutive_failures.get(provider, 0) + 1
        self._last_check[provider] = time.time()
    
    def is_healthy(self, provider: ProviderPriority) -> bool:
        """检查是否健康"""
        return self._status.get(provider, True)
    
    def should_skip(self, provider: ProviderPriority, threshold: int = 3) -> bool:
        """是否应该跳过（连续失败过多）"""
        return self._consecutive_failures.get(provider, 0) >= threshold
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "status": {p.value: s for p, s in self._status.items()},
            "consecutive_failures": {p.value: f for p, f in self._consecutive_failures.items()},
            "last_check": {p.value: t for p, t in self._last_check.items()},
        }


class ModelRouter:
    """
    多模型智能路由器
    
    核心功能:
    - Fallback降级链: OpenRouter → Google → Groq → Cloudflare → 付费API
    - 负载均衡: 同优先级内轮询/随机
    - 成本优化: 优先免费模型，统计每日调用
    - 健康检查: 定期检测Provider可用性
    - 智能路由: 根据任务类型自动选模型
    - 速率限制: 跟踪每个Provider调用计数
    """
    
    def __init__(
        self,
        config: Optional[RouteConfig] = None,
        openrouter_key: Optional[str] = None,
        google_ai_key: Optional[str] = None,
        groq_key: Optional[str] = None,
        cloudflare_account_id: Optional[str] = None,
        cloudflare_api_token: Optional[str] = None,
    ) -> None:
        """
        初始化路由器
        
        Args:
            config: 路由配置
            openrouter_key: OpenRouter API密钥
            google_ai_key: Google AI API密钥
            groq_key: Groq API密钥
            cloudflare_account_id: Cloudflare账户ID
            cloudflare_api_token: Cloudflare API Token
        """
        self.config = config or DEFAULT_ROUTE_CONFIG
        
        # 初始化客户端
        self._clients: Dict[ProviderPriority, BaseModel] = {}
        
        # OpenRouter客户端
        if openrouter_key:
            self._clients[ProviderPriority.OPENROUTER] = OpenRouterClient(
                api_key=openrouter_key,
                app_id=os.getenv("OPENROUTER_APP_ID")
            )
        
        # Google AI客户端
        if google_ai_key:
            self._clients[ProviderPriority.GOOGLE_AI] = GoogleAIClient(
                api_key=google_ai_key
            )
        
        # Groq客户端
        if groq_key:
            self._clients[ProviderPriority.GROQ] = GroqClient(
                api_key=groq_key
            )
        
        # Cloudflare客户端（单独处理）
        self._cloudflare_account_id = cloudflare_account_id
        self._cloudflare_api_token = cloudflare_api_token
        
        # 健康状态
        self._health_status = HealthStatus()
        
        # 每日调用统计
        self._daily_stats: Dict[str, int] = {}  # model_id -> count
        self._daily_reset_timestamp: float = 0
        
        # 负载均衡索引
        self._round_robin_index: Dict[ProviderPriority, int] = {}
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 初始化时检查所有Provider
        asyncio.create_task(self._initial_health_check())
    
    async def _initial_health_check(self) -> None:
        """初始健康检查"""
        await self.check_all_providers()
    
    def _reset_daily_stats(self) -> None:
        """重置每日统计"""
        current_time = time.time()
        if current_time >= self._daily_reset_timestamp:
            self._daily_stats.clear()
            self._daily_reset_timestamp = self._get_next_utc_midnight()
    
    def _get_next_utc_midnight(self) -> float:
        """获取下一个UTC午夜时间戳"""
        now = time.time()
        seconds_until_midnight = 86400 - (now % 86400)
        return now + seconds_until_midnight
    
    async def check_all_providers(self) -> Dict[ProviderPriority, bool]:
        """
        检查所有Provider的健康状态
        
        Returns:
            Provider健康状态字典
        """
        tasks = []
        providers = list(self._clients.keys())
        
        for provider in providers:
            tasks.append(self._check_provider_health(provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        status = {}
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                status[provider] = False
            else:
                status[provider] = result
        
        return status
    
    async def _check_provider_health(
        self,
        provider: ProviderPriority
    ) -> bool:
        """检查单个Provider健康状态"""
        client = self._clients.get(provider)
        if client is None:
            return False
        
        try:
            is_healthy = await asyncio.wait_for(
                client.health_check(),
                timeout=self.config.health_check_timeout
            )
            self._health_status.set_healthy(provider, is_healthy)
            return is_healthy
        except asyncio.TimeoutError:
            self._health_status.set_healthy(provider, False)
            return False
        except Exception:
            self._health_status.set_healthy(provider, False)
            return False
    
    def _get_fallback_chain(
        self,
        task_type: Optional[TaskType] = None
    ) -> List[ProviderPriority]:
        """
        获取降级链
        
        Args:
            task_type: 任务类型
            
        Returns:
            按优先级排序的Provider列表
        """
        if self.config.enable_free_first:
            # 优先免费模型
            chain = [
                ProviderPriority.OPENROUTER,
                ProviderPriority.GOOGLE_AI,
                ProviderPriority.GROQ,
                ProviderPriority.CLOUDFLARE,
                # 付费模型（最低优先级）
                ProviderPriority.SILICONFLOW,
                ProviderPriority.ZHIPU,
                ProviderPriority.MOONSHOT,
                ProviderPriority.DASHSCOPE,
                ProviderPriority.DEEPSEEK,
            ]
        else:
            # 按可用性排序
            chain = [
                ProviderPriority.OPENROUTER,
                ProviderPriority.GOOGLE_AI,
                ProviderPriority.GROQ,
                ProviderPriority.CLOUDFLARE,
                ProviderPriority.SILICONFLOW,
                ProviderPriority.ZHIPU,
                ProviderPriority.MOONSHOT,
                ProviderPriority.DASHSCOPE,
                ProviderPriority.DEEPSEEK,
            ]
        
        # 过滤掉没有客户端的Provider
        return [p for p in chain if p in self._clients or p != ProviderPriority.CLOUDFLARE]
    
    def _select_model_for_provider(
        self,
        provider: ProviderPriority,
        task_type: Optional[TaskType] = None
    ) -> Optional[str]:
        """
        为Provider选择模型
        
        Args:
            provider: Provider类型
            task_type: 任务类型
            
        Returns:
            模型ID或None
        """
        client = self._clients.get(provider)
        if client is None:
            return None
        
        # 如果客户端有select_model_for_task方法，使用它
        if hasattr(client, "select_model_for_task"):
            return client.select_model_for_task(task_type or TaskType.GENERAL)
        
        # 否则返回默认模型
        return client.model_name
    
    async def chat(
        self,
        messages: List[Message],
        task_type: Optional[TaskType] = None,
        preferred_provider: Optional[ProviderPriority] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
        **kwargs
    ) -> ModelResponse:
        """
        智能路由对话
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            preferred_provider: 优先使用的Provider
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            ModelResponse对象
        """
        self._reset_daily_stats()
        
        # 获取降级链
        fallback_chain = self._get_fallback_chain(task_type)
        
        # 如果指定了优先Provider，将其放到最前面
        if preferred_provider and preferred_provider in self._clients:
            fallback_chain.remove(preferred_provider)
            fallback_chain.insert(0, preferred_provider)
        
        last_error: Optional[Exception] = None
        
        for provider in fallback_chain:
            # 检查健康状态
            if self._health_status.should_skip(provider, self.config.unhealthy_threshold):
                continue
            
            # 获取客户端
            client = self._clients.get(provider)
            if client is None:
                continue
            
            # 选择模型
            model_id = self._select_model_for_provider(provider, task_type)
            if model_id is None:
                continue
            
            # 检查该模型的每日限制
            model_info = ALL_MODELS.get(model_id)
            if model_info and model_info.daily_limit:
                daily_count = self._daily_stats.get(model_id, 0)
                if daily_count >= model_info.daily_limit:
                    continue
            
            try:
                # 尝试调用
                response = await self._call_with_timeout(
                    client.chat(
                        messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=stream,
                        **kwargs
                    ),
                    timeout=self.config.request_timeout if not stream else self.config.stream_timeout
                )
                
                # 成功，更新统计
                self._daily_stats[model_id] = self._daily_stats.get(model_id, 0) + 1
                self._health_status.set_healthy(provider, True)
                
                return response
                
            except Exception as e:
                last_error = e
                print(f"Provider {provider.value} 调用失败: {e}")
                
                # 标记Provider可能不健康
                self._health_status.set_healthy(provider, False)
                
                # 如果禁用fallback，直接抛出错误
                if not self.config.enable_provider_fallback:
                    raise
        
        # 所有Provider都失败
        raise Exception(f"所有Provider调用失败: {last_error}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        task_type: Optional[TaskType] = None,
        preferred_provider: Optional[ProviderPriority] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        智能路由流式对话
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            preferred_provider: 优先使用的Provider
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            文本片段
        """
        self._reset_daily_stats()
        
        fallback_chain = self._get_fallback_chain(task_type)
        
        if preferred_provider and preferred_provider in self._clients:
            fallback_chain.remove(preferred_provider)
            fallback_chain.insert(0, preferred_provider)
        
        last_error: Optional[Exception] = None
        
        for provider in fallback_chain:
            if self._health_status.should_skip(provider, self.config.unhealthy_threshold):
                continue
            
            client = self._clients.get(provider)
            if client is None:
                continue
            
            model_id = self._select_model_for_provider(provider, task_type)
            if model_id is None:
                continue
            
            model_info = ALL_MODELS.get(model_id)
            if model_info and model_info.daily_limit:
                daily_count = self._daily_stats.get(model_id, 0)
                if daily_count >= model_info.daily_limit:
                    continue
            
            try:
                self._daily_stats[model_id] = self._daily_stats.get(model_id, 0) + 1
                self._health_status.set_healthy(provider, True)
                
                async for chunk in client.chat_stream(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                ):
                    yield chunk
                
                return
                
            except Exception as e:
                last_error = e
                print(f"Provider {provider.value} 流式调用失败: {e}")
                self._health_status.set_healthy(provider, False)
                
                if not self.config.enable_provider_fallback:
                    raise
        
        raise Exception(f"所有Provider流式调用失败: {last_error}")
    
    async def _call_with_timeout(
        self,
        coro,
        timeout: float
    ) -> ModelResponse:
        """带超时的调用"""
        return await asyncio.wait_for(coro, timeout=timeout)
    
    def get_stats(self) -> Dict:
        """获取路由器统计"""
        self._reset_daily_stats()
        
        return {
            "config": {
                "enable_free_first": self.config.enable_free_first,
                "enable_provider_fallback": self.config.enable_provider_fallback,
                "health_check_interval": self.config.health_check_interval,
            },
            "providers": {
                "enabled": [p.value for p in self._clients.keys()],
                "health": self._health_status.get_stats(),
            },
            "daily_usage": self._daily_stats,
            "round_robin_index": {p.value: i for p, i in self._round_robin_index.items()},
        }
    
    def get_available_models(
        self,
        task_type: Optional[TaskType] = None
    ) -> Dict[ProviderPriority, List[str]]:
        """获取所有可用模型"""
        available = {}
        
        for provider, client in self._clients.items():
            if hasattr(client, "get_available_models"):
                models = client.get_available_models()
                if models:
                    available[provider] = models
        
        return available
    
    def get_usage_report(self) -> Dict:
        """获取使用报告"""
        self._reset_daily_stats()
        
        report = {
            "summary": {
                "total_calls": sum(self._daily_stats.values()),
                "models_used": len(self._daily_stats),
            },
            "by_model": {},
            "by_provider": {},
        }
        
        for model_id, count in self._daily_stats.items():
            model_info = ALL_MODELS.get(model_id)
            if model_info:
                report["by_model"][model_id] = {
                    "count": count,
                    "limit": model_info.daily_limit,
                    "usage_percent": (
                        count / model_info.daily_limit * 100
                        if model_info.daily_limit else 0
                    ),
                    "provider": model_info.provider.value,
                }
                
                provider = model_info.provider
                if provider.value not in report["by_provider"]:
                    report["by_provider"][provider.value] = 0
                report["by_provider"][provider.value] += count
        
        return report


# 全局路由器实例
_router_instance: Optional[ModelRouter] = None


def get_router(
    openrouter_key: Optional[str] = None,
    google_ai_key: Optional[str] = None,
    groq_key: Optional[str] = None,
    config: Optional[RouteConfig] = None,
) -> ModelRouter:
    """
    获取路由器单例
    
    Args:
        openrouter_key: OpenRouter API密钥
        google_ai_key: Google AI API密钥
        groq_key: Groq API密钥
        config: 路由配置
        
    Returns:
        ModelRouter实例
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = ModelRouter(
            config=config,
            openrouter_key=openrouter_key or os.getenv("OPENROUTER_API_KEY"),
            google_ai_key=google_ai_key or os.getenv("GOOGLE_AI_API_KEY"),
            groq_key=groq_key or os.getenv("GROQ_API_KEY"),
            cloudflare_account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID"),
            cloudflare_api_token=os.getenv("CLOUDFLARE_API_TOKEN"),
        )
    
    return _router_instance


def reset_router() -> None:
    """重置路由器实例"""
    global _router_instance
    _router_instance = None
