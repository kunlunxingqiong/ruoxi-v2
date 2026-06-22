"""
🌸 若曦V2 - Apple Health数据导入API
处理Apple Health导出文件的导入请求
"""

import os
import shutil
import tempfile
from platform.backend.core_auth.jwt_auth import get_current_user
from typing import List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from models.database import get_db
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.services.apple_health_import import (
    AppleHealthImporter,
    import_apple_health_data,
)

router = APIRouter(prefix="/import/apple-health", tags=["Apple Health导入"])


# ==================== 响应模型 ====================


class ImportStatusResponse(BaseModel):
    """导入状态响应"""

    success: bool
    message: str
    import_id: Optional[str] = None
    total_records: Optional[int] = None
    parsed_records: Optional[int] = None
    imported_records: Optional[int] = None
    skipped_records: Optional[int] = None
    import_counts: Optional[dict] = None
    errors: Optional[List[str]] = None


class ImportPreviewResponse(BaseModel):
    """导入预览响应"""

    success: bool
    total_records: int
    by_type: dict
    date_range: dict
    sample_records: List[dict]


class ImportHistoryItem(BaseModel):
    """导入历史项"""

    import_id: str
    imported_at: str
    total_records: int
    imported_records: int
    status: str


# ==================== 全局存储（生产环境应使用Redis）===================
_import_jobs: dict = {}


def _generate_import_id() -> str:
    """生成导入任务ID"""
    import uuid

    return str(uuid.uuid4())[:8]


# ==================== API 端点 ====================


@router.post("/upload", response_model=ImportStatusResponse)
async def upload_apple_health_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Apple Health导出的export.xml文件"),
    skip_duplicates: bool = Query(True, description="是否跳过重复记录"),
    dry_run: bool = Query(False, description="仅解析预览，不实际导入"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传并导入Apple Health数据

    - 支持导出文件格式：export.xml
    - 自动解析血压、心率、体重、睡眠、血糖等数据
    - 可选择跳过重复记录
    - dry_run=True时仅预览数据，不实际导入

    支持的Apple Health数据类型：
    - 血压（收缩压/舒张压）
    - 心率（静息/运动）
    - 体重/体脂
    - 睡眠分析
    - 血糖（需要兼容App）
    - 步数/活动能量
    """
    # 验证文件类型
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="只支持XML文件格式")

    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        # 保存上传的文件
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 获取文件大小
        file_size = os.path.getsize(temp_path)
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="文件过大，最大支持100MB")

        if dry_run:
            # 仅预览模式
            importer = AppleHealthImporter(db, current_user.user_id)
            records = importer.parse_xml_file(temp_path)

            # 生成预览统计
            by_type = {}
            for record in records:
                rt = record.record_type
                by_type[rt] = by_type.get(rt, 0) + 1

            dates = [r.start_date for r in records if r.start_date]

            return {
                "success": True,
                "message": "数据预览完成",
                "total_records": len(records),
                "parsed_records": len(records),
                "by_type": by_type,
                "date_range": {
                    "earliest": min(dates).isoformat() if dates else None,
                    "latest": max(dates).isoformat() if dates else None,
                },
                "sample_records": [
                    {
                        "type": r.record_type,
                        "value": r.value,
                        "unit": r.unit,
                        "date": r.start_date.isoformat() if r.start_date else None,
                    }
                    for r in records[:5]
                ],
            }

        # 实际导入模式
        import_id = _generate_import_id()

        # 后台导入任务
        def do_import():
            import_db = next(get_db())
            try:
                result = import_apple_health_data(
                    file_path=temp_path,
                    user_id=current_user.user_id,
                    db=import_db,
                    skip_duplicates=skip_duplicates,
                )
                _import_jobs[import_id] = {"status": "completed", "result": result}
            except Exception as e:
                _import_jobs[import_id] = {"status": "failed", "error": str(e)}
            finally:
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)

        # 小文件直接导入，大文件后台处理
        if file_size < 10 * 1024 * 1024:  # < 10MB
            result = import_apple_health_data(
                file_path=temp_path,
                user_id=current_user.user_id,
                db=db,
                skip_duplicates=skip_duplicates,
            )

            return {
                "success": True,
                "message": "数据导入成功",
                "import_id": import_id,
                **result,
            }
        else:
            # 大文件后台处理
            background_tasks.add_task(do_import)
            _import_jobs[import_id] = {"status": "processing"}

            return {
                "success": True,
                "message": "大文件导入任务已创建，请稍后查询状态",
                "import_id": import_id,
                "status": "processing",
            }

    except HTTPException:
        raise
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/status/{import_id}")
async def get_import_status(import_id: str, current_user=Depends(get_current_user)):
    """
    查询导入任务状态

    用于大文件后台导入的状态查询
    """
    if import_id not in _import_jobs:
        raise HTTPException(status_code=404, detail="导入任务不存在")

    job = _import_jobs[import_id]

    return {
        "success": True,
        "import_id": import_id,
        "status": job.get("status"),
        "result": job.get("result") if job.get("status") == "completed" else None,
        "error": job.get("error") if job.get("status") == "failed" else None,
    }


@router.post("/preview")
async def preview_apple_health_file(
    file: UploadFile = File(..., description="Apple Health导出的export.xml文件"),
    current_user=Depends(get_current_user),
):
    """
    预览Apple Health文件内容

    解析文件并返回数据预览，不实际导入
    """
    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="只支持XML文件格式")

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 仅从文件解析，不连接数据库
        importer = AppleHealthImporter(None, current_user.user_id)
        records = importer.parse_xml_file(temp_path)

        # 统计各类数据
        by_type = {}
        for record in records:
            rt = record.record_type
            by_type[rt] = by_type.get(rt, 0) + 1

        # 日期范围
        dates = [r.start_date for r in records if r.start_date]

        # 示例记录
        samples = []
        for record in records[:10]:
            samples.append(
                {
                    "type": record.record_type,
                    "value": record.value,
                    "unit": record.unit,
                    "date": (
                        record.start_date.isoformat() if record.start_date else None
                    ),
                    "source": record.source_name,
                }
            )

        return {
            "success": True,
            "file_name": file.filename,
            "total_records": len(records),
            "by_type": by_type,
            "date_range": {
                "earliest": min(dates).isoformat() if dates else None,
                "latest": max(dates).isoformat() if dates else None,
            },
            "sample_records": samples,
        }

    finally:
        # 清理
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


@router.get("/supported-types")
async def get_supported_types():
    """
    获取支持导入的Apple Health数据类型

    返回所有可以解析和导入的数据类型列表
    """
    return {
        "success": True,
        "supported_types": {
            "blood_pressure": {
                "name": "血压",
                "apple_types": [
                    "HKQuantityTypeIdentifierBloodPressureSystolic",
                    "HKQuantityTypeIdentifierBloodPressureDiastolic",
                ],
                "unit": "mmHg",
            },
            "heart_rate": {
                "name": "心率",
                "apple_types": [
                    "HKQuantityTypeIdentifierHeartRate",
                    "HKQuantityTypeIdentifierRestingHeartRate",
                ],
                "unit": "bpm",
            },
            "weight": {
                "name": "体重",
                "apple_types": [
                    "HKQuantityTypeIdentifierBodyMass",
                    "HKQuantityTypeIdentifierBodyMassIndex",
                ],
                "unit": "kg",
            },
            "sleep": {
                "name": "睡眠",
                "apple_types": ["HKCategoryTypeIdentifierSleepAnalysis"],
                "unit": "duration",
            },
            "glucose": {
                "name": "血糖",
                "apple_types": ["HKQuantityTypeIdentifierBloodGlucose"],
                "unit": "mmol/L",
                "note": "需要第三方血糖App支持",
            },
            "steps": {
                "name": "步数",
                "apple_types": ["HKQuantityTypeIdentifierStepCount"],
                "unit": "count",
            },
            "calories": {
                "name": "活动能量",
                "apple_types": ["HKQuantityTypeIdentifierActiveEnergyBurned"],
                "unit": "kcal",
            },
        },
    }


@router.get("/import-history")
async def get_import_history(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    获取导入历史记录

    返回用户过去的Apple Health导入记录
    """
    # 这里应该查询专门的导入历史表
    # 简化返回示例数据
    return {
        "success": True,
        "imports": [
            # 实际项目中应从数据库查询
        ],
        "total_imports": 0,
        "last_import": None,
    }


@router.delete("/records/{record_type}")
async def delete_imported_records(
    record_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    删除已导入的Apple Health数据

    用于数据清理或重新导入
    """
    from datetime import datetime

    from sqlalchemy import and_

    deleted_count = 0

    # 根据类型删除记录
    if record_type == "blood_pressure":
        query = db.query(BloodPressureRecord).filter(
            BloodPressureRecord.user_id == current_user.user_id
        )
        if start_date:
            query = query.filter(BloodPressureRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(BloodPressureRecord.measured_at <= end_date)
        deleted_count = query.delete(synchronize_session=False)

    elif record_type == "heart_rate":
        query = db.query(HeartRateRecord).filter(
            HeartRateRecord.user_id == current_user.user_id
        )
        if start_date:
            query = query.filter(HeartRateRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(HeartRateRecord.measured_at <= end_date)
        deleted_count = query.delete(synchronize_session=False)

    elif record_type == "weight":
        query = db.query(WeightRecord).filter(
            WeightRecord.user_id == current_user.user_id
        )
        if start_date:
            query = query.filter(WeightRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(WeightRecord.measured_at <= end_date)
        deleted_count = query.delete(synchronize_session=False)

    elif record_type == "sleep":
        query = db.query(SleepRecord).filter(
            SleepRecord.user_id == current_user.user_id
        )
        if start_date:
            query = query.filter(SleepRecord.bed_time >= start_date)
        if end_date:
            query = query.filter(SleepRecord.bed_time <= end_date)
        deleted_count = query.delete(synchronize_session=False)

    elif record_type == "glucose":
        query = db.query(GlucoseRecord).filter(
            GlucoseRecord.user_id == current_user.user_id
        )
        if start_date:
            query = query.filter(GlucoseRecord.measured_at >= start_date)
        if end_date:
            query = query.filter(GlucoseRecord.measured_at <= end_date)
        deleted_count = query.delete(synchronize_session=False)

    else:
        raise HTTPException(status_code=400, detail=f"不支持的数据类型: {record_type}")

    db.commit()

    return {
        "success": True,
        "message": f"已删除 {deleted_count} 条{record_type}记录",
        "deleted_count": deleted_count,
        "record_type": record_type,
    }
