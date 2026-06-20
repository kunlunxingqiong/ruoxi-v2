# 🌸 若曦V2 使用示例

## 示例1: 快速开始聊天

```python
import requests

# 登录
token = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "user", "password": "pass"}
).json()["access_token"]

# 聊天
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "messages": [{"role": "user", "content": "你好若曦"}]
    }
).json()

print(response["content"])  # 🌸 你好呀~
```

## 示例2: 流式响应

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat/stream",
    headers={"Authorization": f"Bearer {token}"},
    json={"messages": [{"role": "user", "content": "讲个故事"}]},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'), end='')
```

## 示例3: 情绪检测

```python
response = requests.post(
    "http://localhost:8000/api/v1/emotion/analyze",
    headers={"Authorization": f"Bearer {token}"},
    json={"text": "最近压力好大，睡不着"}
).json()

print(f"情绪: {response['emotion']}")  # anxious
print(f"危机等级: {response['crisis_level']}")
```

## 示例4: 健康分析

```python
# 记录血压
requests.post(
    "http://localhost:8000/api/v1/health/records",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "type": "blood_pressure",
        "systolic": 138,
        "diastolic": 88
    }
)

# AI分析
analysis = requests.get(
    "http://localhost:8000/api/v1/health-ai/analyze/blood_pressure",
    headers={"Authorization": f"Bearer {token}"}
).json()

print(analysis["ai_summary"])
print(analysis["recommendations"])
```

## 示例5: JavaScript前端

```javascript
// 建立WebSocket连接
const ws = new WebSocket('ws://localhost:8000/ws/chat/123');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "你好若曦",
    user_id: "user_001"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'chunk') {
    document.getElementById('chat').innerHTML += data.content;
  }
  
  if (data.type === 'emotion') {
    showEmotionEmoji(data.emotion);
  }
};
```

## 示例6: CLI使用

```bash
# 启动服务
ruoxi start

# 检查环境
ruoxi check

# 测试API
ruoxi test

# 快速聊天
ruoxi chat "你好若曦"

# 生成报告
ruoxi report --period weekly --format html
```
