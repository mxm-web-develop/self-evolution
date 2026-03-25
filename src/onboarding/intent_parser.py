"""
自然语言意图解析器（OpenClaw Skill 入口）

把用户的自然语言表达映射为统一的 /evolve 命令，方便 skill 在 OpenClaw 中稳定调用。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ParsedIntent:
    kind: str
    command: Optional[str] = None
    confidence: float = 0.0


class EvolveIntentParser:
    """将中英文自然语言解析为统一的 /evolve 命令。"""

    def parse(self, text: str) -> Optional[ParsedIntent]:
        raw = (text or "").strip()
        if not raw:
            return None

        if raw.startswith("/evolve"):
            return ParsedIntent(kind="command", command=raw, confidence=1.0)

        path = self._extract_existing_path(raw)
        if path:
            return ParsedIntent(kind="existing", command=f"/evolve {path}", confidence=0.98)

        lowered = raw.lower()
        compact = re.sub(r"\s+", " ", lowered)

        if self._is_cancel(raw, compact):
            return ParsedIntent(kind="cancel", command="/evolve cancel", confidence=0.98)

        project_id = self._extract_switch_target(raw)
        if project_id:
            return ParsedIntent(kind="switch", command=f"/evolve switch {project_id}", confidence=0.92)

        if self._is_status(compact):
            return ParsedIntent(kind="status", command="/evolve status", confidence=0.9)

        if self._is_active(compact):
            return ParsedIntent(kind="active", command="/evolve active", confidence=0.9)

        new_goal = self._extract_new_project_goal(raw)
        if new_goal is not None:
            if new_goal:
                return ParsedIntent(kind="new", command=f"/evolve new {new_goal}", confidence=0.88)
            return ParsedIntent(kind="start", command="/evolve", confidence=0.8)

        if self._is_start(raw, compact):
            return ParsedIntent(kind="start", command="/evolve", confidence=0.75)

        if self._is_help(compact):
            return ParsedIntent(kind="help", command="/evolve help", confidence=0.8)

        return None

    def normalize(self, text: str) -> Optional[str]:
        parsed = self.parse(text)
        return parsed.command if parsed else None

    def _extract_existing_path(self, text: str) -> Optional[str]:
        cleaned = text.strip().strip('"').strip("'")
        candidate = Path(cleaned).expanduser()
        if candidate.exists() and candidate.is_dir():
            return str(candidate.resolve())

        patterns = [
            r"(?:接入|导入|分析|跟进|扫描|onboard|import|analy[sz]e)\s+(?:项目|project)?\s*(/[^\s]+)",
            r"(?:接入|导入|分析|跟进|扫描|onboard|import|analy[sz]e)\s+(?:项目|project)?\s*(~?/[^\s]+)",
            r"(?:existing\s+project|project\s+path)\s*[:：]?\s*(~?/[^\s]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                path = Path(match.group(1)).expanduser()
                if path.exists() and path.is_dir():
                    return str(path.resolve())
        return None

    def _extract_switch_target(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:切换(?:到)?(?:项目)?|切到|改用项目)\s+([a-zA-Z0-9][a-zA-Z0-9_-]*)",
            r"(?:switch(?:\s+to)?|use\s+project|change\s+project\s+to)\s+([a-zA-Z0-9][a-zA-Z0-9_-]*)",
            r"(?:当前项目用|project\s+id\s+is)\s+([a-zA-Z0-9][a-zA-Z0-9_-]*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_new_project_goal(self, text: str) -> Optional[str]:
        patterns = [
            r"^(?:帮我|给我|想要|我要)?\s*(?:新项目|新建(?:一个)?项目|创建(?:一个)?项目|开始(?:一个)?新项目|做个项目)\s*[:：]?\s*(.*)$",
            r"^(?:new\s+project|create\s+(?:a\s+)?project|start\s+(?:a\s+)?new\s+project|help\s+me\s+start\s+a\s+new\s+project)\s*[:：]?\s*(.*)$",
            r"^(?:/evolve\s+new)\s+(.*)$",
        ]
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                goal = match.group(1).strip()
                goal = re.sub(r"^(?:for)\s+", "", goal, flags=re.IGNORECASE)
                return goal
        return None

    def _is_cancel(self, raw: str, compact: str) -> bool:
        values = {"取消", "退出", "停止", "cancel", "stop", "quit", "/evolve cancel", "/evolve stop"}
        return raw in values or compact in values

    def _is_status(self, compact: str) -> bool:
        phrases = [
            "项目列表", "查看项目", "所有项目", "列出项目", "看看项目", "有哪些项目",
            "project list", "list projects", "show projects", "project status", "status of projects",
        ]
        return any(p in compact for p in phrases)

    def _is_active(self, compact: str) -> bool:
        phrases = [
            "当前项目", "活跃项目", "现在跟进哪个项目", "现在在跟哪个项目",
            "active project", "current project", "which project is active",
        ]
        return any(p in compact for p in phrases)

    def _is_start(self, raw: str, compact: str) -> bool:
        phrases = [
            "evolve", "self-evolution", "项目进化", "项目演进", "开始进化", "继续进化",
            "开始跟进项目", "帮我跟进项目", "帮我管理项目", "project evolution",
            "help me evolve project", "manage my project", "continue evolve",
        ]
        if raw in {"/evolve", "evolve"}:
            return True
        return any(p in compact for p in phrases)

    def _is_help(self, compact: str) -> bool:
        phrases = ["怎么用", "使用方法", "帮助", "help", "usage", "how to use"]
        return any(p in compact for p in phrases)
