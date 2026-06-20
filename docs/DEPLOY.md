# 🚀 若曦V2 部署指南

本文档介绍如何将 **若曦V2** 部署到生产环境。

## 📋 目录

- [快速部署 (Docker Compose)](#-快速部署-docker-compose)
- [手动部署](#-手动部署)
- [云服务器部署](#-云服务器部署)
- [监控配置](#-监控配置)
- [故障排除](#-故障排除)

---

## 🐳 快速部署 (Docker Compose)

### 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 2核 CPU / 4GB RAM / 20GB 磁盘

### 部署步骤

```bash
# 1. 克隆项目
git clone https://github.com/kunlunxingqiong/ruoxi-v2.git
cd ruoxi-v2

# 2. 配置环境变量
cp .env.example .env

# 编辑 .env 文件，配置以下内容:
# - DATABASE_URL (PostgreSQL连接字符串)
# - REDIS_URL (Redis连接字符串)
# - JWT_SECRET (随机密钥)
# - GROQ_API_KEY (可选，用于AI功能)

# 3. 启动服务
docker-compose up -d

# 4. 检查状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f backend
```

### 访问服务

| 服务 | URL | 默认账号 |
|------|-----|----------|
| API文档 | http://localhost:8000/docs | - |
| API | http://localhost:8000 | - |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |

---

## 🖥️ 手动部署

### 系统要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (前端)

### 后端部署

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
export DATABASE_URL="postgresql://user:password@localhost/ruoxi_health"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="your-secret-key-here"

# 4. 数据库迁移
alembic upgrade head

# 5. 启动服务 (开发模式)
uvicorn platform.backend.main:app --reload

# 或生产模式
uvicorn platform.backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Celery 启动

```bash
# 启动 Worker
celery -A tasks.celery_config worker --loglevel=info

# 启动定时调度
celery -A tasks.celery_config beat --loglevel=info
```

---

## ☁️ 云服务器部署

### 使用 Docker 部署到云服务器

```bash
# 1. 在云服务器上安装 Docker
curl -fsSL https://get.docker.com | sh

# 2. 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. 克隆项目
git clone https://github.com/kunlunxingqiong/ruoxi-v2.git
cd ruoxi-v2

# 4. 配置生产环境变量
# 编辑 .env 文件，使用强密码和随机密钥

# 5. 启动
docker-compose up -d

# 6. 配置防火墙 (如果使用云服务器)
# 开放端口: 8000 (API), 3000 (Grafana), 5432 (PostgreSQL仅限内网)
```

### Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# HTTPS 配置 (推荐使用 certbot)
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 📊 监控配置

### Prometheus 指标

若曦V2 自动暴露以下 Prometheus 指标:

| 指标 | 类型 | 描述 |
|------|------|------|
| `http_requests_total` | Counter | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | HTTP请求耗时 |
| `ruoxi_health_score` | Gauge | 用户健康评分 |

### Grafana 仪表盘

访问 `http://localhost:3000` 查看预配置的仪表盘:

- **系统概览**: CPU、内存、磁盘使用率
- **API性能**: 请求量、响应时间、错误率
- **业务指标**: 活跃用户数、健康记录数

---

## 🔧 故障排除

### 服务无法启动

```bash
# 检查日志
docker-compose logs backend

# 检查数据库连接
docker-compose exec backend python -c "from sqlalchemy import create_engine; e = create_engine('postgresql://user:pass@db:5432/ruoxi'); print(e.connect())"

# 重新构建
docker-compose down
docker-compose up -d --build
```

### 数据库迁移失败

```bash
# 进入容器
docker-compose exec backend bash

# 手动运行迁移
alembic upgrade head

# 或重置迁移
alembic downgrade base
alembic upgrade head
```

### 性能问题

```bash
# 检查资源使用
docker stats

# 查看慢查询 (需要配置PostgreSQL日志)
docker-compose exec db cat /var/lib/postgresql/data/log/postgresql.log | grep "duration"

# 调整Worker数量 (编辑 docker-compose.yml)
# 将 backend 的 workers 从 4 调整为 8
```

---

## 🔄 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建
docker-compose down
docker-compose up -d --build

# 3. 运行迁移
docker-compose exec backend alembic upgrade head
```

---

## 📞 获取帮助

- **GitHub Issues**: https://github.com/kunlunxingqiong/ruoxi-v2/issues
- **文档**: http://localhost:8000/docs
- **日志**: `docker-compose logs -f`

---

**Made with 💜 by 若曦**
