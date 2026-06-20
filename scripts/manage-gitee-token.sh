#!/bin/bash
# 🌸 Gitee凭证管理脚本

echo "═══════════════════════════════════════════════════════════════"
echo "               🔐 Gitee凭证管理"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd /home/admin/workspace/ruoxi-v2

# 检查是否已有存储的凭证
if [ -f .local/gitee-token.txt ]; then
    EXISTING_TOKEN=$(cat .local/gitee-token.txt)
    echo "检测到已存储的Gitee令牌"
    read -p "是否使用现有令牌? [Y/n]: " USE_EXISTING
    if [ "$USE_EXISTING" != "n" ] && [ "$USE_EXISTING" != "N" ]; then
        GITEE_TOKEN="$EXISTING_TOKEN"
    else
        GITEE_TOKEN=""
    fi
fi

if [ -z "$GITEE_TOKEN" ]; then
    echo ""
    echo "请提供Gitee凭证:"
    echo ""
    echo "方式1: 使用私人令牌 (推荐)"
    echo "  获取地址: https://gitee.com/profile/personal_access_tokens"
    echo ""
    echo "方式2: 使用用户名+密码"
    echo ""
    read -p "请选择 [1/2]: " METHOD
    
    if [ "$METHOD" = "2" ]; then
        read -p "用户名: " GITEE_USER
        read -s -p "密码: " GITEE_PASS
        echo ""
        git remote set-url gitee "https://${GITEE_USER}:${GITEE_PASS}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
    else
        read -s -p "私人令牌: " GITEE_TOKEN
        echo ""
        # 保存令牌
        mkdir -p .local
        echo "$GITEE_TOKEN" > .local/gitee-token.txt
        chmod 600 .local/gitee-token.txt
        git remote set-url gitee "https://xingqiongclaw_admin:${GITEE_TOKEN}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
    fi
fi

echo ""
echo "✅ Gitee远程已更新"
echo ""
echo "是否立即推送到Gitee?"
read -p "[Y/n]: " CONFIRM

if [ "$CONFIRM" != "n" ] && [ "$CONFIRM" != "N" ]; then
    echo ""
    echo "🌸 推送到Gitee master分支..."
    if git push -f gitee main:master; then
        echo ""
        echo "🎉 Gitee同步成功!"
        echo "  URL: https://gitee.com/xingqiongclaw_admin/ruoxi-v2"
    else
        echo ""
        echo "❌ 推送失败，请检查凭证"
    fi
else
    echo "配置完成，可稍后手动执行:"
    echo "  git push -f gitee main:master"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
