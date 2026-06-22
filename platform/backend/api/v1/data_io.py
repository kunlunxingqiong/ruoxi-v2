"""
🌸 若曦V2 - 数据导入导出API
"""

from datetime import datetime
from enum import Enum
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from core.export.data_exporter import ExportFormat, ExportType, data_exporter
from core.importing.data_importer import ImportFormat, data_importer

router = APIRouter(prefix="/data", tags=["数据导入导出"])


class ExportFormatEnum(str, Enum):
    json = "json"
    csv = "csv"
    pdf = "pdf"
    excel = "xlsx"
    markdown = "md"


class ImportFormatEnum(str, Enum):
    json = "json"
    csv = "csv"
    apple_health = "apple_health"
    huawei_health = "huawei_health"
    xiaomi_health = "xiaomi_health"


@router.post("/export/health-records")
async def export_health_records(
    format: ExportFormatEnum = ExportFormatEnum.json,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    anonymize: bool = False,
    current_user=Depends(get_current_user),
):
    """导出健康记录"""

    # TODO: 从数据库获取真实数据
    mock_records = [
        {"timestamp": "2026-06-20T08:00:00", "systolic": 120, "diastolic": 80},
        {"timestamp": "2026-06-21T08:00:00", "systolic": 118, "diastolic": 78},
    ]

    date_range = None
    if start_date and end_date:
        date_range = (start_date, end_date)

    export_format = ExportFormat(format.value)

    file_path = await data_exporter.export_health_records(
        user_id=current_user.user_id,
        records=mock_records,
        export_format=export_format,
        date_range=date_range,
        anonymize=anonymize,
    )

    return FileResponse(
        file_path, media_type="application/octet-stream", filename=Path(file_path).name
    )


@router.post("/export/chat-history")
async def export_chat_history(
    format: ExportFormatEnum = ExportFormatEnum.markdown,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user=Depends(get_current_user),
):
    """导出聊天记录"""

    mock_messages = [
        {"role": "user", "content": "你好若曦", "timestamp": "2026-06-21T10:00:00"},
        {
            "role": "assistant",
            "content": "🌸 你好呀~ 曦曦在呢",
            "timestamp": "2026-06-21T10:00:01",
        },
    ]

    date_range = None
    if start_date and end_date:
        date_range = (start_date, end_date)

    export_format = ExportFormat(format.value)

    file_path = await data_exporter.export_chat_history(
        user_id=current_user.user_id,
        messages=mock_messages,
        export_format=export_format,
        date_range=date_range,
    )

    return FileResponse(
        file_path, media_type="application/octet-stream", filename=Path(file_path).name
    )


@router.post("/export/full-backup")
async def export_full_backup(current_user=Depends(get_current_user)):
    """导出完整备份"""

    backup_data = {
        "health_records": [],
        "chat_history": [],
        "emotion_logs": [],
        "memories": [],
    }

    file_path = await data_exporter.create_full_backup(
        user_id=current_user.user_id, data=backup_data
    )

    return FileResponse(
        file_path, media_type="application/octet-stream", filename=Path(file_path).name
    )


@router.get("/exports")
async def list_exports(current_user=Depends(get_current_user)):
    """列出导出文件"""
    exports = data_exporter.get_export_list(current_user.user_id)

    return {"success": True, "exports": exports, "total": len(exports)}


@router.delete("/exports/{filename}")
async def delete_export(filename: str, current_user=Depends(get_current_user)):
    """删除导出文件"""
    import os

    # 构建完整路径
    file_path = Path(f"data/exports/{current_user.user_id}_{filename}")

    # 安全检查：确保文件路径在允许的目录内
    export_dir = Path("data/exports").resolve()
    target_file = file_path.resolve()

    if not str(target_file).startswith(str(export_dir)):
        raise HTTPException(status_code=403, detail="非法文件路径")

    success = data_exporter.delete_export(str(file_path))

    if not success:
        raise HTTPException(status_code=404, detail="文件不存在或删除失败")

    return {"success": True, "message": "导出文件已删除"}


@router.post("/import")
async def import_data(
    file: UploadFile = File(...),
    format: ImportFormatEnum = ImportFormatEnum.json,
    data_type: str = "auto_detect",
    current_user=Depends(get_current_user),
):
    """导入数据"""

    import_format = ImportFormat(format.value)

    # 保存上传文件
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 执行导入
        report = await data_importer.import_from_file(
            user_id=current_user.user_id,
            file_path=temp_path,
            import_format=import_format,
            data_type=data_type,
        )

        return {
            "success": report.result.name != "FAILED",
            "report": {
                "total": report.total_records,
                "success": report.success_count,
                "failed": report.failed_count,
                "skipped": report.skipped_count,
                "duration_ms": report.import_duration_ms,
                "result": report.result.name,
            },
            "errors": report.errors[:10] if report.errors else [],
            "warnings": report.warnings if report.warnings else [],
        }

    finally:
        # 清理临时文件
        import os

        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/import/template/{data_type}")
async def get_import_template(data_type: str, current_user=Depends(get_current_user)):
    """获取导入模板"""
    template = data_importer.get_import_template(data_type)

    if not template:
        raise HTTPException(status_code=404, detail="不支持的导入类型")

    return {"success": True, "data_type": data_type, "template": template}


@router.get("/import/supported-formats")
async def list_supported_formats(current_user=Depends(get_current_user)):
    """列出支持的导入格式"""
    formats = {
        ImportFormat.JSON: {
            "description": "标准JSON格式",
            "use_case": "通用数据导入",
            "extensions": [".json"],
        },
        ImportFormat.CSV: {
            "description": "CSV表格格式",
            "use_case": "Excel/WPS导出数据",
            "extensions": [".csv"],
        },
        ImportFormat.APPLE_HEALTH: {
            "description": "Apple Health导出",
            "use_case": "iPhone健康数据",
            "extensions": [".xml", ".zip"],
        },
        ImportFormat.HUAWEI_HEALTH: {
            "description": "华为健康导出",
            "use_case": "华为手表/健康APP数据",
            "extensions": [".json", ".zip"],
        },
        ImportFormat.XIAOMI_HEALTH: {
            "description": "小米运动导出",
            "use_case": "小米手环/运动数据",
            "extensions": [".json"],
        },
    }

    return {"success": True, "formats": {k.value: v for k, v in formats.items()}}
