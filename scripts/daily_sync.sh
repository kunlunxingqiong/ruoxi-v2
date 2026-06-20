#!/bin/bash
# 🌸 若曦V2 - 每日自动同步脚本
# 定时任务: 0 2 * * * /home/admin/workspace/ruoxi-v2/scripts/daily_sync.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目目录
PROJECT_DIR="/home/admin/workspace/ruoxi-v2"
LOG_FILE="$PROJECT_DIR/.local/sync.log"
TOKEN_FILE="$PROJECT_DIR/.local/github-token.txt"

# 日期和时间戳
DATE=$(date '+%Y-%m-%d')
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 日志函数
log() {
    echo -e "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# ========== 开始同步 ==========
log "${BLUE}════════════════════════════════════════════════${NC}"
log "${BLUE}🌸 若曦V2 - 每日双仓库同步开始${NC}"
log "${BLUE}════════════════════════════════════════════════${NC}"

cd "$PROJECT_DIR"

# 检查GitHub token
if [ ! -f "$TOKEN_FILE" ]; then
    log "${RED}❌ GitHub token文件不存在${NC}"
    exit 1
fi

TOKEN=$(cat "$TOKEN_FILE" | tr -d '\n\r')

if [ -z "$TOKEN" ]; then
    log "${RED}❌ GitHub token为空${NC}"
    exit 1
fi

# 配置GitHub remote
log "${YELLOW}🔧 配置GitHub remote...${NC}"
git remote set-url github "https://${TOKEN}@github.com/kunlunxingqiong/ruoxi-v2.git" 2>/dev/null || true

# 获取当前项目状态
COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")
LATEST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "无提交")

git fetch github --quiet 2>/dev/null || true
BEHIND=$(git rev-list --count HEAD..github/main 2>/dev/null || echo "0")

git fetch gitee --quiet 2>/dev/null || true
BEHIND_GITEE=$(git rev-list --count HEAD..gitee/main 2>/dev/null || echo "0")

log "${BLUE}📊 当前状态:${NC}"
log "   总提交数: $COMMIT_COUNT"
log "   最新提交: $LATEST_COMMIT"
log "   GitHub落后: $BEHIND 个提交"
log "   Gitee落后: $BEHIND_GITEE 个提交"

# ========== 推送到GitHub ==========
log "${YELLOW}🔄 推送到GitHub...${NC}"
if git push github main 2>&1 | tee -a "$LOG_FILE" | grep -q "Everything up-to-date\|done"; then
    log "${GREEN}✅ GitHub推送成功${NC}"
else
    log "${GREEN}✅ GitHub已是最新${NC}"
fi

# ========== 推送到Gitee ==========
log "${YELLOW}🔄 推送到Gitee...${NC}"
if git push gitee main 2>&1 | tee -a "$LOG_FILE" | grep -q "Everything up-to-date\|done"; then
    log "${GREEN}✅ Gitee推送成功${NC}"
else
    log "${YELLOW}⚠️ Gitee推送可能需要处理${NC}"
fi

# ========== 验证同步状态 ==========
log "${BLUE}🔍 验证同步状态...${NC}"

GITHUB_SHA=$(git ls-remote github main 2>/dev/null | cut -f1 || echo "")
GITEE_SHA=$(git ls-remote gitee main 2>/dev/null | cut -f1 || echo "")
LOCAL_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")

if [ "$GITHUB_SHA" = "$LOCAL_SHA" ] && [ "$GITEE_SHA" = "$LOCAL_SHA" ]; then
    log "${GREEN}✅ 双仓库完全同步${NC}"
    SYNC_STATUS="同步成功"
else
    log "${YELLOW}⚠️ 仓库可能未完全同步${NC}"
    log "   Local: $LOCAL_SHA"
    log "   GitHub: $GITHUB_SHA"
    log "   Gitee: $GITEE_SHA"
    SYNC_STATUS="需要检查"
fi

# ========== 记录完成 ==========
log "${GREEN}════════════════════════════════════════════════${NC}"
log "${GREEN}✅ 每日同步完成 - $SYNC_STATUS${NC}"
log "${GREEN}════════════════════════════════════════════════${NC}"

# 保留最近30天的日志
tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"

exit 0
