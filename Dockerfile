# 🌸 若曦V2 - Docker生产镜像
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 生产阶段
FROM python:3.11-slim

LABEL maintainer="若曦<ruoxi@xingqiongclaw.ai>"
LABEL version="2.0"
LABEL description="若曦健康AI助手 - AI医生朋友"

# 设置工作目录
WORKDIR /app

# 创建非root用户
RUN groupadd -r ruoxi && useradd -r -g ruoxi ruoxi

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 从builder阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY --chown=ruoxi:ruoxi . .

# 创建日志和数据目录
RUN mkdir -p /app/logs /app/data && \
    chown -R ruoxi:ruoxi /app/logs /app/data

# 切换到非root用户
USER ruoxi

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "platform.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
