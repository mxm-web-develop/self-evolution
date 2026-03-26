"""
统一入口模块（OnboardingRouter）
根据输入判断：已有项目 / 新项目 / 查看项目列表
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from .index_manager import ProjectIndex
from .new_project import NewProjectInitializer, init_new_project
from .existing_project import ExistingProjectInitializer
from .state import OnboardingSession


class OnboardingRouter:
    """
    统一入口，根据输入自动路由到对应初始化器。

    用法：
        router = OnboardingRouter("/path/to/self-evolution")

        # 初始化新项目
        session = router.init_new_project(
            goal="AI 图片生成 SaaS",
            name="PixGen",
            benchmarks=["Midjourney"],
        )

        # 接入已有项目
        session, scan = router.init_existing_project("/path/to/project")

        # 列出所有项目
        projects = router.list_projects()

        # 获取活跃项目
        active = router.get_active_project()
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.index = ProjectIndex(str(self.base_path))

    # ── 项目列表 ──────────────────────────────────────────────

    def list_projects(self) -> List[dict]:
        """列出所有项目"""
        return self.index.list_projects()

    def get_active_project(self) -> Optional[dict]:
        """获取当前活跃项目"""
        return self.index.get_active_project()

    def get_project(self, project_id: str) -> Optional[dict]:
        """按 ID 获取项目"""
        return self.index.get_project(project_id)

    def switch_project(self, project_id: str) -> dict:
        """切换活跃项目"""
        self.index.set_active_project(project_id)
        return self.index.get_project(project_id)

    # ── 初始化 ────────────────────────────────────────────────

    def init_new_project(
        self,
        goal: str,
        name: str,
        benchmarks: Optional[List[str]] = None,
        priorities: Optional[List[Dict[str, Any]]] = None,
        automation_boundaries: Optional[List[str]] = None,
    ) -> OnboardingSession:
        """
        初始化新项目（一条命令搞定）

        Args:
            goal: 项目目标描述
            name: 项目名称
            benchmarks: 对标竞品列表
            priorities: 优化优先级列表
            automation_boundaries: 自动化边界

        Returns:
            OnboardingSession 对象
        """
        session = init_new_project(
            base_path=str(self.base_path),
            goal=goal,
            name=name,
            benchmarks=benchmarks,
            priorities=priorities,
            automation_boundaries=automation_boundaries,
        )
        return session

    def init_existing_project(self, project_path: str) -> tuple[OnboardingSession, Dict[str, Any]]:
        """
        接入已有项目（扫描 + 画像生成）

        Args:
            project_path: 已有项目目录路径

        Returns:
            (OnboardingSession, scan_result) 元组
        """
        init = ExistingProjectInitializer(str(self.base_path), self.index)
        return init.initialize(project_path)

    # ── 自动路由（基于路径判断）────────────────────────────────

    def auto_route(
        self,
        input_value: str,
    ) -> str:
        """
        根据输入自动判断类型并执行。

        判断规则（按优先级）：
        1. 路径存在 → 已有项目
        2. 包含 "new" / "新建" → 新项目（需额外参数）
        3. 包含 "list" / "status" → 列出项目
        4. 其他 → 返回帮助信息

        Args:
            input_value: 用户输入的原始字符串

        Returns:
            执行结果描述字符串
        """
        from pathlib import Path
        v = input_value.strip()

        # 路径判断
        if Path(v).exists() and Path(v).is_dir():
            session, scan = self.init_existing_project(v)
            return (
                f"✅ 已接入已有项目\n"
                f"   项目名：{session.name}\n"
                f"   项目ID：{session.project_id}\n"
                f"   技术栈：{', '.join(scan['tech_stack'].get('languages', [])) or '未知'}\n"
                f"   目录：{scan['project_path']}\n"
                f"   文件已生成到 projects/{session.project_id}/"
            )

        # 列表/状态
        if v in ("list", "status", "ls", "列表", "状态"):
            return self._format_project_list()

        # 帮助
        if v in ("help", "--help", "-h", "帮助"):
            return self._format_help()

        # 需要更多信息
        return (
            f"⚠️ 无法自动判断：'{v}'\n"
            f"请提供项目路径（目录存在即视为已有项目）\n"
            f"或使用：onboarding.py new --goal '...' --name '...'"
        )

    # ── 格式化输出 ───────────────────────────────────────────

    def _format_project_list(self) -> str:
        projects = self.list_projects()
        active_id = self.index.get_active_project_id()

        if not projects:
            return "📋 当前没有任何项目。使用 `onboarding.py new` 初始化第一个项目。"

        # 检查项目配置完善度
        def check_config(project_id: str) -> str:
            proj_dir = self.index.base_path / "projects" / project_id
            goals = (proj_dir / "profile.md").exists()
            benchmarks = (proj_dir / "profile.md").exists()
            config = (proj_dir / "config.yaml").exists()
            if goals and benchmarks and config:
                return "🎯"   # 完整配置
            elif goals or benchmarks or config:
                return "🔧"   # 部分配置
            else:
                return "⬜"   # 仅有基本扫描

        lines = [
            "📋 项目列表\n",
            "| 状态 | ID | 名称 | 类型 | 阶段 | Onboarding |",
            "|------|-----|------|------|------|------------|",
        ]
        for p in projects:
            marker = "👉" if p["id"] == active_id else "  "
            cfg = check_config(p["id"])
            cfg_label = {"🎯": "✅完整", "🔧": "⚠️部分", "⬜": "⬜未完成"}[cfg]
            lines.append(
                f"| {marker} | `{p['id']}` | {p['name']} |"
                f" {p.get('type', '?')} | {p.get('phase', '?')} | {cfg_label} |"
            )
        return "\n".join(lines)

    def _format_help(self) -> str:
        return """🤖 Self-Evolution Onboarding 使用帮助

用法：
  python -m onboarding.cli --list              # 列出所有项目
  python -m onboarding.cli --active            # 查看活跃项目
  python -m onboarding.cli --new \\            # 初始化新项目
    --goal "做什么" --name "项目名"
  python -m onboarding.cli --existing /path   # 接入已有项目
  python -m onboarding.cli --switch pixgen    # 切换项目

或 Python 代码：
  from src.onboarding import OnboardingRouter
  router = OnboardingRouter("/path/to/self-evolution")
  router.init_new_project(goal="...", name="...")
  router.init_existing_project("/path/to/project")
  router.list_projects()
  router.get_active_project()
"""
