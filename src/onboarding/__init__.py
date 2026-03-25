"""
Onboarding 模块
统一入口，支持新项目初始化、已有项目接入和 /evolve 对话流
"""

from .index_manager import ProjectIndex
from .state import OnboardingSession, OnboardingState, OnboardingPhase
from .new_project import NewProjectInitializer
from .existing_project import ExistingProjectInitializer
from .router import OnboardingRouter
from .chat_flow import EvolveChatFlow
from .intent_parser import EvolveIntentParser, ParsedIntent
from .route_models import Route, RouteAction, RiskLevel, DecisionMode, RouteContext
from .semantic_router import SemanticRouter

__all__ = [
    "ProjectIndex",
    "OnboardingSession",
    "OnboardingState",
    "OnboardingPhase",
    "NewProjectInitializer",
    "ExistingProjectInitializer",
    "OnboardingRouter",
    "EvolveChatFlow",
    "EvolveIntentParser",
    "ParsedIntent",
    "Route",
    "RouteAction",
    "RiskLevel",
    "DecisionMode",
    "RouteContext",
    "SemanticRouter",
]
