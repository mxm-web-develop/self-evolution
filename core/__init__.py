# core/__init__.py
"""
core — 业务逻辑层（平台无关）

本包包含项目进化系统的所有业务逻辑：
调研、诊断、方案生成、评分、审批、执行、学习。
"""

from .models import Phase, ProjectState, Task, Plan, Case
from .interfaces import (
    ITaskExecutor,
    IStateStore,
    INotifier,
    ISearchProvider,
)
from .investigator import Investigator
from .diagnose import DiagnoseEngine
from .planner import Planner
from .critic import Critic
from .approver import Approver
from .executor import Executor
from .learner import Learner
from .case_library import CaseLibrary

__all__ = [
    # models
    "Phase",
    "ProjectState",
    "Task",
    "Plan",
    "Case",
    # interfaces
    "ITaskExecutor",
    "IStateStore",
    "INotifier",
    "ISearchProvider",
    # modules
    "Investigator",
    "DiagnoseEngine",
    "Planner",
    "Critic",
    "Approver",
    "Executor",
    "Learner",
    "CaseLibrary",
]
