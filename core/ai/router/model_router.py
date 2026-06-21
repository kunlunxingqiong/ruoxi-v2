"""
🌸 若曦V2 - 模型路由器 (角色匹配模式)

核心功能:
- 角色匹配路由: 根据团队成员角色自动选择对应模型
- 多级降级链: 主力模型 → 备用模型 → 全局fallback
- 支持角色: RUOXI(若曦), AFU(阿芙), RESEARCHER(小研), CODER(小码)
- 保留通用路由能力 (不指定角色时按任务类型路由)

更新日志:
- 2026-07-13: 角色匹配模式，NVIDIA NIM和硅基流动支持
"""
import asyncio
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, AsyncGenerator

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider
from core.ai.router.route_config import (
    AgentRole,
    ModelInfo,
    ProviderPriority,
    RouteConfig,
    TaskType,
    ROLE_MODEL_CONFIGS,
    get_role_config,
    get_default_role_chain,
    ALL_MODELS,
)


@dataclass
class RouteRequest:
    """路由请求"""
    messages: List[Message]
    agent_role: Optional[AgentRole] = None  # 角色（优先）
    task_type: Optional[TaskType] = None     # 任务类型（无角色时使用）
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False
    model_id: Optional[str] = None  # 强制指定模型


@dataclass
class RouteResult:
    """路由结果"""
    provider: ModelProvider
    model_id: str
    latency_ms: Optional[int] = None


class HealthStatus:
    """健康状态追踪"""
    
    def __init__(self):
        # provider -> 连续失败次数
        self._failures: Dict[ModelProvider, int] = {}
        # provider -> 是否健康
        self._healthy: Dict[ModelProvider, bool] = {}
    
    def record_success(self, provider: ModelProvider) -> None:
        """记录成功"""
        self._failures[provider] = 0
        self._healthy[provider] = True
    
    def record_failure(self, provider: ModelProvider) -> None:
        """记录失败"""
        current = self._failures.get(provider, 0)
        self._failures[provider] = current + 1
        # 连续失败3次标记为不健康
        if current + 1 >= 3:
            self._healthy[provider] = False
    
    def is_healthy(self, provider: ModelProvider, threshold: int = 3) -> bool:
        """检查是否健康"""
        if provider not in self._failures:
            return True
        return self._failures[provider] < threshold
    
    def reset(self, provider: Optional[ModelProvider] = None) -> None:
        """重置健康状态"""
        if provider:
            self._failures.pop(provider, None)
            self._healthy.pop(provider, None)
        else:
            self._failures.clear()
            self._healthy.clear()


class ModelRouter:
    """
    模型路由器 - 角色匹配模式
    
    核心路由逻辑:
    1. 如果指定了 agent_role → 使用角色配置的降级链
    2. 否则按 task_type → 使用通用降级链
    
    降级链规则:
    - 主力模型失败 → 备用模型
    - 备用模型失败 → 全局fallback
    - 全局fallback失败 → 返回错误
    """
    
    def __init__(
        self,
        config: Optional[RouteConfig] = None,
        nvidia_key: Optional[str] = None,
        nvidia_key_2: Optional[str] = None,
        siliconflow_key: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        google_ai_key: Optional[str] = None,
        groq_key: Optional[str] = None,
    ) -> None:
        """
        初始化路由器
        
        Args:
            config: 路由配置
            nvidia_key: NVIDIA NIM API密钥
            nvidia_key_2: NVIDIA NIM 备用密钥
            siliconflow_key: 硅基流动 API密钥
            openrouter_key: OpenRouter API密钥
            google_ai_key: Google AI API密钥
            groq_key: Groq API密钥
        """
        self.config = config or RouteConfig()
        self._clients: Dict[ModelProvider, BaseModel] = {}
        self._health_status = HealthStatus()
        
        # 初始化客户端
        self._init_nvidia_client(nvidia_key, nvidia_key_2)
        self._init_siliconflow_client(siliconflow_key)
        self._init_openrouter_client(openrouter_key)
        self._init_google_ai_client(google_ai_key)
        self._init_groq_client(groq_key)
    
    def _init_nvidia_client(self, key: Optional[str], key_2: Optional[str]) -> None:
        """初始化NVIDIA客户端"""
        key = key or os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_NIM_API_KEY")
        key_2 = key_2 or os.getenv("NVIDIA_API_KEY_2")
        
        if key or key_2:
            try:
                from core.ai.router.nvidia_client import NVIDIAClient
                self._clients[ModelProvider.NVIDIA] = NVIDIAClient(
                    api_key=key,
                    api_key_2=key_2,
                )
            except Exception as e:
                print(f"Failed to init NVIDIA client: {e}")
    
    def _init_siliconflow_client(self, key: Optional[str]) -> None:
        """初始化硅基流动客户端"""
        key = key or os.getenv("SILICONFLOW_KEY")
        
        if key:
            try:
                from core.ai.router.siliconflow_client import SiliconFlowClient
                self._clients[ModelProvider.SILICONFLOW] = SiliconFlowClient(api_key=key)
            except Exception as e:
                print(f"Failed to init SiliconFlow client: {e}")
    
    def _init_openrouter_client(self, key: Optional[str]) -> None:
        """初始化OpenRouter客户端"""
        key = key or os.getenv("OPENROUTER_API_KEY")
        
        if key:
            try:
                from core.ai.router.openrouter_client import OpenRouterClient
                self._clients[ModelProvider.OPENROUTER] = OpenRouterClient(api_key=key)
            except Exception as e:
                print(f"Failed to init OpenRouter client: {e}")
    
    def _init_google_ai_client(self, key: Optional[str]) -> None:
        """初始化Google AI客户端"""
        key = key or os.getenv("GOOGLE_AI_API_KEY")
        
        if key:
            try:
                from core.ai.router.google_ai_client import GoogleAIClient
                self._clients[ModelProvider.GEMINI] = GoogleAIClient(api_key=key)
            except Exception as e:
                print(f"Failed to init Google AI client: {e}")
    
    def _init_groq_client(self, key: Optional[str]) -> None:
        """初始化Groq客户端"""
        key = key or os.getenv("GROQ_API_KEY")
        
        if key:
            try:
                from core.ai.router.groq_client import GroqClient
                self._clients[ModelProvider.GROQ] = GroqClient(api_key=key)
            except Exception as e:
                print(f"Failed to init Groq client: {e}")
    
    def _get_role_fallback_chain(self, role: AgentRole) -> List[tuple]:
        """
        获取角色的降级链
        
        Args:
            role: 角色枚举
            
        Returns:
            [(provider, model_id), ...]
        """
        return get_default_role_chain(role)
    
    def _get_task_fallback_chain(self, task_type: Optional[TaskType]) -> List[tuple]:
        """
        获取任务类型的降级链
        
        Args:
            task_type: 任务类型
            
        Returns:
            [(provider, model_id), ...]
        """
        # 按优先级排序的降级链
        chain = [
            (ModelProvider.NVIDIA, "deepseek-ai/deepseek-v4-pro"),
            (ModelProvider.SILICONFLOW, "deepseek-ai/DeepSeek-V3"),
            (ModelProvider.OPENROUTER, "deepseek/deepseek-v4-flash:free"),
            (ModelProvider.GEMINI, "gemini-2.0-flash-exp"),
            (ModelProvider.GROQ, "llama-3.3-70b-specdec"),
        ]
        return chain
    
    async def chat(
        self,
        messages: List[Message],
        agent_role: Optional[AgentRole] = None,
        task_type: Optional[TaskType] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
        **kwargs
    ) -> ModelResponse:
        """
        智能路由对话
        
        Args:
            messages: 消息列表
            agent_role: 角色（优先）
            task_type: 任务类型（无角色时使用）
            model_id: 强制指定模型
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            ModelResponse对象
        """
        last_error: Optional[Exception] = None
        
        # 1. 如果指定了模型，直接使用
        if model_id:
            provider = self._guess_provider(model_id)
            client = self._clients.get(provider)
            if client:
                try:
                    return await client.chat(
                        messages, temperature, max_tokens, stream, model_id, **kwargs
                    )
                except Exception as e:
                    last_error = e
        
        # 2. 使用角色降级链
        if agent_role:
            chain = self._get_role_fallback_chain(agent_role)
            config = get_role_config(agent_role)
            role_display = config.display_name if config else agent_role.value
        else:
            # 3. 使用任务类型降级链
            chain = self._get_task_fallback_chain(task_type)
            role_display = "通用"
        
        print(f"[Router] {role_display}路由，降级链: {len(chain)}个Provider")
        
        for provider, fallback_model_id in chain:
            # 检查客户端是否存在
            client = self._clients.get(provider)
            if client is None:
                print(f"[Router] Provider {provider.value} 客户端未初始化，跳过")
                continue
            
            # 检查健康状态
            if not self._health_status.is_healthy(provider):
                print(f"[Router] Provider {provider.value} 健康检查失败，跳过")
                continue
            
            try:
                print(f"[Router] 尝试 {provider.value}/{fallback_model_id}")
                response = await client.chat(
                    messages, temperature, max_tokens, stream, fallback_model_id, **kwargs
                )
                self._health_status.record_success(provider)
                return response
                
            except Exception as e:
                print(f"[Router] Provider {provider.value} 失败: {e}")
                self._health_status.record_failure(provider)
                last_error = e
                continue
        
        raise Exception(f"所有Provider调用失败: {last_error}")
    
    async def chat_stream(
        self,
        messages: List[Message],
        agent_role: Optional[AgentRole] = None,
        task_type: Optional[TaskType] = None,
        model_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        智能路由流式对话
        
        Args:
            messages: 消息列表
            agent_role: 角色（优先）
            task_type: 任务类型（无角色时使用）
            model_id: 强制指定模型
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            文本片段
        """
        last_error: Optional[Exception] = None
        
        # 1. 如果指定了模型，直接使用
        if model_id:
            provider = self._guess_provider(model_id)
            client = self._clients.get(provider)
            if client:
                try:
                    async for chunk in client.chat_stream(
                        messages, temperature, max_tokens, model_id, **kwargs
                    ):
                        yield chunk
                    return
                except Exception as e:
                    last_error = e
        
        # 2. 使用角色降级链
        if agent_role:
            chain = self._get_role_fallback_chain(agent_role)
            config = get_role_config(agent_role)
            role_display = config.display_name if config else agent_role.value
        else:
            chain = self._get_task_fallback_chain(task_type)
            role_display = "通用"
        
        for provider, fallback_model_id in chain:
            client = self._clients.get(provider)
            if client is None:
                continue
            
            if not self._health_status.is_healthy(provider):
                continue
            
            try:
                async for chunk in client.chat_stream(
                    messages, temperature, max_tokens, fallback_model_id, **kwargs
                ):
                    yield chunk
                self._health_status.record_success(provider)
                return
                
            except Exception as e:
                last_error = e
                self._health_status.record_failure(provider)
                continue
        
        raise Exception(f"所有Provider流式调用失败: {last_error}")
    
    def _guess_provider(self, model_id: str) -> ModelProvider:
        """根据模型ID猜测Provider"""
        model_lower = model_id.lower()
        
        if "deepseek" in model_lower or "nvidia" in model_lower or "qwen3" in model_lower:
            if "nvidia" in model_lower:
                return ModelProvider.NVIDIA
            return ModelProvider.SILICONFLOW
        if "qwen" in model_lower or "glm" in model_lower:
            return ModelProvider.SILICONFLOW
        if "kimi" in model_lower or "moonshot" in model_lower:
            return ModelProvider.MOONSHOT
        if "gemini" in model_lower:
            return ModelProvider.GEMINI
        if "groq" in model_lower or "llama" in model_lower:
            return ModelProvider.GROQ
        
        return ModelProvider.OPENROUTER
    
    def get_stats(self) -> Dict:
        """获取路由器统计"""
        return {
            "providers": {
                "enabled": [p.value for p in self._clients.keys()],
                "health": {
                    p.value: self._health_status.is_healthy(p)
                    for p in self._clients.keys()
                },
            },
            "roles": {
                role.value: {
                    "display": config.display_name,
                    "primary": config.primary_model,
                    "fallback": config.fallback_model,
                }
                for role, config in ROLE_MODEL_CONFIGS.items()
            }
        }
    
    def list_clients(self) -> List[ModelProvider]:
        """列出已初始化的客户端"""
        return list(self._clients.keys())


# 全局路由器实例
_router_instance: Optional[ModelRouter] = None


def get_router(
    nvidia_key: Optional[str] = None,
    nvidia_key_2: Optional[str] = None,
    siliconflow_key: Optional[str] = None,
    openrouter_key: Optional[str] = None,
    google_ai_key: Optional[str] = None,
    groq_key: Optional[str] = None,
) -> ModelRouter:
    """
    获取路由器单例
    
    Args:
        nvidia_key: NVIDIA NIM API密钥
        nvidia_key_2: NVIDIA NIM 备用密钥
        siliconflow_key: 硅基流动 API密钥
        openrouter_key: OpenRouter API密钥
        google_ai_key: Google AI API密钥
        groq_key: Groq API密钥
        
    Returns:
        ModelRouter实例
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = ModelRouter(
            nvidia_key=nvidia_key,
            nvidia_key_2=nvidia_key_2,
            siliconflow_key=siliconflow_key,
            openrouter_key=openrouter_key,
            google_ai_key=google_ai_key,
            groq_key=groq_key,
        )
    
    return _router_instance


def reset_router() -> None:
    """重置路由器实例"""
    global _router_instance
    _router_instance = None
