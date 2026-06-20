"""
🌸 若曦V2 聊天API
与若曦对话的核心接口
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.log_manager import get_logger
from core.exceptions import ValidationException, AIException
from core.ai.model_manager import ai_manager
from core.ai.streaming import StreamingProcessor
from core.memory.memory_manager import memory_manager
from core.auth import get_current_user, UserAuth

logger = get_logger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """单条聊天消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容", min_length=1)
    timestamp: Optional[str] = Field(default=None, description="时间戳ISO格式")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=4096)
    session_id: Optional[str] = Field(default=None, description="会话ID，为空则创建新会话")
    context: Optional[List[ChatMessage]] = Field(default=[], description="上下文消息")
    use_memory: bool = Field(default=True, description="是否使用记忆")
    stream: bool = Field(default=False, description="是否流式返回")


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool = Field(..., description="是否成功")
    session_id: str = Field(..., description="会话ID")
    message: ChatMessage = Field(..., description="若曦的回复")
    memory_used: bool = Field(default=False, description="是否使用了记忆")
    tokens_used: int = Field(default=0, description="Token消耗")
    model_used: str = Field(default="", description="使用的模型")
    response_time_ms: int = Field(default=0, description="响应时间毫秒")


class ChatIfno(BaseModel):
    """会话信息"""
    session_id: str
    created_at: str
    message_count: int = 0
    last_message_at: Optional[str] = None


# 内存存储（实际应该使用数据库）
chat_sessions: Dict[str, Dict] = {}


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: UserAuth = Depends(get_current_user)
):
    """
    与若曦聊天
    
    发送消息给若曦，获取AI回复
    
    **请求示例:**
    ```json
    {
        "message": "你好若曦，我今天头疼",
        "session_id": "可选的会话ID",
        "use_memory": true
    }
    ```
    
    **响应示例:**
    ```json
    {
        "success": true,
        "session_id": "abc123",
        "message": {
            "role": "assistant",
            "content": "抱抱你，头疼难受呢\n建议先休息一下，如果持续的话建议看医生哦",
            "timestamp": "2026-06-21T02:56:44"
        },
        "tokens_used": 150,
        "model_used": "gemini-2.0-flash"
    }
    ```
    """
    import time
    import uuid
    
    start_time = time.time()
    
    # 参数验证
    if not request.message or len(request.message) > 4096:
        raise ValidationException("消息长度需在1-4096字符之间")
    
    # 生成或获取会话ID
    session_id = request.session_id or str(uuid.uuid4())[:12]
    
    # 初始化会话
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "created_at": datetime.utcnow(),
            "messages": [],
            "message_count": 0
        }
    
    # 记录用户消息
    chat_sessions[session_id]["messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow()
    })
    chat_sessions[session_id]["message_count"] += 1
    
    logger.info(f"💬 聊天请求 | 会话: {session_id} | 消息长度: {len(request.message)}")
    
    # 调用AI模型获取回复
    try:
        # 构建消息列表
        messages = [
            {"role": "system", "content": "你是若曦，一个温柔体贴的AI医生朋友。你擅长健康管理、情感陪伴和日常对话。回答要温暖、友善，适当使用emoji。"},
            {"role": "user", "content": request.message}
        ]
        
        if request.context:
            # 添加上下文
            for msg in request.context:
                messages.append({"role": msg.role, "content": msg.content})
        
        # 调用AI管理器生成回复
        ai_response = await ai_manager.generate(
            messages=messages,
            stream=request.stream,
            use_cache=True
        )
        
        # 构建回复
        assistant_message = ChatMessage(
            role="assistant",
            content=ai_response.content,
            timestamp=datetime.utcnow().isoformat()
        )
        
        tokens_used = ai_response.tokens_output
        model_used = ai_response.model_used
        
        response_time = int((time.time() - start_time) * 1000)
        
        # 记录回复
        chat_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": assistant_message.content,
            "timestamp": datetime.utcnow()
        })
        chat_sessions[session_id]["last_message_at"] = datetime.utcnow()
        
        logger.info(f"✅ 回复成功 | 会话: {session_id} | 耗时: {response_time}ms")
        
        return ChatResponse(
            success=True,
            session_id=session_id,
            message=assistant_message,
            memory_used=request.use_memory,
            tokens_used=tokens_used,
            model_used=model_used,
            response_time_ms=max(response_time, ai_response.response_time_ms)
        )
        
    except Exception as e:
        logger.error(f"❌ AI处理失败: {e}")
        raise AIException(f"模型调用失败: {e}", {"session_id": session_id})


@router.get("/sessions", response_model=List[ChatIfno])
async def list_sessions():
    """
    获取所有会话列表
    
    返回当前所有活跃的聊天会话
    """
    sessions = []
    for session_id, session_data in chat_sessions.items():
        sessions.append(ChatIfno(
            session_id=session_id,
            created_at=session_data["created_at"].isoformat() if isinstance(session_data["created_at"], datetime) else str(session_data["created_at"]),
            message_count=session_data.get("message_count", 0),
            last_message_at=session_data.get("last_message_at", datetime.utcnow()).isoformat() if isinstance(session_data.get("last_message_at"), datetime) else None
        ))
    
    return sessions


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    获取特定会话详情
    
    包括会话中的所有消息
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = chat_sessions[session_id]
    return {
        "session_id": session_id,
        "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else session["created_at"],
        "message_count": session.get("message_count", 0),
        "messages": [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat() if isinstance(msg["timestamp"], datetime) else msg["timestamp"]
            }
            for msg in session.get("messages", [])
        ]
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    del chat_sessions[session_id]
    logger.info(f"🗑️ 会话删除: {session_id}")
    
    return {"success": True, "message": "会话已删除"}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """
    获取聊天历史
    
    - **session_id**: 会话ID
    - **limit**: 返回消息数量限制 (默认50)
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = chat_sessions[session_id].get("messages", [])
    
    # 转换并限制数量
    history = [
        {
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": msg["timestamp"].isoformat() if isinstance(msg["timestamp"], datetime) else msg["timestamp"]
        }
        for msg in messages[-limit:]
    ]
    
    return {
        "session_id": session_id,
        "total_messages": len(messages),
        "returned": len(history),
        "messages": history
    }
