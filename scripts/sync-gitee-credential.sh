#!/bin/bash
# Gitee同步脚本 - 需要手动输入凭证
cd /home/admin/workspace/ruoxi-v2

echo "🌸 Gitee同步准备工作"
echo "===================="
echo ""
echo "当前状态:"
git status --short
git log --oneline -1
echo ""
echo "远程:"
git remote -v
echo ""
echo "请执行以下命令完成Gitee同步:"
echo ""
echo "  方法1: 直接推送(会提示输入用户名密码)"
echo "    git push -f gitee main:master"
echo ""
echo "  方法2: 使用令牌(推荐)"
echo "    git remote set-url gitee https://{username}:{password}@gitee.com/xingqiongclaw_admin/ruoxi-v2.git"
echo "    git push -f gitee main:master"
echo ""
echo "注意: 令牌替代方案在控制台不可用，请在终端手动执行"
echo ""
