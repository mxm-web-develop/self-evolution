# adapter_openclaw/bridge.py
"""
OpenClawBridge — Core 与 Adapter 之间的桥梁

持有所有 Adapter 实例，供 Core 模块调用
实现依赖倒置
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.case_library import CaseLibrary


class OpenClawBridge:
    """
    Core 与 OpenClaw Adapter 之间的桥梁

    所有 Adapter 实例在此统一持有，
    Core 模块通过此 Bridge 获取所需能力。
    """

    def __init__(
        self,
        projects_root: str,
        cases_root: str,
        search_provider=None,
        default_channel: str = "webchat"
    ):
        """
        Args:
            projects_root: 项目根目录
            cases_root: 案例库根目录
            search_provider: 搜索 Provider 实例
            default_channel: 默认通知渠道
        """
        self.projects_root = Path(projects_root)
        self.cases_root = Path(cases_root)
        self.default_channel = default_channel

        # 延迟导入避免循环依赖（使用相对导入）
        from .state_manager import StateManager
        from .notifier import Notifier
        from .scheduler import Scheduler

        # 初始化 Adapter 实例
        self.state_manager = StateManager(str(self.projects_root))
        self.notifier = Notifier(default_channel)
        self.scheduler = Scheduler(self.state_manager)
        self._search_provider = search_provider

        # TaskExecutor 需要 Bridge 引用，形成循环
        # 所以延迟初始化
        self._task_executor = None

    @property
    def task_executor(self):
        """延迟初始化的 TaskExecutor"""
        if self._task_executor is None:
            from .task_executor import TaskExecutor
            self._task_executor = TaskExecutor(self)
        return self._task_executor

    def get_executor(self):
        """获取 TaskExecutor（供 Core 使用）"""
        return self.task_executor

    def get_state_manager(self):
        """获取 StateManager"""
        return self.state_manager

    def get_notifier(self):
        """获取 Notifier"""
        return self.notifier

    def get_scheduler(self):
        """获取 Scheduler"""
        return self.scheduler

    def get_search_provider(self):
        """获取搜索 Provider"""
        return self._search_provider

    def get_case_library(self):
        """获取 CaseLibrary（延迟创建）"""
        from core.case_library import CaseLibrary
        return CaseLibrary(str(self.cases_root))
