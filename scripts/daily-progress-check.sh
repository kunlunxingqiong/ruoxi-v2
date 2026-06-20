#!/bin/bash
# 🌸 若曦V2 每日进度检查脚本

cd /home/admin/workspace/ruoxi-v2

TODAY=$(date +%Y-%m-%d)
PROGRESS_FILE="docs/progress/${TODAY}.md"

echo "═══════════════════════════════════════════════════════════════"
echo "   🌸 若曦V2 每日进度检查 ${TODAY}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# 检查今日进度文件是否存在
if [ ! -f "$PROGRESS_FILE" ]; then
    echo "📋 创建今日进度文件..."
    cat > "$PROGRESS_FILE" << EOF
# 🌸 ${TODAY} 开发进度

## 日期信息
- **日期**: ${TODAY}
- **今日目标**: 6%-10%
- **最低要求**: 5%

## 开发任务

[-] 任务1: 
- 进度: 0%
- 备注: 

[-] 任务2: 
- 进度: 0%
- 备注: 

[-] 任务3: 
- 进度: 0%
- 备注: 

## 代码提交
- 提交次数: 
- 主要变更: 

## 双仓库同步
- [ ] GitHub 已同步
- [ ] Gitee 已同步

## 明日计划
1. 
2. 
3. 

---
🌸 *质量第一，时间第二*
EOF
    echo "✅ 进度文件已创建: ${PROGRESS_FILE}"
else
    echo "✅ 进度文件已存在: ${PROGRESS_FILE}"
fi

echo ""
echo "【今日任务清单】"
grep "^\[-\]" "$PROGRESS_FILE" 2>/dev/null || echo "  暂无任务"

echo ""
echo "【代码统计】"
echo "  Python文件: $(find . -name '*.py' -not -path '*/__pycache__/*' | wc -l) 个"
echo "  今日提交: $(git log --since="${TODAY} 00:00" --oneline | wc -l) 次"

echo ""
echo "【Git状态】"
git status --short | head -5 | sed 's/^/  /' || echo "  工作区干净"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  💡 提示: 记得每天更新进度文件并完成至少5%的开发进度"
echo "═══════════════════════════════════════════════════════════════"
echo ""
