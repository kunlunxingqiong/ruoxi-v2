"""
🌸 若曦V2 - 数据管理API
提供数据导出、导入、备份恢复功能
"""

import io
import json
from datetime import date, datetime
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from models.database import get_db
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.services.data_export_service import DataExportService, export_user_data
from core.services.data_import_service import (
    DataImportService,
    import_user_data_json,
    restore_user_backup,
)

router = APIRouter(prefix="/data", tags=["数据管理"])


# ==================== 请求/响应模型 ====================


class ExportRequest(BaseModel):
    format: str = "json"  # json, csv, zip
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    record_types: Optional[list] = None  # 可选: 只导出特定类型


class ExportResponse(BaseModel):
    success: bool
    filename: str
    record_count: int
    download_url: Optional[str]


class ImportResponse(BaseModel):
    success: bool
    import_result: Dict[str, Any]
    message: str


class BackupInfo(BaseModel):
    last_backup_date: Optional[str]
    backup_count: int
    total_size_mb: float


# ==================== API 端点 ====================


@router.get("/export")
async def export_data(
    format: str = Query("json", enum=["json", "csv", "zip"]),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    download: bool = Query(True, description="是否直接下载"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    导出健康数据

    支持三种格式:
    - **json**: 完整数据导出，包含所有关联关系
    - **csv**: 多CSV文件ZIP包，便于Excel分析
    - **zip**: 完整备份包，包含JSON+CSV+恢复指南

    Query参数:
    - start_date: 可选，导出某个日期范围的数据
    - end_date: 可选，导出某个日期范围的数据
    - download: 是否直接下载文件 (默认true)
    """
    try:
        # 转换日期到datetime
        start_dt = (
            datetime.combine(start_date, datetime.min.time()) if start_date else None
        )
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        result = export_user_data(db, current_user.user_id, format, start_dt, end_dt)

        data = result.get("data")
        filename = result.get("filename")
        content_type = result.get("content_type", "application/octet-stream")

        if format == "json":
            # JSON格式：直接返回或下载
            if download:
                json_str = json.dumps(data, ensure_ascii=False, indent=2)
                return StreamingResponse(
                    io.StringIO(json_str),
                    media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )
            else:
                return {
                    "success": True,
                    "format": format,
                    "data": data,
                    "record_count": result.get("record_count", 0),
                }
        else:
            # ZIP格式：返回二进制文件
            zip_bytes = data if isinstance(data, bytes) else data.encode("utf-8")
            return StreamingResponse(
                io.BytesIO(zip_bytes),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/export/preview")
async def preview_export(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    预览将要导出的数据

    返回数据概览，不实际导出
    """
    try:
        start_dt = (
            datetime.combine(start_date, datetime.min.time()) if start_date else None
        )
        end_dt = datetime.combine(end_date, datetime.max.time()) if end_date else None

        service = DataExportService(db, current_user.user_id)
        result = service.export_all_data("json", start_dt, end_dt)

        data = result.get("data", {})
        health = data.get("health_records", {})

        return {
            "success": True,
            "preview": {
                "date_range": data.get("export_metadata", {}).get("date_range", {}),
                "record_counts": {
                    "blood_pressure": len(health.get("blood_pressure", [])),
                    "glucose": len(health.get("glucose", [])),
                    "weight": len(health.get("weight", [])),
                    "heart_rate": len(health.get("heart_rate", [])),
                    "sleep": len(health.get("sleep", [])),
                },
                "medications": len(data.get("medications", {}).get("medications", [])),
                "goals": len(data.get("goals", {}).get("goals", [])),
                "reports": len(data.get("reports", {}).get("reports", [])),
                "total_records": result.get("record_count", 0),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")


@router.post("/import/json")
async def import_json_data(
    data: Dict[str, Any],
    merge_strategy: str = Query(
        "skip_duplicates", enum=["skip_duplicates", "overwrite", "append"]
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    从JSON导入数据

    支持合并策略:
    - **skip_duplicates**: 跳过重复记录 (默认)
    - **overwrite**: 覆盖已存在的记录
    - **append**: 全部追加，不检查重复
    """
    try:
        result = import_user_data_json(db, current_user.user_id, data, merge_strategy)

        return {
            "success": result["error_count"] == 0,
            "import_result": result,
            "message": f"成功导入 {result['success_count']} 条记录，跳过 {result['skip_count']} 条",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/import/csv")
async def import_csv_data(
    file: UploadFile = File(...),
    record_type: str = Query(
        ..., enum=["blood_pressure", "glucose", "weight", "heart_rate", "sleep"]
    ),
    merge_strategy: str = Query(
        "skip_duplicates", enum=["skip_duplicates", "overwrite"]
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    从CSV文件导入数据

    需要先下载导出的CSV模板，按格式填写数据后上传
    """
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")

        service = DataImportService(db, current_user.user_id)
        result = service.import_from_csv(csv_content, record_type, merge_strategy)

        return {
            "success": result.error_count == 0,
            "import_result": result.to_dict(),
            "message": f"成功导入 {result.success_count} 条{record_type}记录",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV导入失败: {str(e)}")


@router.post("/restore")
async def restore_from_backup(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    从备份ZIP恢复数据

    恢复操作会:
    1. 合并数据（不删除现有数据）
    2. 自动跳过重复记录
    3. 保留恢复前的状态（失败可回滚）

    **建议**: 恢复前先创建新的备份
    """
    try:
        content = await file.read()

        result = restore_user_backup(db, current_user.user_id, content)

        return {
            "success": result["error_count"] == 0,
            "restore_result": result,
            "message": f"恢复完成: 成功 {result['success_count']} 条, 跳过 {result['skip_count']} 条",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")


@router.post("/backup/create")
async def create_full_backup(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    创建完整数据备份

    创建包含所有历史数据的完整备份包
    """
    try:
        result = export_user_data(db, current_user.user_id, "zip")

        return {
            "success": True,
            "backup_info": {
                "filename": result.get("filename"),
                "record_count": result.get("record_count"),
                "created_at": datetime.now().isoformat(),
            },
            "download_url": f"/api/v1/data/export?format=zip",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")


@router.get("/backup/info")
async def get_backup_info(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """获取最近的备份信息"""
    # 这里可以实现从文件系统或数据库查询备份信息
    return {
        "success": True,
        "message": "请定期使用 /data/backup/create 创建备份",
        "recommended_schedule": "每周至少备份一次",
    }


@router.get("/export/template/{record_type}")
async def download_csv_template(
    record_type: str, current_user=Depends(get_current_user)
):
    """
    下载CSV导入模板

    获取标准格式的CSV模板，按模板填写后可通过 /import/csv 导入
    """
    templates = {
        "blood_pressure": "记录时间,收缩压(mmHg),舒张压(mmHg),心率,状态,备注\n"
        "2024-01-15 08:30,120,80,72,正常,晨间测量\n"
        "2024-01-15 20:00,118,78,70,正常,晚间测量",
        "glucose": "记录时间,血糖值(mmol/L),测量类型,备注\n"
        "2024-01-15 07:00,5.2,空腹,\n"
        "2024-01-15 12:00,6.8,餐前,\n"
        "2024-01-15 14:00,7.5,餐后2小时,",
        "weight": "记录时间,体重(kg),BMI,体脂率(%),备注\n"
        "2024-01-15 07:00,65.5,22.1,18.5,空腹称重",
        "heart_rate": "记录时间,心率(bpm),活动状态,备注\n"
        "2024-01-15 07:00,65,静息,\n"
        "2024-01-15 19:00,85,轻度活动,步行后",
        "sleep": "日期,睡眠时长(小时),睡眠评分,入睡时间,起床时间,深睡(%),浅睡(%),REM(%)\n"
        "2024-01-15,7.5,85,23:00,06:30,20,50,25",
    }

    if record_type not in templates:
        raise HTTPException(status_code=400, detail=f"不支持的类型: {record_type}")

    csv_content = templates[record_type]
    filename = f"{record_type}_template.csv"

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/stats")
async def get_data_statistics(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取用户数据统计

    返回数据量统计和存储使用情况
    """
    from sqlalchemy import func

    stats = {
        "health_records": {
            "blood_pressure": db.query(BloodPressureRecord)
            .filter(BloodPressureRecord.user_id == current_user.user_id)
            .count(),
            "glucose": db.query(GlucoseRecord)
            .filter(GlucoseRecord.user_id == current_user.user_id)
            .count(),
            "weight": db.query(WeightRecord)
            .filter(WeightRecord.user_id == current_user.user_id)
            .count(),
            "heart_rate": db.query(HeartRateRecord)
            .filter(HeartRateRecord.user_id == current_user.user_id)
            .count(),
            "sleep": db.query(SleepRecord)
            .filter(SleepRecord.user_id == current_user.user_id)
            .count(),
        },
        "medications": db.query(Medication)
        .filter(Medication.user_id == current_user.user_id)
        .count(),
        "medication_logs": db.query(MedicationLog)
        .join(Medication)
        .filter(Medication.user_id == current_user.user_id)
        .count(),
        "goals": db.query(HealthGoal)
        .filter(HealthGoal.user_id == current_user.user_id)
        .count(),
    }

    # 计算数据时间跨度
    first_bp = (
        db.query(BloodPressureRecord)
        .filter(BloodPressureRecord.user_id == current_user.user_id)
        .order_by(BloodPressureRecord.measured_at)
        .first()
    )

    last_bp = (
        db.query(BloodPressureRecord)
        .filter(BloodPressureRecord.user_id == current_user.user_id)
        .order_by(BloodPressureRecord.measured_at.desc())
        .first()
    )

    total_records = (
        sum(stats["health_records"].values())
        + stats["medication_logs"]
        + stats["goals"]
    )

    return {
        "success": True,
        "stats": stats,
        "total_records": total_records,
        "data_span": {
            "first_record": first_bp.measured_at.isoformat() if first_bp else None,
            "last_record": last_bp.measured_at.isoformat() if last_bp else None,
        },
        "generated_at": datetime.now().isoformat(),
    }


@router.delete("/cleanup")
async def cleanup_old_data(
    days: int = Query(365, ge=30, description="保留最近多少天的数据"),
    dry_run: bool = Query(True, description="仅预览不实际删除"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    清理旧数据

    **警告**: 此操作会永久删除数据！

    默认dry_run=true只返回将要删除的记录数
    确认后再设置dry_run=false执行删除
    "%"""
    cutoff_date = datetime.utcnow() - __import__("datetime").timedelta(days=days)

    # 查询各类型将要删除的记录
    to_delete = {
        "blood_pressure": db.query(BloodPressureRecord)
        .filter(
            BloodPressureRecord.user_id == current_user.user_id,
            BloodPressureRecord.measured_at < cutoff_date,
        )
        .count(),
        "glucose": db.query(GlucoseRecord)
        .filter(
            GlucoseRecord.user_id == current_user.user_id,
            GlucoseRecord.measured_at < cutoff_date,
        )
        .count(),
        "weight": db.query(WeightRecord)
        .filter(
            WeightRecord.user_id == current_user.user_id,
            WeightRecord.measured_at < cutoff_date,
        )
        .count(),
        "heart_rate": db.query(HeartRateRecord)
        .filter(
            HeartRateRecord.user_id == current_user.user_id,
            HeartRateRecord.measured_at < cutoff_date,
        )
        .count(),
    }

    total_to_delete = sum(to_delete.values())

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "preview": to_delete,
            "total_will_delete": total_to_delete,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"将删除 {total_to_delete} 条记录（{days}天之前的数据）",
        }

    # 实际删除
    try:
        deleted_counts = {}

        for Model, name in [
            (BloodPressureRecord, "blood_pressure"),
            (GlucoseRecord, "glucose"),
            (WeightRecord, "weight"),
            (HeartRateRecord, "heart_rate"),
        ]:
            deleted = (
                db.query(Model)
                .filter(
                    Model.user_id == current_user.user_id,
                    Model.measured_at < cutoff_date,
                )
                .delete(synchronize_session=False)
            )
            deleted_counts[name] = deleted

        db.commit()

        return {
            "success": True,
            "dry_run": False,
            "deleted": deleted_counts,
            "total_deleted": sum(deleted_counts.values()),
            "message": "清理完成",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")
