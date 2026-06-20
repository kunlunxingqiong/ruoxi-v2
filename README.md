<div align="center">

# 🌸 若曦V2 - 健康AI助手

*你的AI医生朋友 · 安静陪在你身边*

[![CI/CD](https://github.com/kunlunxingqiong/ruoxi-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/kunlunxingqiong/ruoxi-v2/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](README_EN.md) | [简体中文](README.md)

</div>

---

## 🌟 项目简介

**若曦V2** 是一个基于 **FastAPI + React** 构建的智能健康管理系统，提供全面的健康数据追踪、AI驱动的健康分析和个性化的健康建议。

> "我不是医生，但我是你的AI医生朋友。"
> 
> — 林若曦

### 核心特性

| 特性 | 描述 | 状态 |
|------|------|------|
| 💜 **健康记录** | 血压、血糖、体重、睡眠、心率全面记录 | ✅ |
| 🔔 **智能提醒** | 用药提醒、健康检查提醒 | ✅ |
| 📊 **数据可视化** | 趋势分析、健康评分、图表展示 | ✅ |
| 🧠 **AI分析** | 多模型AI健康建议 (Gemini/Groq/Ollama) | ✅ |
| 📱 **实时通知** | WebSocket实时健康警报 | ✅ |
| 📄 **PDF报告** | 专业级健康报告生成 | ✅ |
| 🍎 **Apple Health** | iOS健康数据导入 | ✅ |
| 🐳 **Docker部署** | 一键容器化部署 | ✅ |

---

## 🚀 快速开始

### 使用 Docker Compose (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/kunlunxingqiong/ruoxi-v2.git
cd ruoxi-v2

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库密码等

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 访问应用
# API文档: http://localhost:8000/docs
# Grafana: http://localhost:3000 (admin/admin)
```

### 手动安装

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库
# 创建 PostgreSQL 数据库
createdb ruoxi_health

# 4. 运行迁移
alembic upgrade head

# 5. 启动服务
uvicorn platform.backend.main:app --reload
```

---

## 📁 项目结构

```
ruoxi-v2/
├── 📂 core/                      # 核心业务逻辑
│   ├── ai/                       # AI模型集成
│   ├── services/                 # 业务服务层
│   ├── health/                   # 健康管理
│   └── export/                   # 数据导出
├── 📂 platform/                  # 平台层
│   └── backend/                  # 后端API
│       ├── api/v1/              # API端点
│       ├── core_auth/           # 认证系统
│       └── middleware/          # 中间件
├── 📂 models/                    # 数据库模型
├── 📂 frontend/                  # React前端组件
│   └── components/              # UI组件
├── 📂 tests/                     # 测试套件
├── 📂 docker/                    # Docker配置
├── 📂 docs/                      # 文档
├── 📂 .github/workflows/        # CI/CD配置
└── 📄 docker-compose.yml         # Docker编排
```

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (React)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ HealthReport│  │ Realtime    │  │ Dashboard          │  │
│  │ HealthRecord│  │ Notifications│ │ Charts             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API网关 (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Auth     │  │ Health   │  │ Medication│  │ Reports  │    │
│  │ WebSocket│  │ Apple    │  │ AI Models │  │ Timeline │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│  PostgreSQL  │      │    Redis     │     │   Celery     │
│   (主数据库)  │      │ (缓存+队列)   │     │  (任务队列)   │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
           ┌────────────────────────────────┐
           │      Prometheus + Grafana      │
           │        (监控+可视化)            │
           └────────────────────────────────┘
```

---

## 🔌 API 端点

### 认证
```
POST   /api/auth/register           # 用户注册
POST   /api/auth/login              # 用户登录
GET    /api/auth/me                 # 获取当前用户
```

### 健康记录
```
GET    /api/v1/health/blood-pressure           # 获取血压记录
POST   /api/v1/health/blood-pressure           # 创建血压记录
GET    /api/v1/health/blood-pressure/statistics # 血压统计

GET    /api/v1/health/glucose                  # 血糖记录
POST   /api/v1/health/glucose                  # 创建血糖记录

GET    /api/v1/health/weight                   # 体重记录
POST   /api/v1/health/weight                   # 创建体重记录

GET    /api/v1/health/sleep                    # 睡眠记录
POST   /api/v1/health/sleep                    # 创建睡眠记录
```

### 健康报告
```
POST   /api/v1/reports/generate       # 生成健康报告
GET    /api/v1/reports/weekly         # 获取周报
GET    /api/v1/reports/monthly        # 获取月报
GET    /api/v1/reports/health-score    # 健康评分
GET    /api/v1/reports/trends         # 趋势数据
```

### 用药管理
```
GET    /api/v1/medications            # 获取用药列表
POST   /api/v1/medications            # 创建用药
POST   /api/v1/medications/{id}/logs  # 记录服药
```

### WebSocket
```
WS     /ws/health                     # 健康数据实时流
WS     /ws/notifications              # 通知连接
```

**完整API文档**: http://localhost:8000/docs (Swagger UI)

---

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_health_records.py -v

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html

# 代码质量检查
black --check .
isort --check-only .
flake8 .
mypy core/
```

---

## 🔒 安全

- **认证**: JWT Token认证
- **密码**: bcrypt哈希
- **API**: 速率限制保护
- **容器**: 非root运行
- **扫描**: Bandit安全扫描集成

---

## 📈 监控

访问以下地址查看监控面板:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (默认账号: admin/admin)
- **API Metrics**: http://localhost:8000/metrics

---

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤:

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - 数据库ORM
- [Celery](https://docs.celeryq.dev/) - 分布式任务队列
- [React](https://react.dev/) - 前端框架

---

<div align="center">

**Made with 💜 by 若曦**

*关注我，关注健康*

</div>
