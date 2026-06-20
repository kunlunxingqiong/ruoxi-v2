#!/bin/bash

# 若曦V2 部署脚本
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
echo "🌸 若曦V2 部署脚本"
echo "环境: $ENVIRONMENT"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "📦 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 创建必要目录
echo "📁 创建目录..."
mkdir -p data logs tmp

# 运行测试
echo "🧪 运行测试..."
if python3 -m pytest platform/backend/tests/ -v --tb=short; then
    echo "✅ 测试通过"
else
    echo "❌ 测试失败"
    exit 1
fi

# 启动服务
echo ""
echo "🚀 启动若曦V2服务..."
echo "访问: http://localhost:8000"
echo "按 Ctrl+C 停止服务"
echo ""

python3 -m platform.backend.main
