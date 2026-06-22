"""
🌸 若曦V2 - 健康异常检测器
基于历史数据识别健康指标的异常波动
使用统计方法和机器学习检测异常
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import Any, Dict, List, Optional, Tuple

from models.database import (
    BloodPressureRecord,
    GlucoseRecord,
    HeartRateRecord,
    WeightRecord,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """异常检测结果"""

    metric: str
    detected: bool
    severity: str  # info/warning/critical
    message: str
    current_value: float
    expected_range: Tuple[float, float]
    deviation_percentage: float
    affected_records: int = 0
    recommendation: str = ""


class HealthAnomalyDetector:
    """
    健康异常检测器

    使用多种方法检测健康指标异常:
    - 统计方法: Z-score, IQR
    - 趋势分析: 突变检测
    - 模式识别: 周期性异常
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.anomalies: List[AnomalyResult] = []

    def detect_all_anomalies(self, days: int = 30) -> Dict[str, Any]:
        """
        检测所有健康指标的异常

        Args:
            days: 检查最近多少天的数据

        Returns:
            所有异常检测结果汇总
        """
        self.anomalies = []

        # 检测各项指标的异常
        self._detect_bp_anomalies(days)
        self._detect_glucose_anomalies(days)
        self._detect_weight_anomalies(days)
        self._detect_hr_anomalies(days)

        return {
            "detected_anomalies": [a.__dict__ for a in self.anomalies],
            "total_anomalies": len(self.anomalies),
            "critical_count": sum(
                1 for a in self.anomalies if a.severity == "critical"
            ),
            "warning_count": sum(1 for a in self.anomalies if a.severity == "warning"),
            "checked_at": datetime.utcnow().isoformat(),
        }

    def _detect_bp_anomalies(self, days: int) -> None:
        """检测血压异常"""
        records = (
            self.db.query(BloodPressureRecord)
            .filter(
                BloodPressureRecord.user_id == self.user_id,
                BloodPressureRecord.measured_at
                >= datetime.utcnow() - timedelta(days=days),
            )
            .all()
        )

        if len(records) < 3:
            return

        systolics = [r.systolic for r in records]
        diastolics = [r.diastolic for r in records]

        # 使用Z-score检测异常
        sys_anomalies = self._zscore_outliers(systolics, threshold=2.5)
        dia_anomalies = self._zscore_outliers(diastolics, threshold=2.5)

        # 检测血压突变
        recent_records = records[-5:] if len(records) >= 5 else records
        for record in recent_records:
            # 危机级别血压
            if record.systolic >= 180 or record.diastolic >= 120:
                self.anomalies.append(
                    AnomalyResult(
                        metric="blood_pressure",
                        detected=True,
                        severity="critical",
                        message=f"血压危机: {record.systolic}/{record.diastolic} mmHg",
                        current_value=record.systolic,
                        expected_range=(90, 140),
                        deviation_percentage=(
                            ((record.systolic - 140) / 140 * 100)
                            if record.systolic > 140
                            else 0
                        ),
                        affected_records=1,
                        recommendation="请立即就医或呼叫急救",
                    )
                )
            # 高血压级别
            elif record.systolic >= 140 or record.diastolic >= 90:
                self.anomalies.append(
                    AnomalyResult(
                        metric="blood_pressure",
                        detected=True,
                        severity="warning",
                        message=f"血压偏高: {record.systolic}/{record.diastolic} mmHg",
                        current_value=record.systolic,
                        expected_range=(90, 140),
                        deviation_percentage=((record.systolic - 140) / 140 * 100),
                        affected_records=1,
                        recommendation="建议调整生活方式，咨询医生",
                    )
                )

        # 检测血压波动过大
        if len(systolics) >= 7:
            recent_mean = mean(systolics[-7:])
            recent_std = stdev(systolics[-7:]) if len(set(systolics[-7:])) > 1 else 0

            if recent_std > 15:
                self.anomalies.append(
                    AnomalyResult(
                        metric="blood_pressure",
                        detected=True,
                        severity="warning",
                        message=f"血压波动较大 (标准差: {recent_std:.1f})",
                        current_value=recent_mean,
                        expected_range=(recent_mean - 10, recent_mean + 10),
                        deviation_percentage=(recent_std / recent_mean * 100),
                        affected_records=7,
                        recommendation="建议记录生活因素，咨询医生是否需要调整用药",
                    )
                )

    def _detect_glucose_anomalies(self, days: int) -> None:
        """检测血糖异常"""
        records = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == self.user_id,
                GlucoseRecord.measured_at >= datetime.utcnow() - timedelta(days=days),
            )
            .all()
        )

        if len(records) < 3:
            return

        # 获取空腹血糖
        fasting_records = [r for r in records if r.meal_type == "fasting"]

        for record in records[-10:]:  # 检查最近10条
            # 严重高血糖
            if record.value > 16.7:
                self.anomalies.append(
                    AnomalyResult(
                        metric="glucose",
                        detected=True,
                        severity="critical",
                        message=f"严重高血糖: {record.value} mmol/L",
                        current_value=record.value,
                        expected_range=(3.9, 11.1),
                        deviation_percentage=((record.value - 11.1) / 11.1 * 100),
                        affected_records=1,
                        recommendation="立即就医检查",
                    )
                )
            # 低血糖
            elif record.value < 3.9:
                self.anomalies.append(
                    AnomalyResult(
                        metric="glucose",
                        detected=True,
                        severity="critical",
                        message=f"低血糖警报: {record.value} mmol/L",
                        current_value=record.value,
                        expected_range=(3.9, 6.1),
                        deviation_percentage=((3.9 - record.value) / 3.9 * 100),
                        affected_records=1,
                        recommendation="立即补充糖分，如症状持续请就医",
                    )
                )

        # 空腹血糖趋势异常
        if len(fasting_records) >= 5:
            fasting_values = [r.value for r in fasting_records[-5:]]
            if mean(fasting_values) > 7.0:
                self.anomalies.append(
                    AnomalyResult(
                        metric="glucose",
                        detected=True,
                        severity="warning",
                        message=f"空腹血糖控制不佳 (平均: {mean(fasting_values):.1f} mmol/L)",
                        current_value=mean(fasting_values),
                        expected_range=(3.9, 6.1),
                        deviation_percentage=((mean(fasting_values) - 6.1) / 6.1 * 100),
                        affected_records=len(fasting_records),
                        recommendation="建议复查糖化血红蛋白，调整饮食和用药",
                    )
                )

    def _detect_weight_anomalies(self, days: int) -> None:
        """检测体重异常变化"""
        records = (
            self.db.query(WeightRecord)
            .filter(
                WeightRecord.user_id == self.user_id,
                WeightRecord.measured_at >= datetime.utcnow() - timedelta(days=days),
            )
            .order_by(WeightRecord.measured_at)
            .all()
        )

        if len(records) < 7:
            return

        weights = [r.weight_kg for r in records]

        # 检测快速减重/增重
        recent_weight = weights[-1]
        weight_7d_ago = weights[-7] if len(weights) >= 7 else weights[0]

        change_7d = recent_weight - weight_7d_ago
        change_pct = (change_7d / weight_7d_ago) * 100 if weight_7d_ago != 0 else 0

        # 7天内变化超过3%
        if abs(change_pct) > 3:
            direction = "增加" if change_7d > 0 else "减少"
            self.anomalies.append(
                AnomalyResult(
                    metric="weight",
                    detected=True,
                    severity="warning" if abs(change_pct) < 5 else "critical",
                    message=f"体重快速{direction}: {abs(change_7d):.1f}kg ({abs(change_pct):.1f}%)",
                    current_value=recent_weight,
                    expected_range=(weight_7d_ago * 0.97, weight_7d_ago * 1.03),
                    deviation_percentage=abs(change_pct),
                    affected_records=len(records),
                    recommendation="建议记录饮食和运动情况，如非计划性减重/增重请咨询医生",
                )
            )

        # 检测异常波动
        if len(weights) >= 14:
            recent_std = stdev(weights[-14:]) if len(set(weights[-14:])) > 1 else 0
            if recent_std > 2:
                self.anomalies.append(
                    AnomalyResult(
                        metric="weight",
                        detected=True,
                        severity="info",
                        message=f"体重波动较大 (标准差: {recent_std:.2f}kg)",
                        current_value=recent_weight,
                        expected_range=(
                            mean(weights[-14:]) - 1,
                            mean(weights[-14:]) + 1,
                        ),
                        deviation_percentage=(recent_std / mean(weights[-14:]) * 100),
                        affected_records=14,
                        recommendation="建议固定称重时间，早上空腹称重最为准确",
                    )
                )

    def _detect_hr_anomalies(self, days: int) -> None:
        """检测心率异常"""
        records = (
            self.db.query(HeartRateRecord)
            .filter(
                HeartRateRecord.user_id == self.user_id,
                HeartRateRecord.measured_at >= datetime.utcnow() - timedelta(days=days),
                HeartRateRecord.activity == "resting",  # 只检查静息心率
            )
            .all()
        )

        if len(records) < 5:
            return

        for record in records[-10:]:
            # 心动过缓
            if record.bpm < 50:
                self.anomalies.append(
                    AnomalyResult(
                        metric="heart_rate",
                        detected=True,
                        severity="warning" if record.bpm >= 40 else "critical",
                        message=f"心动过缓: {record.bpm} bpm",
                        current_value=record.bpm,
                        expected_range=(60, 100),
                        deviation_percentage=((60 - record.bpm) / 60 * 100),
                        affected_records=1,
                        recommendation="如伴有头晕、乏力请咨询医生",
                    )
                )
            # 心动过速
            elif record.bpm > 100:
                self.anomalies.append(
                    AnomalyResult(
                        metric="heart_rate",
                        detected=True,
                        severity="warning" if record.bpm <= 120 else "critical",
                        message=f"心动过速: {record.bpm} bpm",
                        current_value=record.bpm,
                        expected_range=(60, 100),
                        deviation_percentage=((record.bpm - 100) / 100 * 100),
                        affected_records=1,
                        recommendation="检查是否在运动后测量，休息时复测",
                    )
                )

    def _zscore_outliers(
        self, values: List[float], threshold: float = 2.0
    ) -> List[int]:
        """
        使用Z-score检测异常值

        Args:
            values: 数据列表
            threshold: Z-score阈值

        Returns:
            异常值的索引列表
        """
        if len(values) < 3:
            return []

        mean_val = mean(values)
        std_val = stdev(values) if len(set(values)) > 1 else 1

        if std_val == 0:
            return []

        outliers = []
        for i, value in enumerate(values):
            z_score = abs((value - mean_val) / std_val)
            if z_score > threshold:
                outliers.append(i)

        return outliers

    def _iqr_outliers(self, values: List[float]) -> List[int]:
        """
        使用IQR方法检测异常值

        Returns:
            异常值的索引列表
        """
        if len(values) < 4:
            return []

        sorted_values = sorted(values)
        n = len(sorted_values)

        q1_idx = n // 4
        q3_idx = 3 * n // 4

        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]

        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outliers.append(i)

        return outliers


# 便捷函数
def detect_user_health_anomalies(db: Session, user_id: int) -> Dict[str, Any]:
    """检测用户健康异常便捷函数"""
    detector = HealthAnomalyDetector(db, user_id)
    return detector.detect_all_anomalies()
