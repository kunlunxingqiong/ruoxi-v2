#!/bin/bash
# 🌸 若曦V2 - Gitee令牌本地匿名化配置脚本
# 将Gitee令牌安全存储在本地

GITEE_TOKEN="${GITEE_TOKEN:-}"
LOCAL_TOKEN_FILE=".local/gitee-token.txt"

echo "🌸 配置Gitee访问令牌..."

# 创建本地存储目录
mkdir -p .local

# 存储令牌 (如果提供了)
if [ -n "$GITEE_TOKEN" ]; then
    echo "$GITEE_TOKEN" > "$LOCAL_TOKEN_FILE"
    chmod 600 "$LOCAL_TOKEN_FILE"
    echo "✅ Gitee令牌已本地安全存储"
else
    echo "⚠️  未提供GITEE_TOKEN环境变量"
    echo "   请设置: export GITEE_TOKEN=your_token"
fi

# 配置Git使用存储凭证
git config credential.helper store

echo "✅ Gitee凭证辅助已配置"
echo ""
echo "使用方式:"
echo "  export GITEE_TOKEN=your_token"
echo "  ./scripts/setup-gitee-token.sh"
