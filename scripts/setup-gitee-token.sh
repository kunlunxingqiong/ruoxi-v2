#!/bin/bash
# 🌸 Gitee令牌配置脚本

echo "═══════════════════════════════════════════════════════════════"
echo "               🌸 Gitee令牌配置"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd /home/admin/workspace/ruoxi-v2

# 提示输入Gitee令牌
read -s -p "请输入Gitee私人令牌 (从 https://gitee.com/profile/personal_access_tokens 获取): " GITEE_TOKEN
echo ""

if [ -n "$GITEE_TOKEN" ]; then
    # 保存令牌
    mkdir -p .local
    echo "$GITEE_TOKEN" > .local/gitee-token.txt
    chmod 600 .local/gitee-token.txt
    echo "✅ Gitee令牌已安全存储到 .local/gitee-token.txt"
    
    # 配置远程
    git remote remove gitee 2>/dev/null
    git remote add gitee "https://xingqiongclaw_admin:${GITEE_TOKEN}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
    echo "✅ Gitee远程已配置使用令牌"
    
    echo ""
    echo "是否立即推送到Gitee?"
    read -p "[Y/n]: " CONFIRM
    
    if [ "$CONFIRM" != "n" ] && [ "$CONFIRM" != "N" ]; then
        echo ""
        echo "🌸 推送到Gitee master分支..."
        git push -f gitee main:master && \
        echo "" && \
        echo "🎉 Gitee同步成功!" && \
        echo "URL: https://gitee.com/xingqiongclaw_admin/ruoxi-v2"
    else
        echo "已跳过推送，配置完成"
    fi
else
    echo "❌ 未提供令牌，配置取消"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
