"""动态方案生成器：方案数量由差距维度决定，不再写死方向字典。"""

from __future__ import annotations

import json
import uuid
from typing import Dict, List, Any, Optional

from .models import Plan


class Planner:
    def generate_plans(
        self,
        problem: str,
        diagnosis: Dict[str, Any],
        investigation: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> List[Plan]:
        project_context = project_context or {}
        dims = self._extract_gap_dims(diagnosis)
        plans = [
            self._generate_plan_for_dim(problem, dim, diagnosis, investigation, project_context)
            for dim in dims
        ]
        plans = self._prioritize_plans(plans, diagnosis)
        self._debug_print("PLANS", [p.to_dict() for p in plans])
        return plans

    def _extract_gap_dims(self, diagnosis: Dict[str, Any]) -> List[Dict[str, Any]]:
        return diagnosis.get("optimization_dimensions", []) or []

    def _generate_plan_for_dim(
        self,
        problem: str,
        dim: Dict[str, Any],
        diagnosis: Dict[str, Any],
        investigation: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Plan:
        dimension = dim.get("dimension", "未命名维度")
        maturity = diagnosis.get("maturity_assessment") or investigation.get("maturity_assessment")
        title = f"补齐「{dimension}」成熟度缺口"
        action_items = list(dict.fromkeys((dim.get("recommended_actions") or []) + self._extra_actions(dimension, context, investigation)))[:6]
        expected = [
            f"当前状态从「{dim.get('current_state', '未知')}」提升到更接近成熟标准。",
            f"达到的成熟标准：{dim.get('mature_standard', '待补充')}。",
        ]
        return Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id=context.get("project_info", {}).get("id", "current"),
            title=title,
            description=(
                f"围绕维度「{dimension}」制定行动方案。\n"
                f"- 问题背景：{problem[:120]}\n"
                f"- 当前现状：{dim.get('current_state', '未知')}\n"
                f"- 成熟标准：{dim.get('mature_standard', '未知')}"
            ),
            pros=[
                "直接对应本轮最大差距维度",
                "可与历史分析结果串联，避免重复空泛建议",
                "便于后续单维度迭代和验证",
            ],
            cons=[
                "如果缺少更细代码/数据证据，仍需执行中持续校准",
            ],
            resource_estimate={
                "effort": self._effort_from_gap(dim.get("gap_score", 5)),
                "scope": "核心链路" if dim.get("gap_score", 0) >= 8 else "局部到中等范围",
                "automation": "中",
                "execution_style": "先补基线，再做精修",
                "priority": dim.get("priority", "medium"),
                "gap_score": dim.get("gap_score", 0),
            },
            risks=[
                "如果审美/业务期待未进一步对齐，方案可能还需二次收敛",
                "某些成熟标准需要真实用户反馈才能完全验证",
            ],
            expected_outcomes=expected,
            target_dimension=dimension,
            maturity_assessment=maturity,
            action_items=action_items,
            scores=None,
            approved=None,
            approver_notes=None,
        )

    def _prioritize_plans(self, plans: List[Plan], diagnosis: Dict[str, Any]) -> List[Plan]:
        gap_map = {
            item.get("dimension"): item.get("gap_score", 0)
            for item in diagnosis.get("optimization_dimensions", [])
        }
        return sorted(plans, key=lambda p: gap_map.get(p.target_dimension, 0), reverse=True)

    def _extra_actions(self, dimension: str, context: Dict[str, Any], investigation: Dict[str, Any]) -> List[str]:
        goal_text = str(context.get("user_goals", ""))
        actions = []
        if "联系方式" in goal_text or "合作" in goal_text:
            actions.append("检查页面中合作入口和联系方式的显著性")
        if "React" in goal_text or "Vite" in json.dumps(context.get("tech_stack", {}), ensure_ascii=False):
            actions.append("结合当前 React/Vite 结构落地最小可执行改动")
        web_titles = [w.get("title", "") for w in investigation.get("web_findings", [])[:2] if w.get("title")]
        for title in web_titles:
            actions.append(f"参考外部案例《{title}》提炼可迁移做法")
        return actions

    def _effort_from_gap(self, gap_score: int) -> str:
        if gap_score >= 8:
            return "中高"
        if gap_score >= 5:
            return "中"
        return "低"

    def _debug_print(self, label: str, payload: Any) -> None:
        try:
            print(f"\n===== {label} =====")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        except Exception:
            print(f"\n===== {label} =====")
            print(str(payload))
