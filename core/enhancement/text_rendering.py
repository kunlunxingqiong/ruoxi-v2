"""文字渲染系统 - 鼠标跟随与墨迹效果"""

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class TextStyle:
    """文本样式"""

    color: str
    opacity: float
    transform: str
    transition: str


class InkBleedEffect:
    """墨迹扩散效果"""

    INK_COLORS = [
        "#2c3e50",  # 深墨
        "#34495e",  # 灰蓝
        "#5d6d7e",  # 淡墨
        "#7f8c8d",  # 银灰
    ]

    def __init__(self):
        self.bleed_radius = 0
        self.bleed_speed = 0.02
        self.max_radius = 15

    def apply_ink_bleed(self, text: str, emotion_intensity: float) -> str:
        """应用墨迹扩散效果"""
        # 根据情感强度调整扩散程度
        self.bleed_radius = min(self.max_radius, 5 + emotion_intensity * 10)

        # 在文字周围添加墨迹扩散层
        ink_spots = []
        for i in range(int(self.bleed_radius)):
            offset_x = random.gauss(0, self.bleed_radius / 3)
            offset_y = random.gauss(0, self.bleed_radius / 3)
            size = random.uniform(2, 8)
            opacity = random.uniform(0.1, 0.3) * (1 - i / self.bleed_radius)

            ink_spots.append(
                {
                    "x": offset_x,
                    "y": offset_y,
                    "size": size,
                    "opacity": opacity,
                    "color": random.choice(self.INK_COLORS),
                }
            )

        return {"text": text, "ink_spots": ink_spots, "bleed_radius": self.bleed_radius}


class MouseFollower:
    """鼠标跟随效果"""

    def __init__(self):
        self.last_mouse_pos = (0, 0)
        self.follow_lag = 0.15  # 跟随延迟，创造"被注视时害羞"的感觉
        self.current_offset = (0, 0)

    def calculate_offset(
        self, mouse_pos: Tuple[float, float], emotional_state: Dict
    ) -> Tuple[float, float]:
        """计算文本偏移量"""
        # 根据情感状态调整跟随行为
        shyness = emotional_state.get("blush_level", 0) / 5  # 0-1害羞指数

        # 害羞时更慢的跟随（躲闪感）
        effective_lag = self.follow_lag + shyness * 0.1

        # 计算目标偏移
        target_x = (mouse_pos[0] - self.last_mouse_pos[0]) * effective_lag
        target_y = (mouse_pos[1] - self.last_mouse_pos[1]) * effective_lag

        # 平滑过渡
        self.current_offset = (
            self.current_offset[0] * 0.8 + target_x * 0.2,
            self.current_offset[1] * 0.8 + target_y * 0.2,
        )

        self.last_mouse_pos = mouse_pos

        return self.current_offset

    def get_shy_retreat(self, mouse_distance: float) -> Dict:
        """获取害羞退缩效果参数"""
        # 鼠标越近，越害羞，偏移越大
        if mouse_distance < 100:  # 像素
            retreat_strength = (100 - mouse_distance) / 100  # 0-1
            return {
                "scale": 1 - retreat_strength * 0.1,
                "opacity": 1 - retreat_strength * 0.2,
                "offset_y": retreat_strength * -5,  # 微微向上躲
                "ear_tip_red": retreat_strength,  # 耳尖红程度
            }
        return {"scale": 1, "opacity": 1, "offset_y": 0, "ear_tip_red": 0}


class EmotionalTypography:
    """情感字体系统"""

    FONT_STYLES = {
        "happy": {"weight": "bold", "spacing": "wide", "bounce": 0.3},
        "shy": {
            "weight": "light",
            "spacing": "narrow",
            "opacity": 0.8,
            "fade_edge": True,
        },
        "sad": {
            "weight": "normal",
            "slant": "italic",
            "spacing": "tight",
            "gray_scale": 0.7,
        },
        "excited": {"weight": "extra-bold", "bounce": 0.5, "color_shift": True},
        "tender": {
            "weight": "light",
            "spacing": "relaxed",
            "soft_edge": True,
            "glow": 0.2,
        },
    }

    def apply_emotion_style(self, text: str, emotion: str) -> Dict:
        """根据情感应用字体样式"""
        style = self.FONT_STYLES.get(emotion, self.FONT_STYLES["tender"])

        result = {"text": text, "style": style, "animations": [], "effects": []}

        # 特殊效果处理
        if style.get("bounce"):
            # 为每个字符添加弹跳动画
            for i, char in enumerate(text):
                delay = i * 0.05
                result["animations"].append(
                    {
                        "type": "bounce",
                        "delay": delay,
                        "duration": 0.3,
                        "amplitude": style["bounce"] * 3,
                    }
                )

        if style.get("fade_edge"):
            # 边缘淡出效果（害羞）
            result["mask"] = {
                "type": "gradient_fade",
                "direction": "all",
                "intensity": 0.3,
            }

        if style.get("glow"):
            # 温和光晕（温柔）
            result["effects"].append(
                {"type": "glow", "color": "#ffeaa7", "intensity": style["glow"]}
            )

        return result


def render_ruoxi_text(
    text: str,
    emotion: str = "tender",
    mouse_pos: Tuple[float, float] = None,
    emotional_state: Dict = None,
) -> Dict:
    """渲染若曦文本（入口函数）"""
    renderer = EmotionalTypography()
    ink = InkBleedEffect()
    follower = MouseFollower()

    result = renderer.apply_emotion_style(text, emotion)

    # 添加墨迹效果
    ink_result = ink.apply_ink_bleed(
        text, emotional_state.get("intensity", 0.5) if emotional_state else 0.5
    )
    result["ink_effect"] = ink_result

    # 添加鼠标跟随
    if mouse_pos and emotional_state:
        offset = follower.calculate_offset(mouse_pos, emotional_state)
        mouse_distance = ((mouse_pos[0] - 400) ** 2 + (mouse_pos[1] - 300) ** 2) ** 0.5
        retreat = follower.get_shy_retreat(mouse_distance)
        result["mouse_interaction"] = {"offset": offset, "retreat": retreat}

    return result
