# 🚀 若曦V2 部署指南

## 📋 前置要求

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+ (可选，可用SQLite)
- Redis (可选，可用内存缓存)

---

## 🐳 Docker 部署 (推荐)

### 一键部署

```bash
# 克隆项目
git clone https://github.com/kunlunxingqiong/ruoxi-v2.git
cd ruoxi-v2

# 配置环境
cp .env.example .env
# 编辑 .env 填入配置

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api
```

### 服务结构

| 服务 | 端口 | 说明 |
|------|------|------|
| ruoxi-api | 8000 | FastAPI后端 |
| ruoxi-frontend | 3000 | React前端 |
| postgres | 5432 | PostgreSQL数据库 |
| redis | 6379 | Redis缓存 |
| nginx | 80/443 | 反向代理 |

---

## 🐍 手动部署

### 1. 后端部署

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境
export RUOXI_ENV=production
export RUOXI_JWT_SECRET="your-secret-key"
export RUOXI_DB_URL="postgresql://user:pass@localhost/ruoxi"

# 启动
cd platform/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. 前端部署

```bash
cd frontend
npm install
npm run build

# 使用Nginx/serve部署
serve -s dist -l 3000
```

---

## ☁️ 云部署

### Vercel (前端)

```bash
# 安装Vercel CLI
npm i -g vercel

# 部署
cd frontend
vercel --prod
```

### Railway/Render (后端)

1. 连接GitHub仓库
2. 设置环境变量
3. 自动部署

---

## ⚙️ 环境变量

### 必需配置

```bash
# 应用
RUOXI_ENV=production
RUOXI_JWT_SECRET=your-secret-key-min-32-chars

# 数据库 (PostgreSQL)
RUOXI_DB_URL=postgresql://user:password@host:5432/dbname

# AI密钥 (至少一个)
GEMINI_API_KEY=xxx
GROQ_API_KEY=xxx
```

### 可选配置

```bash
# Redis缓存
REDIS_URL=redis://localhost:6379/0

# 监控
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

---

## 🔒 SSL/HTTPS

### Nginx配置

```nginx
server {
    listen 443 ssl http2;
    server_name ruoxi.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

---

## 📊 监控

Prometheus指标: `http://localhost:8000/metrics`

健康检查: `http://localhost:8000/health`

---

## 🐛 故障排查

### 服务无法启动

```bash
# 检查日志
docker-compose logs api

# 检查端口占用
lsof -i :8000

# 检查环境变量
echo $RUOXI_JWT_SECRET
```

### AI响应慢

- 检查API密钥有效性
- 检查网络连接
- 启用缓存

### 数据库错误

```bash
# 重置数据库
alembic downgrade base
alembic upgrade head
```

---

## 💡 生产建议

1. **使用PostgreSQL** - 比SQLite性能更好
2. **启用Redis缓存** - 减少AI调用
3. **配置反向代理** - Nginx处理静态文件
4. **设置日志轮转** - 防止磁盘占满
5. **定期备份** - 数据库定时备份
6. **监控告警** - 配置Prometheus AlertManager

---

有问题请参考 [Troubleshooting](./TROUBLESHOOTING.md)
