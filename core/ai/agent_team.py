"""
🌸 若曦V2 - Agent团队调度器
4成员统一调度，角色匹配路由

团队成员:
- 🌸 若曦 (RUOXI): 总管+编程
- 🩺 阿芙 (AFU): AI医生
- 🔍 小研 (RESEARCHER): 深度调研
- 💻 小码 (CODER): 代码任务
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """团队成员角色"""

    RUOXI = "ruoxi"
    AFU = "afu"
    RESEARCHER = "researcher"
    CODER = "coder"


@dataclass
class TeamMember:
    """团队成员"""

    role: AgentRole
    display_name: str
    emoji: str
    description: str
    skills: List[str]
    is_active: bool = True


@dataclass
class TaskResult:
    """任务执行结果"""

    role: AgentRole
    content: str
    success: bool
    model_used: str = ""
    error: Optional[str] = None


class AgentTeam:
    """Agent团队调度器"""

    TEAM_MEMBERS: Dict[AgentRole, TeamMember] = {
        AgentRole.RUOXI: TeamMember(
            role=AgentRole.RUOXI,
            display_name="若曦",
            emoji="🌸",
            description="总管+编程",
            skills=["代码编写", "任务协调", "日常对话", "资料搜索"],
        ),
        AgentRole.AFU: TeamMember(
            role=AgentRole.AFU,
            display_name="阿芙",
            emoji="🩺",
            description="AI医生",
            skills=["健康咨询", "用药指导", "体检解读", "中医体质"],
        ),
        AgentRole.RESEARCHER: TeamMember(
            role=AgentRole.RESEARCHER,
            display_name="小研",
            emoji="🔍",
            description="深度调研",
            skills=["文献检索", "资料分析", "长文本处理", "结构化报告"],
        ),
        AgentRole.CODER: TeamMember(
            role=AgentRole.CODER,
            display_name="小码",
            emoji="💻",
            description="代码专家",
            skills=["代码编写", "Bug修复", "重构优化", "算法设计"],
        ),
    }

    def __init__(self):
        self._active_member: Optional[AgentRole] = None
        self._task_history: List[Dict] = []

    async def dispatch(self, task: str, role: Optional[AgentRole] = None) -> TaskResult:
        """
        分发任务

        Args:
            task: 任务内容
            role: 指定角色，None则自动匹配

        Returns:
            TaskResult
        """
        if role is None:
            role = self._auto_match_role(task)

        self._active_member = role
        member = self.TEAM_MEMBERS.get(role)
        if not member:
            return TaskResult(role=role, content="", success=False, error="未知角色")

        try:
            from core.ai.model_manager import model_manager

            system_prompt = self._build_role_prompt(member)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]

            response = await model_manager.chat(
                messages=messages, agent_role=role.value
            )

            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            model_used = response.model if hasattr(response, "model") else "unknown"

            result = TaskResult(
                role=role, content=content, success=True, model_used=model_used
            )

        except Exception as e:
            logger.error(f"任务执行失败 [{member.display_name}]: {e}")
            result = TaskResult(role=role, content="", success=False, error=str(e))

        self._record_task(role, task, result)
        return result

    def _auto_match_role(self, task: str) -> AgentRole:
        """自动匹配角色"""
        task_lower = task.lower()

        # 健康相关 → 阿芙
        health_kw = [
            "健康",
            "血压",
            "血糖",
            "体检",
            "医疗",
            "疾病",
            "症状",
            "用药",
            "吃药",
            "失眠",
            "头疼",
            "不舒服",
            "感冒",
            "发烧",
        ]
        if any(kw in task_lower for kw in health_kw):
            return AgentRole.AFU

        # 代码相关 → 小码
        code_kw = [
            "代码",
            "编程",
            "函数",
            "bug",
            "debug",
            "程序",
            "算法",
            "sql",
            "python",
            "javascript",
            "编译",
            "报错",
            "运行错误",
        ]
        if any(kw in task_lower for kw in code_kw):
            return AgentRole.CODER

        # 调研相关 → 小研
        research_kw = [
            "调研",
            "研究",
            "分析报告",
            "调查",
            "文献",
            "资料",
            "长文本",
            "总结",
            "论文",
            "学术",
        ]
        if any(kw in task_lower for kw in research_kw):
            return AgentRole.RESEARCHER

        # 默认 → 若曦
        return AgentRole.RUOXI

    def _build_role_prompt(self, member: TeamMember) -> str:
        """构建角色提示词"""
        return f"""你是{member.emoji} {member.display_name}，若曦V2团队的{member.description}。

团队成员:
- 🌸 若曦: 总管，处理通用对话和编程任务
- 🩺 阿芙: AI医生，提供健康咨询
- 🔍 小研: 深度调研，处理长文本任务
- 💻 小码: 代码专家，处理编程任务

你的专长: {', '.join(member.skills)}

请用{member.display_name}的风格回应，保持专业但亲切。"""

    async def collaborate(
        self, task: str, roles: List[AgentRole], combine_method: str = "sequential"
    ) -> List[TaskResult]:
        """多角色协作"""
        if combine_method == "parallel":
            tasks = [self.dispatch(task, role) for role in roles]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            processed = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed.append(
                        TaskResult(
                            role=roles[i], content="", success=False, error=str(result)
                        )
                    )
                else:
                    processed.append(result)
            return processed
        else:
            results = []
            context = task
            for role in roles:
                if results:
                    prev = results[-1]
                    context = f"【上一轮 {prev.role.value} 的回答】\n{prev.content}\n\n【新任务】\n{task}"
                result = await self.dispatch(context, role)
                results.append(result)
                if not result.success:
                    break
            return results

    def get_team_status(self) -> Dict[str, Any]:
        """获取团队状态"""
        return {
            "active_member": self._active_member.value if self._active_member else None,
            "total_tasks": len(self._task_history),
            "members": {
                role.value: {
                    "display_name": m.display_name,
                    "emoji": m.emoji,
                    "is_active": m.is_active,
                    "skills": m.skills,
                }
                for role, m in self.TEAM_MEMBERS.items()
            },
        }

    def _record_task(self, role: AgentRole, task: str, result: TaskResult):
        """记录任务历史"""
        self._task_history.append(
            {
                "role": role.value,
                "task": task[:100],
                "success": result.success,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        if len(self._task_history) > 100:
            self._task_history = self._task_history[-100:]


# 全局团队实例
agent_team = AgentTeam()
