"""ProjectEvolutionOrchestrator — 动态推理 + 持续记忆版本。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from core.models import Phase, Plan, ProjectState
from core.investigator import Investigator
from core.diagnose import DiagnoseEngine
from core.planner import Planner
from core.critic import Critic
from core.approver import Approver
from core.executor import Executor
from core.learner import Learner
from core.case_library import CaseLibrary


class ProjectEvolutionOrchestrator:
    def __init__(self, bridge):
        self.bridge = bridge
        self._init_core_modules()

    def _init_core_modules(self):
        cases_root = str(self.bridge.cases_root)
        case_library = CaseLibrary(cases_root)
        search_provider = self.bridge.get_search_provider()
        self.investigator = Investigator(search_provider, case_library)
        self.diagnose_engine = DiagnoseEngine()
        self.planner = Planner()
        self.critic = Critic()
        self.approver = Approver()
        self.executor = Executor(self.bridge)
        self.learner = Learner(case_library)
        self._case_library = case_library

    def run(self, project_id: str, problem: str, human_approved: bool = False) -> Dict[str, Any]:
        sm = self.bridge.get_state_manager()
        state = sm.load_state(project_id)
        if state is None:
            state = self._create_state(project_id, problem)
        else:
            self._enrich_context(state)

        state.updated_at = self._now()
        result = self._execute_phase(state, problem, human_approved)
        state.add_history(action=state.phase.value, detail=f"执行结果：{result.get('status', 'unknown')}", payload=result)
        sm.save_state(project_id, state)
        self._append_analysis_history(project_id, state, result)
        return result

    def _execute_phase(self, state: ProjectState, problem: str, human_approved: bool) -> Dict[str, Any]:
        sm = self.bridge.get_state_manager()
        project_id = state.project_id

        if state.phase == Phase.INVESTIGATING:
            investigation = self.investigator.investigate(problem, project_context=state.context, scanned_code=state.context.get("scanned_code"))
            state.context["investigation"] = investigation
            state.context["scanned_code"] = investigation.get("scanned_code")
            state.context["maturity_assessment"] = investigation.get("maturity_assessment")
            state.phase = Phase.IDLE
            sm.save_investigation(project_id, investigation)
            return {"phase": "investigating", "status": "completed", "report": investigation, "next_action": "继续诊断"}

        if state.phase == Phase.DIAGNOSING:
            diagnosis = self.diagnose_engine.diagnose(state.context.get("investigation", {}), project_context=state.context)
            state.context["diagnosis"] = diagnosis
            state.context["maturity_assessment"] = diagnosis.get("maturity_assessment")
            state.phase = Phase.IDLE
            return {"phase": "diagnosing", "status": "completed", "diagnosis": diagnosis, "next_action": "生成方案"}

        if state.phase == Phase.PLANNING:
            plans = self.planner.generate_plans(problem, state.context.get("diagnosis", {}), state.context.get("investigation", {}), project_context=state.context)
            state.context["plans"] = [p.to_dict() for p in plans]
            state.phase = Phase.IDLE
            for plan in plans:
                sm.save_plan(project_id, plan)
            return {"phase": "planning", "status": "completed", "plans_count": len(plans), "plan_ids": [p.plan_id for p in plans], "plans": [p.to_dict() for p in plans], "next_action": "进入评分或人工挑选"}

        if state.phase == Phase.CRITIQUING:
            scored_plans = []
            for plan_data in state.context.get("plans", []):
                plan = self._dict_to_plan(plan_data)
                scores = self.critic.score_plan(plan, state.context)
                plan.scores = scores
                scored_plans.append(plan.to_dict())
                sm.save_plan(project_id, plan)
            state.context["scored_plans"] = scored_plans
            state.phase = Phase.IDLE
            sm.save_scores(project_id, scored_plans)
            return {"phase": "critiquing", "status": "completed", "scores": scored_plans, "next_action": "审批"}

        if state.phase == Phase.APPROVING:
            best_plan = self._get_best_plan(state.context.get("scored_plans", []) or state.context.get("plans", []))
            self.approver.request_approval(best_plan.title, best_plan.scores, self.bridge.get_notifier(), project_id)
            return {"phase": "approving", "status": "waiting_for_human", "plan": best_plan.title, "scores": best_plan.scores, "instruction": "请回复 Approve/Reject/Revise"}

        if state.phase == Phase.EXECUTING:
            best_plan = self._get_best_plan(state.context.get("scored_plans", []) or state.context.get("plans", []))
            result = self.executor.execute_plan(best_plan, self.bridge.get_executor())
            state.context["execution_result"] = result
            state.phase = Phase.LEARNING
            return {"phase": "executing", "status": "completed", "result": result, "next_action": "学习回写"}

        if state.phase == Phase.LEARNING:
            scored_plans = state.context.get("scored_plans") or state.context.get("plans") or [{}]
            plan = self._dict_to_plan(scored_plans[0]) if scored_plans else None
            case = None
            if plan:
                case = self.learner.learn_from_execution(plan, state.context.get("execution_result", {}), state.context.get("diagnosis", {}))
            state.phase = Phase.IDLE
            return {"phase": "learning", "status": "completed", "case_created": case is not None, "case_id": case.case_id if case else None, "next_action": "全部完成"}

        if state.phase == Phase.IDLE:
            if "execution_result" in state.context:
                return {"phase": "idle", "status": "completed", "message": "项目已完成", "result": state.context.get("execution_result", {})}
            state.phase = Phase.INVESTIGATING
            return {"phase": "idle", "status": "starting", "message": f"开始新项目：{problem[:50]}...", "next_phase": "investigating"}

        return {"phase": state.phase.value, "status": "error", "message": f"未知 Phase：{state.phase}"}

    def _create_state(self, project_id: str, problem: str):
        sm = self.bridge.get_state_manager()
        projects_root = Path(sm.projects_root)
        proj_dir = projects_root / project_id
        context = {
            "project_id": project_id,
            "original_problem": problem,
            "analysis_history": self._load_analysis_history(project_id),
        }
        self._load_project_files_into_context(proj_dir, projects_root, project_id, context)
        context["maturity_assessment"] = self._assess_project_maturity(context)
        state = ProjectState(project_id=project_id, phase=Phase.IDLE, created_at=self._now(), updated_at=self._now(), current_task=problem, context=context)
        sm.save_state(project_id, state)
        return state

    def _enrich_context(self, state) -> None:
        sm = self.bridge.get_state_manager()
        projects_root = Path(sm.projects_root)
        proj_dir = projects_root / state.project_id
        state.context.setdefault("project_id", state.project_id)
        state.context["analysis_history"] = self._load_analysis_history(state.project_id)
        self._load_project_files_into_context(proj_dir, projects_root, state.project_id, state.context)
        if not state.context.get("maturity_assessment"):
            state.context["maturity_assessment"] = self._assess_project_maturity(state.context)

    def _load_project_files_into_context(self, proj_dir: Path, projects_root: Path, project_id: str, context: Dict[str, Any]) -> None:
        profile_file = proj_dir / "profile.md"
        if profile_file.exists():
            profile_text = profile_file.read_text(encoding="utf-8")
            context["project_profile"] = profile_text
            context["user_goals"] = profile_text
            context["competitor_benchmarks"] = profile_text
        config_file = proj_dir / "config.yaml"
        if config_file.exists():
            try:
                import yaml
                cfg = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                context["project_config"] = cfg
                context["priorities"] = cfg.get("priorities", [])
                context["tech_stack"] = cfg.get("tech_stack", context.get("tech_stack", {}))
            except Exception:
                pass
        index_file = projects_root / "index.json"
        if index_file.exists():
            try:
                idx = json.loads(index_file.read_text(encoding="utf-8"))
                for proj in idx.get("projects", []):
                    if proj.get("id") == project_id:
                        context["project_info"] = proj
                        context["project_path"] = proj.get("path")
                        if proj.get("tech_stack"):
                            context["tech_stack"] = proj.get("tech_stack")
                        break
            except Exception:
                pass

    def _assess_project_maturity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        reasons = []
        if context.get("user_goals"):
            score += 1
            reasons.append("有 user-goals")
        if context.get("competitor_benchmarks"):
            score += 1
            reasons.append("有竞品基准")
        if context.get("priorities"):
            score += 1
            reasons.append("有优先级配置")
        if context.get("project_path"):
            score += 1
            reasons.append("有关联项目路径")
        if context.get("analysis_history"):
            score += 1
            reasons.append("已有历史分析沉淀")
        stage = "early" if score <= 2 else ("growing" if score <= 4 else "mature")
        label = {"early": "早期", "growing": "成长中", "mature": "相对成熟"}[stage]
        return {"stage": stage, "label": label, "score": score, "reasoning": reasons}

    def _analysis_history_file(self, project_id: str) -> Path:
        return Path(self.bridge.projects_root) / project_id / "analysis" / "outcomes" / "analysis_history.md"

    def _load_analysis_history(self, project_id: str) -> str:
        file = self._analysis_history_file(project_id)
        if not file.exists():
            return ""
        return file.read_text(encoding="utf-8")

    def _append_analysis_history(self, project_id: str, state: ProjectState, result: Dict[str, Any]) -> None:
        file = self._analysis_history_file(project_id)
        file.parent.mkdir(parents=True, exist_ok=True)
        phase = result.get("phase", state.phase.value)
        lines = []
        if not file.exists():
            lines.append(f"# {project_id} analysis history\n\n")
        lines.append(f"## {self._now()} · {phase}\n")
        lines.append(f"- status: {result.get('status', 'unknown')}\n")
        if phase == "investigating" and result.get("report"):
            report = result["report"]
            lines.append(f"- maturity: {report.get('maturity_assessment', {}).get('label', '未知')}\n")
            lines.append(f"- dimensions: {', '.join(d.get('dimension') for d in report.get('optimization_dimensions', [])[:5])}\n")
        if phase == "diagnosing" and result.get("diagnosis"):
            diag = result["diagnosis"]
            lines.append(f"- summary: {diag.get('summary', '')}\n")
            lines.append(f"- root_cause: {diag.get('root_cause', '').replace(chr(10), ' ')}\n")
        if phase == "planning":
            plan_ids = result.get("plan_ids", [])
            lines.append(f"- plans: {', '.join(plan_ids)}\n")
        lines.append("\n")
        with open(file, "a", encoding="utf-8") as f:
            f.writelines(lines)
        state.context["analysis_history"] = self._load_analysis_history(project_id)

    def _get_best_plan(self, plans_data: List[Dict]) -> Plan:
        if not plans_data:
            return Plan(plan_id="default", project_id="current", title="默认方案", description="", pros=[], cons=[], resource_estimate={}, risks=[], expected_outcomes=[])

        def get_final(p):
            return (p.get("scores") or {}).get("final", p.get("resource_estimate", {}).get("gap_score", 0))

        return self._dict_to_plan(max(plans_data, key=get_final))

    def _dict_to_plan(self, data: Dict) -> Plan:
        return Plan.from_dict({
            "plan_id": data.get("plan_id", "default"),
            "project_id": data.get("project_id", "current"),
            "title": data.get("title", "默认方案"),
            "description": data.get("description", ""),
            "pros": data.get("pros", []),
            "cons": data.get("cons", []),
            "resource_estimate": data.get("resource_estimate", {}),
            "risks": data.get("risks", []),
            "expected_outcomes": data.get("expected_outcomes", []),
            "target_dimension": data.get("target_dimension"),
            "maturity_assessment": data.get("maturity_assessment"),
            "action_items": data.get("action_items"),
            "scores": data.get("scores"),
            "approved": data.get("approved"),
            "approver_notes": data.get("approver_notes"),
        })

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def get_status(self, project_id: str) -> Dict[str, Any]:
        sm = self.bridge.get_state_manager()
        state = sm.load_state(project_id)
        if state is None:
            return {"exists": False}
        stats = self._case_library.get_stats() if hasattr(self, "_case_library") else {}
        return {
            "exists": True,
            "project_id": project_id,
            "phase": state.phase.value,
            "current_task": state.current_task,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "history_count": len(state.history),
            "case_library_stats": stats,
            "maturity_assessment": state.context.get("maturity_assessment"),
        }
