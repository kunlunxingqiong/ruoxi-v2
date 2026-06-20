# 🌸 若曦V2 - 贡献指南

感谢您对若曦V2的兴趣！以下是参与贡献的指南。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境搭建](#开发环境搭建)
- [提交规范](#提交规范)
- [代码规范](#代码规范)
- [PR流程](#pr流程)

## 🤝 行为准则

- 尊重所有参与者
- 建设性的沟通和反馈
- 聚焦于技术讨论
- 帮助新人融入社区

## 🎯 如何贡献

### 报告问题

使用 GitHub Issues 报告 bug 或功能请求：

1. 检查是否已有相同问题
2. 使用问题模板创建新Issue
3. 提供详细描述和复现步骤
4. 标注相关标签

### 提交代码

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add: AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 🛠️ 开发环境搭建

### 后端

```bash
# 克隆代码
git clone https://github.com/kunlunxingqiong/ruoxi-v2.git
cd ruoxi-v2

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
python -m platform.backend.main
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev
```

### Docker 方式

```bash
# 启动完整环境
docker-compose -f docker/docker-compose.dev.yml up -d
```

## ✏️ 提交规范

提交信息格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (Type)

- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```bash
feat(chat): 添加情绪识别功能

- 实现情绪分析API
- 前端添加情绪选择器
- 更新系统提示词

Fixes #123
```

## 📐 代码规范

### Python

遵循 PEP 8 规范：
- 使用 4 空格缩进
- 行长度不超过 100 字符
- 有意义的命名

```python
# 函数命名：snake_case
def calculate_blood_pressure_status(systolic: int, diastolic: int) -> str:
    """计算血压状态"""
    if systolic < 120 and diastolic < 80:
        return "normal"
    # ...
```

检查工具：
```bash
flake8 .
black --check .
isort --check-only .
```

### TypeScript/React

遵循 ESLint + Prettier：
- 使用 2 空格缩进
- 单引号
- 尾随逗号

```typescript
// 组件命名：PascalCase
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  userId,
  apiBaseUrl,
}) => {
  // ...
};
```

检查工具：
```bash
npm run lint
npm run format:check
```

## 🧪 测试要求

### 覆盖率标准

- 核心模块：≥85%
- API端点：≥80%
- 前端组件：≥70%

### 运行测试

```bash
# 后端测试
pytest --cov=. --cov-report=html

# 前端测试
npm run test -- --coverage
```

## 📥 PR流程

1. **创建PR** - 填写PR模板，描述改动内容
2. **自动化检查** - 等待CI通过
3. **代码审查** - 至少1人review通过
4. **合并** - 维护者合并到main分支

### PR模板

```markdown
## 描述
简要描述本次改动

## 改动类型
- [ ] 🐛 Bug修复
- [ ] ✨ 新功能
- [ ] 📚 文档更新
- [ ] ♻️ 代码重构
- [ ] 🧪 测试相关

## 检查清单
- [ ] 代码通过本地测试
- [ ] 文档已同步更新
- [ ] 遵循代码规范
- [ ] 提交信息规范

## 相关Issue
Closes #123
```

## 🏷️ 分支策略

```
main              # 生产分支
├── develop       # 开发分支
├── feature/*     # 功能分支
├── bugfix/*      # Bug修复分支
└── hotfix/*      # 紧急修复分支
```

## 🙋 需要帮助？

- 技术问题：创建 GitHub Discussion
- Bug报告：创建 GitHub Issue
- 聊天交流：加入我们的社区群

---

**谢谢你的贡献！🌸**

每一份贡献都让若曦变得更智能、更温暖。
