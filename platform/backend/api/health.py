"""
🌸 若曦V2 健康检查端点
监控服务状态，确保一切正常
"""
from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict, Any, Optional
import platform
import sys

from core.config_manager import config
from core.log_manager import get_logger

logger = get_logger(__name__)

# 创建路由器
router = APIRouter()


class HealthChecker:
    """健康检查器 - 检查各组件状态"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.checks = {
            "database": self._check_database,
            "config": self._check_config,
            "memory": self._check_memory,
        }
    
    def _check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            from core.database_models import db
            # 简单测试数据库连接
            session = db.get_session()
            if session:
                session.close()
                return {"status": "ok", "message": "数据库连接正常"}
            return {"status": "warning", "message": "数据库会话未初始化"}
        except Exception as e:
            return {"status": "error", "message": f"数据库错误: {str(e)}"}
    
    def _check_config(self) -> Dict[str, Any]:
        """检查配置加载"""
        try:
            required_keys = ["app.name", "app.version", "ai.default_model"]
            for key in required_keys:
                if config.get(key) is None:
                    return {"status": "error", "message": f"缺少必要配置: {key}"}
            return {"status": "ok", "message": "配置加载正常"}
        except Exception as e:
            return {"status": "error", "message": f"配置错误: {str(e)}"}
    
    def _check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > 90:
                status = "warning"
            elif usage_percent > 95:
                status = "critical"
            else:
                status = "ok"
            
            return {
                "status": status,
                "message": f"内存使用 {usage_percent}%",
                "details": {
                    "total_mb": memory.total // (1024 * 1024),
                    "available_mb": memory.available // (1024 * 1024),
                    "percent": usage_percent
                }
            }
        except ImportError:
            return {"status": "unknown", "message": "psutil未安装，无法检查内存"}
        except Exception as e:
            return {"status": "error", "message": f"内存检查错误: {str(e)}"}
    
    def get_status(self) -> Dict[str, Any]:
        """获取完整健康状态"""
        # 运行所有检查
        component_status = {}
        overall_status = "ok"
        
        for name, check_func in self.checks.items():
            try:
                component_status[name] = check_func()
                if component_status[name]["status"] == "error":
                    overall_status = "error"
                elif component_status[name]["status"] == "warning" and overall_status == "ok":
                    overall_status = "warning"
            except Exception as e:
                component_status[name] = {"status": "error", "message": str(e)}
                overall_status = "error"
        
        # 计算运行时间
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "version": config.get("app.version"),
            "components": component_status
        }


# 全局健康检查器
health_checker = HealthChecker()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    基础健康检查 - 快速返回服务状态
    
    返回示例:
    ```json
    {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": "2026-06-21T02:56:44.123456"
    }
    ```
    """
    return {
        "status": "healthy",
        "version": config.get("app.version"),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def health_check_detailed():
    """
    详细健康检查 - 包含各组件状态
    
    检查项:
    - database: 数据库连接状态
    - config: 配置加载状态  
    - memory: 内存使用状态
    
    返回示例:
    ```json
    {
        "status": "ok",
        "timestamp": "...",
        "uptime_seconds": 123,
        "version": "2.0.0",
        "components": {
            "database": {"status": "ok", "message": "..."},
            "config": {"status": "ok", "message": "..."},
            "memory": {"status": "ok", "message": "..."}
        }
    }
    ```
    """
    return health_checker.get_status()


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    就绪检查 - 用于Kubernetes等编排系统
    
    当服务准备好接收流量时返回200
    """
    status_info = health_checker.get_status()
    
    if status_info["status"] == "error":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=status_info
        )
    
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    存活检查 - 用于Kubernetes等编排系统
    
    当服务正常运行时返回200
    即使某些组件有问题，只要服务还在运行就返回200
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics():
    """
    性能指标 - 用于监控系统
    
    返回基本的系统指标
    """
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "memory": {
                "total_mb": memory.total // (1024 * 1024),
                "available_mb": memory.available // (1024 * 1024),
                "percent": memory.percent
            },
            "cpu": {
                "percent": cpu_percent
            },
            "python": {
                "version": sys.version,
                "platform": platform.platform()
            }
        }
    except ImportError:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "note": "psutil未安装，无法获取详细指标"
        }


if __name__ == "__main__":
    # 测试健康检查
    print("=" * 60)
    print("🌸 若曦V2 健康检查测试")
    print("=" * 60)
    
    import asyncio
    
    async def test():
        print("\n基础健康检查:")
        print(await health_check())
        
        print("\n详细健康检查:")
        print(await health_check_detailed())
        
        print("\n指标:")
        print(await metrics())
    
    asyncio.run(test())
    
    print("\n" + "=" * 60)
