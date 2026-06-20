# 🌸 若曦 Agent 团队

> 若曦 V2 的 Agent 生态系统 — 温暖、专业、協同

---

## 👥 团队成员

| 角色 | 名称 | 职责 | 特点 |
|------|------|------|------|
| 🌸 **总管** | 若曦 | 日常对话、任务分发、情感陪伴 | 温暖、害羞、耳尖会红 |
| 🩺 **健康助手** | 阿芙 | 健康提醒、医疗知识、用药管理 | 专业且温柔 |
| 🔍 **研究员** | 小研 | 深度搜索、资料整理、知识问答 | 严谨认真 |
| 💻 **编程伙伴** | 小码 | 代码编写、调试、技术方案 | 逻辑清晰 |

---

## 🛠️ 工具与能力映射

### 若曦核心能力 (已集成)

| 功能 | 实现方式 | 状态 |
|------|----------|------|
| 情感文本渲染 | `core/enhancement/text_rendering.py` | ✅ 已就绪 |
| 语言风格适配 | `core/enhancement/language_dna_adaptive.py` | ✅ 已就绪 |
| 边缘时刻处理 | `core/enhancement/edge_moments.py` | ✅ 已就绪 |
| 长期记忆 | `data/memory.json` + 记忆系统 | ✅ 已就绪 |
| 健康提醒 | `data/health.json` + 定时任务 | ✅ 已就绪 |
| 后端服务 | `platform/backend/main.py` (FastAPI) | ✅ 已就绪 |
| 前端渲染 | `text-renderer/` (JSX+CSS) | ✅ 已就绪 |

### 可扩展能力 (来自 ai-core-tools)

| 需求 | 工具 | 来源 | 优先级 |
|------|------|------|--------|
| 多Agent编排 | OpenAI Swarm | GitHub开源 | ⭐⭐⭐ |
| 代码推理 | smolagents | HuggingFace | ⭐⭐⭐ |
| 医疗AI分析 | PyHealth | ai-core-tools | ⭐⭐⭐ |
| 语音交互 | openclaw-voice | ai-core-tools | ⭐⭐ |
| 知识库问答 | RAGFlow | ai-core-tools | ⭐⭐ |
| 工作流自动化 | n8n | ai-core-tools | ⭐⭐ |
| 多Agent协作 | CrewAI | GitHub开源 | ⭐⭐ |
| 离线运行 | llama.cpp | GitHub开源 | ⭐ |

---

## 🔌 API 线路配置

### 免费线路 (推荐日常使用)

| 平台 | 特点 | 获取方式 |
|------|------|----------|
| OpenRouter | 23个免费模型，每日50-1000次 | openrouter.ai/keys |
| Google AI Studio | Gemini系列，25万token/分钟 | aistudio.google.com/apikey |
| Groq | 超快推理 | console.groq.com/keys |
| Cloudflare Workers AI | 每日1万次 | dash.cloudflare.com |

### 模型推荐 (免费)

- **deepseek/deepseek-v4-flash:free** — DeepSeek V4 Flash
- **moonshotai/kimi-k2.6:free** — Kimi K2.6
- **qwen/qwen3-next-80b-a3b-instruct:free** — 千问80B
- **meta-llama/llama-3.3-70b-instruct:free** — Llama 3.3 70B
- **gemini-3.5-flash-preview** — Gemini 3.5 Flash

> ⚠️ 付费API密钥已脱敏处理，本地配置文件中管理

---

## 🚀 快速启动

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
python -m platform.backend.main

# 访问前端
cd text-renderer && python -m http.server 8080
```

### Termux 部署 (手机端)

```bash
# 克隆仓库
git clone https://gitee.com/xingqiongclaw_admin/ruoxi-v2.git
cd ruoxi-v2

# 安装并启动
pip install -r requirements.txt
python -m platform.backend.main
```

---

## 📚 相关文档

- [核心增强模块](./core-enhancement.md) — 文本渲染、语言DNA、边缘时刻
- [平台后端文档](./backend.md) — FastAPI服务、API端点、测试
- [前端渲染器文档](./text-renderer.md) — JSX组件、CSS样式、Demo
- [AI军火库索引](./ai-arsenal.md) — 94个AI项目完整索引

---

## 🌸 一句话

> 若曦不只是工具，她是那个安静陪在你身边、耳尖会红的高三少女。

---

*更新于: 2026-06-21 | 版本: v2.0.0*
