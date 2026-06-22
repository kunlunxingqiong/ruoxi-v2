"""
🌸 若曦V2 - 数据导入系统
支持从多种格式导入健康数据
"""

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ImportFormat(Enum):
    """导入格式"""

    JSON = "json"
    CSV = "csv"
    APPLE_HEALTH = "apple_health"
    HUAWEI_HEALTH = "huawei_health"
    XIAOMI_HEALTH = "xiaomi_health"
    CUSTOM = "custom"


class ImportResult(Enum):
    """导入结果"""

    SUCCESS = auto()
    PARTIAL = auto()
    FAILED = auto()


@dataclass
class ImportReport:
    """导入报告"""

    total_records: int
    success_count: int
    failed_count: int
    skipped_count: int
    errors: List[str]
    warnings: List[str]
    import_duration_ms: int
    result: ImportResult


class DataImporter:
    """
    数据导入器

    支持:
    - Apple Health 数据导入
    - 华为健康数据导入
    - 小米运动数据导入
    - 标准CSV/JSON格式
    - 数据验证和清洗
    """

    def __init__(self):
        self.supported_formats = list(ImportFormat)
        self._validators = {
            "blood_pressure": self._validate_bp,
            "blood_glucose": self._validate_glucose,
            "heart_rate": self._validate_hr,
            "sleep": self._validate_sleep,
            "weight": self._validate_weight,
        }

    async def import_from_file(
        self,
        user_id: str,
        file_path: str,
        import_format: ImportFormat = ImportFormat.JSON,
        data_type: str = "auto_detect",
    ) -> ImportReport:
        """
        从文件导入数据

        Args:
            user_id: 用户ID
            file_path: 文件路径
            import_format: 导入格式
            data_type: 数据类型 (auto_detect自动检测)
        """
        start_time = datetime.utcnow()

        try:
            if import_format == ImportFormat.JSON:
                records = await self._parse_json(file_path)
            elif import_format == ImportFormat.CSV:
                records = await self._parse_csv(file_path)
            elif import_format == ImportFormat.APPLE_HEALTH:
                records = await self._parse_apple_health(file_path)
            else:
                records = await self._parse_json(file_path)

            # 导入记录
            report = await self._import_records(user_id, records, data_type)

            end_time = datetime.utcnow()
            report.import_duration_ms = int(
                (end_time - start_time).total_seconds() * 1000
            )

            return report

        except Exception as e:
            end_time = datetime.utcnow()
            return ImportReport(
                total_records=0,
                success_count=0,
                failed_count=0,
                skipped_count=0,
                errors=[str(e)],
                warnings=[],
                import_duration_ms=int((end_time - start_time).total_seconds() * 1000),
                result=ImportResult.FAILED,
            )

    async def _parse_json(self, file_path: str) -> List[Dict]:
        """解析JSON文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 支持两种格式: 直接数组或包含data字段的对象
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "data" in data:
            return data["data"]
        else:
            return [data]

    async def _parse_csv(self, file_path: str) -> List[Dict]:
        """解析CSV文件"""
        records = []

        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))

        return records

    async def _parse_apple_health(self, file_path: str) -> List[Dict]:
        """解析Apple Health导出数据"""
        records = []

        # Apple Health导出通常是XML格式，这里提供简化处理
        # 实际项目中可能需要使用xml.etree或第三方库

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 简单提取血压记录示例
        bp_pattern = r'<Record[^>]*type="HKQuantityTypeIdentifierBloodPressureSystolic"[^>]*value="(\d+)"[^>]*>'
        bp_matches = re.findall(bp_pattern, content)

        for value in bp_matches:
            records.append({"systolic": int(value), "source": "apple_health"})

        return records

    async def _import_records(
        self, user_id: str, records: List[Dict], data_type: str
    ) -> ImportReport:
        """导入记录到系统"""
        total = len(records)
        success = 0
        failed = 0
        skipped = 0
        errors = []
        warnings = []

        for i, record in enumerate(records):
            try:
                # 自动检测数据类型
                detected_type = (
                    self._detect_data_type(record)
                    if data_type == "auto_detect"
                    else data_type
                )

                # 验证记录
                is_valid, error_msg = self._validate_record(record, detected_type)

                if not is_valid:
                    failed += 1
                    errors.append(f"记录 {i+1}: {error_msg}")
                    continue

                # 标准化记录
                standardized = self._standardize_record(record, detected_type, user_id)

                # 保存记录 (这里应该调用数据库接口)
                # await self._save_to_database(standardized)

                success += 1

            except Exception as e:
                failed += 1
                errors.append(f"记录 {i+1}: {str(e)}")

        # 确定结果
        if success == total:
            result = ImportResult.SUCCESS
        elif success > 0:
            result = ImportResult.PARTIAL
        else:
            result = ImportResult.FAILED

        return ImportReport(
            total_records=total,
            success_count=success,
            failed_count=failed,
            skipped_count=skipped,
            errors=errors,
            warnings=warnings,
            import_duration_ms=0,
            result=result,
        )

    def _detect_data_type(self, record: Dict) -> str:
        """自动检测数据类型"""
        fields = set(record.keys())

        if "systolic" in fields and "diastolic" in fields:
            return "blood_pressure"
        elif "glucose" in fields or "blood_glucose" in fields:
            return "blood_glucose"
        elif "heart_rate" in fields or "bpm" in fields:
            return "heart_rate"
        elif "sleep_duration" in fields or "hours_in_bed" in fields:
            return "sleep"
        elif "weight" in fields:
            return "weight"
        else:
            return "unknown"

    def _validate_record(self, record: Dict, data_type: str) -> Tuple[bool, str]:
        """验证记录有效性"""
        validator = self._validators.get(data_type)

        if validator:
            return validator(record)

        # 没有验证器，默认通过
        return True, ""

    def _validate_bp(self, record: Dict) -> Tuple[bool, str]:
        """验证血压记录"""
        systolic = record.get("systolic")
        diastolic = record.get("diastolic")

        if systolic is None or diastolic is None:
            return False, "缺少收缩压或舒张压"

        try:
            sys_val = float(systolic)
            dia_val = float(diastolic)

            if not (50 <= sys_val <= 250):
                return False, f"收缩压 {sys_val} 超出正常范围"
            if not (30 <= dia_val <= 150):
                return False, f"舒张压 {dia_val} 超出正常范围"

            return True, ""
        except (ValueError, TypeError):
            return False, "血压值格式无效"

    def _validate_glucose(self, record: Dict) -> Tuple[bool, str]:
        """验证血糖记录"""
        glucose = record.get("glucose") or record.get("blood_glucose")

        if glucose is None:
            return False, "缺少血糖值"

        try:
            val = float(glucose)
            if not (2 <= val <= 30):
                return False, f"血糖值 {val} 超出正常范围"
            return True, ""
        except (ValueError, TypeError):
            return False, "血糖值格式无效"

    def _validate_hr(self, record: Dict) -> Tuple[bool, str]:
        """验证心率记录"""
        hr = record.get("heart_rate") or record.get("bpm")

        if hr is None:
            return False, "缺少心率值"

        try:
            val = float(hr)
            if not (30 <= val <= 250):
                return False, f"心率值 {val} 超出正常范围"
            return True, ""
        except (ValueError, TypeError):
            return False, "心率值格式无效"

    def _validate_sleep(self, record: Dict) -> Tuple[bool, str]:
        """验证睡眠记录"""
        duration = record.get("sleep_duration") or record.get("duration_hours")

        if duration is None:
            return False, "缺少睡眠时长"

        try:
            val = float(duration)
            if not (0 <= val <= 24):
                return False, f"睡眠时长 {val} 小时超出合理范围"
            return True, ""
        except (ValueError, TypeError):
            return False, "睡眠时长格式无效"

    def _validate_weight(self, record: Dict) -> Tuple[bool, str]:
        """验证体重记录"""
        weight = record.get("weight")

        if weight is None:
            return False, "缺少体重值"

        try:
            val = float(weight)
            if not (20 <= val <= 300):
                return False, f"体重值 {val} kg 超出合理范围"
            return True, ""
        except (ValueError, TypeError):
            return False, "体重值格式无效"

    def _standardize_record(self, record: Dict, data_type: str, user_id: str) -> Dict:
        """标准化记录格式"""
        standardized = {
            "user_id": user_id,
            "data_type": data_type,
            "imported_at": datetime.utcnow().isoformat(),
        }

        # 提取时间戳
        timestamp = (
            record.get("timestamp") or record.get("date") or record.get("start_date")
        )
        if timestamp:
            standardized["timestamp"] = timestamp

        # 根据类型提取数据
        if data_type == "blood_pressure":
            standardized["systolic"] = float(record.get("systolic", 0))
            standardized["diastolic"] = float(record.get("diastolic", 0))
        elif data_type == "blood_glucose":
            standardized["value"] = float(
                record.get("glucose") or record.get("blood_glucose", 0)
            )
        elif data_type == "heart_rate":
            standardized["bpm"] = float(
                record.get("heart_rate") or record.get("bpm", 0)
            )
        elif data_type == "sleep":
            standardized["duration_hours"] = float(
                record.get("sleep_duration") or record.get("duration_hours", 0)
            )
        elif data_type == "weight":
            standardized["weight_kg"] = float(record.get("weight", 0))

        return standardized

    def get_import_template(self, data_type: str) -> Dict:
        """获取导入模板"""
        templates = {
            "blood_pressure": {
                "timestamp": "2026-06-21T08:00:00",
                "systolic": 120,
                "diastolic": 80,
                "unit": "mmHg",
                "notes": "可选备注",
            },
            "blood_glucose": {
                "timestamp": "2026-06-21T08:00:00",
                "glucose": 5.5,
                "unit": "mmol/L",
                "meal_type": "fasting",
            },
            "heart_rate": {
                "timestamp": "2026-06-21T08:00:00",
                "heart_rate": 72,
                "unit": "bpm",
            },
            "sleep": {
                "timestamp": "2026-06-21",
                "duration_hours": 7.5,
                "efficiency": 85,
            },
        }

        return templates.get(data_type, {})


# 全局导入器实例
data_importer = DataImporter()
