"""
🌸 若曦V2 - Gemini模型适配器
Google Gemini Pro - 永久免费模型
"""
import aiohttp
import time
from typing import AsyncGenerator, List, Optional

from core.ai.models.base_model import BaseModel, Message, ModelResponse, ModelProvider


class GeminiModel(BaseModel):
    """
    Gemini模型适配器
    
    免费额度:
    - Gemini Pro: 60请求/分钟
    - Gemini Pro Vision: 图片理解
    
    官网: https://ai.google.dev/
    """
    
    AVAILABLE_MODELS = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        super().__init__(api_key, model_name, ModelProvider.GEMINI)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._rate_limit_remaining = 60
    
    def _convert_messages(self, messages: List[Message]) -> tuple:
        """
        转换消息格式为Gemini格式
        Gemini使用content.parts结构
        """
        # 构建对话历史
        contents = []
        system_instruction = None
        
        for msg in messages:
            if msg.role == "system":
                # Gemini使用systemInstruction
                system_instruction = msg.content
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        
        return contents, system_instruction
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> ModelResponse:
        """
        调用Gemini进行对话
        
        文档: https://ai.google.dev/gemini-api/docs/text-generation
        """
        start_time = time.time()
        
        contents, system_instruction = self._convert_messages(messages)
        
        url = f"{self.base_url}/models/{self.model_name}:generateContent"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params={"key": self.api_key},
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API错误: {response.status} - {error_text}")
                
                result = await response.json()
                
                # 提取响应文本
                text = ""
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        text = "".join(
                            part.get("text", "")
                            for part in candidate["content"]["parts"]
                        )
                
                latency = int((time.time() - start_time) * 1000)
                
                return ModelResponse(
                    content=text,
                    model=self.model_name,
                    provider=self.provider,
                    latency_ms=latency
                )
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Gemini流式输出
        
        使用server-sent events
        """
        contents, system_instruction = self._convert_messages(messages)
        
        url = f"{self.base_url}/models/{self.model_name}:streamGenerateContent"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params={"key": self.api_key},
                json=payload
            ) as response:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data:'):
                        try:
                            import json
                            data = json.loads(line[5:])
                            if "candidates" in data:
                                for candidate in data["candidates"]:
                                    if "content" in candidate:
                                        for part in candidate["content"].get("parts", []):
                                            if "text" in part:
                                                yield part["text"]
                        except json.JSONDecodeError:
                            pass
    
    async def health_check(self) -> bool:
        """检查Gemini服务状态"""
        try:
            url = f"{self.base_url}/models/{self.model_name}"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params={"key": self.api_key}
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def get_info(self) -> dict:
        """获取模型信息"""
        info = super().get_info()
        info.update({
            "rate_limit": "60 requests/minute (免费)",
            "available_models": self.AVAILABLE_MODELS,
            "features": ["text", "vision", "function_calling"],
            "cost": "永久免费"
        })
        return info
