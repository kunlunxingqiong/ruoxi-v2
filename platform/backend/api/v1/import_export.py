"""
🌸 若曦V2 - 导入导出API
数据导入导出端点
"""

from datetime import datetime, timedelta
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse

from core.data_import_export.exporter import ExportFormat, ExportTemplate, data_exporter
from core.data_import_export.importer import (
    DataType,
    ImportFormat,
    ImportPreview,
    ImportResult,
    data_importer,
)

router = APIRouter(prefix="/data", tags=["数据导入导出"])


@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    data_type: str = Query(
        ...,
        description="数据类型: blood_pressure, blood_glucose, weight, sleep, heart_rate, steps, medication",
    ),
    current_user=Depends(get_current_user),
):
    """
    预览导入数据

    在实际导入前预览数据结构和验证结果
    """
    # 验证数据类型
    try:
        dtype = DataType(data_type)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"无效数据类型，可选: {[t.value for t in DataType]}"
        )

    # 读取文件内容
    contents = await file.read()

    # 生成预览
    from io import BytesIO

    preview = await data_importer.preview(
        file_content=BytesIO(contents), file_name=file.filename, data_type=dtype
    )

    return {"success": True, "preview": preview.to_dict()}


@router.post("/import")
async def import_data(
    file: UploadFile = File(...),
    data_type: str = Query(...),
    skip_validation: bool = Query(False),
    current_user=Depends(get_current_user),
):
    """
    导入健康数据

    支持格式: CSV, Excel (xlsx), JSON
    """
    # 验证数据类型
    try:
        dtype = DataType(data_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效数据类型")

    # 读取文件
    contents = await file.read()

    # 导入数据
    from io import BytesIO

    result = await data_importer.import_data(
        file_content=BytesIO(contents),
        file_name=file.filename,
        data_type=dtype,
        user_id=str(current_user.user_id),
        skip_validation=skip_validation,
    )

    return {"success": result.success, "import": result.to_dict()}


@router.get("/import/templates/{data_type}")
async def get_import_template(
    data_type: str,
    format: str = Query("csv", description="模板格式: csv, excel"),
    current_user=Depends(get_current_user),
):
    """
    下载导入模板

    提供标准的数据导入模板文件
    """
    try:
        dtype = DataType(data_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效数据类型")

    # 获取必需列
    required_cols = data_importer.REQUIRED_COLUMNS.get(dtype, [])

    # 生成示例数据
    import pandas as pd

    if dtype == DataType.BLOOD_PRESSURE:
        sample_data = {
            "timestamp": [datetime.now().isoformat()],
            "systolic": [120],
            "diastolic": [80],
            "pulse": [72],
            "note": ["早晨起床后"],
        }
    elif dtype == DataType.BLOOD_GLUCOSE:
        sample_data = {
            "timestamp": [datetime.now().isoformat()],
            "value": [5.6],
            "unit": ["mmol/L"],
            "meal_type": ["空腹"],
            "note": [""],
        }
    elif dtype == DataType.WEIGHT:
        sample_data = {
            "timestamp": [datetime.now().isoformat()],
            "weight": [65.5],
            "unit": ["kg"],
            "bmi": [22.1],
            "note": [""],
        }
    elif dtype == DataType.SLEEP:
        sample_data = {
            "start_time": [(datetime.now() - timedelta(hours=8)).isoformat()],
            "end_time": [datetime.now().isoformat()],
            "duration_minutes": [480],
            "deep_sleep_minutes": [120],
            "quality": ["良好"],
        }
    elif dtype == DataType.HEART_RATE:
        sample_data = {
            "timestamp": [datetime.now().isoformat()],
            "bpm": [72],
            "activity": ["静息"],
        }
    elif dtype == DataType.STEPS:
        sample_data = {
            "date": [datetime.now().strftime("%Y-%m-%d")],
            "steps": [8000],
            "distance_km": [5.2],
            "calories": [320],
        }
    else:
        sample_data = {col: [""] for col in required_cols}

    df = pd.DataFrame(sample_data)

    # 添加说明行
    comments = pd.DataFrame(
        {col: [f"必需: {col in required_cols}"] for col in df.columns}
    )

    df = pd.concat([comments, df], ignore_index=True)

    # 生成文件
    from io import BytesIO

    output = BytesIO()

    if format == "excel":
        df.to_excel(output, index=False, sheet_name="模板")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{data_type}_import_template.xlsx"
    else:
        df.to_csv(output, index=False, encoding="utf-8-sig")
        media_type = "text/csv"
        filename = f"{data_type}_import_template.csv"

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/import/supported-formats")
async def get_supported_import_formats(current_user=Depends(get_current_user)):
    """获取支持的导入格式"""
    return {
        "success": True,
        "formats": [
            {
                "id": "csv",
                "name": "CSV",
                "extensions": [".csv"],
                "description": "逗号分隔值文件",
            },
            {
                "id": "excel",
                "name": "Excel",
                "extensions": [".xlsx", ".xls"],
                "description": "Microsoft Excel文件",
            },
            {
                "id": "json",
                "name": "JSON",
                "extensions": [".json"],
                "description": "JSON格式数据",
            },
        ],
        "data_types": [
            {
                "id": "blood_pressure",
                "name": "血压",
                "description": "收缩压/舒张压/脉搏",
                "example": "120/80/72",
            },
            {
                "id": "blood_glucose",
                "name": "血糖",
                "description": "血糖数值及时间",
                "example": "5.6 mmol/L (空腹)",
            },
            {
                "id": "weight",
                "name": "体重",
                "description": "体重记录",
                "example": "65.5 kg",
            },
            {
                "id": "sleep",
                "name": "睡眠",
                "description": "睡眠时长和质量",
                "example": "8小时 / 深睡2小时",
            },
            {
                "id": "heart_rate",
                "name": "心率",
                "description": "心率记录",
                "example": "72 bpm",
            },
            {
                "id": "steps",
                "name": "步数",
                "description": "每日步数",
                "example": "8000步",
            },
            {
                "id": "medication",
                "name": "用药",
                "description": "服药记录",
                "example": "阿司匹林 100mg",
            },
        ],
    }


@router.get("/export")
async def export_data(
    data_type: str = Query(..., description="数据类型"),
    export_format: str = Query("excel", description="导出格式: csv, excel, json"),
    template: str = Query(
        "raw_data",
        description="模板: raw_data, daily_summary, weekly_report, monthly_report, for_doctor",
    ),
    date_from: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user=Depends(get_current_user),
):
    """
    导出健康数据

    格式:
    - csv: 纯文本CSV
    - excel: 格式化Excel（推荐）
    - json: JSON数据

    模板:
    - raw_data: 原始数据
    - daily_summary: 每日汇总
    - weekly_report: 周报格式
    - monthly_report: 月报格式
    - for_doctor: 医生格式（标准专业）
    """
    # 解析参数
    try:
        dtype = DataType(data_type)
        fmt = ExportFormat(export_format)
        tmpl = ExportTemplate(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效参数: {e}")

    # 解析日期
    date_from_dt = None
    date_to_dt = None

    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的开始日期格式")

    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的结束日期格式")

    # TODO: 从数据库获取真实数据
    # 模拟数据
    mock_data = []

    # 导出数据
    result = await data_exporter.export(
        data=mock_data,
        data_type=dtype.value,
        user_id=str(current_user.user_id),
        export_format=fmt,
        template=tmpl,
        date_from=date_from_dt,
        date_to=date_to_dt,
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.warnings[0] if result.warnings else "导出失败",
        )

    # 返回文件
    return StreamingResponse(
        io.BytesIO(result.file_content),
        media_type=result.mime_type,
        headers={"Content-Disposition": f"attachment; filename={result.file_name}"},
    )


@router.get("/export/report")
async def export_health_report(
    report_type: str = Query("weekly", description="报告类型: weekly, monthly"),
    export_format: str = Query("excel", description="导出格式: excel, pdf"),
    current_user=Depends(get_current_user),
):
    """
    导出综合健康报告

    包含多种数据类型的综合分析
    """
    try:
        fmt = ExportFormat(export_format)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效导出格式")

    result = await data_exporter.export_health_report(
        user_id=str(current_user.user_id), report_type=report_type, export_format=fmt
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.warnings[0] if result.warnings else "报告生成失败",
        )

    return StreamingResponse(
        io.BytesIO(result.file_content),
        media_type=result.mime_type,
        headers={"Content-Disposition": f"attachment; filename={result.file_name}"},
    )


@router.get("/export/supported-formats")
async def get_supported_export_formats(current_user=Depends(get_current_user)):
    """获取支持的导出格式"""
    return {
        "success": True,
        "formats": [
            {
                "id": "csv",
                "name": "CSV",
                "mime_type": "text/csv",
                "description": "纯文本格式，通用性强",
            },
            {
                "id": "excel",
                "name": "Excel",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "description": "格式化Excel表格，带样式",
            },
            {
                "id": "json",
                "name": "JSON",
                "mime_type": "application/json",
                "description": "JSON格式，适合程序处理",
            },
            {
                "id": "pdf",
                "name": "PDF",
                "mime_type": "application/pdf",
                "description": "PDF报告（开发中）",
            },
        ],
        "templates": [
            {"id": "raw_data", "name": "原始数据", "description": "完整原始记录"},
            {"id": "daily_summary", "name": "每日汇总", "description": "按日汇总统计"},
            {"id": "weekly_report", "name": "周报", "description": "周趋势分析"},
            {"id": "monthly_report", "name": "月报", "description": "月度综合报告"},
            {"id": "for_doctor", "name": "医生格式", "description": "专业医疗格式"},
        ],
    }


@router.post("/export/email")
async def export_and_email(
    email: str,
    data_type: str = Query(...),
    export_format: str = Query("excel"),
    current_user=Depends(get_current_user),
):
    """
    导出并发送到指定邮箱

    适用于分享报告给医生或家人
    """
    # TODO: 实现导出+邮件发送

    return {
        "success": True,
        "message": f"数据导出完成，将发送到 {email}",
        "note": "邮件发送功能开发中",
    }


# 导入io模块
import io
