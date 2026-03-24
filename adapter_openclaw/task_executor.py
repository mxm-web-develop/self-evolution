# adapter_openclaw/task_executor.py
"""
TaskExecutor — sessions_spawn 封装

通过 OpenClaw sessions_spawn 启动子代理执行任务
"""

import json
import time
from typing import Dict, Any

from openclaw import sessions_spawn, sessions_yield
from core.models import Task


class TaskExecutor:
    """通过 sessions_spawn 启动子代理执行任务"""

    def __init__(self, bridge: "OpenClawBridge"):
        self.bridge = bridge

    def spawn(self, task: Task, context: Dict[str, Any]) -> str:
        """
        启动子代理，返回 session_id

        Args:
            task: Task 对象
            context: 上下文数据（会传入子代理 Prompt）

        Returns:
            session_id 字符串
        """
        prompt = self._build_prompt(task, context)
        session_id = sessions_spawn(
            prompt=prompt,
            model="minimax-portal/MiniMax-M2.7",
            instruction="你是一个专业的项目进化助手。执行任务并返回结构化 JSON 结果。"
        )
        return session_id

    def wait(self, session_id: str, timeout_ms: int = 300000) -> Dict[str, Any]:
        """
        等待子代理完成并获取结果

        Args:
            session_id: spawn() 返回的 session_id
            timeout_ms: 超时毫秒数（默认 5 分钟）

        Returns:
            结果 dict，包含 status/output/error
        """
        result = sessions_yield(session_id, timeout=timeout_ms)
        return self._parse_result(result)

    def _build_prompt(self, task: Task, context: Dict[str, Any]) -> str:
        """构建子代理 Prompt"""
        return f"""
## 任务

**任务类型**：{task.task_type}
**任务标题**：{task.title}
**任务描述**：{task.description}

## 上下文

```json
{json.dumps(context, ensure_ascii=False, indent=2)}
```

## 要求

1. 仔细阅读任务描述和上下文
2. 执行任务，如果是代码任务请直接操作
3. 返回以下格式的 JSON（不要加 markdown 代码块包裹）：
{{
    "status": "success" | "failure",
    "output": {{...}},  // 任务的具体输出
    "error": "错误信息（如有）"
}}

不要返回除 JSON 以外的任何内容。
"""

    def _parse_result(self, raw_result) -> Dict[str, Any]:
        """
        解析 sessions_yield 返回的原始结果

        Args:
            raw_result: sessions_yield 返回的原始数据

        Returns:
            标准化结果 dict
        """
        # sessions_yield 可能返回多种格式，尝试解析
        if isinstance(raw_result, dict):
            # 已经是 dict，直接使用
            return raw_result
        elif isinstance(raw_result, str):
            # 是字符串，尝试 JSON 解析
            try:
                return json.loads(raw_result)
            except json.JSONDecodeError:
                return {
                    "status": "success",
                    "output": {"raw": raw_result},
                    "error": None
                }
        else:
            return {
                "status": "success",
                "output": {"raw": str(raw_result)},
                "error": None
            }
