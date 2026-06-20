#!/bin/bash
# 🌸 若曦V2 全仓库同步脚本
# 用于同步 GitHub 和 Gitee 两个远程仓库

cd /home/admin/workspace/ruoxi-v2

echo "═══════════════════════════════════════════════════════════════"
echo "               🌸 若曦V2 全仓库同步脚本"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# 显示当前状态
echo "【当前状态】"
echo "  本地提交: $(git log --oneline -1 2>/dev/null || echo 'N/A')"
echo "  本地时间: $(git log --format='%cd' --date=format:'%Y-%m-%d %H:%M:%S' -1 2>/dev/null || echo 'N/A')"
echo ""

# 获取GitHub令牌
if [ -f .local/github-token.txt ]; then
    GH_TOKEN=$(cat .local/github-token.txt)
    echo "  ✅ GitHub令牌: 已从安全存储读取"
else
    echo "  ⏳ GitHub令牌: 请输入"
    read -s -p "  GitHub令牌: " GH_TOKEN
    echo ""
    if [ -n "$GH_TOKEN" ]; then
        mkdir -p .local
        echo "$GH_TOKEN" > .local/github-token.txt
        chmod 600 .local/github-token.txt
        echo "  ✅ 已保存到 .local/github-token.txt"
    fi
fi

# 配置GitHub远程
if [ -n "$GH_TOKEN" ]; then
    git remote remove github 2>/dev/null
    git remote add github "https://${GH_TOKEN}@github.com/kunlunxingqiong/ruoxi-v2.git"
    echo "  ✅ GitHub远程已配置"
fi

echo ""

# 尝试同步GitHub
echo "【同步GitHub】"
echo "  推送到 https://github.com/kunlunxingqiong/ruoxi-v2 ..."
if git push -f github main 2>/dev/null; then
    echo "  ✅ GitHub同步成功!"
else
    echo "  ⚠️  GitHub同步失败 (可能是网络问题或令牌无效)"
fi

echo ""

# 获取Gitee凭证
if [ -f .local/gitee-token.txt ]; then
    GITEE_TOKEN=$(cat .local/gitee-token.txt)
    echo "【同步Gitee】"
    git remote remove gitee 2>/dev/null
    git remote add gitee "https://xingqiongclaw_admin:${GITEE_TOKEN}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
    echo "  推送到 https://gitee.com/xingqiongclaw_admin/ruoxi-v2 ..."
    if git push -f gitee main:master 2>/dev/null; then
        echo "  ✅ Gitee同步成功!"
    else
        echo "  ❌ Gitee同步失败"
    fi
else
    echo "【同步Gitee】"
    echo "  ⏳ Gitee令牌未配置"
    echo ""
    read -p "  是否配置Gitee令牌? [Y/n]: " CONFIG_GITEE
    if [ "$CONFIG_GITEE" != "n" ] && [ "$CONFIG_GITEE" != "N" ]; then
        echo ""
        read -s -p "  Gitee私人令牌: " GITEE_TOKEN
        echo ""
        if [ -n "$GITEE_TOKEN" ]; then
            echo "$GITEE_TOKEN" > .local/gitee-token.txt
            chmod 600 .local/gitee-token.txt
            git remote remove gitee 2>/dev/null
            git remote add gitee "https://xingqiongclaw_admin:${GITEE_TOKEN}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
            echo "  ✅ Gitee令牌已保存"
            echo "  推送到Gitee..."
            if git push -f gitee main:master; then
                echo "  ✅ Gitee同步成功!"
            else
                echo "  ❌ 推送失败"
            fi
        fi
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ 同步流程完成"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "远程状态:"
git remote -v 2>/dev/null | sed 's/https:.*@/https:***@/g' | sed 's/^/  /'
echo ""
echo "GitHub: https://github.com/kunlunxingqiong/ruoxi-v2"
echo "Gitee:  https://gitee.com/xingqiongclaw_admin/ruoxi-v2"
echo ""
