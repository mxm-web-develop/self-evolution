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
from .intent_parser import EvolveIntentParser


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

        normalized = self.parser.normalize(text)
        effective_text = normalized or text

        # 允许用户直接中断
        if effective_text in {"取消", "退出", "/evolve cancel", "/evolve stop", "stop", "cancel"}:
            self._reset_state()
            return "🛑 已取消当前 /evolve 流程。你可以随时重新输入 /evolve 开始。"

        # 处理显式命令 / 语义命令
        if effective_text.startswith("/evolve"):
            return self._handle_command(effective_text)

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

    def _handle_command(self, text: str) -> str:
        parts = text.split(maxsplit=2)
        cmd = parts[1] if len(parts) > 1 else ""
        arg = parts[2] if len(parts) > 2 else (parts[1] if len(parts) == 2 else "")

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
