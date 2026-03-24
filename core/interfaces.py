# core/interfaces.py
"""
抽象接口定义

为 Core 层解耦做准备
Adapter 必须实现这些接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import Task, ProjectState


class ITaskExecutor(ABC):
    """子代理执行器接口"""

    @abstractmethod
    def spawn(self, task: Task, context: Dict[str, Any]) -> str:
        """
        启动子代理，返回 session_id
        """
        pass

    @abstractmethod
    def wait(self, session_id: str, timeout_ms: int) -> Dict[str, Any]:
        """
        等待子代理完成，返回结果
        """
        pass


class IStateStore(ABC):
    """状态存储接口"""

    @abstractmethod
    def save_state(self, project_id: str, state: ProjectState) -> None:
        pass

    @abstractmethod
    def load_state(self, project_id: str) -> Optional[ProjectState]:
        pass

    @abstractmethod
    def save_plan(self, project_id: str, plan) -> None:
        pass


class INotifier(ABC):
    """通知接口"""

    @abstractmethod
    def notify_user(self, text: str, channel: str, target: Optional[str]) -> None:
        pass

    @abstractmethod
    def notify_approval_request(
        self,
        project_id: str,
        plan_title: str,
        scores: Dict[str, float]
    ) -> None:
        pass


class ISearchProvider(ABC):
    """搜索 Provider 接口"""

    @abstractmethod
    def search(self, query: str, count: int) -> List["SearchResult"]:
        pass

    @abstractmethod
    def fetch(self, url: str, max_chars: int) -> str:
        pass

    def health_check(self) -> bool:
        """健康检查，默认实现"""
        try:
            self.search("test", count=1)
            return True
        except Exception:
            return False


# 前向引用，避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import SearchResult
