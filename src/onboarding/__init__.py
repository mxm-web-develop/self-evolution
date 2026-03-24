"""
Onboarding 模块
统一入口，支持新项目初始化和已有项目接入
"""

from .index_manager import ProjectIndex
from .state import OnboardingSession, OnboardingState, OnboardingPhase
from .new_project import NewProjectInitializer
from .existing_project import ExistingProjectInitializer
from .router import OnboardingRouter

__all__ = [
    "ProjectIndex",
    "OnboardingSession",
    "OnboardingState",
    "OnboardingPhase",
    "NewProjectInitializer",
    "ExistingProjectInitializer",
    "OnboardingRouter",
]
