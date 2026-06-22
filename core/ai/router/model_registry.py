"""
🌸 若曦V2 - 模型注册表
动态模型发现 + 静态核心注册 双层架构

启动流程:
1. 加载静态核心模型 (立即可用)
2. 异步发现动态模型 (后台补充)
3. 合并为完整模型池 (400+)
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredModel:
    """发现的模型"""
    id: str
    name: str
    provider: str
    owned_by: str = ""
    free: bool = False
    context_window: int = 4096
    available: bool = True


class ModelRegistry:
    """
    模型注册中心
    
    双层架构:
    - 静态层: 核心模型，角色匹配用，立即可用
    - 动态层: 从各Provider API发现的全量模型
    """
    
    def __init__(self):
        self._static_models: Dict[str, DiscoveredModel] = {}
        self._dynamic_models: Dict[str, DiscoveredModel] = {}
        self._all_models: Dict[str, DiscoveredModel] = {}
        self._initialized = False
        self._load_static_models()
    
    def _load_static_models(self):
        """加载静态核心模型"""
        static = [
            # NVIDIA NIM 核心模型
            DiscoveredModel("deepseek-ai/deepseek-v4-pro", "DeepSeek V4 Pro", "nvidia", "deepseek", context_window=131072),
            DiscoveredModel("deepseek-ai/deepseek-coder", "DeepSeek Coder", "nvidia", "deepseek", context_window=131072),
            DiscoveredModel("meta/llama-3.1-405b-instruct", "Llama 3.1 405B", "nvidia", "meta", context_window=128000),
            DiscoveredModel("nvidia/nemotron-3-super-120b-a12b:free", "Nemotron 120B", "openrouter", "nvidia", free=True),
            # 硅基流动
            DiscoveredModel("Pro/deepseek-ai/DeepSeek-V3", "DeepSeek V3 (硅基)", "siliconflow", "deepseek"),
            DiscoveredModel("Qwen/Qwen2.5-72B-Instruct", "Qwen 2.5 72B", "siliconflow", "qwen"),
            # 智谱
            DiscoveredModel("glm-4", "GLM-4", "zhipu", "zhipu", context_window=128000),
            DiscoveredModel("glm-4-flash", "GLM-4 Flash", "zhipu", "zhipu", free=True),
            # 月之暗面
            DiscoveredModel("moonshot-v1-128k", "Moonshot 128K", "moonshot", "moonshot", context_window=131072),
            DiscoveredModel("moonshot-v1-32k", "Moonshot 32K", "moonshot", "moonshot", context_window=32768),
            # OpenRouter 免费
            DiscoveredModel("deepseek/deepseek-v4-flash:free", "DeepSeek V4 Flash (免费)", "openrouter", "deepseek", free=True),
            DiscoveredModel("qwen/qwen3-next-80b-a3b-instruct:free", "Qwen3 80B (免费)", "openrouter", "qwen", free=True),
            DiscoveredModel("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B (免费)", "openrouter", "meta", free=True),
            DiscoveredModel("qwen/qwen3-coder:free", "Qwen3 Coder (免费)", "openrouter", "qwen", free=True),
            DiscoveredModel("z-ai/glm-4.5-air:free", "GLM-4.5 Air (免费)", "openrouter", "zhipu", free=True),
            # Groq
            DiscoveredModel("llama-3.3-70b-versatile", "Llama 3.3 70B (Groq)", "groq", "meta", free=True),
            DiscoveredModel("llama-3.1-8b-instant", "Llama 3.1 8B (Groq)", "groq", "meta", free=True),
        ]
        
        for model in static:
            self._static_models[model.id] = model
        
        self._rebuild_index()
        logger.info(f"静态模型加载完成: {len(self._static_models)} 个")
    
    def _rebuild_index(self):
        """重建完整索引"""
        self._all_models = {}
        self._all_models.update(self._static_models)
        self._all_models.update(self._dynamic_models)
    
    def add_dynamic_models(self, models: List[DiscoveredModel]):
        """添加动态发现的模型"""
        added = 0
        for model in models:
            if model.id not in self._static_models:
                self._dynamic_models[model.id] = model
                added += 1
        
        self._rebuild_index()
        logger.info(f"动态模型添加: {added} 个新模型，总计 {len(self._all_models)} 个")
    
    def get_model(self, model_id: str) -> Optional[DiscoveredModel]:
        """获取模型信息"""
        return self._all_models.get(model_id)
    
    def get_all_models(self) -> Dict[str, DiscoveredModel]:
        """获取全部模型"""
        return self._all_models.copy()
    
    def get_models_by_provider(self, provider: str) -> List[DiscoveredModel]:
        """按Provider获取模型"""
        return [m for m in self._all_models.values() if m.provider == provider]
    
    def get_free_models(self) -> List[DiscoveredModel]:
        """获取免费模型"""
        return [m for m in self._all_models.values() if m.free]
    
    def search_models(self, keyword: str) -> List[DiscoveredModel]:
        """搜索模型"""
        keyword_lower = keyword.lower()
        return [
            m for m in self._all_models.values()
            if keyword_lower in m.id.lower() or keyword_lower in m.name.lower()
        ]
    
    @property
    def total_count(self) -> int:
        return len(self._all_models)
    
    @property
    def static_count(self) -> int:
        return len(self._static_models)
    
    @property
    def dynamic_count(self) -> int:
        return len(self._dynamic_models)


# 全局注册表实例
model_registry = ModelRegistry()
