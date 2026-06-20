#!/bin/bash
# 🌸 Gitee同步最终脚本 - 若曦V2

set -e

cd /home/admin/workspace/ruoxi-v2

echo "═══════════════════════════════════════════════════════════════"
echo "               🌸 若曦V2 Gitee同步助手"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "【当前状态】"
echo "  本地提交: $(git log --oneline -1 2>/dev/null || echo 'N/A')"
echo "  本地时间: $(git log --format='%cd' --date=format:'%Y-%m-%d %H:%M:%S' -1 2>/dev/null || echo 'N/A')"
echo ""

# 检查Gitee远程
CURRENT_URL=$(git remote get-url gitee 2>/dev/null || echo "")
if [ -z "$CURRENT_URL" ]; then
    echo "⚠️  Gitee远程未配置"
    git remote add gitee "https://gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
    echo "✅ 已添加默认远程"
fi

echo "Gitee远程:"
git remote get-url gitee | sed 's/^/  /'
echo ""

echo "【同步选项】"
echo ""
echo "方式1: 使用用户名密码 (互动式)"
echo "  git push -f gitee main:master"
echo "  然后输入: Username: xingqiongclaw_admin"
echo "           Password: [您的Gitee密码]"
echo ""

echo "方式2: 使用Gitee私人令牌 (推荐)"
echo "  1. 获取令牌: https://gitee.com/profile/personal_access_tokens"
echo "  2. 设置远程:"
echo "     git remote set-url gitee https://xingqiongclaw_admin:令牌@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
echo "  3. 推送: git push -f gitee main:master"
echo ""

echo "方式3: 此脚本自动处理"
read -p "请输入Gitee私人令牌 (没有请直接回车跳过): " GITEE_TOKEN

if [ -n "$GITEE_TOKEN" ]; then
    echo ""
    echo "设置Gitee远程使用令牌..."
    git remote set-url gitee "https://xingqiongclaw_admin:${GITEE_TOKEN}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
    echo "✅ 远程已更新"
    
    echo ""
    echo "开始推送到Gitee master分支..."
    if git push -f gitee main:master; then
        echo ""
        echo "🎉 推送成功!"
        echo "  地址: https://gitee.com/xingqiongclaw_admin/ruoxi-v2"
        echo ""
        echo "验证结果:"
        curl -s "https://gitee.com/api/v5/repos/xingqiongclaw_admin/ruoxi-v2" 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    if 'pushed_at' in d:
        print(f\"  推送时间: {d.get('pushed_at','N/A')[:16].replace('T',' ')}\")
    else:
        print('  验证信息获取失败')
except:
    pass
"
    else
        echo "❌ 推送失败，请检查令牌是否正确"
        exit 1
    fi
else
    echo ""
    echo "⏳ 跳过自动推送"
    echo "请手动执行: git push -f gitee main:master"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
