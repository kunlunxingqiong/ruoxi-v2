"""
🌸 若曦V2 WebSocket实时通信
支持流式聊天和实时通知
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from core.exceptions import ValidationException
from core.log_manager import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    WebSocket连接管理器

    管理所有活跃的WebSocket连接
    """

    def __init__(self):
        # 活跃连接: {user_id: {websocket}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # 会话连接: {session_id: {websocket}} (用于聊天会话)
        self.session_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """接受新连接"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        logger.info(
            f"🔌 WebSocket连接 | 用户: {user_id} | 当前连接: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket, user_id: str = "anonymous"):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # 从所有会话中移除
        for session_id, connections in self.session_connections.items():
            connections.discard(websocket)

        logger.info(
            f"🔌 WebSocket断开 | 用户: {user_id} | 剩余连接: {len(self.active_connections)}"
        )

    def join_session(self, websocket: WebSocket, session_id: str):
        """加入会话房间"""
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()

        self.session_connections[session_id].add(websocket)
        logger.debug(f"🏠 加入会话 | {session_id}")

    def leave_session(self, websocket: WebSocket, session_id: str):
        """离开会话房间"""
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def send_to_user(self, user_id: str, message: dict):
        """发送消息给特定用户"""
        if user_id in self.active_connections:
            disconnected = set()

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)

            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)

    async def send_to_session(self, session_id: str, message: dict):
        """发送消息给会话中的所有用户"""
        if session_id in self.session_connections:
            disconnected = set()

            for connection in self.session_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)

            # 清理
            for conn in disconnected:
                self.session_connections[session_id].discard(conn)

            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def broadcast(self, message: dict):
        """广播消息给所有用户"""
        disconnected_users = []

        for user_id, connections in self.active_connections.items():
            disconnected = set()

            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)

            # 清理
            for conn in disconnected:
                connections.discard(conn)

            if not connections:
                disconnected_users.append(user_id)

        # 删除空用户
        for user_id in disconnected_users:
            del self.active_connections[user_id]

    def get_stats(self) -> dict:
        """获取连接统计"""
        total_users = len(self.active_connections)
        total_connections = sum(
            len(conns) for conns in self.active_connections.values()
        )
        total_sessions = len(self.session_connections)

        return {
            "total_users": total_users,
            "total_connections": total_connections,
            "active_sessions": total_sessions,
            "timestamp": datetime.utcnow().isoformat(),
        }


# 全局连接管理器
manager = ConnectionManager()


class ChatWebSocket:
    """
    聊天WebSocket处理器

    处理实时聊天消息和流式AI响应
    """

    async def handle(
        self, websocket: WebSocket, session_id: str, user_id: str = "anonymous"
    ):
        """
        处理WebSocket连接

        消息格式:
        {
            "type": "message",      // message/typing/heartbeat
            "content": "...",        // 消息内容
            "use_memory": true       // 是否使用记忆
        }
        """
        await manager.connect(websocket, user_id)
        manager.join_session(websocket, session_id)

        try:
            # 发送连接成功消息
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "session_id": session_id,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            while True:
                # 接收消息
                data = await websocket.receive_text()

                try:
                    message_data = json.loads(data)
                    msg_type = message_data.get("type", "message")

                    if msg_type == "message":
                        # 处理聊天消息
                        await self._handle_chat_message(
                            websocket, session_id, user_id, message_data
                        )

                    elif msg_type == "typing":
                        # 用户正在输入，通知会话中的其他人
                        await manager.send_to_session(
                            session_id,
                            {
                                "type": "typing",
                                "user_id": user_id,
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        )

                    elif msg_type == "heartbeat":
                        # 心跳响应
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )

                    else:
                        await websocket.send_json(
                            {"type": "error", "message": f"未知消息类型: {msg_type}"}
                        )

                except json.JSONDecodeError:
                    await websocket.send_json(
                        {"type": "error", "message": "无效的JSON格式"}
                    )

        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            manager.leave_session(websocket, session_id)

            # 通知会话其他人
            await manager.send_to_session(
                session_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def _handle_chat_message(
        self, websocket: WebSocket, session_id: str, user_id: str, message_data: dict
    ):
        """处理聊天消息 (支持流式响应)"""
        content = message_data.get("content", "")
        use_memory = message_data.get("use_memory", True)

        if not content:
            return

        logger.info(
            f"💬 WS消息 | 会话: {session_id} | 用户: {user_id} | 长度: {len(content)}"
        )

        # 确认收到消息
        await websocket.send_json(
            {
                "type": "message_received",
                "message_id": f"msg_{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # TODO: 调用AI模型获取流式回复
        # 模拟流式响应
        await self._simulate_stream_response(websocket, session_id, user_id)

    async def _simulate_stream_response(
        self, websocket: WebSocket, session_id: str, user_id: str
    ):
        """
        模拟流式AI响应

        真实实现中应该调用AI模型的流式接口
        """
        response_text = "🌸 曦曦收到消息啦~ 这是WebSocket实时回复！"

        # 逐字发送，模拟打字效果
        await websocket.send_json(
            {"type": "response_start", "timestamp": datetime.utcnow().isoformat()}
        )

        sent_text = ""
        for char in response_text:
            sent_text += char

            await websocket.send_json(
                {
                    "type": "response_chunk",
                    "content": char,
                    "partial": sent_text,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # 模拟打字延迟
            await asyncio.sleep(0.05)

        # 发送完成消息
        await websocket.send_json(
            {
                "type": "response_complete",
                "full_content": response_text,
                "model_used": "gemini-2.0-flash",
                "tokens_used": len(response_text),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


# 创建处理器实例
chat_websocket = ChatWebSocket()


# ========== WebSocket路由处理函数 ==========


async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket端点

    客户端连接示例:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/chat/session_123');

    ws.onopen = () => {
        ws.send(JSON.stringify({
            type: 'message',
            content: '你好若曦！',
            use_memory: true
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
    ```
    """
    # TODO: 从token获取user_id
    user_id = "anonymous"  # 实际应该从认证token解析

    await chat_websocket.handle(websocket, session_id, user_id)


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 WebSocket模块")
    print("=" * 60)

    print("\n【功能】")
    print("  - 实时聊天消息")
    print("  - 流式AI响应 (逐字显示)")
    print("  - 在线用户管理")
    print("  - 会话房间 (多人聊天)")
    print("  - 心跳检测")
    print("  - 打字指示器")

    print("\n【消息类型】")
    print("  - connection: 连接状态")
    print("  - message: 聊天消息")
    print("  - message_received: 消息确认")
    print("  - response_start: AI开始回复")
    print("  - response_chunk: AI流式片段")
    print("  - response_complete: AI回复完成")
    print("  - typing: 用户正在输入")
    print("  - heartbeat/pong: 心跳")

    print("\n【使用方式】")
    print("  from websocket.chat_ws import websocket_endpoint")
    print("  app.websocket('/ws/chat/{session_id}')(websocket_endpoint)")

    print("\n" + "=" * 60)
