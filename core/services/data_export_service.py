"""
🌸 若曦V2 - 健康数据导出服务
支持JSON、CSV、PDF格式的数据导出
提供完整的数据备份与恢复功能
"""

import csv
import io
import json
import logging
import tempfile
import zipfile
from datetime import datetime, timedelta
from typing import Any, BinaryIO, Dict, List, Optional

from models.database import (
    BloodPressureRecord,
    CheckupRecord,
    GlucoseRecord,
    GoalCheckIn,
    HealthGoal,
    HealthReport,
    HeartRateRecord,
    Medication,
    MedicationLog,
    MedicationSchedule,
    Notification,
    SleepRecord,
    User,
    WeightRecord,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from config.config import settings

logger = logging.getLogger(__name__)


class DataExportService:
    """
    健康数据导出服务

    支持:
    - JSON格式导出 (机器可读)
    - CSV格式导出 (表格分析)
    - PDF报告导出 (可视化)
    - ZIP批量导出 (完整备份)
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.user = self.db.query(User).filter(User.id == user_id).first()

    def export_all_data(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        导出所有健康数据

        Args:
            format: json, csv, or zip
            start_date: 开始日期过滤
            end_date: 结束日期过滤
        """
        if format == "json":
            return self._export_json(start_date, end_date)
        elif format == "csv":
            return self._export_csv_zip(start_date, end_date)
        elif format == "zip":
            return self._export_full_backup(start_date, end_date)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _export_json(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """导出为JSON格式"""
        data = {
            "export_metadata": {
                "version": "2.0",
                "exported_at": datetime.utcnow().isoformat(),
                "user_id": self.user_id,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                },
            },
            "user_profile": self._get_user_profile(),
            "health_records": self._get_health_records(start_date, end_date),
            "medications": self._get_medications(start_date, end_date),
            "goals": self._get_goals(start_date, end_date),
            "reports": self._get_reports(start_date, end_date),
            "notifications": self._get_notifications(start_date, end_date),
        }

        return {
            "format": "json",
            "filename": f"health_data_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "data": data,
            "record_count": self._count_records(data),
        }

    def _export_csv_zip(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """导出为多个CSV文件的ZIP包"""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 血压记录
            bp_csv = self._export_bp_csv(start_date, end_date)
            if bp_csv:
                zip_file.writestr("blood_pressure.csv", bp_csv)

            # 血糖记录
            glucose_csv = self._export_glucose_csv(start_date, end_date)
            if glucose_csv:
                zip_file.writestr("glucose.csv", glucose_csv)

            # 体重记录
            weight_csv = self._export_weight_csv(start_date, end_date)
            if weight_csv:
                zip_file.writestr("weight.csv", weight_csv)

            # 心率记录
            hr_csv = self._export_hr_csv(start_date, end_date)
            if hr_csv:
                zip_file.writestr("heart_rate.csv", hr_csv)

            # 睡眠记录
            sleep_csv = self._export_sleep_csv(start_date, end_date)
            if sleep_csv:
                zip_file.writestr("sleep.csv", sleep_csv)

            # 用药记录
            med_csv = self._export_medication_csv(start_date, end_date)
            if med_csv:
                zip_file.writestr("medications.csv", med_csv)

            # 导出说明
            readme = self._generate_export_readme()
            zip_file.writestr("README.txt", readme)

        zip_buffer.seek(0)

        return {
            "format": "csv_zip",
            "filename": f"health_data_csv_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            "data": zip_buffer.getvalue(),
            "content_type": "application/zip",
        }

    def _export_full_backup(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """导出完整备份（JSON + CSV + 元数据）"""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # JSON数据
            json_data = self._export_json(start_date, end_date)
            zip_file.writestr(
                "data/health_data.json",
                json.dumps(json_data["data"], ensure_ascii=False, indent=2),
            )

            # CSV数据
            bp_csv = self._export_bp_csv(start_date, end_date)
            if bp_csv:
                zip_file.writestr("csv/blood_pressure.csv", bp_csv)

            glucose_csv = self._export_glucose_csv(start_date, end_date)
            if glucose_csv:
                zip_file.writestr("csv/glucose.csv", glucose_csv)

            weight_csv = self._export_weight_csv(start_date, end_date)
            if weight_csv:
                zip_file.writestr("csv/weight.csv", weight_csv)

            # 元数据
            metadata = {
                "export_date": datetime.utcnow().isoformat(),
                "user_id": self.user_id,
                "version": "2.0",
                "record_count": json_data["record_count"],
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                },
            }
            zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

            # 恢复说明
            restore_guide = self._generate_restore_guide()
            zip_file.writestr("RESTORE_GUIDE.md", restore_guide)

        zip_buffer.seek(0)

        return {
            "format": "full_backup",
            "filename": f"ruoxi_backup_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            "data": zip_buffer.getvalue(),
            "content_type": "application/zip",
            "record_count": json_data["record_count"],
        }

    # ==================== CSV导出辅助方法 ====================

    def _export_bp_csv(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Optional[str]:
        """导出血压记录为CSV"""
        query = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id
        )
        if start_date:
            query = query.filter(BloodPressureRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(BloodPressureRecord.measured_at <= end_date)

        records = query.order_by(BloodPressureRecord.measured_at).all()

        if not records:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["记录时间", "收缩压(mmHg)", "舒张压(mmHg)", "心率", "状态", "备注"]
        )

        for r in records:
            writer.writerow(
                [
                    r.measured_at.strftime("%Y-%m-%d %H:%M"),
                    r.systolic,
                    r.diastolic,
                    r.heart_rate or "",
                    r.status or "",
                    r.note or "",
                ]
            )

        return output.getvalue()

    def _export_glucose_csv(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Optional[str]:
        """导出血糖记录为CSV"""
        query = self.db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == self.user_id
        )
        if start_date:
            query = query.filter(GlucoseRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(GlucoseRecord.measured_at <= end_date)

        records = query.order_by(GlucoseRecord.measured_at).all()

        if not records:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["记录时间", "血糖值(mmol/L)", "测量类型", "备注"])

        meal_type_map = {
            "fasting": "空腹",
            "before_meal": "餐前",
            "after_meal": "餐后2小时",
            "random": "随机",
        }

        for r in records:
            writer.writerow(
                [
                    r.measured_at.strftime("%Y-%m-%d %H:%M"),
                    r.value,
                    meal_type_map.get(r.meal_type, r.meal_type),
                    r.note or "",
                ]
            )

        return output.getvalue()

    def _export_weight_csv(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Optional[str]:
        """导出体重记录为CSV"""
        query = self.db.query(WeightRecord).filter(WeightRecord.user_id == self.user_id)
        if start_date:
            query = query.filter(WeightRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(WeightRecord.measured_at <= end_date)

        records = query.order_by(WeightRecord.measured_at).all()

        if not records:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["记录时间", "体重(kg)", "BMI", "体脂率(%)", "备注"])

        for r in records:
            writer.writerow(
                [
                    r.measured_at.strftime("%Y-%m-%d %H:%M"),
                    r.weight_kg,
                    r.bmi or "",
                    r.body_fat_percentage or "",
                    r.note or "",
                ]
            )

        return output.getvalue()

    def _export_hr_csv(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Optional[str]:
        """导出心率记录为CSV"""
        query = self.db.query(HeartRateRecord).filter(
            HeartRateRecord.user_id == self.user_id
        )
        if start_date:
            query = query.filter(HeartRateRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(HeartRateRecord.measured_at <= end_date)

        records = query.order_by(HeartRateRecord.measured_at).all()

        if not records:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["记录时间", "心率(bpm)", "活动状态", "备注"])

        activity_map = {
            "resting": "静息",
            "light": "轻度活动",
            "moderate": "中度活动",
            "intense": "剧烈运动",
        }

        for r in records:
            writer.writerow(
                [
                    r.measured_at.strftime("%Y-%m-%d %H:%M"),
                    r.bpm,
                    activity_map.get(r.activity, r.activity),
                    r.note or "",
                ]
            )

        return output.getvalue()

    def _export_sleep_csv(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Optional[str]:
        """导出睡眠记录为CSV"""
        query = self.db.query(SleepRecord).filter(SleepRecord.user_id == self.user_id)
        if start_date:
            query = query.filter(SleepRecord.date >= start_date.date())
        if end_date:
            query = query.filter(SleepRecord.date <= end_date.date())

        records = query.order_by(SleepRecord.date).all()

        if not records:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "日期",
                "睡眠时长(小时)",
                "睡眠评分",
                "入睡时间",
                "起床时间",
                "深睡(%)",
                "浅睡(%)",
                "REM(%)",
            ]
        )

        for r in records:
            writer.writerow(
                [
                    r.date.strftime("%Y-%m-%d"),
                    r.duration_hours,
                    r.quality_score or "",
                    r.bedtime.strftime("%H:%M") if r.bedtime else "",
                    r.wake_time.strftime("%H:%M") if r.wake_time else "",
                    r.deep_sleep_percentage or "",
                    r.light_sleep_percentage or "",
                    r.rem_sleep_percentage or "",
                ]
            )

        return output.getvalue()

    def _export_medication_csv(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Optional[str]:
        """导出用药记录为CSV"""
        # 用药日志
        query = (
            self.db.query(MedicationLog)
            .join(Medication)
            .filter(Medication.user_id == self.user_id)
        )
        if start_date:
            query = query.filter(MedicationLog.taken_at >= start_date)
        if end_date:
            query = query.filter(MedicationLog.taken_at <= end_date)

        logs = query.order_by(MedicationLog.taken_at).all()

        if not logs:
            return None

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["服药时间", "药品名称", "剂量", "状态", "备注"])

        for log in logs:
            writer.writerow(
                [
                    log.taken_at.strftime("%Y-%m-%d %H:%M"),
                    log.medication.name if log.medication else "",
                    log.dose_taken or "",
                    log.status,
                    log.note or "",
                ]
            )

        return output.getvalue()

    # ==================== JSON数据获取 ====================

    def _get_user_profile(self) -> Dict[str, Any]:
        """获取用户档案（脱敏）"""
        if not self.user:
            return {}

        return {
            "username": self.user.username,
            "age": self.user.age,
            "gender": self.user.gender,
            "height_cm": self.user.height_cm,
            "weight_kg": self.user.weight_kg,
            "blood_type": self.user.blood_type,
            "chronic_conditions": self.user.chronic_conditions or [],
        }

    def _get_health_records(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Dict[str, List]:
        """获取健康记录"""
        records = {
            "blood_pressure": [],
            "glucose": [],
            "weight": [],
            "heart_rate": [],
            "sleep": [],
        }

        # 血压
        bp_query = self.db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == self.user_id
        )
        if start_date:
            bp_query = bp_query.filter(BloodPressureRecord.measured_at >= start_date)
        if end_date:
            bp_query = bp_query.filter(BloodPressureRecord.measured_at <= end_date)

        for r in bp_query.all():
            records["blood_pressure"].append(
                {
                    "measured_at": r.measured_at.isoformat(),
                    "systolic": r.systolic,
                    "diastolic": r.diastolic,
                    "heart_rate": r.heart_rate,
                    "status": r.status,
                    "note": r.note,
                }
            )

        # 血糖
        glucose_query = self.db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == self.user_id
        )
        if start_date:
            glucose_query = glucose_query.filter(
                GlucoseRecord.measured_at >= start_date
            )
        if end_date:
            glucose_query = glucose_query.filter(GlucoseRecord.measured_at <= end_date)

        for r in glucose_query.all():
            records["glucose"].append(
                {
                    "measured_at": r.measured_at.isoformat(),
                    "value": r.value,
                    "meal_type": r.meal_type,
                    "note": r.note,
                }
            )

        # 体重
        weight_query = self.db.query(WeightRecord).filter(
            WeightRecord.user_id == self.user_id
        )
        if start_date:
            weight_query = weight_query.filter(WeightRecord.measured_at >= start_date)
        if end_date:
            weight_query = weight_query.filter(WeightRecord.measured_at <= end_date)

        for r in weight_query.all():
            records["weight"].append(
                {
                    "measured_at": r.measured_at.isoformat(),
                    "weight_kg": r.weight_kg,
                    "bmi": r.bmi,
                    "body_fat_percentage": r.body_fat_percentage,
                    "note": r.note,
                }
            )

        # 心率
        hr_query = self.db.query(HeartRateRecord).filter(
            HeartRateRecord.user_id == self.user_id
        )
        if start_date:
            hr_query = hr_query.filter(HeartRateRecord.measured_at >= start_date)
        if end_date:
            hr_query = hr_query.filter(HeartRateRecord.measured_at <= end_date)

        for r in hr_query.all():
            records["heart_rate"].append(
                {
                    "measured_at": r.measured_at.isoformat(),
                    "bpm": r.bpm,
                    "activity": r.activity,
                    "note": r.note,
                }
            )

        # 睡眠
        sleep_query = self.db.query(SleepRecord).filter(
            SleepRecord.user_id == self.user_id
        )
        if start_date:
            sleep_query = sleep_query.filter(SleepRecord.date >= start_date.date())
        if end_date:
            sleep_query = sleep_query.filter(SleepRecord.date <= end_date.date())

        for r in sleep_query.all():
            records["sleep"].append(
                {
                    "date": r.date.isoformat(),
                    "duration_hours": r.duration_hours,
                    "quality_score": r.quality_score,
                    "bedtime": r.bedtime.isoformat() if r.bedtime else None,
                    "wake_time": r.wake_time.isoformat() if r.wake_time else None,
                    "deep_sleep_percentage": r.deep_sleep_percentage,
                    "light_sleep_percentage": r.light_sleep_percentage,
                    "rem_sleep_percentage": r.rem_sleep_percentage,
                }
            )

        return records

    def _get_medications(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Dict[str, List]:
        """获取用药数据"""
        medications = []

        meds = (
            self.db.query(Medication).filter(Medication.user_id == self.user_id).all()
        )

        for m in meds:
            med_data = {
                "id": m.id,
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "purpose": m.purpose,
                "start_date": m.start_date.isoformat() if m.start_date else None,
                "end_date": m.end_date.isoformat() if m.end_date else None,
                "is_active": m.is_active,
                "logs": [],
            }

            # 获取用药日志
            logs_query = self.db.query(MedicationLog).filter(
                MedicationLog.medication_id == m.id
            )
            if start_date:
                logs_query = logs_query.filter(MedicationLog.taken_at >= start_date)
            if end_date:
                logs_query = logs_query.filter(MedicationLog.taken_at <= end_date)

            for log in logs_query.all():
                med_data["logs"].append(
                    {
                        "taken_at": log.taken_at.isoformat(),
                        "dose_taken": log.dose_taken,
                        "status": log.status,
                        "note": log.note,
                    }
                )

            medications.append(med_data)

        return {"medications": medications}

    def _get_goals(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Dict[str, List]:
        """获取健康目标"""
        goals = []

        query = self.db.query(HealthGoal).filter(HealthGoal.user_id == self.user_id)

        if start_date:
            query = query.filter(HealthGoal.created_at >= start_date)
        if end_date:
            query = query.filter(HealthGoal.created_at <= end_date)

        for g in query.all():
            goal_data = {
                "id": g.id,
                "title": g.title,
                "category": g.category,
                "target_value": g.target_value,
                "current_value": g.current_value,
                "unit": g.unit,
                "start_date": g.start_date.isoformat() if g.start_date else None,
                "deadline": g.deadline.isoformat() if g.deadline else None,
                "status": g.status,
                "progress_percentage": g.progress_percentage,
                "check_ins": [],
            }

            # 获取打卡记录
            for ci in g.check_ins:
                goal_data["check_ins"].append(
                    {
                        "date": ci.date.isoformat(),
                        "value": ci.value,
                        "note": ci.note,
                        "completed": ci.completed,
                    }
                )

            goals.append(goal_data)

        return {"goals": goals}

    def _get_reports(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Dict[str, List]:
        """获取健康报告"""
        reports = []

        query = self.db.query(HealthReport).filter(HealthReport.user_id == self.user_id)

        if start_date:
            query = query.filter(HealthReport.generated_at >= start_date)
        if end_date:
            query = query.filter(HealthReport.generated_at <= end_date)

        for r in query.all():
            reports.append(
                {
                    "id": r.id,
                    "title": r.title,
                    "type": r.type,
                    "generated_at": r.generated_at.isoformat(),
                    "period_days": r.period_days,
                    "key_findings": r.key_findings or [],
                    "download_url": r.file_path,
                }
            )

        return {"reports": reports}

    def _get_notifications(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> Dict[str, List]:
        """获取通知历史"""
        notifications = []

        query = self.db.query(Notification).filter(Notification.user_id == self.user_id)

        if start_date:
            query = query.filter(Notification.created_at >= start_date)
        if end_date:
            query = query.filter(Notification.created_at <= end_date)

        for n in query.order_by(desc(Notification.created_at)).limit(100).all():
            notifications.append(
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "content": n.content,
                    "priority": n.priority,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
            )

        return {"notifications": notifications}

    def _count_records(self, data: Dict) -> int:
        """统计记录总数"""
        count = 0

        health = data.get("health_records", {})
        count += len(health.get("blood_pressure", []))
        count += len(health.get("glucose", []))
        count += len(health.get("weight", []))
        count += len(health.get("heart_rate", []))
        count += len(health.get("sleep", []))

        meds = data.get("medications", {})
        for m in meds.get("medications", []):
            count += len(m.get("logs", []))

        goals = data.get("goals", {})
        count += len(goals.get("goals", []))

        return count

    def _generate_export_readme(self) -> str:
        """生成导出说明"""
        return f"""若曦V2 健康数据导出
==================

导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
用户ID: {self.user_id}

文件说明:
- blood_pressure.csv: 血压记录
- glucose.csv: 血糖记录
- weight.csv: 体重记录
- heart_rate.csv: 心率记录
- sleep.csv: 睡眠记录
- medications.csv: 用药记录

所有时间均为本地时间。
如有疑问，请联系客服。
"""

    def _generate_restore_guide(self) -> str:
        """生成恢复指南"""
        return f"""# 若曦V2 数据恢复指南

## 备份内容

此备份包含以下数据:
- data/health_data.json - 完整数据 (JSON格式)
- csv/ - 各类型数据的CSV文件
- metadata.json - 导出元数据

## 如何恢复

### 方式1: 通过Web界面
1. 登录若曦V2
2. 进入 "数据管理" → "导入数据"
3. 选择此ZIP文件
4. 按照提示完成恢复

### 方式2: 命令行 (管理员)
```bash
python scripts/restore_backup.py --file backup.zip --user-id {self.user_id}
```

## 注意事项

1. 恢复操作会合并数据，不会删除现有数据
2. 重复记录会被自动跳过
3. 建议在恢复前创建新的备份
4. 如遇到问题，请联系技术支持

## 数据格式版本

版本: 2.0
兼容: 若曦V2.0+
导出时间: {datetime.utcnow().isoformat()}
"""


# 便捷函数
def export_user_data(
    db: Session,
    user_id: int,
    format: str = "json",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """导出用户数据便捷函数"""
    service = DataExportService(db, user_id)
    return service.export_all_data(format, start_date, end_date)
