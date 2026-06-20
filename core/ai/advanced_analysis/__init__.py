"""
🌸 若曦V2 - 高级AI分析模块

提供以下高级分析功能:
- 健康趋势预测 (Health Predictor)
- 异常检测 (Anomaly Detector)
- 疾病风险评估 (Disease Risk Assessment)

使用方法:
    from core.ai.advanced_analysis import AdvancedHealthAnalyzer
    analyzer = AdvancedHealthAnalyzer(db, user_id)
    analysis = analyzer.full_analysis()
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from .health_predictor import HealthPredictor, predict_user_health_trends
from .anomaly_detector import HealthAnomalyDetector, detect_user_health_anomalies
from .risk_assessment import DiseaseRiskAssessor, assess_user_disease_risks


class AdvancedHealthAnalyzer:
    """
    高级健康分析器
    
    整合所有高级AI分析功能，提供一站式健康分析服务
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.predictor = HealthPredictor(db, user_id)
        self.anomaly_detector = HealthAnomalyDetector(db, user_id)
        self.risk_assessor = DiseaseRiskAssessor(db, user_id)
    
    def full_analysis(self) -> Dict[str, Any]:
        """
        进行完整的健康分析
        
        Returns:
            包含预测、异常检测、风险评估的综合报告
        """
        predictions = self.predictor.get_all_predictions()
        anomalies = self.anomaly_detector.detect_all_anomalies()
        risks = self.risk_assessor.assess_all_risks()
        
        # 生成综合建议
        recommendations = self._generate_comprehensive_recommendations(
            predictions, anomalies, risks
        )
        
        return {
            "predictions": predictions,
            "anomalies": anomalies,
            "risks": risks,
            "recommendations": recommendations,
            "summary": self._generate_summary(predictions, anomalies, risks),
            "analyzed_at": datetime.utcnow().isoformat(),
            "user_id": self.user_id
        }
    
    def _generate_comprehensive_recommendations(
        self,
        predictions: Dict,
        anomalies: Dict,
        risks: Dict
    ) -> Dict[str, Any]:
        """生成综合建议"""
        immediate_actions = []
        short_term_goals = []
        long_term_goals = []
        monitoring_plan = []
        
        # 基于异常检测生成即时行动建议
        if anomalies.get("critical_count", 0) > 0:
            immediate_actions.append("存在严重健康异常，建议尽快就医")
        if anomalies.get("warning_count", 0) > 0:
            immediate_actions.append("有健康指标需要关注，请查看详细建议")
        
        for anomaly in anomalies.get("detected_anomalies", []):
            if anomaly.get("severity") == "critical":
                immediate_actions.append(f"[{anomaly['metric']}] {anomaly['recommendation']}")
            elif anomaly.get("severity") == "warning":
                short_term_goals.append(f"改善{anomaly['metric']}: {anomaly['recommendation']}")
        
        # 基于风险评估生成目标
        for risk in risks.get("risks", []):
            if risk.get("risk_level") in ["high", "very_high"]:
                short_term_goals.extend(risk.get("recommendations", []))
            else:
                long_term_goals.extend(risk.get("recommendations", []))
        
        # 基于预测生成长期目标
        for metric, pred in predictions.get("predictions", {}).items():
            if pred.get("risk_level") in ["high", "critical"]:
                long_term_goals.append(f"关注{metric}趋势，采取预防措施")
            if pred.get("trend_direction") == "increasing":
                if metric == "weight":
                    short_term_goals.append("关注体重增长趋势，调整饮食计划")
        
        # 去重
        immediate_actions = list(dict.fromkeys(immediate_actions))
        short_term_goals = list(dict.fromkeys(short_term_goals))
        long_term_goals = list(dict.fromkeys(long_term_goals))
        
        return {
            "immediate_actions": immediate_actions[:5],
            "short_term_goals": short_term_goals[:5],
            "long_term_goals": long_term_goals[:5],
            "monitoring_plan": self._generate_monitoring_plan(anomalies, risks)
        }
    
    def _generate_monitoring_plan(self, anomalies: Dict, risks: Dict) -> Dict[str, Any]:
        """生成监测计划"""
        bp_frequency = "daily" if any(a.get("metric") == "blood_pressure" and a.get("severity") in ["critical", "warning"] for a in anomalies.get("detected_anomalies", [])) else "weekly"
        
        glucose_frequency = "daily" if any(a.get("metric") == "glucose" for a in anomalies.get("detected_anomalies", [])) else "weekly"
        
        weight_frequency = "daily"
        
        return {
            "blood_pressure": {"frequency": bp_frequency, "best_time": "早晨空腹或睡前"},
            "glucose": {"frequency": glucose_frequency, "best_time": "空腹或餐后2小时"},
            "weight": {"frequency": weight_frequency, "best_time": "每天早晨空腹"},
            "heart_rate": {"frequency": bp_frequency, "best_time": "静息状态下"}
        }
    
    def _generate_summary(self, predictions: Dict, anomalies: Dict, risks: Dict) -> Dict[str, Any]:
        """生成分析摘要"""
        pred_count = len(predictions.get("predictions", {}))
        anomaly_count = anomalies.get("total_anomalies", 0)
        risk_count = len(risks.get("risks", []))
        
        # 整体健康状态
        if anomalies.get("critical_count", 0) > 0:
            status = "attention_required"
            status_text = "需要关注"
        elif anomalies.get("warning_count", 0) > 0:
            status = "caution"
            status_text = "谨慎关注"
        else:
            status = "good"
            status_text = "整体良好"
        
        return {
            "health_status": status,
            "health_status_text": status_text,
            "analysis_coverage": f"{pred_count}项指标预测，{risk_count}种疾病风险评估",
            "alerts_summary": f"发现{anomaly_count}个异常，其中{anomalies.get('critical_count', 0)}个严重",
            "next_check_recommended": "建议7天内复查异常指标"
        }


__all__ = [
    "AdvancedHealthAnalyzer",
    "HealthPredictor",
    "predict_user_health_trends",
    "HealthAnomalyDetector",
    "detect_user_health_anomalies",
    "DiseaseRiskAssessor",
    "assess_user_disease_risks"
]
