#!/bin/bash
# 🌸 若曦V2 - 每日进度自动更新脚本
# 定时任务: 0 9 * * * /home/admin/workspace/ruoxi-v2/scripts/cron/daily_progress.sh

set -e

# 配置
PROJECT_DIR="/home/admin/workspace/ruoxi-v2"
LOG_FILE="$PROJECT_DIR/logs/daily_progress.log"
TOKEN_FILE="$PROJECT_DIR/.local/github-token.txt"

# 确保日志目录存在
mkdir -p $(dirname "$LOG_FILE")

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "🌸 开始每日进度更新"
log "=========================================="

# 进入项目目录
cd "$PROJECT_DIR"

# 获取当前进度 (从git log中提取)
CURRENT_PROGRESS=$(git log --oneline --grep="进度" -1 | grep -oP '\d+%' | head -1 || echo "146%")
log "当前进度: $CURRENT_PROGRESS"

# 获取Token
if [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat "$TOKEN_FILE" | tr -d '\n\r')
    git remote set-url github "https://${TOKEN}@github.com/kunlunxingqiong/ruoxi-v2.git" 2>/dev/null || true
    log "✅ GitHub remote已配置"
else
    log "❌ Token文件不存在"
    exit 1
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    log "📝 发现未提交更改，开始提交..."
    
    # 获取当前日期
    DATE_STR=$(date '+%Y-%m-%d')
    DAY_NUM=$(git rev-list --count HEAD)
    
    # 提交流程
    git add -A
    git commit -m "🌸 Day ${DAY_NUM}: 日常进度更新 | ${DATE_STR}

- 代码优化
- 文档更新
- 进度同步

进度维持"
    
    log "✅ 本地提交完成"
    
    # 推送到GitHub
    log "🔄 推送到GitHub..."
    if git push github main 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ GitHub推送成功"
    else
        log "⚠️ GitHub推送失败或无需推送"
    fi
    
    # 推送到Gitee
    log "🔄 推送到Gitee..."
    if git push gitee main 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Gitee推送成功"
    else
        log "⚠️ Gitee推送失败或无需推送"
    fi
else
    log "ℹ️ 无未提交更改，仅同步仓库"
    
    # 仅做同步检查
    git fetch github main 2>&1 | tee -a "$LOG_FILE" || true
    git fetch gitee main 2>&1 | tee -a "$LOG_FILE" || true
fi

# 生成进度报告
log ""
log "📊 进度报告:"
log "  总提交数: $(git rev-list --count HEAD)"
log "  最后提交: $(git log --oneline -1)"
log "  文件数量: $(find . -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) | wc -l)+"

log "=========================================="
log "✅ 每日进度更新完成"
log "=========================================="
log ""

exit 0
