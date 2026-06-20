"""
🌸 若曦V2 - 模型管理器
多模型统一管理和智能路由
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

from core.ai.models.base_model import BaseModel, ModelProvider, Message, ModelResponse
from core.ai.models.gemini_model import GeminiModel
from core.ai.models.groq_model import GroqModel
from core.ai.models.ollama_model import OllamaModel


@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    api_key: str
    model_name: str
    priority: int = 1  # 优先级，1最高
    enabled: bool = True
    is_local: bool = False
    base_url: Optional[str] = None


class ModelManager:
    """
    AI模型管理器
    
    功能:
    - 多模型统一管理
    - 故障自动切换
    - 负载均衡
    - 健康检查
    - 成本优化 (优先免费模型)
    """
    
    def __init__(self):
        self._models: Dict[str, BaseModel] = {}
        self._configs: Dict[str, ModelConfig] = {}
        self._health_status: Dict[str, bool] = {}
    
    def register_model(self, name: str, config: ModelConfig) -> bool:
        """
        注册模型
        
        Args:
            name: 模型名称（如 "gemini", "groq", "ollama"）
            config: 模型配置
        """
        try:
            if config.provider == ModelProvider.GEMINI:
                model = GeminiModel(config.api_key, config.model_name)
            elif config.provider == ModelProvider.GROQ:
                model = GroqModel(config.api_key, config.model_name)
            elif config.provider == ModelProvider.OLLAMA:
                base_url = config.base_url or "http://localhost:11434"
                model = OllamaModel(config.model_name, base_url, config.api_key)
            else:
                return False
            
            self._models[name] = model
            self._configs[name] = config
            return True
            
        except Exception as e:
            print(f"注册模型 {name} 失败: {e}")
            return False
    
    def unregister_model(self, name: str) -> bool:
        """注销模型"""
        if name in self._models:
            del self._models[name]
            del self._configs[name]
            if name in self._health_status:
                del self._health_status[name]
            return True
        return False
    
    def get_model(self, name: str) -> Optional[BaseModel]:
        """获取指定模型"""
        return self._models.get(name)
    
    def list_models(self, only_enabled: bool = True) -> Dict[str, dict]:
        """
        列出所有模型
        
        Returns:
            模型信息字典
        """
        result = {}
        for name, config in self._configs.items():
            if only_enabled and not config.enabled:
                continue
            
            if name in self._models:
                info = self._models[name].get_info()
                info.update({
                    "name": name,
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "healthy": self._health_status.get(name, True)
                })
                result[name] = info
        
        return result
    
    def select_best_model(self, prefer_local: bool = False) -> Optional[str]:
        """
        选择最佳可用模型
        
        选择策略:
        1. 优先选择本地模型（如果 prefer_local=True）
        2. 优先选择健康的模型
        3. 按优先级排序
        4. 同优先级随机选择（负载均衡）
        
        Returns:
            模型名称
        """
        candidates = []
        
        for name, config in self._configs.items():
            if not config.enabled:
                continue
            
            # 检查健康状态
            is_healthy = self._health_status.get(name, True)
            if not is_healthy:
                continue
            
            candidates.append((name, config))
        
        if not candidates:
            return None
        
        # 按优先级分组
        priority_groups: Dict[int, List[str]] = {}
        for name, config in candidates:
            if prefer_local and not config.is_local:
                continue
            
            p = config.priority
            if p not in priority_groups:
                priority_groups[p] = []
            priority_groups[p].append(name)
        
        if not priority_groups:
            # 如果没有本地模型，使用所有候选
            priority_groups = {}
            for name, config in candidates:
                p = config.priority
                if p not in priority_groups:
                    priority_groups[p] = []
                priority_groups[p].append(name)
        
        # 选择最高优先级
        best_priority = min(priority_groups.keys())
        best_models = priority_groups[best_priority]
        
        # 同优先级随机选择
        return random.choice(best_models)
    
    async def chat(
        self,
        messages: List[Message],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        prefer_local: bool = False,
        fallback: bool = True
    ) -> ModelResponse:
        """
        多模型智能对话
        
        Args:
            messages: 消息列表
            model_name: 指定模型，None则自动选择
            temperature: 温度参数
            max_tokens: 最大token数
            prefer_local: 优先使用本地模型
            fallback: 失败时是否回退到其他模型
        """
        selected_models = []
        
        if model_name:
            # 使用指定模型
            if model_name in self._models and self._configs[model_name].enabled:
                selected_models.append(model_name)
        else:
            # 选择最佳模型
            best = self.select_best_model(prefer_local)
            if best:
                selected_models.append(best)
            
            # 准备其他候选（用于回退）
            if fallback:
                for name in self._models.keys():
                    if name not in selected_models:
                        config = self._configs.get(name)
                        if config and config.enabled:
                            selected_models.append(name)
        
        if not selected_models:
            raise Exception("没有可用的AI模型")
        
        # 尝试调用模型
        last_error = None
        for model_name in selected_models:
            model = self._models[model_name]
            
            try:
                response = await model.chat(messages, temperature, max_tokens)
                
                # 标记模型健康
                self._health_status[model_name] = True
                
                return response
                
            except Exception as e:
                last_error = e
                print(f"模型 {model_name} 调用失败: {e}")
                
                # 标记模型可能不健康
                self._health_status[model_name] = False
                
                if not fallback:
                    break
        
        raise Exception(f"所有模型调用失败: {last_error}")
    
    async def run_health_check(self) -> Dict[str, bool]:
        """运行健康检查"""
        results = {}
        
        for name, model in self._models.items():
            try:
                is_healthy = await model.health_check()
                self._health_status[name] = is_healthy
                results[name] = is_healthy
            except Exception as e:
                self._health_status[name] = False
                results[name] = False
                print(f"模型 {name} 健康检查失败: {e}")
        
        return results
    
    def enable_model(self, name: str) -> bool:
        """启用模型"""
        if name in self._configs:
            self._configs[name].enabled = True
            return True
        return False
    
    def disable_model(self, name: str) -> bool:
        """禁用模型"""
        if name in self._configs:
            self._configs[name].enabled = False
            return True
        return False
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = len(self._models)
        enabled = sum(1 for c in self._configs.values() if c.enabled)
        healthy = sum(1 for h in self._health_status.values() if h)
        
        return {
            "total_models": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "providers": list(set(
                c.provider.value for c in self._configs.values()
            ))
        }


# 全局模型管理器实例
model_manager = ModelManager()
