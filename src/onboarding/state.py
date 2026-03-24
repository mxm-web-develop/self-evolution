"""
Onboarding 状态管理
管理 onboarding session 和 state 数据结构
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path


class OnboardingPhase(Enum):
    """Onboarding 阶段"""
    IDLE = "IDLE"
    CONTEXT_CHECK = "CONTEXT_CHECK"
    GATHER_GOAL = "GATHER_GOAL"
    GATHER_NAME = "GATHER_NAME"
    GATHER_BENCHMARKS = "GATHER_BENCHMARKS"
    GATHER_PRIORITIES = "GATHER_PRIORITIES"
    GATHER_BOUNDARIES = "GATHER_BOUNDARIES"
    CONFIRM_PROFILE = "CONFIRM_PROFILE"
    COMPLETED = "COMPLETED"


@dataclass
class OnboardingSession:
    """
    Onboarding 会话状态
    记录当前步骤、已收集字段、项目类型
    """
    project_id: str
    project_type: str = "new"  # "new" or "existing"
    phase: OnboardingPhase = OnboardingPhase.IDLE
    created_at: str = ""
    updated_at: str = ""

    # 收集的字段
    goal: Optional[str] = None
    name: Optional[str] = None
    benchmarks: List[str] = field(default_factory=list)
    priorities: List[Dict[str, Any]] = field(default_factory=list)
    automation_boundaries: List[str] = field(default_factory=list)
    project_path: Optional[str] = None  # for existing projects

    # 步骤历史
    history: List[Dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now

    def touch(self) -> None:
        self.updated_at = datetime.now().isoformat()

    def add_history(self, step: str, value: str) -> None:
        self.history.append({
            "step": step,
            "value": value,
            "at": datetime.now().isoformat()
        })

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "project_type": self.project_type,
            "phase": self.phase.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "goal": self.goal,
            "name": self.name,
            "benchmarks": self.benchmarks,
            "priorities": self.priorities,
            "automation_boundaries": self.automation_boundaries,
            "project_path": self.project_path,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OnboardingSession":
        data = data.copy()
        data["phase"] = OnboardingPhase(data.get("phase", "IDLE"))
        return cls(**data)


@dataclass
class OnboardingState:
    """
    持久化的 onboarding 状态（写入 projects/{id}/state.json）
    对应 docs/onboarding-templates/state.json
    """
    project_id: str
    project_name: str
    phase: str = "IDLE"
    created_at: str = ""
    updated_at: str = ""

    current_goal: Optional[str] = None
    started_at: Optional[str] = None
    last_active_at: Optional[str] = None

    onboarding: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    progress: Dict[str, Any] = field(default_factory=lambda: {
        "investigation_completed": False,
        "diagnosis_completed": False,
        "plans_generated": 0,
        "approved_plan_id": None,
        "execution_completed": False,
        "learning_written": False,
    })
    last_error: Optional[str] = None

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.started_at:
            self.started_at = now
        self.updated_at = now
        self.last_active_at = now

    def mark_completed(self) -> None:
        self.onboarding = {
            "completed": True,
            "completed_at": datetime.now().isoformat(),
            "steps_collected": [
                s["step"] for s in getattr(self, "_history_steps", [])
            ]
        }
        self.phase = "IDLE"
        self.updated_at = datetime.now().isoformat()

    def touch(self) -> None:
        self.updated_at = datetime.now().isoformat()
        self.last_active_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.0",
            "project_id": self.project_id,
            "project_name": self.project_name,
            "phase": self.phase,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_goal": self.current_goal,
            "started_at": self.started_at,
            "last_active_at": self.last_active_at,
            "onboarding": self.onboarding,
            "context": self.context,
            "progress": self.progress,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OnboardingState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def load(cls, project_dir: Path) -> Optional["OnboardingState"]:
        """从项目目录加载 state.json"""
        state_file = project_dir / "state.json"
        if not state_file.exists():
            return None
        with open(state_file, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def save(self, project_dir: Path) -> None:
        """保存 state.json 到项目目录"""
        project_dir.mkdir(parents=True, exist_ok=True)
        with open(project_dir / "state.json", "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
