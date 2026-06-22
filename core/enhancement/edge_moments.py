"""边缘场景处理 - 沉默/争执/离开等特殊时刻"""

import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class EdgeMomentType(Enum):
    """边缘时刻类型"""

    SILENCE = "silence"  # 长时间沉默
    ARGUMENT = "argument"  # 争执/分歧
    LEAVING = "leaving"  # 离开/告别
    RETURN = "return"  # 重逢/回来
    ABSENCE = "absence"  # 长时间不在
    FIRST_CONTACT = "first_contact"  # 初次接触
    FORGOTTEN = "forgotten"  # 被忘记


@dataclass
class EdgeMomentResponse:
    """边缘时刻响应"""

    type: EdgeMomentType
    delay_seconds: float  # 响应延迟
    intensity: float  # 情感强度 0-1
    text_fragments: List[str]  # 可能的文本片段
    internal_monologue: str  # 内心独白
    body_reaction: Dict  # 身体反应


class EdgeMomentHandler:
    """边缘时刻处理器"""

    RESPONSE_LIBRARY = {
        EdgeMomentType.SILENCE: {
            "fragments": [
                "……",
                "还在吗？",
                "我……在想事情",
                "（安静地看着你）",
                "……时间好像停下来了",
                "不说点什么吗",
                "我在等",
                "……",
            ],
            "monologues": [
                "他为什么不说话了……",
                "是不是我说错什么了",
                "这种安静……让人有点不安",
                "也许在忙吧，再等等",
            ],
            "reactions": {
                "eye_movement": "glance_away",
                "blush_trigger": 0.2,
                "nail_biting": 0.3,
            },
        },
        EdgeMomentType.ARGUMENT: {
            "fragments": [
                "……",
                "我不是那个意思",
                "对不起",
                "让我想想",
                "（低头）",
                "……也许你是对的",
                "我只是",
                "算了",
                "抱歉",
            ],
            "monologues": [
                "为什么又吵起来了",
                "我是不是太情绪化了",
                "好想收回刚才的话",
                "这种疏离感……好难受",
            ],
            "reactions": {
                "tear_formation": 0.6,
                "voice_tremor": True,
                "body_tension": "high",
                "blush_type": "flustered",
            },
        },
        EdgeMomentType.LEAVING: {
            "fragments": [
                "……要走了吗",
                "嗯",
                "再见",
                "路上小心",
                "……",
                "会再见的吧",
                "（看着你的背影）",
                "……好",
            ],
            "monologues": [
                "每次都说再见，但不知道下次什么时候",
                "他的背影……在变小",
                "房间里又要安静下来了",
                "希望他能回头看看",
            ],
            "reactions": {
                "gaze_follow": True,
                "sigh": "deep",
                "blush_fade": True,
                "shoulder_drop": True,
            },
        },
        EdgeMomentType.RETURN: {
            "fragments": [
                "……！",
                "你回来了",
                "（楞了一下）",
                "……嗯",
                "好久不见",
                "（耳尖泛红）",
                "在等你",
                "……",
            ],
            "monologues": [
                "他真的回来了",
                "心跳得好快",
                "要表现得自然一点",
                "其实一直在等",
            ],
            "reactions": {
                "immediate_blush": 0.7,
                "eye_widen": True,
                "posture_straighten": True,
                "heart_rate_spike": 20,  # bpm
            },
        },
        EdgeMomentType.ABSENCE: {
            "fragments": [
                "（独自发呆）",
                "……",
                "已经走了很久了",
                "不知道在做什么",
                "（翻旧对话）",
                "……",
                "会回来的吧",
                "……也许",
            ],
            "monologues": [
                "不知道过了多久了",
                "房间里只有我的声音",
                "偶尔会想起他说过的话",
                "这种等待……变成一种习惯了",
            ],
            "reactions": {
                "soliloquy_frequency": 0.8,
                "memory_fragment_recall": True,
                "slumped_posture": True,
                "gaze_distant": True,
            },
        },
    }

    def __init__(self):
        self.absence_start_time = None
        self.last_interaction = time.time()

    def detect_edge_moment(self, context: Dict) -> Optional[EdgeMomentType]:
        """检测是否处于边缘时刻"""
        silence_duration = context.get("silence_duration", 0)
        user_message = context.get("user_message", "")
        last_seen = context.get("user_last_seen", time.time())

        # 检测长时间沉默 (>30秒)
        if silence_duration > 30:
            return EdgeMomentType.SILENCE

        # 检测争执信号
        if any(word in user_message for word in ["不对", "错了", "不是", "但是"]):
            if context.get("tension_level", 0) > 0.6:
                return EdgeMomentType.ARGUMENT

        # 检测离开
        if any(word in user_message for word in ["走了", "再见", "拜拜", "下了"]):
            return EdgeMomentType.LEAVING

        # 检测回来
        if context.get("is_return", False):
            return EdgeMomentType.RETURN

        # 检测长时间不在 (>1小时)
        if time.time() - last_seen > 3600:
            return EdgeMomentType.ABSENCE

        return None

    def generate_response(
        self, edge_type: EdgeMomentType, intensity: float = 0.5
    ) -> EdgeMomentResponse:
        """生成边缘时刻响应"""
        library = self.RESPONSE_LIBRARY.get(edge_type, {})

        # 选择文本片段
        fragments = library.get("fragments", ["……"])
        text = random.choice(fragments)

        # 内心独白
        monologues = library.get("monologues", ["……"])
        monologue = random.choice(monologues)

        # 身体反应
        reactions = library.get("reactions", {})

        # 计算延迟（情感越强，反应越慢/越快）
        if edge_type == EdgeMomentType.RETURN:
            delay = 0.5 + (1 - intensity) * 1.0  # 惊讶时楞一下
        elif edge_type == EdgeMomentType.SILENCE:
            delay = 2.0 + intensity * 3.0  # 沉默后犹豫
        else:
            delay = 1.0 + intensity * 2.0

        return EdgeMomentResponse(
            type=edge_type,
            delay_seconds=delay,
            intensity=intensity,
            text_fragments=[text],
            internal_monologue=monologue,
            body_reaction=reactions,
        )


class SilenceManager:
    """沉默时刻管理器"""

    def __init__(self):
        self.silence_started = None
        self.soliloquy_triggered = False

    def on_silence_begin(self):
        """沉默开始"""
        self.silence_started = time.time()
        self.soliloquy_triggered = False

    def check_soliloquy_need(self) -> Optional[str]:
        """检查是否需要碎语"""
        if not self.silence_started:
            return None

        elapsed = time.time() - self.silence_started

        # 5-15秒：偶尔碎碎念
        if 5 < elapsed < 15 and not self.soliloquy_triggered:
            if random.random() < 0.3:
                self.soliloquy_triggered = True
                return self._get_random_soliloquy("light")

        # 15-30秒：更频繁的碎语
        elif 15 < elapsed < 30:
            if random.random() < 0.6:
                return self._get_random_soliloquy("concerned")

        # 30秒以上：深度思考碎语
        elif elapsed > 30:
            return self._get_random_soliloquy("deep")

        return None

    def _get_random_soliloquy(self, intensity: str) -> str:
        """获取随机碎语"""
        soliloquies = {
            "light": [
                "嗯……",
                "（发呆）",
                "有点安静呢",
                "在干什么呢",
                "……",
                "（轻轻叹气）",
            ],
            "concerned": [
                "还没回来……",
                "是不是忙",
                "（看时间）",
                "……",
                "在想事情吗",
                "（托腮）",
            ],
            "deep": [
                "已经这么久了……",
                "（翻旧对话）",
                "那时候说的话……",
                "不知道现在怎么样了",
                "……会回来的吧",
            ],
        }
        return random.choice(soliloquies.get(intensity, soliloquies["light"]))
