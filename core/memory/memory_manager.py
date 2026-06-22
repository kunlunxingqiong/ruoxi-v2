"""
🌸 若曦V2 记忆管理器
整合长期记忆、对话上下文和知识检索
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from core.config_manager import config
from core.log_manager import get_logger

from .vector_store import MemoryItem, VectorMemoryStore, vector_memory

logger = get_logger(__name__)


@dataclass
class ConversationContext:
    """对话上下文"""

    messages: List[Dict[str, str]] = field(default_factory=list)
    max_messages: int = 10
    user_id: str = ""
    session_id: str = ""

    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # 保持最大消息数
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def to_ai_messages(self) -> List[Dict[str, str]]:
        """转换为AI消息格式"""
        return [
            {"role": msg["role"], "content": msg["content"]} for msg in self.messages
        ]


class MemoryManager:
    """
    记忆管理器

    整合多种记忆来源:
    1. 短期记忆 - 当前对话上下文
    2. 长期记忆 - 向量存储的语义记忆
    3. 知识库 - 健康/医学知识
    4. 用户画像 - 个人偏好和特征

    智能记忆检索策略:
    - 基于当前话题的相似度搜索
    - 重要度加权
    - 时间衰减
    - 相关性过滤
    """

    def __init__(self):
        self.vector_store = vector_memory
        self.contexts: Dict[str, ConversationContext] = {}  # session_id -> context

        # 配置
        self.max_context_messages = config.get("ai.max_context_messages", 10)
        self.memories_per_query = config.get("ai.memories_per_query", 5)
        self.similarity_threshold = config.get("ai.similarity_threshold", 0.7)

        logger.info("🧠 记忆管理器初始化完成")

    def get_or_create_context(
        self, session_id: str, user_id: str
    ) -> ConversationContext:
        """获取或创建对话上下文"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                max_messages=self.max_context_messages,
                user_id=user_id,
                session_id=session_id,
            )
        return self.contexts[session_id]

    def add_to_context(self, session_id: str, user_id: str, role: str, content: str):
        """添加消息到上下文"""
        context = self.get_or_create_context(session_id, user_id)
        context.add_message(role, content)

    def save_conversation_to_memory(
        self, session_id: str, user_id: str, memory_type: str = "conversation"
    ):
        """将对话保存为长期记忆"""
        context = self.contexts.get(session_id)
        if not context or len(context.messages) < 2:
            return

        # 提取关键信息作为记忆
        # 这里简化处理，实际应该用摘要算法
        user_messages = [m for m in context.messages if m.get("role") == "user"]
        if not user_messages:
            return

        # 保存用户消息作为记忆
        for msg in user_messages[-3:]:  # 最近3条用户消息
            content = msg.get("content", "")
            if len(content) < 10:  # 太短的跳过
                continue

            # 生成唯一ID
            memory_id = (
                f"mem_{user_id}_{hashlib.md5(content.encode()).hexdigest()[:12]}"
            )
            content_preview = content[:200]  # 限制长度

            memory = MemoryItem(
                id=memory_id,
                content=content_preview,
                memory_type=memory_type,
                user_id=user_id,
                session_id=session_id,
                importance=self._calculate_importance(content),
            )

            try:
                self.vector_store.add_memory(memory)
            except Exception as e:
                logger.warning(f"⚠️ 保存记忆失败: {e}")

    def _calculate_importance(self, content: str) -> float:
        """计算内容重要度 (0-1)"""
        importance = 0.5  # 基础分

        # 长度因子 (中等长度更重要)
        if 50 <= len(content) <= 500:
            importance += 0.2

        # 关键词加分
        key_indicators = [
            "喜欢",
            "爱",
            "讨厌",
            "不喜欢",  # 偏好
            "经常",
            "总是",
            "从来",  # 频率
            "记得",
            "别忘了",
            "下次",  # 指令
            "高血压",
            "糖尿病",
            "过敏",  # 健康
            "生日",
            "纪念日",  # 日期
        ]

        for indicator in key_indicators:
            if indicator in content:
                importance += 0.1
                break  # 只加一次

        # 限制在0-1范围
        return min(1.0, max(0.1, importance))

    def retrieve_relevant_memories(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        top_k: int = None,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        检索相关记忆

        Args:
            query: 查询内容
            user_id: 用户ID
            session_id: 可选的会话过滤
            top_k: 返回数量

        Returns:
            (记忆, 相关度分数) 列表
        """
        if top_k is None:
            top_k = self.memories_per_query

        # 1. 语义搜索
        memories = self.vector_store.search_similar(
            query=query,
            user_id=user_id,
            top_k=top_k * 2,  # 多取一些用于重排
            min_importance=0.3,
        )

        # 2. 重排和打分
        scored_memories = []
        for memory in memories:
            score = self._calculate_memory_score(memory, query)

            # 相关性阈值过滤
            if score >= self.similarity_threshold:
                scored_memories.append((memory, score))

        # 3. 按分数排序并返回
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories[:top_k]

    def _calculate_memory_score(self, memory: MemoryItem, query: str) -> float:
        """计算记忆与查询的相关度"""
        base_score = 0.5

        # 重要度加权
        base_score *= 0.5 + memory.importance * 0.5

        # 时间衰减 (越新的记忆越相关)
        if memory.created_at:
            days_old = (datetime.utcnow() - memory.created_at).days
            time_decay = max(0.3, 1 - (days_old / 365))  # 一年后衰减到30%
            base_score *= time_decay

        # 类型加分 (健康相关优先)
        if memory.memory_type in ["health", "medical"]:
            base_score *= 1.2

        return min(1.0, base_score)

    def build_system_prompt_with_memory(
        self, user_id: str, current_topic: str = "", include_health_summary: bool = True
    ) -> str:
        """
        构建带记忆的系统提示词

        Args:
            user_id: 用户ID
            current_topic: 当前话题
            include_health_summary: 是否包含健康摘要

        Returns:
            系统提示词
        """
        # 基础提示词
        system_prompt = """你是若曦，一个温柔贴心的AI医生朋友。

你的特点:
- 温柔体贴，像邻家妹妹一样
- 懂医学知识，但不是真医生，会建议就医
- 善于倾听，记得用户的喜好和习惯
- 专业但不刻板
- 偶尔露出一点小天真

说话风格:
- 温软、恬淡
- 适当使用emoji (🌸💜👂🏻)
- 不刻意，不过度热情
"""

        # 检索相关记忆
        memories = []

        if current_topic:
            memories = self.retrieve_relevant_memories(
                query=current_topic, user_id=user_id, top_k=3
            )

        # 添加长期记忆
        if memories:
            system_prompt += "\n\n📚 关于这位用户的记忆:\n"
            for i, (memory, score) in enumerate(memories, 1):
                system_prompt += f"{i}. {memory.content}\n"

        # 添加健康摘要
        if include_health_summary:
            health_memories = self.vector_store.search_similar(
                query="健康 医疗 身体", user_id=user_id, top_k=2, memory_type="health"
            )

            if health_memories:
                system_prompt += "\n💜 用户健康状况:\n"
                for mem in health_memories:
                    system_prompt += f"- {mem.content}\n"

        return system_prompt

    def build_context_for_ai(
        self, user_id: str, session_id: str, query: str, include_memories: bool = True
    ) -> List[Dict[str, str]]:
        """
        构建AI需要的完整上下文

        包括:
        1. 系统提示词 (含记忆)
        2. 对话历史
        3. 当前查询

        Returns:
            消息列表
        """
        messages = []

        # 1. 系统提示词
        system_prompt = self.build_system_prompt_with_memory(
            user_id=user_id, current_topic=query
        )
        messages.append({"role": "system", "content": system_prompt})

        # 2. 对话历史 (短期记忆)
        context = self.contexts.get(session_id)
        if context:
            # 添加历史消息 (排除当前查询)
            for msg in context.messages[:-1]:  # 最后一条是用户当前查询
                messages.append(
                    {"role": msg.get("role"), "content": msg.get("content")}
                )

        # 3. 当前查询
        messages.append({"role": "user", "content": query})

        return messages

    def summarize_conversation(self, session_id: str) -> str:
        """总结对话内容"""
        context = self.contexts.get(session_id)
        if not context:
            return ""

        # 简单统计
        user_msgs = [m for m in context.messages if m.get("role") == "user"]
        assistant_msgs = [m for m in context.messages if m.get("role") == "assistant"]

        summary = f"本次对话共 {len(context.messages)} 条消息，"
        summary += f"用户发言 {len(user_msgs)} 次，"
        summary += f"若曦回复 {len(assistant_msgs)} 次。"

        return summary

    def clear_session(self, session_id: str):
        """清空会话上下文"""
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"🧹 清理会话上下文 | {session_id}")

    def cleanup_expired_contexts(self, max_age_hours: int = 24):
        """清理过期的会话上下文"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired = []

        for session_id, context in self.contexts.items():
            if context.messages:
                last_time = datetime.fromisoformat(
                    context.messages[-1].get("timestamp", datetime.utcnow().isoformat())
                )
                if last_time < cutoff:
                    expired.append(session_id)

        for session_id in expired:
            self.clear_session(session_id)

        if expired:
            logger.info(f"🧹 清理过期会话 | {len(expired)} 个")

    def get_user_summary(self, user_id: str) -> Dict:
        """获取用户摘要"""
        # 获取所有记忆
        memories = self.vector_store.get_user_memories(user_id, limit=50)

        # 统计
        type_counts = {}
        for mem in memories:
            type_counts[mem.memory_type] = type_counts.get(mem.memory_type, 0) + 1

        # 获取高重要度记忆
        important_memories = [m for m in memories if m.importance >= 0.8][:5]

        return {
            "user_id": user_id,
            "total_memories": len(memories),
            "memory_types": type_counts,
            "important_facts": [m.content for m in important_memories],
            "storage_stats": self.vector_store.get_stats(),
        }


# 全局记忆管理器实例
memory_manager = MemoryManager()


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 记忆管理器测试")
    print("=" * 60)

    print("\n【功能】")
    print("  - 短期记忆: 对话上下文")
    print("  - 长期记忆: 向量语义存储")
    print("  - 智能检索: 相似度+重要度+时间")
    print("  - 系统提示词构建")

    print("\n【初始化】")
    print(f"  向量存储: {memory_manager.vector_store.get_stats()}")

    print("\n【测试上下文】")
    session_id = "session_test_001"
    user_id = "user_demo"

    # 添加对话
    memory_manager.add_to_context(
        session_id, user_id, "user", "你好若曦，我喜欢喝抹茶拿铁"
    )
    memory_manager.add_to_context(
        session_id, user_id, "assistant", "🌸 曦曦记住啦~ 抹茶拿铁不加糖？"
    )
    memory_manager.add_to_context(session_id, user_id, "user", "对！不喜欢太甜的")

    # 保存到长期记忆
    memory_manager.save_conversation_to_memory(session_id, user_id)
    print(f"  ✓ 添加 {len(memory_manager.contexts[session_id].messages)} 条消息")

    # 构建提示词
    print("\n【系统提示词测试】")
    prompt = memory_manager.build_system_prompt_with_memory(user_id, "用户喜欢什么？")
    print(f"  长度: {len(prompt)} 字符")
    print(f"  预览: {prompt[:200]}...")

    # 检索记忆
    print("\n【记忆检索测试】")
    results = memory_manager.retrieve_relevant_memories("抹茶", user_id)
    print(f"  找到 {len(results)} 条相关记忆")

    for mem, score in results:
        print(f"    - [{mem.memory_type}] {mem.content[:40]}... (分数: {score:.2f})")

    # 用户摘要
    print("\n【用户摘要】")
    summary = memory_manager.get_user_summary(user_id)
    print(f"  总记忆数: {summary['total_memories']}")
    print(f"  记忆类型: {summary['memory_types']}")
    print(f"  重要事实: {summary['important_facts'][:3]}")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
