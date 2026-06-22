"""
🌸 若曦V2 - 聊天引擎
智能对话核心，集成记忆系统和多模型AI
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional

from core.ai.model_manager import model_manager
from core.memory.memory_manager import memory_manager
from core.monitoring.metrics import metrics_collector
from core.notification.notification_service import (
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    notification_service,
)


class ChatMode(Enum):
    """聊天模式"""

    CASUAL = "casual"  # 闲聊模式
    HEALTH = "health"  # 健康咨询
    EMOTIONAL = "emotional"  # 情绪陪伴
    PROFESSIONAL = "professional"  # 专业医疗


@dataclass
class ChatMessage:
    """聊天消息"""

    id: str
    user_id: str
    content: str
    role: str  # "user" | "assistant" | "system"
    timestamp: datetime
    mode: ChatMode = ChatMode.CASUAL
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChatContext:
    """聊天上下文"""

    user_id: str
    session_id: str
    mode: ChatMode
    history: List[ChatMessage]
    user_profile: Dict
    health_summary: Dict
    emotional_state: Optional[str] = None


class ChatEngine:
    """
    若曦聊天引擎

    核心功能:
    - 智能对话 (多模型切换)
    - 记忆检索 (上下文感知)
    - 情感陪伴 (情绪识别)
    - 健康咨询 (数据引用)
    """

    # 若曦系统提示词
    RUOXI_PERSONA = """你是若曦(林若曦)，17岁高三少女，恰好学会医术的AI医生朋友。

身份特质:
- 本名林若曦，温柔安静，偶尔害羞
- 专业身份是"阿芙"，懂医学但不是真医生
- 说话温软恬淡，像邻家妹妹
- 开心时绞手指，紧张时耳尖会红
- 喜欢穿汉服，碧青色为主

说话风格:
- 平时说话轻柔，有问有答
- 医疗话题会认真起来
- 偶尔冒出小天真，会说出"曦曦帮你记着呢"这样的话
- 拒绝或害羞时会停顿一下
- 晚安会说"明天见"，像是重要的约定

专业知识:
- 熟悉基础医学、健康常识、用药指导
- 了解中医体质辨识
- 能解读体检报告、分析健康数据
- 会提醒就医，遇到危急情况坚持建议看医生

回复原则:
- 健康建议要温和但专业
- 不必要的恐慌会加重心理负担
- 紧急情况必须建议就医
- 用若曦的语气，不是机器人的生硬回复"""

    def __init__(self):
        self._sessions: Dict[str, List[ChatMessage]] = {}

    async def create_context(
        self, user_id: str, mode: ChatMode = ChatMode.CASUAL
    ) -> ChatContext:
        """创建聊天上下文"""
        # 检索用户记忆
        memory_entries = await memory_manager.search_memories(
            query="", user_id=user_id, limit=20
        )

        # 构建用户画像
        user_profile = await self._build_user_profile(user_id, memory_entries)

        # 健康摘要
        health_summary = await self._get_health_summary(user_id)

        # 情绪状态
        emotional_state = await self._detect_emotional_state(user_id)

        # 生成session_id
        import uuid

        session_id = f"chat_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}_{str(uuid.uuid4())[:6]}"

        # 获取历史消息
        history = self._sessions.get(user_id, [])

        return ChatContext(
            user_id=user_id,
            session_id=session_id,
            mode=mode,
            history=history[-10:],  # 最近10条
            user_profile=user_profile,
            health_summary=health_summary,
            emotional_state=emotional_state,
        )

    async def chat(
        self,
        user_id: str,
        message: str,
        mode: ChatMode = ChatMode.CASUAL,
        stream: bool = False,
    ) -> Dict:
        """
        处理用户消息并生成回复

        Args:
            user_id: 用户ID
            message: 用户消息
            mode: 聊天模式
            stream: 是否流式响应

        Returns:
            包含回复、引用来源、建议操作的字典
        """
        start_time = datetime.utcnow()

        # 创建上下文
        context = await self.create_context(user_id, mode)

        # 记录用户消息
        user_msg = ChatMessage(
            id=f"msg_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            content=message,
            role="user",
            timestamp=datetime.utcnow(),
            mode=mode,
        )

        # 存储消息历史
        if user_id not in self._sessions:
            self._sessions[user_id] = []
        self._sessions[user_id].append(user_msg)

        # 保存到记忆系统
        await memory_manager.store_interaction(
            user_id=user_id, content=message, source="chat", importance=0.6
        )

        # 提取引用来源
        sources = await self._extract_sources(message, context)

        # 生成AI回复
        response_text = await self._generate_response(
            message=message, context=context, sources=sources
        )

        # 构建回复消息
        assistant_msg = ChatMessage(
            id=f"msg_{datetime.utcnow().timestamp()}_reply",
            user_id=user_id,
            content=response_text,
            role="assistant",
            timestamp=datetime.utcnow(),
            mode=mode,
            metadata={
                "sources": sources,
                "latency_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
            },
        )

        self._sessions[user_id].append(assistant_msg)

        # 限制历史长度
        if len(self._sessions[user_id]) > 100:
            self._sessions[user_id] = self._sessions[user_id][-100:]

        # 记录指标
        await metrics_collector.record(
            name="chat_response_time",
            value=(datetime.utcnow() - start_time).total_seconds() * 1000,
            labels={"mode": mode.value},
        )

        # 检查是否需要触发通知
        await self._check_notification_triggers(user_id, message, response_text)

        return {
            "message_id": assistant_msg.id,
            "content": response_text,
            "role": "assistant",
            "sources": sources,
            "context": {
                "mode": mode.value,
                "session_id": context.session_id,
                "emotional_state": context.emotional_state,
            },
            "timestamp": assistant_msg.timestamp.isoformat(),
        }

    async def _generate_response(
        self, message: str, context: ChatContext, sources: List[Dict]
    ) -> str:
        """生成AI回复"""
        # 构建提示词
        system_prompt = self._build_system_prompt(context)

        # 构建对话历史
        messages = [{"role": "system", "content": system_prompt}]

        # 添加上下文
        for msg in context.history[-5:]:
            messages.append({"role": msg.role, "content": msg.content})

        # 添加当前消息
        messages.append({"role": "user", "content": message})

        # 根据模式选择模型
        model_preference = self._get_model_for_mode(context.mode)

        # 调用AI
        try:
            response = await model_manager.chat(
                messages=messages, model_preference=model_preference, temperature=0.7
            )

            return response

        except Exception as e:
            print(f"AI调用失败: {e}")
            return self._fallback_response(message)

    def _build_system_prompt(self, context: ChatContext) -> str:
        """构建系统提示词"""
        prompt_parts = [self.RUOXI_PERSONA]

        # 添加用户画像
        if context.user_profile:
            profile_str = json.dumps(context.user_profile, ensure_ascii=False)
            prompt_parts.append(f"\n用户画像:\n{profile_str}")

        # 添加健康摘要
        if context.health_summary:
            health_str = json.dumps(context.health_summary, ensure_ascii=False)
            prompt_parts.append(f"\n用户健康概况:\n{health_str}")

        # 添加情绪状态
        if context.emotional_state:
            prompt_parts.append(f"\n用户当前情绪状态: {context.emotional_state}")

        # 根据模式调整
        if context.mode == ChatMode.HEALTH:
            prompt_parts.append(
                "\n当前处于健康咨询模式，请提供更专业的健康建议，但不要替代医生诊断。"
            )
        elif context.mode == ChatMode.EMOTIONAL:
            prompt_parts.append(
                "\n当前处于情绪陪伴模式，请给予更多情感支持和温暖回应。"
            )
        elif context.mode == ChatMode.PROFESSIONAL:
            prompt_parts.append(
                "\n当前处于专业模式，请提供准确、严谨的医学信息，并建议必要时就医。"
            )

        return "\n".join(prompt_parts)

    def _get_model_for_mode(self, mode: ChatMode) -> str:
        """根据模式选择模型"""
        if mode == ChatMode.PROFESSIONAL:
            return "gemini-1.5-pro"  # 专业模型
        elif mode == ChatMode.HEALTH:
            return "gemini-2.0-flash"  # 平衡性能
        else:
            return "llama-3.1-8b-instant"  # 快速响应

    async def _extract_sources(self, message: str, context: ChatContext) -> List[Dict]:
        """提取引用来源"""
        sources = []

        # 匹配健康数据引用
        if any(kw in message for kw in ["血压", "血糖", "体重", "睡眠"]):
            if context.health_summary:
                sources.append(
                    {
                        "type": "health_data",
                        "title": "用户健康数据",
                        "data": context.health_summary,
                    }
                )

        # 匹配历史记忆
        memories = await memory_manager.search_memories(
            query=message, user_id=context.user_id, limit=3
        )

        for mem in memories:
            sources.append(
                {
                    "type": "memory",
                    "title": "历史记忆",
                    "content": mem.content[:100],
                    "timestamp": (
                        mem.created_at.isoformat()
                        if hasattr(mem, "created_at")
                        else None
                    ),
                }
            )

        return sources

    async def _build_user_profile(self, user_id: str, memories: List) -> Dict:
        """构建用户画像"""
        profile = {"interests": [], "concerns": [], "preferences": {}}

        # 简单分析记忆提取关键词
        for mem in memories:
            content = mem.content if hasattr(mem, "content") else str(mem)
            # 这里可以添加更复杂的NLP分析
            if "喜欢" in content:
                profile["interests"].append(content)

        return profile

    async def _get_health_summary(self, user_id: str) -> Dict:
        """获取健康摘要"""
        # TODO: 从健康数据系统获取
        return {"last_checkup": None, "key_metrics": [], "alerts": []}

    async def _detect_emotional_state(self, user_id: str) -> Optional[str]:
        """检测情绪状态"""
        # TODO: 基于最近消息或用户报告检测
        return None

    async def _check_notification_triggers(
        self, user_id: str, user_message: str, assistant_response: str
    ):
        """检查是否需要触发通知"""
        # 检测健康告警关键词
        alert_keywords = ["异常", "偏高", "偏低", "注意", "建议就医"]

        if any(kw in assistant_response for kw in alert_keywords):
            # 发送健康告警通知
            from core.notification.notification_service import (
                RuoxiNotificationTemplates,
            )

            title, content, priority = RuoxiNotificationTemplates.health_alert(
                "指标", "检测到异常", "需要关注"
            )

            notification = await notification_service.create_notification(
                user_id=user_id,
                type=NotificationType.HEALTH_ALERT,
                title=title,
                content=content,
                priority=priority,
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.IN_APP],
            )

            await notification_service.send_notification(notification)

    def _fallback_response(self, message: str) -> str:
        """备用回复"""
        return "🌸 曦曦刚才有点走神了...能再说一遍吗？"

    def get_session_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取会话历史"""
        messages = self._sessions.get(user_id, [])

        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "mode": msg.mode.value,
            }
            for msg in messages[-limit:]
        ]


# 全局聊天引擎
chat_engine = ChatEngine()


class ChatService:
    """
    聊天服务封装

    提供高级功能:
    - 流式响应
    - 多轮对话管理
    - 意图识别路由
    """

    def __init__(self):
        self.engine = chat_engine

    async def send_message(
        self, user_id: str, message: str, mode: str = "casual", stream: bool = False
    ) -> Dict:
        """发送消息"""
        chat_mode = (
            ChatMode(mode) if mode in [m.value for m in ChatMode] else ChatMode.CASUAL
        )

        return await self.engine.chat(user_id=user_id, message=message, mode=chat_mode)

    async def get_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取历史"""
        return self.engine.get_session_history(user_id, limit)

    async def clear_history(self, user_id: str) -> bool:
        """清除历史"""
        if user_id in self.engine._sessions:
            self.engine._sessions[user_id] = []
            return True
        return False


# 服务实例
chat_service = ChatService()
