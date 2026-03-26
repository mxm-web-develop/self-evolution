"""
EvolutionAnalyzer — 从活跃项目出发的全流程分析入口

整合 onboarding 项目上下文 + OpenClaw orchestrator 全流程：
research → diagnose → plan（部分），形成最小闭环。

使用方法：
    from src.onboarding.evolution_analyzer import EvolutionAnalyzer

    analyzer = EvolutionAnalyzer(base_path="/path/to/self-evolution")
    result = analyzer.analyze_from_active_project(
        problem="用户上传图片慢，想优化性能",
        phases=["investigate", "diagnose"]  # 默认只跑这两步
    )
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 确保 core/adapter_openclaw 在路径
_ROOT = Path(__file__).resolve().parent.parent.parent
for p in [str(_ROOT / "core"), str(_ROOT / "adapter_openclaw"), str(_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def _get_search_provider():
    """初始化搜索 Provider，依次尝试 Tavily → DuckDuckGo。"""
    # 优先用 Tavily（需要 API key）
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    if tavily_key:
        try:
            from providers.tavily import TavilySearchProvider
            prov = TavilySearchProvider(api_key=tavily_key)
            if prov.health_check():
                return prov
        except Exception:
            pass

    # DuckDuckGo fallback（无需 key）
    try:
        from providers.duckduckgo import DuckDuckGoSearchProvider
        prov = DuckDuckGoSearchProvider()
        if prov.health_check():
            return prov
    except Exception:
        pass

    # 直接用无依赖的简单 provider
    return _FallbackSearchProvider()


class _FallbackSearchProvider:
    """完全离线的 fallback provider，永不失败。"""
    name = "fallback"
    requires_api_key = False

    def search(self, query, count=5):
        return []

    def fetch(self, url, max_chars=5000):
        return ""

    def health_check(self):
        return True


class EvolutionAnalyzer:
    """
    从活跃项目出发的全流程分析器。

    读取 onboarding 的项目索引，找到当前活跃项目，
    初始化 OpenClawBridge + ProjectEvolutionOrchestrator，
    执行 investigation + diagnosis（同步），返回格式化报告。
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.index_file = self.base_path / "projects" / "index.json"

    def get_active_project(self) -> Optional[Dict[str, Any]]:
        """读取当前活跃项目。"""
        import json
        if not self.index_file.exists():
            return None
        with open(self.index_file, encoding="utf-8") as f:
            data = json.load(f)
        active_id = data.get("active_project_id")
        for proj in data.get("projects", []):
            if proj.get("id") == active_id:
                return proj
        return None

    def analyze_from_active_project(
        self,
        problem: str,
        phases: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        从当前活跃项目出发，执行指定阶段。

        Args:
            problem: 用户描述的问题或优化目标
            phases: 要执行的阶段，默认 ["investigate", "diagnose"]
                   可选加 "plan"（需要方案生成，会返回多个候选方案）

        Returns:
            包含各阶段结果的 dict
        """
        if phases is None:
            phases = ["investigate", "diagnose"]

        active = self.get_active_project()
        if not active:
            return {
                "status": "error",
                "message": "当前没有活跃项目，请先说 /evolve 或「帮我新建项目」来指定一个项目。"
            }

        project_id = active["id"]
        project_name = active.get("name", project_id)

        # 初始化 Bridge + Orchestrator
        try:
            bridge = self._build_bridge()
            from adapter_openclaw.orchestrator import ProjectEvolutionOrchestrator
            orch = ProjectEvolutionOrchestrator(bridge)
        except Exception as exc:
            return {
                "status": "error",
                "message": f"初始化分析引擎失败：{exc}",
                "hint": "请确认已运行 bootstrap.sh 或安装 duckduckgo-search：pip install duckduckgo-search"
            }

        # 首次运行：建立项目状态（Phase=IDLE 会触发新流程）
        init_result = orch.run(project_id, problem, human_approved=False)
        results = {
            "project_id": project_id,
            "project_name": project_name,
            "problem": problem,
            "phases_completed": [],
            "investigation": None,
            "diagnosis": None,
            "plans": None,
            "status": "running"
        }

        # 执行 investigation 阶段
        if "investigate" in phases:
            # 设置 Phase 为 INVESTIGATING 并运行
            sm = bridge.get_state_manager()
            state = sm.load_state(project_id)
            if state:
                from core.models import Phase
                state.phase = Phase.INVESTIGATING
                sm.save_state(project_id, state)

            inv_result = orch.run(project_id, problem, human_approved=False)
            results["investigation"] = inv_result.get("report")
            results["phases_completed"].append("investigate")

            # 自动进入 diagnose
            if "diagnose" in phases:
                state = sm.load_state(project_id)
                if state:
                    from core.models import Phase
                    state.phase = Phase.DIAGNOSING
                    sm.save_state(project_id, state)

        if "diagnose" in phases:
            diag_result = orch.run(project_id, problem, human_approved=False)
            results["diagnosis"] = diag_result.get("diagnosis")
            results["phases_completed"].append("diagnose")

            # 自动进入 planning
            if "plan" in phases:
                state = sm.load_state(project_id)
                if state:
                    from core.models import Phase
                    state.phase = Phase.PLANNING
                    sm.save_state(project_id, state)

        if "plan" in phases:
            plan_result = orch.run(project_id, problem, human_approved=False)
            results["plans"] = plan_result.get("plan_ids")
            results["phases_completed"].append("plan")

        results["status"] = "completed"
        return results

    def format_report(self, results: Dict[str, Any]) -> str:
        """把分析结果格式化为人类可读的 Markdown 文本。"""
        if results.get("status") == "error":
            return f"❌ {results.get('message', '未知错误')}"

        project_name = results.get("project_name", "?")
        problem = results.get("problem", "")

        lines = [
            f"# 🔍 项目分析报告：{project_name}",
            f"\n**分析问题**：{problem}\n",
        ]

        # Investigation
        inv = results.get("investigation")
        if inv:
            lines.append("## 📋 调研结果\n")
            cases = inv.get("similar_cases", [])
            if cases:
                lines.append("**相似案例**：")
                for c in cases[:3]:
                    cat = c.get("category", "通用")
                    title = c.get("title", "")
                    score = c.get("score", 0)
                    lines.append(f"- 【{cat}】{title} (相似度 {score})")
                lines.append("")

            web = inv.get("web_findings", [])
            if web and not any("error" in str(w) for w in web):
                lines.append("**网络发现**：")
                for w in web[:3]:
                    title = w.get("title", "")
                    snippet = w.get("snippet", "")
                    lines.append(f"- {title}：{snippet[:80]}...")
                lines.append("")

            recs = inv.get("recommendations", [])
            if recs:
                lines.append("**初步建议**：")
                for r in recs[:4]:
                    lines.append(f"- {r}")
                lines.append("")

        # Diagnosis
        diag = results.get("diagnosis")
        if diag:
            lines.append("## 🩺 诊断结论\n")
            maturity = diag.get("maturity_assessment", {})
            confidence = diag.get("confidence", 0.0)
            lines.append(f"**项目成熟度**：{maturity.get('label', '未知')}（score={maturity.get('score', '?')}）")
            lines.append(f"**置信度**：{confidence:.0%}")
            lines.append("**优化维度列表**：")
            for item in diag.get("optimization_dimensions", [])[:5]:
                lines.append(f"- {item.get('dimension')}（差距 {item.get('gap_score', '?')}/10）")
            lines.append("")
            lines.append(f"**根因分析**：{diag.get('root_cause', '未知')}\n")

        # Plans
        plans = results.get("plans")
        if plans:
            lines.append("## 📐 候选方案\n")
            lines.append(f"已生成 {len(plans)} 个候选方案，保存在：")
            for pid in plans:
                lines.append(f"- 方案 ID：`{pid}`")
            lines.append("\n可用 `/evolve plan {id}` 查看详情，或回复「执行方案A」开始。\n")

        phases = results.get("phases_completed", [])
        lines.append("---")
        lines.append(f"✅ 已完成阶段：{' → '.join(phases) if phases else '无'}")

        if "diagnose" in phases and "plan" not in phases:
            lines.append("\n💡 **下一步**：回复「生成方案」或「帮我规划」，我将基于诊断结果生成多个候选方案。")

        return "\n".join(lines)

    def _build_bridge(self):
        """构建 OpenClawBridge，包含 search provider。"""
        from adapter_openclaw.bridge import OpenClawBridge

        projects_root = str(self.base_path / "projects")
        cases_root = str(self.base_path / "cases")
        provider = _get_search_provider()

        bridge = OpenClawBridge(
            projects_root=projects_root,
            cases_root=cases_root,
            search_provider=provider,
            default_channel="webchat"
        )
        return bridge
