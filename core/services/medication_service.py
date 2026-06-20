"""
🌸 若曦V2 - 用药提醒服务层
管理用药提醒、服药记录追踪、依从性分析
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import json

from models.database import (
    User as UserModel,
    Medication,
    MedicationLog,
    Notification
)


class MedicationService:
    """用药管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_medications(self, user_id: int) -> List[Medication]:
        """获取用户当前活跃的用药列表"""
        today = date.today()
        return self.db.query(Medication).filter(
            Medication.user_id == user_id,
            Medication.is_active == True,
            and_(
                Medication.start_date <= today,
                or_(
                    Medication.end_date == None,
                    Medication.end_date >= today
                )
            )
        ).all()
    
    def get_due_medications(self, user_id: int, check_time: datetime) -> List[Dict[str, Any]]:
        """
        获取在当前时间应该提醒的用药
        
        检查逻辑：
        1. 用药是活跃的
        2. 当前时间与用药提醒时间匹配
        3. 今天还没有记录（或记录为跳过）
        """
        current_time = check_time.time()
        today = check_time.date()
        
        # 获取所有活跃用药
        medications = self.get_active_medications(user_id)
        
        due_medications = []
        for med in medications:
            if not med.reminder_enabled or not med.reminder_time:
                continue
            
            # 解析提醒时间
            try:
                reminder_hour, reminder_minute = map(int, med.reminder_time.split(':'))
                reminder_time = time(reminder_hour, reminder_minute)
            except (ValueError, AttributeError):
                continue
            
            # 检查是否在提醒窗口内 (±15分钟)
            current_minutes = current_time.hour * 60 + current_time.minute
            reminder_minutes = reminder_hour * 60 + reminder_minute
            time_diff = abs(current_minutes - reminder_minutes)
            
            if time_diff > 15:
                continue
            
            # 检查今天是否已经服药或跳过
            today_log = self.db.query(MedicationLog).filter(
                MedicationLog.medication_id == med.id,
                func.date(MedicationLog.taken_at) == today
            ).first()
            
            if today_log:
                continue  # 今天已有记录
            
            due_medications.append({
                "medication": med,
                "is_overdue": current_minutes > reminder_minutes + 5,
                "minutes_until": reminder_minutes - current_minutes if current_minutes < reminder_minutes else 0,
                "minutes_overdue": current_minutes - reminder_minutes if current_minutes > reminder_minutes else 0
            })
        
        return due_medications
    
    def create_medication(
        self,
        user_id: int,
        name: str,
        dosage: str,
        frequency: str,
        purpose: Optional[str] = None,
        reminder_time: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Medication:
        """创建新的用药记录"""
        medication = Medication(
            user_id=user_id,
            name=name,
            dosage=dosage,
            frequency=frequency,
            purpose=purpose,
            reminder_time=reminder_time,
            reminder_enabled=reminder_time is not None,
            start_date=start_date or date.today(),
            end_date=end_date,
            is_active=True
        )
        
        self.db.add(medication)
        self.db.commit()
        self.db.refresh(medication)
        
        return medication
    
    def record_medication_taken(
        self,
        medication_id: int,
        user_id: int,
        taken_at: Optional[datetime] = None,
        dosage_taken: Optional[str] = None,
        note: Optional[str] = None
    ) -> MedicationLog:
        """记录服药"""
        log = MedicationLog(
            user_id=user_id,
            medication_id=medication_id,
            taken_at=taken_at or datetime.now(),
            dosage_taken=dosage_taken,
            skipped=False,
            note=note
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def record_medication_skipped(
        self,
        medication_id: int,
        user_id: int,
        reason: Optional[str] = None,
        skip_time: Optional[datetime] = None
    ) -> MedicationLog:
        """记录跳过服药"""
        log = MedicationLog(
            user_id=user_id,
            medication_id=medication_id,
            taken_at=skip_time or datetime.now(),
            skipped=True,
            skip_reason=reason,
            dosage_taken=None
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def get_medication_adherence(
        self,
        user_id: int,
        medication_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        计算用药依从性
        
        依从性 = 实际服药次数 / 应服药次数
        """
        start_date = date.today() - timedelta(days=days)
        
        # 查询条件
        base_query = self.db.query(MedicationLog).join(Medication).filter(
            Medication.user_id == user_id,
            MedicationLog.taken_at >= start_date
        )
        
        if medication_id:
            base_query = base_query.filter(MedicationLog.medication_id == medication_id)
        
        # 实际服药次数
        logs = base_query.all()
        taken_count = sum(1 for log in logs if not log.skipped)
        skipped_count = sum(1 for log in logs if log.skipped)
        
        # 计算应服药次数
        expected_count = 0
        medications_query = self.db.query(Medication).filter(
            Medication.user_id == user_id,
            Medication.is_active == True,
            Medication.start_date <= date.today()
        )
        
        if medication_id:
            medications_query = medications_query.filter(Medication.id == medication_id)
        
        medications = medications_query.all()
        
        for med in medications:
            # 计算在该时间段内应服药次数
            med_start = max(med.start_date or start_date, start_date)
            med_days = (date.today() - med_start).days + 1
            
            # 根据频次估算
            freq = med.frequency or "每日1次"
            if "每日" in freq or "每天" in freq:
                daily_dose = 1
            elif "每周" in freq:
                daily_dose = 1 / 7
            elif "每2" in freq or "隔天" in freq:
                daily_dose = 0.5
            else:
                daily_dose = 1
            
            expected_count += int(med_days * daily_dose)
        
        adherence_rate = (taken_count / expected_count * 100) if expected_count > 0 else 0
        
        return {
            "adherence_rate": round(adherence_rate, 1),
            "taken_count": taken_count,
            "skipped_count": skipped_count,
            "expected_count": expected_count,
            "analysis_days": days,
            "status": self._classify_adherence(adherence_rate),
            "recommendation": self._generate_adherence_recommendation(adherence_rate)
        }
    
    def _classify_adherence(self, rate: float) -> str:
        """依从性分类"""
        if rate >= 95:
            return "excellent"  # 优秀
        elif rate >= 80:
            return "good"  # 良好
        elif rate >= 50:
            return "fair"  # 一般
        else:
            return "poor"  # 需改善
    
    def _generate_adherence_recommendation(self, rate: float) -> str:
        """生成依从性建议"""
        if rate >= 95:
            return "用药依从性优秀，请继续保持！"
        elif rate >= 80:
            return "用药依从性良好，偶尔有遗漏，建议设置提醒或建立固定服药习惯。"
        elif rate >= 50:
            return "用药依从性一般，经常遗漏服药。建议检查用药方案是否过于复杂，或咨询医生调整方案。"
        else:
            return "用药依从性较差，过半药物未按时服用。这可能影响治疗效果，强烈建议与医生讨论简化用药方案或寻找漏服原因。"
    
    def get_medication_schedule(
        self,
        user_id: int,
        target_date: date
    ) -> List[Dict[str, Any]]:
        """获取某日的用药计划"""
        # 获取活跃的用药
        medications = self.db.query(Medication).filter(
            Medication.user_id == user_id,
            Medication.is_active == True,
            Medication.reminder_enabled == True,
            Medication.start_date <= target_date,
            or_(
                Medication.end_date == None,
                Medication.end_date >= target_date
            )
        ).all()
        
        schedule = []
        for med in medications:
            # 检查当天是否已服药
            log = self.db.query(MedicationLog).filter(
                MedicationLog.medication_id == med.id,
                func.date(MedicationLog.taken_at) == target_date
            ).first()
            
            status = "pending"
            taken_at = None
            
            if log:
                if log.skipped:
                    status = "skipped"
                else:
                    status = "taken"
                    taken_at = log.taken_at
            
            schedule.append({
                "medication_id": med.id,
                "name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "reminder_time": med.reminder_time,
                "purpose": med.purpose,
                "status": status,
                "taken_at": taken_at.isoformat() if taken_at else None,
                "log_id": log.id if log else None
            })
        
        # 按提醒时间排序
        schedule.sort(key=lambda x: x["reminder_time"] or "00:00")
        
        return schedule
    
    def detect_missed_doses(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """检测漏服记录"""
        start_date = date.today() - timedelta(days=days)
        
        # 获取期间所有应服药的用药
        medications = self.db.query(Medication).filter(
            Medication.user_id == user_id,
            Medication.is_active == True,
            Medication.reminder_enabled == True,
            Medication.start_date <= date.today(),
            or_(
                Medication.end_date == None,
                Medication.end_date >= start_date
            )
        ).all()
        
        missed_doses = []
        
        for med in medications:
            # 检查每一天
            for i in range(days):
                check_date = date.today() - timedelta(days=i)
                
                # 跳过用药开始前的日期
                if med.start_date and check_date < med.start_date:
                    continue
                
                # 跳过用药结束后的日期
                if med.end_date and check_date > med.end_date:
                    continue
                
                # 检查当天记录
                log = self.db.query(MedicationLog).filter(
                    MedicationLog.medication_id == med.id,
                    func.date(MedicationLog.taken_at) == check_date
                ).first()
                
                # 如果没有记录，且过去的时间，则为漏服
                if not log and check_date < date.today():
                    missed_doses.append({
                        "medication_id": med.id,
                        "name": med.name,
                        "dosage": med.dosage,
                        "date": check_date.isoformat(),
                        "reminder_time": med.reminder_time,
                        "expected_time": f"{check_date} {med.reminder_time}" if med.reminder_time else str(check_date)
                    })
        
        return missed_doses
    
    def get_medication_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用药摘要"""
        # 活跃用药
        active_count = self.db.query(Medication).filter(
            Medication.user_id == user_id,
            Medication.is_active == True
        ).count()
        
        # 今日计划
        today_schedule = self.get_medication_schedule(user_id, date.today())
        
        today_pending = sum(1 for s in today_schedule if s["status"] == "pending")
        today_taken = sum(1 for s in today_schedule if s["status"] == "taken")
        today_skipped = sum(1 for s in today_schedule if s["status"] == "skipped")
        
        # 依从性
        adherence = self.get_medication_adherence(user_id, days=30)
        
        # 漏服检测
        recent_missed = self.detect_missed_doses(user_id, days=3)
        
        return {
            "active_medications": active_count,
            "today_schedule": {
                "total": len(today_schedule),
                "pending": today_pending,
                "taken": today_taken,
                "skipped": today_skipped,
                "completion_rate": round(today_taken / len(today_schedule) * 100, 1) if today_schedule else 0
            },
            "adherence": adherence,
            "recent_missed_count": len(recent_missed),
            "recent_missed": recent_missed[:5]  # 只返回最近5个
        }
    
    def generate_medication_report(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """生成用药报告"""
        report = {
            "period": {
                "start": (date.today() - timedelta(days=days)).isoformat(),
                "end": date.today().isoformat()
            },
            "summary": self.get_medication_summary(user_id),
            "adherence": self.get_medication_adherence(user_id, days=days),
            "missed_doses": self.detect_missed_doses(user_id, days=days),
            "medications": []
        }
        
        # 各用药详细统计
        medications = self.db.query(Medication).filter(
            Medication.user_id == user_id
        ).all()
        
        for med in medications:
            med_stats = self.get_medication_adherence(user_id, med.id, days)
            report["medications"].append({
                "id": med.id,
                "name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "purpose": med.purpose,
                "adherence": med_stats
            })
        
        return report


# 辅助函数
from sqlalchemy import or_