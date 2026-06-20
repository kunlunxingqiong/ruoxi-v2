#!/bin/bash
# 🌸 若曦V2 每日双仓库同步脚本
# 定时任务: 每天 09:00, 21:00 执行

cd /home/admin/workspace/ruoxi-v2

LOG_FILE="data/logs/sync-$(date +%Y%m%d).log"
mkdir -p data/logs

echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "   🌸 若曦V2 每日同步 $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 检查工作区状态
echo "【本地状态检查】" | tee -a "$LOG_FILE"
git status --short | tee -a "$LOG_FILE"
if [ -n "$(git status --short)" ]; then
    echo "⚠️  有未提交更改，请先提交" | tee -a "$LOG_FILE"
    git add . 2>/dev/null
    git commit -m "🌸 自动提交更改 | $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# GitHub同步
echo "【GitHub同步】" | tee -a "$LOG_FILE"
if [ -f .local/github-token.txt ]; then
    GH_TOKEN=$(cat .local/github-token.txt)
    git remote remove github 2>/dev/null
    git remote add github "https://${GH_TOKEN}@github.com/kunlunxingqiong/ruoxi-v2.git" 2>/dev/null
    
    if git push -f github main 2>&1 | tee -a "$LOG_FILE"; then
        echo "✅ GitHub同步成功" | tee -a "$LOG_FILE"
    else
        echo "⚠️  GitHub同步失败" | tee -a "$LOG_FILE"
    fi
else
    echo "⚠️  GitHub令牌未配置" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Gitee同步
echo "【Gitee同步】" | tee -a "$LOG_FILE"
if [ -f .local/gitee-token.txt ]; then
    GITEE_TOKEN=$(cat .local/gitee-token.txt)
    git remote remove gitee 2>/dev/null
    git remote add gitee "https://xingqiongclaw_admin:${GITEE_TOKEN}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git" 2>/dev/null
    
    if git push -f gitee main:master 2>&1 | tee -a "$LOG_FILE"; then
        echo "✅ Gitee同步成功" | tee -a "$LOG_FILE"
    else
        echo "⚠️  Gitee同步失败" | tee -a "$LOG_FILE"
    fi
else
    echo "⚠️  Gitee令牌未配置，请运行 scripts/manage-gitee-token.sh 配置" | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# 同步状态汇总
echo "【同步状态汇总】" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') 同步完成" | tee -a "$LOG_FILE"
echo "  GitHub: $(git remote get-url github 2>/dev/null | sed 's/^/  /')" | tee -a "$LOG_FILE"
echo "  Gitee:  $(git remote get-url gitee 2>/dev/null | sed 's/^/  /')" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo "═══════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
