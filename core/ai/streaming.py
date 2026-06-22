"""
🌸 若曦V2 流式AI响应处理器
支持 SSE (Server-Sent Events) 和 WebSocket 流式输出
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, Optional

from fastapi import Request
from fastapi.responses import StreamingResponse

from core.exceptions import AIException
from core.log_manager import get_logger

logger = get_logger(__name__)


@dataclass
class StreamChunk:
    """流式数据块"""

    content: str
    is_start: bool = False
    is_end: bool = False
    metadata: Dict[str, Any] = None

    def to_sse(self) -> str:
        """转换为SSE格式"""
        data = {
            "content": self.content,
            "is_start": self.is_start,
            "is_end": self.is_end,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if self.metadata:
            data.update(self.metadata)

        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def to_ws(self) -> Dict:
        """转换为WebSocket格式"""
        result = {
            "type": "stream_chunk",
            "content": self.content,
            "is_start": self.is_start,
            "is_end": self.is_end,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if self.metadata:
            result.update(self.metadata)
        return result


class StreamingProcessor:
    """
    流式响应处理器

    支持多种形式:
    1. SSE (Server-Sent Events) - HTTP流式
    2. WebSocket - 双向实时通信
    3. Callback - 回调函数式
    """

    def __init__(self):
        self.retry_count = 3
        self.chunk_size = 10  # 每块字符数

    async def stream_chat_completion(
        self, messages: list, ai_manager, model_config: Optional[Dict] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        流式聊天完成

        Args:
            messages: 消息列表
            ai_manager: AI模型管理器
            model_config: 额外模型配置

        Yields:
            StreamChunk: 流式数据块
        """
        try:
            # 发送开始标记
            yield StreamChunk(
                content="",
                is_start=True,
                metadata={
                    "model": (
                        model_config.get("model", "default")
                        if model_config
                        else "default"
                    )
                },
            )

            # 获取AI回复 (非流式模拟，真实实现需接入流式API)
            response = await ai_manager.generate(
                messages=messages, stream=False  # 当前模拟，实际应启用流式
            )

            if not response.success:
                raise AIException(f"AI生成失败: {response.error_message}")

            content = response.content

            # 分块输出，模拟打字效果
            for i in range(0, len(content), self.chunk_size):
                chunk = content[i : i + self.chunk_size]

                # 模拟一定的延迟，创造打字感
                await asyncio.sleep(0.03)  # 30ms每块

                yield StreamChunk(content=chunk)

            # 发送结束标记
            yield StreamChunk(
                content="",
                is_end=True,
                metadata={
                    "tokens_used": response.tokens_output,
                    "model_used": response.model_used,
                    "response_time_ms": response.response_time_ms,
                    "cached": response.cached,
                },
            )

        except Exception as e:
            logger.error(f"🔴 流式生成错误: {e}")
            yield StreamChunk(
                content=f"\n\n[生成出错: {str(e)}]",
                is_end=True,
                metadata={"error": str(e)},
            )

    def create_sse_response(
        self, generator: AsyncGenerator[StreamChunk, None]
    ) -> StreamingResponse:
        """
        创建SSE响应

        使用方式:
        ```python
        @router.post("/chat/stream")
        async def chat_stream(request: ChatRequest):
            processor = StreamingProcessor()
            generator = processor.stream_chat_completion(messages, ai_manager)
            return processor.create_sse_response(generator)
        ```
        """

        async def sse_generator():
            """SSE格式生成器"""
            try:
                async for chunk in generator:
                    yield chunk.to_sse()
            except Exception as e:
                logger.error(f"🔴 SSE生成错误: {e}")
                error_chunk = StreamChunk(
                    content="", is_end=True, metadata={"error": str(e)}
                )
                yield error_chunk.to_sse()

        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            },
        )

    async def stream_to_websocket(
        self, generator: AsyncGenerator[StreamChunk, None], websocket
    ):
        """
        流式输出到WebSocket

        Args:
            generator: 流式生成器
            websocket: WebSocket连接
        """
        try:
            async for chunk in generator:
                await websocket.send_json(chunk.to_ws())
        except Exception as e:
            logger.error(f"🔴 WebSocket流式错误: {e}")
            try:
                await websocket.send_json(
                    {"type": "stream_error", "error": str(e), "is_end": True}
                )
            except:
                pass  # WebSocket已关闭

    async def generate_with_progress(
        self,
        messages: list,
        ai_manager,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        带进度回调的生成

        用于需要进度反馈的场景 (如长文生成)

        Args:
            messages: 消息列表
            ai_manager: AI模型管理器
            progress_callback: 进度回调函数 (current, total)

        Returns:
            完整内容
        """
        full_content = []
        token_count = 0
        expected_tokens = 500  # 预估token数

        generator = self.stream_chat_completion(messages, ai_manager)

        async for chunk in generator:
            full_content.append(chunk.content)
            token_count += len(chunk.content) // 4  # 粗略估算

            if progress_callback and not chunk.is_end:
                progress_callback(min(token_count, expected_tokens), expected_tokens)

        return "".join(full_content)


class TokenStreamBuffer:
    """
    Token流缓冲区

    用于优化流式输出，减少网络请求次数:
    - 收集小token
    - 达到阈值或超时时批量发送
    """

    def __init__(self, max_buffer_size: int = 20, flush_interval_ms: int = 100):
        self.buffer: list = []
        self.max_buffer_size = max_buffer_size
        self.flush_interval_ms = flush_interval_ms
        self.last_flush_time = datetime.utcnow()

    async def add(self, token: str) -> Optional[str]:
        """添加token，如果达到阈值则返回批量内容"""
        self.buffer.append(token)

        # 检查是否需要刷新
        should_flush = (
            len(self.buffer) >= self.max_buffer_size
            or (datetime.utcnow() - self.last_flush_time).total_seconds() * 1000
            >= self.flush_interval_ms
        )

        if should_flush:
            return await self.flush()

        return None

    async def flush(self) -> str:
        """强制刷新缓冲区"""
        if not self.buffer:
            return ""

        content = "".join(self.buffer)
        self.buffer = []
        self.last_flush_time = datetime.utcnow()

        return content

    def is_empty(self) -> bool:
        """缓冲区是否为空"""
        return len(self.buffer) == 0


# 客户端使用示例代码 (JavaScript)
CLIENT_EXAMPLE = """
// ==================== SSE 客户端示例 ====================

// 方式1: EventSource (简单)
const eventSource = new EventSource('/api/v1/chat/stream');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.is_start) {
        console.log('开始生成...');
    } else if (data.is_end) {
        console.log('生成完成', data.tokens_used);
        eventSource.close();
    } else {
        appendToChat(data.content);  // 逐字显示
    }
};

eventSource.onerror = (error) => {
    console.error('SSE错误:', error);
    eventSource.close();
};

// 方式2: Fetch + ReadableStream (更灵活)
async function streamChat(message) {
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message})
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                appendToChat(data.content);
            }
        }
    }
}

// ==================== WebSocket 客户端示例 ====================

const ws = new WebSocket('ws://localhost:8000/ws/chat/session_123');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'message',
        content: '你好若曦',
        stream: true  // 启用流式
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'connection':
            console.log('已连接:', data.session_id);
            break;
        case 'stream_chunk':
            if (data.is_start) {
                console.log('开始生成...');
            } else if (data.is_end) {
                console.log('生成完成:', data.tokens_used);
            } else {
                appendToChat(data.content);
            }
            break;
    }
};
"""


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 流式响应处理器")
    print("=" * 60)

    print("\n【支持格式】")
    print("  1. SSE (Server-Sent Events) - HTTP流式")
    print("  2. WebSocket - 双向实时通信")
    print("  3. Callback - 回调函数式")

    print("\n【特性】")
    print("  ✅ 分块输出，打字效果")
    print("  ✅ Token缓冲区优化")
    print("  ✅ 错误处理")
    print("  ✅ 进度回调")

    print("\n【客户端示例】")
    print("  见代码末尾 CLIENT_EXAMPLE 变量")

    print("\n" + "=" * 60)
