# adapter-openclaw/scheduler.py
"""
Scheduler — 定时任务封装

记录调度计划（实际触发依赖 OpenClaw cron 配置）
"""

import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class ScheduledJob:
    """定时任务"""
    job_id: str
    cron_expr: str
    handler_name: str
    payload: Dict
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


class Scheduler:
    """
    调度器（记录调度计划）

    注：实际的 cron 触发由 OpenClaw 系统层面配置，
    这里只负责记录和持久化调度计划。
    """

    def __init__(self, state_manager):
        """
        Args:
            state_manager: StateManager 实例（用于持久化）
        """
        self.state_manager = state_manager
        self.jobs: Dict[str, ScheduledJob] = {}

    def schedule(
        self,
        cron_expr: str,
        handler_name: str,
        payload: Dict,
        enabled: bool = True
    ) -> str:
        """
        注册一个定时任务

        Args:
            cron_expr: cron 表达式（如 "0 9 * * *"）
            handler_name: 处理函数名
            payload: 传递给处理函数的参数
            enabled: 是否启用

        Returns:
            job_id
        """
        job_id = str(uuid.uuid4())[:8]
        job = ScheduledJob(
            job_id=job_id,
            cron_expr=cron_expr,
            handler_name=handler_name,
            payload=payload,
            enabled=enabled
        )
        self.jobs[job_id] = job
        return job_id

    def unschedule(self, job_id: str) -> bool:
        """
        取消定时任务

        Args:
            job_id: 任务 ID

        Returns:
            是否成功取消
        """
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """获取任务"""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[ScheduledJob]:
        """获取所有任务"""
        return list(self.jobs.values())

    def get_enabled_jobs(self) -> List[ScheduledJob]:
        """获取所有启用中的任务"""
        return [j for j in self.jobs.values() if j.enabled]

    def enable(self, job_id: str) -> bool:
        """启用任务"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            return True
        return False

    def disable(self, job_id: str) -> bool:
        """禁用任务"""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            return True
        return False

    def to_dict(self) -> Dict:
        """导出为字典（用于序列化）"""
        return {
            "jobs": [j.to_dict() for j in self.jobs.values()]
        }

    @classmethod
    def from_dict(cls, data: Dict, state_manager) -> "Scheduler":
        """从字典恢复"""
        scheduler = cls(state_manager)
        for job_data in data.get("jobs", []):
            job = ScheduledJob(**job_data)
            scheduler.jobs[job.job_id] = job
        return scheduler
