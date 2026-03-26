from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class Phase(Enum):
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
    project_id: str
    phase: Phase
    created_at: str
    updated_at: str
    current_task: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_task": self.current_task,
            "context": self.context,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState":
        data = data.copy()
        data["phase"] = Phase(str(data.get("phase", "idle")).lower())
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def add_history(self, action: str, detail: str = "", payload: Optional[Dict[str, Any]] = None) -> None:
        item = {
            "action": action,
            "detail": detail,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        if payload is not None:
            item["payload"] = payload
        self.history.append(item)


@dataclass
class Task:
    task_id: str
    title: str
    description: str
    task_type: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)


@dataclass
class Plan:
    plan_id: str
    project_id: str
    title: str
    description: str
    pros: List[str]
    cons: List[str]
    resource_estimate: Dict[str, Any]
    risks: List[str]
    expected_outcomes: List[str]
    target_dimension: Optional[str] = None
    maturity_assessment: Optional[Dict[str, Any]] = None
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
    case_id: str
    category: str
    tags: List[str]
    problem: str
    investigation_summary: str
    diagnosis: str
    plan_executed: str
    result: str
    lessons: str
    outcome: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Case":
        return cls(**data)
