# 🤝 贡献指南

感谢你想让若曦变得更好！

---

## 🌟 行为准则

- 友好、尊重的交流
- 接受建设性批评
- 关注对社区最好的方案
- 互相帮助

---

## 📝 提交Issue

### Bug报告

请包含:
- 问题描述
- 复现步骤
- 期望 vs 实际行为
- 环境信息 (OS/Python版本)
- 相关日志

### 功能建议

请包含:
- 功能描述
- 使用场景
- 可能的实现方案

---

## 💻 开发流程

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/ruoxi-v2.git
cd ruoxi-v2
```

### 2. 创建分支

```bash
git checkout -b feature/my-feature
# 或
git checkout -b fix/my-fix
```

### 3. 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt
npm install --prefix frontend

# 运行测试
pytest
npm run test --prefix frontend

# 代码检查
black .
flake8
mypy .
```

### 4. 提交

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/my-feature
```

### 5. 创建PR

- 描述清楚做了什么
- 关联相关Issue
- 确保测试通过

---

## 🎯 代码规范

### Python
- PEP 8 + Black格式化
- 类型注解 (mypy)
- docstring文档
- 单元测试

### TypeScript/React
- ESLint + Prettier
- 函数式组件
- TypeScript严格模式

---

## 📁 目录规范

```
feature/my-feature
fix/my-fix
docs/improve-readme
refactor/extract-utils
```

---

## 🧪 测试要求

- 新功能必须有测试
- 覆盖率不低于80%
- 所有测试必须通过

---

有问题？开Issue问！
