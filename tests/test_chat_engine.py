"""
🌸 若曦V2 - 聊天引擎测试
单元测试和集成测试
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from core.chat.chat_engine import (
    ChatEngine, 
    ChatMode, 
    ChatMessage, 
    ChatContext,
    chat_engine,
    chat_service
)


class TestChatMessage:
    """聊天消息测试"""
    
    def test_message_creation(self):
        """测试消息创建"""
        msg = ChatMessage(
            id="msg_001",
            user_id="user_001",
            content="你好若曦",
            role="user",
            timestamp=datetime.utcnow(),
            mode=ChatMode.CASUAL
        )
        
        assert msg.id == "msg_001"
        assert msg.role == "user"
        assert msg.mode == ChatMode.CASUAL
        assert msg.metadata == {}
    
    def test_message_with_metadata(self):
        """测试带元数据的消息"""
        msg = ChatMessage(
            id="msg_002",
            user_id="user_001",
            content="测试",
            role="assistant",
            timestamp=datetime.utcnow(),
            metadata={"sources": [{"type": "memory"}]}
        )
        
        assert msg.metadata["sources"][0]["type"] == "memory"


class TestChatEngine:
    """聊天引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        return ChatEngine()
    
    @pytest.mark.asyncio
    async def test_create_context(self, engine, sample_user_id):
        """测试上下文创建"""
        context = await engine.create_context(
            user_id=sample_user_id,
            mode=ChatMode.CASUAL
        )
        
        assert context.user_id == sample_user_id
        assert context.mode == ChatMode.CASUAL
        assert context.session_id.startswith("chat_")
        assert isinstance(context.history, list)
    
    @pytest.mark.asyncio
    async def test_build_system_prompt(self, engine):
        """测试系统提示词构建"""
        context = ChatContext(
            user_id="user_001",
            session_id="session_001",
            mode=ChatMode.CASUAL,
            history=[],
            user_profile={"interests": ["阅读"]},
            health_summary={},
            emotional_state="开心"
        )
        
        prompt = engine._build_system_prompt(context)
        
        assert "若曦" in prompt
        assert "林若曦" in prompt
        assert "开心" in prompt
    
    def test_get_model_for_mode(self, engine):
        """测试模型选择"""
        assert engine._get_model_for_mode(ChatMode.PROFESSIONAL) == "gemini-1.5-pro"
        assert engine._get_model_for_mode(ChatMode.HEALTH) == "gemini-2.0-flash"
        assert engine._get_model_for_mode(ChatMode.CASUAL) == "llama-3.1-8b-instant"
    
    def test_fallback_response(self, engine):
        """测试备用回复"""
        response = engine._fallback_response("测试消息")
        assert "曦曦" in response or "若曦" in response
    
    def test_get_session_history_empty(self, engine, sample_user_id):
        """测试获取空历史"""
        history = engine.get_session_history(sample_user_id)
        assert history == []


class TestChatService:
    """聊天服务测试"""
    
    @pytest.mark.asyncio
    async def test_send_message_modes(self):
        """测试不同模式的消息发送"""
        # Mock 引擎方法
        with patch.object(chat_engine, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "message_id": "msg_001",
                "content": "测试回复",
                "role": "assistant"
            }
            
            # 测试健康模式
            await chat_service.send_message(
                user_id="user_001",
                message="我血压有点高",
                mode="health"
            )
            
            call_args = mock_chat.call_args
            assert call_args[1]["mode"] == ChatMode.HEALTH
    
    @pytest.mark.asyncio
    async def test_clear_history(self):
        """测试清除历史"""
        user_id = "test_clear_user"
        
        # 先添加一些消息
        chat_engine._sessions[user_id] = [
            ChatMessage(
                id="msg_001",
                user_id=user_id,
                content="测试",
                role="user",
                timestamp=datetime.utcnow()
            )
        ]
        
        # 清除
        result = await chat_service.clear_history(user_id)
        assert result is True
        assert chat_engine._sessions[user_id] == []
    
    @pytest.mark.asyncio
    async def test_clear_history_nonexistent(self):
        """测试清除不存在的用户历史"""
        result = await chat_service.clear_history("nonexistent_user")
        assert result is False


class TestChatModes:
    """聊天模式测试"""
    
    def test_chat_mode_values(self):
        """测试聊天模式值"""
        assert ChatMode.CASUAL.value == "casual"
        assert ChatMode.HEALTH.value == "health"
        assert ChatMode.EMOTIONAL.value == "emotional"
        assert ChatMode.PROFESSIONAL.value == "professional"
    
    def test_mode_from_string(self):
        """测试从字符串创建模式"""
        mode_str = "health"
        mode = ChatMode(mode_str)
        assert mode == ChatMode.HEALTH


@pytest.mark.integration
class TestChatIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="需要AI模型服务")
    async def test_full_chat_flow(self):
        """测试完整聊天流程"""
        # 这是一个集成测试，需要实际的AI服务
        pass
