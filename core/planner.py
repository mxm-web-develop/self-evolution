# core/planner.py
"""
方案生成模块

根据诊断结果生成多个候选方案。
注意：resource_estimate 已改为更适合 AI 开发场景的表达，
不再强依赖“工时/人天”。
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
        """
        diag_type = diagnosis.get("type", "unknown")

        plans = []

        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="渐进式改进",
            description=f"以最小风险的方式逐步解决：{problem[:100]}",
            pros=self._get_pros(diag_type, "conservative"),
            cons=self._get_cons(diag_type, "conservative"),
            resource_estimate={
                "effort": "低",
                "scope": "局部优化",
                "automation": "高",
                "execution_style": "小步快跑"
            },
            risks=["可能需要二次迭代", "效果可能不彻底"],
            expected_outcomes=["问题得到缓解", "积累相关经验"]
        ))

        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="全面重构/重做",
            description=f"从根本上解决：{problem[:100]}",
            pros=self._get_pros(diag_type, "aggressive"),
            cons=self._get_cons(diag_type, "aggressive"),
            resource_estimate={
                "effort": "高",
                "scope": "全局改造",
                "automation": "中",
                "execution_style": "阶段推进"
            },
            risks=["影响现有功能", "改动范围大", "回归验证成本高"],
            expected_outcomes=["彻底解决问题", "架构更清晰", "可维护性提升"]
        ))

        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="折中方案",
            description=f"在成本和效果间取得平衡：{problem[:100]}",
            pros=self._get_pros(diag_type, "balanced"),
            cons=self._get_cons(diag_type, "balanced"),
            resource_estimate={
                "effort": "中",
                "scope": "核心链路",
                "automation": "高",
                "execution_style": "先关键后扩展"
            },
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
            "aggressive": ["根因处理更彻底", "长期收益更高"],
            "balanced": ["平衡风险和收益", "更适合持续迭代"]
        }.get(style, [])

        return base + style_pros

    def _get_cons(self, diag_type: str, style: str) -> List[str]:
        style_cons = {
            "conservative": ["可能不是最优解", "后续仍需持续观察"],
            "aggressive": ["改动面大", "验证成本更高", "回滚复杂"],
            "balanced": ["两边都不完美", "需要更细的执行控制"]
        }.get(style, [])

        type_cons = {
            "feature_request": ["需求边界可能继续变化"],
            "bug_fix": ["根因可能未真正找到"],
            "optimization": ["效果可能不明显"],
            "architecture": ["可能影响现有功能"],
            "unknown": []
        }.get(diag_type, [])

        return style_cons + type_cons
