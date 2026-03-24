"""
新项目初始化器
输入：项目目标、项目名、对标产品、优先级、自动化边界
输出：projects/{project-id}/ 下生成 profile.md, user-goals.md 等文件
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from .state import OnboardingSession, OnboardingPhase
from .index_manager import ProjectIndex
from . import templates


def make_project_id(name: str) -> str:
    """从项目名生成合法的 project_id（小写 + 连字符）"""
    # Remove special chars, lowercase, replace spaces with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
    slug = "-".join(slug.lower().split())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or "project"


class NewProjectInitializer:
    """新项目初始化器"""

    def __init__(self, base_path: str, index: ProjectIndex):
        self.base_path = Path(base_path)
        self.index = index

    # ── 交互式收集（最小版：支持直接传参）─────────────────────────

    def collect(
        self,
        goal: Optional[str] = None,
        name: Optional[str] = None,
        benchmarks: Optional[List[str]] = None,
        priorities: Optional[List[Dict[str, Any]]] = None,
        automation_boundaries: Optional[List[str]] = None,
    ) -> OnboardingSession:
        """
        收集新项目信息并返回 session。
        参数可选，为 None 时留空（供后续步骤填充）。
        """
        # 生成 project_id
        project_id = make_project_id(name or goal or "new-project")
        session = OnboardingSession(
            project_id=project_id,
            project_type="new",
            phase=OnboardingPhase.GATHER_GOAL,
            goal=goal,
            name=name,
            benchmarks=benchmarks or [],
            priorities=priorities or [],
            automation_boundaries=automation_boundaries or [],
        )

        if goal:
            session.add_history("goal", goal)
        if name:
            session.add_history("name", name)
        if benchmarks:
            session.add_history("benchmarks", ", ".join(benchmarks))
        if priorities:
            dims = ", ".join(p.get("dimension","") for p in priorities)
            session.add_history("priorities", dims)
        if automation_boundaries:
            session.add_history("automation_boundaries", ", ".join(automation_boundaries))

        session.touch()
        return session

    # ── 落地文件 ─────────────────────────────────────────────────

    def initialize(self, session: OnboardingSession, context: Dict[str, Any] = None) -> Path:
        """
        将 session 数据写入 projects/{project-id}/ 下的所有文件
        """
        project_dir = self.base_path / "projects" / session.project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        ctx = context or {}

        # 1. state.json
        state_data = templates.build_state_json(session, ctx)
        with open(project_dir / "state.json", "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)

        # 2. profile.md
        profile_md = templates.build_profile_md(session, ctx)
        with open(project_dir / "profile.md", "w", encoding="utf-8") as f:
            f.write(profile_md)

        # 3. user-goals.md
        goals_md = templates.build_user_goals_md(session)
        with open(project_dir / "user-goals.md", "w", encoding="utf-8") as f:
            f.write(goals_md)

        # 4. competitor-benchmarks.md
        benchmarks_md = templates.build_competitor_benchmarks_md(session)
        with open(project_dir / "competitor-benchmarks.md", "w", encoding="utf-8") as f:
            f.write(benchmarks_md)

        # 5. optimization-roadmap.md
        roadmap_md = templates.build_optimization_roadmap_md(session)
        with open(project_dir / "optimization-roadmap.md", "w", encoding="utf-8") as f:
            f.write(roadmap_md)

        # 6. config.yaml（最小配置）
        config_yaml = self._make_config_yaml(session)
        with open(project_dir / "config.yaml", "w", encoding="utf-8") as f:
            f.write(config_yaml)

        # 7. 更新 index.json
        idx_entry = self.index.make_project_entry(
            project_id=session.project_id,
            name=session.name or session.project_id,
            project_path=str(project_dir),
            project_type="new",
            description=session.goal or "",
        )
        idx_entry["onboarding_completed"] = True
        try:
            self.index.add_project(idx_entry)
        except ValueError:
            # 项目已存在，更新
            self.index.update_project(session.project_id, idx_entry)

        return project_dir

    def _make_config_yaml(self, session: OnboardingSession) -> str:
        return f"""# {session.name or session.project_id} 项目配置
# 由 onboarding 自动生成

project:
  id: {session.project_id}
  name: {session.name or session.project_id}
  description: {session.goal or ""}

search:
  provider: duckduckgo  # 默认免费 provider
  default_count: 5

notification:
  channel: webchat
  target: main

execution:
  timeout_ms: 300000
  phases_per_run: 1
"""


# ── 快捷函数 ───────────────────────────────────────────────────────────────

def init_new_project(
    base_path: str,
    goal: str,
    name: str,
    benchmarks: List[str] = None,
    priorities: List[Dict[str, Any]] = None,
    automation_boundaries: List[str] = None,
) -> OnboardingSession:
    """
    一句话初始化新项目的便捷函数。

    用法示例：
        session = init_new_project(
            base_path="/path/to/self-evolution",
            goal="做一个 AI 图片生成 SaaS",
            name="PixGen",
            benchmarks=["Midjourney", "Leonardo.ai"],
            priorities=[
                {"dimension": "performance", "weight": 0.4, "reason": "用户关注速度"},
                {"dimension": "conversion", "weight": 0.3, "reason": "提升转化"},
            ],
            automation_boundaries=["cost_approval", "external_release"],
        )
    """
    base_path = Path(base_path)
    idx = ProjectIndex(str(base_path))
    init = NewProjectInitializer(str(base_path), idx)

    session = init.collect(
        goal=goal,
        name=name,
        benchmarks=benchmarks,
        priorities=priorities,
        automation_boundaries=automation_boundaries,
    )
    init.initialize(session)
    return session
