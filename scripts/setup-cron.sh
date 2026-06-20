#!/bin/bash
# 🌸 若曦V2 定时任务设置脚本

echo "═══════════════════════════════════════════════════════════════"
echo "               🌸 若曦V2 定时任务设置"
echo "═══════════════════════════════════════════════════════════════"
echo ""

PROJECT_DIR="/home/admin/workspace/ruoxi-v2"

# 创建临时crontab内容
CRON_CONTENT="# 🌸 若曦V2 每日定时任务 - $(date '+%Y-%m-%d')
# 每天早上9点: 工作开始前进度检查
0 9 * * * cd ${PROJECT_DIR} && bash scripts/daily-progress-check.sh >> data/logs/cron.log 2>&1

# 每天中午12点: 午间同步
0 12 * * * cd ${PROJECT_DIR} && bash scripts/daily-sync.sh >> data/logs/cron.log 2>&1

# 每天晚上6点: 下班前同步
0 18 * * * cd ${PROJECT_DIR} && bash scripts/daily-sync.sh >> data/logs/cron.log 2>&1

# 每天晚上9点: 晚间检查
0 21 * * * cd ${PROJECT_DIR} && bash scripts/daily-progress-check.sh >> data/logs/cron.log 2>&1
"

echo "【即将添加到crontab的任务】"
echo ""
echo "$CRON_CONTENT"
echo ""

read -p "确认添加到crontab? [Y/n]: " CONFIRM

if [ "$CONFIRM" != "n" ] && [ "$CONFIRM" != "N" ]; then
    # 保存现有crontab
    crontab -l > /tmp/current_crontab.txt 2>/dev/null || echo "# 现有crontab为空" > /tmp/current_crontab.txt
    
    # 添加新任务
    echo "$CRON_CONTENT" >> /tmp/current_crontab.txt
    
    # 安装新crontab
    crontab /tmp/current_crontab.txt
    
    echo ""
    echo "✅ 定时任务已添加！"
    echo ""
    echo "当前crontab:"
    crontab -l | tail -10
    echo ""
    echo "💡 查看日志: tail -f ${PROJECT_DIR}/data/logs/cron.log"
else
    echo ""
    echo "已取消，手动添加方式:"
    echo "  crontab -e"
    echo ""
    echo "然后粘贴以下内容:"
    echo "$CRON_CONTENT"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
