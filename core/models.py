# core/models.py
"""
数据模型定义

所有业务对象使用 @dataclass 定义，支持 JSON 序列化/反序列化
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class Phase(Enum):
    """项目阶段枚举"""
    IDLE = "idle"
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    PLANNING = "planning"
    CRITIQUING = "critiquing"
    APPROVING = "approving"
    EXECUTING = "executing"
    LEARNING = "learning"


@dataclass
class ProjectState:
    """项目状态"""
    project_id: str
    phase: Phase
    created_at: str
    updated_at: str
    current_task: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转为字典（用于 JSON 序列化）"""
        return {
            "project_id": self.project_id,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_task": self.current_task,
            "context": self.context,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState":
        """从字典恢复，只取 dataclass 已知字段，忽略多余字段。"""
        # 兼容大小写：onboarding 保存 "IDLE"，enum 值是 "idle"
        data = data.copy()
        phase_str = str(data.get("phase", "idle")).lower()
        data["phase"] = Phase(phase_str)
        # 只传 dataclass 已知字段
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def add_history(self, action: str, detail: str = "") -> None:
        """添加历史记录"""
        self.history.append({
            "action": action,
            "detail": detail,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })


@dataclass
class Task:
    """任务单元（用于子代理执行）"""
    task_id: str
    title: str
    description: str
    task_type: str  # investigation | planning | execution
    input_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending | running | done | failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)


@dataclass
class Plan:
    """方案"""
    plan_id: str
    project_id: str
    title: str
    description: str
    pros: List[str]
    cons: List[str]
    resource_estimate: Dict[str, Any]
    risks: List[str]
    expected_outcomes: List[str]
    action_items: Optional[List[str]] = None
    scores: Optional[Dict[str, float]] = None
    approved: Optional[bool] = None
    approver_notes: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        return cls(**data)


@dataclass
class Case:
    """案例（已完成的经验沉淀）"""
    case_id: str
    category: str
    tags: List[str]
    problem: str
    investigation_summary: str
    diagnosis: str
    plan_executed: str
    result: str
    lessons: str
    outcome: str  # success | failure | partial
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Case":
        return cls(**data)
