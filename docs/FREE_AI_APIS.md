# 🤖 若曦V2 免费AI API 资源汇总

> 为若曦主脑选择永久免费、稳定可靠的AI模型API

## 永久免费推荐

### 1. Google Gemini (强力推荐)
- **API**: Google AI Studio
- **免费额度**:  generous免费层
- **模型**: gemini-2.0-flash / gemini-2.0-pro
- **限制**: 60 requests/minute
- **优点**: 速度快、支持多模态
- **文档**: https://ai.google.dev/

```python
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')
```

### 2. Groq (速度之王)
- **API**: OpenAI兼容
- **免费额度**:  generous限制
- **模型**: Llama 3.3 / Mixtral / Gemma
- **限制**: 较高请求频率
- **优点**: 极速响应、OpenAI SDK兼容
- **注册**: https://console.groq.com

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)
```

### 3. Together AI
- **API**: OpenAI兼容
- **免费额度**: 有免费层
- **模型**: 多种开源模型
- **优点**: 模型丰富、易于切换
- **注册**: https://api.together.xyz

### 4. Ollama (本地部署)
- **方式**: 本地运行
- **费用**: 完全免费
- **模型**: 本地运行Llama、Mistral等
- **优点**: 无网络延迟、隐私安全

```bash
ollama run llama3.2
```

## 带免费额度

### 5. Cohere (推荐)
- **免费额度**:  generous免费层
- **优点**: 文本生成质量高
- **注册**: https://cohere.com

### 6. HuggingFace Inference API
- **免费额度**: 有限免费层
- **优点**: 模型多样
- **限制**: 有速率限制

## 开源项目参考

| 项目 | 链接 | 说明 |
|------|------|------|
| gpt4free | https://github.com/xtekky/gpt4free | 多API聚合 |
| free-chatgpt-api | https://github.com/... | 免费GPT API |
| poe-api-wrapper | https://github.com/... | Poe API封装 |
| one-api | https://github.com/songquanpeng/one-api | 统一API网关 |
| ChatGPT-Next-Web | https://github.com/Yidadaa/ChatGPT-Next-Web | 开源客户端 |

## 若曦V2 集成策略

### 主脑模型优先级
1. **首选**: Google Gemini (gemini-2.0-flash) - 免费、快速、稳定
2. **备用1**: Groq (Llama 3.3) - 极速、可靠
3. **备用2**: Together AI - 模型丰富
4. **本地**: Ollama - 完全离线、隐私

### 降级机制
```python
ai_models = [
    {"name": "gemini", "priority": 1, "timeout": 10},
    {"name": "groq", "priority": 2, "timeout": 5},
    {"name": "together", "priority": 3, "timeout": 15},
    {"name": "ollama", "priority": 4, "timeout": 30},
]
```

### 成本优化
- 缓存常用响应
- 预估token消耗
- 按场景选择模型（快思/慢想）
- 批量请求合并

## 配置示例

```yaml
# config/ai.yaml
ai:
  primary:
    provider: gemini
    model: gemini-2.0-flash
    api_key: ${GEMINI_API_KEY}
  
  fallback:
    - provider: groq
      model: llama-3.3-70b
      api_key: ${GROQ_API_KEY}
    
    - provider: ollama
      model: llama3.2
      base_url: http://localhost:11434
  
  timeout: 30
  retry: 3
  cache: true
```

---

🌸 *为若曦选择最优质的免费AI大脑*
