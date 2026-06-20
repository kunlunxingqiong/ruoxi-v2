"""
🌸 若曦V2 - WebSocket连接管理器
实时双向通信支持
"""
from typing import Dict, Set, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio
from fastapi import WebSocket


@dataclass
class WebSocketClient:
    """WebSocket客户端"""
    id: str
    websocket: WebSocket
    user_id: Optional[str]
    connected_at: datetime
    channels: Set[str]
    metadata: Dict[str, Any]


class ConnectionManager:
    """
    WebSocket连接管理器
    
    功能:
    - 多客户端连接管理
    - 频道订阅系统
    - 消息广播/定向发送
    - 心跳检测
    - 自动重连支持
    """
    
    def __init__(self):
        # 所有活跃连接
        self._connections: Dict[str, WebSocketClient] = {}
        # 按用户ID索引
        self._user_connections: Dict[str, Set[str]] = {}
        # 按频道索引
        self._channel_subscribers: Dict[str, Set[str]] = {}
        # 消息历史 (用于断线重连)
        self._message_history: Dict[str, List[Dict]] = {}
        # 心跳任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        # 统计
        self._stats = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> WebSocketClient:
        """
        建立新连接
        
        Args:
            websocket: WebSocket对象
            client_id: 客户端唯一ID
            user_id: 关联用户ID
            metadata: 附加元数据
        """
        await websocket.accept()
        
        client = WebSocketClient(
            id=client_id,
            websocket=websocket,
            user_id=user_id,
            connected_at=datetime.utcnow(),
            channels=set(),
            metadata=metadata or {}
        )
        
        self._connections[client_id] = client
        
        # 索引用户连接
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(client_id)
        
        self._stats["total_connections"] += 1
        
        # 发送欢迎消息
        await self.send_to_client(
            client_id,
            {
                "type": "connected",
                "client_id": client_id,
                "message": "🌸 若曦已连接，有什么可以帮你的吗？"
            }
        )
        
        return client
    
    async def disconnect(self, client_id: str):
        """断开连接"""
        if client_id not in self._connections:
            return
        
        client = self._connections[client_id]
        
        # 从频道中移除
        for channel in list(client.channels):
            await self.unsubscribe(client_id, channel)
        
        # 从用户索引中移除
        if client.user_id and client.user_id in self._user_connections:
            self._user_connections[client.user_id].discard(client_id)
            if not self._user_connections[client.user_id]:
                del self._user_connections[client.user_id]
        
        # 关闭连接
        try:
            await client.websocket.close()
        except Exception:
            pass
        
        # 移除连接
        del self._connections[client_id]
    
    async def subscribe(self, client_id: str, channel: str):
        """
        订阅频道
        
        频道类型:
        - `user:{user_id}` - 用户私有频道
        - `room:{room_id}` - 房间/群组频道
        - `broadcast` - 广播频道
        - `notifications` - 通知频道
        """
        if client_id not in self._connections:
            return False
        
        client = self._connections[client_id]
        client.channels.add(channel)
        
        if channel not in self._channel_subscribers:
            self._channel_subscribers[channel] = set()
        self._channel_subscribers[channel].add(client_id)
        
        # 发送订阅确认
        await self.send_to_client(
            client_id,
            {
                "type": "subscribed",
                "channel": channel
            }
        )
        
        return True
    
    async def unsubscribe(self, client_id: str, channel: str):
        """取消订阅频道"""
        if client_id not in self._connections:
            return False
        
        client = self._connections[client_id]
        client.channels.discard(channel)
        
        if channel in self._channel_subscribers:
            self._channel_subscribers[channel].discard(client_id)
            if not self._channel_subscribers[channel]:
                del self._channel_subscribers[channel]
        
        return True
    
    async def send_to_client(
        self,
        client_id: str,
        message: Dict
    ) -> bool:
        """发送消息到指定客户端"""
        if client_id not in self._connections:
            return False
        
        client = self._connections[client_id]
        
        try:
            await client.websocket.send_json(message)
            self._stats["messages_sent"] += 1
            return True
        except Exception as e:
            print(f"发送消息失败 {client_id}: {e}")
            return False
    
    async def send_to_user(
        self,
        user_id: str,
        message: Dict
    ) -> int:
        """发送消息给用户 (所有设备)"""
        if user_id not in self._user_connections:
            return 0
        
        sent_count = 0
        for client_id in self._user_connections[user_id]:
            if await self.send_to_client(client_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_channel(
        self,
        channel: str,
        message: Dict,
        exclude: Optional[Set[str]] = None
    ) -> int:
        """广播消息到频道"""
        if channel not in self._channel_subscribers:
            return 0
        
        exclude = exclude or set()
        sent_count = 0
        
        for client_id in self._channel_subscribers[channel]:
            if client_id not in exclude:
                if await self.send_to_client(client_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: Dict, exclude: Optional[Set[str]] = None) -> int:
        """广播消息到所有连接"""
        exclude = exclude or set()
        sent_count = 0
        
        for client_id in self._connections.keys():
            if client_id not in exclude:
                if await self.send_to_client(client_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def handle_message(self, client_id: str, data: Dict):
        """处理客户端消息"""
        self._stats["messages_received"] += 1
        
        msg_type = data.get("type", "unknown")
        
        if msg_type == "ping":
            # 心跳响应
            await self.send_to_client(client_id, {"type": "pong", "timestamp": datetime.utcnow().isoformat()})
        
        elif msg_type == "subscribe":
            # 订阅频道
            channel = data.get("channel")
            if channel:
                await self.subscribe(client_id, channel)
        
        elif msg_type == "unsubscribe":
            # 取消订阅
            channel = data.get("channel")
            if channel:
                await self.unsubscribe(client_id, channel)
        
        elif msg_type == "chat":
            # 聊天消息 - 需要处理AI回复
            message_text = data.get("message", "")
            # 这里可以调用AI处理
            await self.send_to_client(
                client_id,
                {
                    "type": "chat_response",
                    "message": f"🌸 若曦收到: {message_text}",
                    "echo": True
                }
            )
        
        else:
            # 未知消息类型
            await self.send_to_client(
                client_id,
                {"type": "error", "message": f"未知消息类型: {msg_type}"}
            )
    
    async def start_heartbeat(self, interval: int = 30):
        """启动心跳检测"""
        async def heartbeat_loop():
            while True:
                await asyncio.sleep(interval)
                
                # 发送心跳给所有客户端
                disconnected = []
                
                for client_id, client in list(self._connections.items()):
                    try:
                        await client.websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception:
                        # 连接已断开
                        disconnected.append(client_id)
                
                # 清理断开的连接
                for client_id in disconnected:
                    await self.disconnect(client_id)
        
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def stop_heartbeat(self):
        """停止心跳检测"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
    
    def get_stats(self) -> Dict:
        """获取连接统计"""
        return {
            "active_connections": len(self._connections),
            "total_connections": self._stats["total_connections"],
            "messages_sent": self._stats["messages_sent"],
            "messages_received": self._stats["messages_received"],
            "active_channels": len(self._channel_subscribers),
            "users_online": len(self._user_connections)
        }
    
    def get_user_count(self) -> int:
        """获取在线用户数 (去重)"""
        return len(self._user_connections)
    
    def is_connected(self, client_id: str) -> bool:
        """检查客户端是否连接"""
        return client_id in self._connections


# 全局连接管理器
connection_manager = ConnectionManager()
