"""
🌸 若曦V2 流式聊天API
支持Server-Sent Events流式响应
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List

from core.ai.streaming import StreamingProcessor, StreamChunk
from core.ai.model_manager import ai_manager
from core.memory.memory_manager import memory_manager
from core.auth import get_current_user, UserAuth
from core.log_manager import get_logger

logger = get_logger(__name__)

router = APIRouter()


class StreamChatRequest(BaseModel):
    """流式聊天请求"""
    message: str = Field(..., description="用户消息", min_length=1)
    session_id: Optional[str] = Field(default=None, description="会话ID")
    use_memory: bool = Field(default=True, description="是否使用记忆")


@router.post("/stream")
async def chat_stream(
    request: StreamChatRequest,
    user: UserAuth = Depends(get_current_user)
):
    """
    流式聊天 (SSE)
    
    实时逐字输出若曦的回复，创造打字效果。
    
    **使用方式 (JavaScript):**
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/stream', {
        method: 'POST',
        body: JSON.stringify({message: "你好"})
    });
    
    eventSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.is_start) {
            console.log('开始生成...');
        } else if (data.is_end) {
            console.log('生成完成');
            eventSource.close();
        } else {
            appendToChat(data.content);  // 逐字显示
        }
    };
    ```
    """
    session_id = request.session_id or f"stream_{user.user_id}_{int(datetime.utcnow().timestamp())}"
    
    # 添加到上下文
    memory_manager.add_to_context(session_id, user.user_id, "user", request.message)
    
    # 构建完整上下文
    messages = memory_manager.build_context_for_ai(
        user_id=user.user_id,
        session_id=session_id,
        query=request.message,
        include_memories=request.use_memory
    )
    
    # 创建流式处理器
    processor = StreamingProcessor()
    generator = processor.stream_chat_completion(messages, ai_manager)
    
    # 返回SSE响应
    return processor.create_sse_response(generator)


from datetime import datetime


async def save_response_to_memory(
    session_id: str,
    user_id: str,
    content: str
):
    """保存AI回复到记忆"""
    memory_manager.add_to_context(session_id, user_id, "assistant", content)
    # 定期保存到长期记忆
    if len(memory_manager.get_or_create_context(session_id, user_id).messages) % 5 == 0:
        memory_manager.save_conversation_to_memory(session_id, user_id)