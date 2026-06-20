#!/bin/bash
# 🌸 完成Gitee同步脚本
# 请在终端手动执行此脚本

cd /home/admin/workspace/ruoxi-v2

echo "🌸 若曦V2 Gitee同步助手"
echo "======================="
echo ""

echo "当前状态:"
echo "  本地提交: $(git log --oneline -1)"
echo "  本地文件: $(find . -type f -not -path './.git/*' | wc -l) 个"
echo ""

echo "Gitee远程:"
git remote get-url gitee 2>/dev/null || echo "  未配置，将使用默认URL"
echo ""

echo "同步选项:"
echo ""
echo "【选项A】使用用户名密码交互式推送"
echo "  命令: git push -f gitee main:master"
echo "  然后按提示输入:"
echo "    Username: xingqiongclaw_admin"
echo "    Password: [您的Gitee密码]"
echo ""

echo "【选项B】使用Gitee私人令牌(推荐)"
echo "  请先获取Gitee私人令牌: https://gitee.com/profile/personal_access_tokens"
echo "  然后执行:"
echo "    export GITEE_TOKEN=您的令牌"
echo "    git remote set-url gitee https://xingqiongclaw_admin:\$GITEE_TOKEN@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
echo "    git push -f gitee main:master"
echo ""

echo "【选项C】使用此脚本自动设置"
read -p "请输入Gitee私人令牌 (或直接回车跳过): " TOKEN

if [ -n "$TOKEN" ]; then
    echo "设置远程URL..."
    git remote remove gitee 2>/dev/null
    git remote add gitee "https://xingqiongclaw_admin:${TOKEN}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
    echo "开始推送..."
    git push -f gitee main:master
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Gitee同步成功!"
        echo "URL: https://gitee.com/xingqiongclaw_admin/ruoxi-v2"
    else
        echo ""
        echo "⚠️ 推送失败，请检查令牌权限"
    fi
else
    echo "跳过设置，请手动执行推送"
fi

echo ""
echo "🌸 完成"
