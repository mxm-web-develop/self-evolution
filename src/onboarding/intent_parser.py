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
    analyze_problem: Optional[str] = None


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

        # 分析/诊断类意图（优先级较高）
        if self._is_analyze(compact):
            problem = self._extract_analyze_problem(raw)
            return ParsedIntent(
                kind="analyze",
                command=f"/evolve analyze",
                confidence=0.88,
                analyze_problem=problem or raw
            )

        # 审批/执行意图（优先于 plan，避免“执行方案A”被误判成“生成方案”）
        if self._is_approve(compact) or self._is_execute(compact):
            plan_id = self._extract_plan_id_from_response(raw)
            return ParsedIntent(
                kind="execute",
                command="/evolve approve" if self._is_approve(compact) else "/evolve execute",
                confidence=0.9,
                analyze_problem=plan_id
            )

        # 方案/规划类意图（优先级高，优先于 new_project 检测）
        if self._is_plan(compact):
            problem = self._extract_plan_problem(raw)
            return ParsedIntent(
                kind="plan",
                command="/evolve plan",
                confidence=0.88,
                analyze_problem=problem
            )

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
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_new_project_goal(self, text: str) -> Optional[str]:
        patterns = [
            r"^(?:帮我|给我|想要|我要)?\s*(?:新项目|新建(?:一个)?项目|创建(?:一个)?项目|开始(?:一个)?新项目|做个项目)\s*[:：]?\s*(.*)$",
            r"^(?:new\s+project|create\s+(?:a\s+)?project|start\s+(?:a\s+)?new\s+project)\s*[:：]?\s*(.*)$",
        ]
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                goal = match.group(1).strip()
                goal = re.sub(r"^(?:for)\s+", "", goal, flags=re.IGNORECASE)
                return goal
        return None

    def _extract_analyze_problem(self, text: str) -> Optional[str]:
        """从分析意图文本中提取核心问题描述。"""
        text = text.strip()
        # 按长度降序排列，确保"帮我诊断"优先于"诊断"匹配
        prefixes = sorted([
            # 英文长词优先
            "help me analyze", "run an analysis on",
            "analyze", "diagnose", "research", "investigate",
            # 中文四字以上组合
            "帮我诊断", "帮我分析", "帮我研究", "帮我调研",
            "分析一下", "诊断一下", "研究一下", "调研一下", "考察一下",
            # 中文两字动词放最后
            "诊断", "分析", "研究", "调研", "考察",
        ], key=len, reverse=True)

        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                rest = text[len(prefix):].strip("：: ").strip()
                if rest:
                    return rest
        return None

    def _is_cancel(self, raw: str, compact: str) -> bool:
        values = {"取消", "退出", "停止", "cancel", "stop", "quit", "/evolve cancel", "/evolve stop"}
        return raw in values or compact in values

    def _is_status(self, compact: str) -> bool:
        phrases = [
            "项目列表", "查看项目", "所有项目", "列出项目", "看看项目", "有哪些项目",
            "project list", "list projects", "show projects",
        ]
        return any(p in compact for p in phrases)

    def _is_active(self, compact: str) -> bool:
        phrases = [
            "当前项目", "活跃项目", "现在跟进哪个项目",
            "active project", "current project", "which project is active",
        ]
        return any(p in compact for p in phrases)

    def _is_analyze(self, compact: str) -> bool:
        analyze_phrases = [
            "分析", "诊断", "调研", "研究", "考察",
            "帮我分析", "帮我诊断", "分析一下", "诊断一下",
            "看看问题", "排查问题", "查找问题", "看看哪里",
            "优化方向", "优化建议", "改进建议", "提升建议",
            "analyze", "diagnose", "research", "investigate",
            "help me analyze", "run an analysis", "do a diagnosis",
            "look into", "check on", "audit",
            "优化这个", "改善这个", "改进项目",
        ]
        return any(p in compact for p in analyze_phrases)

    def _is_start(self, raw: str, compact: str) -> bool:
        phrases = [
            "evolve", "self-evolution", "项目进化", "项目演进",
            "开始进化", "继续进化", "开始跟进项目",
            "help me evolve", "continue evolve",
        ]
        if raw in {"/evolve", "evolve"}:
            return True
        return any(p in compact for p in phrases)

    def _is_help(self, compact: str) -> bool:
        phrases = ["怎么用", "使用方法", "帮助", "help", "usage", "how to use"]
        return any(p in compact for p in phrases)

    def _is_plan(self, compact: str) -> bool:
        plan_phrases = [
            "生成方案", "制定方案", "规划方案", "帮我规划", "规划一下",
            "制定计划", "做计划", "方案", "有什么方案", "候选方案",
            "如何解决", "怎么解决", "解决方案有哪些",
            "下一步做什么", "下一步是什么", "下一步我应该",
            "make a plan", "generate plan", "create a plan", "make plans",
            "give me options", "what are my options", "propose solutions",
            "what should i do", "advice me", "建议怎么做",
        ]
        return any(p in compact for p in plan_phrases)

    def _is_approve(self, compact: str) -> bool:
        phrases = [
            "批准", "通过", "approve", "ok", "好", "可以", "同意", "执行",
            "采纳", "就用这个", "就这个", "选a", "选b", "选c",
            "执行方案", "开始执行",
        ]
        return any(p in compact for p in phrases)

    def _is_execute(self, compact: str) -> bool:
        phrases = [
            "开始执行", "run it", "do it", "go ahead", "let's go",
        ]
        return any(p in compact for p in phrases)

    def _extract_plan_id_from_response(self, text: str) -> Optional[str]:
        """从审批/执行回复中提取 plan ID。"""
        match = re.search(r"plan-([a-f0-9]{8})", text, re.IGNORECASE)
        if match:
            return f"plan-{match.group(1)}"
        # 方案 A / 方案B / plan A 等
        plan_labels = {
            "方案a": "plan-a", "方案b": "plan-b", "方案c": "plan-c",
            "plan a": "plan-a", "plan b": "plan-b", "plan c": "plan-c",
            "a方案": "plan-a", "b方案": "plan-b", "c方案": "plan-c",
        }
        for label, plan_id in plan_labels.items():
            if label in text.lower():
                return plan_id
        return None

    def _extract_plan_problem(self, text: str) -> Optional[str]:
        """从规划意图文本中提取问题/目标描述（可选）。"""
        text = text.strip()
        prefixes = sorted([
            "帮我规划", "生成方案", "制定方案", "规划方案", "规划一下",
            "制定计划", "做计划", "方案是什么", "有什么方案",
            "如何解决", "怎么解决", "解决方案",
            "make a plan", "generate plan", "create a plan",
            "give me options", "what are my options", "propose solutions",
            "what should i do", "建议怎么做", "下一步是什么",
        ], key=len, reverse=True)
        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                rest = text[len(prefix):].strip("：: ").strip()
                return rest if rest else None
        return None
