"""
🌸 若曦V2 - 健康记录服务层
业务逻辑封装，提供高层次的健康数据管理接口
"""

import statistics
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from models.database import (
    BloodPressureCategory,
    BloodPressureRecord,
    GlucoseRecord,
    HeartRateRecord,
    SleepRecord,
)
from models.database import User as UserModel
from models.database import (
    WeightRecord,
)
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session


class HealthService:
    """健康记录服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 血压服务 ====================

    def get_bp_statistics(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        获取血压统计分析

        返回包含平均、最大、最小、标准差等统计指标
        """
        query = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == user_id
        )

        if start_date:
            query = query.filter(BloodPressureRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(BloodPressureRecord.measured_at <= end_date)

        records = query.all()

        if not records:
            return {
                "count": 0,
                "average": None,
                "max": None,
                "min": None,
                "standard_deviation": None,
                "category_distribution": {},
            }

        systolic_values = [r.systolic for r in records]
        diastolic_values = [r.diastolic for r in records]

        # 分类统计
        category_counts = {}
        for cat in BloodPressureCategory:
            category_counts[cat.value] = sum(1 for r in records if r.category == cat)

        return {
            "count": len(records),
            "average": {
                "systolic": round(statistics.mean(systolic_values), 1),
                "diastolic": round(statistics.mean(diastolic_values), 1),
            },
            "max": {
                "systolic": max(systolic_values),
                "diastolic": max(diastolic_values),
            },
            "min": {
                "systolic": min(systolic_values),
                "diastolic": min(diastolic_values),
            },
            "standard_deviation": {
                "systolic": (
                    round(statistics.stdev(systolic_values), 2)
                    if len(systolic_values) > 1
                    else 0
                ),
                "diastolic": (
                    round(statistics.stdev(diastolic_values), 2)
                    if len(diastolic_values) > 1
                    else 0
                ),
            },
            "category_distribution": category_counts,
            "abnormal_count": sum(
                category_counts.get(cat, 0) for cat in ["stage1", "stage2", "crisis"]
            ),
        }

    def get_morning_bp_surge(
        self, user_id: int, days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        检测晨峰血压 (Morning Surge)

        比较晨间(6-10点)与其他时段的血压差异
        """
        from datetime import time

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        records = (
            self.db.query(BloodPressureRecord)
            .filter(
                BloodPressureRecord.user_id == user_id,
                BloodPressureRecord.measured_at >= start_date,
            )
            .all()
        )

        if len(records) < 10:
            return None

        morning_records = [
            r for r in records if time(6, 0) <= r.measured_at.time() <= time(10, 0)
        ]
        other_records = [
            r
            for r in records
            if r.measured_at.time() < time(6, 0) or r.measured_at.time() > time(10, 0)
        ]

        if not morning_records or not other_records:
            return None

        morning_avg_sys = statistics.mean([r.systolic for r in morning_records])
        other_avg_sys = statistics.mean([r.systolic for r in other_records])

        surge = morning_avg_sys - other_avg_sys

        return {
            "has_morning_surge": surge > 20,  # 晨峰定义: >20mmHg
            "surge_mmhg": round(surge, 1),
            "morning_avg": round(morning_avg_sys, 1),
            "other_avg": round(other_avg_sys, 1),
            "morning_readings": len(morning_records),
            "other_readings": len(other_records),
        }

    # ==================== 血糖服务 ====================

    def get_glucose_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """获取血糖趋势分析"""
        start_date = datetime.now() - timedelta(days=days)

        records = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == user_id,
                GlucoseRecord.measured_at >= start_date,
            )
            .order_by(GlucoseRecord.measured_at)
            .all()
        )

        if not records:
            return {"trend": "no_data", "records_count": 0}

        # 按时段分组
        by_meal_type = {}
        for r in records:
            mt = r.meal_type
            if mt not in by_meal_type:
                by_meal_type[mt] = []
            by_meal_type[mt].append(r.value)

        # 计算各时段平均和控制率
        meal_stats = {}
        for meal_type, values in by_meal_type.items():
            meal_stats[meal_type] = {
                "average": round(statistics.mean(values), 2),
                "min": min(values),
                "max": max(values),
                "count": len(values),
                "in_control": self._check_glucose_control(meal_type, values),
            }

        # 整体趋势
        values = [r.value for r in records]
        first_week = values[: len(values) // 4] if len(values) >= 4 else values[:1]
        last_week = values[-len(values) // 4 :] if len(values) >= 4 else values[-1:]

        first_avg = statistics.mean(first_week)
        last_avg = statistics.mean(last_week)

        if last_avg < first_avg - 0.5:
            trend = "improving"
        elif last_avg > first_avg + 0.5:
            trend = "worsening"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "records_count": len(records),
            "period_days": days,
            "by_meal_type": meal_stats,
            "average_change": round(last_avg - first_avg, 2),
        }

    def _check_glucose_control(
        self, meal_type: str, values: List[float]
    ) -> Dict[str, Any]:
        """检查血糖控制情况"""
        # 目标范围 (mmol/L)
        targets = {
            "fasting": (4.4, 7.0),
            "before_meal": (4.4, 7.0),
            "after_meal": (4.4, 10.0),
            "before_bed": (5.0, 8.3),
            "random": (3.9, 11.1),
        }

        target = targets.get(meal_type, (3.9, 11.1))
        low, high = target

        in_range = sum(1 for v in values if low <= v <= high)
        below = sum(1 for v in values if v < low)
        above = sum(1 for v in values if v > high)

        return {
            "target_range": f"{low}-{high}",
            "in_range": in_range,
            "below_target": below,
            "above_target": above,
            "control_rate": round(in_range / len(values) * 100, 1) if values else 0,
        }

    # ==================== 体重服务 ====================

    def calculate_weight_progress(
        self, user_id: int, goal_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """计算体重进度"""
        records = (
            self.db.query(WeightRecord)
            .filter(WeightRecord.user_id == user_id)
            .order_by(WeightRecord.measured_at)
            .all()
        )

        if not records:
            return {"status": "no_data"}

        current = records[-1].weight_kg
        start = records[0].weight_kg

        # 获取用户目标体重
        if goal_weight is None:
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if user and user.height_cm:
                # BMI 22 作为健康目标
                goal_weight = round(22 * (user.height_cm / 100) ** 2, 1)
            else:
                goal_weight = current  # 无目标时设为当前

        total_change = round(current - start, 2)
        goal_distance = round(current - goal_weight, 2)

        progress_percent = 0
        if abs(start - goal_weight) > 0.1:
            progress_percent = round(
                (1 - abs(goal_distance) / abs(start - goal_weight)) * 100, 1
            )
            progress_percent = max(0, min(100, progress_percent))

        return {
            "start_weight": start,
            "current_weight": current,
            "goal_weight": goal_weight,
            "total_change_kg": total_change,
            "distance_to_goal": goal_distance,
            "progress_percent": progress_percent,
            "records_count": len(records),
            "trend": (
                "decreasing"
                if total_change < -0.5
                else "increasing" if total_change > 0.5 else "stable"
            ),
        }

    # ==================== 睡眠服务 ====================

    def get_sleep_quality_score(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """计算睡眠质量评分"""
        start_date = datetime.now() - timedelta(days=days)

        records = (
            self.db.query(SleepRecord)
            .filter(SleepRecord.user_id == user_id, SleepRecord.bed_time >= start_date)
            .all()
        )

        if not records:
            return {"score": None, "status": "no_data"}

        # 各项评分因子
        scores = []

        for record in records:
            score = 0

            # 时长评分 (目标7-9小时 = 100分)
            duration_hours = record.duration_minutes / 60
            if 7 <= duration_hours <= 9:
                score += 30
            elif 6 <= duration_hours < 7 or 9 < duration_hours <= 10:
                score += 20
            elif 5 <= duration_hours < 6:
                score += 10
            else:
                score += 5

            # 睡眠质量评分 (用户自评 1-10)
            if record.sleep_quality:
                score += record.sleep_quality * 3

            # 深睡比例 (深睡占总睡眠的15-25%为佳)
            if record.deep_sleep_minutes and record.duration_minutes:
                deep_ratio = record.deep_sleep_minutes / record.duration_minutes
                if 0.15 <= deep_ratio <= 0.25:
                    score += 20
                elif 0.1 <= deep_ratio < 0.15:
                    score += 15
                else:
                    score += 10

            # 醒来次数 (越少越好)
            if record.awake_times is not None:
                if record.awake_times == 0:
                    score += 10
                elif record.awake_times <= 2:
                    score += 7
                else:
                    score += 3

            scores.append(score)

        avg_score = round(statistics.mean(scores), 1) if scores else 0

        # 状态评级
        if avg_score >= 85:
            status = "excellent"
        elif avg_score >= 70:
            status = "good"
        elif avg_score >= 55:
            status = "fair"
        else:
            status = "poor"

        return {
            "score": avg_score,
            "max_score": 100,
            "status": status,
            "analysis_days": days,
            "records_analyzed": len(records),
            "recommendations": self._generate_sleep_recommendations(records),
        }

    def _generate_sleep_recommendations(self, records: List[SleepRecord]) -> List[str]:
        """生成睡眠改善建议"""
        recommendations = []

        avg_duration = statistics.mean([r.duration_minutes / 60 for r in records])
        if avg_duration < 6:
            recommendations.append("建议增加睡眠时间，目标每晚7-9小时")

        awake_counts = [r.awake_times for r in records if r.awake_times is not None]
        if awake_counts and statistics.mean(awake_counts) > 3:
            recommendations.append("夜间醒来次数较多，建议改善睡眠环境或减少晚间饮水")

        deep_sleep_records = [r for r in records if r.deep_sleep_minutes]
        if deep_sleep_records:
            avg_deep_ratio = statistics.mean(
                [r.deep_sleep_minutes / r.duration_minutes for r in deep_sleep_records]
            )
            if avg_deep_ratio < 0.15:
                recommendations.append("深睡比例偏低，建议增加日间运动并规律作息")

        if not recommendations:
            recommendations.append("睡眠质量良好，继续保持！")

        return recommendations

    # ==================== 心率服务 ====================

    def get_heart_rate_variability(
        self, user_id: int, days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        计算心率变异性 (HRV) 指标

        HRV是心脏健康的良好指标
        """
        start_date = datetime.now() - timedelta(days=days)

        resting_records = (
            self.db.query(HeartRateRecord)
            .filter(
                HeartRateRecord.user_id == user_id,
                HeartRateRecord.activity == "resting",
                HeartRateRecord.measured_at >= start_date,
            )
            .all()
        )

        if len(resting_records) < 5:
            return None

        values = [r.bpm for r in resting_records]

        # 计算RR间期变异 (简化HRV)
        mean_hr = statistics.mean(values)
        sdnn = statistics.stdev(values) if len(values) > 1 else 0

        # HRV评级
        if sdnn > 50:
            hrv_status = "excellent"
        elif sdnn > 30:
            hrv_status = "good"
        elif sdnn > 15:
            hrv_status = "average"
        else:
            hrv_status = "below_average"

        return {
            "sdnn_ms": round(sdnn, 1),
            "mean_hr": round(mean_hr, 1),
            "hrv_status": hrv_status,
            "readings_count": len(values),
            "health_indication": self._interpret_hrv(sdnn, mean_hr),
        }

    def _interpret_hrv(self, sdnn: float, mean_hr: float) -> str:
        """解读HRV指标"""
        if sdnn > 50 and mean_hr < 70:
            return "心脏健康状况优秀，自主神经系统功能良好"
        elif sdnn > 30:
            return "心脏健康良好"
        elif sdnn > 15:
            return "心脏功能正常，建议适当增加有氧运动"
        else:
            return "心率变异性偏低，建议关注心血管健康，必要时咨询医生"

    # ==================== 综合服务 ====================

    def get_health_score(self, user_id: int) -> Dict[str, Any]:
        """
        计算综合健康评分

        基于多项指标计算0-100的综合评分
        """
        scores = {}
        weights = {
            "blood_pressure": 25,
            "glucose": 20,
            "weight": 20,
            "sleep": 20,
            "heart_rate": 15,
        }

        # 血压评分
        bp_stats = self.get_bp_statistics(user_id, days=30)
        if bp_stats["count"] > 0:
            abnormal_rate = bp_stats["abnormal_count"] / bp_stats["count"]
            scores["blood_pressure"] = max(0, 100 - int(abnormal_rate * 100))
        else:
            scores["blood_pressure"] = None

        # 血糖评分 (基于控制率)
        glucose_trend = self.get_glucose_trends(user_id, days=30)
        if glucose_trend["records_count"] > 0:
            control_rates = [
                meal["control_rate"]
                for meal in glucose_trend.get("by_meal_type", {}).values()
            ]
            scores["glucose"] = (
                round(statistics.mean(control_rates)) if control_rates else None
            )
        else:
            scores["glucose"] = None

        # 睡眠评分
        sleep_score = self.get_sleep_quality_score(user_id, days=7)
        scores["sleep"] = sleep_score.get("score")

        # 心率评分
        hrv = self.get_heart_rate_variability(user_id, days=30)
        if hrv:
            hrv_scores = {
                "excellent": 100,
                "good": 85,
                "average": 70,
                "below_average": 50,
            }
            scores["heart_rate"] = hrv_scores.get(hrv["hrv_status"], 50)
        else:
            scores["heart_rate"] = None

        # 体重评分 (假设有目标)
        weight_progress = self.calculate_weight_progress(user_id)
        if weight_progress.get("progress_percent") is not None:
            scores["weight"] = weight_progress["progress_percent"]
        else:
            scores["weight"] = None

        # 计算加权总分
        total_score = 0
        total_weight = 0

        for metric, weight in weights.items():
            if scores.get(metric) is not None:
                total_score += scores[metric] * (weight / 100)
                total_weight += weight

        final_score = (
            round(total_score * (100 / total_weight)) if total_weight > 0 else None
        )

        # 评级
        if final_score is not None:
            if final_score >= 90:
                grade = "A"
                status = "健康状态优秀"
            elif final_score >= 80:
                grade = "B"
                status = "健康状态良好"
            elif final_score >= 60:
                grade = "C"
                status = "健康状态一般，有改善空间"
            else:
                grade = "D"
                status = "健康状态需要关注"
        else:
            grade = "?"
            status = "数据不足，无法评估"

        return {
            "total_score": final_score,
            "max_score": 100,
            "grade": grade,
            "status": status,
            "component_scores": scores,
            "assessment_date": date.today().isoformat(),
        }

    def generate_weekly_report(self, user_id: int) -> Dict[str, Any]:
        """生成周健康报告"""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        report = {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "blood_pressure": self.get_bp_statistics(user_id, start_date, end_date),
            "glucose": self.get_glucose_trends(user_id, days=7),
            "sleep": self.get_sleep_quality_score(user_id, days=7),
            "heart_rate": self.get_heart_rate_variability(user_id, days=7),
            "overall_score": self.get_health_score(user_id),
        }

        # 添加改进建议
        report["recommendations"] = self._generate_weekly_recommendations(report)

        return report

    def _generate_weekly_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """基于周报生成建议"""
        recommendations = []

        # 血压建议
        bp = report.get("blood_pressure", {})
        if bp.get("abnormal_count", 0) > 3:
            recommendations.append("本周血压异常次数较多，建议增加监测频率并咨询医生")

        # 血糖建议
        glucose = report.get("glucose", {})
        if glucose.get("trend") == "worsening":
            recommendations.append("血糖趋势上升，请注意控制饮食和增加运动")

        # 睡眠建议
        sleep = report.get("sleep", {})
        if sleep.get("score", 100) < 60:
            recommendations.append("睡眠质量评分偏低，建议改善睡眠习惯")

        return recommendations
