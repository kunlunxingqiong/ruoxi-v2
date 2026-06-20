"""
🌸 若曦V2 - AI模型管理器
多模型统一路由与管理
支持 Gemini / Groq / Ollama 三大免费API
"""

import os
import json
import asyncio
from typing import Dict, Optional, List, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """模型提供商"""
    GEMINI = "gemini"      # Google Gemini (免费 60 req/min)
    GROQ = "groq"          # Groq (免费 14400 req/day)
    OLLAMA = "ollama"      # 本地Ollama (无限制)


class ModelCapability(Enum):
    """模型能力"""
    CHAT = "chat"                  # 对话
    STREAMING = "streaming"        # 流式输出
    VISION = "vision"              # 图像理解
    FUNCTION_CALLING = "function"  # 函数调用
    LONG_CONTEXT = "long_context"  # 长上下文


@dataclass
class ModelConfig:
    """模型配置"""
    provider: ModelProvider
    model_id: str
    display_name: str
    capabilities: List[ModelCapability] = field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.7
    context_window: int = 8192
    priority: int = 100  # 优先级，数字越小优先级越高
    is_free: bool = True
    rate_limit_rpm: int = 60  # 每分钟请求限制
    rate_limit_rpd: int = 14400  # 每天请求限制
    
    def to_dict(self) -> Dict:
        return {
            "provider": self.provider.value,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "capabilities": [c.value for c in self.capabilities],
            "max_tokens": self.max_tokens,
            "context_window": self.context_window,
            "is_free": self.is_free,
            "rate_limit": {
                "rpm": self.rate_limit_rpm,
                "rpd": self.rate_limit_rpd
            }
        }


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class ChatRequest:
    """聊天请求"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    enable_memory: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "messages": [m.to_dict() for m in self.messages],
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": self.stream
        }


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict] = None
    finish_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason
        }


class BaseModelClient(ABC):
    """模型客户端基类"""
    
    def __init__(self, config: ModelConfig, api_key: Optional[str] = None):
        self.config = config
        self.api_key = api_key
        self._request_count = 0
        self._last_reset = asyncio.get_event_loop().time()
    
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式对话"""
        pass
    
    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """流式对话"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    def _check_rate_limit(self) -> bool:
        """检查限流"""
        current_time = asyncio.get_event_loop().time()
        
        # 每分钟重置
        if current_time - self._last_reset >= 60:
            self._request_count = 0
            self._last_reset = current_time
        
        if self._request_count >= self.config.rate_limit_rpm:
            return False
        
        self._request_count += 1
        return True


class GeminiClient(BaseModelClient):
    """Gemini API客户端"""
    
    def __init__(self, config: ModelConfig, api_key: str):
        super().__init__(config, api_key)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Gemini对话"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded for Gemini")
        
        try:
            import aiohttp
            
            # 构建Gemini格式的消息
            contents = self._format_messages(request.messages)
            
            url = f"{self.base_url}/models/{self.config.model_id}:generateContent"
            params = {"key": self.api_key}
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": request.temperature or self.config.temperature,
                    "maxOutputTokens": request.max_tokens or self.config.max_tokens,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Gemini API error: {resp.status} - {error_text}")
                    
                    data = await resp.json()
                    
                    # 解析响应
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    usage = data.get("usageMetadata", {})
                    
                    return ChatResponse(
                        content=content,
                        model=self.config.model_id,
                        provider="gemini",
                        usage={
                            "prompt_tokens": usage.get("promptTokenCount", 0),
                            "completion_tokens": usage.get("candidatesTokenCount", 0),
                            "total_tokens": usage.get("totalTokenCount", 0)
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Gemini流式对话"""
        try:
            import aiohttp
            
            contents = self._format_messages(request.messages)
            
            url = f"{self.base_url}/models/{self.config.model_id}:streamGenerateContent"
            params = {"key": self.api_key}
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": request.temperature or self.config.temperature,
                    "maxOutputTokens": request.max_tokens or self.config.max_tokens,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, json=payload) as resp:
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "candidates" in data:
                                    text = data["candidates"][0]["content"]["parts"][0].get("text", "")
                                    if text:
                                        yield text
                            except:
                                pass
                                
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise
    
    def _format_messages(self, messages: List[ChatMessage]) -> List[Dict]:
        """格式化消息为Gemini格式"""
        contents = []
        
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        
        return contents
    
    async def health_check(self) -> bool:
        """检查Gemini服务状态"""
        try:
            import aiohttp
            url = f"{self.base_url}/models"
            params = {"key": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    return resp.status == 200
        except:
            return False


class GroqClient(BaseModelClient):
    """Groq API客户端"""
    
    def __init__(self, config: ModelConfig, api_key: str):
        super().__init__(config, api_key)
        self.base_url = "https://api.groq.com/openai/v1"
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Groq对话"""
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded for Groq")
        
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.model_id,
                "messages": [m.to_dict() for m in request.messages],
                "temperature": request.temperature or self.config.temperature,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Groq API error: {resp.status} - {error_text}")
                    
                    data = await resp.json()
                    
                    return ChatResponse(
                        content=data["choices"][0]["message"]["content"],
                        model=self.config.model_id,
                        provider="groq",
                        usage=data.get("usage"),
                        finish_reason=data["choices"][0].get("finish_reason")
                    )
                    
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Groq流式对话"""
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.model_id,
                "messages": [m.to_dict() for m in request.messages],
                "temperature": request.temperature or self.config.temperature,
                "stream": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as resp:
                    async for line in resp.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                            except:
                                pass
                                
        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """检查Groq服务状态"""
        try:
            import aiohttp
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=10
                ) as resp:
                    return resp.status == 200
        except:
            return False


class OllamaClient(BaseModelClient):
    """Ollama本地模型客户端"""
    
    def __init__(self, config: ModelConfig, base_url: str = "http://localhost:11434"):
        super().__init__(config)
        self.base_url = base_url
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Ollama对话"""
        try:
            import aiohttp
            
            payload = {
                "model": self.config.model_id,
                "messages": [m.to_dict() for m in request.messages],
                "stream": False,
                "options": {
                    "temperature": request.temperature or self.config.temperature,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=300
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Ollama error: {resp.status}")
                    
                    data = await resp.json()
                    
                    return ChatResponse(
                        content=data["message"]["content"],
                        model=self.config.model_id,
                        provider="ollama",
                        usage=None  # Ollama不提供token统计
                    )
                    
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Ollama流式对话"""
        try:
            import aiohttp
            
            payload = {
                "model": self.config.model_id,
                "messages": [m.to_dict() for m in request.messages],
                "stream": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as resp:
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    yield data["message"]["content"]
                            except:
                                pass
                                
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """检查Ollama服务状态"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=5
                ) as resp:
                    return resp.status == 200
        except:
            return False


class AIModelManager:
    """
    AI模型管理器
    
    统一管理多个AI模型，提供：
    1. 自动路由选择
    2. 故障转移
    3. 负载均衡
    4. 统一接口
    """
    
    # 预定义模型配置
    DEFAULT_MODELS = [
        # Gemini模型 (免费: 60RPM)
        ModelConfig(
            provider=ModelProvider.GEMINI,
            model_id="gemini-2.0-flash",
            display_name="Gemini 2.0 Flash",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.STREAMING,
                ModelCapability.VISION,
                ModelCapability.LONG_CONTEXT
            ],
            max_tokens=8192,
            context_window=1048576,
            priority=10,
            is_free=True,
            rate_limit_rpm=60,
            rate_limit_rpd=1500
        ),
        ModelConfig(
            provider=ModelProvider.GEMINI,
            model_id="gemini-2.0-flash-lite",
            display_name="Gemini 2.0 Flash Lite",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT
            ],
            max_tokens=8192,
            context_window=1048576,
            priority=15,
            is_free=True,
            rate_limit_rpm=60,
            rate_limit_rpd=1500
        ),
        
        # Groq模型 (免费: 14400 req/day)
        ModelConfig(
            provider=ModelProvider.GROQ,
            model_id="llama-3.3-70b-versatile",
            display_name="Llama 3.3 70B",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.STREAMING,
                ModelCapability.FUNCTION_CALLING
            ],
            max_tokens=32768,
            context_window=128000,
            priority=20,
            is_free=True,
            rate_limit_rpm=30,
            rate_limit_rpd=1000
        ),
        ModelConfig(
            provider=ModelProvider.GROQ,
            model_id="deepseek-r1-distill-llama-70b",
            display_name="DeepSeek R1 Distill",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.STREAMING
            ],
            max_tokens=131072,
            context_window=128000,
            priority=25,
            is_free=True,
            rate_limit_rpm=30,
            rate_limit_rpd=14400
        ),
        ModelConfig(
            provider=ModelProvider.GROQ,
            model_id="gemma2-9b-it",
            display_name="Gemma 2 9B",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.STREAMING
            ],
            max_tokens=8192,
            context_window=8192,
            priority=30,
            is_free=True,
            rate_limit_rpm=30,
            rate_limit_rpd=14400
        ),
        
        # Ollama本地模型 (无限制)
        ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_id="llama3.1",
            display_name="Llama 3.1 (本地)",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.STREAMING
            ],
            max_tokens=4096,
            context_window=128000,
            priority=50,  # 本地模型优先级较低，作为后备
            is_free=True,
            rate_limit_rpm=1000,
            rate_limit_rpd=100000
        ),
    ]
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.clients: Dict[str, BaseModelClient] = {}
        self._init_models()
    
    def _init_models(self):
        """初始化模型"""
        for config in self.DEFAULT_MODELS:
            self.models[config.model_id] = config
        
        logger.info(f"初始化完成，共 {len(self.models)} 个模型")
    
    def setup_clients(self):
        """
        设置API客户端
        
        从环境变量读取API密钥
        """
        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            for model_id, config in self.models.items():
                if config.provider == ModelProvider.GEMINI:
                    self.clients[model_id] = GeminiClient(config, gemini_key)
                    logger.info(f"初始化Gemini客户端: {model_id}")
        
        # Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            for model_id, config in self.models.items():
                if config.provider == ModelProvider.GROQ:
                    self.clients[model_id] = GroqClient(config, groq_key)
                    logger.info(f"初始化Groq客户端: {model_id}")
        
        # Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        for model_id, config in self.models.items():
            if config.provider == ModelProvider.OLLAMA:
                self.clients[model_id] = OllamaClient(config, ollama_url)
                logger.info(f"初始化Ollama客户端: {model_id}")
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        request_capability: Optional[ModelCapability] = None
    ) -> ChatResponse:
        """
        执行对话
        
        Args:
            messages: 消息列表
            model: 指定模型，None则自动选择
            temperature: 温度
            max_tokens: 最大token数
            stream: 是否流式
            request_capability: 需要的模型能力
        
        Returns:
            聊天响应
        """
        request = ChatRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        # 选择模型
        selected_model = model or self._select_best_model(request_capability, stream)
        
        if selected_model not in self.clients:
            raise Exception(f"模型未初始化: {selected_model}")
        
        client = self.clients[selected_model]
        
        try:
            if stream:
                # 流式响应包装
                content_parts = []
                async for chunk in client.chat_stream(request):
                    content_parts.append(chunk)
                
                return ChatResponse(
                    content="".join(content_parts),
                    model=selected_model,
                    provider=client.config.provider.value
                )
            else:
                return await client.chat(request)
                
        except Exception as e:
            logger.error(f"模型 {selected_model} 调用失败: {e}")
            
            # 故障转移
            fallback_model = self._get_fallback_model(selected_model)
            if fallback_model and fallback_model != selected_model:
                logger.info(f"切换到备用模型: {fallback_model}")
                return await self.chat(
                    messages=messages,
                    model=fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
            
            raise
    
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式对话
        
        Yields:
            文本片段
        """
        request = ChatRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        selected_model = model or self._select_best_model(ModelCapability.STREAMING, True)
        
        if selected_model not in self.clients:
            raise Exception(f"模型未初始化: {selected_model}")
        
        client = self.clients[selected_model]
        
        try:
            async for chunk in client.chat_stream(request):
                yield chunk
        except Exception as e:
            logger.error(f"流式对话失败: {e}")
            raise
    
    def _select_best_model(
        self,
        capability: Optional[ModelCapability] = None,
        streaming: bool = False
    ) -> str:
        """
        选择最适合的模型
        
        策略：
        1. 优先可用且健康的模型
        2. 根据能力需求过滤
        3. 根据优先级排序
        """
        candidates = list(self.models.values())
        
        # 过滤未初始化的模型
        candidates = [m for m in candidates if m.model_id in self.clients]
        
        # 根据能力过滤
        if capability:
            candidates = [m for m in candidates if capability in m.capabilities]
        
        if streaming:
            candidates = [m for m in candidates if ModelCapability.STREAMING in m.capabilities]
        
        # 仅免费模型（按配置）
        candidates = [m for m in candidates if m.is_free]
        
        if not candidates:
            raise Exception("没有可用的模型")
        
        # 按优先级排序
        candidates.sort(key=lambda m: m.priority)
        
        return candidates[0].model_id
    
    def _get_fallback_model(self, current_model: str) -> Optional[str]:
        """获取备用模型"""
        current_config = self.models.get(current_model)
        if not current_config:
            return None
        
        # 找到同类型但优先级稍低的模型
        same_provider = [
            m for m in self.models.values()
            if m.provider == current_config.provider
            and m.model_id != current_model
            and m.model_id in self.clients
        ]
        
        if same_provider:
            same_provider.sort(key=lambda m: m.priority)
            return same_provider[0].model_id
        
        # 跨提供商备用
        all_models = [
            m for m in self.models.values()
            if m.model_id != current_model
            and m.model_id in self.clients
        ]
        
        if all_models:
            all_models.sort(key=lambda m: m.priority)
            return all_models[0].model_id
        
        return None
    
    async def health_check(self) -> Dict[str, bool]:
        """检查所有模型健康状态"""
        results = {}
        
        for model_id, client in self.clients.items():
            try:
                healthy = await client.health_check()
                results[model_id] = healthy
            except:
                results[model_id] = False
        
        return results
    
    def get_available_models(self) -> List[Dict]:
        """获取可用模型列表"""
        return [
            config.to_dict()
            for config in self.models.values()
            if config.model_id in self.clients
        ]
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """获取模型信息"""
        config = self.models.get(model_id)
        if config:
            return config.to_dict()
        return None


# 全局管理器实例
ai_model_manager = AIModelManager()
