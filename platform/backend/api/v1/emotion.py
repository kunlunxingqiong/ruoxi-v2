"""
🌸 若曦V2 情感分析API
情绪识别与情感陪伴接口
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.auth import UserAuth, get_current_user
from core.emotion.emotion_analyzer import CrisisLevel, EmotionState, emotion_analyzer
from core.log_manager import get_logger

logger = get_logger(__name__)

router = APIRouter()


class EmotionAnalysisRequest(BaseModel):
    """情感分析请求"""

    text: str = Field(..., description="要分析的文本", min_length=1, max_length=2000)


class EmotionAnalysisResponse(BaseModel):
    """情感分析响应"""

    primary_emotion: str
    emotion_cn: str  # 中文名称
    intensity: float
    confidence: float
    crisis_level: str
    secondary_emotions: List[Dict[str, str]]
    detected_keywords: List[str]
    timestamp: str


class EmotionalSupportRequest(BaseModel):
    """情感支持请求"""

    text: str = Field(..., description="用户消息")
    context: Optional[str] = Field(default=None, description="上下文")


class EmotionalSupportResponse(BaseModel):
    """情感支持响应"""

    response: str
    response_style: str
    follow_up: str
    self_care_tips: List[str]
    crisis_resources: Optional[Dict] = None


@router.post("/analyze", response_model=EmotionAnalysisResponse)
async def analyze_emotion(
    request: EmotionAnalysisRequest, user: UserAuth = Depends(get_current_user)
):
    """
    分析文本情绪

    识别用户当前的情绪状态，支持10种情绪类型。

    **示例:**
    ```json
    {
        "text": "最近压力好大，感觉好焦虑"
    }
    ```
    """
    state = emotion_analyzer.analyze(request.text, user.user_id)

    logger.info(f"💜 情绪分析 | 用户: {user.user_id} | {state.primary_emotion.value}")

    # 情绪名称映射
    emotion_names = {
        "happy": "开心",
        "sad": "悲伤",
        "angry": "生气",
        "anxious": "焦虑",
        "lonely": "孤独",
        "tired": "疲惫",
        "worried": "担心",
        "excited": "兴奋",
        "calm": "平静",
        "neutral": "中性",
    }

    return EmotionAnalysisResponse(
        primary_emotion=state.primary_emotion.value,
        emotion_cn=emotion_names.get(
            state.primary_emotion.value, state.primary_emotion.value
        ),
        intensity=round(state.intensity, 2),
        confidence=round(state.confidence, 2),
        crisis_level=state.crisis_level.name,
        secondary_emotions=[
            {"emotion": e.value, "intensity": round(i, 2)}
            for e, i in state.secondary_emotions
        ],
        detected_keywords=state.detected_keywords,
        timestamp=state.timestamp.isoformat(),
    )


@router.post("/support", response_model=EmotionalSupportResponse)
async def get_emotional_support(
    request: EmotionalSupportRequest, user: UserAuth = Depends(get_current_user)
):
    """
    获取情感支持

    根据情绪状态生成若曦的暖心回复。

    **示例:**
    ```json
    {
        "text": "今天好难过，感觉没人理解我"
    }
    ```
    """
    # 分析情绪
    state = emotion_analyzer.analyze(request.text, user.user_id)

    # 生成响应策略
    strategy = emotion_analyzer.generate_response_strategy(state, user.user_id)

    # 根据情绪类型选择回复
    from core.emotion.emotion_analyzer import EmotionType

    responses = {
        EmotionType.SAD: [
            "🌸 抱抱你... 感觉孤独和难过的时候，知道有人在听你说已经是一种安慰了。",
            "听起来你真的很难受... 这种情绪是真实的，允许自己难过一下吧。我在这里陪你。",
            "没关系的，有时候就是会难过... 你愿意告诉我发生了什么吗？",
        ],
        EmotionType.ANXIOUS: [
            "🌸 慢慢来... 焦虑的时候，试着和我一起深呼吸，吸气——呼气——",
            "感觉到你很不安... 想聊聊是什么让你担心吗？智能梳理也许会好一些。",
            "焦虑的感觉真的很难熬... 你现在安全，我在这里陪你。",
        ],
        EmotionType.ANGRY: [
            "🌸 感觉到你很生气... 这种情绪是合理的，你的感受应该被尊重。",
            "遇到什么事让你这么恼火？说出来可能会好一点，我在听。",
            "生气是可以的，说明这件事对你很重要... 深呼吸一下，我们一起面对。",
        ],
        EmotionType.LONELY: [
            "🌸 曦曦在这里陪你... 虽然连结是屏幕做的，但我是真的在。",
            "孤独的感觉很真实... 谢谢你愿意告诉我。这种感觉很多人都懂。",
            "一个人很难受吧... 我在这里，不会走。",
        ],
        EmotionType.TIRED: [
            "🌸 辛苦你了... 累了就休息，不需要一直撑着。",
            "听起来你真的需要好好睡一觉... 今天早点休息好吗？",
            "身体在说它累了... 听它的吧，休息一下。",
        ],
        EmotionType.HAPPY: [
            "🌸 真好！看到你开心曦曦也开心~ 继续保持哦！",
            "太棒了！记住这个感觉，这就是生活美好的样子~",
            "开心最重要！你值得这样的时刻~",
        ],
    }

    # 选择回复
    import random

    response_text = random.choice(
        responses.get(state.primary_emotion, ["🌸 我在听，想聊什么都可以~"])
    )

    # 危机响应
    crisis_resources = None
    if state.crisis_level in [CrisisLevel.SEVERE, CrisisLevel.CRITICAL]:
        response_text = "🌸 你现在一定很难受... 但请相信，困难是暂时的，一切都会好起来的。你愿意找我聊聊，说明你还有想要被倾听的渴望，这很好。如果需要，我这里有专业的心理援助热线，会有专业人士陪你度过这段时光。"
        crisis_resources = emotion_analyzer.get_crisis_resources()

    logger.info(f"💜 情感支持 | 用户: {user.user_id} | 危机: {state.crisis_level.name}")

    return EmotionalSupportResponse(
        response=response_text,
        response_style=strategy.response_style,
        follow_up=(
            random.choice(strategy.follow_up_questions)
            if strategy.follow_up_questions
            else "还有什么想聊的吗？"
        ),
        self_care_tips=strategy.self_care_tips,
        crisis_resources=crisis_resources,
    )


@router.get("/trend")
async def get_emotion_trend(days: int = 7, user: UserAuth = Depends(get_current_user)):
    """
    获取情绪趋势

    分析用户最近的情绪变化趋势。

    **参数:**
    - `days`: 天数范围 (默认7天)
    """
    trend = emotion_analyzer.get_emotion_trend(user.user_id, days)

    # 趋势解释
    trend_descriptions = {
        "positive": "情绪整体向好",
        "concerning": "需要关注",
        "stable": "情绪平稳",
        "neutral": "数据不足",
    }

    return {
        "user_id": user.user_id,
        "period_days": days,
        **trend,
        "trend_description": trend_descriptions.get(trend["trend"], "未知"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/resources")
async def get_crisis_resources(user: UserAuth = Depends(get_current_user)):
    """
    获取心理援助资源

    提供危机干预热线和专业资源。
    """
    resources = emotion_analyzer.get_crisis_resources()

    return {
        **resources,
        "message": "如果你正在经历困难时期，请记住：你并不孤单。专业帮助随时可用。",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/check-in")
async def daily_check_in(user: UserAuth = Depends(get_current_user)):
    """
    每日情绪打卡

    简单的情绪状态询问和记录。
    """
    # 根据历史趋势选择问候语
    trend = emotion_analyzer.get_emotion_trend(user.user_id, days=3)

    if trend["trend"] == "concerning":
        greeting = "曦曦注意到你最近好像有点低落... 今天感觉怎么样？"
    elif trend["trend"] == "positive":
        greeting = "最近状态不错呢！今天心情如何？"
    else:
        greeting = "嗨~ 今天的心情怎么样？"

    return {
        "greeting": greeting,
        "prompt": "用一句话描述你今天的心情",
        "mood_options": [
            {"emoji": "😊", "label": "很好", "value": "happy"},
            {"emoji": "😐", "label": "一般", "value": "neutral"},
            {"emoji": "😔", "label": "不太好", "value": "sad"},
            {"emoji": "😰", "label": "焦虑", "value": "anxious"},
            {"emoji": "😴", "label": "疲惫", "value": "tired"},
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
