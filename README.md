# 🌸 若曦V2 - 你的AI医生朋友

<div align="center">

![若曦](https://img.shields.io/badge/若曦-V2.0.0-ff6b9d?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<br>

<img src="https://via.placeholder.com/200x200/ff6b9d/ffffff?text=🌸" width="150" style="border-radius: 50%;">

<br>

**一款有记忆、懂情感、会关心你健康的AI助手**

[English](./README_EN.md) | [文档](https://docs.ruoxi.ai) | [演示](https://demo.ruoxi.ai)

</div>

---

## ✨ 特性

### 💜 温柔陪伴
- **长期记忆** - 若曦会记住你的喜好、习惯和故事
- **情感陪伴** - 10种情绪识别，温暖回应你的每一刻
- **多轮对话** - 话题连贯，就像和老朋友聊天

### 🏥 健康守护
- **数据分析** - 血压、血糖、睡眠数据分析
- **AI报告** - 个性化健康建议和风险评估
- **趋势追踪** - 可视化健康趋势图

### 🤖 智能大脑
- **多模型** - Gemini + Groq + Together + Ollama 智能调度
- **永远在线** - 4级故障转移，确保稳定响应
- **流式输出** - 打字机效果，更真实的聊天体验

### 🔒 安全可靠
- **JWT认证** - 安全的用户身份验证
- **请求限流** - 保护API免受滥用
- **熔断降级** - 优雅处理服务异常

---

## 🚀 快速开始

### 后台部署

```bash
# 1. 克隆项目
git clone https://github.com/kunlunxingqiong/ruoxi-v2.git
cd ruoxi-v2

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API密钥

# 4. 启动服务
cd platform/backend
python main.py
```

服务将在 http://localhost:8000 启动

### 前端部署

```bash
cd frontend
npm install
npm run dev
```

前端将在 http://localhost:3000 启动

### Docker部署

```bash
# 一键启动所有服务
docker-compose up -d
```

---

## 📚 项目结构

```
ruoxi-v2/
├── core/                    # 核心模块
│   ├── ai/                 # AI模型管理
│   ├── memory/             # 向量记忆系统
│   ├── health/             # 健康分析
│   ├── emotion/            # 情感分析
│   └── cache/              # 多级缓存
├── platform/backend/       # FastAPI后端
│   ├── api/                # REST API
│   ├── websocket/          # WebSocket
│   └── main.py             # 入口
├── frontend/               # React前端
│   ├── src/                # 源码
│   └── package.json        # 依赖
├── tests/                  # 测试
├── docker/                 # 部署配置
└── docs/                   # 文档
```

---

## 📝 API文档

启动服务后访问 `

---

## 📝 API文档


启动服务后访问 http://localhost:8000/docs 查看交互式API文档

### 主要端点

```
POST /api/v1/auth/login          # 登录
POST /api/v1/chat                # 聊天
POST /api/v1/chat/stream         # 流式聊天
GET  /api/v1/health-ai/analyze   # 健康分析
GET  /api/v1/emotion/analyze     # 情感分析
```

---

## 🛠️ 技术栈

### 后端
- **FastAPI** - 高性能Web框架
- **SQLAlchemy** - ORM
- **ChromaDB** - 向量数据库
- **Redis** - 缓存

### 前端
- **React 18** + TypeScript
- **Vite** - 构建工具
- **Tailwind CSS** - 样式
- **Framer Motion** - 动画

### AI
- **Gemini** - Google (首选)
- **Groq** - Llama (极速)
- **Together/Cohere** - 备选
- **Ollama** - 本地部署

---

## 🤝 贡献

欢迎提交Issue和PR！

1. Fork 本仓库
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 📄 许可证

[MIT License](./LICENSE)

---

## 💜 致谢

感谢所有贡献者和用户，让若曦变得更加温柔。

<div align="center">

**Made with ❤️+🌸+🤖 in China**

<p>
  <a href="https://github.com/kunlunxingqiong/ruoxi-v2">⭐ Star 支持项目</a>
</p>

</div>
