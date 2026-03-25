# adapter_openclaw/task_executor.py
"""
TaskExecutor — 执行任务适配层

当前版本执行优先级：
1. 若任务自带 shell command，直接本地执行；
2. 否则优先尝试通过 `openclaw agent --local` 拉起真实 agent 执行；
3. 若真实执行不可用，则回退为 execution brief，保证闭环不断。

稳定性增强：
- 支持项目级 execution.timeout_ms
- 每个子任务都会落 execution result JSON
- agent 超时/失败时会清晰回退，不再长时间无反馈
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.models import Task


class TaskExecutor:
    """执行器（命令执行 + OpenClaw Agent + 任务卡回退）"""

    def __init__(self, bridge: "OpenClawBridge"):
        self.bridge = bridge
        self._results: Dict[str, Dict[str, Any]] = {}
        self._openclaw_bin = shutil.which("openclaw") or "/Users/mxm_pro/.npm-global/bin/openclaw"
        self._node_bin_dir = "/Users/mxm_pro/.local/share/fnm/aliases/default/bin"

    def spawn(self, task: Task, context: Dict[str, Any]) -> str:
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        result = self._run_task(task, context)
        self._results[execution_id] = result
        return execution_id

    def wait(self, session_id: str, timeout_ms: int = 300000) -> Dict[str, Any]:
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
            result = self._run_shell_commands(task, commands, context)
            self._write_execution_result(task, context, result)
            return result

        agent_result = self._run_via_openclaw_agent(task, context)
        if agent_result is not None:
            self._write_execution_result(task, context, agent_result)
            return agent_result

        fallback = self._write_manual_brief(task, context, note="真实 agent 执行不可用，已回退为任务卡。")
        self._write_execution_result(task, context, fallback)
        return fallback

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
        cwd = self._resolve_target_dir(context)
        timeout_seconds = max(30, self._resolve_timeout_ms(context) // 1000)

        for command in commands:
            try:
                completed = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                return {
                    "status": "failure",
                    "output": {"commands": outputs, "mode": "shell", "timeout_seconds": timeout_seconds},
                    "error": f"命令执行超时（>{timeout_seconds}s）：{command}",
                    "summary": f"❌ 执行超时：{task.title}",
                }

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
                    "output": {"commands": outputs, "mode": "shell"},
                    "error": completed.stderr.strip() or f"命令执行失败：{command}",
                    "summary": f"❌ 执行失败：{task.title}",
                }

        return {
            "status": "success",
            "output": {"commands": outputs, "mode": "shell"},
            "error": None,
            "summary": f"✅ 已执行命令型任务：{task.title}",
        }

    def _run_via_openclaw_agent(self, task: Task, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not Path(self._openclaw_bin).exists():
            return None

        prompt = self._build_agent_prompt(task, context)
        env = os.environ.copy()
        env["PATH"] = f"{self._node_bin_dir}:{env.get('PATH', '')}"
        cwd = self._resolve_target_dir(context) or str(self.bridge.projects_root.parent)
        timeout_seconds = max(60, self._resolve_timeout_ms(context) // 1000)

        command = [
            self._openclaw_bin,
            "agent",
            "--local",
            "--agent",
            "main",
            "--thinking",
            "low",
            "--json",
            "--timeout",
            str(timeout_seconds),
            "--message",
            prompt,
        ]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout_seconds + 20,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return self._write_manual_brief(
                task,
                context,
                note=f"真实 agent 执行超时（>{timeout_seconds}s），已自动回退为任务卡。",
            )
        except Exception as exc:
            return {
                "status": "failure",
                "output": {"mode": "openclaw-agent", "exception": str(exc)},
                "error": str(exc),
                "summary": f"❌ 真实 agent 执行启动失败：{task.title}",
            }

        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "").strip()
            if "requires Node" in stderr:
                return None
            return self._write_manual_brief(
                task,
                context,
                note=f"真实 agent 执行失败，已回退为任务卡。错误：{stderr or 'unknown'}",
            )

        parsed = self._parse_agent_json_output(completed.stdout)
        if parsed is None:
            return {
                "status": "success",
                "output": {
                    "mode": "openclaw-agent",
                    "raw": completed.stdout.strip(),
                },
                "error": None,
                "summary": f"✅ 真实 agent 已执行任务：{task.title}",
            }

        return {
            "status": parsed.get("status", "success"),
            "output": {
                "mode": "openclaw-agent",
                "agent_result": parsed,
            },
            "error": parsed.get("error"),
            "summary": parsed.get("summary") or f"✅ 真实 agent 已执行任务：{task.title}",
        }

    def _parse_agent_json_output(self, stdout: str) -> Optional[Dict[str, Any]]:
        text = (stdout or "").strip()
        if not text:
            return None

        try:
            outer = json.loads(text)
        except json.JSONDecodeError:
            return None

        payloads = outer.get("payloads")
        if not isinstance(payloads, list) or not payloads:
            return outer if isinstance(outer, dict) else None

        text_payload = payloads[0].get("text") if isinstance(payloads[0], dict) else None
        if not text_payload:
            return None

        try:
            return json.loads(text_payload)
        except json.JSONDecodeError:
            return {
                "status": "success",
                "summary": text_payload.strip(),
                "raw": text_payload,
            }

    def _resolve_target_dir(self, context: Dict[str, Any]) -> Optional[str]:
        plan = context.get("plan", {}) if isinstance(context, dict) else {}
        project_id = plan.get("project_id") or "current"
        project_dir = self.bridge.projects_root / project_id

        state_file = project_dir / "state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                real_path = data.get("context", {}).get("project_path")
                if real_path and Path(real_path).exists():
                    return str(Path(real_path))
            except Exception:
                pass

        if project_dir.exists():
            return str(project_dir)
        return None

    def _resolve_timeout_ms(self, context: Dict[str, Any]) -> int:
        plan = context.get("plan", {}) if isinstance(context, dict) else {}
        project_id = plan.get("project_id") or "current"
        config_file = self.bridge.projects_root / project_id / "config.yaml"
        default_timeout = 300000
        if not config_file.exists():
            return default_timeout

        try:
            lines = config_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            return default_timeout

        in_execution = False
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not line.startswith(" ") and stripped.startswith("execution:"):
                in_execution = True
                continue
            if in_execution and not line.startswith(" "):
                in_execution = False
            if in_execution and stripped.startswith("timeout_ms:"):
                raw = stripped.split(":", 1)[1].split("#", 1)[0].strip()
                try:
                    return int(raw)
                except Exception:
                    return default_timeout
        return default_timeout

    def _build_agent_prompt(self, task: Task, context: Dict[str, Any]) -> str:
        plan = context.get("plan", {}) if isinstance(context, dict) else {}
        target_dir = self._resolve_target_dir(context) or str(self.bridge.projects_root.parent)

        prompt = {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "target_dir": target_dir,
            "input_data": task.input_data or {},
            "plan": plan,
        }

        return f"""
你正在执行 self-evolution 的真实执行任务。

目标目录：{target_dir}
要求：
1. 只在目标目录及其必要上下文内工作；
2. 能实际落地就直接落地（允许读写文件、运行必要命令）；
3. 如果信息不足，至少产出一个清晰的 execution artifact（如 TODO、实现草稿、变更说明）；
4. 返回时只输出 JSON，不要输出 markdown 代码块。

输出 JSON 格式：
{{
  "status": "success" | "failure",
  "summary": "一句话总结",
  "files_changed": ["相对或绝对路径"],
  "commands_run": ["命令"],
  "notes": ["补充说明"],
  "error": null
}}

任务上下文：
{json.dumps(prompt, ensure_ascii=False, indent=2)}
""".strip()

    def _write_execution_result(self, task: Task, context: Dict[str, Any], result: Dict[str, Any]) -> None:
        plan = context.get("plan", {}) if isinstance(context, dict) else {}
        project_id = plan.get("project_id") or "current"
        project_dir = self.bridge.projects_root / project_id
        execution_dir = project_dir / "execution"
        execution_dir.mkdir(parents=True, exist_ok=True)
        result_file = execution_dir / f"{task.task_id}.result.json"
        payload = {
            "task": task.to_dict(),
            "context": context,
            "result": result,
        }
        result_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_manual_brief(self, task: Task, context: Dict[str, Any], note: str = "当前版本尚未接入真实 OpenClaw 子代理执行，因此先生成任务卡，供后续人工或 Agent 执行。") -> Dict[str, Any]:
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
            note,
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
