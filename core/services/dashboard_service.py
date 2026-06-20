"""
🌸 若曦V2 - 个人健康仪表盘服务
聚合展示用户健康数据概览
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import logging

from models.database import (
    User,
    BloodPressureRecord,
    GlucoseRecord,
    WeightRecord,
    HeartRateRecord,
    SleepRecord,
    Medication,
    MedicationLog,
    MedicationSchedule,
    HealthGoal,
    GoalCheckIn,
    Notification,
    HealthReport
)
from core.services.user_preference_service import UserPreferenceService

logger = logging.getLogger(__name__)


class DashboardService:
    """
    个人健康仪表盘服务
    
    聚合展示:
    - 今日健康摘要
    - 近期趋势
    - 待办任务（用药、打卡）
    - 目标进度
    - AI健康洞察
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.pref_service = UserPreferenceService(db, user_id)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取完整仪表盘数据"""
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        return {
            "user_summary": self._get_user_summary(),
            "today_overview": self._get_today_overview(),
            "today_tasks": self._get_today_tasks(),
            "health_trends": self._get_recent_trends(days=7),
            "goal_progress": self._get_active_goals(),
            "recent_records": self._get_recent_records(limit=5),
            "health_alerts": self._get_health_alerts(),
            "insights": self._get_ai_insights(),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_today_summary(self) -> Dict[str, Any]:
        """获取今日摘要"""
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 今日记录数
        bp_count = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id,
            BloodPressureRecord.measured_at >= today_start,
            BloodPressureRecord.measured_at <= today_end
        ).count()
        
        glucose_count = self.db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == self.user_id,
            GlucoseRecord.measured_at >= today_start,
            GlucoseRecord.measured_at <= today_end
        ).count()
        
        weight_today = self.db.query(WeightRecord).filter(
            WeightRecord.user_id == self.user_id,
            WeightRecord.measured_at >= today_start,
            WeightRecord.measured_at <= today_end
        ).first()
        
        # 睡眠
        sleep_today = self.db.query(SleepRecord).filter(
            SleepRecord.user_id == self.user_id,
            SleepRecord.date == today
        ).first()
        
        # 用药完成率
        med_stats = self._get_medication_stats(today)
        
        # 目标打卡
        goal_checkins = self.db.query(GoalCheckIn).filter(
            GoalCheckIn.date == today
        ).count()
        
        return {
            "date": today.isoformat(),
            "records": {
                "blood_pressure": bp_count,
                "glucose": glucose_count,
                "weight": weight_today.weight_kg if weight_today else None,
                "sleep_duration": sleep_today.duration_hours if sleep_today else None,
                "sleep_quality": sleep_today.quality_score if sleep_today else None
            },
            "medication": med_stats,
            "goal_checkins": goal_checkins,
            "completion_status": self._calculate_completion_status(
                bp_count, glucose_count, weight_today, med_stats, sleep_today
            )
        }
    
    def get_quick_actions(self) -> List[Dict[str, Any]]:
        """获取快捷操作"""
        actions = []
        
        # 常用记录类型
        actions.append({
            "id": "add_bp",
            "title": "记录血压",
            "icon": "activity",
            "action": "/records/bp/add",
            "color": "red"
        })
        
        actions.append({
            "id": "add_glucose",
            "title": "记录血糖",
            "icon": "droplet",
            "action": "/records/glucose/add",
            "color": "blue"
        })
        
        actions.append({
            "id": "add_weight",
            "title": "记录体重",
            "icon": "scale",
            "action": "/records/weight/add",
            "color": "green"
        })
        
        actions.append({
            "id": "add_sleep",
            "title": "记录睡眠",
            "icon": "moon",
            "action": "/records/sleep/add",
            "color": "purple"
        })
        
        # 检查今日是否已记录体重
        today = date.today()
        has_weight_today = self.db.query(WeightRecord).filter(
            WeightRecord.user_id == self.user_id,
            func.date(WeightRecord.measured_at) == today
        ).first()
        
        if not has_weight_today:
            actions.append({
                "id": "remind_weight",
                "title": "今日未称重",
                "icon": "bell",
                "action": "/records/weight/add",
                "color": "orange",
                "is_reminder": True
            })
        
        return actions
    
    def get_weekly_stats(self) -> Dict[str, Any]:
        """获取本周统计"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_dates = [week_start + timedelta(days=i) for i in range(7)]
        
        # 计算本周各项指标平均
        week_start_dt = datetime.combine(week_start, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 血压平均
        bp_records = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id,
            BloodPressureRecord.measured_at >= week_start_dt,
            BloodPressureRecord.measured_at <= today_end
        ).all()
        
        avg_systolic = sum(r.systolic for r in bp_records) / len(bp_records) if bp_records else None
        avg_diastolic = sum(r.diastolic for r in bp_records) / len(bp_records) if bp_records else None
        
        # 血糖平均
        glucose_records = self.db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == self.user_id,
            GlucoseRecord.measured_at >= week_start_dt,
            GlucoseRecord.measured_at <= today_end
        ).all()
        
        avg_glucose = sum(r.value for r in glucose_records) / len(glucose_records) if glucose_records else None
        
        # 体重变化
        weight_records = self.db.query(WeightRecord).filter(
            WeightRecord.user_id == self.user_id
        ).order_by(WeightRecord.measured_at).all()
        
        weight_change = None
        if len(weight_records) >= 2:
            # 本周最新 vs 上周
            week_weights = [r for r in weight_records if r.measured_at >= week_start_dt]
            if week_weights and len(weight_records) >= len(week_weights) + 1:
                week_avg = sum(w.weight_kg for w in week_weights) / len(week_weights)
                prev_record = weight_records[-len(week_weights) - 1]
                weight_change = week_avg - prev_record.weight_kg
        
        # 睡眠平均
        sleep_records = self.db.query(SleepRecord).filter(
            SleepRecord.user_id == self.user_id,
            SleepRecord.date >= week_start,
            SleepRecord.date <= today
        ).all()
        
        avg_sleep = sum(s.duration_hours for s in sleep_records) / len(sleep_records) if sleep_records else None
        
        # 用药依从性
        med_logs_week = self.db.query(MedicationLog).join(Medication).filter(
            Medication.user_id == self.user_id,
            MedicationLog.taken_at >= week_start_dt,
            MedicationLog.taken_at <= today_end,
            MedicationLog.status == "taken"
        ).count()
        
        return {
            "week_start": week_start.isoformat(),
            "week_end": today.isoformat(),
            "blood_pressure": {
                "avg_systolic": round(avg_systolic, 1) if avg_systolic else None,
                "avg_diastolic": round(avg_diastolic, 1) if avg_diastolic else None,
                "record_count": len(bp_records)
            },
            "glucose": {
                "avg_value": round(avg_glucose, 1) if avg_glucose else None,
                "record_count": len(glucose_records)
            },
            "weight": {
                "change_kg": round(weight_change, 2) if weight_change else None,
                "change_direction": "down" if weight_change and weight_change < 0 else "up" if weight_change and weight_change > 0 else "stable"
            },
            "sleep": {
                "avg_hours": round(avg_sleep, 1) if avg_sleep else None,
                "record_count": len(sleep_records)
            },
            "medication": {
                "taken_count": med_logs_week
            }
        }
    
    # ==================== 私有辅助方法 ====================
    
    def _get_user_summary(self) -> Dict[str, Any]:
        """获取用户摘要"""
        user = self.db.query(User).filter(User.id == self.user_id).first()
        
        if not user:
            return {}
        
        return {
            "username": user.username,
            "avatar": user.avatar,
            "member_since": user.created_at.isoformat() if user.created_at else None,
            "health_score": self._calculate_health_score(),
            "streak_days": self._get_record_streak()
        }
    
    def _calculate_health_score(self) -> int:
        """计算健康评分 (0-100)"""
        score = 70  # 基础分
        
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        # 记录频率加分
        bp_week = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id,
            BloodPressureRecord.measured_at >= week_ago
        ).count()
        
        if bp_week >= 7:
            score += 10
        elif bp_week >= 3:
            score += 5
        
        # 用药依从性加分
        med_adherence = self._get_medication_adherence(week_ago, today)
        if med_adherence >= 0.9:
            score += 10
        elif med_adherence >= 0.7:
            score += 5
        
        # 目标完成加分
        goals = self.db.query(HealthGoal).filter(
            HealthGoal.user_id == self.user_id,
            HealthGoal.status == "active"
        ).all()
        
        if goals:
            avg_progress = sum(g.progress_percentage for g in goals) / len(goals)
            if avg_progress >= 80:
                score += 10
            elif avg_progress >= 50:
                score += 5
        
        return min(100, max(0, score))
    
    def _get_record_streak(self) -> int:
        """获取连续记录天数"""
        # 简化实现：检查最近30天有多少天有记录
        streak = 0
        today = date.today()
        
        for i in range(30):
            check_date = today - timedelta(days=i)
            has_record = self.db.query(BloodPressureRecord).filter(
                BloodPressureRecord.user_id == self.user_id,
                func.date(BloodPressureRecord.measured_at) == check_date
            ).first()
            
            if has_record:
                streak += 1
            else:
                break
        
        return streak
    
    def _get_today_overview(self) -> Dict[str, Any]:
        """获取今日概览"""
        return self.get_today_summary()
    
    def _get_today_tasks(self) -> List[Dict[str, Any]]:
        """获取今日任务列表"""
        tasks = []
        today = date.today()
        now = datetime.now()
        
        # 1. 今日用药提醒
        meds = self.db.query(Medication).filter(
            Medication.user_id == self.user_id,
            Medication.is_active == True
        ).all()
        
        for med in meds:
            # 检查今天是否已服用
            today_start = datetime.combine(today, datetime.min.time())
            taken_today = self.db.query(MedicationLog).filter(
                MedicationLog.medication_id == med.id,
                MedicationLog.taken_at >= today_start,
                MedicationLog.status == "taken"
            ).first()
            
            if not taken_today:
                tasks.append({
                    "id": f"med_{med.id}",
                    "type": "medication",
                    "title": f"服用 {med.name}",
                    "description": med.dosage,
                    "due_time": "09:00",  # 简化
                    "priority": "high" if med.is_essential else "normal",
                    "completed": False
                })
        
        # 2. 目标打卡提醒
        goals = self.db.query(HealthGoal).filter(
            HealthGoal.user_id == self.user_id,
            HealthGoal.status == "active"
        ).all()
        
        for goal in goals:
            # 检查今天是否已打卡
            checked_in = self.db.query(GoalCheckIn).filter(
                GoalCheckIn.goal_id == goal.id,
                GoalCheckIn.date == today
            ).first()
            
            if not checked_in:
                tasks.append({
                    "id": f"goal_{goal.id}",
                    "type": "goal",
                    "title": f"打卡: {goal.title}",
                    "description": f"目标: {goal.target_value}{goal.unit}",
                    "priority": "normal",
                    "completed": False
                })
        
        # 3. 记录提醒
        has_bp_today = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id,
            func.date(BloodPressureRecord.measured_at) == today
        ).first()
        
        if not has_bp_today:
            tasks.append({
                "id": "record_bp",
                "type": "record",
                "title": "记录今日血压",
                "description": "建议早晚各测一次",
                "priority": "low",
                "completed": False
            })
        
        return tasks
    
    def _get_recent_trends(self, days: int = 7) -> Dict[str, Any]:
        """获取近期趋势"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return {
            "blood_pressure": self._get_bp_trend(start_date, end_date),
            "weight": self._get_weight_trend(start_date, end_date),
            "glucose": self._get_glucose_trend(start_date, end_date),
            "sleep": self._get_sleep_trend(start_date, end_date)
        }
    
    def _get_bp_trend(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取血压趋势"""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        records = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id,
            BloodPressureRecord.measured_at >= start_dt,
            BloodPressureRecord.measured_at <= end_dt
        ).order_by(BloodPressureRecord.measured_at).all()
        
        if not records:
            return {"has_data": False}
        
        data_points = [
            {
                "date": r.measured_at.strftime("%Y-%m-%d"),
                "systolic": r.systolic,
                "diastolic": r.diastolic
            }
            for r in records
        ]
        
        return {
            "has_data": True,
            "data_points": data_points,
            "avg_systolic": round(sum(r.systolic for r in records) / len(records), 1),
            "avg_diastolic": round(sum(r.diastolic for r in records) / len(records), 1),
            "trend": "improving" if records[-1].systolic < records[0].systolic else "stable" if records[-1].systolic == records[0].systolic else "worsening"
        }
    
    def _get_weight_trend(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取体重趋势"""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        records = self.db.query(WeightRecord).filter(
            WeightRecord.user_id == self.user_id,
            WeightRecord.measured_at >= start_dt,
            WeightRecord.measured_at <= end_dt
        ).order_by(WeightRecord.measured_at).all()
        
        if len(records) < 2:
            return {"has_data": False}
        
        change = records[-1].weight_kg - records[0].weight_kg
        
        return {
            "has_data": True,
            "start_weight": records[0].weight_kg,
            "current_weight": records[-1].weight_kg,
            "change_kg": round(change, 2),
            "trend": "decreasing" if change < 0 else "stable" if change == 0 else "increasing"
        }
    
    def _get_glucose_trend(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取血糖趋势"""
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        records = self.db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == self.user_id,
            GlucoseRecord.measured_at >= start_dt,
            GlucoseRecord.measured_at <= end_dt
        ).all()
        
        if not records:
            return {"has_data": False}
        
        return {
            "has_data": True,
            "avg_value": round(sum(r.value for r in records) / len(records), 1),
            "record_count": len(records)
        }
    
    def _get_sleep_trend(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取睡眠趋势"""
        records = self.db.query(SleepRecord).filter(
            SleepRecord.user_id == self.user_id,
            SleepRecord.date >= start_date,
            SleepRecord.date <= end_date
        ).all()
        
        if not records:
            return {"has_data": False}
        
        return {
            "has_data": True,
            "avg_duration": round(sum(r.duration_hours for r in records) / len(records), 1),
            "avg_quality": round(sum(r.quality_score or 0 for r in records) / len(records)) if records else None
        }
    
    def _get_active_goals(self) -> List[Dict[str, Any]]:
        """获取活跃目标进度"""
        goals = self.db.query(HealthGoal).filter(
            HealthGoal.user_id == self.user_id,
            HealthGoal.status.in_(["active", "in_progress"])
        ).limit(3).all()
        
        result = []
        for goal in goals:
            result.append({
                "id": goal.id,
                "title": goal.title,
                "category": goal.category,
                "progress_percentage": goal.progress_percentage,
                "current_value": goal.current_value,
                "target_value": goal.target_value,
                "unit": goal.unit,
                "deadline": goal.deadline.isoformat() if goal.deadline else None,
                "days_remaining": (goal.deadline - date.today()).days if goal.deadline else None
            })
        
        return result
    
    def _get_recent_records(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近记录"""
        records = []
        
        # 获取各类型的最近记录
        bp = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id
        ).order_by(desc(BloodPressureRecord.measured_at)).first()
        
        if bp:
            records.append({
                "type": "blood_pressure",
                "title": "血压",
                "value": f"{bp.systolic}/{bp.diastolic}",
                "unit": "mmHg",
                "time": bp.measured_at.isoformat(),
                "status": bp.status
            })
        
        glucose = self.db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == self.user_id
        ).order_by(desc(GlucoseRecord.measured_at)).first()
        
        if glucose:
            records.append({
                "type": "glucose",
                "title": "血糖",
                "value": glucose.value,
                "unit": "mmol/L",
                "time": glucose.measured_at.isoformat(),
                "note": glucose.note
            })
        
        weight = self.db.query(WeightRecord).filter(
            WeightRecord.user_id == self.user_id
        ).order_by(desc(WeightRecord.measured_at)).first()
        
        if weight:
            records.append({
                "type": "weight",
                "title": "体重",
                "value": weight.weight_kg,
                "unit": "kg",
                "time": weight.measured_at.isoformat(),
                "bmi": weight.bmi
            })
        
        # 按时间排序
        records.sort(key=lambda x: x["time"], reverse=True)
        
        return records[:limit]
    
    def _get_health_alerts(self) -> List[Dict[str, Any]]:
        """获取健康警报"""
        alerts = []
        
        # 检查最近是否有异常记录
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # 高血压警报
        high_bp = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id,
            BloodPressureRecord.systolic >= 140,
            BloodPressureRecord.measured_at >= week_ago
        ).first()
        
        if high_bp:
            alerts.append({
                "type": "warning",
                "title": "血压偏高",
                "message": f"最近血压 {high_bp.systolic}/{high_bp.diastolic} mmHg，请注意",
                "action": "/analysis/anomalies",
                "priority": "high"
            })
        
        # 高血糖警报
        high_glucose = self.db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == self.user_id,
            GlucoseRecord.value > 11.1,
            GlucoseRecord.measured_at >= week_ago
        ).first()
        
        if high_glucose:
            alerts.append({
                "type": "warning",
                "title": "血糖偏高",
                "message": "检测到高血糖记录，建议复查",
                "action": "/analysis/anomalies",
                "priority": "medium"
            })
        
        return alerts
    
    def _get_ai_insights(self) -> List[Dict[str, Any]]:
        """获取AI健康洞察"""
        insights = []
        
        # 基于最近的体重变化生成洞察
        weight_trend = self._get_recent_trends(7).get("weight", {})
        
        if weight_trend.get("has_data"):
            if weight_trend.get("change_kg", 0) < -0.5:
                insights.append({
                    "type": "positive",
                    "title": "体重管理不错",
                    "message": f"本周体重下降 {abs(weight_trend['change_kg'])}kg，继续保持！"
                })
            elif weight_trend.get("change_kg", 0) > 0.5:
                insights.append({
                    "type": "suggestion",
                    "title": "关注体重变化",
                    "message": "本周体重有上升趋势，建议注意饮食和运动"
                })
        
        # 基于记录频率生成洞察
        streak = self._get_record_streak()
        if streak >= 7:
            insights.append({
                "type": "achievement",
                "title": "坚持记录",
                "message": f"已连续记录 {streak} 天，好习惯！"
            })
        
        return insights
    
    def _get_medication_stats(self, for_date: date) -> Dict[str, Any]:
        """获取用药统计"""
        today_start = datetime.combine(for_date, datetime.min.time())
        today_end = datetime.combine(for_date, datetime.max.time())
        
        # 今日应服
        meds = self.db.query(Medication).filter(
            Medication.user_id == self.user_id,
            Medication.is_active == True
        ).all()
        
        total_doses = len(meds)  # 简化，假设每天一次
        
        # 今日已服
        taken = self.db.query(MedicationLog).join(Medication).filter(
            Medication.user_id == self.user_id,
            MedicationLog.taken_at >= today_start,
            MedicationLog.taken_at <= today_end,
            MedicationLog.status == "taken"
        ).count()
        
        return {
            "total": total_doses,
            "taken": taken,
            "completion_rate": round(taken / total_doses * 100, 1) if total_doses > 0 else 100
        }
    
    def _get_medication_adherence(self, start_date: date, end_date: date) -> float:
        """计算用药依从性"""
        # 简化实现
        return 0.85  # 85%依从性作为示例
    
    def _calculate_completion_status(self, bp_count: int, glucose_count: int,
                                     weight: Optional[WeightRecord],
                                     med_stats: Dict, sleep: Optional[SleepRecord]) -> str:
        """计算今日完成状态"""
        completed = 0
        total = 4  # BP, glucose, weight, sleep
        
        if bp_count > 0:
            completed += 1
        if glucose_count > 0:
            completed += 1
        if weight:
            completed += 1
        if sleep:
            completed += 1
        
        if completed == total:
            return "completed"
        elif completed >= total / 2:
            return "good"
        else:
            return "incomplete"


# 便捷函数
def get_dashboard_data(db: Session, user_id: int) -> Dict[str, Any]:
    """获取仪表盘数据便捷函数"""
    service = DashboardService(db, user_id)
    return service.get_dashboard_data()
