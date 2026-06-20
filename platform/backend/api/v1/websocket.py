"""
🌸 若曦V2 - WebSocket API
实时通信端点
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import json

from core.websocket.connection_manager import connection_manager, ConnectionManager
from core.auth.jwt_auth import get_current_user_ws  # WebSocket专用认证


router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket聊天端点
    
    支持:
    - 实时双向通信
    - 用户认证
    - 心跳检测
    - 自动重连
    
    消息格式:
    ```json
    {"type": "chat", "message": "你好若曦"}
    {"type": "subscribe", "channel": "user:123"}
    {"type": "ping"}
    ```
    """
    # 认证
    user_id = None
    if token:
        try:
            # TODO: 验证token获取user_id
            user_id = "authenticated_user"
        except Exception:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    
    # 生成client_id
    if not client_id:
        import uuid
        client_id = str(uuid.uuid4())[:8]
    
    # 建立连接
    client = await connection_manager.connect(
        websocket=websocket,
        client_id=client_id,
        user_id=user_id,
        metadata={"endpoint": "chat"}
    )
    
    # 订阅用户私有频道
    if user_id:
        await connection_manager.subscribe(client_id, f"user:{user_id}")
    
    # 订阅广播频道
    await connection_manager.subscribe(client_id, "broadcast")
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await connection_manager.handle_message(client_id, message)
            except json.JSONDecodeError:
                await connection_manager.send_to_client(
                    client_id,
                    {"type": "error", "message": "无效的JSON格式"}
                )
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket通知端点
    
    专门用于接收实时通知:
    - 健康告警
    - 用药提醒
    - 系统通知
    """
    # 必须认证
    try:
        # TODO: 验证token
        user_id = "authenticated_user"
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    if not client_id:
        import uuid
        client_id = str(uuid.uuid4())[:8]
    
    # 建立连接
    client = await connection_manager.connect(
        websocket=websocket,
        client_id=client_id,
        user_id=user_id,
        metadata={"endpoint": "notifications"}
    )
    
    # 订阅通知频道
    await connection_manager.subscribe(client_id, f"notifications:{user_id}")
    await connection_manager.subscribe(client_id, f"user:{user_id}")
    
    try:
        # 主要保持连接，接收心跳
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await connection_manager.send_to_client(
                    client_id,
                    {"type": "pong", "timestamp": "..."}
                )
    
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)


@router.get("/stats")
async def get_websocket_stats():
    """获取WebSocket连接统计"""
    return {
        "success": True,
        "stats": connection_manager.get_stats()
    }


@router.post("/broadcast")
async def broadcast_message(message: dict):
    """广播消息到所有客户端"""
    sent = await connection_manager.broadcast(message)
    
    return {
        "success": True,
        "sent_count": sent
    }


@router.post("/send-to-user/{user_id}")
async def send_to_user(user_id: str, message: dict):
    """发送消息给指定用户"""
    sent = await connection_manager.send_to_user(user_id, message)
    
    return {
        "success": True,
        "sent_count": sent
    }
