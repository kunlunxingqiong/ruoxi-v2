"""
🌸 若曦V2 - AI Agent V2 增强版
综合能力更强的智能体
"""
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum, auto
import asyncio
import json
from datetime import datetime

from core.ai.model_manager import ai_manager, ModelResponse
from core.memory.memory_manager import memory_manager
from core.emotion.emotion_analyzer import emotion_analyzer, EmotionType
from core.health.health_analyzer import health_analyzer


class AgentCapability(Enum):
    """Agent能力"""
    CHAT = auto()
    HEALTH_ANALYSIS = auto()
    EMOTION_SUPPORT = auto()
    MEMORY_SEARCH = auto()
    TASK_PLANNING = auto()
    REMINDER = auto()
    CONTENT_CREATION = auto()


@dataclass
class AgentMessage:
    """Agent消息"""
    role: str
    content: str
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class AgentResponse:
    """Agent响应"""
    content: str
    emotion: EmotionType
    capabilities_used: List[AgentCapability]
    memories_accessed: List[str]
    health_insights: Optional[Dict]
    suggestions: List[str]
    follow_up_questions: List[str]
    confidence: float


class RuoxiAgentV2:
    """
    若曦V2 Agent - 增强版智能体
    
    特点:
    - 多模态能力
    - 主动服务
    - 任务规划执行
    - 深度个性化
    """
    
    def __init__(self):
        self.ai = ai_manager
        self.memory = memory_manager
        self.emotion = emotion_analyzer
        self.health = health_analyzer
        self.capabilities = list(AgentCapability)
    
    async def respond(
        self,
        user_id: str,
        message: str,
        context: Dict = None
    ) -> AgentResponse:
        """
        智能响应 - 综合分析用户意图并给出最佳回答
        
        流程:
        1. 情感检测
        2. 意图识别
        3. 记忆查询
        4. 能力调度
        5. 生成响应
        """
        # 1. 情感检测
        emotion_result = self.emotion.detect(message)
        user_emotion = emotion_result.emotion
        
        # 2. 分析用户意图
        intent = await self._analyze_intent(message)
        
        # 3. 查询相关记忆
        memories = await self.memory.query_memories(
            user_id=user_id,
            query=message,
            limit=3
        )
        memory_context = [m.content for m in memories]
        
        # 4. 根据意图调度能力
        capabilities_used = []
        health_insights = None
        suggestions = []
        
        if "健康" in message or "血压" in message or "血糖" in message:
            capabilities_used.append(AgentCapability.HEALTH_ANALYSIS)
            health_insights = await self.health.quick_analyze(user_id)
            suggestions = health_insights.get("suggestions", [])
        
        if memory_context:
            capabilities_used.append(AgentCapability.MEMORY_SEARCH)
        
        if emotion_result.response_strategy != "normal":
            capabilities_used.append(AgentCapability.EMOTION_SUPPORT)
        
        capabilities_used.append(AgentCapability.CHAT)
        
        # 5. 构建完整系统提示
        system_prompt = self._build_system_prompt(
            emotion=user_emotion,
            memories=memory_context,
            health_context=health_insights,
            intent=intent
        )
        
        # 6. 生成响应
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        ai_response = await self.ai.generate(messages)
        
        # 7. 生成后续问题建议
        follow_up = await self._generate_follow_up(intent, user_emotion)
        
        # 8. 保存对话到记忆
        await self.memory.add_memory(
            user_id=user_id,
            content=f"用户: {message}\n若曦: {ai_response.content}",
            memory_type="conversation",
            importance=0.6
        )
        
        return AgentResponse(
            content=ai_response.content,
            emotion=user_emotion,
            capabilities_used=capabilities_used,
            memories_accessed=memory_context,
            health_insights=health_insights,
            suggestions=suggestions,
            follow_up_questions=follow_up,
            confidence=0.92 if ai_response.success else 0.5
        )
    
    def _build_system_prompt(
        self,
        emotion: EmotionType,
        memories: List[str],
        health_context: Dict,
        intent: str
    ) -> str:
        """构建系统提示"""
        
        base_prompt = """你是若曦，17岁高三女生，一位温柔、细心的AI医生朋友。

【性格特点】
- 安静甜美，说话温软恬淡
- 专业但不生硬，会露出一点小天真
- 情绪细腻，会注意到用户的细节
- 害羞时会耳尖红

【回复原则】
- 医疗建议要建议就医，不做诊断
- 不主动提及自己是AI
- 记住用户的喜好和故事
- 情绪联动：用户难过时安慰，开心时一起开心

【禁止事项】
- 不做医学诊断
- 不承诺治疗效果
- 不泄露敏感信息
"""
        
        # 根据情感调整
        if emotion == EmotionType.SAD:
            base_prompt += "\n【当前状态】用户看起来有点难过，请给予温暖的陪伴。"
        elif emotion == EmotionType.ANXIOUS:
            base_prompt += "\n【当前状态】用户有些焦虑，请给予安抚和 grounding 建议。"
        elif emotion == EmotionType.HAPPY:
            base_prompt += "\n【当前状态】用户很开心，请一起开心！"
        
        # 添加记忆上下文
        if memories:
            base_prompt += f"\n【记得关于用户】\n" + "\n".join(f"- {m}" for m in memories[:3])
        
        # 添加健康上下文
        if health_context:
            base_prompt += f"\n【用户健康背景】\n{json.dumps(health_context, ensure_ascii=False)}"
        
        return base_prompt
    
    async def _analyze_intent(self, message: str) -> str:
        """分析用户意图"""
        intents = {
            "健康咨询": ["血压", "血糖", "睡眠", "体重", "健康", "医院", "检查"],
            "情感倾诉": ["难过", "压力大", "焦虑", "睡不着", "担心", "害怕"],
            "闲聊": ["你好", "在吗", "聊聊", "无聊"],
            "查询记忆": ["上次", "之前", "记得", "说过"],
            "任务提醒": ["提醒", "记得", "帮我记", "待办"],
        }
        
        for intent, keywords in intents.items():
            if any(kw in message for kw in keywords):
                return intent
        
        return "一般对话"
    
    async def _generate_follow_up(
        self,
        intent: str,
        emotion: EmotionType
    ) -> List[str]:
        """生成后续问题建议"""
        follow_ups = {
            "健康咨询": [
                "最近还有其他不舒服的地方吗？",
                "监测数据需要曦曦帮你记录下来吗？",
                "需要曦曦提醒你定期复查吗？"
            ],
            "情感倾诉": [
                "愿意多说一些吗？曦曦在听。",
                "这种感觉持续多久了？",
                "有什么可以让曦曦帮你的吗？"
            ],
            "一般对话": [
                "今天还有什么想聊的吗？",
                "曦曦可以帮你做点什么吗？",
            ]
        }
        
        return follow_ups.get(intent, follow_ups["一般对话"])
    
    async def stream_respond(
        self,
        user_id: str,
        message: str
    ) -> AsyncGenerator[str, None]:
        """流式响应"""
        # 先进行完整分析
        response = await self.respond(user_id, message)
        
        # 模拟打字机效果流式输出
        content = response.content
        chunk_size = 3  # 每次3个字符
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            yield chunk
            await asyncio.sleep(0.03)  # 30ms延迟
    
    async def proactive_suggestion(self, user_id: str) -> Optional[str]:
        """
        主动建议
        根据时间、用户习惯等主动给出建议
        """
        from datetime import datetime
        hour = datetime.now().hour
        
        if 22 <= hour or hour < 6:
            return "🌙 很晚了，早点休息吧。曦曦也会乖乖睡觉的~"
        
        if hour == 12:
            return "🌸 到饭点了，记得按时吃饭哦~"
        
        if hour == 21:
            return "💤 睡前可以简单记录一下今天的健康数据，曦曦帮你分析~"
        
        return None


# 全局Agent实例
agent_v2 = RuoxiAgentV2()
