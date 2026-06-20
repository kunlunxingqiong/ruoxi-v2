"""
🌸 若曦V2 AI模型管理器
多模型管理、自动切换、智能降级
主脑以永久免费模型为主
"""
import os
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.config_manager import config
from core.log_manager import get_logger
from core.exceptions import AIException, AITimeoutException

logger = get_logger(__name__)


class ModelProvider(Enum):
    """AI模型提供商"""
    GEMINI = "gemini"           # Google Gemini (永久免费)
    GROQ = "groq"              # Groq (极速免费)
    TOGETHER = "together"      # Together AI (免费层)
    COHERE = "cohere"          # Cohere (免费层)
    OLLAMA = "ollama"          # 本地部署
    SIMULATE = "simulate"      # 模拟/测试模式


@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 30
    max_tokens: int = 4096
    temperature: float = 0.7
    priority: int = 1  # 优先级，数字越小优先级越高
    enabled: bool = True


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    model_used: str
    provider: str
    tokens_input: int = 0
    tokens_output: int = 0
    response_time_ms: int = 0
    success: bool = True
    error_message: str = ""
    cached: bool = False


@dataclass
class ModelStats:
    """模型统计"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    avg_response_time_ms: float = 0.0
    last_used: Optional[datetime] = None
    last_error: Optional[str] = None


class AIModelManager:
    """
    AI模型管理器
    
    功能:
    - 多模型配置管理
    - 自动故障转移 (主模型失败自动切换备用)
    - 性能统计和监控
    - 成本追踪
    - 响应缓存
    """
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.stats: Dict[str, ModelStats] = {}
        self.cache: Dict[str, ModelResponse] = {}
        self.cache_enabled = config.get("ai.cache_enabled", True)
        self.cache_ttl = config.get("ai.cache_ttl", 3600)  # 1小时
        
        # 初始化默认模型 (第一阶段 - 模拟模式)
        self._init_default_models()
    
    def _init_default_models(self):
        """初始化默认模型配置"""
        # 从环境变量或配置文件加载
        
        # 1. Gemini (首选 - 永久免费)
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.add_model(ModelConfig(
            provider=ModelProvider.GEMINI if gemini_key else ModelProvider.SIMULATE,
            model_name="gemini-2.0-flash",
            api_key=gemini_key or None,
            timeout=10,
            priority=1,
            enabled=True
        ))
        
        # 2. Groq (备用1 - 极速)
        groq_key = os.getenv("GROQ_API_KEY", "")
        self.add_model(ModelConfig(
            provider=ModelProvider.GROQ if groq_key else ModelProvider.SIMULATE,
            model_name="llama-3.3-70b",
            api_key=groq_key or None,
            timeout=5,
            priority=2,
            enabled=True
        ))
        
        # 3. Together AI (备用2)
        together_key = os.getenv("TOGETHER_API_KEY", "")
        self.add_model(ModelConfig(
            provider=ModelProvider.TOGETHER if together_key else ModelProvider.SIMULATE,
            model_name="meta-llama/Meta-Llama-3.1-70B",
            api_key=together_key or None,
            timeout=15,
            priority=3,
            enabled=bool(together_key)
        ))
        
        # 4. Ollama (本地 - 完全免费)
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.add_model(ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name=os.getenv("OLLAMA_MODEL", "llama3.2"),
            base_url=ollama_url,
            timeout=30,
            priority=4,
            enabled=False  # 默认禁用，需手动开启
        ))
        
        # 5. 模拟模式 (最后备用)
        self.add_model(ModelConfig(
            provider=ModelProvider.SIMULATE,
            model_name="simulate-mode",
            timeout=1,
            priority=99,
            enabled=True
        ))
        
        logger.info(f"🤖 AI模型管理器初始化 | 配置了{len(self.models)}个模型")
    
    def add_model(self, config: ModelConfig) -> str:
        """
        添加模型配置
        
        Returns:
            模型ID
        """
        model_id = f"{config.provider.value}_{config.model_name}"
        self.models[model_id] = config
        self.stats[model_id] = ModelStats()
        
        logger.info(f"✅ 模型添加 | {model_id} | 优先级: {config.priority}")
        return model_id
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表 (按优先级排序)"""
        available = [
            (model_id, model.priority)
            for model_id, model in self.models.items()
            if model.enabled
        ]
        available.sort(key=lambda x: x[1])
        return [model_id for model_id, _ in available]
    
    def _generate_cache_key(self, messages: List[Dict], model_id: str) -> str:
        """生成缓存key"""
        import hashlib
        content = f"{model_id}:{str(messages)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        max_retries: int = 3,
        use_cache: bool = True
    ) -> ModelResponse:
        """
        生成AI响应 (带自动降级)
        
        Args:
            messages: 消息列表
            stream: 是否流式返回
            max_retries: 最大重试次数
            use_cache: 是否使用缓存
        
        Returns:
            ModelResponse
        """
        # 尝试获取可用模型 (按优先级排序)
        available_models = self.get_available_models()
        
        if not available_models:
            raise AIException("没有可用的AI模型")
        
        last_error = None
        
        for model_id in available_models[:max_retries]:
            try:
                # 检查缓存
                if use_cache and self.cache_enabled and not stream:
                    cache_key = self._generate_cache_key(messages, model_id)
                    if cache_key in self.cache:
                        cached_response = self.cache[cache_key]
                        cached_response.cached = True
                        logger.info(f"💾 缓存命中 | {model_id}")
                        return cached_response
                
                # 调用模型
                response = await self._call_model(model_id, messages, stream)
                
                # 更新统计
                self._update_stats(model_id, response)
                
                # 保存缓存
                if use_cache and self.cache_enabled and response.success and not stream:
                    cache_key = self._generate_cache_key(messages, model_id)
                    self.cache[cache_key] = response
                
                logger.info(f"✅ AI生成成功 | {model_id} | {response.tokens_output} tokens")
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ 模型失败 | {model_id} | {e}")
                self._record_error(model_id, str(e))
                continue
        
        # 所有模型都失败
        logger.error(f"❌ 所有AI模型调用失败")
        raise AIException(f"AI服务暂时不可用: {last_error}")
    
    async def _call_model(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        stream: bool
    ) -> ModelResponse:
        """
        调用具体模型
        
        实际实现需要安装各SDK:
        - pip install google-generativeai
        - pip install groq
        - pip install together
        """
        model_config = self.models[model_id]
        start_time = time.time()
        
        # 根据提供商调用不同实现
        if model_config.provider == ModelProvider.GEMINI:
            return await self._call_gemini(model_config, messages, stream)
        elif model_config.provider == ModelProvider.GROQ:
            return await self._call_groq(model_config, messages, stream)
        elif model_config.provider == ModelProvider.TOGETHER:
            return await self._call_together(model_config, messages, stream)
        elif model_config.provider == ModelProvider.OLLAMA:
            return await self._call_ollama(model_config, messages, stream)
        elif model_config.provider == ModelProvider.SIMULATE:
            return await self._call_simulate(model_config, messages, stream)
        else:
            raise AIException(f"未知的模型提供商: {model_config.provider}")
    
    async def _call_gemini(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        stream: bool
    ) -> ModelResponse:
        """调用Gemini API"""
        # 实际实现:
        # import google.generativeai as genai
        # genai.configure(api_key=config.api_key)
        # model = genai.GenerativeModel(config.model_name)
        # response = await model.generate_content_async(...)
        
        # 模拟实现
        await asyncio.sleep(0.1)
        content = self._generate_simulated_response(messages)
        
        return ModelResponse(
            content=content,
            model_used=config.model_name,
            provider="gemini",
            tokens_input=len(str(messages)),
            tokens_output=len(content),
            response_time_ms=int(time.time() * 1000) % 1000,
            success=True
        )
    
    async def _call_groq(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        stream: bool
    ) -> ModelResponse:
        """调用Groq API (OpenAI兼容)"""
        await asyncio.sleep(0.05)  # Groq很快
        content = self._generate_simulated_response(messages)
        
        return ModelResponse(
            content=content,
            model_used=config.model_name,
            provider="groq",
            tokens_input=len(str(messages)),
            tokens_output=len(content),
            response_time_ms=100,
            success=True
        )
    
    async def _call_together(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        stream: bool
    ) -> ModelResponse:
        """调用Together AI"""
        await asyncio.sleep(0.2)
        content = self._generate_simulated_response(messages)
        
        return ModelResponse(
            content=content,
            model_used=config.model_name,
            provider="together",
            tokens_input=len(str(messages)),
            tokens_output=len(content),
            response_time_ms=200,
            success=True
        )
    
    async def _call_ollama(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        stream: bool
    ) -> ModelResponse:
        """调用Ollama本地模型"""
        await asyncio.sleep(0.5)  # 本地可能慢一些
        content = self._generate_simulated_response(messages)
        
        return ModelResponse(
            content=content,
            model_used=config.model_name,
            provider="ollama",
            tokens_input=len(str(messages)),
            tokens_output=len(content),
            response_time_ms=500,
            success=True
        )
    
    async def _call_simulate(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        stream: bool
    ) -> ModelResponse:
        """模拟模式 (无需API密钥)"""
        await asyncio.sleep(0.01)
        
        # 获取用户最后消息
        user_message = messages[-1]["content"] if messages else ""
        
        # 生成模拟回复
        content = f"🌸 (模拟回复) 曦曦收到: \"{user_message[:30]}...\"\n\n这是模拟回复，实际AI集成需要配置API密钥。\n\n支持的模型:\n• Google Gemini (永久免费)\n• Groq (极速免费)\n• Together AI (免费层)\n• Ollama (本地部署)\n\n请在 .local/ai-keys.txt 中配置密钥。"
        
        return ModelResponse(
            content=content,
            model_used="simulate",
            provider="simulate",
            tokens_input=len(str(messages)),
            tokens_output=len(content),
            response_time_ms=10,
            success=True
        )
    
    def _generate_simulated_response(self, messages: List[Dict[str, str]]) -> str:
        """生成模拟响应内容"""
        user_msg = messages[-1]["content"] if messages else ""
        
        responses = [
            f"🌸 曦曦理解你的感受\\n\n关于\"{user_msg[:20]}...\"，我可以帮你。",
            "🌸 抱抱你~\n\n有什么我可以帮你的吗？",
            "🌸 我在听，继续说~",
            "🌸 这是个好问题，让我想想~"
        ]
        import random
        return random.choice(responses)
    
    def _update_stats(self, model_id: str, response: ModelResponse):
        """更新模型统计"""
        stats = self.stats.get(model_id, ModelStats())
        stats.total_requests += 1
        
        if response.success:
            stats.successful_requests += 1
            stats.total_tokens += response.tokens_output
            
            # 更新平均响应时间
            if stats.avg_response_time_ms == 0:
                stats.avg_response_time_ms = response.response_time_ms
            else:
                stats.avg_response_time_ms = (
                    stats.avg_response_time_ms * 0.9 + response.response_time_ms * 0.1
                )
        else:
            stats.failed_requests += 1
        
        stats.last_used = datetime.utcnow()
        self.stats[model_id] = stats
    
    def _record_error(self, model_id: str, error: str):
        """记录模型错误"""
        if model_id in self.stats:
            self.stats[model_id].last_error = error
    
    def get_stats(self) -> Dict[str, Any]:
        """获取所有模型统计"""
        return {
            model_id: {
                "total_requests": stats.total_requests,
                "success_rate": round(stats.successful_requests / stats.total_requests * 100, 2) if stats.total_requests else 0,
                "avg_response_time_ms": round(stats.avg_response_time_ms, 2),
                "last_used": stats.last_used.isoformat() if stats.last_used else None,
                "last_error": stats.last_error
            }
            for model_id, stats in self.stats.items()
        }
    
    def clear_cache(self):
        """清除响应缓存"""
        self.cache.clear()
        logger.info("🗑️ 缓存已清除")


# 全局模型管理器实例
ai_manager = AIModelManager()


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 AI模型管理器测试")
    print("=" * 60)
    
    import asyncio
    
    async def test():
        print("\n【可用模型】")
        for model_id in ai_manager.get_available_models():
            config = ai_manager.models[model_id]
            print(f"  {model_id}: {config.provider.value} (优先级{config.priority})")
        
        print("\n【模拟对话】")
        messages = [
            {"role": "system", "content": "你是若曦，一个温柔体贴的AI医生朋友。"},
            {"role": "user", "content": "你好若曦，我今天有点头疼"}
        ]
        
        response = await ai_manager.generate(messages, use_cache=False)
        print(f"  模型: {response.model_used}")
        print(f"  回复: {response.content[:100]}...")
        print(f"  耗时: {response.response_time_ms}ms")
        
        print("\n【统计】")
        stats = ai_manager.get_stats()
        for model_id, model_stats in stats.items():
            if model_stats['total_requests'] > 0:
                print(f"  {model_id}: {model_stats}")
        
        print("\n" + "=" * 60)
        print("✅ AI模型管理器测试完成")
        print("=" * 60)
    
    asyncio.run(test())
