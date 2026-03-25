# adapter_openclaw/state_manager.py
"""
StateManager — 文件状态管理

基于文件系统的持久化状态管理
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from core.models import ProjectState, Plan


class StateManager:
    """基于文件的持久化状态管理"""

    def __init__(self, projects_root: str):
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def save_state(self, project_id: str, state: ProjectState) -> None:
        state_file = self._state_file(project_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        if state_file.exists():
            backup_file = state_file.parent / f"{state_file.stem}.bak{state_file.suffix}"
            shutil.copy(state_file, backup_file)

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

    def load_state(self, project_id: str) -> Optional[ProjectState]:
        state_file = self._state_file(project_id)

        if state_file.exists():
            try:
                with open(state_file, encoding="utf-8") as f:
                    data = json.load(f)
                return ProjectState.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass

        backup_file = state_file.parent / f"{state_file.stem}.bak{state_file.suffix}"
        if backup_file.exists():
            try:
                with open(backup_file, encoding="utf-8") as f:
                    data = json.load(f)
                return ProjectState.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass

        return None

    def save_plan(self, project_id: str, plan: Plan) -> None:
        plans_dir = self.projects_root / project_id / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)

        plan_file = plans_dir / f"{plan.plan_id}.md"
        with open(plan_file, "w", encoding="utf-8") as f:
            f.write(self._plan_to_md(plan))

    def save_investigation(self, project_id: str, investigation: dict) -> None:
        inv_file = self.projects_root / project_id / "investigation.md"
        inv_file.parent.mkdir(parents=True, exist_ok=True)

        lines = [f"# 调研报告：{project_id}\n\n"]
        lines.append(f"**问题**：{investigation.get('problem', '')}\n\n")

        cases = investigation.get("similar_cases", [])
        if cases:
            lines.append("## 相似案例\n\n")
            for c in cases:
                lines.append(f"- 【{c.get('category', '')}】{c.get('title', '')} (相似度:{c.get('score', 0)})\n")
            lines.append("\n")

        web = investigation.get("web_findings", [])
        if web and not any("error" in str(r) for r in web):
            lines.append("## 网络发现\n\n")
            for r in web:
                lines.append(f"- [{r.get('title', '')}]({r.get('url', '')}): {r.get('snippet', '')}\n")
            lines.append("\n")

        recs = investigation.get("recommendations", [])
        if recs:
            lines.append("## 建议\n\n")
            for rec in recs:
                lines.append(f"- {rec}\n")

        with open(inv_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def save_scores(self, project_id: str, scores: list) -> None:
        scores_file = self.projects_root / project_id / "scores.json"
        scores_file.parent.mkdir(parents=True, exist_ok=True)
        with open(scores_file, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)

    def _state_file(self, project_id: str) -> Path:
        return self.projects_root / project_id / "state.json"

    def _plan_to_md(self, plan: Plan) -> str:
        approved_emoji = {
            True: "✅ 通过",
            False: "❌ 拒绝",
            None: "⏳ 待审批"
        }

        scores_md = ""
        if plan.scores:
            s = plan.scores
            scores_md = f"""
## 评分结果

| 维度 | 分值 |
|---|---|
| 业务价值 | {s.get('business', 'N/A')} |
| 技术可行性 | {s.get('technical', 'N/A')} |
| 用户体验 | {s.get('ux', 'N/A')} |
| **总分** | **{s.get('final', 'N/A')}** |

**建议**：{s.get('recommendation', 'N/A')}
"""

        est = plan.resource_estimate or {}
        pros_lines = "".join(f"- {p}\n" for p in plan.pros)
        cons_lines = "".join(f"- {c}\n" for c in plan.cons)
        risks_lines = "".join(f"- {r}\n" for r in plan.risks)
        outcomes_lines = "".join(f"- {o}\n" for o in plan.expected_outcomes)

        return f"""# 方案：{plan.title}

## 描述
{plan.description}

## 优势
{pros_lines}## 劣势
{cons_lines}## 实施评估
- **投入级别**：{est.get('effort', 'N/A')}
- **影响范围**：{est.get('scope', 'N/A')}
- **自动化适配**：{est.get('automation', 'N/A')}
- **执行方式**：{est.get('execution_style', 'N/A')}

## 风险
{risks_lines}## 预期结果
{outcomes_lines}{scores_md}

## 审批
**状态**：{approved_emoji.get(plan.approved, '⏳ 待审批')}
**备注**：{plan.approver_notes or '无'}
"""
