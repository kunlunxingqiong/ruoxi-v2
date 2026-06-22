"""
🌸 若曦V2 - PDF健康报告生成服务
生成专业级健康报告PDF文档
"""

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from models.database import (
    BloodPressureRecord,
    GlucoseRecord,
    Goal,
    HealthTimeline,
    HeartRateRecord,
    Medication,
    MedicationLog,
    SleepRecord,
)
from models.database import User as UserModel
from models.database import (
    WeightRecord,
)
from sqlalchemy.orm import Session

from core.services.health_service import HealthService

logger = logging.getLogger(__name__)


@dataclass
class ReportPeriod:
    """报告周期"""

    start_date: date
    end_date: date

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    @property
    def label(self) -> str:
        if self.days == 1:
            return "日报"
        elif self.days == 7:
            return "周报"
        elif self.days == 30:
            return "月报"
        elif self.days == 90:
            return "季报"
        elif self.days == 365:
            return "年报"
        return f"{self.days}天报告"


class PDFReportService:
    """
    PDF健康报告生成服务

    生成专业级健康报告，支持：
    - 多时间维度报告（日/周/月/季/年）
    - 综合健康评分
    - 各项指标趋势分析
    - 用药依从性统计
    - 目标完成情况
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.user = self._get_user()
        self.health_service = HealthService(db)

    def _get_user(self) -> Optional[UserModel]:
        """获取用户信息"""
        return self.db.query(UserModel).filter(UserModel.id == self.user_id).first()

    def generate_health_report(
        self,
        period: ReportPeriod,
        report_type: str = "comprehensive",
        include_charts: bool = True,
    ) -> Dict[str, Any]:
        """
        生成健康报告

        Args:
            period: 报告周期
            report_type: 报告类型 (comprehensive/summary/medical)
            include_charts: 是否包含图表

        Returns:
            报告数据和元信息
        """
        logger.info(f"生成{period.label}健康报告: 用户{self.user_id}")

        report = {
            "meta": self._generate_report_meta(period, report_type),
            "user_summary": self._generate_user_summary(),
            "health_overview": self._generate_health_overview(period),
            "blood_pressure": self._generate_bp_section(period),
            "glucose": self._generate_glucose_section(period),
            "weight": self._generate_weight_section(period),
            "sleep": self._generate_sleep_section(period),
            "heart_rate": self._generate_hr_section(period),
            "medication": self._generate_medication_section(period),
            "goals": self._generate_goals_section(period),
            "recommendations": self._generate_recommendations(period),
        }

        return report

    def _generate_report_meta(
        self, period: ReportPeriod, report_type: str
    ) -> Dict[str, Any]:
        """生成报告元信息"""
        return {
            "title": f"若曦健康报告 - {period.label}",
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": report_type,
            "period": {
                "start": period.start_date.isoformat(),
                "end": period.end_date.isoformat(),
                "days": period.days,
                "label": period.label,
            },
            "report_id": f"RH-{self.user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "version": "2.0",
        }

    def _generate_user_summary(self) -> Dict[str, Any]:
        """生成用户摘要"""
        if not self.user:
            return {"error": "用户不存在"}

        user_data = {
            "user_id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "display_name": self.user.display_name or self.user.username,
            "age": self.user.age,
            "gender": self.user.gender,
            "height_cm": self.user.height_cm,
            "weight_kg": self.user.weight_kg,
            "bmi": None,
            "health_conditions": self.user.health_conditions or [],
            "allergies": self.user.allergies or [],
            "emergency_contact": self.user.emergency_contact,
        }

        # 计算BMI
        if self.user.height_cm and self.user.weight_kg:
            height_m = self.user.height_cm / 100
            user_data["bmi"] = round(self.user.weight_kg / (height_m**2), 1)

        return user_data

    def _generate_health_overview(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成健康概览"""
        # 计算各项数据点数量
        bp_count = (
            self.db.query(BloodPressureRecord)
            .filter(
                BloodPressureRecord.user_id == self.user_id,
                BloodPressureRecord.measured_at >= period.start_date,
                BloodPressureRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .count()
        )

        glucose_count = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == self.user_id,
                GlucoseRecord.measured_at >= period.start_date,
                GlucoseRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .count()
        )

        weight_count = (
            self.db.query(WeightRecord)
            .filter(
                WeightRecord.user_id == self.user_id,
                WeightRecord.measured_at >= period.start_date,
                WeightRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .count()
        )

        sleep_count = (
            self.db.query(SleepRecord)
            .filter(
                SleepRecord.user_id == self.user_id,
                SleepRecord.bed_time >= period.start_date,
                SleepRecord.bed_time < period.end_date + timedelta(days=1),
            )
            .count()
        )

        hr_count = (
            self.db.query(HeartRateRecord)
            .filter(
                HeartRateRecord.user_id == self.user_id,
                HeartRateRecord.measured_at >= period.start_date,
                HeartRateRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .count()
        )

        # 计算综合健康评分
        health_score = self._calculate_overall_score(period)

        return {
            "data_summary": {
                "blood_pressure_records": bp_count,
                "glucose_records": glucose_count,
                "weight_records": weight_count,
                "sleep_records": sleep_count,
                "heart_rate_records": hr_count,
                "total_data_points": bp_count
                + glucose_count
                + weight_count
                + sleep_count
                + hr_count,
            },
            "health_score": health_score,
            "health_trend": self._determine_trend(period),
            "last_sync": datetime.utcnow().isoformat(),
        }

    def _calculate_overall_score(self, period: ReportPeriod) -> Dict[str, Any]:
        """计算综合健康评分 (0-100)"""
        scores = {}
        weights = {}

        # 血压评分
        bp_score = self._calculate_bp_score(period)
        if bp_score is not None:
            scores["blood_pressure"] = bp_score
            weights["blood_pressure"] = 0.25

        # 血糖评分
        glucose_score = self._calculate_glucose_score(period)
        if glucose_score is not None:
            scores["glucose"] = glucose_score
            weights["glucose"] = 0.25

        # 体重评分
        weight_score = self._calculate_weight_score(period)
        if weight_score is not None:
            scores["weight"] = weight_score
            weights["weight"] = 0.20

        # 睡眠评分
        sleep_score = self._calculate_sleep_score(period)
        if sleep_score is not None:
            scores["sleep"] = sleep_score
            weights["sleep"] = 0.15

        # 心率评分
        hr_score = self._calculate_hr_score(period)
        if hr_score is not None:
            scores["heart_rate"] = hr_score
            weights["heart_rate"] = 0.15

        # 加权计算总分
        total_weight = sum(weights.values())
        if total_weight == 0:
            overall_score = None
        else:
            overall_score = sum(
                scores[key] * weights[key] / total_weight for key in scores
            )

        return {
            "overall": round(overall_score) if overall_score else None,
            "details": scores,
            "interpretation": self._interpret_score(overall_score),
        }

    def _interpret_score(self, score: Optional[float]) -> str:
        """解读健康评分"""
        if score is None:
            return "数据不足，无法评估"
        elif score >= 90:
            return "优秀 - 健康状况良好"
        elif score >= 80:
            return "良好 - 整体健康，注意细节"
        elif score >= 70:
            return "一般 - 需要关注某些指标"
        elif score >= 60:
            return "需改善 - 建议调整生活方式"
        else:
            return "重点关注 - 建议尽快就医"

    def _calculate_bp_score(self, period: ReportPeriod) -> Optional[float]:
        """计算血压健康评分"""
        records = (
            self.db.query(BloodPressureRecord)
            .filter(
                BloodPressureRecord.user_id == self.user_id,
                BloodPressureRecord.measured_at >= period.start_date,
                BloodPressureRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not records:
            return None

        # 根据血压分类统计
        normal_count = sum(1 for r in records if r.category == "normal")
        total = len(records)

        # 基础分
        score = (normal_count / total) * 100

        # 扣分项
        for r in records:
            if r.category == "crisis":
                score -= 30
            elif r.category == "stage2":
                score -= 15
            elif r.category == "stage1":
                score -= 5

        return max(0, min(100, score))

    def _calculate_glucose_score(self, period: ReportPeriod) -> Optional[float]:
        """计算血糖健康评分"""
        records = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == self.user_id,
                GlucoseRecord.measured_at >= period.start_date,
                GlucoseRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not records:
            return None

        normal_count = sum(1 for r in records if r.is_normal)
        total = len(records)

        return (normal_count / total) * 100

    def _calculate_weight_score(self, period: ReportPeriod) -> Optional[float]:
        """计算体重健康评分"""
        if not self.user or not self.user.height_cm:
            return None

        records = (
            self.db.query(WeightRecord)
            .filter(
                WeightRecord.user_id == self.user_id,
                WeightRecord.measured_at >= period.start_date,
                WeightRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .order_by(WeightRecord.measured_at.desc())
            .all()
        )

        if not records:
            return None

        # 计算BMI
        height_m = self.user.height_cm / 100
        latest_bmi = records[0].weight_kg / (height_m**2)

        # BMI评分 (18.5-24为最佳)
        if 18.5 <= latest_bmi <= 24:
            return 100
        elif 24 < latest_bmi <= 28:
            return 80 - (latest_bmi - 24) * 10
        elif latest_bmi > 28:
            return max(0, 40 - (latest_bmi - 28) * 2)
        else:  # < 18.5
            return max(0, 80 - (18.5 - latest_bmi) * 15)

    def _calculate_sleep_score(self, period: ReportPeriod) -> Optional[float]:
        """计算睡眠健康评分"""
        records = (
            self.db.query(SleepRecord)
            .filter(
                SleepRecord.user_id == self.user_id,
                SleepRecord.bed_time >= period.start_date,
                SleepRecord.bed_time < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not records:
            return None

        # 平均睡眠时长
        avg_duration = sum(r.duration_minutes for r in records) / len(records) / 60

        # 理想睡眠7-9小时
        if 7 <= avg_duration <= 9:
            return 100
        elif avg_duration < 7:
            return max(0, 100 - (7 - avg_duration) * 20)
        else:
            return max(0, 100 - (avg_duration - 9) * 10)

    def _calculate_hr_score(self, period: ReportPeriod) -> Optional[float]:
        """计算心率健康评分"""
        records = (
            self.db.query(HeartRateRecord)
            .filter(
                HeartRateRecord.user_id == self.user_id,
                HeartRateRecord.measured_at >= period.start_date,
                HeartRateRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not records:
            return None

        # 静息心率评估
        resting_records = [r for r in records if r.activity == "resting"]
        if resting_records:
            avg_resting = sum(r.bpm for r in resting_records) / len(resting_records)
            # 理想静息心率60-80
            if 60 <= avg_resting <= 80:
                return 100
            elif avg_resting < 60:
                return max(0, 100 - (60 - avg_resting) * 3)
            else:
                return max(0, 100 - (avg_resting - 80) * 2)

        return None

    def _determine_trend(self, period: ReportPeriod) -> str:
        """确定健康趋势"""
        # 简化逻辑：与前一周/月比较
        prev_start = period.start_date - timedelta(days=period.days)
        prev_end = period.end_date - timedelta(days=period.days)

        prev_score = self._calculate_overall_score(ReportPeriod(prev_start, prev_end))
        curr_score = self._calculate_overall_score(period)

        prev_overall = prev_score.get("overall") if prev_score else None
        curr_overall = curr_score.get("overall") if curr_score else None

        if prev_overall is None or curr_overall is None:
            return "stable"

        diff = curr_overall - prev_overall
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        return "stable"

    def _generate_bp_section(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成血压章节"""
        records = (
            self.db.query(BloodPressureRecord)
            .filter(
                BloodPressureRecord.user_id == self.user_id,
                BloodPressureRecord.measured_at >= period.start_date,
                BloodPressureRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .order_by(BloodPressureRecord.measured_at)
            .all()
        )

        if not records:
            return {"status": "no_data", "message": "本周期无血压记录"}

        systolics = [r.systolic for r in records]
        diastolics = [r.diastolic for r in records]
        pulses = [r.pulse for r in records if r.pulse]

        # 分类统计
        categories = {}
        for r in records:
            cat = r.category or "unknown"
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "status": "ok",
            "statistics": {
                "total_readings": len(records),
                "avg_systolic": round(sum(systolics) / len(systolics)),
                "avg_diastolic": round(sum(diastolics) / len(diastolics)),
                "avg_pulse": round(sum(pulses) / len(pulses)) if pulses else None,
                "min_systolic": min(systolics),
                "max_systolic": max(systolics),
                "min_diastolic": min(diastolics),
                "max_diastolic": max(diastolics),
            },
            "category_distribution": categories,
            "classification_summary": self._interpret_bp_categories(categories),
        }

    def _interpret_bp_categories(self, categories: Dict[str, int]) -> str:
        """解读血压分类统计"""
        total = sum(categories.values())
        normal_pct = (categories.get("normal", 0) / total) * 100

        if normal_pct >= 90:
            return "血压控制优秀，大部分时间在正常范围"
        elif normal_pct >= 70:
            return "血压控制良好，偶有波动"
        elif normal_pct >= 50:
            return "血压控制一般，建议加强监测和管理"
        else:
            return "血压控制需改善，建议咨询医生"

    def _generate_glucose_section(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成血糖章节"""
        records = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == self.user_id,
                GlucoseRecord.measured_at >= period.start_date,
                GlucoseRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not records:
            return {"status": "no_data", "message": "本周期无血糖记录"}

        by_meal_type = {}
        for r in records:
            meal = r.meal_type or "unknown"
            if meal not in by_meal_type:
                by_meal_type[meal] = []
            by_meal_type[meal].append(r.value)

        stats_by_meal = {}
        for meal, values in by_meal_type.items():
            stats_by_meal[meal] = {
                "count": len(values),
                "avg": round(sum(values) / len(values), 1),
                "min": round(min(values), 1),
                "max": round(max(values), 1),
            }

        return {
            "status": "ok",
            "total_readings": len(records),
            "by_meal_type": stats_by_meal,
            "normal_rate": self._calculate_glucose_normal_rate(records),
        }

    def _calculate_glucose_normal_rate(self, records: List) -> Dict[str, Any]:
        """计算血糖正常率"""
        normal_count = sum(1 for r in records if r.is_normal)
        total = len(records)

        return {
            "normal_count": normal_count,
            "abnormal_count": total - normal_count,
            "normal_percentage": round((normal_count / total) * 100, 1),
        }

    def _generate_weight_section(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成体重章节"""
        records = (
            self.db.query(WeightRecord)
            .filter(
                WeightRecord.user_id == self.user_id,
                WeightRecord.measured_at >= period.start_date,
                WeightRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .order_by(WeightRecord.measured_at)
            .all()
        )

        if not records:
            return {"status": "no_data", "message": "本周期无体重记录"}

        weights = [r.weight_kg for r in records]
        start_weight = weights[0]
        end_weight = weights[-1]
        change = end_weight - start_weight

        return {
            "status": "ok",
            "measurements": len(records),
            "start_weight": round(start_weight, 2),
            "end_weight": round(end_weight, 2),
            "change_kg": round(change, 2),
            "change_pct": round((change / start_weight) * 100, 2),
            "min_weight": round(min(weights), 2),
            "max_weight": round(max(weights), 2),
            "avg_weight": round(sum(weights) / len(weights), 2),
            "trend": (
                "decreasing"
                if change < -0.5
                else "increasing" if change > 0.5 else "stable"
            ),
        }

    def _generate_sleep_section(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成睡眠章节"""
        records = (
            self.db.query(SleepRecord)
            .filter(
                SleepRecord.user_id == self.user_id,
                SleepRecord.bed_time >= period.start_date,
                SleepRecord.bed_time < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not records:
            return {"status": "no_data", "message": "本周期无睡眠记录"}

        durations = [r.duration_minutes / 60 for r in records]  # 转小时
        qualities = [r.sleep_quality for r in records if r.sleep_quality]

        return {
            "status": "ok",
            "total_nights": len(records),
            "avg_duration_hours": round(sum(durations) / len(durations), 1),
            "min_duration": round(min(durations), 1),
            "max_duration": round(max(durations), 1),
            "avg_quality": (
                round(sum(qualities) / len(qualities), 1) if qualities else None
            ),
            "days_under_7h": sum(1 for d in durations if d < 7),
            "days_over_9h": sum(1 for d in durations if d > 9),
            "optimal_days": sum(1 for d in durations if 7 <= d <= 9),
        }

    def _generate_hr_section(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成心率章节"""
        records = (
            self.db.query(HeartRateRecord)
            .filter(
                HeartRateRecord.user_id == self.user_id,
                HeartRateRecord.measured_at >= period.start_date,
                HeartRateRecord.measured_at < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not records:
            return {"status": "no_data", "message": "本周期无心率记录"}

        by_activity = {}
        for r in records:
            act = r.activity or "unknown"
            if act not in by_activity:
                by_activity[act] = []
            by_activity[act].append(r.bpm)

        stats_by_activity = {}
        for act, bpms in by_activity.items():
            stats_by_activity[act] = {
                "count": len(bpms),
                "avg": round(sum(bpms) / len(bpms)),
                "min": min(bpms),
                "max": max(bpms),
            }

        return {
            "status": "ok",
            "total_readings": len(records),
            "by_activity": stats_by_activity,
        }

    def _generate_medication_section(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成用药章节"""
        active_medications = (
            self.db.query(Medication)
            .filter(Medication.user_id == self.user_id, Medication.is_active == True)
            .all()
        )

        if not active_medications:
            return {"status": "no_active", "message": "当前无活跃用药"}

        med_reports = []
        for med in active_medications:
            logs = (
                self.db.query(MedicationLog)
                .filter(
                    MedicationLog.medication_id == med.id,
                    MedicationLog.taken_at >= period.start_date,
                    MedicationLog.taken_at < period.end_date + timedelta(days=1),
                )
                .all()
            )

            taken_count = sum(1 for l in logs if l.status == "taken")
            skipped_count = sum(1 for l in logs if l.status == "skipped")
            total = taken_count + skipped_count

            adherence_rate = (taken_count / total * 100) if total > 0 else None

            med_reports.append(
                {
                    "medication_id": med.id,
                    "name": med.name,
                    "dosage": med.dosage,
                    "purpose": med.purpose,
                    "taken_count": taken_count,
                    "skipped_count": skipped_count,
                    "adherence_rate": (
                        round(adherence_rate, 1) if adherence_rate else None
                    ),
                    "status": (
                        "excellent"
                        if adherence_rate and adherence_rate >= 95
                        else (
                            "good"
                            if adherence_rate and adherence_rate >= 80
                            else (
                                "fair"
                                if adherence_rate and adherence_rate >= 50
                                else "poor"
                            )
                        )
                    ),
                }
            )

        return {
            "status": "ok",
            "active_medications": len(active_medications),
            "medications": med_reports,
            "overall_adherence": self._calculate_overall_adherence(med_reports),
        }

    def _calculate_overall_adherence(self, med_reports: List[dict]) -> Dict[str, Any]:
        """计算整体依从性"""
        rates = [m["adherence_rate"] for m in med_reports if m["adherence_rate"]]
        if not rates:
            return {"rate": None, "status": "unknown"}

        avg_rate = sum(rates) / len(rates)
        return {
            "rate": round(avg_rate, 1),
            "status": (
                "excellent"
                if avg_rate >= 95
                else (
                    "good"
                    if avg_rate >= 80
                    else "fair" if avg_rate >= 50 else "needs_improvement"
                )
            ),
        }

    def _generate_goals_section(self, period: ReportPeriod) -> Dict[str, Any]:
        """生成目标章节"""
        goals = (
            self.db.query(Goal)
            .filter(
                Goal.user_id == self.user_id,
                Goal.created_at < period.end_date + timedelta(days=1),
            )
            .all()
        )

        if not goals:
            return {"status": "no_goals", "message": "未设定健康目标"}

        active = sum(1 for g in goals if g.status == "active")
        completed = sum(1 for g in goals if g.status == "completed")
        expired = sum(1 for g in goals if g.status == "expired")

        return {
            "status": "ok",
            "total_goals": len(goals),
            "active": active,
            "completed": completed,
            "expired": expired,
            "completion_rate": round((completed / len(goals)) * 100, 1),
        }

    def _generate_recommendations(self, period: ReportPeriod) -> List[Dict[str, str]]:
        """生成健康建议"""
        recommendations = []

        # 血压建议
        bp_section = self._generate_bp_section(period)
        if bp_section.get("status") == "ok":
            cat_dist = bp_section.get("category_distribution", {})
            if cat_dist.get("crisis", 0) > 0 or cat_dist.get("stage2", 0) > 2:
                recommendations.append(
                    {
                        "category": "血压管理",
                        "priority": "high",
                        "message": "近期血压控制不佳，建议尽快就医调整治疗方案",
                        "actions": ["预约心内科", "加强血压监测", "低盐饮食"],
                    }
                )
            elif cat_dist.get("stage1", 0) > 3:
                recommendations.append(
                    {
                        "category": "血压管理",
                        "priority": "medium",
                        "message": "血压偶有升高，建议改善生活方式",
                        "actions": ["减少钠盐摄入", "规律运动", "控制体重"],
                    }
                )

        # 血糖建议
        glucose_section = self._generate_glucose_section(period)
        if glucose_section.get("status") == "ok":
            normal_rate = glucose_section.get("normal_rate", {})
            if normal_rate.get("normal_percentage", 0) < 70:
                recommendations.append(
                    {
                        "category": "血糖管理",
                        "priority": "high",
                        "message": "血糖控制率偏低，建议咨询医生调整管理方案",
                        "actions": ["监测饮食", "按时用药", "定期复查"],
                    }
                )

        # 睡眠建议
        sleep_section = self._generate_sleep_section(period)
        if sleep_section.get("status") == "ok":
            if sleep_section.get("days_under_7h", 0) > 3:
                recommendations.append(
                    {
                        "category": "睡眠改善",
                        "priority": "medium",
                        "message": "睡眠不足，建议保证每晚7-9小时睡眠",
                        "actions": ["固定作息时间", "睡前放松", "减少咖啡因"],
                    }
                )

        # 默认建议
        if not recommendations:
            recommendations.append(
                {
                    "category": "整体健康",
                    "priority": "low",
                    "message": "整体健康状况良好，继续保持！",
                    "actions": ["坚持记录", "定期体检", "保持运动"],
                }
            )

        return recommendations


def generate_weekly_report(db: Session, user_id: int) -> Dict[str, Any]:
    """生成周报便捷函数"""
    end = date.today()
    start = end - timedelta(days=6)
    service = PDFReportService(db, user_id)
    return service.generate_health_report(ReportPeriod(start, end), "comprehensive")


def generate_monthly_report(db: Session, user_id: int) -> Dict[str, Any]:
    """生成月报便捷函数"""
    end = date.today()
    start = end - timedelta(days=29)
    service = PDFReportService(db, user_id)
    return service.generate_health_report(ReportPeriod(start, end), "comprehensive")
