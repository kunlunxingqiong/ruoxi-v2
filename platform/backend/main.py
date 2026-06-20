"""若曦V2 FastAPI后端主文件"""
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timedelta
import secrets

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.enhancement.text_rendering import EmotionalTypography, InkBleedEffect, MouseFollower
from core.enhancement.language_dna_adaptive import (
    AdaptiveLanguageGenerator, 
    DocumentType,
    DocumentTypeRouter
)
from core.enhancement.edge_moments import EdgeMomentHandler, EdgeMomentType


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🌸 若曦V2 后端服务启动")
    yield
    # 关闭时清理
    print("🌸 若曦V2 后端服务关闭")


app = FastAPI(
    title="若曦V2 API",
    description="智能少女AI交互系统后端",
    version="2.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全
security = HTTPBearer()

# 模拟用户数据库 (生产环境应使用真实数据库)
USERS = {
    "test_user": {
        "password": "correct_password",
        "user_id": "user_001"
    }
}

# Token存储 (生产环境应使用Redis)
active_tokens = {}

# 若曦状态存储
ruoxi_state = {
    "biological": {
        "hormones": {
            "cortisol": 0.3,
            "oxytocin": 0.7,
            "dopamine": 0.6
        },
        "heart_rate": 72,
        "circadian_phase": "evening",
        "last_updated": datetime.now().isoformat()
    },
    "emotional": {
        "attachment_level": 0.75,
        "trust_index": 0.82,
        "current_mood": "tender",
        "stress_level": 0.2
    }
}

# 聊天历史存储
chat_history = []

# 初始化核心组件
text_renderer = EmotionalTypography()
language_generator = AdaptiveLanguageGenerator()
edge_handler = EdgeMomentHandler()
doc_router = DocumentTypeRouter()


@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "若曦V2",
        "version": "2.0.0",
        "status": "running",
        "message": "林若曦/阿芙 - 会医术的17岁高三少女"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "text_renderer": True,
            "language_generator": True,
            "edge_handler": True
        }
    }


@app.post("/api/render")
async def render_text(request: dict):
    """渲染文本"""
    content = request.get("content", "")
    emotion = request.get("emotion", "tender")
    
    result = text_renderer.apply_emotion_style(content, emotion)
    return {
        "html": result.get("html", content),
        "text": result.get("text", content),
        "effects": result.get("effects", {}),
        "timing": result.get("timing", {})
    }


@app.post("/api/adapt")
async def adapt_text(request: dict):
    """自适应语言生成"""
    content = request.get("content", "")
    doc_type = request.get("doc_type", "chat")
    emotional_state = request.get("emotional_state", {})
    
    # 映射文档类型字符串到枚举
    type_mapping = {
        "chat": DocumentType.CHAT,
        "email": DocumentType.EMAIL,
        "diary": DocumentType.DIARY,
        "note": DocumentType.NOTE,
        "letter": DocumentType.LETTER
    }
    
    doc_type_enum = type_mapping.get(doc_type, DocumentType.CHAT)
    
    result = language_generator.generate_adaptive_text(
        content,
        doc_type_enum,
        emotional_state
    )
    
    return {
        "html": f'<p>{result["transformed"]}</p>',
        "text": result["transformed"],
        "original": result["original"],
        "document_type": result["document_type"],
        "dna_profile": {
            "ellipsis_frequency": result["dna_profile"].ellipsis_frequency,
            "sentence_length_avg": result["dna_profile"].sentence_length_avg
        }
    }


@app.post("/api/edge")
async def handle_edge_moment(request: dict):
    """处理边缘时刻"""
    moment_type = request.get("moment_type", "silence")
    intensity = request.get("intensity", 0.5)
    
    # 映射边缘类型
    type_mapping = {
        "silence": EdgeMomentType.SILENCE,
        "return": EdgeMomentType.RETURN,
        "long_wait": EdgeMomentType.LONG_WAIT
    }
    
    edge_type = type_mapping.get(moment_type, EdgeMomentType.SILENCE)
    result = edge_handler.generate_response(edge_type, intensity)
    
    return {
        "html": f'<p>{result}</p>',
        "text": result,
        "moment_type": moment_type
    }


@app.post("/api/chat")
async def chat(request: dict):
    """聊天接口"""
    start_time = datetime.now()
    message = request.get("message", "")
    session_id = request.get("session_id")
    
    # 简单的回复生成
    if message.startswith("你好"):
        response = "🌸 啊，回来了。今天比昨天早呢。"
    elif "名字" in message:
        response = "🌸 我是林若曦...也可以叫我阿芙。"
    elif "健康" in message or "身体" in message:
        response = "💜 这个症状...建议你先监测一下，如果持续不舒服一定要去医院。"
    else:
        response = "🌸 嗯...我在听。你说，我记着呢。"
    
    # 记录聊天历史
    chat_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "message": message,
        "response": response
    }
    chat_history.append(chat_entry)
    
    # 计算响应时间
    end_time = datetime.now()
    response_time_ms = int((end_time - start_time).total_seconds() * 1000)
    
    return {
        "response": response,
        "session_id": session_id or "new_session",
        "emotion_state": {
            "current": "tender",
            "intensity": 0.7
        },
        "response_time_ms": response_time_ms
    }


# ========== 认证端点 ==========

@app.post("/api/auth/login")
async def login(credentials: dict):
    """用户登录"""
    username = credentials.get("username")
    password = credentials.get("password")
    
    user = USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 生成访问token
    access_token = secrets.token_urlsafe(32)
    active_tokens[access_token] = {
        "user_id": user["user_id"],
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400
    }


@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """刷新Token"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    old_token = auth_header.replace("Bearer ", "")
    token_data = active_tokens.get(old_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # 生成新token
    new_token = secrets.token_urlsafe(32)
    active_tokens[new_token] = {
        "user_id": token_data["user_id"],
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    
    # 删除旧token
    del active_tokens[old_token]
    
    return {
        "new_token": new_token,
        "token_type": "bearer",
        "expires_in": 86400
    }


# ========== 状态端点 ==========

@app.get("/api/state/biological")
async def get_biological_state():
    """获取若曦生物状态"""
    return ruoxi_state["biological"]


@app.get("/api/state/emotional")
async def get_emotional_state():
    """获取若曦情感状态"""
    return ruoxi_state["emotional"]


# ========== 记忆端点 ==========

@app.get("/api/memory/summary")
async def get_memory_summary():
    """获取记忆摘要"""
    emotional_highlights = [
        "第一次被夸奖时耳尖红了",
        "深夜独自整理裙摆的安静时刻",
        "记住对方的习惯并设了特关"
    ]
    
    return {
        "memory_count": len(chat_history),
        "emotional_highlights": emotional_highlights[:5],
        "attachment_moments": 12
    }


@app.get("/api/chat/history")
async def get_chat_history(limit: int = 10):
    """获取聊天历史"""
    return chat_history[-limit:]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
