# adapter_openclaw/orchestrator.py
"""
ProjectEvolutionOrchestrator — 项目进化主流程编排器

串联 Core 各模块，按 Phase 顺序驱动完整流程
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from core.models import Phase, Plan
from core.investigator import Investigator
from core.diagnose import DiagnoseEngine
from core.planner import Planner
from core.critic import Critic
from core.approver import Approver
from core.executor import Executor
from core.learner import Learner
from core.case_library import CaseLibrary


class ProjectEvolutionOrchestrator:
    """
    项目进化主流程编排器

    每次 run() 调用执行当前 Phase 的工作，
    状态外置到文件，支持中断和恢复。
    """

    def __init__(self, bridge):
        """
        Args:
            bridge: OpenClawBridge 实例
        """
        self.bridge = bridge
        self._init_core_modules()

    def _init_core_modules(self):
        """初始化 Core 各模块"""
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

    def run(
        self,
        project_id: str,
        problem: str,
        human_approved: bool = False
    ) -> Dict[str, Any]:
        """
        执行项目进化流程的当前阶段

        Args:
            project_id: 项目 ID
            problem: 用户描述的问题
            human_approved: 是否已获得人类审批

        Returns:
            当前阶段的执行结果
        """
        sm = self.bridge.get_state_manager()
        state = sm.load_state(project_id)

        if state is None:
            state = self._create_state(project_id, problem)
        else:
            # 已加载的 state，也补充 config 上下文（如果缺失）
            self._enrich_context(state)

        # 保存当前时间
        state.updated_at = self._now()

        result = self._execute_phase(state, problem, human_approved)

        # 更新历史
        state.add_history(
            action=state.phase.value,
            detail=f"执行结果：{result.get('status', 'unknown')}"
        )

        # 保存状态
        sm.save_state(project_id, state)

        return result

    def _execute_phase(
        self,
        state,
        problem: str,
        human_approved: bool
    ) -> Dict[str, Any]:
        """根据当前 Phase 执行对应逻辑"""
        sm = self.bridge.get_state_manager()
        project_id = state.project_id

        # Phase: INVESTIGATING
        if state.phase == Phase.INVESTIGATING:
            investigation = self.investigator.investigate(problem, project_context=state.context)
            state.context["investigation"] = investigation
            state.phase = Phase.IDLE
            sm.save_investigation(project_id, investigation)
            return {
                "phase": "investigating",
                "status": "completed",
                "report": investigation,
                "next_action": "继续调研 → 进入诊断"
            }

        # Phase: DIAGNOSING
        if state.phase == Phase.DIAGNOSING:
            diagnosis = self.diagnose_engine.diagnose(
                state.context.get("investigation", {}),
                project_context=state.context
            )
            state.context["diagnosis"] = diagnosis
            state.phase = Phase.IDLE
            return {
                "phase": "diagnosing",
                "status": "completed",
                "diagnosis": diagnosis,
                "next_action": "诊断完成 → 生成方案"
            }

        # Phase: PLANNING
        if state.phase == Phase.PLANNING:
            plans = self.planner.generate_plans(
                problem,
                state.context.get("diagnosis", {}),
                state.context.get("investigation", {}),
                project_context=state.context
            )
            state.context["plans"] = [p.to_dict() for p in plans]
            state.phase = Phase.IDLE

            # 保存方案文件
            for plan in plans:
                sm.save_plan(project_id, plan)

            return {
                "phase": "planning",
                "status": "completed",
                "plans_count": len(plans),
                "plan_ids": [p.plan_id for p in plans],
                "next_action": "方案生成完成 → 进入评分"
            }

        # Phase: CRITIQUING
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

            return {
                "phase": "critiquing",
                "status": "completed",
                "scores": scored_plans,
                "next_action": "评分完成 → 进入审批"
            }

        # Phase: APPROVING
        if state.phase == Phase.APPROVING:
            best_plan = self._get_best_plan(state.context.get("scored_plans", []))
            self.approver.request_approval(
                best_plan.title,
                best_plan.scores,
                self.bridge.get_notifier(),
                project_id
            )
            return {
                "phase": "approving",
                "status": "waiting_for_human",
                "plan": best_plan.title,
                "scores": best_plan.scores,
                "instruction": "请回复 Approve/Reject/Revise"
            }

        # Phase: EXECUTING
        if state.phase == Phase.EXECUTING:
            best_plan = self._get_best_plan(state.context.get("scored_plans", []))
            result = self.executor.execute_plan(
                best_plan,
                self.bridge.get_executor()
            )
            state.context["execution_result"] = result
            state.phase = Phase.LEARNING
            return {
                "phase": "executing",
                "status": "completed",
                "result": result,
                "next_action": "执行完成 → 进入学习"
            }

        # Phase: LEARNING
        if state.phase == Phase.LEARNING:
            scored_plans = state.context.get("scored_plans", [{}])
            plan = self._dict_to_plan(scored_plans[0]) if scored_plans else None
            case = None
            if plan:
                case = self.learner.learn_from_execution(
                    plan,
                    state.context.get("execution_result", {}),
                    state.context.get("diagnosis", {})
                )
            state.phase = Phase.IDLE
            return {
                "phase": "learning",
                "status": "completed",
                "case_created": case is not None,
                "case_id": case.case_id if case else None,
                "next_action": "全部流程完成 ✅"
            }

        # Phase: IDLE — 开始新流程
        if state.phase == Phase.IDLE:
            # 检查是否有历史上下文，决定从哪个阶段继续
            if "execution_result" in state.context:
                return {
                    "phase": "idle",
                    "status": "completed",
                    "message": "项目已完成，上次执行结果：",
                    "result": state.context.get("execution_result", {})
                }

            # 开始新流程：从调研开始
            original_problem = state.context.get("original_problem", problem)
            state.phase = Phase.INVESTIGATING
            return {
                "phase": "idle",
                "status": "starting",
                "message": f"开始新项目：{original_problem[:50]}...",
                "next_phase": "investigating"
            }

        # 未知 Phase
        return {
            "phase": state.phase.value,
            "status": "error",
            "message": f"未知 Phase：{state.phase}"
        }

    def _create_state(self, project_id: str, problem: str):
        """创建新的项目状态，加载项目配置文件作为上下文"""
        from core.models import ProjectState
        from pathlib import Path

        sm = self.bridge.get_state_manager()
        projects_root = Path(sm.projects_root)
        proj_dir = projects_root / project_id

        # 加载项目配置文件
        context = {"original_problem": problem}

        # 读取 user-goals.md
        goals_file = proj_dir / "user-goals.md"
        if goals_file.exists():
            try:
                context["user_goals"] = goals_file.read_text(encoding="utf-8")
            except Exception:
                pass

        # 读取 competitor-benchmarks.md
        benchmarks_file = proj_dir / "competitor-benchmarks.md"
        if benchmarks_file.exists():
            try:
                context["competitor_benchmarks"] = benchmarks_file.read_text(encoding="utf-8")
            except Exception:
                pass

        # 读取 config.yaml
        config_file = proj_dir / "config.yaml"
        if config_file.exists():
            try:
                import yaml
                with open(config_file, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                if cfg:
                    context["project_config"] = cfg
                    context["priorities"] = cfg.get("priorities", [])
                    context["tech_stack"] = cfg.get("tech_stack", {})
            except Exception:
                pass

        # 从 projects/index.json 读取项目基本信息
        index_file = projects_root / "index.json"
        if index_file.exists():
            import json
            try:
                with open(index_file, encoding="utf-8") as f:
                    idx = json.load(f)
                for proj in idx.get("projects", []):
                    if proj.get("id") == project_id:
                        context["project_info"] = proj
                        context["tech_stack"] = proj.get("tech_stack", context.get("tech_stack", {}))
                        break
            except Exception:
                pass

        state = ProjectState(
            project_id=project_id,
            phase=Phase.IDLE,
            created_at=self._now(),
            updated_at=self._now(),
            current_task=problem,
            context=context
        )
        sm.save_state(project_id, state)
        return state

    def _enrich_context(self, state) -> None:
        """为已有 state 补充 config 上下文（如果缺失）"""
        from pathlib import Path
        import json

        sm = self.bridge.get_state_manager()
        projects_root = Path(sm.projects_root)
        proj_dir = projects_root / state.project_id
        ctx = state.context

        # 读取 user-goals.md
        if "user_goals" not in ctx:
            goals_file = proj_dir / "user-goals.md"
            if goals_file.exists():
                try:
                    ctx["user_goals"] = goals_file.read_text(encoding="utf-8")
                except Exception:
                    pass

        # 读取 competitor-benchmarks.md
        if "competitor_benchmarks" not in ctx:
            benchmarks_file = proj_dir / "competitor-benchmarks.md"
            if benchmarks_file.exists():
                try:
                    ctx["competitor_benchmarks"] = benchmarks_file.read_text(encoding="utf-8")
                except Exception:
                    pass

        # 读取 config.yaml（始终重新加载，确保最新）
        config_file = proj_dir / "config.yaml"
        if config_file.exists():
            try:
                import yaml
                with open(config_file, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                if cfg:
                    ctx["project_config"] = cfg
                    ctx["priorities"] = cfg.get("priorities", [])
                    ctx["tech_stack"] = cfg.get("tech_stack", {})
            except Exception:
                pass

        # 从 index.json 补 tech_stack
        if "tech_stack" not in ctx or not ctx.get("tech_stack"):
            index_file = projects_root / "index.json"
            if index_file.exists():
                try:
                    with open(index_file, encoding="utf-8") as f:
                        idx = json.load(f)
                    for proj in idx.get("projects", []):
                        if proj.get("id") == state.project_id:
                            ctx["tech_stack"] = proj.get("tech_stack", {})
                            break
                except Exception:
                    pass

    def _get_best_plan(self, plans_data: List[Dict]) -> Plan:
        """从评分中选择最优方案"""
        if not plans_data:
            return Plan(
                plan_id="default",
                project_id="current",
                title="默认方案",
                description="",
                pros=[], cons=[],
                resource_estimate={},
                risks=[],
                expected_outcomes=[]
            )

        def get_final(p):
            scores = p.get("scores", {})
            return scores.get("final", 0.0)

        best_data = max(plans_data, key=get_final)
        return self._dict_to_plan(best_data)

    def _dict_to_plan(self, data: Dict) -> Plan:
        """从字典恢复 Plan"""
        # 过滤掉非 Plan 字段
        plan_fields = {
            "plan_id", "project_id", "title", "description",
            "pros", "cons", "resource_estimate", "risks",
            "expected_outcomes", "scores", "approved", "approver_notes"
        }
        filtered = {k: v for k, v in data.items() if k in plan_fields}
        return Plan(**filtered)

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def get_status(self, project_id: str) -> Dict[str, Any]:
        """获取项目状态摘要"""
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
            "case_library_stats": stats
        }
