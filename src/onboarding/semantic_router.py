"""
Semantic Router v1 — 统一动作路由层

将用户自然语言映射为结构化动作（Route），支持：
1. Rule fast-path：高置信度规则匹配
2. Semantic fallback：规则增强版自由表达归一化
3. LLM adapter hook：预留未来接入在线 LLM 的接口

设计原则：
- 保持现有 public API 不炸
- 优先保证可读性和后续可扩展性
- 为未来 LLM 路由预留 adapter interface
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from .route_models import (
    Route,
    RouteAction,
    RiskLevel,
    DecisionMode,
    RouteContext,
)
from .intent_parser import EvolveIntentParser, ParsedIntent


# =============================================================================
# 高风险动作定义（需要确认门）
# =============================================================================

HIGH_RISK_ACTIONS = {
    RouteAction.EXECUTE,
    RouteAction.APPROVE,
    RouteAction.NEW_PROJECT,
    RouteAction.EXISTING_PROJECT,
    RouteAction.SWITCH_PROJECT,
}

CONFIRM_REQUIRED_ACTIONS = {
    RouteAction.EXECUTE,
    RouteAction.APPROVE,
    RouteAction.EXISTING_PROJECT,
    RouteAction.SWITCH_PROJECT,
}

# 确认短语（用户表示确认）
CONFIRM_PHRASES = {
    "确认", "确认执行", "确认批准", "继续", "是的", "好的", "好", "可以",
    "confirm", "confirmed", "yes", "yeah", "sure", "go ahead", "do it",
    "执行", "批准", "通过", "approve", "ok",
}

# 取消/拒绝短语
CANCEL_PHRASES = {
    "取消", "退出", "停止", "不要", "算了",
    "cancel", "stop", "quit", "no", "don't", "abort",
}


class SemanticRouter:
    """
    Semantic Router v1
    
    将用户输入路由为结构化动作。
    v1 使用规则增强版，预留 LLM adapter 接口。
    """
    
    def __init__(self):
        self.intent_parser = EvolveIntentParser()
    
    def route(self, text: str, context: Optional[RouteContext] = None) -> Route:
        """
        主路由入口
        
        Args:
            text: 用户输入
            context: 路由上下文（当前状态）
        
        Returns:
            Route: 结构化路由结果
        """
        text = (text or "").strip()
        if not text:
            return self._unknown_route(text)
        
        # 1. Rule fast-path（高置信度）
        route = self._rule_fast_path(text, context)
        if route and route.confidence >= 0.85:
            return self._apply_risk_gate(route, text, context)
        
        # 2. Semantic fallback（规则增强版自由表达）
        route = self._semantic_fallback(text, context)
        if route:
            return self._apply_risk_gate(route, text, context)
        
        # 3. 未知路由
        return self._unknown_route(text)
    
    def _rule_fast_path(self, text: str, context: Optional[RouteContext] = None) -> Optional[Route]:
        """
        Rule fast-path：复用现有 intent_parser 的高置信度匹配
        
        负责：
        - /evolve 显式命令
        - 明确路径
        - status/active/switch/cancel
        - approve/reject/revise/execute 的高置信短语
        """
        parsed = self.intent_parser.parse(text)
        if not parsed:
            return None
        
        # 显式命令
        if text.startswith("/evolve"):
            return self._parse_evolve_command(text, context)
        
        # 映射 intent 到 RouteAction
        action_map = {
            "cancel": (RouteAction.CANCEL, RiskLevel.LOW),
            "switch": (RouteAction.SWITCH_PROJECT, RiskLevel.MEDIUM),
            "status": (RouteAction.STATUS, RiskLevel.LOW),
            "active": (RouteAction.ACTIVE_PROJECT, RiskLevel.LOW),
            "analyze": (RouteAction.ANALYZE, RiskLevel.LOW),
            "plan": (RouteAction.PLAN, RiskLevel.LOW),
            "execute": (RouteAction.EXECUTE, RiskLevel.HIGH),
            "approve": (RouteAction.APPROVE, RiskLevel.HIGH),
            "new": (RouteAction.NEW_PROJECT, RiskLevel.MEDIUM),
            "start": (RouteAction.NEW_PROJECT, RiskLevel.MEDIUM),
            "existing": (RouteAction.EXISTING_PROJECT, RiskLevel.MEDIUM),
            "help": (RouteAction.HELP, RiskLevel.LOW),
        }
        
        if parsed.kind in action_map:
            action, risk = action_map[parsed.kind]
            entities = {}
            
            # 提取实体
            if parsed.kind == "switch" and parsed.command:
                parts = parsed.command.split()
                if len(parts) > 2:
                    entities["project_id"] = parts[2]
            elif parsed.kind == "execute" and parsed.analyze_problem:
                entities["plan_id"] = parsed.analyze_problem
            
            return Route(
                action=action,
                confidence=parsed.confidence,
                source="rule",
                risk_level=risk,
                entities=entities,
                original_text=text,
            )
        
        return None
    
    def _parse_evolve_command(self, text: str, context: Optional[RouteContext] = None) -> Route:
        """解析 /evolve 命令"""
        parts = text.split(maxsplit=2)
        cmd = parts[1] if len(parts) > 1 else ""
        arg = parts[2] if len(parts) > 2 else ""
        
        # 直接路径（接入已有项目）
        if len(parts) == 2 and Path(parts[1]).expanduser().exists():
            return Route(
                action=RouteAction.EXISTING_PROJECT,
                confidence=0.98,
                source="rule",
                risk_level=RiskLevel.MEDIUM,
                entities={"path": parts[1]},
                original_text=text,
            )
        
        cmd_map = {
            "status": (RouteAction.STATUS, RiskLevel.LOW),
            "list": (RouteAction.STATUS, RiskLevel.LOW),
            "ls": (RouteAction.STATUS, RiskLevel.LOW),
            "active": (RouteAction.ACTIVE_PROJECT, RiskLevel.LOW),
            "switch": (RouteAction.SWITCH_PROJECT, RiskLevel.MEDIUM),
            "new": (RouteAction.NEW_PROJECT, RiskLevel.MEDIUM),
            "analyze": (RouteAction.ANALYZE, RiskLevel.LOW),
            "plan": (RouteAction.PLAN, RiskLevel.LOW),
            "approve": (RouteAction.APPROVE, RiskLevel.HIGH),
            "execute": (RouteAction.EXECUTE, RiskLevel.HIGH),
            "reject": (RouteAction.REJECT, RiskLevel.HIGH),
            "revise": (RouteAction.REVISE, RiskLevel.HIGH),
            "help": (RouteAction.HELP, RiskLevel.LOW),
            "cancel": (RouteAction.CANCEL, RiskLevel.LOW),
        }
        
        if cmd in cmd_map:
            action, risk = cmd_map[cmd]
            entities = {}
            if arg:
                if cmd == "switch":
                    entities["project_id"] = arg
                elif cmd in {"approve", "execute", "reject", "revise", "plan"}:
                    entities["plan_id"] = arg
                elif cmd == "new":
                    entities["goal"] = arg
            
            return Route(
                action=action,
                confidence=0.95,
                source="rule",
                risk_level=risk,
                entities=entities,
                original_text=text,
            )
        
        return Route(
            action=RouteAction.UNKNOWN,
            confidence=0.5,
            source="rule",
            original_text=text,
        )
    
    def _semantic_fallback(self, text: str, context: Optional[RouteContext] = None) -> Optional[Route]:
        """
        Semantic fallback：规则增强版自由表达归一化
        
        处理非命令式的自然语言表达。
        """
        lowered = text.lower()
        compact = re.sub(r"\s+", " ", lowered)
        
        # 确认回复（针对 pending approval）
        if context and context.pending_approval:
            if any(p in compact for p in CONFIRM_PHRASES):
                return Route(
                    action=RouteAction.APPROVE,
                    confidence=0.95,
                    source="semantic",
                    risk_level=RiskLevel.HIGH,
                    entities={"plan_id": context.pending_approval_plan_id},
                    metadata={"confirmed": True},
                    original_text=text,
                )
            if any(p in compact for p in CANCEL_PHRASES):
                return Route(
                    action=RouteAction.CANCEL,
                    confidence=0.95,
                    source="semantic",
                    risk_level=RiskLevel.LOW,
                    original_text=text,
                )
        
        # 新建项目（自由表达）
        new_project_patterns = [
            (r"帮我 (?:新建 | 创建 | 开始 | 做个) (?:一个)?项目", RouteAction.NEW_PROJECT),
            (r"想要 (?:一个)?新项目", RouteAction.NEW_PROJECT),
            (r"新项目.*[:：]?\s*(.*)", RouteAction.NEW_PROJECT),
            (r"(?:new|create|start).*project", RouteAction.NEW_PROJECT),
        ]
        for pattern, action in new_project_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                entities = {}
                match = re.search(r"新项目.*[:：]?\s*(.*)", text)
                if match and match.group(1).strip():
                    entities["goal"] = match.group(1).strip()
                return Route(
                    action=action,
                    confidence=0.85,
                    source="semantic",
                    risk_level=RiskLevel.MEDIUM,
                    entities=entities,
                    original_text=text,
                )
        
        # 查看项目列表
        list_patterns = [
            r"(?:看看 | 查看 | 列出 | 显示 | 有哪些).*(?:项目 | 项目列表)",
            r"(?:项目 | 项目列表).*(?:有哪些 | 列表 | 清单)",
            r"(?:show|list|view).*(?:project|projects)",
        ]
        for pattern in list_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return Route(
                    action=RouteAction.STATUS,
                    confidence=0.88,
                    source="semantic",
                    risk_level=RiskLevel.LOW,
                    original_text=text,
                )
        
        # 分析/诊断
        analyze_patterns = [
            (r"帮我 (?:分析 | 诊断 | 研究 | 调研) (?:这个)?项目", RouteAction.ANALYZE),
            (r"(?:分析 | 诊断| 调研| 研究).*(?:问题 | 方向 | 建议)", RouteAction.ANALYZE),
            (r"(?:analyze|diagnose|research).*(?:project|problem)", RouteAction.ANALYZE),
        ]
        for pattern, action in analyze_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return Route(
                    action=action,
                    confidence=0.85,
                    source="semantic",
                    risk_level=RiskLevel.LOW,
                    original_text=text,
                )
        
        # 生成方案
        plan_patterns = [
            (r"帮我 (?:生成 | 制定 | 规划) (?:一个)?方案", RouteAction.PLAN),
            (r"(?:方案 | 计划).*(?:生成 | 制定 | 规划 | 有哪些)", RouteAction.PLAN),
            (r"(?:make|generate|create).*plan", RouteAction.PLAN),
            (r"下一步.*(?:做什么 | 是什么)", RouteAction.PLAN),
        ]
        for pattern, action in plan_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return Route(
                    action=action,
                    confidence=0.85,
                    source="semantic",
                    risk_level=RiskLevel.LOW,
                    original_text=text,
                )
        
        # 执行方案（高风险）
        execute_patterns = [
            (r"执行.*方案.*([abcABC])", RouteAction.EXECUTE),
            (r"(?:批准 | 通过| 采纳).*方案", RouteAction.APPROVE),
            (r"(?:approve|execute|run).*(?:plan|option)", RouteAction.EXECUTE),
        ]
        for pattern, action in execute_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities = {}
                plan_match = re.search(r"方案.*([abcABC])", text)
                if plan_match:
                    entities["plan_label"] = plan_match.group(1).upper()
                return Route(
                    action=action,
                    confidence=0.88,
                    source="semantic",
                    risk_level=RiskLevel.HIGH,
                    entities=entities,
                    original_text=text,
                )
        
        # 切换项目
        switch_patterns = [
            (r"切换 (?:到)?(?:项目)?\s*([a-zA-Z0-9_-]+)", RouteAction.SWITCH_PROJECT),
            (r"切到\s*([a-zA-Z0-9_-]+)", RouteAction.SWITCH_PROJECT),
            (r"switch.*(?:to)?\s*([a-zA-Z0-9_-]+)", RouteAction.SWITCH_PROJECT),
        ]
        for pattern, action in switch_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return Route(
                    action=action,
                    confidence=0.88,
                    source="semantic",
                    risk_level=RiskLevel.MEDIUM,
                    entities={"project_id": match.group(1)},
                    original_text=text,
                )
        
        # 取消
        if any(p in compact for p in CANCEL_PHRASES):
            return Route(
                action=RouteAction.CANCEL,
                confidence=0.9,
                source="semantic",
                risk_level=RiskLevel.LOW,
                original_text=text,
            )
        
        return None
    
    def _apply_risk_gate(self, route: Route, text: str, context: Optional[RouteContext] = None) -> Route:
        """
        应用风险门（confirmation gate）
        
        对高风险动作，如果不是已确认的，设置 decision_mode 为 CONFIRM_REQUIRED
        """
        if route.action in CONFIRM_REQUIRED_ACTIONS:
            if route.metadata.get("confirmed", False):
                route.decision_mode = DecisionMode.AUTO
            else:
                route.decision_mode = DecisionMode.CONFIRM_REQUIRED
                route.clarification_question = (
                    f"⚠️ 这个操作会改变项目状态或触发后续动作，请确认是否继续？\n"
                    f"回复「确认」继续，或回复「取消」放弃。"
                )
        
        return route
    
    def _unknown_route(self, text: str) -> Route:
        """未知路由"""
        return Route(
            action=RouteAction.UNKNOWN,
            confidence=0.0,
            source="rule",
            risk_level=RiskLevel.LOW,
            clarification_question="抱歉，我没有理解你的意思。你可以试试：\n- 帮我新建项目\n- 看看项目列表\n- 帮我分析当前项目\n- 生成方案",
            original_text=text,
        )
    
    def is_confirmation_response(self, text: str) -> bool:
        """检查是否是确认回复"""
        compact = re.sub(r"\s+", " ", (text or "").lower()).strip()
        return any(p in compact for p in CONFIRM_PHRASES)
    
    def is_cancellation_response(self, text: str) -> bool:
        """检查是否是取消回复"""
        compact = re.sub(r"\s+", " ", (text or "").lower()).strip()
        return any(p in compact for p in CANCEL_PHRASES)


# =============================================================================
# LLM Adapter Interface（预留接口）
# =============================================================================

class LLMRouterAdapter:
    """
    LLM Router Adapter Interface
    
    预留接口，用于未来接入在线 LLM 进行语义路由。
    实现此接口的类可以替换 SemanticRouter 中的规则路由。
    """
    
    def route(self, text: str, context: Optional[RouteContext] = None) -> Route:
        """
        使用 LLM 进行语义路由
        
        Args:
            text: 用户输入
            context: 路由上下文
        
        Returns:
            Route: 结构化路由结果
        """
        raise NotImplementedError("Subclasses must implement route()")
    
    def health_check(self) -> bool:
        """检查 LLM 服务是否可用"""
        raise NotImplementedError("Subclasses must implement health_check()")


class MockLLMRouterAdapter(LLMRouterAdapter):
    """
    Mock LLM Router Adapter
    
    用于测试，返回固定路由。
    """
    
    def route(self, text: str, context: Optional[RouteContext] = None) -> Route:
        return Route(
            action=RouteAction.UNKNOWN,
            confidence=0.5,
            source="llm_mock",
            original_text=text,
        )
    
    def health_check(self) -> bool:
        return True
