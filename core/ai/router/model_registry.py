"""
🌸 若曦V2 - 模型注册中心

核心功能:
- 动态模型发现: 启动时调用各Provider的 discover_models() 填充模型池
- 静态核心模型: 保留 route_config.py 中的角色首选配置
- 智能匹配: 根据 task_type 和 agent_role 匹配最佳模型
- 全量查询: get_all_models(), get_models_by_provider()

更新日志:
- 2026-07-13: 初始版本，动态+静态双层注册
"""
import asyncio
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any

from core.ai.router.route_config import (
    AgentRole,
    ModelInfo,
    ProviderPriority,
    RoleModelConfig,
    TaskType,
    ROLE_MODEL_CONFIGS,
)


@dataclass
class DiscoveredModel:
    """动态发现的模型"""
    model_id: str
    provider: ProviderPriority
    provider_name: str
    name: str
    context_length: int = 128000
    description: str = ""
    is_free: bool = False
    supports_streaming: bool = True
    supports_vision: bool = False
    task_types: Set[TaskType] = field(default_factory=set)


class ModelRegistry:
    """
    模型注册中心
    
    实现动态+静态双层模型注册:
    1. 静态核心模型: 来自 ROLE_MODEL_CONFIGS 的角色首选模型配置
    2. 动态发现模型: 启动时从各Provider API获取的完整模型列表
    
    提供智能匹配接口:
    - get_model_for_task(): 根据任务类型获取最佳模型
    - get_all_models(): 获取全量模型
    - get_models_by_provider(): 按Provider查询
    """
    
    def __init__(self):
        """初始化模型注册中心"""
        # 静态核心模型 (角色首选配置)
        self._static_models: Dict[str, ModelInfo] = {}
        
        # 动态发现模型
        self._dynamic_models: Dict[str, DiscoveredModel] = {}
        
        # Provider客户端
        self._clients: Dict[ProviderPriority, Any] = {}
        
        # 初始化静态模型
        self._init_static_models()
    
    def _init_static_models(self) -> None:
        """初始化静态核心模型"""
        # 从角色配置中提取核心模型
        for role, config in ROLE_MODEL_CONFIGS.items():
            # 主力模型
            primary_info = ModelInfo(
                model_id=config.primary_model,
                provider=config.primary_provider,
                provider_name=self._get_provider_name(config.primary_provider),
                task_types=config.optimized_for,
                is_free=False,
                description=f"{config.display_name} 主力模型"
            )
            self._static_models[config.primary_model] = primary_info
            
            # 备用模型
            fallback_info = ModelInfo(
                model_id=config.fallback_model,
                provider=config.fallback_provider,
                provider_name=self._get_provider_name(config.fallback_provider),
                task_types=config.optimized_for,
                is_free=False,
                description=f"{config.display_name} 备用模型"
            )
            self._static_models[config.fallback_model] = fallback_info
            
            # 全局降级模型
            global_info = ModelInfo(
                model_id=config.global_fallback_model,
                provider=config.global_fallback_provider,
                provider_name=self._get_provider_name(config.global_fallback_provider),
                task_types=config.optimized_for,
                is_free=True,
                description=f"{config.display_name} 全局降级模型"
            )
            self._static_models[config.global_fallback_model] = global_info
    
    def _get_provider_name(self, provider: ProviderPriority) -> str:
        """获取Provider名称"""
        names = {
            ProviderPriority.NVIDIA: "NVIDIA NIM",
            ProviderPriority.SILICONFLOW: "硅基流动",
            ProviderPriority.OPENROUTER: "OpenRouter",
            ProviderPriority.GOOGLE_AI: "Google AI",
            ProviderPriority.GROQ: "Groq",
            ProviderPriority.CLOUDFLARE: "Cloudflare",
            ProviderPriority.ZHIPU: "智谱",
            ProviderPriority.MOONSHOT: "月之暗面",
            ProviderPriority.DASHSCOPE: "阿里百炼",
            ProviderPriority.DEEPSEEK: "DeepSeek",
        }
        return names.get(provider, provider.name)
    
    def register_client(self, provider: ProviderPriority, client: Any) -> None:
        """
        注册Provider客户端
        
        Args:
            provider: Provider优先级
            client: 客户端实例
        """
        self._clients[provider] = client
    
    async def discover_all_models(self) -> int:
        """
        从所有Provider发现模型
        
        Returns:
            发现的总模型数
        """
        tasks = []
        provider_map = {}
        
        # NVIDIA
        if ProviderPriority.NVIDIA in self._clients:
            client = self._clients[ProviderPriority.NVIDIA]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_nvidia(client))
                provider_map[id(tasks[-1])] = ProviderPriority.NVIDIA
        
        # 硅基流动
        if ProviderPriority.SILICONFLOW in self._clients:
            client = self._clients[ProviderPriority.SILICONFLOW]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_siliconflow(client))
                provider_map[id(tasks[-1])] = ProviderPriority.SILICONFLOW
        
        # OpenRouter
        if ProviderPriority.OPENROUTER in self._clients:
            client = self._clients[ProviderPriority.OPENROUTER]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_openrouter(client))
                provider_map[id(tasks[-1])] = ProviderPriority.OPENROUTER
        
        # Google AI
        if ProviderPriority.GOOGLE_AI in self._clients:
            client = self._clients[ProviderPriority.GOOGLE_AI]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_google_ai(client))
                provider_map[id(tasks[-1])] = ProviderPriority.GOOGLE_AI
        
        # Groq
        if ProviderPriority.GROQ in self._clients:
            client = self._clients[ProviderPriority.GROQ]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_groq(client))
                provider_map[id(tasks[-1])] = ProviderPriority.GROQ
        
        # 月之暗面
        if ProviderPriority.MOONSHOT in self._clients:
            client = self._clients[ProviderPriority.MOONSHOT]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_moonshot(client))
                provider_map[id(tasks[-1])] = ProviderPriority.MOONSHOT
        
        # 智谱
        if ProviderPriority.ZHIPU in self._clients:
            client = self._clients[ProviderPriority.ZHIPU]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_zhipu(client))
                provider_map[id(tasks[-1])] = ProviderPriority.ZHIPU
        
        # 阿里百炼
        if ProviderPriority.DASHSCOPE in self._clients:
            client = self._clients[ProviderPriority.DASHSCOPE]
            if hasattr(client, 'discover_models'):
                tasks.append(self._discover_dashscope(client))
                provider_map[id(tasks[-1])] = ProviderPriority.DASHSCOPE
        
        # Cloudflare (静态列表)
        if ProviderPriority.CLOUDFLARE in self._clients:
            self._discover_cloudflare(self._clients[ProviderPriority.CLOUDFLARE])
        
        # 并发执行所有发现任务
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print(f"[Registry] 模型发现失败: {result}")
        
        return len(self._dynamic_models)
    
    async def _discover_nvidia(self, client) -> None:
        """发现NVIDIA模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "")
            if model_id:
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.NVIDIA,
                    provider_name="NVIDIA NIM",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 64000),
                    description=m.get("description", ""),
                    is_free=False,
                )
    
    async def _discover_siliconflow(self, client) -> None:
        """发现硅基流动模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "")
            if model_id:
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.SILICONFLOW,
                    provider_name="硅基流动",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 128000),
                    description=m.get("description", ""),
                    is_free=False,
                )
    
    async def _discover_openrouter(self, client) -> None:
        """发现OpenRouter模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "")
            if model_id:
                pricing = m.get("pricing", {})
                is_free = pricing.get("prompt", "0") == "0" and pricing.get("completion", "0") == "0"
                
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.OPENROUTER,
                    provider_name="OpenRouter",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 128000),
                    description=m.get("description", ""),
                    is_free=is_free,
                )
    
    async def _discover_google_ai(self, client) -> None:
        """发现Google AI模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "").replace("models/", "")
            if model_id:
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.GOOGLE_AI,
                    provider_name="Google AI",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 1000000),
                    description=m.get("description", ""),
                    is_free=True,
                    supports_vision="vision" in model_id.lower(),
                )
    
    async def _discover_groq(self, client) -> None:
        """发现Groq模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "")
            if model_id:
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.GROQ,
                    provider_name="Groq",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 128000),
                    description=m.get("description", ""),
                    is_free=True,
                )
    
    async def _discover_moonshot(self, client) -> None:
        """发现月之暗面模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "")
            if model_id:
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.MOONSHOT,
                    provider_name="月之暗面",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 128000),
                    description=m.get("description", ""),
                    is_free=False,
                )
    
    async def _discover_zhipu(self, client) -> None:
        """发现智谱模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "")
            if model_id:
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.ZHIPU,
                    provider_name="智谱",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 128000),
                    description=m.get("description", ""),
                    is_free=False,
                    supports_vision="vision" in model_id.lower() or "glm-4v" in model_id.lower(),
                )
    
    async def _discover_dashscope(self, client) -> None:
        """发现阿里百炼模型"""
        models = await client.discover_models()
        for m in models:
            model_id = m.get("id", "")
            if model_id:
                self._dynamic_models[model_id] = DiscoveredModel(
                    model_id=model_id,
                    provider=ProviderPriority.DASHSCOPE,
                    provider_name="阿里百炼",
                    name=m.get("name", model_id),
                    context_length=m.get("context_length", 128000),
                    description=m.get("description", ""),
                    is_free=False,
                )
    
    def _discover_cloudflare(self, client) -> None:
        """发现Cloudflare模型 (静态)"""
        if hasattr(client, 'discover_models'):
            models = client.discover_models()
            for m in models:
                model_id = m.get("id", "")
                if model_id:
                    self._dynamic_models[model_id] = DiscoveredModel(
                        model_id=model_id,
                        provider=ProviderPriority.CLOUDFLARE,
                        provider_name="Cloudflare",
                        name=m.get("name", model_id),
                        context_length=m.get("context_length", 8192),
                        description=m.get("description", ""),
                        is_free=True,
                    )
    
    def get_model_for_task(
        self,
        task_type: Optional[TaskType] = None,
        agent_role: Optional[AgentRole] = None,
        preferred_provider: Optional[ProviderPriority] = None
    ) -> Optional[DiscoveredModel]:
        """
        根据任务类型和角色获取最佳模型
        
        Args:
            task_type: 任务类型
            agent_role: 角色
            preferred_provider: 首选Provider
            
        Returns:
            最佳匹配模型
        """
        # 1. 如果有角色，优先使用角色配置
        if agent_role:
            config = ROLE_MODEL_CONFIGS.get(agent_role)
            if config:
                # 先尝试主力模型
                model = self._dynamic_models.get(config.primary_model)
                if model and self._is_model_suitable(model, task_type, preferred_provider):
                    return model
                
                # 尝试备用模型
                model = self._dynamic_models.get(config.fallback_model)
                if model and self._is_model_suitable(model, task_type, preferred_provider):
                    return model
                
                # 尝试全局降级模型
                model = self._dynamic_models.get(config.global_fallback_model)
                if model and self._is_model_suitable(model, task_type, preferred_provider):
                    return model
        
        # 2. 从动态模型池中按能力匹配
        candidates = []
        for model in self._dynamic_models.values():
            if self._is_model_suitable(model, task_type, preferred_provider):
                candidates.append(model)
        
        # 按优先级排序
        candidates.sort(key=lambda m: m.provider.value)
        
        # 返回最高优先级的可用模型
        return candidates[0] if candidates else None
    
    def _is_model_suitable(
        self,
        model: DiscoveredModel,
        task_type: Optional[TaskType],
        preferred_provider: Optional[ProviderPriority]
    ) -> bool:
        """检查模型是否适合任务"""
        # Provider过滤
        if preferred_provider and model.provider != preferred_provider:
            return False
        
        # 任务类型过滤 (如果有明确要求)
        if task_type and model.task_types:
            if task_type not in model.task_types:
                return False
        
        return True
    
    def get_all_models(self) -> Dict[str, DiscoveredModel]:
        """获取所有动态模型"""
        return self._dynamic_models.copy()
    
    def get_static_models(self) -> Dict[str, ModelInfo]:
        """获取所有静态核心模型"""
        return self._static_models.copy()
    
    def get_models_by_provider(self, provider: ProviderPriority) -> List[DiscoveredModel]:
        """
        获取指定Provider的所有模型
        
        Args:
            provider: Provider优先级
            
        Returns:
            模型列表
        """
        return [
            m for m in self._dynamic_models.values()
            if m.provider == provider
        ]
    
    def get_model_count(self) -> Dict[str, int]:
        """获取各Provider模型数量统计"""
        counts = {
            "static": len(self._static_models),
            "dynamic": len(self._dynamic_models),
        }
        
        for provider in ProviderPriority:
            provider_models = self.get_models_by_provider(provider)
            if provider_models:
                counts[provider.name] = len(provider_models)
        
        return counts
    
    def get_model_by_id(self, model_id: str) -> Optional[DiscoveredModel]:
        """
        根据模型ID获取模型信息
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型信息
        """
        return self._dynamic_models.get(model_id)
    
    def get_free_models(self) -> List[DiscoveredModel]:
        """获取所有免费模型"""
        return [
            m for m in self._dynamic_models.values()
            if m.is_free
        ]


# 全局注册中心实例
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """获取注册中心单例"""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def reset_registry() -> None:
    """重置注册中心"""
    global _registry
    _registry = None
