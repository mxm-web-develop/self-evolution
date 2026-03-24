# adapter_openclaw/__init__.py
"""
adapter_openclaw — OpenClaw 平台适配层

本包提供 OpenClaw 工具的封装实现，
供 Core 层通过 Bridge 调用。
"""

from .bridge import OpenClawBridge
from .orchestrator import ProjectEvolutionOrchestrator
from .state_manager import StateManager
from .task_executor import TaskExecutor
from .notifier import Notifier
from .scheduler import Scheduler

__all__ = [
    "OpenClawBridge",
    "ProjectEvolutionOrchestrator",
    "StateManager",
    "TaskExecutor",
    "Notifier",
    "Scheduler",
]
