#!/bin/bash
# 🌸 若曦V2最终同步脚本

cd /home/admin/workspace/ruoxi-v2

echo "🌸 最终同步开始..."
echo ""
echo "当前git状态:"
git status --short
git log --oneline -1
echo ""

# 保存token到环境变量
GITHUB_TOKEN="$1"

echo "配置远程仓库..."
git remote remove origin 2>/dev/null
git remote remove github 2>/dev/null
git remote remove gitee 2>/dev/null

echo "添加GitHub远程..."
git remote add github "https://${GITHUB_TOKEN}@github.com/kunlunxingqiong/ruoxi-v2.git"

echo "添加Gitee远程..."
# Gitee使用公共URL，推送时会提示输入凭证
git remote add gitee "https://gitee.com/xingqiongclaw_admin/ruoxi-v2.git"

echo ""
echo "远程配置:"
git remote -v
echo ""

echo "推送到GitHub..."
if git push -f github main; then
    echo "✅ GitHub推送成功!"
else
    echo "⚠️ GitHub推送失败"
fi

echo ""
echo "推送到Gitee..."
echo "注意: Gitee推送需要手动输入凭证"
if git push -f gitee main:master; then
    echo "✅ Gitee推送成功!"
else
    echo "⚠️ Gitee推送失败 (可能需要手动输入凭证)"
fi

echo ""
echo "🌸 同步完成"
