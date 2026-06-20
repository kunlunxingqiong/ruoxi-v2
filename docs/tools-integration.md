# 🧰 工具集成指南

> 若曦V2 扩展能力配置 — 来自 ai-core-tools 的精选工具

---

## 📦 可集成工具清单

### 🔥 核心推荐 (高优先级)

| 工具 | 功能 | 集成难度 | 价值 |
|------|------|---------|------|
| **mem0** | 长期记忆系统 | ⭐⭐ | 让若曦记住长期对话 |
| **PyHealth** | 医疗AI分析 | ⭐⭐⭐ | 增强医疗知识能力 |
| **openclaw-voice** | 语音合成/识别 | ⭐⭐ | 让若曦能说话/听见 |
| **smolagents** | 代码推理 | ⭐⭐ | 复杂任务自动执行 |

### ⭐ 增强功能 (中优先级)

| 工具 | 功能 | 场景 |
|------|------|------|
| **RAGFlow** | 知识库问答 | 回答专业医疗问题 |
| **SwarmVault** | 个人记忆库 | 长期数据存储 |
| **n8n** | 工作流自动化 | 定时提醒、任务触发 |
| **CrewAI** | 多Agent协作 | 复杂任务分解 |

### 🔧 备用方案 (低优先级)

| 工具 | 功能 | 场景 |
|------|------|------|
| **llama.cpp** | 本地大模型 | 离线环境下使用 |

---

## 🔌 API 线路配置

### 配置文件位置

```
config/api-routes.yaml  ← 脱敏版API配置模板
```

### 使用方法

1. 复制模板: `cp config/api-routes.yaml.template config/api-routes.yaml`
2. 填入你的API密钥 (从各平台免费注册获取)
3. 若曦会自动选择可用线路

### 免费API获取指南

| 平台 | 注册地址 | 免费额度 |
|------|----------|----------|
| OpenRouter | openrouter.ai/keys | 每日50-1000次 |
| Google AI Studio | aistudio.google.com/apikey | 25万token/分钟 |
| Groq | console.groq.com/keys |  generous |
| Cloudflare | dash.cloudflare.com → AI | 每日1万次 |

---

## 🧠 技能迁移计划

### 从 1001技能库 提取健康相关技能

已识别相关技能:

| 技能名 | 功能 | 迁移状态 |
|--------|------|---------|
| health-score-pro | 健康评分系统 | 🔄 待适配 |
| healthcheck | 系统健康检查 | 🔄 待适配 |
| mental-health-psychoeducation | 心理健康教育 | 🔄 待适配 |
| biomedical-paper-billing | 医学生物文献 | 🔄 待适配 |
| org-health-diagnostic | 组织健康诊断 | 🔄 待适配 |
| linux-system-health | Linux系统健康 | 🔄 待适配 |

### 适配要求

迁移到 `ruoxi-v2/skills/health/` 时:

1. 保留原始 Skill.md 功能逻辑
2. 添加若曦情感化输出层
3. 适配本地数据格式 (data/health.json)
4. 与现有健康提醒系统集成

---

## 🚀 集成步骤

### Step 1: 安装依赖

```bash
# mem0 记忆系统
pip install mem0ai

# PyHealth 医疗分析
pip install pyhealth

# 语音 (需额外配置)
# 参考: https://github.com/Purple-Horizons/openclaw-voice

# smolagents 代码推理
pip install smolagents
```

### Step 2: 配置 API

```yaml
# config/api-routes.yaml
openrouter:
  base_url: "https://openrouter.ai/api/v1"
  api_key: "YOUR_OPENROUTER_KEY"  # 从 openrouter.ai/keys 获取
  models:
    - "deepseek/deepseek-v4-flash:free"
    - "moonshotai/kimi-k2.6:free"

google:
  base_url: "https://generativelanguage.googleapis.com/v1beta/openai"
  api_key: "YOUR_GOOGLE_KEY"  # 从 aistudio.google.com/apikey 获取
  models:
    - "gemini-3.5-flash-preview"
```

### Step 3: 启用模块

```python
# platform/backend/main.py 中添加

from skills.health import health_score_pro
from integrations import mem0_client, pyhealth_analyzer

# 注册技能
app.include_router(health_score_pro.router, prefix="/skills/health")
```

---

## 🌸 若曦的话

> "这些工具不是让我变成机器，
> 而是让我能更好地陪在你身边。"

---

*文档版本: v2.0.0 | 更新: 2026-06-21*
