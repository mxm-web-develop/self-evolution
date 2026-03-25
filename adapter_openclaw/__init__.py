# adapter_openclaw/__init__.py
"""
adapter_openclaw — OpenClaw 平台适配层

本包提供 OpenClaw 工具的封装实现，
供 Core 层通过 Bridge 调用。
"""

from .bridge import OpenClawBridge
from .orchestrator import ProjectEvolutionOrchestrator
from .state_manager import StateManager
from .notifier import Notifier
from .scheduler import Scheduler

# TaskExecutor 需要 openclaw 模块，仅在 OpenClaw 环境中可用
# 通过 bridge.task_executor 延迟访问，不在此处直接导入
__all__ = [
    "OpenClawBridge",
    "ProjectEvolutionOrchestrator",
    "StateManager",
    "Notifier",
    "Scheduler",
]
