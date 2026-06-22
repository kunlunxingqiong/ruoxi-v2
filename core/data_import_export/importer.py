"""
🌸 若曦V2 - 健康数据导入器
支持多种格式的健康数据导入
"""

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union

import pandas as pd


class ImportFormat(Enum):
    """支持的导入格式"""

    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    APPLE_HEALTH = "apple_health"
    HUAWEI_HEALTH = "huawei_health"
    XIAOMI_HEALTH = "xiaomi_health"


class DataType(Enum):
    """数据类型"""

    BLOOD_PRESSURE = "blood_pressure"
    BLOOD_GLUCOSE = "blood_glucose"
    WEIGHT = "weight"
    SLEEP = "sleep"
    HEART_RATE = "heart_rate"
    STEPS = "steps"
    MEDICATION = "medication"


@dataclass
class ImportResult:
    """导入结果"""

    success: bool
    total_rows: int
    imported_rows: int
    skipped_rows: int
    errors: List[Dict]
    warnings: List[str]
    data_type: DataType
    file_name: str

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "total_rows": self.total_rows,
            "imported_rows": self.imported_rows,
            "skipped_rows": self.skipped_rows,
            "errors": self.errors,
            "warnings": self.warnings,
            "data_type": self.data_type.value,
            "file_name": self.file_name,
        }


@dataclass
class ImportPreview:
    """导入预览"""

    data_type: DataType
    columns: List[str]
    sample_rows: List[Dict]
    total_rows: int
    validation_errors: List[str]

    def to_dict(self) -> Dict:
        return {
            "data_type": self.data_type.value,
            "columns": self.columns,
            "sample_rows": self.sample_rows[:5],  # 只返回前5行预览
            "total_rows": self.total_rows,
            "validation_errors": self.validation_errors,
        }


class DataImporter:
    """
    健康数据导入器

    支持:
    - CSV/Excel/JSON 格式
    - Apple Health 导出数据
    - 华为/小米等厂商健康数据
    - 数据验证和清洗
    - 批量导入
    """

    # 各数据类型的必需列
    REQUIRED_COLUMNS = {
        DataType.BLOOD_PRESSURE: ["timestamp", "systolic", "diastolic"],
        DataType.BLOOD_GLUCOSE: ["timestamp", "value", "unit"],
        DataType.WEIGHT: ["timestamp", "weight", "unit"],
        DataType.SLEEP: ["start_time", "end_time", "duration_minutes"],
        DataType.HEART_RATE: ["timestamp", "bpm"],
        DataType.STEPS: ["date", "steps"],
        DataType.MEDICATION: ["medication_name", "scheduled_time", "dosage"],
    }

    # 列名映射 (标准列名 -> 可能的变体)
    COLUMN_MAPPINGS = {
        "timestamp": [
            "timestamp",
            "date",
            "time",
            "datetime",
            "记录时间",
            "日期",
            "时间",
        ],
        "systolic": ["systolic", "收缩压", "高压", "sbp"],
        "diastolic": ["diastolic", "舒张压", "低压", "dbp"],
        "value": ["value", "value", "数值", "血糖值"],
        "unit": ["unit", "单位"],
        "weight": ["weight", "体重", "重量"],
        "bpm": ["bpm", "heart_rate", "心率", "心跳"],
        "steps": ["steps", "步数", "step_count"],
        "start_time": ["start_time", "开始时间", "入睡时间"],
        "end_time": ["end_time", "结束时间", "醒来时间"],
        "duration_minutes": ["duration_minutes", "duration", "持续时间", "睡眠时长"],
        "medication_name": ["medication_name", "药品名称", "药物", "药名"],
        "scheduled_time": ["scheduled_time", "计划时间", "服药时间"],
        "dosage": ["dosage", "剂量", "用量"],
    }

    def __init__(self):
        self._validation_rules = {}

    async def preview(
        self,
        file_content: BinaryIO,
        file_name: str,
        data_type: DataType,
        file_format: Optional[ImportFormat] = None,
    ) -> ImportPreview:
        """
        预览导入数据

        在进行实际导入前预览数据结构，验证格式是否正确
        """
        # 自动检测格式
        if file_format is None:
            file_format = self._detect_format(file_name)

        # 读取数据
        df = self._read_file(file_content, file_format)

        if df is None or df.empty:
            return ImportPreview(
                data_type=data_type,
                columns=[],
                sample_rows=[],
                total_rows=0,
                validation_errors=["无法读取文件或文件为空"],
            )

        # 标准化列名
        df = self._normalize_columns(df)

        # 验证必需列
        errors = self._validate_columns(df, data_type)

        # 数据预览
        sample = df.head(5).to_dict("records")

        return ImportPreview(
            data_type=data_type,
            columns=list(df.columns),
            sample_rows=sample,
            total_rows=len(df),
            validation_errors=errors,
        )

    async def import_data(
        self,
        file_content: BinaryIO,
        file_name: str,
        data_type: DataType,
        user_id: str,
        file_format: Optional[ImportFormat] = None,
        skip_validation: bool = False,
    ) -> ImportResult:
        """
        导入数据

        Args:
            file_content: 文件内容
            file_name: 文件名
            data_type: 数据类型
            user_id: 用户ID
            file_format: 文件格式
            skip_validation: 是否跳过验证
        """
        # 自动检测格式
        if file_format is None:
            file_format = self._detect_format(file_name)

        # 读取数据
        df = self._read_file(file_content, file_format)

        if df is None:
            return ImportResult(
                success=False,
                total_rows=0,
                imported_rows=0,
                skipped_rows=0,
                errors=[{"row": -1, "error": "无法读取文件"}],
                warnings=[],
                data_type=data_type,
                file_name=file_name,
            )

        total_rows = len(df)

        # 标准化列名
        df = self._normalize_columns(df)

        # 验证数据
        errors = []
        if not skip_validation:
            errors = self._validate_columns(df, data_type)
            if errors:
                return ImportResult(
                    success=False,
                    total_rows=total_rows,
                    imported_rows=0,
                    skipped_rows=total_rows,
                    errors=[{"row": -1, "error": err} for err in errors],
                    warnings=[],
                    data_type=data_type,
                    file_name=file_name,
                )

        # 数据清洗
        df, cleaning_warnings = self._clean_data(df, data_type)

        # 导入到数据库
        imported_count, import_errors = await self._store_data(df, data_type, user_id)

        errors.extend(import_errors)

        return ImportResult(
            success=len(errors) == 0 or imported_count > 0,
            total_rows=total_rows,
            imported_rows=imported_count,
            skipped_rows=total_rows - imported_count,
            errors=errors,
            warnings=cleaning_warnings,
            data_type=data_type,
            file_name=file_name,
        )

    def _detect_format(self, file_name: str) -> ImportFormat:
        """自动检测文件格式"""
        ext = Path(file_name).suffix.lower()

        format_map = {
            ".csv": ImportFormat.CSV,
            ".xlsx": ImportFormat.EXCEL,
            ".xls": ImportFormat.EXCEL,
            ".json": ImportFormat.JSON,
            ".xml": ImportFormat.APPLE_HEALTH,
        }

        return format_map.get(ext, ImportFormat.CSV)

    def _read_file(
        self, file_content: BinaryIO, file_format: ImportFormat
    ) -> Optional[pd.DataFrame]:
        """读取文件为DataFrame"""
        try:
            if file_format == ImportFormat.CSV:
                # 尝试不同的编码
                for encoding in ["utf-8", "gbk", "gb2312", "utf-8-sig"]:
                    try:
                        file_content.seek(0)
                        return pd.read_csv(file_content, encoding=encoding)
                    except UnicodeDecodeError:
                        continue
                raise ValueError("无法识别CSV编码")

            elif file_format == ImportFormat.EXCEL:
                file_content.seek(0)
                return pd.read_excel(file_content)

            elif file_format == ImportFormat.JSON:
                file_content.seek(0)
                data = json.load(file_content)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict) and "data" in data:
                    return pd.DataFrame(data["data"])
                else:
                    return pd.json_normalize(data)

            else:
                # 其他格式暂不支持
                return None

        except Exception as e:
            print(f"读取文件失败: {e}")
            return None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        column_mapping = {}

        for col in df.columns:
            col_lower = str(col).lower().strip()

            # 查找匹配的标准列名
            for standard, variants in self.COLUMN_MAPPINGS.items():
                if col_lower in [v.lower() for v in variants]:
                    column_mapping[col] = standard
                    break
            else:
                column_mapping[col] = col_lower

        return df.rename(columns=column_mapping)

    def _validate_columns(self, df: pd.DataFrame, data_type: DataType) -> List[str]:
        """验证必需列"""
        errors = []
        required = self.REQUIRED_COLUMNS.get(data_type, [])

        missing = [col for col in required if col not in df.columns]

        if missing:
            errors.append(f"缺少必需列: {', '.join(missing)}")
            errors.append(f"当前列: {', '.join(df.columns)}")

        return errors

    def _clean_data(
        self, df: pd.DataFrame, data_type: DataType
    ) -> tuple[pd.DataFrame, List[str]]:
        """清洗数据"""
        warnings = []

        # 移除完全空行
        before_count = len(df)
        df = df.dropna(how="all")
        after_count = len(df)

        if before_count != after_count:
            warnings.append(f"移除了 {before_count - after_count} 行空数据")

        # 根据数据类型进行特定清洗
        if data_type == DataType.BLOOD_PRESSURE:
            # 确保数值类型
            df["systolic"] = pd.to_numeric(df["systolic"], errors="coerce")
            df["diastolic"] = pd.to_numeric(df["diastolic"], errors="coerce")

            # 过滤异常值
            invalid = df[
                (df["systolic"] < 50)
                | (df["systolic"] > 250)
                | (df["diastolic"] < 30)
                | (df["diastolic"] > 150)
            ]

            if not invalid.empty:
                warnings.append(f"发现 {len(invalid)} 行异常血压值")
                df = df[
                    (df["systolic"] >= 50)
                    & (df["systolic"] <= 250)
                    & (df["diastolic"] >= 30)
                    & (df["diastolic"] <= 150)
                ]

        elif data_type == DataType.BLOOD_GLUCOSE:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")

            # 过滤异常值
            invalid = df[(df["value"] < 1) | (df["value"] > 50)]
            if not invalid.empty:
                warnings.append(f"发现 {len(invalid)} 行异常血糖值")
                df = df[(df["value"] >= 1) & (df["value"] <= 50)]

        # 移除NaN行
        df = df.dropna(subset=self.REQUIRED_COLUMNS.get(data_type, []))

        return df, warnings

    async def _store_data(
        self, df: pd.DataFrame, data_type: DataType, user_id: str
    ) -> tuple[int, List[Dict]]:
        """存储数据到数据库"""
        imported = 0
        errors = []

        # TODO: 实现实际的数据库存储
        # 这里简化为模拟存储

        for idx, row in df.iterrows():
            try:
                # 转换为记录
                record = self._row_to_record(row, data_type)
                record["user_id"] = user_id
                record["created_at"] = datetime.utcnow().isoformat()

                # 存储 (模拟)
                imported += 1

            except Exception as e:
                errors.append({"row": idx, "error": str(e), "data": row.to_dict()})

        return imported, errors

    def _row_to_record(self, row: pd.Series, data_type: DataType) -> Dict:
        """将DataFrame行转换为记录"""
        record = row.to_dict()
        record["data_type"] = data_type.value
        return record

    async def import_apple_health(self, file_content: BinaryIO, user_id: str) -> Dict:
        """
        导入 Apple Health 导出数据

        Apple Health导出为XML格式，需要特殊处理
        """
        # TODO: 解析Apple Health的export.xml
        return {
            "success": False,
            "message": "Apple Health导入功能开发中",
            "supported_types": [
                "HKQuantityTypeIdentifierBloodPressureSystolic",
                "HKQuantityTypeIdentifierBloodPressureDiastolic",
                "HKQuantityTypeIdentifierBloodGlucose",
                "HKQuantityTypeIdentifierBodyMass",
                "HKQuantityTypeIdentifierHeartRate",
            ],
        }


# 导入器实例
data_importer = DataImporter()
