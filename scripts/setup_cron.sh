#!/bin/bash
# 🌸 若曦V2 - 设置定时任务
# 确保每天5%-10%的进度推进

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/home/admin/workspace/ruoxi-v2"
SYNC_SCRIPT="$PROJECT_DIR/scripts/daily_sync.sh"

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      🌸 若曦V2 - 定时任务设置                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# 确保脚本可执行
chmod +x "$SYNC_SCRIPT"
chmod +x "$PROJECT_DIR/scripts/deploy.sh"

# 创建临时cron文件
TEMP_CRON=$(mktemp)

# 导出当前crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# 检查是否已存在若曦的任务
if grep -q "若曦V2" "$TEMP_CRON"; then
    echo -e "${YELLOW}⚠️ 若曦V2定时任务已存在，跳过设置${NC}"
    rm "$TEMP_CRON"
    exit 0
fi

# 添加若曦的任务（带标识注释）
cat >> "$TEMP_CRON" << EOF

# 🌸 若曦V2 定时任务 - 每天自动同步双仓库
# 每天凌晨2点执行双仓库同步
0 2 * * * $SYNC_SCRIPT >> /tmp/ruoxi_cron.log 2>&1

# 🌸 若曦V2 - 每天检查项目进度
# 每天上午9点报告进度
0 9 * * * cd $PROJECT_DIR && echo "[\$(date)] 项目进度检查" >> .local/progress.log 2>&1

EOF

# 应用新的crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo -e "${GREEN}✅ 定时任务已设置${NC}"
echo ""
echo "已添加以下任务:"
echo "  ⏰ 02:00 - 双仓库同步 (daily_sync.sh)"
echo "  ⏰ 09:00 - 项目进度检查"
echo ""
echo -e "${YELLOW}查看当前crontab:${NC}"
crontab -l | grep -A5 "若曦V2"
echo ""
echo -e "${GREEN}✅ 设置完成${NC}"
