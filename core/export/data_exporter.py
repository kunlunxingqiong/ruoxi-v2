"""
🌸 若曦V2 - 数据导出系统
支持健康数据、聊天记录导出为多种格式
"""
from typing import Dict, List, Optional, Any, BinaryIO
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
import json
import csv
import io


class ExportFormat(Enum):
    """导出格式"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "xlsx"
    MARKDOWN = "md"


class ExportType(Enum):
    """导出类型"""
    HEALTH_RECORDS = auto()
    CHAT_HISTORY = auto()
    EMOTION_LOGS = auto()
    MEMORY_SNAPSHOT = auto()
    FULL_BACKUP = auto()


@dataclass
class ExportJob:
    """导出任务"""
    id: str
    user_id: str
    export_type: ExportType
    export_format: ExportFormat
    start_date: datetime
    end_date: datetime
    status: str  # pending, processing, completed, failed
    file_path: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class DataExporter:
    """
    数据导出器
    
    支持:
    - 多格式导出 (JSON/CSV/PDF/Excel/Markdown)
    - 批量健康数据导出
    - 聊天记录导出
    - 完整备份
    - 数据脱敏选项
    """
    
    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_health_records(
        self,
        user_id: str,
        records: List[Dict],
        export_format: ExportFormat = ExportFormat.JSON,
        date_range: Optional[tuple] = None,
        anonymize: bool = False
    ) -> str:
        """
        导出健康记录
        
        Args:
            user_id: 用户ID
            records: 健康记录列表
            export_format: 导出格式
            date_range: 日期范围 (start, end)
            anonymize: 是否脱敏
        """
        # 过滤日期范围
        if date_range:
            start, end = date_range
            records = [
                r for r in records
                if start <= datetime.fromisoformat(r.get('timestamp', '2000-01-01')) <= end
            ]
        
        # 脱敏处理
        if anonymize:
            records = self._anonymize_records(records)
        
        # 根据格式导出
        if export_format == ExportFormat.JSON:
            return await self._export_json(user_id, "health_records", records)
        elif export_format == ExportFormat.CSV:
            return await self._export_csv(user_id, "health_records", records)
        elif export_format == ExportFormat.MARKDOWN:
            return await self._export_health_md(user_id, records)
        else:
            return await self._export_json(user_id, "health_records", records)
    
    async def export_chat_history(
        self,
        user_id: str,
        messages: List[Dict],
        export_format: ExportFormat = ExportFormat.MARKDOWN,
        date_range: Optional[tuple] = None
    ) -> str:
        """导出聊天记录"""
        if date_range:
            start, end = date_range
            messages = [
                m for m in messages
                if start <= datetime.fromisoformat(m.get('timestamp', '2000-01-01')) <= end
            ]
        
        if export_format == ExportFormat.MARKDOWN:
            return await self._export_chat_md(user_id, messages)
        elif export_format == ExportFormat.JSON:
            return await self._export_json(user_id, "chat_history", messages)
        else:
            return await self._export_chat_md(user_id, messages)
    
    async def export_emotion_logs(
        self,
        user_id: str,
        emotions: List[Dict],
        export_format: ExportFormat = ExportFormat.CSV
    ) -> str:
        """导出情绪记录"""
        if export_format == ExportFormat.CSV:
            return await self._export_csv(user_id, "emotion_logs", emotions)
        elif export_format == ExportFormat.JSON:
            return await self._export_json(user_id, "emotion_logs", emotions)
        else:
            return await self._export_csv(user_id, "emotion_logs", emotions)
    
    async def create_full_backup(
        self,
        user_id: str,
        data: Dict[str, List[Dict]]
    ) -> str:
        """创建完整备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{user_id}_full_backup_{timestamp}.json"
        filepath = self.output_dir / filename
        
        backup_data = {
            "user_id": user_id,
            "export_type": "full_backup",
            "created_at": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "data": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    async def _export_json(
        self,
        user_id: str,
        data_type: str,
        data: List[Dict]
    ) -> str:
        """导出为JSON"""
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{user_id}_{data_type}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        export_data = {
            "user_id": user_id,
            "export_type": data_type,
            "exported_at": datetime.utcnow().isoformat(),
            "count": len(data),
            "data": data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    async def _export_csv(
        self,
        user_id: str,
        data_type: str,
        data: List[Dict]
    ) -> str:
        """导出为CSV"""
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{user_id}_{data_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        if not data:
            # 创建空CSV
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                f.write('')
            return str(filepath)
        
        # 获取所有字段
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return str(filepath)
    
    async def _export_health_md(
        self,
        user_id: str,
        records: List[Dict]
    ) -> str:
        """导出健康记录为Markdown"""
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{user_id}_health_records_{timestamp}.md"
        filepath = self.output_dir / filename
        
        md_content = f"""# 🌸 健康记录导出

**导出日期**: {datetime.now().strftime('%Y年%m月%d日')}
**记录数量**: {len(records)} 条

---

## 📊 记录详情

"""
        
        for record in records:
            md_content += f"""
### {record.get('timestamp', '未知时间')}

"""
            for key, value in record.items():
                if key != 'timestamp':
                    md_content += f"- **{key}**: {value}\n"
            
            md_content += "\n---\n\n"
        
        md_content += f"""
*由若曦V2导出 - Made with 💜*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(filepath)
    
    async def _export_chat_md(
        self,
        user_id: str,
        messages: List[Dict]
    ) -> str:
        """导出聊天记录为Markdown"""
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{user_id}_chat_history_{timestamp}.md"
        filepath = self.output_dir / filename
        
        md_content = f"""# 💬 聊天记录导出

**导出日期**: {datetime.now().strftime('%Y年%m月%d日')}
**消息数量**: {len(messages)} 条

---

"""
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            if role == 'user':
                md_content += f"""
**👤 用户** ({timestamp}):
{content}

"""
            elif role == 'assistant':
                md_content += f"""
**🌸 若曦** ({timestamp}):
{content}

---

"""
        
        md_content += f"""
*与若曦的温暖回忆 - 💜*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(filepath)
    
    def _anonymize_records(self, records: List[Dict]) -> List[Dict]:
        """脱敏处理"""
        anonymized = []
        for record in records:
            clean_record = {}
            for key, value in record.items():
                # 移除敏感字段
                if key not in ['user_id', 'ip_address', 'device_id']:
                    clean_record[key] = value
            anonymized.append(clean_record)
        return anonymized
    
    def get_export_list(self, user_id: str) -> List[Dict]:
        """获取用户导出文件列表"""
        exports = []
        
        for file_path in self.output_dir.glob(f"{user_id}_*"):
            stat = file_path.stat()
            exports.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return sorted(exports, key=lambda x: x['created_at'], reverse=True)
    
    def delete_export(self, file_path: str) -> bool:
        """删除导出文件"""
        try:
            path = Path(file_path)
            if path.exists() and self.output_dir in path.parents:
                path.unlink()
                return True
        except Exception:
            pass
        return False


# 全局导出器实例
data_exporter = DataExporter()
