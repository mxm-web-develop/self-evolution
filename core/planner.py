# core/planner.py
"""
方案生成模块

根据诊断结果生成多个候选方案
"""

from typing import Dict, List, Any
from .models import Plan
import uuid


class Planner:
    """方案生成模块"""

    def generate_plans(
        self,
        problem: str,
        diagnosis: Dict[str, Any],
        investigation: Dict[str, Any]
    ) -> List[Plan]:
        """
        根据诊断结果生成候选方案

        Args:
            problem: 原始问题描述
            diagnosis: 诊断结果
            investigation: 调研报告

        Returns:
            Plan 对象列表（通常3个：保守/激进/折中）
        """
        diag_type = diagnosis.get("type", "unknown")
        priority = diagnosis.get("priority", 5)

        plans = []

        # 方案 A：保守方案（最小风险）
        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="渐进式改进",
            description=f"以最小风险的方式逐步解决：{problem[:100]}",
            pros=self._get_pros(diag_type, "conservative"),
            cons=self._get_cons(diag_type, "conservative"),
            resource_estimate={"days": 2, "people": 1, "cost": "low"},
            risks=["可能需要二次迭代", "效果可能不彻底"],
            expected_outcomes=["问题得到缓解", "积累相关经验"]
        ))

        # 方案 B：激进方案（彻底解决）
        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="全面重构/重做",
            description=f"从根本上解决：{problem[:100]}",
            pros=self._get_pros(diag_type, "aggressive"),
            cons=self._get_cons(diag_type, "aggressive"),
            resource_estimate={"days": 14, "people": 2, "cost": "high"},
            risks=["影响现有功能", "周期长", "成本高"],
            expected_outcomes=["彻底解决问题", "架构更清晰", "可维护性提升"]
        ))

        # 方案 C：折中方案
        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="折中方案",
            description=f"在成本和效果间取得平衡：{problem[:100]}",
            pros=self._get_pros(diag_type, "balanced"),
            cons=self._get_cons(diag_type, "balanced"),
            resource_estimate={"days": 5, "people": 1, "cost": "medium"},
            risks=["两边都不完美", "需要精细执行"],
            expected_outcomes=["较好解决问题", "风险可控"]
        ))

        return plans

    def _get_pros(self, diag_type: str, style: str) -> List[str]:
        base = {
            "feature_request": ["满足用户需求", "提升产品竞争力"],
            "bug_fix": ["消除用户痛点", "提升稳定性"],
            "optimization": ["提升用户体验", "降低资源消耗"],
            "architecture": ["提升系统可维护性", "为未来扩展打好基础"],
            "unknown": ["解决当前问题", "改善现状"]
        }.get(diag_type, ["解决当前问题"])

        style_pros = {
            "conservative": ["风险低", "可快速启动", "易于回滚"],
            "aggressive": ["一劳永逸", "效果最彻底"],
            "balanced": ["平衡风险和收益", "周期适中"]
        }.get(style, [])

        return base + style_pros

    def _get_cons(self, diag_type: str, style: str) -> List[str]:
        style_cons = {
            "conservative": ["可能不是最优解", "周期较长"],
            "aggressive": ["成本高", "风险大", "周期长"],
            "balanced": ["两边都不完美", "需要精细执行"]
        }.get(style, [])

        type_cons = {
            "feature_request": ["开发周期不确定"],
            "bug_fix": ["根因可能未真正找到"],
            "optimization": ["效果可能不明显"],
            "architecture": ["可能影响现有功能"],
            "unknown": []
        }.get(diag_type, [])

        return style_cons + type_cons
