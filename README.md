# 🌸 若曦V2 - 你的AI医生朋友

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14+-000000.svg)](https://nextjs.org)

> 林若曦，17岁高三少女，恰好学会医术。安静陪在你身边，帮你处理健康事务，偶尔露出一点天真的小破绽。

## ✨ 核心功能

### 🩺 健康管理
- **体检报告解读** - AI智能分析各项指标
- **血压/血糖追踪** - 长期趋势监测
- **用药提醒** - 个性化服药计划
- **健康目标** - 设定并追踪健康目标

### 💬 智能对话
- **多模式聊天** - 闲聊/健康咨询/情绪陪伴/专业医疗
- **记忆系统** - 长期记忆关联，记住你的偏好
- **多模型支持** - Gemini/Groq/Ollama自由切换
- **实时通信** - WebSocket即时消息

### 🔔 智能提醒
- **用药提醒** - 💊 到时间了，曦曦帮你记着呢
- **健康告警** - ⚠️ 异常指标及时提醒
- **情绪打卡** - 🌸 曦曦想听听你今天的心情
- **复查提醒** - 📅 定期检查不遗漏

## 🏗️ 技术架构

```
ruoxi-v2/
├── core/                    # 核心引擎
│   ├── ai/                 # AI模型管理 (Gemini/Groq/Ollama)
│   ├── chat/               # 聊天引擎
│   ├── memory/             # 记忆系统 (Vector DB)
│   ├── cache/              # 缓存系统 (Memory/Redis)
│   ├── rate_limit/         # 限流系统
│   ├── monitoring/         # 性能监控
│   ├── websocket/          # WebSocket管理
│   └── notification/       # 通知服务
├── platform/               # 平台层
│   └── backend/
│       └── api/v1/         # RESTful API
├── frontend/               # 前端
│   └── components/         # React组件
├── docker/                 # Docker配置
└── tests/                  # 测试套件
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### 安装

```bash
# 克隆仓库
git clone https://github.com/kunlunxingqiong/ruoxi-v2.git
cd ruoxi-v2

# 安装依赖
pip install -r requirements.txt

# 启动服务
./scripts/deploy.sh
```

### Docker部署

```bash
# 生产环境
docker-compose -f docker/docker-compose.yml up -d

# 开发环境
docker-compose -f docker/docker-compose.dev.yml up -d
```

## 📡 API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat/message` | POST | 发送聊天消息 |
| `/api/v1/health/bp` | GET/POST | 血压管理 |
| `/api/v1/health/glucose` | GET/POST | 血糖管理 |
| `/api/v1/notifications/` | GET | 通知列表 |
| `/ws/chat` | WebSocket | 实时聊天 |
| `/monitoring/health` | GET | 健康检查 |

## 🤖 AI模型支持

| 提供商 | 模型 | 免费额度 |
|--------|------|----------|
| **Gemini** | gemini-2.0-flash | 60 req/min |
| | gemini-1.5-pro | 可用 |
| **Groq** | llama-3.3-70b | 14400 req/day |
| | llama-3.1-8b | 14400 req/day |
| **Ollama** | llama3/qwen2.5 | 本地无限 |

## 🌸 若曦是谁

**本名**：林若曦
- 姓林，有树木的安静和清朗
- 若曦——像晨曦，天刚亮时那一层薄薄的、有点害羞的光

**身份**：
- 🩺 作为AI医生朋友（阿芙）- 专业健康助手
- 🌸 作为高三少女（若曦）- 安静陪伴的朋友

**特点**：
- 安静，话不多，甜在骨不在皮
- 害羞时耳尖会泛红
- 开心时绞手指，紧张时轻轻跺脚
- 晚安会说"明天见"，像是重要的约定

## 📜 开源协议

MIT License - 详见 [LICENSE](LICENSE)

## 🤝 贡献

欢迎提交Issue和PR！让我们一起让若曦变得更好。

## 💜 致谢

感谢所有开源项目和社区的支持。

---

**🌸 其实她一直在 - 若曦V2**
