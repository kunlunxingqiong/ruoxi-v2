"""
🌸 若曦V2 - AI模型管理API
多模型配置、健康检查、使用的API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from core.ai.model_manager import model_manager, ModelConfig, ModelProvider
from core.ai.models.base_model import Message
from platform.backend.core_auth.jwt_auth import get_current_user


router = APIRouter(prefix="/ai", tags=["AI模型"])


class ModelConfigRequest(BaseModel):
    """模型配置请求"""
    provider: str  # gemini, groq, ollama
    api_key: str
    model_name: str
    priority: int = 1
    base_url: Optional[str] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[dict]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    prefer_local: bool = False


@router.post("/models/register")
async def register_model(
    name: str,
    config: ModelConfigRequest,
    current_user = Depends(get_current_user)
):
    """注册AI模型"""
    
    # 转换provider字符串为枚举
    try:
        provider = ModelProvider(config.provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型提供商: {config.provider}"
        )
    
    model_config = ModelConfig(
        provider=provider,
        api_key=config.api_key,
        model_name=config.model_name,
        priority=config.priority,
        is_local=(provider == ModelProvider.OLLAMA),
        base_url=config.base_url
    )
    
    success = model_manager.register_model(name, model_config)
    
    if not success:
        raise HTTPException(status_code=400, detail="模型注册失败")
    
    return {
        "success": True,
        "message": f"模型 {name} 注册成功",
        "model_info": model_manager.get_model(name).get_info()
    }


@router.delete("/models/{name}")
async def unregister_model(
    name: str,
    current_user = Depends(get_current_user)
):
    """注销AI模型"""
    success = model_manager.unregister_model(name)
    
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    return {
        "success": True,
        "message": f"模型 {name} 已注销"
    }


@router.get("/models")
async def list_models(
    only_enabled: bool = True,
    current_user = Depends(get_current_user)
):
    """列出所有AI模型"""
    models = model_manager.list_models(only_enabled)
    
    return {
        "success": True,
        "models": models,
        "total": len(models)
    }


@router.get("/models/{name}")
async def get_model_info(
    name: str,
    current_user = Depends(get_current_user)
):
    """获取模型详细信息"""
    model = model_manager.get_model(name)
    
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    return {
        "success": True,
        "info": model.get_info()
    }


@router.post("/models/{name}/enable")
async def enable_model(
    name: str,
    current_user = Depends(get_current_user)
):
    """启用模型"""
    success = model_manager.enable_model(name)
    
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    return {
        "success": True,
        "message": f"模型 {name} 已启用"
    }


@router.post("/models/{name}/disable")
async def disable_model(
    name: str,
    current_user = Depends(get_current_user)
):
    """禁用模型"""
    success = model_manager.disable_model(name)
    
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    return {
        "success": True,
        "message": f"模型 {name} 已禁用"
    }


@router.get("/models/health/check")
async def health_check(
    current_user = Depends(get_current_user)
):
    """运行模型健康检查"""
    results = await model_manager.run_health_check()
    
    return {
        "success": True,
        "health_status": results,
        "summary": {
            "total": len(results),
            "healthy": sum(1 for v in results.values() if v),
            "unhealthy": sum(1 for v in results.values() if not v)
        }
    }


@router.get("/models/stats")
async def get_stats(
    current_user = Depends(get_current_user)
):
    """获取模型统计信息"""
    stats = model_manager.get_stats()
    
    return {
        "success": True,
        "stats": stats
    }


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user)
):
    """AI对话接口 - 自动选择最佳模型"""
    
    # 转换消息格式
    messages = [
        Message(role=msg.get("role", "user"), content=msg.get("content", ""))
        for msg in request.messages
    ]
    
    try:
        response = await model_manager.chat(
            messages=messages,
            model_name=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            prefer_local=request.prefer_local
        )
        
        return {
            "success": True,
            "content": response.content,
            "model": response.model,
            "provider": response.provider.value,
            "latency_ms": response.latency_ms,
            "usage": response.usage
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI调用失败: {str(e)}")


@router.get("/providers")
async def list_providers(
    current_user = Depends(get_current_user)
):
    """列出支持的模型提供商"""
    
    providers = {
        "gemini": {
            "name": "Google Gemini",
            "description": "Google提供的免费AI模型",
            "cost": "永久免费 (60请求/分钟)",
            "requires_api_key": True,
            "features": ["text", "vision", "function_calling"],
            "models": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        },
        "groq": {
            "name": "Groq Cloud",
            "description": "超高速AI推理平台",
            "cost": "永久免费 (14,400请求/天)",
            "requires_api_key": True,
            "features": ["text", "high_speed", "low_latency"],
            "models": ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "mixtral-8x7b"]
        },
        "ollama": {
            "name": "Ollama (本地)",
            "description": "本地LLM运行，完全免费",
            "cost": "永久免费 (无限制)",
            "requires_api_key": False,
            "features": ["text", "local", "privacy", "offline"],
            "models": ["llama3.3", "qwen2.5", "deepseek-r1", "mistral"],
            "setup": "需本地安装Ollama"
        }
    }
    
    return {
        "success": True,
        "providers": providers
    }


@router.get("/models/recommend")
async def recommend_model(
    current_user = Depends(get_current_user)
):
    """推荐最佳免费模型配置"""
    
    recommendation = {
        "default": {
            "name": "gemini",
            "provider": "Google Gemini",
            "model": "gemini-2.0-flash",
            "reason": "无需翻墙，国内可访问，速度稳定",
            "api_key_url": "https://aistudio.google.com/app/apikey",
            "priority": 1
        },
        "high_speed": {
            "name": "groq",
            "provider": "Groq Cloud",
            "model": "llama-3.3-70b-versatile",
            "reason": "超高速度，适合实时对话",
            "api_key_url": "https://console.groq.com/keys",
            "priority": 2
        },
        "privacy": {
            "name": "ollama",
            "provider": "Ollama (本地)",
            "model": "qwen2.5",
            "reason": "数据不出本机，极致隐私",
            "setup_guide": "https://ollama.com/download",
            "priority": 3
        }
    }
    
    return {
        "success": True,
        "recommendations": recommendation,
        "note": "所有推荐均为永久免费方案"
    }
