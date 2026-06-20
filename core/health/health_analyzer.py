"""
🌸 若曦V2 健康分析AI
基于健康数据的智能分析和建议生成
"""
import os
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from core.config_manager import config
from core.log_manager import get_logger
from core.ai.model_manager import ai_manager

logger = get_logger(__name__)


class HealthMetricType(Enum):
    """健康指标类型"""
    BLOOD_PRESSURE = "blood_pressure"      # 血压
    BLOOD_GLUCOSE = "blood_glucose"        # 血糖
    HEART_RATE = "heart_rate"              # 心率
    WEIGHT = "weight"                      # 体重
    BMI = "bmi"                            # BMI
    SLEEP = "sleep"                        # 睡眠
    STEPS = "steps"                        # 步数
    TEMPERATURE = "temperature"            # 体温
    CHOLESTEROL = "cholesterol"            # 胆固醇
    URIC_ACID = "uric_acid"                # 尿酸


@dataclass
class HealthMetric:
    """健康指标数据点"""
    metric_type: str                       # 指标类型
    value: float                           # 数值
    unit: str                              # 单位
    timestamp: datetime                    # 记录时间
    source: str = "manual"                 # 数据来源
    notes: Optional[str] = None            # 备注
    systolic: Optional[float] = None       # 收缩压 (血压专用)
    diastolic: Optional[float] = None      # 舒张压 (血压专用)


@dataclass
class HealthAnalysisResult:
    """健康分析结果"""
    metric_type: str
    current_status: str                    # 当前状态 (正常/偏高/偏低/异常)
    trend: str                             # 趋势 (上升/下降/稳定)
    risk_level: str                        # 风险等级 (低/中/高)
    suggestions: List[str]                 # 医生建议
    abnormal_flags: List[str]              # 异常标记
    summary: str                           # 友好的总结


class HealthAnalyzer:
    """
    健康数据智能分析器
    
    功能:
    - 指标趋势分析
    - 异常检测
    - 风险评估
    - AI建议生成
    - 健康摘要
    """
    
    # 健康指标标准范围 (参考中国临床指南)
    HEALTH_RANGES = {
        "blood_pressure": {
            "normal": {"systolic": (90, 120), "diastolic": (60, 80)},
            "elevated": {"systolic": (120, 139), "diastolic": (80, 89)},
            "high": {"systolic": (140, float('inf')), "diastolic": (90, float('inf'))},
            "unit": "mmHg"
        },
        "blood_glucose": {
            "fasting": {"normal": (3.9, 6.1), "prediabetes": (6.1, 7.0), "diabetes": (7.0, float('inf'))},
            "postprandial": {"normal": (3.9, 7.8), "prediabetes": (7.8, 11.1), "diabetes": (11.1, float('inf'))},
            "unit": "mmol/L"
        },
        "heart_rate": {
            "normal": (60, 100),
            "bradycardia": (0, 60),
            "tachycardia": (100, float('inf')),
            "unit": "bpm"
        },
        "bmi": {
            "underweight": (0, 18.5),
            "normal": (18.5, 24),
            "overweight": (24, 28),
            "obese": (28, float('inf'))
        },
        "sleep_duration": {
            "insufficient": (0, 6),
            "normal": (6, 9),
            "excessive": (9, float('inf')),
            "unit": "hours"
        }
    }
    
    def __init__(self):
        self.ai_manager = ai_manager
        self.cache: Dict[str, Any] = {}
        logger.info("💜 健康分析器初始化完成")
    
    def analyze_blood_pressure(
        self,
        records: List[HealthMetric]
    ) -> HealthAnalysisResult:
        """
        分析血压数据
        
        Returns:
            血压分析报告
        """
        if not records:
            return HealthAnalysisResult(
                metric_type="blood_pressure",
                current_status="无数据",
                trend="未知",
                risk_level="未知",
                suggestions=["开始记录血压数据~"],
                abnormal_flags=[],
                summary="还没有记录血压数据呢，建议开始监测哦。"
            )
        
        # 获取最新记录
        latest = records[-1]
        
        # 分类
        ranges = self.HEALTH_RANGES["blood_pressure"]
        sys_val = latest.systolic
        dia_val = latest.diastolic
        
        # 确定状态
        if sys_val and dia_val:
            if (ranges["normal"]["systolic"][0] <= sys_val <= ranges["normal"]["systolic"][1] and
                ranges["normal"]["diastolic"][0] <= dia_val <= ranges["normal"]["diastolic"][1]):
                status = "正常"
                risk = "低"
                summary = f"血压在正常范围 ({sys_val}/{dia_val} mmHg)，继续保持！"
            elif (ranges["elevated"]["systolic"][0] <= sys_val <= ranges["elevated"]["systolic"][1] or
                  ranges["elevated"]["diastolic"][0] <= dia_val <= ranges["elevated"]["diastolic"][1]):
                status = "正常高值"
                risk = "中"
                summary = f"血压在正常高值 ({sys_val}/{dia_val} mmHg)，注意监测。"
            else:
                status = "偏高"
                risk = "高"
                summary = f"血压偏高 ({sys_val}/{dia_val} mmHg)，建议就医检查。"
        else:
            status = "数据不完整"
            risk = "未知"
            summary = "血压数据不完整。"
        
        # 分析趋势
        trend = self._analyze_trend([r.systolic for r in records if r.systolic])
        
        # 异常标记
        abnormal = []
        if sys_val and sys_val > 140:
            abnormal.append("收缩压偏高")
        if sys_val and sys_val < 90:
            abnormal.append("收缩压偏低")
        if dia_val and dia_val > 90:
            abnormal.append("舒张压偏高")
        if dia_val and dia_val < 60:
            abnormal.append("舒张压偏低")
        
        # 建议
        suggestions = self._generate_bp_suggestions(status, trend)
        
        return HealthAnalysisResult(
            metric_type="blood_pressure",
            current_status=status,
            trend=trend,
            risk_level=risk,
            suggestions=suggestions,
            abnormal_flags=abnormal,
            summary=summary
        )
    
    def analyze_blood_glucose(
        self,
        records: List[HealthMetric],
        test_type: str = "fasting"
    ) -> HealthAnalysisResult:
        """分析血糖数据"""
        if not records:
            return self._empty_result("blood_glucose", "血糖")
        
        latest = records[-1]
        val = latest.value
        ranges = self.HEALTH_RANGES["blood_glucose"][test_type]
        
        if ranges["normal"][0] <= val <= ranges["normal"][1]:
            status = "正常"
            risk = "低"
        elif ranges["prediabetes"][0] <= val <= ranges["prediabetes"][1]:
            status = "空腹血糖受损" if test_type == "fasting" else "糖耐量异常"
            risk = "中"
        else:
            status = "偏高"
            risk = "高"
        
        trend = self._analyze_trend([r.value for r in records])
        abnormal = ["血糖偏高"] if val > ranges["normal"][1] else []
        
        suggestions = [
            "控制碳水化合物摄入",
            "定期监测血糖",
            "适量运动"
        ] if risk != "低" else ["保持当前饮食习惯"]
        
        return HealthAnalysisResult(
            metric_type="blood_glucose",
            current_status=status,
            trend=trend,
            risk_level=risk,
            suggestions=suggestions,
            abnormal_flags=abnormal,
            summary=f"血糖{status} ({val} mmol/L)，趋势{trend}。"
        )
    
    def analyze_sleep(
        self,
        records: List[HealthMetric]
    ) -> HealthAnalysisResult:
        """分析睡眠数据"""
        if not records:
            return self._empty_result("sleep", "睡眠")
        
        # 计算平均时长
        durations = [r.value for r in records]
        avg_duration = sum(durations) / len(durations)
        ranges = self.HEALTH_RANGES["sleep_duration"]
        
        if ranges["normal"][0] <= avg_duration <= ranges["normal"][1]:
            status = "正常"
            risk = "低"
            summary = f"平均睡眠{avg_duration:.1f}小时，很棒！"
        elif avg_duration < ranges["normal"][0]:
            status = "不足"
            risk = "中"
            summary = f"平均睡眠{avg_duration:.1f}小时，有点少呢~"
        else:
            status = "过多"
            risk = "中"
            summary = f"平均睡眠{avg_duration:.1f}小时，注意休息适度。"
        
        trend = self._analyze_trend(durations[-7:] if len(durations) >= 7 else durations)
        
        suggestions = []
        if avg_duration < 6:
            suggestions.extend([
                "尽量在23点前入睡",
                "睡前1小时不看手机",
                "创造舒适的睡眠环境"
            ])
        else:
            suggestions.append("保持良好的睡眠习惯")
        
        return HealthAnalysisResult(
            metric_type="sleep",
            current_status=status,
            trend=trend,
            risk_level=risk,
            suggestions=suggestions,
            abnormal_flags=["睡眠不足"] if avg_duration < 6 else [],
            summary=summary
        )
    
    async def generate_health_report(
        self,
        user_id: str,
        health_records: Dict[str, List[HealthMetric]]
    ) -> str:
        """
        生成综合健康报告 (AI驱动)
        
        Args:
            user_id: 用户ID
            health_records: 各类健康记录
        
        Returns:
            友好的健康报告
        """
        # 1. 各指标分析
        analyses = []
        
        if "blood_pressure" in health_records:
            analyses.append(self.analyze_blood_pressure(health_records["blood_pressure"]))
        
        if "blood_glucose" in health_records:
            analyses.append(self.analyze_blood_glucose(health_records["blood_glucose"]))
        
        if "sleep" in health_records:
            analyses.append(self.analyze_sleep(health_records["sleep"]))
        
        # 2. 构建AI提示词
        prompt_data = {
            "user_id": user_id,
            "analyses": [
                {
                    "type": a.metric_type,
                    "status": a.current_status,
                    "risk": a.risk_level,
                    "summary": a.summary
                }
                for a in analyses
            ],
            "high_risk": [
                a.metric_type for a in analyses if a.risk_level == "高"
            ]
        }
        
        system_prompt = """你是若曦，一个温柔的AI健康助理。
请根据健康数据生成一份温暖、易懂的健康报告。
要求:
1. 语气温柔、体贴，像朋友聊天
2. 突出需要注意的问题
3. 给出具体、可操作的建议
4. 适当使用emoji
5. 不要制造焦虑，但要提醒就医
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请为以下用户生成健康报告:\n{json.dumps(prompt_data, ensure_ascii=False, indent=2)}"}
        ]
        
        # 3. 调用AI生成报告
        try:
            response = await self.ai_manager.generate(messages, use_cache=False)
            return response.content
        except Exception as e:
            logger.error(f"🔴 健康报告生成失败: {e}")
            return "生成报告时出错，请稍后再试~ 🌸"
    
    async def answer_health_question(
        self,
        question: str,
        user_health_data: Dict
    ) -> str:
        """
        回答健康问题 (结合用户数据)
        
        Args:
            question: 用户问题
            user_health_data: 用户的健康数据
        
        Returns:
            个性化健康建议
        """
        system_prompt = """你是若曦，一个懂医学的AI助手。
重要提示:
1. 你不是真正的医生，只能提供一般性健康信息
2. 涉及诊断必须建议就医
3. 回答要专业但易懂
4. 结合用户的具体数据给出建议
5. 不确定时坦诚说"不太确定，建议咨询医生"
"""
        
        context = f"用户健康问题: {question}\n\n用户健康数据:\n{json.dumps(user_health_data, ensure_ascii=False)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
        
        try:
            response = await self.ai_manager.generate(messages)
            return response.content
        except Exception as e:
            logger.error(f"🔴 健康问题回答失败: {e}")
            return "这个问题有点复杂，建议咨询专业医生哦~ 💜"
    
    def _analyze_trend(self, values: List[float]) -> str:
        """分析数值趋势"""
        if len(values) < 3:
            return "数据不足"
        
        # 简单线性趋势
        recent = sum(values[-3:]) / 3
        older = sum(values[:3]) / 3 if len(values) >= 6 else recent
        
        diff = recent - older
        threshold = abs(older) * 0.05  # 5%变化视为有意义
        
        if abs(diff) < threshold:
            return "稳定"
        elif diff > 0:
            return "上升"
        else:
            return "下降"
    
    def _generate_bp_suggestions(self, status: str, trend: str) -> List[str]:
        """生成血压建议"""
        suggestions = []
        
        if status in ["偏高", "正常高值"]:
            suggestions.extend([
                "减少盐摄入，每天不超过6克",
                "多吃蔬菜水果",
                "每周运动150分钟以上"
            ])
        
        if trend == "上升":
            suggestions.append("血压有上升趋势，建议更频繁监测")
        
        if not suggestions:
            suggestions.append("保持当前健康习惯，定期监测")
        
        return suggestions
    
    def _empty_result(self, metric_type: str, name: str) -> HealthAnalysisResult:
        """生成空数据结果"""
        return HealthAnalysisResult(
            metric_type=metric_type,
            current_status="无数据",
            trend="未知",
            risk_level="未知",
            suggestions=[f"开始记录{name}数据吧~"],
            abnormal_flags=[],
            summary=f"还没有{name}数据，建议开始记录哦。"
        )


# 全局健康分析器实例
health_analyzer = HealthAnalyzer()


if __name__ == "__main__":
    print("=" * 60)
    print("🌸 若曦V2 健康分析器")
    print("=" * 60)
    
    print("\n【功能】")
    print("  - 血压/血糖/睡眠分析")
    print("  - 趋势检测")
    print("  - 风险评估")
    print("  - AI报告生成")
    
    print("\n【测试】")
    
    # 测试血压分析
    bp_records = [
        HealthMetric("blood_pressure", 0, "mmHg", datetime.now(), systolic=125, diastolic=82),
        HealthMetric("blood_pressure", 0, "mmHg", datetime.now(), systolic=128, diastolic=85),
        HealthMetric("blood_pressure", 0, "mmHg", datetime.now(), systolic=118, diastolic=78),
    ]
    
    result = health_analyzer.analyze_blood_pressure(bp_records)
    print(f"\n血压分析:")
    print(f"  状态: {result.current_status}")
    print(f"  风险: {result.risk_level}")
    print(f"  建议: {result.suggestions}")
    print(f"  摘要: {result.summary}")
    
    # 统计
    print(f"\n统计: {health_analyzer.HEALTH_RANGES.keys()}")
    
    print("\n" + "=" * 60)
    print("✅ 健康分析器就绪")
    print("=" * 60)
