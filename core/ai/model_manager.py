"""
🌸 若曦V2 - 模型管理器 (增强版)
多模型统一管理 + 智能路由 + 角色匹配 + 400+模型

兼容原有接口，新增:
- 角色匹配路由 (AgentRole)
- 新Provider (NVIDIA/SiliconFlow/OpenRouter/Cloudflare)
- 动态模型发现
- 双格式消息兼容 (Message对象 + dict列表)
"""
import os
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import random
import logging

from core.ai.models.base_model import BaseModel, ModelProvider, Message, ModelResponse

logger = logging.getLogger(__name__)

# 延迟导入，避免循环依赖
def _import_provider_clients():
    """延迟导入Provider客户端"""
    from core.ai.models.gemini_model import GeminiModel
    from core.ai.models.groq_model import GroqModel
    from core.ai.models.ollama_model import OllamaModel
    from core.ai.models.zhipu_model import ZhipuModel
    from core.ai.models.deepseek_model import DeepseekModel
    from core.ai.models.moonshot_model import MoonshotModel
    from core.ai.models.dashscope_model import DashscopeModel
    return {
        ModelProvider.GEMINI: GeminiModel,
        ModelProvider.GROQ: GroqModel,
        ModelProvider.OLLAMA: OllamaModel,
        ModelProvider.ZHIPU: ZhipuModel,
        ModelProvider.DEEPSEEK: DeepseekModel,
        ModelProvider.MOONSHOT: MoonshotModel,
        ModelProvider.DASHSCOPE: DashscopeModel,
    }


def _import_new_provider_clients():
    """延迟导入新Provider客户端"""
    try:
        from core.ai.models.nvidia_model import NVIDIAModel
        from core.ai.models.siliconflow_model import SiliconFlowModel
        from core.ai.models.openrouter_model import OpenRouterModel
        from core.ai.models.cloudflare_model import CloudflareModel
        return {
            ModelProvider.NVIDIA: NVIDIAModel,
            ModelProvider.SILICONFLOW: SiliconFlowModel,
            ModelProvider.OPENROUTER: OpenRouterModel,
            ModelProvider.CLOUDFLARE: CloudflareModel,
        }
    except ImportError as e:
        logger.warning(f"新Provider客户端导入失败: {e}")
        return {}


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
    api_key_2: Optional[str] = None  # 双Key (NVIDIA用)
    account_id: Optional[str] = None  # Cloudflare用


class ModelManager:
    """
    AI模型管理器 (增强版)
    
    功能:
    - 多模型统一管理 (原有)
    - 故障自动切换 (原有)
    - 负载均衡 (原有)
    - 健康检查 (原有)
    - 成本优化 (原有)
    - 角色匹配路由 (新增)
    - 动态模型发现 (新增)
    - 双格式消息兼容 (新增)
    """
    
    def __init__(self):
        self._models: Dict[str, BaseModel] = {}
        self._configs: Dict[str, ModelConfig] = {}
        self._health_status: Dict[str, bool] = {}
        self._role: Optional[str] = None  # 当前活跃角色
        self._use_router: bool = False  # 是否启用路由器模式
        self._provider_clients: Dict = {}
        self._new_provider_clients: Dict = {}
    
    def _ensure_clients_imported(self):
        """确保客户端已导入"""
        if not self._provider_clients:
            self._provider_clients = _import_provider_clients()
        if not self._new_provider_clients:
            self._new_provider_clients = _import_new_provider_clients()
    
    def register_model(self, name: str, config: ModelConfig) -> bool:
        """
        注册模型 (兼容原有接口 + 新Provider)
        """
        self._ensure_clients_imported()
        
        try:
            # 原有Provider
            if config.provider in self._provider_clients:
                ClientClass = self._provider_clients[config.provider]
                if config.provider == ModelProvider.OLLAMA:
                    base_url = config.base_url or "http://localhost:11434"
                    model = ClientClass(config.model_name, base_url, config.api_key)
                else:
                    model = ClientClass(config.api_key, config.model_name)
            
            # 新Provider
            elif config.provider in self._new_provider_clients:
                ClientClass = self._new_provider_clients[config.provider]
                if config.provider == ModelProvider.NVIDIA:
                    model = ClientClass(config.api_key, config.model_name, config.api_key_2)
                elif config.provider == ModelProvider.CLOUDFLARE:
                    model = ClientClass(config.api_key, config.model_name, config.account_id or "")
                else:
                    model = ClientClass(config.api_key, config.model_name)
            
            else:
                logger.warning(f"未知Provider: {config.provider}")
                return False
            
            self._models[name] = model
            self._configs[name] = config
            return True
            
        except Exception as e:
            logger.error(f"注册模型 {name} 失败: {e}")
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
        """列出所有模型"""
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
        """选择最佳可用模型"""
        candidates = []
        for name, config in self._configs.items():
            if not config.enabled:
                continue
            is_healthy = self._health_status.get(name, True)
            if not is_healthy:
                continue
            candidates.append((name, config))
        
        if not candidates:
            return None
        
        priority_groups: Dict[int, List[str]] = {}
        for name, config in candidates:
            if prefer_local and not config.is_local:
                continue
            p = config.priority
            if p not in priority_groups:
                priority_groups[p] = []
            priority_groups[p].append(name)
        
        if not priority_groups:
            priority_groups = {}
            for name, config in candidates:
                p = config.priority
                if p not in priority_groups:
                    priority_groups[p] = []
                priority_groups[p].append(name)
        
        best_priority = min(priority_groups.keys())
        best_models = priority_groups[best_priority]
        return random.choice(best_models)
    
    @staticmethod
    def _normalize_messages(messages: Union[List[Message], List[Dict]]) -> List[Message]:
        """将消息统一为Message对象列表 (兼容dict和Message两种格式)"""
        if not messages:
            return []
        
        normalized = []
        for msg in messages:
            if isinstance(msg, Message):
                normalized.append(msg)
            elif isinstance(msg, dict):
                normalized.append(Message(role=msg.get("role", "user"), content=msg.get("content", "")))
            else:
                normalized.append(Message(role="user", content=str(msg)))
        
        return normalized
    
    async def chat(
        self,
        messages: Union[List[Message], List[Dict]],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        prefer_local: bool = False,
        fallback: bool = True,
        # 新增参数 (兼容旧调用)
        model_preference: Optional[str] = None,
        agent_role: Optional[str] = None,
        use_cache: bool = True,
    ) -> Union[ModelResponse, str]:
        """
        多模型智能对话 (兼容原有接口 + 新功能)
        
        兼容参数:
        - messages: 支持Message对象列表和dict列表
        - model_preference: 兼容chat_engine的旧参数，等同于model_name
        - agent_role: 角色匹配路由
        - use_cache: 兼容health_analyzer的generate方法
        
        Returns:
            ModelResponse对象 (兼容旧代码可能当str用)
        """
        # 参数兼容
        if model_preference and not model_name:
            model_name = model_preference
        
        # 统一消息格式
        msg_list = self._normalize_messages(messages)
        
        # 角色匹配路由
        if agent_role and not model_name:
            model_name = self._select_model_by_role(agent_role)
        
        # 选择模型
        selected_models = []
        if model_name:
            if model_name in self._models and self._configs[model_name].enabled:
                selected_models.append(model_name)
        else:
            best = self.select_best_model(prefer_local)
            if best:
                selected_models.append(best)
            if fallback:
                for name in self._models.keys():
                    if name not in selected_models:
                        config = self._configs.get(name)
                        if config and config.enabled:
                            selected_models.append(name)
        
        if not selected_models:
            raise Exception("没有可用的AI模型")
        
        # 调用模型
        last_error = None
        for name in selected_models:
            model = self._models[name]
            try:
                response = await model.chat(msg_list, temperature, max_tokens)
                self._health_status[name] = True
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"模型 {name} 调用失败: {e}")
                self._health_status[name] = False
                if not fallback:
                    break
        
        raise Exception(f"所有模型调用失败: {last_error}")
    
    async def generate(self, messages: Union[List[Message], List[Dict]], **kwargs) -> ModelResponse:
        """
        兼容health_analyzer的generate方法
        
        health_analyzer调用: ai_manager.generate(messages, use_cache=False)
        返回: 需要有.content属性
        """
        return await self.chat(messages=messages, **kwargs)
    
    def _select_model_by_role(self, agent_role: str) -> Optional[str]:
        """根据角色选择模型"""
        try:
            from core.ai.router.route_config import AgentRole, ROLE_DEFAULT_MODELS
            
            # 将字符串转为枚举
            role_map = {
                "ruoxi": AgentRole.RUOXI,
                "afu": AgentRole.AFU,
                "researcher": AgentRole.RESEARCHER,
                "coder": AgentRole.CODER,
                "RUOXI": AgentRole.RUOXI,
                "AFU": AgentRole.AFU,
                "RESEARCHER": AgentRole.RESEARCHER,
                "CODER": AgentRole.CODER,
            }
            
            role_enum = role_map.get(agent_role)
            if not role_enum:
                return None
            
            # 从默认模型中找已注册的
            default_model = ROLE_DEFAULT_MODELS.get(role_enum)
            if default_model and default_model in self._models:
                return default_model
            
            # 尝试Fallback链
            from core.ai.router.route_config import ROLE_FALLBACK_CHAINS
            for model_name in ROLE_FALLBACK_CHAINS.get(role_enum, []):
                if model_name in self._models:
                    return model_name
            
            return None
            
        except ImportError:
            logger.warning("路由配置未安装，使用默认模型选择")
            return None
    
    def enable_router(self, role: Optional[str] = None):
        """启用路由器模式"""
        self._use_router = True
        if role:
            self._role = role
    
    def set_agent_role(self, role: str):
        """设置当前活跃的Agent角色"""
        self._role = role
    
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
                logger.warning(f"模型 {name} 健康检查失败: {e}")
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
            "router_enabled": self._use_router,
            "active_role": self._role,
            "providers": list(set(
                c.provider.value for c in self._configs.values()
            ))
        }
    
    def setup_default_models(self):
        """
        使用环境变量设置默认模型
        
        从.env或环境变量读取API密钥，注册所有可用Provider
        """
        # NVIDIA NIM (主力)
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            nvidia_key_2 = os.getenv("NVIDIA_API_KEY_2")
            self.register_model("nvidia_deepseek_v4", ModelConfig(
                provider=ModelProvider.NVIDIA,
                api_key=nvidia_key,
                model_name="deepseek-ai/deepseek-v4-pro",
                priority=1,
                api_key_2=nvidia_key_2
            ))
            self.register_model("nvidia_deepseek_coder", ModelConfig(
                provider=ModelProvider.NVIDIA,
                api_key=nvidia_key,
                model_name="deepseek-ai/deepseek-coder",
                priority=1,
                api_key_2=nvidia_key_2
            ))
        
        # 硅基流动
        sf_key = os.getenv("SILICONFLOW_KEY")
        if sf_key:
            self.register_model("siliconflow_deepseek_v3", ModelConfig(
                provider=ModelProvider.SILICONFLOW,
                api_key=sf_key,
                model_name="Pro/deepseek-ai/DeepSeek-V3",
                priority=2
            ))
            self.register_model("siliconflow_qwen72b", ModelConfig(
                provider=ModelProvider.SILICONFLOW,
                api_key=sf_key,
                model_name="Qwen/Qwen2.5-72B-Instruct",
                priority=3
            ))
        
        # 智谱
        zhipu_key = os.getenv("ZHIPU_KEY")
        if zhipu_key:
            self.register_model("zhipu_glm4", ModelConfig(
                provider=ModelProvider.ZHIPU,
                api_key=zhipu_key,
                model_name="glm-4",
                priority=2
            ))
        
        # 月之暗面
        moonshot_key = os.getenv("MOONSHOT_KEY")
        if moonshot_key:
            self.register_model("moonshot_128k", ModelConfig(
                provider=ModelProvider.MOONSHOT,
                api_key=moonshot_key,
                model_name="moonshot-v1-128k",
                priority=2
            ))
        
        # OpenRouter (免费)
        or_key = os.getenv("OPENROUTER_API_KEY")
        if or_key:
            self.register_model("openrouter_deepseek_v4_free", ModelConfig(
                provider=ModelProvider.OPENROUTER,
                api_key=or_key,
                model_name="deepseek/deepseek-v4-flash:free",
                priority=3
            ))
            self.register_model("openrouter_qwen3_coder_free", ModelConfig(
                provider=ModelProvider.OPENROUTER,
                api_key=or_key,
                model_name="qwen/qwen3-coder:free",
                priority=3
            ))
        
        # Groq (免费)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.register_model("groq_llama33_70b", ModelConfig(
                provider=ModelProvider.GROQ,
                api_key=groq_key,
                model_name="llama-3.3-70b-versatile",
                priority=3
            ))
        
        # Google AI (免费)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.register_model("gemini_flash", ModelConfig(
                provider=ModelProvider.GEMINI,
                api_key=gemini_key,
                model_name="gemini-2.0-flash",
                priority=3
            ))
        
        # 阿里百炼
        dashscope_key = os.getenv("ALIYUN_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if dashscope_key:
            self.register_model("dashscope_qwen", ModelConfig(
                provider=ModelProvider.DASHSCOPE,
                api_key=dashscope_key,
                model_name="qwen-plus",
                priority=4
            ))
        
        logger.info(f"默认模型设置完成: {len(self._models)} 个模型, 角色={self._role}")
    
    async def discover_all_models(self):
        """
        异步发现所有Provider的可用模型
        启动时调用，填充ModelRegistry的动态层
        """
        try:
            from core.ai.router.model_registry import model_registry, DiscoveredModel
        except ImportError:
            logger.warning("ModelRegistry未安装，跳过动态发现")
            return
        
        discovered = []
        
        # NVIDIA
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            try:
                from core.ai.models.nvidia_model import NVIDIAModel
                models = NVIDIAModel.discover_models(nvidia_key)
                discovered.extend([DiscoveredModel(**m) for m in models])
                logger.info(f"NVIDIA发现 {len(models)} 个模型")
            except Exception as e:
                logger.warning(f"NVIDIA发现失败: {e}")
        
        # 硅基流动
        sf_key = os.getenv("SILICONFLOW_KEY")
        if sf_key:
            try:
                from core.ai.models.siliconflow_model import SiliconFlowModel
                models = SiliconFlowModel.discover_models(sf_key)
                discovered.extend([DiscoveredModel(**m) for m in models])
                logger.info(f"硅基流动发现 {len(models)} 个模型")
            except Exception as e:
                logger.warning(f"硅基流动发现失败: {e}")
        
        # OpenRouter
        or_key = os.getenv("OPENROUTER_API_KEY")
        if or_key:
            try:
                from core.ai.models.openrouter_model import OpenRouterModel
                models = OpenRouterModel.discover_models(or_key)
                discovered.extend([DiscoveredModel(**m) for m in models])
                logger.info(f"OpenRouter发现 {len(models)} 个免费模型")
            except Exception as e:
                logger.warning(f"OpenRouter发现失败: {e}")
        
        if discovered:
            model_registry.add_dynamic_models(discovered)
            logger.info(f"动态发现总计: {len(discovered)} 个模型，注册表总计: {model_registry.total_count}")


# 全局模型管理器实例
model_manager = ModelManager()

# 兼容别名: health_analyzer引用的ai_manager
ai_manager = model_manager
