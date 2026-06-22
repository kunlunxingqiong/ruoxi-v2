"""
🌸 若曦V2 - 任务调度器
定时任务管理，支持健康提醒、报告生成等
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class TaskType(Enum):
    """任务类型"""

    HEALTH_REMINDER = auto()  # 健康提醒
    EMOTION_CHECKIN = auto()  # 情绪打卡
    REPORT_GENERATION = auto()  # 报告生成
    DATA_BACKUP = auto()  # 数据备份
    SYNC_CHECK = auto()  # 同步检查
    CUSTOM = auto()  # 自定义


class TaskPriority(Enum):
    """任务优先级"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ScheduledTask:
    """定时任务"""

    id: str
    name: str
    task_type: TaskType
    cron_expression: str  # 如 "0 9 * * *" (每天9点)
    callback: Callable
    user_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None


class TaskScheduler:
    """
    任务调度器

    功能:
    - Cron表达式支持
    - 任务优先级队列
    - 执行历史记录
    - 失败重试机制
    """

    def __init__(self, data_dir: str = "data/scheduler"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None

        # 预定义若曦的健康提醒任务
        self._init_default_tasks()

    def _init_default_tasks(self):
        """初始化若曦默认提醒任务"""
        self.default_reminders = [
            {
                "name": "早晨喝水提醒",
                "cron": "0 8 * * *",
                "message": "🌸 早上好~该喝一杯温水啦，开启美好的一天！",
            },
            {
                "name": "午餐提醒",
                "cron": "0 12 * * *",
                "message": "🍚 午饭时间到啦，记得吃点热的，不要太油腻哦~",
            },
            {
                "name": "下午休息提醒",
                "cron": "0 15 * * *",
                "message": "☕ 起来活动一下吧，喝杯茶，看看窗外，让眼睛休息一下~",
            },
            {
                "name": "晚餐提醒",
                "cron": "0 18 * * *",
                "message": "🌙 晚饭时间，记得七分饱，晚餐要清淡些哦~",
            },
            {
                "name": "准备睡觉提醒",
                "cron": "0 21 * * *",
                "message": "💤 该准备睡觉啦，放下手机，泡个脚，放松心情~",
            },
            {
                "name": "入睡提醒",
                "cron": "0 22 * * *",
                "message": "🌸 很晚啦，曦曦也要去睡了，晚安，做个好梦~",
            },
        ]

    def add_task(
        self,
        name: str,
        task_type: TaskType,
        cron_expression: str,
        callback: Callable,
        user_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_runs: Optional[int] = None,
    ) -> str:
        """
        添加定时任务

        Args:
            name: 任务名称
            task_type: 任务类型
            cron_expression: Cron表达式 (分 时 日 月 周)
            callback: 回调函数
            user_id: 关联用户ID
            priority: 优先级
            max_runs: 最大执行次数
        """
        import hashlib

        task_id = hashlib.md5(f"{name}:{user_id or 'global'}".encode()).hexdigest()[:12]

        task = ScheduledTask(
            id=task_id,
            name=name,
            task_type=task_type,
            cron_expression=cron_expression,
            callback=callback,
            user_id=user_id,
            priority=priority,
            max_runs=max_runs,
        )

        self._tasks[task_id] = task
        self._calculate_next_run(task)

        return task_id

    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = True
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = False
            return True
        return False

    async def start(self):
        """启动调度器"""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        print("🌸 若曦任务调度器已启动")

    async def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        print("🌸 若曦任务调度器已停止")

    async def _scheduler_loop(self):
        """调度主循环"""
        while self._running:
            now = datetime.utcnow()

            # 查找需要执行的任务
            due_tasks = [
                task
                for task in self._tasks.values()
                if task.enabled and task.next_run and task.next_run <= now
            ]

            # 按优先级排序
            due_tasks.sort(key=lambda t: t.priority.value)

            # 执行任务
            for task in due_tasks:
                try:
                    await self._execute_task(task)
                except Exception as e:
                    print(f"任务执行失败 {task.name}: {e}")

            # 等待到下一秒
            await asyncio.sleep(1)

    async def _execute_task(self, task: ScheduledTask):
        """执行单个任务"""
        task.last_run = datetime.utcnow()
        task.run_count += 1

        # 检查是否达到最大执行次数
        if task.max_runs and task.run_count >= task.max_runs:
            task.enabled = False

        # 计算下次执行时间
        self._calculate_next_run(task)

        # 执行回调
        try:
            if asyncio.iscoroutinefunction(task.callback):
                await task.callback(task)
            else:
                task.callback(task)
        except Exception as e:
            print(f"任务回调执行失败: {e}")

    def _calculate_next_run(self, task: ScheduledTask):
        """计算下次执行时间"""
        # 简单的cron计算实现
        from pytz import timezone

        now = datetime.utcnow()
        cron_parts = task.cron_expression.split()

        if len(cron_parts) != 5:
            task.next_run = None
            return

        minute, hour, day, month, weekday = cron_parts

        # 简单的每天执行计算
        if day == "*" and month == "*":
            # 计算下一个执行时间点
            next_run = now.replace(
                hour=int(hour), minute=int(minute), second=0, microsecond=0
            )

            if next_run <= now:
                next_run += timedelta(days=1)

            task.next_run = next_run

    def get_task_list(self, user_id: Optional[str] = None) -> List[ScheduledTask]:
        """获取任务列表"""
        tasks = list(self._tasks.values())

        if user_id:
            tasks = [t for t in tasks if t.user_id == user_id]

        return sorted(tasks, key=lambda t: t.priority.value)

    def get_task_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_tasks": len(self._tasks),
            "enabled": sum(1 for t in self._tasks.values() if t.enabled),
            "disabled": sum(1 for t in self._tasks.values() if not t.enabled),
            "by_type": {
                task_type.name: sum(
                    1 for t in self._tasks.values() if t.task_type == task_type
                )
                for task_type in TaskType
            },
            "total_runs": sum(t.run_count for t in self._tasks.values()),
        }


# 若曦专属提醒回调
async def ruoxi_reminder_callback(task: ScheduledTask):
    """若曦提醒回调"""
    reminders = {
        "早晨喝水提醒": "🌸 早上好~该喝一杯温水啦，开启美好的一天！",
        "午餐提醒": "🍚 午饭时间到啦，记得吃点热的，不要太油腻哦~",
        "下午休息提醒": "☕ 起来活动一下吧，喝杯茶，看看窗外，让眼睛休息一下~",
        "晚餐提醒": "🌙 晚饭时间，记得七分饱，晚餐要清淡些哦~",
        "准备睡觉提醒": "💤 该准备睡觉啦，放下手机，泡个脚，放松心情~",
        "入睡提醒": "🌸 很晚啦，曦曦也要去睡了，晚安，做个好梦~",
    }

    message = reminders.get(task.name, f"⏰ {task.name}")

    # 这里可以集成通知系统
    print(f"[{datetime.now().strftime('%H:%M')}] {message}")

    # 如果有用户ID，可以推送给特定用户
    if task.user_id:
        print(f"   发送给用户: {task.user_id}")


# 全局调度器实例
task_scheduler = TaskScheduler()
