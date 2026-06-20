"""
🌸 若曦V2 - 聊天API
对话接口端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel

from core.chat.chat_engine import chat_service, ChatMode
from core.notification.notification_service import notification_service
from core.websocket.connection_manager import connection_manager
from platform.backend.core_auth.jwt_auth import get_current_user


router = APIRouter(prefix="/chat", tags=["聊天"])


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    mode: str = "casual"
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应"""
    message_id: str
    content: str
    role: str
    sources: List[dict]
    context: dict
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """历史响应"""
    success: bool
    messages: List[dict]
    total: int


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user = Depends(get_current_user)
):
    """
    发送聊天消息
    
    模式:
    - `casual` - 闲聊
    - `health` - 健康咨询
    - `emotional` - 情绪陪伴
    - `professional` - 专业医疗
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    # 验证模式
    valid_modes = [m.value for m in ChatMode]
    if request.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"无效模式，可选: {valid_modes}")
    
    # 调用聊天服务
    response = await chat_service.send_message(
        user_id=str(current_user.user_id),
        message=request.message,
        mode=request.mode,
        stream=request.stream
    )
    
    # 通过WebSocket推送
    await connection_manager.send_to_user(
        str(current_user.user_id),
        {
            "type": "chat_message",
            "message": response
        }
    )
    
    return ChatResponse(**response)


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """获取聊天历史"""
    messages = await chat_service.get_history(
        user_id=str(current_user.user_id),
        limit=limit
    )
    
    return ChatHistoryResponse(
        success=True,
        messages=messages,
        total=len(messages)
    )


@router.delete("/history")
async def clear_chat_history(
    current_user = Depends(get_current_user)
):
    """清除聊天历史"""
    success = await chat_service.clear_history(str(current_user.user_id))
    
    if not success:
        raise HTTPException(status_code=404, detail="没有找到历史记录")
    
    return {
        "success": True,
        "message": "聊天历史已清除"
    }


@router.post("/emotion-check")
async def emotion_checkin(
    mood: str,
    note: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    情绪打卡
    
    mood: 情绪状态 (happy/sad/neutral/anxious/angry)
    """
    user_id = str(current_user.user_id)
    
    # 存储情绪记录到记忆系统
    from core.memory.memory_manager import memory_manager
    await memory_manager.store_interaction(
        user_id=user_id,
        content=f"情绪打卡: {mood}" + (f" - {note}" if note else ""),
        source="emotion_checkin",
        importance=0.7,
        metadata={"mood": mood}
    )
    
    # 根据情绪提供响应
    responses = {
        "happy": "🌸 看到你开心，曦曦也很高兴呢~",
        "sad": "🌸 抱抱你...愿意和曦曦说说吗？",
        "neutral": "🌸 平稳的一天也是好的一天~",
        "anxious": "🌸 深呼吸，曦曦在这里陪着你",
        "angry": "🌸 平复一下情绪，曦曦听你讲"
    }
    
    response_text = responses.get(mood, "🌸 曦曦收到了你的情绪记录")
    
    # 如果有笔记，AI进一步回复
    if note:
        ai_response = await chat_service.send_message(
            user_id=user_id,
            message=f"我今天的情绪是{mood}，因为{note}",
            mode="emotional"
        )
        response_text = ai_response["content"]
    
    return {
        "success": True,
        "mood": mood,
        "response": response_text,
        "timestamp": "..."
    }


@router.get("/modes")
async def get_chat_modes():
    """获取所有聊天模式"""
    return {
        "success": True,
        "modes": [
            {
                "id": "casual",
                "name": "闲聊模式",
                "description": "和若曦随便聊聊",
                "icon": "💬"
            },
            {
                "id": "health",
                "name": "健康咨询",
                "description": "健康相关问题",
                "icon": "🩺"
            },
            {
                "id": "emotional",
                "name": "情绪陪伴",
                "description": "情绪支持和倾听",
                "icon": "🌸"
            },
            {
                "id": "professional",
                "name": "专业医疗",
                "description": "专业医疗信息",
                "icon": "🏥"
            }
        ]
    }


@router.get("/suggestions")
async def get_chat_suggestions(
    current_user = Depends(get_current_user)
):
    """获取聊天建议（快捷输入）"""
    # 基于用户历史和健康数据提供建议
    suggestions = [
        "今天血压怎么样？",
        "帮我记录今天的体重",
        "最近睡眠有点不好",
        "要提醒我吃药吗？",
        "分析一下昨天的体检报告",
        "今天心情不太好..."
    ]
    
    return {
        "success": True,
        "suggestions": suggestions[:6]
    }


@router.post("/voice")
async def voice_chat(
    audio_data: bytes,
    current_user = Depends(get_current_user)
):
    """语音聊天（TTS/STT）"""
    # TODO: 集成语音识别和合成
    return {
        "success": True,
        "message": "语音功能开发中",
        "note": "请使用文字聊天"
    }
