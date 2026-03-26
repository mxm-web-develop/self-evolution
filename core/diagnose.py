"""动态诊断引擎：不枚举业务类型，直接基于调研报告和上下文推理差距维度。"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional, List


class DiagnoseEngine:
    def diagnose(
        self,
        investigation_report: Dict[str, Any],
        project_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        project_context = project_context or {}
        maturity = self._read_maturity_from_context(investigation_report, project_context)
        dims = self._infer_dims_from_findings(investigation_report, project_context)
        ranked_dims = self._rank_dims_by_gap(dims, maturity, project_context)
        root_cause = self._generate_root_cause(ranked_dims, maturity, investigation_report, project_context)
        diagnosis = {
            "optimization_dimensions": ranked_dims,
            "priority_dimensions": [d["dimension"] for d in ranked_dims],
            "root_cause": root_cause,
            "maturity_assessment": maturity,
            "confidence": self._estimate_confidence(investigation_report, ranked_dims),
            "summary": self._build_summary(ranked_dims, maturity),
        }
        self._debug_print("DIAGNOSIS", diagnosis)
        return diagnosis

    def _read_maturity_from_context(self, investigation_report: Dict[str, Any], project_context: Dict[str, Any]) -> Dict[str, Any]:
        return (
            investigation_report.get("maturity_assessment")
            or project_context.get("maturity_assessment")
            or {"stage": "unknown", "label": "未知", "score": 0, "reasoning": []}
        )

    def _infer_dims_from_findings(self, investigation_report: Dict[str, Any], project_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        dims = []
        for item in investigation_report.get("optimization_dimensions", []):
            dims.append({
                "dimension": item.get("dimension"),
                "evidence": item.get("evidence", []),
                "why_it_matters": item.get("why_it_matters", ""),
                "priority_hint": item.get("priority_hint", 5),
            })
        if not dims:
            dims.append({
                "dimension": "核心价值表达与体验基线",
                "evidence": ["调研结果不足"],
                "why_it_matters": "需要先补齐关键体验与成熟度基线。",
                "priority_hint": 6,
            })
        return dims

    def _rank_dims_by_gap(self, dims: List[Dict[str, Any]], maturity: Dict[str, Any], project_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        stage = maturity.get("stage", "unknown")
        stage_penalty = {"early": 2, "growing": 1, "mature": 0, "unknown": 1}.get(stage, 1)
        priorities = project_context.get("priorities", []) or []

        ranked = []
        for dim in dims:
            priority_boost = 0
            for p in priorities:
                dimension_text = str(p.get("dimension", "")).lower()
                if any(token in dimension_text for token in self._tokens(dim["dimension"])):
                    priority_boost += max(1, int(float(p.get("weight", 0.3)) * 10))
            gap_score = min(10, dim.get("priority_hint", 5) + priority_boost + stage_penalty)
            ranked.append({
                "dimension": dim["dimension"],
                "gap_score": gap_score,
                "priority": "high" if gap_score >= 8 else ("medium" if gap_score >= 5 else "low"),
                "current_state": self._infer_current_state(dim, project_context, maturity),
                "mature_standard": self._infer_mature_standard(dim, maturity),
                "evidence": dim.get("evidence", []),
                "why_it_matters": dim.get("why_it_matters", ""),
                "recommended_actions": self._recommend_actions(dim),
            })
        ranked.sort(key=lambda x: x["gap_score"], reverse=True)
        return ranked

    def _generate_root_cause(
        self,
        ranked_dims: List[Dict[str, Any]],
        maturity: Dict[str, Any],
        investigation_report: Dict[str, Any],
        project_context: Dict[str, Any],
    ) -> str:
        top = ranked_dims[:3]
        if not top:
            return "当前信息不足，无法形成稳定根因判断。"
        lines = [
            f"项目当前处于{maturity.get('label', '未知')}阶段，核心问题不是单点 bug，而是成熟度基线与目标期望之间仍有缺口。",
        ]
        for item in top:
            lines.append(
                f"- 维度「{item['dimension']}」的主要差距在于：当前更偏向{item['current_state']}，但成熟项目通常会做到{item['mature_standard']}。"
            )
        history = (project_context.get("analysis_history", "") or "").strip()
        if history:
            lines.append("- 历史记录显示项目已经有过分析/方案沉淀，因此本轮应避免重复泛化建议，优先补最大缺口。")
        return "\n".join(lines)

    def _estimate_confidence(self, investigation_report: Dict[str, Any], ranked_dims: List[Dict[str, Any]]) -> float:
        signals = 0
        if investigation_report.get("scanned_code", {}).get("exists"):
            signals += 1
        if investigation_report.get("web_findings"):
            signals += 1
        if investigation_report.get("similar_cases"):
            signals += 1
        if ranked_dims:
            signals += 1
        return min(0.95, 0.45 + signals * 0.12)

    def _build_summary(self, ranked_dims: List[Dict[str, Any]], maturity: Dict[str, Any]) -> str:
        dims = "、".join(d["dimension"] for d in ranked_dims[:3]) or "暂无"
        return f"当前项目处于{maturity.get('label', '未知')}阶段，优先补齐：{dims}。"

    def _infer_current_state(self, dim: Dict[str, Any], project_context: Dict[str, Any], maturity: Dict[str, Any]) -> str:
        evidence = ", ".join(dim.get("evidence", [])[:3]) or "上下文有限"
        return f"局部已有想法，但仍以碎片化信号为主（证据：{evidence}；阶段：{maturity.get('label', '未知')}）"

    def _infer_mature_standard(self, dim: Dict[str, Any], maturity: Dict[str, Any]) -> str:
        mapping = {
            "品牌表达与定位清晰度": "用户进入后能迅速理解价值主张、代表作品和合作入口",
            "视觉系统与一致性": "有统一的视觉语言、组件规则和品牌辨识度",
            "交互反馈与浏览流畅度": "关键交互有明确反馈，浏览节奏自然且性能稳定",
            "内容结构与转化路径": "信息层级清楚，内容可信，CTA 和联系方式自然收口",
            "性能与加载质量": "首屏、图片、字体、脚本等核心资源都经过优化",
            "SEO与可发现性": "技术 SEO、语义内容与分享展示都有基础闭环",
            "工程可维护性": "结构清楚、扩展成本低、后续改版不容易失控",
        }
        return mapping.get(dim["dimension"], "在该维度上具备稳定、可复用、可持续优化的成熟做法")

    def _recommend_actions(self, dim: Dict[str, Any]) -> List[str]:
        mapping = {
            "品牌表达与定位清晰度": ["重写首屏价值主张", "明确代表作和能力标签", "补齐合作/联系入口"],
            "视觉系统与一致性": ["建立统一配色与字体层级", "统一插画/吉祥物风格", "收敛组件样式差异"],
            "交互反馈与浏览流畅度": ["梳理关键滚动与 hover 反馈", "减少无意义动画", "保证动效服务信息层级"],
            "内容结构与转化路径": ["重排页面模块顺序", "精简文案冗余", "强化 CTA 和联系路径"],
            "性能与加载质量": ["分析构建产物", "懒加载图片/模块", "优化字体与资源体积"],
            "SEO与可发现性": ["补 meta/OG/schema", "检查语义化标题结构", "增加 sitemap / 分享展示"],
            "工程可维护性": ["梳理组件边界", "沉淀设计 token", "约束后续页面扩展方式"],
        }
        return mapping.get(dim["dimension"], ["补充上下文后细化行动项"])

    def _tokens(self, text: str) -> List[str]:
        return [t for t in text.lower().replace("与", " ").replace("/", " ").split() if t]

    def _debug_print(self, label: str, payload: Any) -> None:
        try:
            print(f"\n===== {label} =====")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        except Exception:
            print(f"\n===== {label} =====")
            print(str(payload))
