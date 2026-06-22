"""
🌸 若曦V2 - AI模型管理API
模型管理及相关接口
"""

from platform.backend.core_auth.jwt_auth import get_current_user
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.ai.ai_model_manager import ChatMessage, ModelCapability, ai_model_manager

router = APIRouter(prefix="/ai", tags=["AI模型"])


@router.get("/models")
async def get_available_models(current_user=Depends(get_current_user)):
    """
    获取可用AI模型列表

    返回所有已配置且可用的AI模型信息
    """
    models = ai_model_manager.get_available_models()

    return {
        "success": True,
        "models": models,
        "count": len(models),
        "recommendations": {
            "default": "gemini-2.0-flash",
            "fast": "gemini-2.0-flash-lite",
            "capable": "llama-3.3-70b-versatile",
            "local": "llama3.1",
        },
    }


@router.get("/models/{model_id}")
async def get_model_info(model_id: str, current_user=Depends(get_current_user)):
    """
    获取指定模型详细信息
    """
    info = ai_model_manager.get_model_info(model_id)

    if not info:
        raise HTTPException(status_code=404, detail="模型不存在")

    return {"success": True, "model": info}


@router.post("/chat")
async def chat_completion(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    current_user=Depends(get_current_user),
):
    """
    AI对话接口

    统一的对话接口，自动路由到最佳可用模型

    请求示例:
    ```json
    {
      "messages": [
        {"role": "system", "content": "你是若曦，AI医生朋友"},
        {"role": "user", "content": "我的血压120/80正常吗？"}
      ],
      "model": "gemini-2.0-flash",
      "temperature": 0.7
    }
    ```
    """
    try:
        # 转换消息格式
        chat_messages = [
            ChatMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                name=msg.get("name"),
            )
            for msg in messages
        ]

        # 执行对话
        response = await ai_model_manager.chat(
            messages=chat_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        return {"success": True, "response": response.to_dict()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    messages: List[dict],
    model: Optional[str] = None,
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = None,
    current_user=Depends(get_current_user),
):
    """
    流式AI对话接口

    返回SSE格式的流式响应
    """
    from fastapi.responses import StreamingResponse

    async def generate():
        try:
            chat_messages = [
                ChatMessage(
                    role=msg.get("role", "user"), content=msg.get("content", "")
                )
                for msg in messages
            ]

            async for chunk in ai_model_manager.chat_stream(
                messages=chat_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield f"data: {chunk}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/health")
async def check_model_health(current_user=Depends(get_current_user)):
    """
    检查AI模型健康状态

    返回各模型的可用性状态
    """
    health_status = await ai_model_manager.health_check()

    healthy_count = sum(1 for v in health_status.values() if v)
    total_count = len(health_status)

    return {
        "success": True,
        "health_status": health_status,
        "summary": {
            "healthy": healthy_count,
            "unhealthy": total_count - healthy_count,
            "total": total_count,
            "availability": f"{healthy_count}/{total_count}",
        },
    }


@router.post("/health/{model_id}")
async def check_single_model_health(
    model_id: str, current_user=Depends(get_current_user)
):
    """
    检查单个模型健康状态
    """
    if model_id not in ai_model_manager.clients:
        raise HTTPException(status_code=404, detail="模型不存在或未初始化")

    client = ai_model_manager.clients[model_id]
    healthy = await client.health_check()

    return {
        "success": True,
        "model_id": model_id,
        "healthy": healthy,
        "provider": client.config.provider.value,
    }


@router.get("/capabilities")
async def get_capabilities(current_user=Depends(get_current_user)):
    """
    获取所有模型能力列表
    """
    capabilities = [
        {"id": "chat", "name": "对话", "description": "基础对话能力"},
        {"id": "streaming", "name": "流式输出", "description": "支持流式响应"},
        {"id": "vision", "name": "图像理解", "description": "理解图片内容"},
        {"id": "function", "name": "函数调用", "description": "调用外部函数"},
        {"id": "long_context", "name": "长上下文", "description": "支持长文本"},
    ]

    return {"success": True, "capabilities": capabilities}


@router.post("/translate")
async def translate_text(
    text: str,
    target_language: str = Query("zh", description="目标语言: zh/en/ja/ko"),
    model: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """
    文本翻译接口

    使用AI模型进行文本翻译
    """
    try:
        messages = [
            ChatMessage(
                role="system",
                content=f"You are a translator. Translate the following text to {target_language}. Only output the translation, no explanations.",
            ),
            ChatMessage(role="user", content=text),
        ]

        response = await ai_model_manager.chat(
            messages=messages, model=model, temperature=0.3  # 低温度确保准确性
        )

        return {
            "success": True,
            "original": text,
            "translated": response.content,
            "target_language": target_language,
            "model_used": response.model,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/summarize")
async def summarize_text(
    text: str,
    max_length: int = Query(200, ge=50, le=1000, description="摘要最大长度"),
    model: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """
    文本摘要接口

    生成文本摘要
    """
    try:
        messages = [
            ChatMessage(
                role="system",
                content=f"Summarize the following text in {max_length} characters or less. Be concise and capture the main points.",
            ),
            ChatMessage(role="user", content=text),
        ]

        response = await ai_model_manager.chat(
            messages=messages, model=model, temperature=0.5
        )

        return {
            "success": True,
            "original_length": len(text),
            "summary": response.content,
            "summary_length": len(response.content),
            "model_used": response.model,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {str(e)}")


@router.post("/analyze-health")
async def analyze_health_data(
    data: dict,
    data_type: str = Query(..., description="数据类型: bp/glucose/weight/sleep"),
    model: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """
    健康数据分析接口

    使用AI分析健康数据并提供建议
    """
    try:
        # 构建分析提示
        type_descriptions = {
            "bp": "血压数据",
            "glucose": "血糖数据",
            "weight": "体重数据",
            "sleep": "睡眠数据",
        }

        description = type_descriptions.get(data_type, "健康数据")

        prompt = f"""作为AI健康助手，分析以下{description}并提供专业建议。

数据: {json.dumps(data, ensure_ascii=False)}

请提供:
1. 数据解读（正常/异常）
2. 可能的原因分析
3. 健康建议
4. 是否需要就医提醒

回答要简洁专业，避免过度医疗建议。"""

        messages = [
            ChatMessage(
                role="system",
                content="你是一位专业的AI健康助手，提供准确的健康数据分析和建议。注意：这只是参考建议，不能替代医生诊断。",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        response = await ai_model_manager.chat(
            messages=messages, model=model, temperature=0.7
        )

        return {
            "success": True,
            "analysis": response.content,
            "data_type": data_type,
            "model_used": response.model,
            "disclaimer": "本分析仅供参考，不能替代专业医疗建议",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


# 导入json用于健康分析
import json
