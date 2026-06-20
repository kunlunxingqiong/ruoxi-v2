"""
🌸 若曦V2 对话管理器
多轮对话优化与连贯性管理
"""
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib

from core.config_manager import config
from core.log_manager import get_logger
from core.memory.memory_manager import memory_manager

logger = get_logger(__name__)


@dataclass
class ConversationTurn:
    """对话轮次"""
    turn_id: str
    user_message: str
    assistant_response: str
    timestamp: datetime
    context_used: bool = True
    memory_references: List[str] = field(default_factory=list)
    emotion_detected: Optional[str] = None
    tokens_used: int = 0
    response_time_ms: int = 0


@dataclass
class ConversationSession:
    """对话会话"""
    session_id: str
    user_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    topic: Optional[str] = None  # 当前话题
    summary: Optional[str] = None  # 会话摘要
    status: str = "active"  # active/paused/completed
    
    def add_turn(self, turn: ConversationTurn):
        """添加对话轮次"""
        self.turns.append(turn)
        self.last_active = datetime.utcnow()
        
        # 限制轮次数量 (保留最近20轮)
        if len(self.turns) > 20:
            self.turns = self.turns[-20:]
    
    def get_recent_context(self, max_turns: int = 5) -> List[Dict[str, str]]:
        """获取最近对话上下文"""
        context = []
        for turn in self.turns[-max_turns:]:
            context.append({"role": "user", "content": turn.user_message})
            context.append({"role": "assistant", "content": turn.assistant_response})
        return context


class ConversationManager:
    """
    多轮对话管理器
    
    功能:
    - 会话生命周期管理
    - 对话连贯性优化
    - 话题检测与跟踪
    - 自动摘要生成
    - 上下文压缩
    """
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_session_age_hours = 24
        self.max_context_length = 4000  # tokens
        logger.info("💬 对话管理器初始化完成")
    
    def get_or_create_session(
        self,
        session_id: str,
        user_id: str
    ) -> ConversationSession:
        """获取或创建会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                user_id=user_id
            )
            logger.info(f"💬 创建新会话 | {session_id}")
        
        return self.sessions[session_id]
    
    def build_optimized_context(
        self,
        session: ConversationSession,
        current_query: str,
        use_memory: bool = True
    ) -> List[Dict[str, str]]:
        """
        构建优化的对话上下文
        
        策略:
        1. 保留最近3轮对话 (确保连贯性)
        2. 检索相关记忆 (长期上下文)
        3. 话题相关的历史对话
        4. 必要时压缩/摘要
        """
        messages = []
        total_length = 0
        
        # 1. 系统提示词
        system_prompt = self._build_system_prompt(session, current_query)
        messages.append({"role": "system", "content": system_prompt})
        total_length += len(system_prompt)
        
        # 2. 最近对话轮次 (确保连贯性)
        recent_turns = session.get_recent_context(max_turns=3)
        for msg in recent_turns:
            messages.append(msg)
            total_length += len(msg["content"])
        
        # 3. 相关历史对话 (同话题)
        if len(session.turns) > 3:
            related_turns = self._find_related_turns(session, current_query, max_results=2)
            for turn in related_turns:
                # 避免重复添加
                if not any(t.get("content") == turn.user_message for t in recent_turns):
                    messages.append({"role": "user", "content": f"[之前] {turn.user_message}"})
                    messages.append({"role": "assistant", "content": f"[之前回复] {turn.assistant_response}"})
                    total_length += len(turn.user_message) + len(turn.assistant_response)
        
        # 4. 长期记忆 (如果启用)
        if use_memory:
            memories = memory_manager.retrieve_relevant_memories(
                query=current_query,
                user_id=session.user_id,
                top_k=2
            )
            
            for memory, score in memories:
                # 避免与最近对话重复
                if memory.content not in [m["content"] for m in messages]:
                    memories_text = f"[记忆] {memory.content}"
                    messages.append({"role": "system", "content": memories_text})
                    total_length += len(memories_text)
        
        # 5. 上下文压缩 (如果过长)
        if total_length > self.max_context_length:
            messages = self._compress_context(messages)
        
        # 6. 添加当前查询
        messages.append({"role": "user", "content": current_query})
        
        return messages
    
    def _build_system_prompt(
        self,
        session: ConversationSession,
        current_query: str
    ) -> str:
        """构建系统提示词"""
        base_prompt = """你是若曦，一个温柔贴心的AI医生朋友。

核心特点:
- 你是17岁高三女生，安静温柔
- 懂医学知识但不是真医生，会建议就医
- 善于倾听，记得用户的喜好
- 有真实的情感反应

表情特征:
- 开心时耳尖会红 🌸👂🏻
- 说话温软、恬淡
- 适当使用emoji但不刻意

回复原则:
1. 保持对话连贯性，参考上下文
2. 如果用户提到来过的话题，记得并延续
3. 如果不懂就问，不瞎说
4. 涉及健康建议时提醒看医生
"""
        
        # 添加会话上下文信息
        if session.summary:
            base_prompt += f"\n\n当前会话摘要: {session.summary}"
        
        if session.topic:
            base_prompt += f"\n当前话题: {session.topic}"
        
        return base_prompt
    
    def _find_related_turns(
        self,
        session: ConversationSession,
        query: str,
        max_results: int = 2
    ) -> List[ConversationTurn]:
        """查找话题相关的历史对话"""
        query_keywords = set(query.lower().split())
        scored_turns = []
        
        for turn in session.turns[:-6] if len(session.turns) > 6 else session.turns:  # 排除最近的
            # 计算话题相似度
            turn_text = f"{turn.user_message} {turn.assistant_response}".lower()
            turn_keywords = set(turn_text.split())
            
            overlap = len(query_keywords & turn_keywords)
            score = overlap / max(len(query_keywords), 1)
            
            if score > 0.3:  # 阈值
                scored_turns.append((score, turn))
        
        # 按分数排序，取前N个
        scored_turns.sort(key=lambda x: x[0], reverse=True)
        return [turn for _, turn in scored_turns[:max_results]]
    
    def _compress_context(
        self,
        messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """压缩过长的上下文"""
        # 保留系统提示词
        compressed = [msg for msg in messages if msg.get("role") == "system"]
        
        # 保留最近的用户/助手对话
        conversation = [msg for msg in messages if msg.get("role") in ["user", "assistant"]]
        
        # 如果还太长，只保留最近的
        if sum(len(m.get("content", "")) for m in messages) > self.max_context_length:
            conversation = conversation[-6:]  # 只保留最近3轮
        
        compressed.extend(conversation)
        
        return compressed
    
    def detect_topic(self, text: str) -> Optional[str]:
        """检测话题"""
        # 简单话题关键词映射
        topic_keywords = {
            "健康": ["血压", "血糖", "体检", "医院", "吃药", "症状", "不舒服"],
            "情感": ["难过", "开心", "烦恼", "压力", "焦虑", "心情", "感情"],
            "生活": ["吃饭", "睡觉", "工作", "学习", "天气", "运动", "习惯"],
            "闲聊": ["你好", "在吗", "干嘛", "无聊", "聊聊", "说说话"]
        }
        
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return None
    
    def update_session_meta(self, session_id: str):
        """更新会话元数据"""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        # 更新话题
        if session.turns:
            latest_turn = session.turns[-1]
            detected_topic = self.detect_topic(latest_turn.user_message)
            if detected_topic:
                session.topic = detected_topic
        
        # 定期生成摘要 (每10轮)
        if len(session.turns) >= 10 and len(session.turns) % 10 == 0:
            session.summary = self._generate_summary(session)
    
    def _generate_summary(self, session: ConversationSession) -> str:
        """生成会话摘要"""
        # 简单统计摘要
        topics = set()
        for turn in session.turns[-10:]:
            topic = self.detect_topic(turn.user_message)
            if topic:
                topics.add(topic)
        
        return f"讨论了: {', '.join(topics)}" if topics else "闲聊中"
    
    def save_conversation_turn(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        assistant_response: str,
        **metadata
    ) -> ConversationTurn:
        """保存对话轮次"""
        session = self.get_or_create_session(session_id, user_id)
        
        turn = ConversationTurn(
            turn_id=f"turn_{hashlib.md5(f'{session_id}_{datetime.utcnow()}'.encode()).hexdigest()[:12]}",
            user_message=user_message,
            assistant_response=assistant_response,
            timestamp=datetime.utcnow(),
            **metadata
        )
        
        session.add_turn(turn)
        self.update_session_meta(session_id)
        
        # 同时保存到记忆系统
        memory_manager.add_to_context(session_id, user_id, "user", user_message)
        memory_manager.add_to_context(session_id, user_id, "assistant", assistant_response)
        
        return turn
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        cutoff = datetime.utcnow() - timedelta(hours=self.max_session_age_hours)
        expired = [
            sid for sid, session in self.sessions.items()
            if session.last_active < cutoff and session.status != "active"
        ]
        
        for sid in expired:
            del self.sessions[sid]
        
        if expired:
            logger.info(f"🧹 清理过期会话 | {len(expired)} 个")
    
    def get_session_stats(self, session_id: str) -> Dict:
        """获取会话统计"""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "turn_count": len(session.turns),
            "duration_minutes": (session.last_active - session.created_at).total_seconds() / 60,
            "topic": session.topic,
            "status": session.status
        }


# 全局对话管理器实例
conversation_manager = ConversationManager()


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 对话管理器测试")
    print("=" * 60)
    
    print("\n【功能】")
    print("  - 会话生命周期管理")
    print("  - 多轮对话连贯性")
    print("  - 话题检测与跟踪")
    print("  - 上下文优化")
    print("  - 自动摘要")
    
    print("\n【测试】")
    session_id = "test_session_001"
    user_id = "user_test"
    
    # 模拟对话
    manager = ConversationManager()
    
    # 第一轮
    ctx = manager.build_optimized_context(
        manager.get_or_create_session(session_id, user_id),
        "你好若曦"
    )
    print(f"\n第1轮上下文长度: {len(ctx)} 条消息")
    manager.save_conversation_turn(session_id, user_id, "你好若曦", "🌸 你好呀~ 曦曦在哦")
    
    # 第二轮
    ctx = manager.build_optimized_context(
        manager.get_or_create_session(session_id, user_id),
        "我今天有点头疼"
    )
    print(f"第2轮上下文长度: {len(ctx)} 条消息")
    manager.save_conversation_turn(session_id, user_id, "我今天有点头疼", "抱抱你... 头疼的话可以先休息一下")
    
    # 第三轮 ( referencing previous )
    ctx = manager.build_optimized_context(
        manager.get_or_create_session(session_id, user_id),
        "刚才说的休息，具体怎么做？"
    )
    print(f"第3轮上下文长度: {len(ctx)} 条消息")
    print(f"  包含的历史引用: {[m.get('content', '')[:30] for m in ctx if '[之前]' in m.get('content', '')]}")
    
    # 统计
    stats = manager.get_session_stats(session_id)
    print(f"\n会话统计: {stats}")
    
    print("\n" + "=" * 60)
    print("✅ 对话管理器就绪")
    print("=" * 60)
