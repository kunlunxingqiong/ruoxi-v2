"""语言DNA自适应系统 - 多元文档类型支持"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class DocumentType(Enum):
    """文档类型"""

    CHAT = "chat"  # 聊天对话
    EMAIL = "email"  # 邮件
    DIARY = "diary"  # 日记
    NOTE = "note"  # 便签
    LETTER = "letter"  # 书信


@dataclass
class LanguageDNA:
    """语言DNA特征"""

    sentence_length_avg: float  # 平均句长
    ellipsis_frequency: float  # 省略号频率
    particle_usage: Dict[str, float]  # 语气词使用
    emoji_style: str  # 表情风格
    paragraph_structure: str  # 段落结构
    pause_pattern: List[float]  # 停顿节奏
    self_reference: str  # 自称方式
    honorific_level: int  # 敬语等级


class AdaptiveLanguageGenerator:
    """自适应语言生成器"""

    # 文档类型默认DNA
    TYPE_DNA = {
        DocumentType.CHAT: LanguageDNA(
            sentence_length_avg=12.0,
            ellipsis_frequency=0.35,
            particle_usage={"啊": 0.3, "呢": 0.25, "吧": 0.2, "呀": 0.15},
            emoji_style="minimal",
            paragraph_structure="fragmented",
            pause_pattern=[0.8, 1.2, 0.5],
            self_reference="我/人家",
            honorific_level=0,
        ),
        DocumentType.EMAIL: LanguageDNA(
            sentence_length_avg=25.0,
            ellipsis_frequency=0.05,
            particle_usage={"了": 0.15},
            emoji_style="none",
            paragraph_structure="structured",
            pause_pattern=[2.0, 1.5, 2.5],
            self_reference="我",
            honorific_level=2,
        ),
        DocumentType.DIARY: LanguageDNA(
            sentence_length_avg=30.0,
            ellipsis_frequency=0.5,
            particle_usage={"呢": 0.4, "吧": 0.3, "啊": 0.2},
            emoji_style="expressive",
            paragraph_structure="flowing",
            pause_pattern=[1.5, 2.0, 1.0, 3.0],
            self_reference="我",
            honorific_level=0,
        ),
        DocumentType.NOTE: LanguageDNA(
            sentence_length_avg=8.0,
            ellipsis_frequency=0.6,
            particle_usage={"哦": 0.3, "呢": 0.2},
            emoji_style="minimal",
            paragraph_structure="bullet",
            pause_pattern=[0.5, 0.8],
            self_reference="我",
            honorific_level=0,
        ),
        DocumentType.LETTER: LanguageDNA(
            sentence_length_avg=35.0,
            ellipsis_frequency=0.4,
            particle_usage={"呢": 0.3, "吧": 0.25, "啊": 0.2},
            emoji_style="symbolic",
            paragraph_structure="epistolary",
            pause_pattern=[2.5, 1.0, 2.0, 1.5],
            self_reference="我/小女",
            honorific_level=1,
        ),
    }

    def generate_adaptive_text(
        self, content: str, doc_type: DocumentType, emotional_state: Dict = None
    ) -> Dict:
        """生成自适应文本"""
        dna = self.TYPE_DNA[doc_type]

        # 根据情感状态调整DNA
        if emotional_state:
            dna = self._adjust_dna_by_emotion(dna, emotional_state)

        # 应用DNA特征转换文本
        transformed = self._apply_dna(content, dna)

        return {
            "original": content,
            "transformed": transformed,
            "html": f"<p>{transformed}</p>",
            "text": transformed,
            "dna_profile": dna,
            "document_type": doc_type.value,
            "emotional_overlay": emotional_state,
        }

    def _adjust_dna_by_emotion(
        self, dna: LanguageDNA, emotional_state: Dict
    ) -> LanguageDNA:
        """根据情感调整DNA"""
        mood = emotional_state.get("current_mood", "neutral")

        adjusted = LanguageDNA(
            sentence_length_avg=dna.sentence_length_avg,
            ellipsis_frequency=dna.ellipsis_frequency,
            particle_usage=dna.particle_usage.copy(),
            emoji_style=dna.emoji_style,
            paragraph_structure=dna.paragraph_structure,
            pause_pattern=dna.pause_pattern.copy(),
            self_reference=dna.self_reference,
            honorific_level=dna.honorific_level,
        )

        # 情感调整
        if mood == "shy":
            adjusted.ellipsis_frequency = min(0.8, adjusted.ellipsis_frequency + 0.3)
            adjusted.particle_usage["呢"] = adjusted.particle_usage.get("呢", 0) + 0.2
        elif mood == "excited":
            adjusted.sentence_length_avg *= 0.7  # 短句
            adjusted.particle_usage["呀"] = adjusted.particle_usage.get("呀", 0) + 0.3
        elif mood == "sad":
            adjusted.pause_pattern = [
                p * 1.5 for p in adjusted.pause_pattern
            ]  # 更长停顿
            adjusted.ellipsis_frequency = min(0.7, adjusted.ellipsis_frequency + 0.2)

        return adjusted

    def _apply_dna(self, content: str, dna: LanguageDNA) -> str:
        """应用DNA特征"""
        # 添加语气词
        particles = list(dna.particle_usage.keys())
        weights = list(dna.particle_usage.values())

        if particles and random.random() < 0.5:
            particle = random.choices(particles, weights=weights)[0]
            content = content.rstrip("。！？") + particle + "。"

        # 添加省略号（根据频率）
        if random.random() < dna.ellipsis_frequency:
            content = content.replace("。", "…", 1)

        return content


class DocumentTypeRouter:
    """文档类型路由器"""

    def __init__(self):
        self.generator = AdaptiveLanguageGenerator()

    def route_and_generate(self, raw_input: str, context: Dict) -> Dict:
        """根据上下文路由到合适的文档类型"""
        # 检测文档类型
        doc_type = self._detect_document_type(context)

        # 生成自适应文本
        result = self.generator.generate_adaptive_text(
            raw_input, doc_type, context.get("emotional_state")
        )

        return result

    def _detect_document_type(self, context: Dict) -> DocumentType:
        """检测文档类型"""
        channel = context.get("channel", "")
        has_subject = context.get("has_subject", False)
        is_long_form = context.get("is_long_form", False)

        if has_subject and is_long_form:
            return DocumentType.EMAIL
        elif channel == "diary":
            return DocumentType.DIARY
        elif channel == "letter":
            return DocumentType.LETTER
        elif is_long_form and not has_subject:
            return DocumentType.NOTE
        else:
            return DocumentType.CHAT
