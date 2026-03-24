# core/critic.py
"""
评分/批判模块

对候选方案进行三维评分
"""

from typing import Dict, Any
from .models import Plan


class Critic:
    """评分/批判模块"""

    # 评分权重
    WEIGHTS = {
        "business": 0.3,   # 业务价值
        "technical": 0.4,  # 技术可行性
        "ux": 0.3          # 用户体验
    }

    def score_plan(self, plan: Plan, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        对方案进行三维评分

        Args:
            plan: Plan 对象
            context: 上下文（可选）

        Returns:
            评分结果 dict：
            - business: 业务价值（0-10）
            - technical: 技术可行性（0-10）
            - ux: 用户体验（0-10）
            - final: 加权总分（0-10）
            - recommendation: 建议（推荐通过/建议修改后重审/建议否决）
        """
        business = self._score_business(plan, context)
        technical = self._score_technical(plan)
        ux = self._score_ux(plan)

        final = (
            business * self.WEIGHTS["business"] +
            technical * self.WEIGHTS["technical"] +
            ux * self.WEIGHTS["ux"]
        )

        return {
            "business": round(business, 1),
            "technical": round(technical, 1),
            "ux": round(ux, 1),
            "final": round(final, 1),
            "recommendation": self._get_recommendation(final)
        }

    def _score_business(self, plan: Plan, context: Dict = None) -> float:
        """业务价值评分（0-10）"""
        outcome_count = len(plan.expected_outcomes)
        risk_count = len(plan.risks)
        pro_count = len(plan.pros)

        score = outcome_count * 2.5 + pro_count * 1.0 - risk_count * 0.5
        return min(10.0, max(1.0, score))

    def _score_technical(self, plan: Plan) -> float:
        """技术可行性评分（0-10）"""
        days = plan.resource_estimate.get("days", 7)
        people = plan.resource_estimate.get("people", 1)
        cost = plan.resource_estimate.get("cost", "medium")

        # 工时越大，可行性越低
        effort = days * people
        effort_score = max(1.0, min(10.0, 20.0 - effort * 0.4))

        # 成本加成
        cost_map = {"low": 10.0, "medium": 7.5, "high": 5.0}
        cost_score = cost_map.get(cost, 7.5)

        return (effort_score * 0.6 + cost_score * 0.4)

    def _score_ux(self, plan: Plan) -> float:
        """用户体验评分（0-10）"""
        # 风险多则 UX 低
        risk_penalty = len(plan.risks) * 1.5
        # 劣势多则 UX 低
        con_penalty = len(plan.cons) * 1.0
        # 优势多则 UX 高
        pro_bonus = len(plan.pros) * 0.5

        score = 10.0 - risk_penalty - con_penalty + pro_bonus
        return min(10.0, max(1.0, score))

    def _get_recommendation(self, final: float) -> str:
        """根据总分给出建议"""
        if final >= 7.0:
            return "推荐通过"
        elif final >= 5.0:
            return "建议修改后重审"
        else:
            return "建议否决"
