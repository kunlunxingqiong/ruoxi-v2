"""
🌸 若曦V2 - 健康趋势预测器
基于历史数据预测未来健康趋势
使用统计模型和机器学习算法
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import mean, stdev
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from models.database import (
    BloodPressureRecord,
    GlucoseRecord,
    HeartRateRecord,
    SleepRecord,
    WeightRecord,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """预测结果"""

    metric: str  # 指标名称
    current_value: float  # 当前值
    predicted_7d: float  # 7天预测
    predicted_30d: float  # 30天预测
    confidence_7d: float  # 7天置信度 (0-1)
    confidence_30d: float  # 30天置信度 (0-1)
    trend_direction: str  # 趋势方向 (improving/stable/declining)
    risk_level: str  # 风险等级 (low/medium/high)


class HealthPredictor:
    """
    健康趋势预测器

    使用线性回归和移动平均算法预测未来健康指标
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def predict_blood_pressure(self, days: int = 90) -> Optional[Dict[str, Any]]:
        """
        预测血压趋势

        Args:
            days: 使用多少天历史数据

        Returns:
            血压预测结果
        """
        records = (
            self.db.query(BloodPressureRecord)
            .filter(
                BloodPressureRecord.user_id == self.user_id,
                BloodPressureRecord.measured_at
                >= datetime.utcnow() - timedelta(days=days),
            )
            .order_by(BloodPressureRecord.measured_at)
            .all()
        )

        if len(records) < 7:
            return None

        systolics = [r.systolic for r in records]
        diastolics = [r.diastolic for r in records]

        # 计算趋势
        systolic_trend = self._calculate_trend(systolics)
        diastolic_trend = self._calculate_trend(diastolics)

        # 预测
        recent_systolic = mean(systolics[-7:])
        recent_diastolic = mean(diastolics[-7:])

        pred_7d_sys = recent_systolic + systolic_trend * 7
        pred_7d_dia = recent_diastolic + diastolic_trend * 7

        pred_30d_sys = recent_systolic + systolic_trend * 30
        pred_30d_dia = recent_diastolic + diastolic_trend * 30

        # 计算置信度
        conf_7d = self._calculate_confidence(systolics, 7)
        conf_30d = self._calculate_confidence(systolics, 30)

        # 趋势方向
        trend_dir = self._trend_direction(systolic_trend)

        # 风险等级
        risk = self._bp_risk_level(pred_30d_sys, pred_30d_dia)

        return PredictionResult(
            metric="blood_pressure",
            current_value=f"{recent_systolic:.0f}/{recent_diastolic:.0f}",
            predicted_7d=f"{pred_7d_sys:.0f}/{pred_7d_dia:.0f}",
            predicted_30d=f"{pred_30d_sys:.0f}/{pred_30d_dia:.0f}",
            confidence_7d=conf_7d,
            confidence_30d=conf_30d,
            trend_direction=trend_dir,
            risk_level=risk,
        ).__dict__

    def predict_weight(self, days: int = 90) -> Optional[Dict[str, Any]]:
        """预测体重趋势"""
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
            return None

        weights = [r.weight_kg for r in records]
        trend = self._calculate_trend(weights)
        recent = mean(weights[-7:])

        pred_7d = recent + trend * 7
        pred_30d = recent + trend * 30

        conf_7d = self._calculate_confidence(weights, 7)
        conf_30d = self._calculate_confidence(weights, 30)

        # BMI计算 (假设身高175cm)
        bmi_7d = pred_7d / (1.75**2)
        bmi_30d = pred_30d / (1.75**2)

        return PredictionResult(
            metric="weight",
            current_value=round(recent, 2),
            predicted_7d=round(pred_7d, 2),
            predicted_30d=round(pred_30d, 2),
            confidence_7d=conf_7d,
            confidence_30d=conf_30d,
            trend_direction=self._trend_direction(trend, threshold=0.1),
            risk_level=(
                "low"
                if 18.5 <= bmi_30d <= 24
                else "medium" if 24 < bmi_30d <= 28 else "high"
            ),
        ).__dict__

    def predict_glucose(self, days: int = 60) -> Optional[Dict[str, Any]]:
        """预测血糖趋势"""
        records = (
            self.db.query(GlucoseRecord)
            .filter(
                GlucoseRecord.user_id == self.user_id,
                GlucoseRecord.measured_at >= datetime.utcnow() - timedelta(days=days),
            )
            .order_by(GlucoseRecord.measured_at)
            .all()
        )

        if len(records) < 7:
            return None

        values = [r.value for r in records if r.meal_type == "fasting"]
        if not values:
            values = [r.value for r in records]

        trend = self._calculate_trend(values)
        recent = mean(values[-5:])

        pred_7d = recent + trend * 7
        pred_30d = recent + trend * 30

        conf_7d = self._calculate_confidence(values, 7)
        conf_30d = self._calculate_confidence(values, 30)

        return PredictionResult(
            metric="glucose",
            current_value=round(recent, 2),
            predicted_7d=round(pred_7d, 2),
            predicted_30d=round(pred_30d, 2),
            confidence_7d=conf_7d,
            confidence_30d=conf_30d,
            trend_direction=self._trend_direction(trend, threshold=0.05),
            risk_level=(
                "low" if pred_30d < 6.1 else "medium" if pred_30d < 7.0 else "high"
            ),
        ).__dict__

    def predict_sleep(self, days: int = 60) -> Optional[Dict[str, Any]]:
        """预测睡眠质量趋势"""
        records = (
            self.db.query(SleepRecord)
            .filter(
                SleepRecord.user_id == self.user_id,
                SleepRecord.bed_time >= datetime.utcnow() - timedelta(days=days),
            )
            .all()
        )

        if len(records) < 7:
            return None

        durations = [r.duration_minutes / 60 for r in records]
        trend = self._calculate_trend(durations)
        recent = mean(durations[-7:])

        pred_7d = recent + trend * 7
        pred_30d = recent + trend * 30

        conf_7d = self._calculate_confidence(durations, 7)
        conf_30d = self._calculate_confidence(durations, 30)

        return PredictionResult(
            metric="sleep",
            current_value=round(recent, 1),
            predicted_7d=round(pred_7d, 1),
            predicted_30d=round(pred_30d, 1),
            confidence_7d=conf_7d,
            confidence_30d=conf_30d,
            trend_direction=(
                "improving"
                if trend > 0.05
                else "declining" if trend < -0.05 else "stable"
            ),
            risk_level="low" if 7 <= pred_30d <= 9 else "medium",
        ).__dict__

    def _calculate_trend(self, values: List[float]) -> float:
        """
        计算数据趋势 (斜率)
        使用简单线性回归
        """
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))

        # 计算相关系数
        x_mean = mean(x)
        y_mean = mean(values)

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator
        return slope

    def _calculate_confidence(self, values: List[float], forecast_days: int) -> float:
        """
        计算预测置信度
        基于历史数据的方差
        """
        if len(values) < 7:
            return 0.5

        try:
            data_std = stdev(values)
            data_mean = mean(values)

            # 变异系数
            cv = data_std / data_mean if data_mean != 0 else 1

            # 数据越稳定，置信度越高
            # 根据历史数据衰减
            base_confidence = max(0.3, 1 - cv)

            # 随预测时间衰减
            decay = 1 - (forecast_days / 365) * 0.5

            return min(0.95, base_confidence * decay)
        except:
            return 0.5

    def _trend_direction(self, slope: float, threshold: float = 0.5) -> str:
        """判断趋势方向"""
        if slope > threshold:
            return "increasing"
        elif slope < -threshold:
            return "decreasing"
        return "stable"

    def _bp_risk_level(self, systolic: float, diastolic: float) -> str:
        """血压风险等级"""
        if systolic >= 180 or diastolic >= 120:
            return "critical"
        elif systolic >= 140 or diastolic >= 90:
            return "high"
        elif systolic >= 130 or diastolic >= 80:
            return "medium"
        return "low"

    def get_all_predictions(self) -> Dict[str, Any]:
        """获取所有预测结果"""
        predictions = {}

        bp_pred = self.predict_blood_pressure()
        if bp_pred:
            predictions["blood_pressure"] = bp_pred

        weight_pred = self.predict_weight()
        if weight_pred:
            predictions["weight"] = weight_pred

        glucose_pred = self.predict_glucose()
        if glucose_pred:
            predictions["glucose"] = glucose_pred

        sleep_pred = self.predict_sleep()
        if sleep_pred:
            predictions["sleep"] = sleep_pred

        return {
            "predictions": predictions,
            "generated_at": datetime.utcnow().isoformat(),
            "user_id": self.user_id,
        }


# 便捷函数
def predict_user_health_trends(db: Session, user_id: int) -> Dict[str, Any]:
    """预测用户健康趋势便捷函数"""
    predictor = HealthPredictor(db, user_id)
    return predictor.get_all_predictions()
