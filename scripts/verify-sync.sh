#!/bin/bash
# 🌸 同步验证脚本

echo "═══════════════════════════════════════════════════════════════"
echo "                🌸 若曦V2 同步状态验证"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd /home/admin/workspace/ruoxi-v2

echo "【本地状态】"
echo "  提交: $(git log --oneline -1)"
echo "  文件: $(find . -type f -not -path './.git/*' -not -path '*/__pycache__/*' | wc -l) 个"
echo ""

echo "【远程状态】"
git remote -v 2>/dev/null | sed 's/https:.*@/https:***@/g' | sed 's/^/  /'
echo ""

echo "【GitHub验证】(API检查)"
curl -s "https://api.github.com/repos/kunlunxingqiong/ruoxi-v2" 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    if 'pushed_at' in d:
        print(f\"  推送时间: {str(d.get('pushed_at','N/A'))[:16].replace('T',' ')}\")
        print(f\"  默认分支: {d.get('default_branch')}\")
        print(f\"  公开状态: {'公开' if not d.get('private') else '私密'}\")
    else:
        print(f\"  无法获取状态\")
except:
    print('  检查失败')
"
echo ""

echo "【Gitee验证】(API检查)"
curl -s "https://gitee.com/api/v5/repos/xingqiongclaw_admin/ruoxi-v2" 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    if 'pushed_at' in d:
        print(f\"  推送时间: {str(d.get('pushed_at','N/A'))[:16].replace('T',' ')}\")
        print(f\"  默认分支: {d.get('default_branch')}\")
        print(f\"  公开状态: {'公开' if not d.get('private') else '私密'}\")
    else:
        print(f\"  无法获取状态\")
except:
    print('  检查失败')
"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  🌸 若曦V2 同步验证完成"
echo "═══════════════════════════════════════════════════════════════"
