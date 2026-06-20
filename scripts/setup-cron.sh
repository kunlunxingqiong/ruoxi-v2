#!/bin/bash
# 🌸 若曦V2 - 定时任务配置脚本
# 确保每天5%-10%进度更新 (至少5%)

CRON_FILE=".local/ruoxi-cron"
REPO_PATH="/home/admin/workspace/ruoxi-v2"

echo "🌸 配置每日自动同步定时任务..."

# 创建cron任务内容
cat > "$CRON_FILE" << EOF
# 若曦V2 - 每日自动同步 (5%-10%进度保障)
# 每天 09:00 执行双仓库同步
0 9 * * * cd $REPO_PATH && $REPO_PATH/scripts/sync-all-repos.sh >> $REPO_PATH/.local/sync.log 2>&1

# 每天 18:00 执行第二次同步 (确保进度)
0 18 * * * cd $REPO_PATH && $REPO_PATH/scripts/sync-all-repos.sh >> $REPO_PATH/.local/sync.log 2>&1

# 每周日 00:00 执行深度检查
0 0 * * 0 cd $REPO_PATH && python $REPO_PATH/scripts/check_env.py >> $REPO_PATH/.local/check.log 2>&1
EOF

echo "✅ 定时任务配置已生成: $CRON_FILE"
echo ""
echo "安装方式:"
echo "  crontab $CRON_FILE"
echo ""
echo "查看当前任务:"
echo "  crontab -l"
