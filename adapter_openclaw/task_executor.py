# adapter_openclaw/task_executor.py
"""
TaskExecutor — 执行任务适配层

当前版本优先保证：
1. 不依赖不存在的 OpenClaw Python SDK；
2. 在没有真实子代理接入时，也能产出可追踪的执行结果；
3. 若任务自带 shell command，则可以本地同步执行。
"""

from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, List

from core.models import Task


class TaskExecutor:
    """执行器（当前为同步/本地优先实现）"""

    def __init__(self, bridge: "OpenClawBridge"):
        self.bridge = bridge
        self._results: Dict[str, Dict[str, Any]] = {}

    def spawn(self, task: Task, context: Dict[str, Any]) -> str:
        """
        同步执行任务并返回 execution id。

        之所以保留 spawn/wait 形状，是为了和上层 Executor 接口兼容。
        """
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        result = self._run_task(task, context)
        self._results[execution_id] = result
        return execution_id

    def wait(self, session_id: str, timeout_ms: int = 300000) -> Dict[str, Any]:
        """返回已缓存的同步执行结果。"""
        return self._results.pop(
            session_id,
            {
                "status": "failure",
                "output": {},
                "error": f"未知执行会话：{session_id}",
                "summary": f"❌ 未找到执行结果：{session_id}",
            },
        )

    def _run_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        input_data = task.input_data or {}

        commands = self._collect_commands(input_data)
        if commands:
            return self._run_shell_commands(task, commands, context)

        return self._write_manual_brief(task, context)

    def _collect_commands(self, input_data: Dict[str, Any]) -> List[str]:
        commands: List[str] = []

        single = input_data.get("command")
        if isinstance(single, str) and single.strip():
            commands.append(single.strip())

        multi = input_data.get("commands")
        if isinstance(multi, list):
            for item in multi:
                if isinstance(item, str) and item.strip():
                    commands.append(item.strip())

        return commands

    def _run_shell_commands(self, task: Task, commands: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        outputs = []
        cwd = None
        plan = context.get("plan", {}) if isinstance(context, dict) else {}
        project_id = plan.get("project_id") or "current"
        project_dir = self.bridge.projects_root / project_id
        if project_dir.exists():
            cwd = str(project_dir)

        for command in commands:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300,
            )
            outputs.append(
                {
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout.strip(),
                    "stderr": completed.stderr.strip(),
                }
            )
            if completed.returncode != 0:
                return {
                    "status": "failure",
                    "output": {"commands": outputs},
                    "error": completed.stderr.strip() or f"命令执行失败：{command}",
                    "summary": f"❌ 执行失败：{task.title}",
                }

        return {
            "status": "success",
            "output": {"commands": outputs},
            "error": None,
            "summary": f"✅ 已执行命令型任务：{task.title}",
        }

    def _write_manual_brief(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        当没有真实可执行命令时，生成 execution brief，
        让闭环至少能沉淀成可追踪产物，而不是直接报错。
        """
        plan = context.get("plan", {}) if isinstance(context, dict) else {}
        project_id = plan.get("project_id") or "current"
        project_dir = self.bridge.projects_root / project_id
        execution_dir = project_dir / "execution"
        execution_dir.mkdir(parents=True, exist_ok=True)

        brief_file = execution_dir / f"{task.task_id}.md"
        brief = [
            f"# 执行任务卡：{task.title}",
            "",
            f"- 任务 ID：`{task.task_id}`",
            f"- 任务类型：`{task.task_type}`",
            f"- 描述：{task.description}",
            "",
            "## 输入数据",
            "```json",
            json.dumps(task.input_data or {}, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 上下文",
            "```json",
            json.dumps(context or {}, ensure_ascii=False, indent=2),
            "```",
            "",
            "## 说明",
            "当前版本尚未接入真实 OpenClaw 子代理执行，因此先生成任务卡，供后续人工或 Agent 执行。",
        ]
        brief_file.write_text("\n".join(brief), encoding="utf-8")

        return {
            "status": "success",
            "output": {
                "mode": "manual-brief",
                "brief_file": str(brief_file),
                "task": task.to_dict(),
            },
            "error": None,
            "summary": f"✅ 已生成执行任务卡：{task.title}",
        }
