"""
Semantic Router - 数据模型定义

定义统一的路由输出结构，为未来接入 LLM 预留接口。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class RouteAction(Enum):
    """支持的动作类型"""
    # 项目管理
    NEW_PROJECT = "new_project"
    EXISTING_PROJECT = "existing_project"
    LIST_PROJECTS = "list_projects"
    SWITCH_PROJECT = "switch_project"
    ACTIVE_PROJECT = "active_project"
    CANCEL = "cancel"
    
    # 分析诊断
    ANALYZE = "analyze"
    DIAGNOSE = "diagnose"
    
    # 方案规划
    PLAN = "plan"
    VIEW_PLAN = "view_plan"
    
    # 审批执行（高风险）
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    EXECUTE = "execute"
    
    # 帮助/状态
    HELP = "help"
    STATUS = "status"
    
    # 未知/需要澄清
    UNKNOWN = "unknown"
    CLARIFICATION_NEEDED = "clarification_needed"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"  # 查询类操作
    MEDIUM = "medium"  # 创建/切换项目
    HIGH = "high"  # 执行/审批/导入


class DecisionMode(Enum):
    """决策模式"""
    AUTO = "auto"  # 自动执行
    CONFIRM_REQUIRED = "confirm_required"  # 需要确认
    CLARIFICATION_NEEDED = "clarification_needed"  # 需要更多信息


@dataclass
class Route:
    """
    Semantic Router 的输出结构
    
    统一的动作层，包含：
    - action: 要执行的动作
    - confidence: 置信度 (0-1)
    - source: 路由来源 (rule/semantic/llm)
    - risk_level: 风险等级
    - decision_mode: 决策模式（自动/确认/澄清）
    - entities: 提取的实体（项目 ID、方案 ID、路径等）
    - clarification_question: 如果需要澄清，要问的问题
    - original_text: 原始用户输入
    """
    action: RouteAction
    confidence: float = 0.0
    source: str = "rule"  # rule | semantic | llm
    risk_level: RiskLevel = RiskLevel.LOW
    decision_mode: DecisionMode = DecisionMode.AUTO
    entities: Dict[str, Any] = field(default_factory=dict)
    clarification_question: Optional[str] = None
    original_text: str = ""
    
    # 扩展字段，为未来 LLM 路由预留
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "confidence": self.confidence,
            "source": self.source,
            "risk_level": self.risk_level.value,
            "decision_mode": self.decision_mode.value,
            "entities": self.entities,
            "clarification_question": self.clarification_question,
            "original_text": self.original_text,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Route":
        return cls(
            action=RouteAction(data.get("action", "unknown")),
            confidence=data.get("confidence", 0.0),
            source=data.get("source", "rule"),
            risk_level=RiskLevel(data.get("risk_level", "low")),
            decision_mode=DecisionMode(data.get("decision_mode", "auto")),
            entities=data.get("entities", {}),
            clarification_question=data.get("clarification_question"),
            original_text=data.get("original_text", ""),
            metadata=data.get("metadata", {}),
        )
    
    def is_confirmed_action(self) -> bool:
        """检查是否是已确认的高风险动作"""
        return self.metadata.get("confirmed", False)


@dataclass
class RouteContext:
    """
    路由上下文
    包含当前状态信息，用于路由决策
    """
    user_input: str
    active_project: Optional[Dict[str, Any]] = None
    onboarding_active: bool = False
    onboarding_step: Optional[str] = None
    pending_approval: bool = False
    pending_approval_plan_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "user_input": self.user_input,
            "active_project": self.active_project,
            "onboarding_active": self.onboarding_active,
            "onboarding_step": self.onboarding_step,
            "pending_approval": self.pending_approval,
            "pending_approval_plan_id": self.pending_approval_plan_id,
        }
