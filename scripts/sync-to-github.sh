#!/bin/bash
# 🌸 若曦V2 同步到GitHub/Gitee脚本
# 用法: bash scripts/sync-to-github.sh

echo "🌸 开始同步若曦V2到云端..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查git
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ 未找到git命令${NC}"
    exit 1
fi

# GitHub仓库信息
GITHUB_USER="kunlunxingqiong"
GITHUB_REPO="ruoxi-v2"
GITHUB_URL="https://github.com/$GITHUB_USER/$GITHUB_REPO.git"

# Gitee仓库信息
GITEE_USER="xingqiongclaw_admin"
GITEE_REPO="ruoxi-v2"
GITEE_URL="https://gitee.com/$GITEE_USER/$GITEE_REPO.git"

echo "========================================"
echo "📦 仓库信息"
echo "========================================"
echo "GitHub: $GITHUB_URL"
echo "Gitee:  $GITEE_URL"
echo ""

# 检查本地仓库
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠ 初始化本地git仓库...${NC}"
    git init
    git branch -M main
fi

# 配置远程仓库
echo "🔧 配置远程仓库..."
git remote remove github 2>/dev/null
git remote remove gitee 2>/dev/null
git remote add github "$GITHUB_URL"
git remote add gitee "$GITEE_URL"

echo "  ✓ GitHub: $GITHUB_URL"
echo "  ✓ Gitee:  $GITEE_URL"
echo ""

# 添加到暂存区
echo "📁 添加文件到暂存区..."
git add -A
git status -s
echo ""

# 提交更改
COMMIT_MSG="🌸 同步更新: $(date '+%Y-%m-%d %H:%M:%S')

更新内容:
- 整合GitHub AGENT_TEAM.md文档
- 整合Gitee ai-core-tools工具清单
- 新增docs/agent-team.md (Agent团队文档)
- 新增docs/ai-arsenal.md (94项目AI军火库)
- 新增docs/tools-integration.md (工具集成指南)
- 新增config/api-routes.yaml.template (脱敏API配置)
- 更新.gitignore (API配置保护)"

echo "📝 创建提交..."
git commit -m "$COMMIT_MSG" || echo -e "${YELLOW}⚠ 无新更改或已提交${NC}"
echo ""

# 推送到GitHub
echo "☁️ 推送到GitHub..."
if git push github main; then
    echo -e "${GREEN}✅ GitHub推送成功!${NC}"
    echo "   URL: https://github.com/$GITHUB_USER/$GITHUB_REPO"
else
    echo -e "${RED}✗ GitHub推送失败${NC}"
    echo "   可能需要配置git凭证或检查网络"
fi
echo ""

# 推送到Gitee
echo "☁️ 推送到Gitee..."
if git push gitee main; then
    echo -e "${GREEN}✅ Gitee推送成功!${NC}"
    echo "   URL: https://gitee.com/$GITEE_USER/$GITEE_REPO"
else
    echo -e "${RED}✗ Gitee推送失败${NC}"
    echo "   可能需要配置git凭证或检查网络"
fi
echo ""

echo "========================================"
echo -e "${GREEN}🌸 同步完成!${NC}"
echo "========================================"
echo ""
echo "GitHub: https://github.com/$GITHUB_USER/$GITHUB_REPO"
echo "Gitee:  https://gitee.com/$GITEE_USER/$GITEE_REPO"
echo ""
echo "建议操作:"
echo "  1. 访问上述URL确认推送成功"
echo "  2. 在Gitee设置Webhook自动同步到GitHub"
echo "  3. 配置GitHub Actions自动发布"
echo ""
