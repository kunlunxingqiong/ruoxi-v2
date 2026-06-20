# 🌸 若曦V2 API 完整使用指南

## 快速开始

### 1. 认证

所有API需要JWT认证：

```bash
# 登录获取Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 2. 使用Token访问API

```bash
curl http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "你是若曦"},
      {"role": "user", "content": "你好"}
    ]
  }'
```

## API端点列表

### 💬 聊天

#### POST /api/v1/chat
普通聊天

**请求:**
```json
{
  "messages": [
    {"role": "system", "content": "你是若曦"},
    {"role": "user", "content": "你好"}
  ],
  "model": "gemini-2.0-flash",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**响应:**
```json
{
  "content": "🌸 你好呀~ 曦曦在呢",
  "model_used": "gemini-2.0-flash",
  "tokens_input": 10,
  "tokens_output": 15,
  "response_time_ms": 520
}
```

#### POST /api/v1/chat/stream
流式聊天

**请求:** 同上，添加 `"stream": true`

**响应:** SSE流 (Server-Sent Events)

### 💜 健康

#### GET /api/v1/health-ai/analyze/{type}
分析健康数据

**类型:** blood_pressure, blood_glucose, sleep, heart_rate

**响应:**
```json
{
  "overall_status": "正常",
  "metrics": [{"name": "血压", "value": "120/80", "status": "normal"}],
  "ai_summary": "整体健康情况良好",
  "recommendations": ["继续保持当前习惯"],
  "risk_level": "low"
}
```

#### POST /api/v1/health-ai/report
生成健康报告

**请求:**
```json
{
  "period": "weekly",
  "format": "html"
}
```

**响应:** 报告下载链接

### 💕 情感

#### POST /api/v1/emotion/analyze
分析情感

**请求:**
```json
{
  "text": "今天好开心！"
}
```

**响应:**
```json
{
  "emotion": "happy",
  "intensity": 8,
  "confidence": 0.92,
  "response_strategy": "celebrate",
  "crisis_level": "NONE"
}
```

### 🧠 记忆

#### POST /api/v1/memory/add
添加记忆

**请求:**
```json
{
  "content": "用户喜欢喝抹茶拿铁",
  "type": "fact",
  "importance": 0.8
}
```

#### GET /api/v1/memory/query
查询记忆

**参数:** `query=关键词&limit=5`

**响应:**
```json
{
  "memories": [
    {
      "id": "mem_001",
      "content": "用户喜欢喝抹茶拿铁",
      "similarity": 0.95
    }
  ]
}
```

### 📊 监控

#### GET /metrics
Prometheus指标

#### GET /health
健康检查

```json
{
  "status": "healthy",
  "timestamp": "2026-06-21T10:00:00Z",
  "version": "2.0.0",
  "services": {
    "database": "up",
    "cache": "up",
    "ai_models": "up"
  }
}
```

## 错误处理

### 标准错误格式

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "请求参数无效",
  "details": {
    "field": "blood_pressure.systolic",
    "reason": "必须在90-200之间"
  }
}
```

### 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| AUTHENTICATION_ERROR | 401 | 认证失败 |
| AUTHORIZATION_ERROR | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| VALIDATION_ERROR | 422 | 参数无效 |
| RATE_LIMIT_ERROR | 429 | 请求过快 |
| INTERNAL_ERROR | 500 | 服务器错误 |

## 限流规则

| 端点 | 限流 |
|------|------|
| /api/v1/chat | 20 req/min |
| /api/v1/health-ai/* | 100 req/min |
| /api/v1/emotion/* | 100 req/min |
| /health | 1000 req/min |

## WebSocket

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/{session_id}');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "你好若曦",
    user_id: "user_001"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.chunk);  // 流式输出
};
```

---
更多详情请访问: http://localhost:8000/docs
