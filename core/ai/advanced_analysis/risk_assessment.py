"""
🌸 若曦V2 - 疾病风险评估系统
基于健康数据评估患病风险
使用医学模型和风险因子计算
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
from typing import Any, Dict, List, Optional

from models.database import (
    BloodPressureRecord,
    GlucoseRecord,
    HeartRateRecord,
    User,
    WeightRecord,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    """风险因子"""

    name: str
    value: float
    weight: float  # 权重 (0-1)
    contribution: float  # 对总风险的贡献


@dataclass
class DiseaseRisk:
    """疾病风险评估结果"""

    disease_name: str
    risk_score: float  # 0-100
    risk_level: str  # low/medium/high/very_high
    contributing_factors: List[RiskFactor]
    protective_factors: List[str]
    recommendations: List[str]
    screening_recommendations: List[str]
    last_updated: str


class DiseaseRiskAssessor:
    """
    疾病风险评估器

    评估以下疾病风险:
    - 高血压并发症
    - 2型糖尿病
    - 心血管疾病
    - 代谢综合征
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.user = self._get_user()

    def _get_user(self) -> Optional[User]:
        """获取用户信息"""
        return self.db.query(User).filter(User.id == self.user_id).first()

    def assess_all_risks(self) -> Dict[str, Any]:
        """评估所有疾病风险"""
        if not self.user:
            return {"error": "用户不存在"}

        risks = []

        # 评估各种疾病风险
        hypertension_risk = self._assess_hypertension_risk()
        if hypertension_risk:
            risks.append(hypertension_risk.__dict__)

        diabetes_risk = self._assess_diabetes_risk()
        if diabetes_risk:
            risks.append(diabetes_risk.__dict__)

        cvd_risk = self._assess_cardiovascular_risk()
        if cvd_risk:
            risks.append(cvd_risk.__dict__)

        metabolic_risk = self._assess_metabolic_syndrome()
        if metabolic_risk:
            risks.append(metabolic_risk.__dict__)

        return {
            "overall_risk_score": self._calculate_overall_risk(risks),
            "risks": risks,
            "assessed_at": datetime.utcnow().isoformat(),
            "user_id": self.user_id,
        }

    def _assess_hypertension_risk(self) -> Optional[DiseaseRisk]:
        """评估高血压风险"""
        # 获取最近血压记录
        records = (
            self.db.query(BloodPressureRecord)
            .filter(
                BloodPressureRecord.user_id == self.user_id,
                BloodPressureRecord.measured_at
                >= datetime.utcnow() - timedelta(days=30),
            )
            .all()
        )

        if not records:
            return None

        factors = []
        protective = []
        recommendations = []
        screening = []

        # 计算平均血压
        avg_systolic = mean([r.systolic for r in records])
        avg_diastolic = mean([r.diastolic for r in records])

        # 血压因子
        if avg_systolic > 140 or avg_diastolic > 90:
            bp_contrib = min(40, ((avg_systolic - 120) / 120 * 30))
            factors.append(
                RiskFactor(
                    name="高血压",
                    value=avg_systolic,
                    weight=0.4,
                    contribution=bp_contrib,
                )
            )
            recommendations.append("严格监测血压，遵医嘱用药")
            screening.append("每月检查血压")
        elif avg_systolic > 120:
            factors.append(
                RiskFactor(
                    name="血压偏高", value=avg_systolic, weight=0.3, contribution=15
                )
            )
            recommendations.append("调整饮食，减少盐摄入")
            screening.append("每两周检查血压")
        else:
            protective.append("血压控制良好")
            screening.append("每季度检查血压")

        # 年龄因子
        if self.user.age:
            if self.user.age > 55:
                factors.append(
                    RiskFactor(
                        name="年龄", value=self.user.age, weight=0.2, contribution=15
                    )
                )
            elif self.user.age > 40:
                factors.append(
                    RiskFactor(
                        name="年龄", value=self.user.age, weight=0.15, contribution=10
                    )
                )

        # BMI因子
        bmi = self._calculate_bmi()
        if bmi and bmi > 25:
            factors.append(
                RiskFactor(
                    name="超重/肥胖",
                    value=bmi,
                    weight=0.25,
                    contribution=min(20, (bmi - 25) * 3),
                )
            )
            recommendations.append("控制体重，目标BMI < 25")

        # 计算总风险
        total_risk = sum(f.contribution for f in factors)
        risk_level = self._risk_level(total_risk)

        if not recommendations:
            recommendations.append("保持目前健康生活方式")
            recommendations.append("定期监测血压")

        return DiseaseRisk(
            disease_name="高血压并发症",
            risk_score=min(100, total_risk),
            risk_level=risk_level,
            contributing_factors=factors,
            protective_factors=protective,
            recommendations=recommendations,
            screening_recommendations=screening,
            last_updated=datetime.utcnow().isoformat(),
        )

    def _assess_diabetes_risk(self) -> Optional[DiseaseRisk]:
        """评估糖尿病风险 (基于中国糖尿病风险评分)"""
        # 获取血糖记录
        records = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == self.user_id,
                GlucoseRecord.measured_at >= datetime.utcnow() - timedelta(days=60),
            )
            .all()
        )

        factors = []
        protective = []
        recommendations = []
        screening = []

        score = 0

        # 年龄评分
        if self.user.age:
            if self.user.age >= 60:
                score += 8
                factors.append(RiskFactor("年龄≥60", self.user.age, 0.15, 8))
            elif self.user.age >= 50:
                score += 5
                factors.append(RiskFactor("年龄50-59", self.user.age, 0.1, 5))
            elif self.user.age >= 40:
                score += 3
                factors.append(RiskFactor("年龄40-49", self.user.age, 0.08, 3))

        # BMI评分
        bmi = self._calculate_bmi()
        if bmi:
            if bmi >= 30:
                score += 6
                factors.append(RiskFactor("BMI≥30", bmi, 0.2, 6))
            elif bmi >= 25:
                score += 4
                factors.append(RiskFactor("BMI 25-29.9", bmi, 0.15, 4))
            elif bmi < 24:
                protective.append("体重正常")

        # 血糖评分
        if records:
            fasting_records = [r for r in records if r.meal_type == "fasting"]
            if fasting_records:
                avg_fasting = mean([r.value for r in fasting_records[-5:]])
                if avg_fasting > 7.0:
                    score += 10
                    factors.append(RiskFactor("空腹血糖异常", avg_fasting, 0.3, 10))
                    recommendations.append("建议复查糖化血红蛋白")
                    screening.append("每月检查空腹血糖")
                elif avg_fasting > 6.1:
                    score += 5
                    factors.append(RiskFactor("空腹血糖偏高", avg_fasting, 0.2, 5))

        # 血压对糖尿病的影响
        bp_records = (
            self.db.query(BloodPressureRecord)
            .filter(BloodPressureRecord.user_id == self.user_id)
            .all()
        )
        if bp_records:
            avg_systolic = mean([r.systolic for r in bp_records[-10:]])
            if avg_systolic > 140:
                score += 4
                factors.append(RiskFactor("高血压", avg_systolic, 0.15, 4))

        # 转换为百分制风险
        # 中国糖尿病风险评分: <25低风险, 25-35中风险, >=35高风险
        risk_score = min(100, score * 2.5)
        risk_level = "low" if score < 25 else "medium" if score < 35 else "high"

        if not recommendations:
            recommendations.append("保持健康体重")
            recommendations.append("增加体力活动")
            recommendations.append("控制总热量摄入")

        screening.append("每年检查空腹血糖和糖化血红蛋白")

        return DiseaseRisk(
            disease_name="2型糖尿病",
            risk_score=risk_score,
            risk_level=risk_level,
            contributing_factors=factors,
            protective_factors=protective,
            recommendations=recommendations,
            screening_recommendations=screening,
            last_updated=datetime.utcnow().isoformat(),
        )

    def _assess_cardiovascular_risk(self) -> Optional[DiseaseRisk]:
        """评估心血管疾病风险"""
        factors = []
        protective = []
        recommendations = []
        screening = []

        score = 0

        # 年龄 (男性>55, 女性>65为风险)
        if self.user.age:
            if self.user.age > 60:
                score += 15
                factors.append(RiskFactor("年龄", self.user.age, 0.2, 15))

        # 血压
        bp_records = (
            self.db.query(BloodPressureRecord)
            .filter(BloodPressureRecord.user_id == self.user_id)
            .all()
        )
        if bp_records:
            avg_systolic = mean([r.systolic for r in bp_records[-10:]])
            if avg_systolic > 160:
                score += 20
                factors.append(RiskFactor("高血压", avg_systolic, 0.25, 20))
            elif avg_systolic > 140:
                score += 10
                factors.append(RiskFactor("血压偏高", avg_systolic, 0.2, 10))
            else:
                protective.append("血压控制良好")

        # BMI
        bmi = self._calculate_bmi()
        if bmi and bmi > 30:
            score += 10
            factors.append(RiskFactor("肥胖", bmi, 0.15, 10))
        elif bmi and bmi > 25:
            score += 5
            factors.append(RiskFactor("超重", bmi, 0.1, 5))

        # 心率
        hr_records = (
            self.db.query(HeartRateRecord)
            .filter(
                HeartRateRecord.user_id == self.user_id,
                HeartRateRecord.activity == "resting",
            )
            .all()
        )
        if hr_records:
            avg_hr = mean([r.bpm for r in hr_records[-10:]])
            if avg_hr > 90:
                score += 5
                factors.append(RiskFactor("静息心率偏快", avg_hr, 0.1, 5))

        risk_score = min(100, score)
        risk_level = self._risk_level(risk_score)

        recommendations.append("戒烟限酒")
        recommendations.append("每周至少150分钟中等强度运动")
        recommendations.append("地中海饮食模式")

        screening.append("每年检查血脂四项")
        screening.append("每年心电图检查")

        return DiseaseRisk(
            disease_name="心血管疾病",
            risk_score=risk_score,
            risk_level=risk_level,
            contributing_factors=factors,
            protective_factors=protective,
            recommendations=recommendations,
            screening_recommendations=screening,
            last_updated=datetime.utcnow().isoformat(),
        )

    def _assess_metabolic_syndrome(self) -> Optional[DiseaseRisk]:
        """评估代谢综合征风险"""
        # 代谢综合征诊断标准 (满足3项以上)
        components_met = 0
        factors = []
        recommendations = []

        # 1. 血压 >= 130/85
        bp_records = (
            self.db.query(BloodPressureRecord)
            .filter(BloodPressureRecord.user_id == self.user_id)
            .all()
        )
        if bp_records:
            avg_systolic = mean([r.systolic for r in bp_records[-5:]])
            avg_diastolic = mean([r.diastolic for r in bp_records[-5:]])
            if avg_systolic >= 130 or avg_diastolic >= 85:
                components_met += 1
                factors.append(RiskFactor("血压升高", avg_systolic, 0.2, 20))

        # 2. 空腹血糖 >= 6.1
        glucose_records = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == self.user_id,
                GlucoseRecord.meal_type == "fasting",
            )
            .all()
        )
        if glucose_records:
            avg_glucose = mean([r.value for r in glucose_records[-5:]])
            if avg_glucose >= 6.1:
                components_met += 1
                factors.append(RiskFactor("血糖升高", avg_glucose, 0.2, 20))

        # 3. 超重/肥胖 (BMI > 25)
        bmi = self._calculate_bmi()
        if bmi and bmi > 25:
            components_met += 1
            factors.append(RiskFactor("超重/肥胖", bmi, 0.2, 20))

        # 风险等级
        if components_met >= 3:
            score = 80
            level = "very_high"
            recommendations.append("强烈建议就医，进行全面评估和治疗")
        elif components_met == 2:
            score = 60
            level = "high"
            recommendations.append("已具备代谢综合征前期特征，建议干预")
        elif components_met == 1:
            score = 40
            level = "medium"
            recommendations.append("注意生活方式调整，防止发展为代谢综合征")
        else:
            score = 20
            level = "low"
            recommendations.append("保持目前健康状态")

        recommendations.append("减重5-10%可显著改善代谢指标")
        recommendations.append("增加有氧运动")

        return DiseaseRisk(
            disease_name="代谢综合征",
            risk_score=score,
            risk_level=level,
            contributing_factors=factors,
            protective_factors=[],
            recommendations=recommendations,
            screening_recommendations=["每季度评估代谢指标"],
            last_updated=datetime.utcnow().isoformat(),
        )

    def _calculate_bmi(self) -> Optional[float]:
        """计算BMI"""
        if not self.user or not self.user.height_cm or not self.user.weight_kg:
            return None

        height_m = self.user.height_cm / 100
        return round(self.user.weight_kg / (height_m**2), 2)

    def _risk_level(self, score: float) -> str:
        """根据分数确定风险等级"""
        if score < 25:
            return "low"
        elif score < 50:
            return "medium"
        elif score < 75:
            return "high"
        return "very_high"

    def _calculate_overall_risk(self, risks: List[Dict]) -> Dict[str, Any]:
        """计算综合风险"""
        if not risks:
            return {"score": 0, "level": "unknown"}

        avg_score = sum(r.get("risk_score", 0) for r in risks) / len(risks)

        # 找出最高风险
        max_risk = max(risks, key=lambda x: x.get("risk_score", 0))

        return {
            "average_score": round(avg_score, 1),
            "highest_risk_disease": max_risk.get("disease_name"),
            "highest_risk_score": max_risk.get("risk_score"),
            "risk_level": self._risk_level(avg_score),
        }


# 便捷函数
def assess_user_disease_risks(db: Session, user_id: int) -> Dict[str, Any]:
    """评估用户疾病风险便捷函数"""
    assessor = DiseaseRiskAssessor(db, user_id)
    return assessor.assess_all_risks()
