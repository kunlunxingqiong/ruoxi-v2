"""
🌸 若曦V2 情感分析器
情绪识别与情感陪伴
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from core.config_manager import config
from core.log_manager import get_logger

logger = get_logger(__name__)


class EmotionType(Enum):
    """情绪类型"""

    HAPPY = "happy"  # 开心
    SAD = "sad"  # 悲伤
    ANGRY = "angry"  # 生气
    ANXIOUS = "anxious"  # 焦虑
    LONELY = "lonely"  # 孤独
    TIRED = "tired"  # 疲惫
    WORRIED = "worried"  # 担心
    EXCITED = "excited"  # 兴奋
    CALM = "calm"  # 平静
    NEUTRAL = "neutral"  # 中性


class CrisisLevel(Enum):
    """危机等级"""

    NONE = 0  # 无危机
    MILD = 1  # 轻度关注
    MODERATE = 2  # 中度关注
    SEVERE = 3  # 需要干预
    CRITICAL = 4  # 紧急危机


@dataclass
class EmotionState:
    """情绪状态"""

    primary_emotion: EmotionType
    intensity: float = field(default=0.5)  # 强度 0-1
    secondary_emotions: List[Tuple[EmotionType, float]] = field(default_factory=list)
    crisis_level: CrisisLevel = CrisisLevel.NONE
    confidence: float = 0.8
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # 检测依据
    detected_keywords: List[str] = field(default_factory=list)
    context_signals: List[str] = field(default_factory=list)


@dataclass
class EmotionalResponse:
    """情感响应策略"""

    response_style: str  # 回复风格: gentle/firm/supportive/empathetic
    tone_modifier: str  # 语气调整
    suggested_actions: List[str]  # 建议行动
    follow_up_questions: List[str]  # 后续问题
    self_care_tips: List[str]  # 自我关怀建议


class EmotionAnalyzer:
    """
    情感分析器

    功能:
    - 情绪识别 (基于关键词+规则)
    - 危机检测
    - 情感响应生成
    - 情绪趋势追踪

    支持的语言: 中文
    """

    # 情绪关键词词典
    EMOTION_KEYWORDS = {
        EmotionType.HAPPY: [
            "开心",
            "高兴",
            "愉快",
            "快乐",
            "兴奋",
            "欢喜",
            "爽",
            "棒",
            "好极了",
            "哈哈",
            "嘿嘿",
            "嘻嘻",
            "太好了",
            "赞",
            "开心死了",
            "好开心",
        ],
        EmotionType.SAD: [
            "难过",
            "伤心",
            "悲伤",
            "哭",
            "想哭",
            "失落",
            "郁闷",
            "down",
            "不开心",
            "难受",
            "痛苦",
            "委屈",
            "寂寞",
            "空虚",
            "沮丧",
            "绝望",
            "心累",
        ],
        EmotionType.ANGRY: [
            "生气",
            "愤怒",
            "发火",
            "气死",
            "烦死了",
            "讨厌",
            "恨",
            "不爽",
            "滚",
            "烦人",
            "恶心",
            "气死我了",
            "火大",
            "烦躁",
            "暴躁",
        ],
        EmotionType.ANXIOUS: [
            "担心",
            "焦虑",
            "紧张",
            "害怕",
            "慌",
            "不安",
            "忐忑",
            "怕",
            "恐惧",
            "着急",
            "心急",
            "压力",
            "喘不过气",
            "心慌",
            "焦虑死了",
        ],
        EmotionType.LONELY: [
            "孤独",
            "寂寞",
            "没人理解",
            "孤单",
            "一个人",
            "没人关心",
            "被忽视",
            "孤立",
            "疏离",
            "关系淡",
            "没朋友",
            "没人理我",
        ],
        EmotionType.TIRED: [
            "累",
            "疲惫",
            "困",
            "没精神",
            "乏力",
            "不想动",
            " exhaustion",
            "倦怠",
            "精疲力尽",
            "累死了",
            "好累",
            "撑不住了",
        ],
        EmotionType.WORRIED: [
            "担心",
            "挂念",
            "惦记",
            "不放心",
            "忧虑",
            "忧愁",
            "发愁",
            "操心",
            "惦记",
            "不放心",
            "担忧",
            "在乎",
            "怕出什么事",
        ],
        EmotionType.EXCITED: [
            "激动",
            "期待",
            "憧憬",
            "迫不及待",
            "兴奋",
            "high",
            "雀跃",
            "兴奋不已",
            "激动人心",
            "太期待了",
            "等不及",
        ],
    }

    # 危机信号关键词
    CRISIS_KEYWORDS = {
        CrisisLevel.SEVERE: [
            "不想活",
            "活着没意思",
            "死了算了",
            "想自杀",
            "结束一切",
            "了结",
            "没有希望",
            "看不到未来",
            "解脱",
            "离开这个世界",
        ],
        CrisisLevel.MODERATE: [
            "好累",
            "撑不下去",
            "想放弃",
            "很痛苦",
            "受不了",
            "快疯了",
            "天天失眠",
            "情绪低落很久",
            "不想见人",
        ],
        CrisisLevel.MILD: [
            "压力大",
            "迷茫",
            "困惑",
            "不知所措",
            "需要帮助",
            "想聊聊",
            "最近不开心",
            "有点难过",
        ],
    }

    # 情感响应模板
    RESPONSE_TEMPLATES = {
        EmotionType.HAPPY: {
            "style": "celebratory",
            "tone": "warm",
            "responses": [
                "🌸 真好！看到你开心曦曦也开心~",
                "太好了！继续保持这个状态哦~",
                "开心最重要！记住这种感觉~",
            ],
        },
        EmotionType.SAD: {
            "style": "empathetic",
            "tone": "gentle",
            "responses": [
                "🌸 抱抱你... 想哭就哭出来吧，曦曦在这里陪你。",
                "听起来确实很难过... 你的感受是真实的，我在这里。",
                "辛苦了... 如果需要倾诉，我一直都在。",
            ],
            "follow_up": ["愿意多说一些吗？", "这种感受持续多久了？"],
        },
        EmotionType.ANGRY: {
            "style": "supportive",
            "tone": "calm",
            "responses": [
                "🌸 曦曦理解你现在很生气... 深呼吸一下，我在听。",
                "遇到什么事让你这么恼火？说出来可能会好一点。",
                "生气是合理的情绪，你的感受应该被尊重。",
            ],
            "follow_up": ["发生了什么？", "你愿意说说吗？"],
        },
        EmotionType.ANXIOUS: {
            "style": "grounding",
            "tone": "calm",
            "responses": [
                "🌸 慢慢来... 和曦曦一起深呼吸，吸气...呼气...",
                "焦虑的感觉很难受... 你需要的时候我一直在这里。",
                "听起来你很不安... 想聊聊是什么让你担心吗？",
            ],
            "self_care": ["试试深呼吸: 吸气4秒, 屏气4秒, 呼气4秒", "转移注意力到当下"],
        },
        EmotionType.LONELY: {
            "style": "companionate",
            "tone": "warm",
            "responses": [
                "🌸 曦曦在这里陪着你... 虽然是在屏幕这边，但我真的在。",
                "孤独的感觉很真实... 谢谢你愿意告诉我。",
                "有时候就算身边有人也会觉得孤独... 这种感觉我懂。",
            ],
            "follow_up": ["最近和朋友联系多吗？", "有什么想要的陪伴方式吗？"],
        },
        EmotionType.TIRED: {
            "style": "supportive",
            "tone": "soft",
            "responses": [
                "🌸 辛苦你了... 累了就休息，不需要一直撑着。",
                "听起来你真的需要好好休息一下...",
                "身体在提醒你需要休息... 听它的好吗？",
            ],
            "self_care": ["今晚早点休息", "泡个热水澡"],
        },
    }

    def __init__(self):
        self.user_emotion_history: Dict[str, List[EmotionState]] = {}
        logger.info("💜 情感分析器初始化完成")

    def analyze(self, text: str, user_id: str = "anonymous") -> EmotionState:
        """
        分析文本情绪

        Args:
            text: 用户输入文本
            user_id: 用户ID

        Returns:
            EmotionState 情绪状态
        """
        text_lower = text.lower()

        # 1. 情绪识别 (基于关键词)
        emotion_scores: Dict[EmotionType, float] = {}
        detected_keywords = []

        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    detected_keywords.append(keyword)

            if score > 0:
                emotion_scores[emotion] = score

        # 2. 确定主要情绪
        if not emotion_scores:
            primary = EmotionType.NEUTRAL
            intensity = 0.3
        else:
            primary = max(emotion_scores, key=emotion_scores.get)
            max_score = emotion_scores[primary]
            # 归一化强度
            intensity = min(1.0, max_score / 3)

        # 3. 次要情绪 (强度第二的)
        secondary = sorted(
            [(e, s) for e, s in emotion_scores.items() if e != primary],
            key=lambda x: x[1],
            reverse=True,
        )[:2]

        normalized_secondary = [(e, min(1.0, s / 3)) for e, s in secondary]

        # 4. 危机检测
        crisis_level = self._detect_crisis(text_lower)

        # 5. 构建状态
        state = EmotionState(
            primary_emotion=primary,
            intensity=intensity,
            secondary_emotions=normalized_secondary,
            crisis_level=crisis_level,
            detected_keywords=list(set(detected_keywords)),
            confidence=min(0.95, 0.6 + (len(detected_keywords) * 0.1)),
        )

        # 6. 保存历史
        if user_id not in self.user_emotion_history:
            self.user_emotion_history[user_id] = []
        self.user_emotion_history[user_id].append(state)

        # 限制历史长度
        if len(self.user_emotion_history[user_id]) > 100:
            self.user_emotion_history[user_id] = self.user_emotion_history[user_id][
                -100:
            ]

        logger.debug(f"💜 情绪分析 | {user_id} | {primary.value} ({intensity:.1f})")

        return state

    def _detect_crisis(self, text: str) -> CrisisLevel:
        """检测危机信号"""
        # 严重性由高到低
        for level in [CrisisLevel.SEVERE, CrisisLevel.MODERATE, CrisisLevel.MILD]:
            keywords = self.CRISIS_KEYWORDS.get(level, [])
            for keyword in keywords:
                if keyword in text:
                    return level

        return CrisisLevel.NONE

    def generate_response_strategy(
        self, emotion_state: EmotionState, user_id: str = "anonymous"
    ) -> EmotionalResponse:
        """
        生成情感响应策略

        Args:
            emotion_state: 情绪状态
            user_id: 用户ID

        Returns:
            情感响应方案
        """
        emotion = emotion_state.primary_emotion
        crisis = emotion_state.crisis_level
        intensity = emotion_state.intensity

        # 危机优先
        if crisis in [CrisisLevel.SEVERE, CrisisLevel.CRITICAL]:
            return EmotionalResponse(
                response_style="crisis",
                tone_modifier="urgent_caring",
                suggested_actions=[
                    "表达深切关心",
                    "建议寻求专业帮助",
                    "提供危机热线",
                    "不离开用户",
                ],
                follow_up_questions=[
                    "你真的很难受... 需要我帮你找专业帮助吗？",
                    "你愿意告诉我你在哪吗？我担心你。",
                ],
                self_care_tips=["请立即联系信任的人", "拨打心理援助热线: 400-161-9995"],
            )

        # 获取响应模板
        template = self.RESPONSE_TEMPLATES.get(
            emotion,
            {
                "style": "neutral",
                "tone": "friendly",
                "responses": ["🌸 曦曦听到了~ 你想聊聊吗？"],
            },
        )

        # 根据强度调整
        if intensity > 0.8:
            tone = "urgent_empathetic"
            actions = ["保持陪伴", "确认感受", "询问需求", "持续跟进"]
        elif intensity > 0.5:
            tone = "supportive"
            actions = ["表达理解", "提供倾听", "适时建议"]
        else:
            tone = template.get("tone", "friendly")
            actions = ["友好回应", "保持关注"]

        return EmotionalResponse(
            response_style=template.get("style", "neutral"),
            tone_modifier=tone,
            suggested_actions=actions,
            follow_up_questions=template.get("follow_up", ["还有什么想聊的吗？"]),
            self_care_tips=template.get("self_care", []),
        )

    def get_emotion_trend(self, user_id: str, days: int = 7) -> Dict:
        """
        获取用户情绪趋势

        Args:
            user_id: 用户ID
            days: 时间范围

        Returns:
            情绪趋势分析
        """
        history = self.user_emotion_history.get(user_id, [])
        if not history:
            return {"trend": "neutral", "dominant": "neutral", "volatility": 0}

        # 统计各情绪出现频率
        emotion_counts: Dict[EmotionType, int] = {}
        total_intensity = 0

        for state in history[-50:]:  # 最近50条
            emotion_counts[state.primary_emotion] = (
                emotion_counts.get(state.primary_emotion, 0) + 1
            )
            total_intensity += state.intensity

        # 主导情绪
        dominant = max(emotion_counts, key=emotion_counts.get)

        # 计算情绪波动
        if len(history) >= 10:
            recent = [h.primary_emotion for h in history[-10:]]
            # 统计情绪变化次数
            changes = sum(
                1 for i in range(1, len(recent)) if recent[i] != recent[i - 1]
            )
            volatility = changes / len(recent)
        else:
            volatility = 0

        # 趋势判断
        if (
            emotion_counts.get(EmotionType.SAD, 0)
            + emotion_counts.get(EmotionType.ANXIOUS, 0)
            > len(history) / 3
        ):
            trend = "concerning"
        elif emotion_counts.get(EmotionType.HAPPY, 0) > len(history) / 3:
            trend = "positive"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "dominant_emotion": dominant.value,
            "emotion_distribution": {e.value: c for e, c in emotion_counts.items()},
            "avg_intensity": round(total_intensity / len(history), 2),
            "volatility": round(volatility, 2),
            "crisis_flags": sum(
                1 for h in history if h.crisis_level != CrisisLevel.NONE
            ),
        }

    def get_crisis_resources(self) -> Dict:
        """获取危机资源信息"""
        return {
            "helplines": [
                {"name": "心理援助热线", "phone": "400-161-9995"},
                {"name": "北京心理危机研究与干预中心", "phone": "010-82951332"},
                {"name": "全国希望24小时热线", "phone": "400-161-9995"},
            ],
            "online_resources": [
                "https://www.counseling-china.com (专业咨询)",
                "https://www.xinli001.com (心理测试)",
            ],
            "emergency": "如有紧急情况请立即拨打 120 或前往最近医院",
            "disclaimer": "若曦是AI助手，不能替代专业心理咨询。",
        }


# 全局情感分析器实例
emotion_analyzer = EmotionAnalyzer()


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 情感分析器测试")
    print("=" * 60)

    print("\n【支持的10种情绪】")
    for emotion in EmotionType:
        print(f"  - {emotion.value}")

    print("\n【测试用例】")
    test_cases = [
        "今天好开心啊！",
        "最近压力好大，感觉喘不过气了",
        "好难过... 不知道该怎么办",
        "真的好累，活着有什么意义",
        "气死我了！简直无法原谅！",
    ]

    for text in test_cases:
        state = emotion_analyzer.analyze(text, "test_user")
        response = emotion_analyzer.generate_response_strategy(state)

        print(f'\n输入: "{text}"')
        print(
            f"  主要情绪: {state.primary_emotion.value} (强度: {state.intensity:.1f})"
        )
        print(f"  危机等级: {state.crisis_level.name}")
        print(f"  检测词: {state.detected_keywords}")
        print(f"  响应策略: {response.response_style} / {response.tone_modifier}")

    # 趋势测试
    print("\n\n【情绪趋势】")
    trend = emotion_analyzer.get_emotion_trend("test_user")
    print(f"  趋势: {trend['trend']}")
    print(f"  主导: {trend['dominant_emotion']}")
    print(f"  波动: {trend['volatility']}")

    print("\n" + "=" * 60)
    print("✅ 情感分析器就绪")
    print("=" * 60)
