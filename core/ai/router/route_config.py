"""
🌸 若曦V2 - 路由配置
角色匹配模式 + 400+模型静态注册表

团队成员:
- 🌸 若曦 (RUOXI): 总管+编程 → DeepSeek V4 Pro
- 🩺 阿芙 (AFU): AI医生 → 智谱GLM-4
- 🔍 小研 (RESEARCHER): 深度调研 → 月之暗面128K
- 💻 小码 (CODER): 代码任务 → DeepSeek Coder

模型来源: AFuclaw验证过的仓库API线路 (无需用户额外注册)
"""
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class AgentRole(Enum):
    """团队成员角色"""
    RUOXI = "ruoxi"            # 🌸 若曦 - 总管+编程
    AFU = "afu"                # 🩺 阿芙 - AI医生
    RESEARCHER = "researcher"  # 🔍 小研 - 深度调研
    CODER = "coder"            # 💻 小码 - 代码任务


# ====== 角色默认模型 (核心注册表) ======
ROLE_DEFAULT_MODELS: Dict[AgentRole, str] = {
    AgentRole.RUOXI: "deepseek-ai/deepseek-v4-pro",       # NVIDIA NIM
    AgentRole.AFU: "glm-4",                                 # 智谱
    AgentRole.RESEARCHER: "moonshot-v1-128k",               # 月之暗面
    AgentRole.CODER: "deepseek-ai/deepseek-coder",          # NVIDIA NIM
}

# ====== 角色Fallback链 ======
ROLE_FALLBACK_CHAINS: Dict[AgentRole, List[str]] = {
    AgentRole.RUOXI: [
        "deepseek-ai/deepseek-v4-pro",          # NVIDIA主力
        "deepseek/deepseek-v4-flash:free",       # OpenRouter免费
        "Pro/deepseek-ai/DeepSeek-V3",           # 硅基流动
        "qwen/qwen3-next-80b-a3b-instruct:free", # OpenRouter免费
    ],
    AgentRole.AFU: [
        "glm-4",                                  # 智谱主力
        "z-ai/glm-4.5-air:free",                 # OpenRouter免费智谱
        "deepseek-ai/deepseek-v4-pro",            # NVIDIA备用
    ],
    AgentRole.RESEARCHER: [
        "moonshot-v1-128k",                       # 月之暗面主力
        "deepseek-ai/deepseek-v4-pro",            # NVIDIA长文本
        "Pro/deepseek-ai/DeepSeek-V3",            # 硅基流动
    ],
    AgentRole.CODER: [
        "deepseek-ai/deepseek-coder",             # NVIDIA主力
        "qwen/qwen3-coder:free",                  # OpenRouter免费
        "Pro/deepseek-ai/DeepSeek-V3",            # 硅基流动
    ],
}

# ====== Provider配置 (已验证可用) ======
PROVIDER_CONFIGS = {
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "provider": "nvidia",
        "model_count": 117,
        "priority": 1,  # 主力
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "provider": "siliconflow",
        "model_count": 92,
        "priority": 2,  # 备用
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "provider": "openrouter",
        "free_models": 23,
        "priority": 3,  # 免费补充
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "provider": "zhipu",
        "model_count": 6,
        "priority": 2,
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "provider": "moonshot",
        "model_count": 8,
        "priority": 2,
    },
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "provider": "dashscope",
        "model_count": 200,
        "priority": 3,  # 免费额度已用完
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "provider": "groq",
        "model_count": 5,
        "priority": 3,  # 免费高速
    },
    "cloudflare": {
        "base_url": "https://api.cloudflare.com/client/v4/accounts/{id}/ai",
        "provider": "cloudflare",
        "free_models": 6,
        "priority": 4,  # 免费兜底
    },
    "google_ai": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "provider": "google_ai",
        "model_count": 5,
        "priority": 3,  # 免费大量额度
    },
}


def get_role_model(role: AgentRole) -> str:
    """获取角色默认模型"""
    return ROLE_DEFAULT_MODELS.get(role, ROLE_DEFAULT_MODELS[AgentRole.RUOXI])


def get_role_fallback_chain(role: AgentRole) -> List[str]:
    """获取角色Fallback链"""
    return ROLE_FALLBACK_CHAINS.get(role, ROLE_FALLBACK_CHAINS[AgentRole.RUOXI])
