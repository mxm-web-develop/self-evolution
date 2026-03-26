"""
/evolve 对话式入口（v2 - Semantic Router）

核心流程：
1. build route context
2. rule fast-path / semantic fallback
3. risk gate (confirmation)
4. dispatch
5. 若无全局意图则继续 onboarding step
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any

from .router import OnboardingRouter
from .semantic_router import SemanticRouter
from .route_models import RouteContext, Route, RouteAction, DecisionMode

RUNTIME_STATE_FILE = "runtime/evolve-chat-state.json"


@dataclass
class ChatState:
    active: bool = False
    mode: Optional[str] = None  # new | existing
    step: str = "idle"
    project_path: Optional[str] = None
    goal: Optional[str] = None
    name: Optional[str] = None
    benchmarks: List[str] = None
    priorities: List[Dict[str, Any]] = None
    automation_boundaries: List[str] = None
    pending_confirmation: bool = False
    pending_action: Optional[str] = None
    pending_entities: Dict[str, Any] = None

    def __post_init__(self):
        self.benchmarks = self.benchmarks or []
        self.priorities = self.priorities or []
        self.automation_boundaries = self.automation_boundaries or []
        self.pending_entities = self.pending_entities or {}

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ChatState":
        return cls(**data)


class EvolveChatFlow:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.router = OnboardingRouter(str(self.base_path))
        self.semantic_router = SemanticRouter()
        self.state_file = self.base_path / RUNTIME_STATE_FILE
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> ChatState:
        if not self.state_file.exists():
            return ChatState()
        with open(self.state_file, "r", encoding="utf-8") as f:
            return ChatState.from_dict(json.load(f))

    def _save_state(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)

    def _reset_state(self) -> None:
        self.state = ChatState()
        self._save_state()

    def _clear_confirmation(self) -> None:
        self.state.pending_confirmation = False
        self.state.pending_action = None
        self.state.pending_entities = {}
        self._save_state()

    def _build_route_context(self, user_input: str) -> RouteContext:
        active = self.router.get_active_project()
        pending_plan_id = None
        pending_approval = False
        if active:
            try:
                from core.models import Phase
                from .evolution_analyzer import EvolutionAnalyzer
                analyzer = EvolutionAnalyzer(str(self.base_path))
                bridge = analyzer._build_bridge()
                sm = bridge.get_state_manager()
                project_state = sm.load_state(active["id"])
                if project_state and project_state.phase == Phase.APPROVING:
                    pending_approval = True
                    pending_plan_id = project_state.context.get("selected_plan_id")
            except Exception:
                pass

        return RouteContext(
            user_input=user_input,
            active_project=active,
            onboarding_active=self.state.active,
            onboarding_step=self.state.step if self.state.active else None,
            pending_approval=pending_approval,
            pending_approval_plan_id=pending_plan_id,
        )

    def handle(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return self._help()

        context = self._build_route_context(text)

        if self.state.pending_confirmation:
            return self._handle_confirmation_response(text, context)

        route = self.semantic_router.route(text, context)

        if route.action == RouteAction.UNKNOWN:
            if self.state.active:
                return self._continue_flow(text)
            return self._help()

        return self._dispatch_route(route, context)

    def _handle_confirmation_response(self, text: str, context: RouteContext) -> str:
        if self.semantic_router.is_confirmation_response(text):
            action = self.state.pending_action or RouteAction.UNKNOWN.value
            entities = self.state.pending_entities or {}
            self._clear_confirmation()
            route = Route(
                action=RouteAction(action),
                confidence=0.99,
                source="confirmation",
                decision_mode=DecisionMode.AUTO,
                entities=entities,
                original_text=text,
                metadata={"confirmed": True},
            )
            return self._dispatch_route(route, context)

        if self.semantic_router.is_cancellation_response(text):
            self._clear_confirmation()
            return "✅ 已取消操作。"

        return "⚠️ 这是一个待确认操作。回复「确认」继续，或回复「取消」放弃。"

    def _dispatch_route(self, route: Route, context: RouteContext) -> str:
        if route.decision_mode == DecisionMode.CONFIRM_REQUIRED and not route.is_confirmed_action():
            self.state.pending_confirmation = True
            self.state.pending_action = route.action.value
            self.state.pending_entities = route.entities or {}
            self._save_state()
            return route.clarification_question or "⚠️ 请先确认后继续。"

        if route.action in {RouteAction.STATUS, RouteAction.ACTIVE_PROJECT, RouteAction.CANCEL, RouteAction.SWITCH_PROJECT}:
            return self._handle_global_action(route)

        handlers = {
            RouteAction.NEW_PROJECT: self._route_new_project,
            RouteAction.EXISTING_PROJECT: self._route_existing_project,
            RouteAction.ANALYZE: self._route_analyze,
            RouteAction.DIAGNOSE: self._route_analyze,
            RouteAction.PLAN: self._route_plan,
            RouteAction.VIEW_PLAN: self._route_view_plan,
            RouteAction.APPROVE: self._route_execute,
            RouteAction.EXECUTE: self._route_execute,
            RouteAction.REJECT: self._route_execute,
            RouteAction.REVISE: self._route_execute,
            RouteAction.HELP: lambda _r: self._help(),
            RouteAction.CLARIFICATION_NEEDED: lambda r: r.clarification_question or self._help(),
        }
        handler = handlers.get(route.action)
        if handler:
            return handler(route)

        if self.state.active:
            return self._continue_flow(route.original_text)
        return self._help()

    def _handle_global_action(self, route: Route) -> str:
        if route.action == RouteAction.STATUS:
            return self.router._format_project_list()
        if route.action == RouteAction.ACTIVE_PROJECT:
            active = self.router.get_active_project()
            if not active:
                return "当前没有活跃项目。可以先输入 /evolve 开始。"
            return (
                f"👉 当前活跃项目：{active['name']}\n"
                f"ID：{active['id']}\n"
                f"类型：{active.get('type', '?')}\n"
                f"路径：{active.get('path', '?')}"
            )
        if route.action == RouteAction.CANCEL:
            self._reset_state()
            return "🛑 已取消当前 /evolve 流程。"
        if route.action == RouteAction.SWITCH_PROJECT:
            project_id = (route.entities or {}).get("project_id")
            if not project_id:
                return "请告诉我要切换到哪个项目。"
            try:
                proj = self.router.switch_project(project_id)
                return f"✅ 已切换到项目：{proj['name']} [{proj['id']}]"
            except Exception as exc:
                return f"❌ 切换失败：{exc}"
        return self._help()

    def _route_new_project(self, route: Route) -> str:
        goal = (route.entities or {}).get("goal")
        self.state = ChatState(active=True, mode="new", step="gather_name", goal=goal or None)
        self._save_state()
        if goal:
            return f"收到，新项目目标先记为：{goal}\n\n请再告诉我这个项目叫什么名字？"
        return "好的，我们从 0 开始。先告诉我：这个项目想做什么？一句话就行。"

    def _route_existing_project(self, route: Route) -> str:
        project_path = (route.entities or {}).get("path") or (route.entities or {}).get("project_path")
        if not project_path:
            self.state = ChatState(active=True, mode="existing", step="existing_path")
            self._save_state()
            return "好的，这是已有项目。请把项目路径发给我。"
        session, scan = self.router.init_existing_project(project_path)
        self._reset_state()
        return self._format_existing_result(session, scan)

    def _route_analyze(self, route: Route) -> str:
        problem = (route.entities or {}).get("problem") or route.original_text
        return self._handle_analyze(problem, original_text=route.original_text)

    def _route_plan(self, route: Route) -> str:
        plan_id = (route.entities or {}).get("plan_id")
        if plan_id and plan_id.startswith("plan-"):
            return self._view_plan(plan_id)
        return self._handle_plan(original_text=route.original_text)

    def _route_view_plan(self, route: Route) -> str:
        plan_id = (route.entities or {}).get("plan_id")
        if not plan_id:
            return "请告诉我要查看哪个方案。"
        return self._view_plan(plan_id)

    def _route_execute(self, route: Route) -> str:
        class ParsedLike:
            analyze_problem = None
            command = None
        parsed = ParsedLike()
        entities = route.entities or {}
        plan_id = entities.get("plan_id")
        if plan_id in {"plan-a", "plan-b", "plan-c"}:
            parsed.analyze_problem = self._resolve_plan_label(plan_id.split("-", 1)[1].upper())
        else:
            parsed.analyze_problem = plan_id or self._resolve_plan_label(entities.get("plan_label"))
        parsed.command = f"{route.action.value}:confirmed" if route.is_confirmed_action() else route.action.value
        return self._handle_execute(parsed, original_text=route.original_text)

    def _continue_flow(self, text: str) -> str:
        if self.state.step == "context_check":
            candidate = Path(text).expanduser()
            if candidate.exists() and candidate.is_dir():
                self.state.mode = "existing"
                self.state.project_path = str(candidate.resolve())
                session, scan = self.router.init_existing_project(self.state.project_path)
                self._reset_state()
                return self._format_existing_result(session, scan)

            if any(k in text for k in ["已有", "existing", "现有"]):
                self.state.mode = "existing"
                self.state.step = "existing_path"
                self._save_state()
                return "好的，这是已有项目。请把项目路径发给我。"

            self.state.mode = "new"
            self.state.step = "gather_goal"
            self._save_state()
            return "好的，我们按新项目来。先告诉我：这个项目想做什么？一句话描述目标即可。"

        if self.state.mode == "existing" and self.state.step == "existing_path":
            candidate = Path(text).expanduser()
            if not candidate.exists() or not candidate.is_dir():
                return "这个路径看起来不存在，麻烦再发一次项目目录路径。"
            self.state.project_path = str(candidate.resolve())
            session, scan = self.router.init_existing_project(self.state.project_path)
            self._reset_state()
            return self._format_existing_result(session, scan)

        if self.state.mode == "new" and self.state.step == "gather_goal":
            self.state.goal = text
            self.state.step = "gather_name"
            self._save_state()
            return "收到。那这个项目叫什么名字？如果没想好，我也可以先帮你起一个临时名。"

        if self.state.mode == "new" and self.state.step == "gather_name":
            self.state.name = text
            self.state.step = "gather_benchmarks"
            self._save_state()
            return "有没有你对标的产品或竞品？多个可以用逗号分隔；如果没有就回复“跳过”。"

        if self.state.mode == "new" and self.state.step == "gather_benchmarks":
            if text not in {"跳过", "skip", "无", "没有"}:
                self.state.benchmarks = [x.strip() for x in text.split(",") if x.strip()]
            self.state.step = "gather_priorities"
            self._save_state()
            return (
                "你当前最优先优化哪些方向？\n"
                "可以直接回复，例如：业务, 交互, 功能\n"
                "也可以写成：business:0.5, ux:0.2, feature:0.3"
            )

        if self.state.mode == "new" and self.state.step == "gather_priorities":
            self.state.priorities = self._parse_priorities(text)
            self.state.step = "gather_boundaries"
            self._save_state()
            return (
                "最后一个问题：有哪些事情你不希望全自动处理？\n"
                "例如：费用审批、对外发布、密钥配置、依赖升级。\n"
                "多个可用逗号分隔；如果没有就回复“跳过”。"
            )

        if self.state.mode == "new" and self.state.step == "gather_boundaries":
            if text not in {"跳过", "skip", "无", "没有"}:
                self.state.automation_boundaries = [x.strip() for x in text.split(",") if x.strip()]
            session = self.router.init_new_project(
                goal=self.state.goal or "",
                name=self.state.name or "new-project",
                benchmarks=self.state.benchmarks,
                priorities=self.state.priorities,
                automation_boundaries=self.state.automation_boundaries,
            )
            project = self.router.get_project(session.project_id)
            self._reset_state()
            return self._format_new_result(session.project_id, project)

        return self._help()

    def _handle_analyze(self, problem: str, original_text: str = "") -> str:
        from .evolution_analyzer import EvolutionAnalyzer

        analyzer = EvolutionAnalyzer(str(self.base_path))
        active = analyzer.get_active_project()
        if not active:
            return (
                "🔍 我需要知道你要分析哪个项目，但现在还没有活跃项目。\n"
                "请先说「帮我新建项目」或「接入已有项目」。"
            )

        final_problem = problem or original_text
        if not final_problem or len(final_problem) < 3:
            return (
                f"🔍 好，要分析项目「{active.get('name', active['id'])}」。\n\n"
                "请告诉我你想分析什么问题或优化方向？"
            )

        results = analyzer.analyze_from_active_project(problem=final_problem, phases=["investigate", "diagnose"])
        return analyzer.format_report(results)

    def _handle_plan(self, original_text: str = "") -> str:
        from .evolution_analyzer import EvolutionAnalyzer

        analyzer = EvolutionAnalyzer(str(self.base_path))
        active = analyzer.get_active_project()
        if not active:
            return (
                "📐 我需要知道要给哪个项目生成方案，但现在还没有活跃项目。\n"
                "请先说「帮我新建项目」或「接入已有项目」。"
            )

        project_id = active["id"]
        project_name = active.get("name", project_id)
        problem = None
        if original_text and len(original_text) >= 3:
            extracted = self.semantic_router.intent_parser._extract_plan_problem(original_text)
            if extracted and len(extracted) >= 3:
                problem = extracted

        if not problem:
            health_report = self.base_path / "projects" / project_id / "health-report.md"
            inv_report = self.base_path / "projects" / project_id / "investigation.md"
            if not health_report.exists() and not inv_report.exists():
                return (
                    f"📐 好，要为项目「{project_name}」生成方案。\n\n"
                    "我目前还没有这个项目的诊断数据。\n"
                    "请先说「帮我分析这个项目」或「诊断一下」。"
                )
            problem = "基于已有诊断结果，生成优化方案"

        results = analyzer.analyze_from_active_project(problem=problem, phases=["investigate", "diagnose", "plan"])
        return self._format_plan_results(results, project_name)

    def _handle_execute(self, parsed, original_text: str = "") -> str:
        from core.models import Phase
        from .evolution_analyzer import EvolutionAnalyzer
        from adapter_openclaw.orchestrator import ProjectEvolutionOrchestrator

        plan_id = getattr(parsed, "analyze_problem", None)
        analyzer = EvolutionAnalyzer(str(self.base_path))
        active = analyzer.get_active_project()
        if not active:
            return "❌ 当前没有活跃项目。"

        project_id = active["id"]
        bridge = analyzer._build_bridge()
        sm = bridge.get_state_manager()
        state = sm.load_state(project_id)

        if state and state.phase == Phase.APPROVING:
            selected_plan_id = state.context.get("selected_plan_id")
            decision_text = (original_text or getattr(parsed, 'command', '') or '').lower()
            if any(k in decision_text for k in ["reject", "拒绝", "否决"]):
                state.phase = Phase.IDLE
                state.add_history("approval_rejected", f"方案 {selected_plan_id or plan_id or 'unknown'} 被拒绝")
                sm.save_state(project_id, state)
                return "❌ 已拒绝当前方案。你可以重新说“生成方案”或补充新的约束。"
            if any(k in decision_text for k in ["revise", "修改", "调整"]):
                state.phase = Phase.IDLE
                state.add_history("approval_revise", f"方案 {selected_plan_id or plan_id or 'unknown'} 需要修改")
                sm.save_state(project_id, state)
                return "🔄 已记录为需要修改。请告诉我你希望怎么调整方案。"

            plan_id = selected_plan_id or plan_id
            if not plan_id:
                return "❌ 当前没有待审批的方案。"
            chosen = self._load_plan_as_dict(project_id, plan_id)
            if not chosen:
                return f"❌ 找不到待执行方案 `{plan_id}`。"

            state.context["scored_plans"] = [chosen]
            state.context["selected_plan_id"] = plan_id
            state.phase = Phase.EXECUTING
            state.add_history("approval_approved", f"方案 {plan_id} 已批准，开始执行")
            sm.save_state(project_id, state)

            orch = ProjectEvolutionOrchestrator(bridge)
            exec_result = orch.run(project_id, state.current_task or state.context.get("original_problem", ""), human_approved=True)
            learn_result = orch.run(project_id, state.current_task or state.context.get("original_problem", ""), human_approved=True)

            summary = exec_result.get("result", {}).get("summary", "执行已触发")
            case_id = learn_result.get("case_id")
            learn_line = f"\n- 学习回写：`{case_id}`" if case_id else "\n- 学习回写：已完成（未生成案例 ID）"
            return (
                f"# 🚀 方案开始执行\n\n"
                f"**方案**：`{plan_id}`\n"
                f"- 执行结果：{summary}"
                f"{learn_line}\n\n"
                f"当前版本会优先生成可追踪的执行任务卡；如果任务本身带命令，则会直接执行。"
            )

        if not plan_id:
            plans_dir = self.base_path / "projects" / project_id / "plans"
            if plans_dir.exists():
                existing = sorted(plans_dir.glob("plan-*.md"))
                if existing:
                    plan_id = existing[-1].stem
        if not plan_id:
            return "❌ 没有找到可执行的方案。请先说「生成方案」或「帮我规划」。"

        plan_file = self.base_path / "projects" / project_id / "plans" / f"{plan_id}.md"
        if not plan_file.exists():
            return f"❌ 找不到方案 `{plan_id}`。"

        plan_content = plan_file.read_text(encoding="utf-8")
        title = plan_content.split("\n", 1)[0].lstrip("#").strip()

        if "execute:confirmed" in (getattr(parsed, 'command', '') or ''):
            if state:
                chosen = self._load_plan_as_dict(project_id, plan_id)
                if not chosen:
                    return f"❌ 找不到待执行方案 `{plan_id}`。"
                state.context["scored_plans"] = [chosen]
                state.context["selected_plan_id"] = plan_id
                state.phase = Phase.EXECUTING
                state.add_history("execute_confirmed", f"方案 {plan_id} 已确认执行")
                sm.save_state(project_id, state)
            orch = ProjectEvolutionOrchestrator(bridge)
            exec_result = orch.run(project_id, state.current_task or state.context.get("original_problem", ""), human_approved=True)
            learn_result = orch.run(project_id, state.current_task or state.context.get("original_problem", ""), human_approved=True)
            summary = exec_result.get("result", {}).get("summary", "执行已触发")
            case_id = learn_result.get("case_id")
            learn_line = f"\n- 学习回写：`{case_id}`" if case_id else "\n- 学习回写：已完成（未生成案例 ID）"
            return (
                f"# 🚀 方案开始执行\n\n"
                f"**方案**：`{plan_id}`\n"
                f"**标题**：{title}\n"
                f"- 执行结果：{summary}"
                f"{learn_line}\n\n"
                f"当前版本会优先生成可追踪的执行任务卡；如果任务本身带命令，则会直接执行。"
            )

        if state:
            state.phase = Phase.APPROVING
            state.context["selected_plan_id"] = plan_id
            state.add_history("approval_requested", f"方案 {plan_id} 请求审批")
            sm.save_state(project_id, state)

        return (
            f"# ✅ 审批请求已提交\n\n"
            f"**方案**：`{plan_id}`\n"
            f"**标题**：{title}\n\n"
            f"请确认后回复：\n"
            f"- `确认` → 开始执行\n"
            f"- `取消` → 放弃此方案\n\n"
            f"⚠️ 当前版本的执行阶段会优先生成执行任务卡，便于继续落地。"
        )

    def _format_plan_results(self, results: Dict[str, Any], project_name: str) -> str:
        if results.get("status") == "error":
            return f"❌ {results.get('message', '未知错误')}"
        phases = results.get("phases_completed", [])
        if "diagnose" not in phases:
            return (
                f"📐 我目前还没有「{project_name}」的诊断数据。\n\n"
                "请先说「帮我分析这个项目」或「诊断一下」。"
            )

        lines = [f"# 📐 方案生成报告：{project_name}", ""]
        diag = results.get("diagnosis")
        if diag:
            dtype_labels = {
                "visual_design": "🎨 视觉/美观优化",
                "ux_interaction": "⚡ 交互体验优化",
                "performance": "🚀 性能优化",
                "feature_request": "🆕 功能需求",
                "bug_fix": "🐛 缺陷修复",
                "architecture": "🏗️ 架构调整",
                "content": "📝 内容/文案优化",
                "seo_discoverability": "🔍 SEO/可发现性",
                "unknown": "❓ 待确认",
            }
            lines.append(f"**诊断类型**：{dtype_labels.get(diag.get('type', 'unknown'), diag.get('type', 'unknown'))}")
            lines.append(f"**优先级**：{diag.get('priority', '?')}/10")
            lines.append(f"**根因**：{diag.get('root_cause', '未知')}")
            lines.append("")

        plans = results.get("plans")
        if plans:
            lines.append("## 📋 候选方案\n")
            lines.append(f"已生成 **{len(plans)}** 个候选方案：\n")
            plans_dir = self.base_path / "projects" / results.get("project_id", "") / "plans"
            for i, plan_id in enumerate(plans, 1):
                plan_file = plans_dir / f"{plan_id}.md"
                label = chr(ord('A') + i - 1)
                if plan_file.exists():
                    content = plan_file.read_text(encoding="utf-8")
                    title = content.split("\n", 1)[0].lstrip("#").strip()
                    est_match = content.split("**投入级别**：", 1)
                    est = ""
                    if len(est_match) > 1:
                        est_line = est_match[1].split("\n", 1)[0].strip()
                        est = f"（投入：{est_line}）"
                    lines.append(f"**方案 {label}**：{title} {est}")
                else:
                    lines.append(f"**方案 {label}**：{plan_id}")
                lines.append(f"  可用 `/evolve plan {plan_id}` 查看详情\n")
            lines.append("")
            lines.append("💡 回复「执行方案A」「批准方案B」或「/evolve approve <id>」开始审批。")
        else:
            lines.append("⚠️ 方案生成未返回结果，请确认项目已有调研和诊断数据。")

        lines.append("")
        lines.append("---")
        lines.append(f"✅ 已完成阶段：{' → '.join(phases)}")
        return "\n".join(lines)

    def _view_plan(self, plan_id: str) -> str:
        active = self.router.get_active_project()
        if not active:
            return "❌ 当前没有活跃项目。"
        project_id = active["id"]
        plan_file = self.base_path / "projects" / project_id / "plans" / f"{plan_id}.md"
        if not plan_file.exists():
            return f"❌ 找不到方案 `{plan_id}`，可能尚未生成或已被清理。"
        content = plan_file.read_text(encoding="utf-8")
        return f"# 📄 方案详情：{plan_id}\n\n{content}\n\n💡 回复「批准 {plan_id}」或「执行 {plan_id}」开始审批流程。"

    def _resolve_plan_label(self, plan_label: Optional[str]) -> Optional[str]:
        if not plan_label:
            return None
        active = self.router.get_active_project()
        if not active:
            return None
        plans_dir = self.base_path / "projects" / active["id"] / "plans"
        if not plans_dir.exists():
            return None
        files = sorted(plans_dir.glob("plan-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if len(files) < 3:
            files = sorted(plans_dir.glob("plan-*.md"))
        mapping = {"A": 0, "B": 1, "C": 2}
        idx = mapping.get(str(plan_label).upper())
        if idx is None or idx >= len(files):
            return None
        return files[idx].stem

    def _load_plan_as_dict(self, project_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        plan_file = self.base_path / "projects" / project_id / "plans" / f"{plan_id}.md"
        if not plan_file.exists():
            return None
        content = plan_file.read_text(encoding="utf-8")
        title = content.split("\n", 1)[0].lstrip("#").replace("方案：", "").strip()

        def section_list(name: str) -> List[str]:
            marker = f"## {name}\n"
            if marker not in content:
                return []
            tail = content.split(marker, 1)[1]
            next_idx = tail.find("\n## ")
            body = tail[:next_idx] if next_idx >= 0 else tail
            return [line[2:].strip() for line in body.splitlines() if line.startswith("- ")]

        def section_text(name: str) -> str:
            marker = f"## {name}\n"
            if marker not in content:
                return ""
            tail = content.split(marker, 1)[1]
            next_idx = tail.find("\n## ")
            body = tail[:next_idx] if next_idx >= 0 else tail
            return body.strip()

        def field_value(label: str) -> str:
            marker = f"**{label}**："
            if marker not in content:
                return ""
            return content.split(marker, 1)[1].split("\n", 1)[0].strip()

        return {
            "plan_id": plan_id,
            "project_id": project_id,
            "title": title or plan_id,
            "description": section_text("描述"),
            "pros": section_list("优势"),
            "cons": section_list("劣势"),
            "resource_estimate": {
                "effort": field_value("投入级别") or "中",
                "scope": field_value("影响范围") or "核心链路",
                "automation": field_value("自动化适配") or "高",
                "execution_style": field_value("执行方式") or "先关键后扩展",
            },
            "risks": section_list("风险"),
            "expected_outcomes": section_list("预期结果"),
            "scores": {"final": 0.0, "recommendation": "用户手动选中"},
        }

    def _parse_priorities(self, text: str) -> List[Dict[str, Any]]:
        text = text.strip()
        if not text:
            return []
        items = []
        if ":" in text:
            for part in text.split(","):
                part = part.strip()
                if not part:
                    continue
                dim, *rest = [x.strip() for x in part.split(":")]
                weight = 0.5
                if rest:
                    try:
                        weight = float(rest[0])
                    except Exception:
                        weight = 0.5
                items.append({"dimension": dim, "weight": weight, "reason": ""})
            return items
        for dim in [x.strip() for x in text.split(",") if x.strip()]:
            items.append({"dimension": dim, "weight": 0.5, "reason": ""})
        return items

    def _format_existing_result(self, session, scan: Dict[str, Any]) -> str:
        langs = ", ".join(scan.get("tech_stack", {}).get("languages", [])) or "未知"
        frameworks = ", ".join(scan.get("tech_stack", {}).get("frameworks", [])) or "未知"
        return (
            f"✅ 已完成已有项目接入\n\n"
            f"项目名：{session.name}\n"
            f"项目ID：{session.project_id}\n"
            f"技术栈：{langs}\n"
            f"框架：{frameworks}\n"
            f"目录：{scan.get('project_path', '?')}\n\n"
            f"后续你可以直接说：帮我分析当前项目 / 帮我生成方案"
        )

    def _format_new_result(self, project_id: str, project: Optional[dict]) -> str:
        return (
            f"✅ 已完成新项目初始化\n\n"
            f"项目名：{project.get('name', project_id) if project else project_id}\n"
            f"项目ID：{project_id}\n"
            f"目标：{project.get('description', self.state.goal or '') if project else (self.state.goal or '')}\n\n"
            f"后续你可以直接说：帮我分析当前项目 / 帮我生成方案"
        )

    def _help(self) -> str:
        return (
            "你可以这样用 self-evolution：\n"
            "- /evolve\n"
            "- 帮我新建一个项目：AI 图片工作流平台\n"
            "- 接入项目 /Users/xxx/my-repo\n"
            "- 看看我有哪些项目\n"
            "- 当前活跃项目是哪个\n"
            "- 切换到 pixgen\n"
            "- 帮我分析当前项目\n"
            "- 帮我生成方案"
        )
