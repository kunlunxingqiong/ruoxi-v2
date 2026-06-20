"""
🌸 若曦V2 - Apple Health数据导入服务
解析Apple Health导出的XML文件，导入健康数据
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import re
from sqlalchemy.orm import Session

from models.database import (
    BloodPressureRecord,
    GlucoseRecord,
    WeightRecord,
    SleepRecord,
    HeartRateRecord
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthDataRecord:
    """健康数据记录"""
    record_type: str
    value: float
    unit: str
    start_date: datetime
    end_date: Optional[datetime] = None
    source_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AppleHealthImporter:
    """
    Apple Health数据导入器
    
    支持解析Apple Health导出的export.xml文件
    提取血压、血糖、体重、睡眠、心率等数据
    """
    
    # Apple Health数据类型映射
    RECORD_TYPE_MAP = {
        # 血压
        'HKQuantityTypeIdentifierBloodPressureSystolic': 'systolic_bp',
        'HKQuantityTypeIdentifierBloodPressureDiastolic': 'diastolic_bp',
        # 心率
        'HKQuantityTypeIdentifierHeartRate': 'heart_rate',
        'HKQuantityTypeIdentifierRestingHeartRate': 'resting_hr',
        # 体重
        'HKQuantityTypeIdentifierBodyMass': 'weight',
        'HKQuantityTypeIdentifierBodyMassIndex': 'bmi',
        'HKQuantityTypeIdentifierBodyFatPercentage': 'body_fat',
        # 睡眠
        'HKCategoryTypeIdentifierSleepAnalysis': 'sleep',
        # 血糖 (需要第三方App支持)
        'HKQuantityTypeIdentifierBloodGlucose': 'glucose',
        # 步数和活动
        'HKQuantityTypeIdentifierStepCount': 'steps',
        'HKQuantityTypeIdentifierActiveEnergyBurned': 'calories',
        # 体温
        'HKQuantityTypeIdentifierBodyTemperature': 'temperature',
        # 血氧
        'HKQuantityTypeIdentifierOxygenSaturation': 'spo2',
    }
    
    # 单位转换映射
    UNIT_CONVERSION = {
        'mmHg': 1.0,
        'count/min': 1.0,
        'kg': 1.0,
        'lb': 0.453592,  # 磅转公斤
        'oz': 0.0283495, # 盎司转公斤
        'mg/dL': 0.0555, # mg/dL转mmol/L (血糖)
        'mmol/L': 1.0,
        'degC': 1.0,
        'degF': lambda x: (x - 32) * 5/9,  # 华氏转摄氏
        '%': 1.0,
        'count': 1.0,
        'kcal': 1.0,
        'cal': 0.001,
    }
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.import_stats = {
            'total_records': 0,
            'parsed_records': 0,
            'imported_records': 0,
            'skipped_records': 0,
            'errors': []
        }
    
    def parse_xml_file(self, file_path: str) -> List[HealthDataRecord]:
        """
        解析Apple Health XML文件
        
        Args:
            file_path: export.xml文件路径
            
        Returns:
            解析出的健康数据记录列表
        """
        logger.info(f"开始解析Apple Health文件: {file_path}")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            records = []
            
            # 解析Record元素
            for record_elem in root.findall('.//Record'):
                try:
                    record = self._parse_record_element(record_elem)
                    if record:
                        records.append(record)
                        self.import_stats['parsed_records'] += 1
                except Exception as e:
                    logger.warning(f"解析记录失败: {e}")
                    self.import_stats['errors'].append(str(e))
            
            # 解析Workout元素（运动记录）
            for workout_elem in root.findall('.//Workout'):
                try:
                    workout_records = self._parse_workout_element(workout_elem)
                    records.extend(workout_records)
                except Exception as e:
                    logger.warning(f"解析运动记录失败: {e}")
            
            self.import_stats['total_records'] = len(records)
            logger.info(f"解析完成: {len(records)} 条记录")
            
            return records
            
        except ET.ParseError as e:
            logger.error(f"XML解析错误: {e}")
            raise ValueError(f"无法解析Apple Health文件: {e}")
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise
    
    def _parse_record_element(self, elem: ET.Element) -> Optional[HealthDataRecord]:
        """解析单个Record元素"""
        record_type = elem.get('type', '')
        
        # 检查是否是我们关心的类型
        if record_type not in self.RECORD_TYPE_MAP:
            return None
        
        # 解析数值
        value_str = elem.get('value', '')
        if not value_str or value_str == 'NA':
            return None
        
        try:
            value = float(value_str)
        except ValueError:
            return None
        
        # 解析单位
        unit = elem.get('unit', '')
        
        # 单位转换
        converted_value = self._convert_unit(value, unit)
        
        # 解析日期
        start_date = self._parse_apple_health_date(elem.get('startDate', ''))
        end_date = self._parse_apple_health_date(elem.get('endDate', ''))
        
        # 解析源信息
        source_name = elem.get('sourceName', '')
        
        # 解析元数据
        metadata = {}
        for metadata_entry in elem.findall('MetadataEntry'):
            key = metadata_entry.get('key', '')
            val = metadata_entry.get('value', '')
            if key:
                metadata[key] = val
        
        return HealthDataRecord(
            record_type=self.RECORD_TYPE_MAP[record_type],
            value=converted_value,
            unit=self._get_standard_unit(self.RECORD_TYPE_MAP[record_type]),
            start_date=start_date,
            end_date=end_date,
            source_name=source_name,
            metadata=metadata
        )
    
    def _parse_workout_element(self, elem: ET.Element) -> List[HealthDataRecord]:
        """解析Workout元素"""
        records = []
        
        workout_type = elem.get('workoutActivityType', '')
        start_date = self._parse_apple_health_date(elem.get('startDate', ''))
        end_date = self._parse_apple_health_date(elem.get('endDate', ''))
        
        # 获取运动统计
        for stat in elem.findall('WorkoutStatistics'):
            stat_type = stat.get('type', '')
            if stat_type in self.RECORD_TYPE_MAP:
                try:
                    value = float(stat.get('sum', 0))
                    unit = stat.get('unit', '')
                    converted_value = self._convert_unit(value, unit)
                    
                    records.append(HealthDataRecord(
                        record_type=self.RECORD_TYPE_MAP[stat_type],
                        value=converted_value,
                        unit=self._get_standard_unit(self.RECORD_TYPE_MAP[stat_type]),
                        start_date=start_date,
                        end_date=end_date,
                        source_name=elem.get('sourceName', ''),
                        metadata={'workout_type': workout_type}
                    ))
                except (ValueError, TypeError):
                    continue
        
        return records
    
    def _convert_unit(self, value: float, unit: str) -> float:
        """转换单位为标准单位"""
        if unit in self.UNIT_CONVERSION:
            conversion = self.UNIT_CONVERSION[unit]
            if callable(conversion):
                return conversion(value)
            return value * conversion
        return value
    
    def _get_standard_unit(self, record_type: str) -> str:
        """获取标准单位"""
        unit_map = {
            'systolic_bp': 'mmHg',
            'diastolic_bp': 'mmHg',
            'heart_rate': 'bpm',
            'resting_hr': 'bpm',
            'weight': 'kg',
            'bmi': 'kg/m2',
            'body_fat': '%',
            'glucose': 'mmol/L',
            'steps': 'count',
            'calories': 'kcal',
            'temperature': 'degC',
            'spo2': '%',
            'sleep': 'category',
        }
        return unit_map.get(record_type, '')
    
    def _parse_apple_health_date(self, date_str: str) -> datetime:
        """解析Apple Health日期格式"""
        # Apple Health日期格式: 2024-01-15 08:30:00 +0800
        if not date_str:
            return datetime.now()
        
        # 处理时区偏移
        date_str = re.sub(r' ([+-]\d{4})$', r'\1', date_str)
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %z')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return datetime.now()
    
    def import_to_database(
        self, 
        records: List[HealthDataRecord],
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        将解析的数据导入数据库
        
        Args:
            records: 健康数据记录列表
            skip_duplicates: 是否跳过重复记录
            
        Returns:
            导入统计信息
        """
        logger.info(f"开始导入 {len(records)} 条记录到数据库")
        
        # 按类型分组
        grouped = self._group_records_by_type(records)
        
        # 导入各类数据
        import_counts = {
            'blood_pressure': self._import_blood_pressure(grouped.get('bp_pairs', []), skip_duplicates),
            'heart_rate': self._import_heart_rate(grouped.get('heart_rate', []), skip_duplicates),
            'weight': self._import_weight(grouped.get('weight', []), skip_duplicates),
            'sleep': self._import_sleep(grouped.get('sleep', []), skip_duplicates),
            'glucose': self._import_glucose(grouped.get('glucose', []), skip_duplicates),
        }
        
        total_imported = sum(import_counts.values())
        self.import_stats['imported_records'] = total_imported
        
        logger.info(f"导入完成: {total_imported} 条记录")
        
        return {
            'success': True,
            'import_counts': import_counts,
            'total_imported': total_imported,
            'stats': self.import_stats
        }
    
    def _group_records_by_type(
        self, 
        records: List[HealthDataRecord]
    ) -> Dict[str, List[HealthDataRecord]]:
        """按类型分组记录"""
        grouped: Dict[str, List[HealthDataRecord]] = {
            'heart_rate': [],
            'weight': [],
            'sleep': [],
            'glucose': [],
            'bp_pairs': []
        }
        
        # 特殊处理血压：需要配对收缩压和舒张压
        bp_systolic = {}
        bp_diastolic = {}
        
        for record in records:
            rt = record.record_type
            
            if rt == 'heart_rate':
                grouped['heart_rate'].append(record)
            elif rt == 'resting_hr':
                record.record_type = 'heart_rate'
                record.metadata = {'activity': 'resting'}
                grouped['heart_rate'].append(record)
            elif rt == 'weight':
                grouped['weight'].append(record)
            elif rt == 'sleep':
                grouped['sleep'].append(record)
            elif rt == 'glucose':
                grouped['glucose'].append(record)
            elif rt == 'systolic_bp':
                # 按时间分组用于配对
                time_key = record.start_date.strftime('%Y-%m-%d %H:%M')
                bp_systolic[time_key] = record
            elif rt == 'diastolic_bp':
                time_key = record.start_date.strftime('%Y-%m-%d %H:%M')
                bp_diastolic[time_key] = record
        
        # 配对血压记录
        for time_key in bp_systolic:
            if time_key in bp_diastolic:
                grouped['bp_pairs'].append({
                    'systolic': bp_systolic[time_key],
                    'diastolic': bp_diastolic[time_key]
                })
        
        return grouped
    
    def _import_blood_pressure(
        self, 
        bp_pairs: List[Dict], 
        skip_duplicates: bool
    ) -> int:
        """导入血压记录"""
        count = 0
        
        for pair in bp_pairs:
            sys_record = pair['systolic']
            dia_record = pair['diastolic']
            
            # 跳过重复检查
            if skip_duplicates:
                existing = self.db.query(BloodPressureRecord).filter(
                    BloodPressureRecord.user_id == self.user_id,
                    BloodPressureRecord.measured_at == sys_record.start_date
                ).first()
                if existing:
                    self.import_stats['skipped_records'] += 1
                    continue
            
            # 创建记录
            bp_record = BloodPressureRecord(
                user_id=self.user_id,
                systolic=int(sys_record.value),
                diastolic=int(dia_record.value),
                pulse=None,  # Apple Health可能不提供脉搏
                measured_at=sys_record.start_date,
                device_id=sys_record.source_name
            )
            
            self.db.add(bp_record)
            count += 1
        
        self.db.commit()
        return count
    
    def _import_heart_rate(
        self, 
        records: List[HealthDataRecord], 
        skip_duplicates: bool
    ) -> int:
        """导入心率记录"""
        count = 0
        
        for record in records:
            if skip_duplicates:
                existing = self.db.query(HeartRateRecord).filter(
                    HeartRateRecord.user_id == self.user_id,
                    HeartRateRecord.measured_at == record.start_date
                ).first()
                if existing:
                    continue
            
            activity = record.metadata.get('activity', 'unknown') if record.metadata else 'unknown'
            
            hr_record = HeartRateRecord(
                user_id=self.user_id,
                bpm=int(record.value),
                activity=activity,
                measured_at=record.start_date,
                device_id=record.source_name
            )
            
            self.db.add(hr_record)
            count += 1
        
        self.db.commit()
        return count
    
    def _import_weight(
        self, 
        records: List[HealthDataRecord], 
        skip_duplicates: bool
    ) -> int:
        """导入体重记录"""
        count = 0
        
        for record in records:
            if skip_duplicates:
                existing = self.db.query(WeightRecord).filter(
                    WeightRecord.user_id == self.user_id,
                    WeightRecord.measured_at == record.start_date
                ).first()
                if existing:
                    continue
            
            weight_record = WeightRecord(
                user_id=self.user_id,
                weight_kg=record.value,
                bmi=None,  # 需要身高计算
                measured_at=record.start_date,
                device_id=record.source_name
            )
            
            self.db.add(weight_record)
            count += 1
        
        self.db.commit()
        return count
    
    def _import_sleep(
        self, 
        records: List[HealthDataRecord], 
        skip_duplicates: bool
    ) -> int:
        """导入睡眠记录"""
        # 睡眠记录在Apple Health中通常是时间段
        # 这里简化处理，实际需要解析睡眠阶段
        count = 0
        
        # 按日期分组，合并同一晚的睡眠
        sleep_by_night: Dict[str, Dict] = {}
        
        for record in records:
            if not record.end_date:
                continue
            
            night_key = record.start_date.strftime('%Y-%m-%d')
            
            if night_key not in sleep_by_night:
                sleep_by_night[night_key] = {
                    'start': record.start_date,
                    'end': record.end_date,
                    'source': record.source_name
                }
            else:
                # 取最早开始和最晚结束
                if record.start_date < sleep_by_night[night_key]['start']:
                    sleep_by_night[night_key]['start'] = record.start_date
                if record.end_date > sleep_by_night[night_key]['end']:
                    sleep_by_night[night_key]['end'] = record.end_date
        
        for night_key, sleep_data in sleep_by_night.items():
            if skip_duplicates:
                existing = self.db.query(SleepRecord).filter(
                    SleepRecord.user_id == self.user_id,
                    func.date(SleepRecord.bed_time) == night_key
                ).first()
                if existing:
                    continue
            
            duration_minutes = int((sleep_data['end'] - sleep_data['start']).total_seconds() / 60)
            
            sleep_record = SleepRecord(
                user_id=self.user_id,
                bed_time=sleep_data['start'],
                wake_time=sleep_data['end'],
                duration_minutes=duration_minutes,
                sleep_quality=None,
                device_id=sleep_data['source']
            )
            
            self.db.add(sleep_record)
            count += 1
        
        self.db.commit()
        return count
    
    def _import_glucose(
        self, 
        records: List[HealthDataRecord], 
        skip_duplicates: bool
    ) -> int:
        """导入血糖记录"""
        count = 0
        
        for record in records:
            if skip_duplicates:
                existing = self.db.query(GlucoseRecord).filter(
                    GlucoseRecord.user_id == self.user_id,
                    GlucoseRecord.measured_at == record.start_date
                ).first()
                if existing:
                    continue
            
            # 尝试判断测量时段
            hour = record.start_date.hour
            if 5 <= hour < 8:
                meal_type = 'fasting'  # 空腹
            elif 11 <= hour < 14:
                meal_type = 'after_meal'  # 餐后
            elif 17 <= hour < 20:
                meal_type = 'after_meal'
            else:
                meal_type = 'random'
            
            glucose_record = GlucoseRecord(
                user_id=self.user_id,
                value=record.value,
                unit='mmol/L',
                meal_type=meal_type,
                measured_at=record.start_date,
                device_id=record.source_name
            )
            
            self.db.add(glucose_record)
            count += 1
        
        self.db.commit()
        return count


# 便捷函数
def import_apple_health_data(
    file_path: str, 
    user_id: int, 
    db: Session,
    skip_duplicates: bool = True
) -> Dict[str, Any]:
    """
    便捷函数：导入Apple Health数据
    
    Args:
        file_path: export.xml文件路径
        user_id: 用户ID
        db: 数据库会话
        skip_duplicates: 是否跳过重复
        
    Returns:
        导入结果统计
    """
    importer = AppleHealthImporter(db, user_id)
    records = importer.parse_xml_file(file_path)
    result = importer.import_to_database(records, skip_duplicates)
    return result


# 导入func用于日期查询
from sqlalchemy import func
