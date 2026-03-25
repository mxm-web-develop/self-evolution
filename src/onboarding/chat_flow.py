"""
/evolve 对话式入口（MVP）

目标：
- 让用户通过自然对话/简单命令触发 onboarding
- 用一个轻量持久化状态文件维护当前 onboarding 进度
- 支持：项目列表 / 活跃项目 / 切换项目 / 新项目引导 / 已有项目接入
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any

from .router import OnboardingRouter
from .intent_parser import EvolveIntentParser, ParsedIntent


RUNTIME_DIR = "runtime"
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

    def __post_init__(self):
        self.benchmarks = self.benchmarks or []
        self.priorities = self.priorities or []
        self.automation_boundaries = self.automation_boundaries or []

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ChatState":
        return cls(**data)


class EvolveChatFlow:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.router = OnboardingRouter(str(self.base_path))
        self.parser = EvolveIntentParser()
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

    def handle(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return self._help()

        # 先做意图解析（避免 normalize 后丢失自然语言信息）
        parsed = self.parser.parse(text)

        # 允许用户直接中断
        cancel_phrases = {"取消", "退出", "/evolve cancel", "/evolve stop", "stop", "cancel"}
        if any(c in text for c in cancel_phrases):
            self._reset_state()
            return "🛑 已取消当前 /evolve 流程。你可以随时重新输入 /evolve 开始。"

        # 意图触发的处理（优先于 normalize 路径，避免自然语言被覆盖）
        if parsed and parsed.kind == "analyze":
            return self._handle_analyze(parsed.analyze_problem or "", original_text=text)
        if parsed and parsed.kind == "plan":
            return self._handle_plan(original_text=text)
        if parsed and parsed.kind == "execute":
            return self._handle_execute(parsed, original_text=text)

        # 显式命令路径（/evolve xxx）
        normalized = self.parser.normalize(text)
        effective_text = normalized or text
        if effective_text.startswith("/evolve"):
            return self._handle_command(effective_text, original_text=text)

        # 如果没有 pending state，就把普通文本当作帮助/提示
        if not self.state.active:
            return (
                "我这边没有进行中的 /evolve 对话。\n"
                "你可以试试：\n"
                "- /evolve\n"
                "- /evolve status\n"
                "- /evolve switch <project-id>\n"
                "- /evolve /Users/xxx/your-project\n"
                "- 或直接说：帮我新建项目 / 看看项目列表 / 切换到 pixgen"
            )

        # 有进行中的多轮对话时，优先把普通文本当作当前步骤输入
        return self._continue_flow(text)

    def _handle_analyze(self, problem: str, original_text: str = "") -> str:
        """
        从当前活跃项目出发，执行调研+诊断最小闭环。

        Args:
            problem: 从命令参数提取的问题描述
            original_text: 原始用户输入（用于从自然语言中提取问题）
        """
        # 延迟导入避免循环
        from .evolution_analyzer import EvolutionAnalyzer

        base = str(self.base_path)
        analyzer = EvolutionAnalyzer(base)

        active = analyzer.get_active_project()
        if not active:
            return (
                "🔍 我需要知道你要分析哪个项目，但现在还没有活跃项目。\n"
                "请先说「帮我新建项目」或「接入已有项目」。"
            )

        project_name = active.get("name", active["id"])

        # 如果 problem 为空，尝试从原始文本提取
        final_problem = problem
        if not final_problem or len(final_problem) < 3:
            if original_text:
                extracted = self.parser._extract_analyze_problem(original_text)
                if extracted and len(extracted) >= 3:
                    final_problem = extracted
        if not final_problem or len(final_problem) < 3:
            return (
                f"🔍 好，要分析项目「{project_name}」。\n\n"
                "请告诉我你想分析什么问题或优化方向？\n"
                "比如：\n"
                "- 帮我分析这个项目的性能瓶颈\n"
                "- 用户体验有哪些可以优化的地方\n"
                "- 帮我看看这个项目适合做什么功能"
            )

        # 执行调研+诊断
        results = analyzer.analyze_from_active_project(
            problem=final_problem,
            phases=["investigate", "diagnose"]
        )

        return analyzer.format_report(results)

    def _handle_plan(self, original_text: str = "") -> str:
        """
        从当前活跃项目出发，基于已有诊断生成方案。
        """
        from .evolution_analyzer import EvolutionAnalyzer

        base = str(self.base_path)
        analyzer = EvolutionAnalyzer(base)

        active = analyzer.get_active_project()
        if not active:
            return (
                "📐 我需要知道要给哪个项目生成方案，但现在还没有活跃项目。\n"
                "请先说「帮我新建项目」或「接入已有项目」。"
            )

        project_id = active["id"]
        project_name = active.get("name", project_id)

        # 尝试从原始文本提取问题描述
        problem = None
        if original_text and len(original_text) >= 3:
            extracted = self.parser._extract_plan_problem(original_text)
            if extracted and len(extracted) >= 3:
                problem = extracted

        # 如果用户没提供问题描述，直接基于已有诊断生成方案
        if not problem:
            # 检查项目目录下是否有已有诊断
            health_report = self.base_path / "projects" / project_id / "health-report.md"
            inv_report = self.base_path / "projects" / project_id / "investigation.md"
            if not health_report.exists() and not inv_report.exists():
                return (
                    f"📐 好，要为项目「{project_name}」生成方案。\n\n"
                    "我目前还没有这个项目的诊断数据。\n"
                    "请先说「帮我分析这个项目」或「诊断一下」，\n"
                    "等诊断完成后我会为你生成多个候选方案。"
                )
            # 有诊断数据，但没有问题描述 → 用通用问题驱动方案生成
            problem = "基于已有诊断结果，生成优化方案"

        # 执行调研+诊断+方案全流程（plan 阶段）
        results = analyzer.analyze_from_active_project(
            problem=problem,
            phases=["investigate", "diagnose", "plan"]
        )

        return self._format_plan_results(results, project_name)

    def _handle_execute(self, parsed, original_text: str = "") -> str:
        """
        处理审批/执行意图。

        - 第一次触发：发起审批请求
        - APPROVING 状态下再次触发：视为批准/拒绝/修改决策
        """
        from core.models import Phase
        from .evolution_analyzer import EvolutionAnalyzer
        from adapter_openclaw.orchestrator import ProjectEvolutionOrchestrator

        plan_id = parsed.analyze_problem
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
            decision_text = (original_text or parsed.command or "").lower()
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

        if plan_id in {"plan-a", "plan-b", "plan-c"}:
            plans_dir = self.base_path / "projects" / project_id / "plans"
            if plans_dir.exists():
                existing = sorted(plans_dir.glob("plan-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
                latest_batch = list(reversed(existing[:3]))
                label_map = {"plan-a": 0, "plan-b": 1, "plan-c": 2}
                idx = label_map.get(plan_id)
                if idx is not None and idx < len(latest_batch):
                    plan_id = latest_batch[idx].stem

        if not plan_id:
            plans_dir = self.base_path / "projects" / project_id / "plans"
            if plans_dir.exists():
                existing = sorted(plans_dir.glob("plan-*.md"))
                if existing:
                    plan_id = existing[-1].stem
        if not plan_id:
            return (
                "❌ 没有找到可执行的方案。\n"
                "请先说「生成方案」或「帮我规划」。"
            )

        plan_file = self.base_path / "projects" / project_id / "plans" / f"{plan_id}.md"
        if not plan_file.exists():
            return f"❌ 找不到方案 `{plan_id}`。"

        plan_content = plan_file.read_text(encoding="utf-8")
        title_line = plan_content.split("\n", 1)
        title = title_line[0].lstrip("#").strip() if title_line else plan_id

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
            f"- `approve {plan_id}` 或「批准」→ 开始执行\n"
            f"- `reject {plan_id}` 或「拒绝」→ 放弃此方案\n"
            f"- `revise {plan_id}` 或「修改」→ 调整方案参数\n\n"
            f"⚠️ 当前版本的执行阶段会优先生成执行任务卡，便于继续落地。"
        )

    def _format_plan_results(self, results: Dict[str, Any], project_name: str) -> str:
        """格式化方案生成结果。"""
        if results.get("status") == "error":
            return f"❌ {results.get('message', '未知错误')}"

        phases = results.get("phases_completed", [])

        # 如果还没做诊断，先提示用户
        if "diagnose" not in phases:
            return (
                f"📐 我目前还没有「{project_name}」的诊断数据。\n\n"
                "请先说「帮我分析这个项目」或「诊断一下」，\n"
                "等诊断完成后再生成方案。"
            )

        lines = [
            f"# 📐 方案生成报告：{project_name}",
            ""
        ]

        # 诊断摘要
        diag = results.get("diagnosis")
        if diag:
            dtype_labels = {
                "feature_request": "🆕 功能需求",
                "bug_fix": "🐛 缺陷修复",
                "optimization": "⚡ 性能/体验优化",
                "architecture": "🏗️ 架构调整",
                "unknown": "❓ 待确认"
            }
            dtype = diag.get("type", "unknown")
            root = diag.get("root_cause", "未知")
            priority = diag.get("priority", "?")
            lines.append(f"**诊断类型**：{dtype_labels.get(dtype, dtype)}")
            lines.append(f"**优先级**：{priority}/10")
            lines.append(f"**根因**：{root}")
            lines.append("")

        # 候选方案列表
        plans = results.get("plans")
        if plans:
            lines.append("## 📋 候选方案\n")
            lines.append(f"已生成 **{len(plans)}** 个候选方案：\n")

            # 加载并展示每个方案
            plans_dir = self.base_path / "projects" / results.get("project_id", "") / "plans"
            for i, plan_id in enumerate(plans, 1):
                plan_file = plans_dir / f"{plan_id}.md"
                label = chr(ord('A') + i - 1)  # A, B, C
                if plan_file.exists():
                    content = plan_file.read_text(encoding="utf-8")
                    # 提取标题（第一个 # 后面）
                    title = content.split("\n", 1)[0].lstrip("#").strip()
                    title = title.removeprefix("方案：").strip()
                    # 提取执行画像中的投入级别
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
            lines.append("💡 回复「执行方案A」「批准方案B」或「/evolve approve {id}」开始审批。")
        else:
            lines.append("⚠️ 方案生成未返回结果，请确认项目已有调研和诊断数据。")

        lines.append("")
        lines.append(f"---")
        lines.append(f"✅ 已完成阶段：{' → '.join(phases)}")
        return "\n".join(lines)

    def _view_plan(self, plan_id: str) -> str:
        """查看指定方案的详细内容。"""
        from .evolution_analyzer import EvolutionAnalyzer

        analyzer = EvolutionAnalyzer(str(self.base_path))
        active = analyzer.get_active_project()
        if not active:
            return "❌ 当前没有活跃项目。"

        project_id = active["id"]
        plan_file = self.base_path / "projects" / project_id / "plans" / f"{plan_id}.md"
        if not plan_file.exists():
            return f"❌ 找不到方案 `{plan_id}`，可能尚未生成或已被清理。"

        content = plan_file.read_text(encoding="utf-8")
        return (
            f"# 📄 方案详情：{plan_id}\n\n"
            f"{content}\n\n"
            f"💡 回复「批准 {plan_id}」或「执行 {plan_id}」开始审批流程。"
        )

    def _load_plan_as_dict(self, project_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        """从 Markdown 方案文件恢复一个最小可执行 plan dict。"""
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

    def _handle_command(self, text: str, original_text: str = "") -> str:
        parts = text.split(maxsplit=2)
        cmd = parts[1] if len(parts) > 1 else ""
        arg = parts[2] if len(parts) > 2 else (parts[1] if len(parts) == 1 else "")

        if text == "/evolve":
            self.state = ChatState(active=True, step="context_check")
            self._save_state()
            return (
                "🚀 开始 self-evolution onboarding。\n\n"
                "先确认一下：这是一个**已有项目**还是**新项目**？\n"
                "你可以回复：\n"
                "- 已有项目\n"
                "- 新项目\n"
                "- 或者直接给我项目路径"
            )

        if cmd in {"status", "list", "ls"} or text in {"/evolve status", "/evolve list"}:
            return self.router._format_project_list()

        if cmd == "active":
            active = self.router.get_active_project()
            if not active:
                return "当前没有活跃项目。可以先输入 /evolve 开始。"
            return (
                f"👉 当前活跃项目：{active['name']}\n"
                f"ID：{active['id']}\n"
                f"类型：{active.get('type', '?')}\n"
                f"路径：{active.get('path', '?')}"
            )

        if cmd == "switch":
            project_id = arg.strip()
            if not project_id:
                return "请使用：/evolve switch <project-id>"
            try:
                proj = self.router.switch_project(project_id)
                return f"✅ 已切换到项目：{proj['name']} [{proj['id']}]"
            except Exception as exc:
                return f"❌ 切换失败：{exc}"

        # 直接给路径
        candidate = text.replace("/evolve", "", 1).strip()
        if candidate and Path(candidate).expanduser().exists():
            session, scan = self.router.init_existing_project(candidate)
            self._reset_state()
            return self._format_existing_result(session, scan)

        # /evolve new <goal>
        if cmd == "new":
            goal = arg.strip()
            self.state = ChatState(active=True, mode="new", step="gather_name", goal=goal or None)
            self._save_state()
            if goal:
                return (
                    f"收到，新项目目标先记为：{goal}\n\n"
                    "请再告诉我这个项目叫什么名字？"
                )
            return "好的，我们从 0 开始。先告诉我：这个项目想做什么？一句话就行。"

        if cmd == "analyze":
            # arg 直接作为问题描述；original_text 是用户原始输入（用于提取问题）
            return self._handle_analyze(
                arg.strip() if arg.strip() else "",
                original_text=original_text
            )

        if cmd == "plan":
            plan_id = arg.strip()
            if plan_id and plan_id.startswith("plan-"):
                return self._view_plan(plan_id)
            return self._handle_plan(original_text=plan_id)

        if cmd in {"approve", "execute", "reject", "revise"}:
            parsed = self.parser.parse(f"{cmd} {arg}".strip())
            if parsed:
                return self._handle_execute(parsed, original_text=text)

        return self._help()

    def _continue_flow(self, text: str) -> str:
        if self.state.step == "context_check":
            # 直接路径
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

            # 默认走新项目
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
            f"路径：{scan.get('project_path')}\n\n"
            f"已生成项目档案到：projects/{session.project_id}/\n"
            f"下一步你可以继续说：\n"
            f"- /evolve status\n"
            f"- /evolve switch {session.project_id}\n"
            f"- 继续让我分析这个项目的优化方向"
        )

    def _format_new_result(self, project_id: str, project: Optional[dict]) -> str:
        name = project.get("name") if project else project_id
        return (
            f"✅ 新项目 onboarding 完成\n\n"
            f"项目名：{name}\n"
            f"项目ID：{project_id}\n"
            f"项目档案：projects/{project_id}/\n\n"
            f"已生成：profile.md / user-goals.md / competitor-benchmarks.md / optimization-roadmap.md / state.json / config.yaml\n\n"
            f"下一步你可以继续说：\n"
            f"- /evolve status\n"
            f"- /evolve switch {project_id}\n"
            f"- 帮我分析这个项目接下来优先做什么"
        )

    def _help(self) -> str:
        return (
            "🤖 /evolve 使用方式\n\n"
            "- /evolve                开始 onboarding\n"
            "- /evolve status         查看项目列表\n"
            "- /evolve active         查看当前活跃项目\n"
            "- /evolve switch <id>    切换项目\n"
            "- /evolve <项目路径>      接入已有项目\n"
            "- /evolve new <目标>     快速开始一个新项目\n\n"
            "如果你想开始，直接发：/evolve"
        )
