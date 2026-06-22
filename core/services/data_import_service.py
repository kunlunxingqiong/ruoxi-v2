"""
🌸 若曦V2 - 健康数据导入服务
支持从JSON、CSV格式导入数据
提供数据恢复和迁移功能
"""

import csv
import io
import json
import logging
import zipfile
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from models.database import (
    BloodPressureRecord,
    GlucoseRecord,
    GoalCheckIn,
    HealthGoal,
    HeartRateRecord,
    Medication,
    MedicationLog,
    SleepRecord,
    User,
    WeightRecord,
)
from sqlalchemy.orm import Session

from core.services.data_export_service import DataExportService

logger = logging.getLogger(__name__)


class DataImportResult:
    """导入结果"""

    def __init__(self):
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0
        self.errors: List[str] = []
        self.imported_records: List[str] = []

    def add_success(self, record_type: str, record_id: int = None):
        self.success_count += 1
        self.imported_records.append(f"{record_type}:{record_id}")

    def add_skip(self, reason: str):
        self.skip_count += 1
        self.errors.append(f"跳过: {reason}")

    def add_error(self, error: str):
        self.error_count += 1
        self.errors.append(f"错误: {error}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_count": self.success_count,
            "skip_count": self.skip_count,
            "error_count": self.error_count,
            "total": self.success_count + self.skip_count + self.error_count,
            "errors": self.errors[:10],  # 只返回前10个错误
        }


class DataImportService:
    """
    健康数据导入服务

    支持:
    - JSON格式导入
    - CSV格式导入
    - ZIP备份恢复
    - 数据合并和去重
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.result = DataImportResult()

    def import_from_json(
        self, json_data: Dict[str, Any], merge_strategy: str = "skip_duplicates"
    ) -> DataImportResult:
        """
        从JSON导入数据

        Args:
            json_data: JSON格式的数据
            merge_strategy: skip_duplicates/overwrite/append
        """
        self.result = DataImportResult()

        try:
            # 验证数据结构
            if "health_records" in json_data:
                health = json_data["health_records"]
                self._import_blood_pressure(
                    health.get("blood_pressure", []), merge_strategy
                )
                self._import_glucose(health.get("glucose", []), merge_strategy)
                self._import_weight(health.get("weight", []), merge_strategy)
                self._import_heart_rate(health.get("heart_rate", []), merge_strategy)
                self._import_sleep(health.get("sleep", []), merge_strategy)

            # 导入用药数据
            if "medications" in json_data:
                self._import_medications(
                    json_data["medications"].get("medications", []), merge_strategy
                )

            # 导入目标数据
            if "goals" in json_data:
                self._import_goals(json_data["goals"].get("goals", []), merge_strategy)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self.result.add_error(f"导入失败: {str(e)}")
            logger.error(f"数据导入失败: {e}")

        return self.result

    def import_from_csv(
        self, csv_data: str, record_type: str, merge_strategy: str = "skip_duplicates"
    ) -> DataImportResult:
        """从CSV导入数据"""
        self.result = DataImportResult()

        try:
            if record_type == "blood_pressure":
                self._import_bp_csv(csv_data, merge_strategy)
            elif record_type == "glucose":
                self._import_glucose_csv(csv_data, merge_strategy)
            elif record_type == "weight":
                self._import_weight_csv(csv_data, merge_strategy)
            elif record_type == "heart_rate":
                self._import_hr_csv(csv_data, merge_strategy)
            elif record_type == "sleep":
                self._import_sleep_csv(csv_data, merge_strategy)
            else:
                raise ValueError(f"不支持的记录类型: {record_type}")

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self.result.add_error(f"CSV导入失败: {str(e)}")
            logger.error(f"CSV导入失败: {e}")

        return self.result

    def restore_from_backup(self, zip_bytes: bytes) -> DataImportResult:
        """从ZIP备份恢复数据"""
        self.result = DataImportResult()

        try:
            zip_buffer = io.BytesIO(zip_bytes)

            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                # 读取metadata
                metadata_content = zip_file.read("metadata.json")
                metadata = json.loads(metadata_content)

                logger.info(
                    f"恢复备份: 版本 {metadata.get('version')}, "
                    f"记录数 {metadata.get('record_count')}"
                )

                # 读取JSON数据
                if "data/health_data.json" in zip_file.namelist():
                    json_content = zip_file.read("data/health_data.json")
                    json_data = json.loads(json_content)

                    # 执行导入
                    self.import_from_json(json_data, merge_strategy="skip_duplicates")
                else:
                    # 从CSV文件导入
                    for filename in zip_file.namelist():
                        if filename.startswith("csv/") and filename.endswith(".csv"):
                            record_type = filename.replace("csv/", "").replace(
                                ".csv", ""
                            )
                            csv_content = zip_file.read(filename).decode("utf-8")
                            self.import_from_csv(
                                csv_content, record_type, "skip_duplicates"
                            )

        except Exception as e:
            self.result.add_error(f"恢复失败: {str(e)}")
            logger.error(f"恢复备份失败: {e}")

        return self.result

    # ==================== JSON导入辅助方法 ====================

    def _import_blood_pressure(self, records: List[Dict], merge_strategy: str):
        """导入血压记录"""
        for record_data in records:
            try:
                measured_at = datetime.fromisoformat(record_data["measured_at"])

                # 检查是否已存在
                existing = (
                    self.db.query(BloodPressureRecord)
                    .filter(
                        BloodPressureRecord.user_id == self.user_id,
                        BloodPressureRecord.measured_at == measured_at,
                    )
                    .first()
                )

                if existing:
                    if merge_strategy == "skip_duplicates":
                        self.result.add_skip(f"血压记录已存在: {measured_at}")
                        continue
                    elif merge_strategy == "overwrite":
                        self.db.delete(existing)

                record = BloodPressureRecord(
                    user_id=self.user_id,
                    systolic=record_data["systolic"],
                    diastolic=record_data["diastolic"],
                    heart_rate=record_data.get("heart_rate"),
                    measured_at=measured_at,
                    status=record_data.get("status"),
                    note=record_data.get("note"),
                )
                self.db.add(record)
                self.result.add_success("blood_pressure", record.id)

            except Exception as e:
                self.result.add_error(f"血压记录导入失败: {e}")

    def _import_glucose(self, records: List[Dict], merge_strategy: str):
        """导出血糖记录"""
        for record_data in records:
            try:
                measured_at = datetime.fromisoformat(record_data["measured_at"])

                existing = (
                    self.db.query(GlucoseRecord)
                    .filter(
                        GlucoseRecord.user_id == self.user_id,
                        GlucoseRecord.measured_at == measured_at,
                        GlucoseRecord.meal_type
                        == record_data.get("meal_type", "fasting"),
                    )
                    .first()
                )

                if existing:
                    if merge_strategy == "skip_duplicates":
                        self.result.add_skip(f"血糖记录已存在: {measured_at}")
                        continue
                    elif merge_strategy == "overwrite":
                        self.db.delete(existing)

                record = GlucoseRecord(
                    user_id=self.user_id,
                    value=record_data["value"],
                    meal_type=record_data.get("meal_type", "fasting"),
                    measured_at=measured_at,
                    note=record_data.get("note"),
                )
                self.db.add(record)
                self.result.add_success("glucose", record.id)

            except Exception as e:
                self.result.add_error(f"血糖记录导入失败: {e}")

    def _import_weight(self, records: List[Dict], merge_strategy: str):
        """导入体重记录"""
        for record_data in records:
            try:
                measured_at = datetime.fromisoformat(record_data["measured_at"])

                existing = (
                    self.db.query(WeightRecord)
                    .filter(
                        WeightRecord.user_id == self.user_id,
                        WeightRecord.measured_at == measured_at,
                    )
                    .first()
                )

                if existing:
                    if merge_strategy == "skip_duplicates":
                        self.result.add_skip(f"体重记录已存在: {measured_at}")
                        continue
                    elif merge_strategy == "overwrite":
                        existing.weight_kg = record_data["weight_kg"]
                        existing.bmi = record_data.get("bmi")
                        existing.body_fat_percentage = record_data.get(
                            "body_fat_percentage"
                        )
                        self.result.add_success("weight", existing.id)
                        continue

                record = WeightRecord(
                    user_id=self.user_id,
                    weight_kg=record_data["weight_kg"],
                    bmi=record_data.get("bmi"),
                    body_fat_percentage=record_data.get("body_fat_percentage"),
                    measured_at=measured_at,
                    note=record_data.get("note"),
                )
                self.db.add(record)
                self.result.add_success("weight", record.id)

            except Exception as e:
                self.result.add_error(f"体重记录导入失败: {e}")

    def _import_heart_rate(self, records: List[Dict], merge_strategy: str):
        """导入心率记录"""
        for record_data in records:
            try:
                measured_at = datetime.fromisoformat(record_data["measured_at"])

                existing = (
                    self.db.query(HeartRateRecord)
                    .filter(
                        HeartRateRecord.user_id == self.user_id,
                        HeartRateRecord.measured_at == measured_at,
                    )
                    .first()
                )

                if existing:
                    if merge_strategy == "skip_duplicates":
                        self.result.add_skip(f"心率记录已存在: {measured_at}")
                        continue
                    elif merge_strategy == "overwrite":
                        self.db.delete(existing)

                record = HeartRateRecord(
                    user_id=self.user_id,
                    bpm=record_data["bpm"],
                    activity=record_data.get("activity", "resting"),
                    measured_at=measured_at,
                    note=record_data.get("note"),
                )
                self.db.add(record)
                self.result.add_success("heart_rate", record.id)

            except Exception as e:
                self.result.add_error(f"心率记录导入失败: {e}")

    def _import_sleep(self, records: List[Dict], merge_strategy: str):
        """导入睡眠记录"""
        for record_data in records:
            try:
                record_date = date.fromisoformat(record_data["date"])

                existing = (
                    self.db.query(SleepRecord)
                    .filter(
                        SleepRecord.user_id == self.user_id,
                        SleepRecord.date == record_date,
                    )
                    .first()
                )

                if existing:
                    if merge_strategy == "skip_duplicates":
                        self.result.add_skip(f"睡眠记录已存在: {record_date}")
                        continue
                    elif merge_strategy == "overwrite":
                        existing.duration_hours = record_data["duration_hours"]
                        existing.quality_score = record_data.get("quality_score")
                        self.result.add_success("sleep", existing.id)
                        continue

                bedtime = (
                    datetime.fromisoformat(record_data["bedtime"])
                    if record_data.get("bedtime")
                    else None
                )
                wake_time = (
                    datetime.fromisoformat(record_data["wake_time"])
                    if record_data.get("wake_time")
                    else None
                )

                record = SleepRecord(
                    user_id=self.user_id,
                    date=record_date,
                    duration_hours=record_data["duration_hours"],
                    quality_score=record_data.get("quality_score"),
                    bedtime=bedtime,
                    wake_time=wake_time,
                    deep_sleep_percentage=record_data.get("deep_sleep_percentage"),
                    light_sleep_percentage=record_data.get("light_sleep_percentage"),
                    rem_sleep_percentage=record_data.get("rem_sleep_percentage"),
                )
                self.db.add(record)
                self.result.add_success("sleep", record.id)

            except Exception as e:
                self.result.add_error(f"睡眠记录导入失败: {e}")

    def _import_medications(self, medications: List[Dict], merge_strategy: str):
        """导入用药数据"""
        for med_data in medications:
            try:
                # 查找或创建药品
                existing = (
                    self.db.query(Medication)
                    .filter(
                        Medication.user_id == self.user_id,
                        Medication.name == med_data["name"],
                    )
                    .first()
                )

                if existing and merge_strategy == "skip_duplicates":
                    self.result.add_skip(f"药品已存在: {med_data['name']}")
                    continue

                if not existing:
                    medication = Medication(
                        user_id=self.user_id,
                        name=med_data["name"],
                        dosage=med_data.get("dosage"),
                        frequency=med_data.get("frequency"),
                        purpose=med_data.get("purpose"),
                        start_date=(
                            date.fromisoformat(med_data["start_date"])
                            if med_data.get("start_date")
                            else None
                        ),
                        end_date=(
                            date.fromisoformat(med_data["end_date"])
                            if med_data.get("end_date")
                            else None
                        ),
                        is_active=med_data.get("is_active", True),
                    )
                    self.db.add(medication)
                    self.db.flush()  # 获取ID
                    self.result.add_success("medication", medication.id)
                else:
                    medication = existing

                # 导入用药日志
                for log_data in med_data.get("logs", []):
                    self._import_medication_log(medication.id, log_data, merge_strategy)

            except Exception as e:
                self.result.add_error(f"药品导入失败: {e}")

    def _import_medication_log(
        self, medication_id: int, log_data: Dict, merge_strategy: str
    ):
        """导入用药日志"""
        try:
            taken_at = datetime.fromisoformat(log_data["taken_at"])

            existing = (
                self.db.query(MedicationLog)
                .filter(
                    MedicationLog.medication_id == medication_id,
                    MedicationLog.taken_at == taken_at,
                )
                .first()
            )

            if existing and merge_strategy == "skip_duplicates":
                return

            log = MedicationLog(
                medication_id=medication_id,
                taken_at=taken_at,
                dose_taken=log_data.get("dose_taken"),
                status=log_data["status"],
                note=log_data.get("note"),
            )
            self.db.add(log)
            self.result.add_success("medication_log", log.id)

        except Exception as e:
            self.result.add_error(f"用药日志导入失败: {e}")

    def _import_goals(self, goals: List[Dict], merge_strategy: str):
        """导入健康目标"""
        for goal_data in goals:
            try:
                existing = (
                    self.db.query(HealthGoal)
                    .filter(
                        HealthGoal.user_id == self.user_id,
                        HealthGoal.title == goal_data["title"],
                    )
                    .first()
                )

                if existing and merge_strategy == "skip_duplicates":
                    self.result.add_skip(f"目标已存在: {goal_data['title']}")
                    continue

                goal = HealthGoal(
                    user_id=self.user_id,
                    title=goal_data["title"],
                    category=goal_data.get("category", "other"),
                    target_value=goal_data.get("target_value"),
                    current_value=goal_data.get("current_value", 0),
                    unit=goal_data.get("unit"),
                    start_date=(
                        date.fromisoformat(goal_data["start_date"])
                        if goal_data.get("start_date")
                        else date.today()
                    ),
                    deadline=(
                        date.fromisoformat(goal_data["deadline"])
                        if goal_data.get("deadline")
                        else None
                    ),
                    status=goal_data.get("status", "active"),
                    progress_percentage=goal_data.get("progress_percentage", 0),
                )
                self.db.add(goal)
                self.db.flush()
                self.result.add_success("goal", goal.id)

                # 导入打卡记录
                for check_in_data in goal_data.get("check_ins", []):
                    self._import_check_in(goal.id, check_in_data, merge_strategy)

            except Exception as e:
                self.result.add_error(f"目标导入失败: {e}")

    def _import_check_in(self, goal_id: int, check_in_data: Dict, merge_strategy: str):
        """导入打卡记录"""
        try:
            check_date = date.fromisoformat(check_in_data["date"])

            existing = (
                self.db.query(GoalCheckIn)
                .filter(GoalCheckIn.goal_id == goal_id, GoalCheckIn.date == check_date)
                .first()
            )

            if existing and merge_strategy == "skip_duplicates":
                return

            check_in = GoalCheckIn(
                goal_id=goal_id,
                date=check_date,
                value=check_in_data.get("value"),
                note=check_in_data.get("note"),
                completed=check_in_data.get("completed", False),
            )
            self.db.add(check_in)
            self.result.add_success("check_in", check_in.id)

        except Exception as e:
            self.result.add_error(f"打卡记录导入失败: {e}")

    # ==================== CSV导入辅助方法 ====================

    def _import_bp_csv(self, csv_content: str, merge_strategy: str):
        """从CSV导入血压记录"""
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                measured_at = datetime.strptime(row["记录时间"], "%Y-%m-%d %H:%M")

                existing = (
                    self.db.query(BloodPressureRecord)
                    .filter(
                        BloodPressureRecord.user_id == self.user_id,
                        BloodPressureRecord.measured_at == measured_at,
                    )
                    .first()
                )

                if existing and merge_strategy == "skip_duplicates":
                    self.result.add_skip(f"血压记录已存在: {measured_at}")
                    continue

                record = BloodPressureRecord(
                    user_id=self.user_id,
                    systolic=int(row["收缩压(mmHg)"]),
                    diastolic=int(row["舒张压(mmHg)"]),
                    heart_rate=int(row["心率"]) if row.get("心率") else None,
                    measured_at=measured_at,
                    status=row.get("状态") or None,
                    note=row.get("备注") or None,
                )
                self.db.add(record)
                self.result.add_success("blood_pressure", record.id)

            except Exception as e:
                self.result.add_error(f"CSV血压导入失败: {e}")

    def _import_glucose_csv(self, csv_content: str, merge_strategy: str):
        """从CSV导出血糖记录"""
        reader = csv.DictReader(io.StringIO(csv_content))

        meal_type_reverse = {
            "空腹": "fasting",
            "餐前": "before_meal",
            "餐后2小时": "after_meal",
            "随机": "random",
        }

        for row in reader:
            try:
                measured_at = datetime.strptime(row["记录时间"], "%Y-%m-%d %H:%M")
                meal_type = meal_type_reverse.get(row["测量类型"], "fasting")

                existing = (
                    self.db.query(GlucoseRecord)
                    .filter(
                        GlucoseRecord.user_id == self.user_id,
                        GlucoseRecord.measured_at == measured_at,
                        GlucoseRecord.meal_type == meal_type,
                    )
                    .first()
                )

                if existing and merge_strategy == "skip_duplicates":
                    self.result.add_skip(f"血糖记录已存在: {measured_at}")
                    continue

                record = GlucoseRecord(
                    user_id=self.user_id,
                    value=float(row["血糖值(mmol/L)"]),
                    meal_type=meal_type,
                    measured_at=measured_at,
                    note=row.get("备注") or None,
                )
                self.db.add(record)
                self.result.add_success("glucose", record.id)

            except Exception as e:
                self.result.add_error(f"CSV血糖导入失败: {e}")

    def _import_weight_csv(self, csv_content: str, merge_strategy: str):
        """从CSV导入体重记录"""
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                measured_at = datetime.strptime(row["记录时间"], "%Y-%m-%d %H:%M")

                existing = (
                    self.db.query(WeightRecord)
                    .filter(
                        WeightRecord.user_id == self.user_id,
                        WeightRecord.measured_at == measured_at,
                    )
                    .first()
                )

                if existing and merge_strategy == "skip_duplicates":
                    self.result.add_skip(f"体重记录已存在: {measured_at}")
                    continue

                record = WeightRecord(
                    user_id=self.user_id,
                    weight_kg=float(row["体重(kg)"]),
                    bmi=float(row["BMI"]) if row.get("BMI") else None,
                    body_fat_percentage=(
                        float(row["体脂率(%)"]) if row.get("体脂率(%)") else None
                    ),
                    measured_at=measured_at,
                    note=row.get("备注") or None,
                )
                self.db.add(record)
                self.result.add_success("weight", record.id)

            except Exception as e:
                self.result.add_error(f"CSV体重导入失败: {e}")

    def _import_hr_csv(self, csv_content: str, merge_strategy: str):
        """从CSV导入心率记录"""
        reader = csv.DictReader(io.StringIO(csv_content))

        activity_reverse = {
            "静息": "resting",
            "轻度活动": "light",
            "中度活动": "moderate",
            "剧烈运动": "intense",
        }

        for row in reader:
            try:
                measured_at = datetime.strptime(row["记录时间"], "%Y-%m-%d %H:%M")
                activity = activity_reverse.get(row["活动状态"], "resting")

                existing = (
                    self.db.query(HeartRateRecord)
                    .filter(
                        HeartRateRecord.user_id == self.user_id,
                        HeartRateRecord.measured_at == measured_at,
                    )
                    .first()
                )

                if existing and merge_strategy == "skip_duplicates":
                    self.result.add_skip(f"心率记录已存在: {measured_at}")
                    continue

                record = HeartRateRecord(
                    user_id=self.user_id,
                    bpm=int(row["心率(bpm)"]),
                    activity=activity,
                    measured_at=measured_at,
                    note=row.get("备注") or None,
                )
                self.db.add(record)
                self.result.add_success("heart_rate", record.id)

            except Exception as e:
                self.result.add_error(f"CSV心率导入失败: {e}")

    def _import_sleep_csv(self, csv_content: str, merge_strategy: str):
        """从CSV导入睡眠记录"""
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            try:
                record_date = datetime.strptime(row["日期"], "%Y-%m-%d").date()

                existing = (
                    self.db.query(SleepRecord)
                    .filter(
                        SleepRecord.user_id == self.user_id,
                        SleepRecord.date == record_date,
                    )
                    .first()
                )

                if existing and merge_strategy == "skip_duplicates":
                    self.result.add_skip(f"睡眠记录已存在: {record_date}")
                    continue

                bedtime = (
                    datetime.strptime(row["入睡时间"], "%H:%M")
                    if row.get("入睡时间")
                    else None
                )
                wake_time = (
                    datetime.strptime(row["起床时间"], "%H:%M")
                    if row.get("起床时间")
                    else None
                )

                record = SleepRecord(
                    user_id=self.user_id,
                    date=record_date,
                    duration_hours=float(row["睡眠时长(小时)"]),
                    quality_score=int(row["睡眠评分"]) if row.get("睡眠评分") else None,
                    bedtime=bedtime,
                    wake_time=wake_time,
                    deep_sleep_percentage=(
                        float(row["深睡(%)"]) if row.get("深睡(%)") else None
                    ),
                    light_sleep_percentage=(
                        float(row["浅睡(%)"]) if row.get("浅睡(%)") else None
                    ),
                    rem_sleep_percentage=(
                        float(row["REM(%)"]) if row.get("REM(%)") else None
                    ),
                )
                self.db.add(record)
                self.result.add_success("sleep", record.id)

            except Exception as e:
                self.result.add_error(f"CSV睡眠导入失败: {e}")


# 便捷函数
def import_user_data_json(
    db: Session,
    user_id: int,
    json_data: Dict[str, Any],
    merge_strategy: str = "skip_duplicates",
) -> Dict[str, Any]:
    """从JSON导入数据便捷函数"""
    service = DataImportService(db, user_id)
    result = service.import_from_json(json_data, merge_strategy)
    return result.to_dict()


def restore_user_backup(db: Session, user_id: int, zip_bytes: bytes) -> Dict[str, Any]:
    """恢复用户备份便捷函数"""
    service = DataImportService(db, user_id)
    result = service.restore_from_backup(zip_bytes)
    return result.to_dict()
