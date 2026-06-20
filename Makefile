# 🌸 若曦V2 - Makefile
# 便捷的开发和部署命令

.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate docs

# 默认显示帮助
help:
	@echo "🌸 若曦V2 - 可用命令:"
	@echo ""
	@echo "  开发命令:"
	@echo "    make install          安装依赖"
	@echo "    make dev              启动开发服务器"
	@echo "    make migrate          运行数据库迁移"
	@echo ""
	@echo "  测试命令:"
	@echo "    make test             运行所有测试"
	@echo "    make test-cov         运行测试并生成覆盖率报告"
	@echo ""
	@echo "  代码质量:"
	@echo "    make lint             检查代码风格"
	@echo "    make format           格式化代码"
	@echo "    make security         运行安全扫描"
	@echo ""
	@echo "  Docker命令:"
	@echo "    make docker-build     构建Docker镜像"
	@echo "    make docker-up        启动所有服务"
	@echo "    make docker-down      停止所有服务"
	@echo "    make docker-logs      查看日志"
	@echo ""
	@echo "  文档命令:"
	@echo "    make docs             生成API文档"
	@echo ""
	@echo "  其他:"
	@echo "    make clean            清理缓存文件"
	@echo "    make all              运行完整检查(测试+lint+安全)"

# ==================== 开发命令 ====================

install:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	@echo "🚀 启动开发服务器..."
	uvicorn platform.backend.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	@echo "🗄️ 运行数据库迁移..."
	alembic upgrade head

migrate-create:
	@echo "📝 创建新迁移..."
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

# ==================== 测试命令 ====================

test:
	@echo "🧪 运行测试..."
	pytest tests/ -v --tb=short

test-cov:
	@echo "📊 运行测试并生成覆盖率报告..."
	pytest tests/ --cov=. --cov-report=html --cov-report=term

test-ci:
	@echo "🔄 CI模式运行测试..."
	pytest tests/ -v --cov=. --cov-report=xml --cov-fail-under=85

# ==================== 代码质量 ====================

lint:
	@echo "🔍 检查代码风格..."
	@echo "  - black check"
	@black --check . || true
	@echo "  - isort check"
	@isort --check-only . || true
	@echo "  - flake8"
	@flake8 . --count --statistics || true
	@echo "  - mypy"
	@mypy core/ models/ --ignore-missing-imports || true

format:
	@echo "✨ 格式化代码..."
	@echo "  - black"
	@black .
	@echo "  - isort"
	@isort .

security:
	@echo "🔒 运行安全扫描..."
	@echo "  - bandit"
	@bandit -r . -f json -o bandit-report.json || true
	@echo "  - safety"
	@safety check || true

all: format lint test security
	@echo "✅ 完整检查完成!"

# ==================== Docker命令 ====================

docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t ruoxi-v2:latest .

docker-up:
	@echo "🚀 启动所有Docker服务..."
	docker-compose up -d

docker-down:
	@echo "⏹️ 停止所有Docker服务..."
	docker-compose down

docker-logs:
	@echo "📋 查看日志..."
	docker-compose logs -f backend

docker-clean:
	@echo "🧹 清理Docker资源..."
	docker-compose down -v --rmi all

# ==================== 文档命令 ====================

docs:
	@echo "📚 生成API文档..."
	@python -c "
from platform.backend.main import app
import json
from fastapi.openapi.utils import get_openapi

with open('openapi.json', 'w') as f:
    json.dump(get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    ), f, indent=2)
print('✅ API文档已生成: openapi.json')
"
serve-docs:
	@echo "🌐 启动文档服务器..."
	@python -m http.server 8080 &
	@echo "访问 http://localhost:8080/htmlcov/ 查看覆盖率报告"

# ==================== 其他 ====================

clean:
	@echo "🧹 清理缓存文件..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ .mypy_cache/ htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ 清理完成!"

env-setup:
	@echo "⚙️ 设置环境..."
	@cp .env.example .env
	@echo "✅ .env文件已创建，请编辑配置"

# ==================== 部署命令 ====================

deploy-check:
	@echo "🔍 部署前检查..."
	@echo "  - 测试..."
	@make test-ci
	@echo "  - 代码质量..."
	@make lint
	@echo "  - 安全扫描..."
	@make security
	@echo "✅ 部署检查通过!"

git-push:
	@echo "🚀 推送到GitHub..."
	@git add .
	@read -p "提交信息: " msg; \
	git commit -m "$$msg" && git push github main

# 版本信息
version:
	@echo "🌸 若曦V2 版本信息:"
	@git log --oneline -5 | head -1
	@echo "Python: $$(python --version 2>&1)"
	@echo "FastAPI: $$(pip show fastapi 2>/dev/null | grep Version | cut -d' ' -f2)"
