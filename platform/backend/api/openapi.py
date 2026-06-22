"""
🌸 若曦V2 - OpenAPI规范
API文档和Swagger配置
"""

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    自定义OpenAPI Schema

    生成完整的API文档
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="🌸 若曦V2 API",
        version="2.0.0",
        description="""
# 若曦V2 - 你的AI医生朋友

若曦(V2)是一个智能健康助手，提供：

## 核心功能

### 🩺 健康管理
- **血压/血糖追踪** - 长期趋势监测
- **用药提醒** - 个性化服药计划  
- **体检报告解读** - AI智能分析
- **健康目标** - 设定并追踪目标

### 💬 智能对话
- **多模式聊天** - 闲聊/健康咨询/情绪陪伴/专业医疗
- **记忆系统** - 长期记忆关联
- **多模型支持** - Gemini/Groq/Ollama

### 🔔 通知提醒
- **用药提醒** - 💊 曦曦帮你记着呢
- **健康告警** - ⚠️ 异常指标提醒
- **情绪打卡** - 🌸 曦曦想听听你的心情

## 认证

所有API（除公开端点外）需要JWT Token认证：
```
Authorization: Bearer <token>
```

## 限流

API有限流保护，响应头包含：
- `X-RateLimit-Limit` - 限制次数
- `X-RateLimit-Remaining` - 剩余次数
- `Retry-After` - 重试时间（限流时）

## 健康指标

常见健康指标参考：

### 血压 (Blood Pressure)
| 分类 | 收缩压 | 舒张压 |
|------|--------|--------|
| 正常 | <120 | <80 |
| 正常高值 | 120-129 | <80 |
| 高血压1级 | 130-139 | 80-89 |
| 高血压2级 | ≥140 | ≥90 |

### 血糖 (Blood Glucose)
| 时段 | 正常范围 |
|------|----------|
| 空腹 | 3.9-6.1 mmol/L |
| 餐后2小时 | <7.8 mmol/L |

### BMI
| 分类 | 范围 |
|------|------|
| 偏瘦 | <18.5 |
| 正常 | 18.5-23.9 |
| 超重 | 24-27.9 |
| 肥胖 | ≥28 |

## 错误代码

| 代码 | 含义 |
|------|------|
| 400 | 请求参数错误 |
| 401 | 未授权/Token过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 更多

- GitHub: https://github.com/kunlunxingqiong/ruoxi-v2
- License: MIT
        """,
        routes=app.routes,
    )

    # 添加安全定义
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Token认证，在前面添加'Bearer '",
        }
    }

    # 添加标签
    openapi_schema["tags"] = [
        {"name": "认证", "description": "用户登录注册相关接口"},
        {"name": "聊天", "description": "智能对话接口"},
        {"name": "健康数据", "description": "血压、血糖等健康指标管理"},
        {"name": "用户", "description": "用户信息管理"},
        {"name": "设置", "description": "系统配置"},
        {"name": "监控", "description": "系统健康检查和指标"},
        {"name": "数据导入导出", "description": "健康数据上传下载"},
        {"name": "WebSocket", "description": "实时通信接口"},
        {"name": "通知", "description": "消息推送管理"},
    ]

    # 添加服务器信息
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "本地开发环境"},
        {"url": "https://api.ruoxi.example.com", "description": "生产环境"},
    ]

    # 添加联系信息
    openapi_schema["info"]["contact"] = {
        "name": "若曦V2 Team",
        "url": "https://github.com/kunlunxingqiong/ruoxi-v2",
    }

    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_swagger_ui(app: FastAPI):
    """
    配置Swagger UI

    自定义Swagger界面
    """
    from fastapi.openapi.docs import get_swagger_ui_html
    from fastapi.staticfiles import StaticFiles

    # 挂载静态文件
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except:
        pass


# API端点清单
API_ENDPOINTS = {
    "v1": {
        "auth": {
            "login": "POST /api/v1/auth/login - 用户登录",
            "register": "POST /api/v1/auth/register - 用户注册",
            "refresh": "POST /api/v1/auth/refresh - 刷新Token",
            "logout": "POST /api/v1/auth/logout - 退出登录",
        },
        "chat": {
            "send": "POST /api/v1/chat/message - 发送消息",
            "history": "GET /api/v1/chat/history - 获取历史",
            "clear": "DELETE /api/v1/chat/history - 清除历史",
            "emotion": "POST /api/v1/chat/emotion-check - 情绪打卡",
            "modes": "GET /api/v1/chat/modes - 聊天模式",
            "suggestions": "GET /api/v1/chat/suggestions - 建议输入",
        },
        "health": {
            "bp_list": "GET /api/v1/health/bp - 血压列表",
            "bp_create": "POST /api/v1/health/bp - 记录血压",
            "bp_stats": "GET /api/v1/health/bp/stats - 血压统计",
            "glucose_list": "GET /api/v1/health/glucose - 血糖列表",
            "glucose_create": "POST /api/v1/health/glucose - 记录血糖",
            "weight_list": "GET /api/v1/health/weight - 体重列表",
            "weight_create": "POST /api/v1/health/weight - 记录体重",
        },
        "user": {
            "profile": "GET /api/v1/users/me - 我的资料",
            "update": "PUT /api/v1/users/me - 更新资料",
            "settings": "GET /api/v1/users/settings - 用户设置",
            "update_settings": "PUT /api/v1/users/settings - 更新设置",
        },
        "notification": {
            "list": "GET /api/v1/notifications/ - 通知列表",
            "unread": "GET /api/v1/notifications/unread-count - 未读数",
            "mark_read": "POST /api/v1/notifications/{id}/read - 标记已读",
            "test": "POST /api/v1/notifications/test/* - 测试通知",
        },
        "data_io": {
            "preview": "POST /api/v1/data/import/preview - 预览导入",
            "import": "POST /api/v1/data/import - 执行导入",
            "template": "GET /api/v1/data/import/templates/{type} - 下载模板",
            "export": "GET /api/v1/data/export - 导出数据",
            "report": "GET /api/v1/data/export/report - 健康报告",
        },
        "monitoring": {
            "health": "GET /api/v1/monitoring/health - 健康检查",
            "ready": "GET /api/v1/monitoring/ready - 就绪检查",
            "metrics": "GET /api/v1/monitoring/metrics - 系统指标",
            "cache": "GET /api/v1/monitoring/cache/stats - 缓存统计",
            "clear_cache": "POST /api/v1/monitoring/cache/clear - 清除缓存",
        },
        "websocket": {
            "chat": "WS /api/v1/ws/chat - 实时聊天",
            "notifications": "WS /api/v1/ws/notifications - 实时通知",
            "stats": "GET /api/v1/ws/stats - 连接统计",
        },
    }
}


def generate_api_markdown() -> str:
    """
    生成API文档Markdown

    用于README或文档网站
    """
    md = """# 🌸 若曦V2 API 文档

## 认证

所有API需要JWT Token：
```
Authorization: Bearer <your-token>
```

## 端点列表

### 认证接口
| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 | 公开 |
| POST | `/api/v1/auth/register` | 注册 | 公开 |
| POST | `/api/v1/auth/refresh` | 刷新Token | 已登录 |

### 聊天接口
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/chat/message` | 发送消息 |
| GET | `/api/v1/chat/history` | 获取历史 |
| POST | `/api/v1/chat/emotion-check` | 情绪打卡 |

### 健康数据
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/health/bp` | 血压列表 |
| POST | `/api/v1/health/bp` | 记录血压 |
| GET | `/api/v1/health/glucose` | 血糖列表 |
| POST | `/api/v1/health/glucose` | 记录血糖 |

### 通知
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/notifications/` | 通知列表 |
| GET | `/api/v1/notifications/unread-count` | 未读数 |
| POST | `/api/v1/notifications/{id}/read` | 标为已读 |

### 数据导入导出
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/data/import/preview` | 预览导入 |
| POST | `/api/v1/data/import` | 执行导入 |
| GET | `/api/v1/data/export` | 导出数据 |

### WebSocket
| 协议 | 端点 | 描述 |
|------|------|------|
| WS | `/api/v1/ws/chat` | 实时聊天 |
| WS | `/api/v1/ws/notifications` | 实时通知 |

### 监控
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/monitoring/health` | 健康检查 |
| GET | `/api/v1/monitoring/metrics` | 系统指标 |

## 错误处理

错误响应格式：
```json
{
  "error": "错误代码",
  "message": "错误描述",
  "details": {}
}
```

## 限流

限流Headers：
- `X-RateLimit-Limit`: 请求上限
- `X-RateLimit-Remaining`: 剩余次数
- `Retry-After`: 重试等待秒数

---
📄 [查看完整Swagger文档]()
"""
    return md
