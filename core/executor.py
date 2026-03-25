# core/executor.py
"""
执行模块

将已批准的方案拆解为子任务，通过 TaskExecutor 执行。
当前版本优先支持：
- 命令型执行；
- 无命令时生成执行任务卡（manual brief），保证闭环不断。
"""

from typing import Dict, List, Any
from .models import Task, Plan


class Executor:
    """执行模块"""

    def __init__(self, bridge):
        self.bridge = bridge

    def execute_plan(
        self,
        plan: Plan,
        task_executor
    ) -> Dict[str, Any]:
        subtasks = self._decompose(plan)

        results = []
        for task in subtasks:
            session_id = task_executor.spawn(
                task,
                context={"plan": plan.to_dict()}
            )
            result = task_executor.wait(session_id)
            results.append(result)

        return {
            "status": "completed",
            "subtask_results": results,
            "summary": self._summarize(results)
        }

    def _decompose(self, plan: Plan) -> List[Task]:
        resource = plan.resource_estimate or {}
        effort = resource.get("effort", "中")

        subtasks = [
            Task(
                task_id=f"sub-prep-{plan.plan_id}",
                title="准备工作",
                description=f"为方案 '{plan.title}' 做准备，包括范围确认、依赖检查、风险提醒等",
                task_type="execution",
                input_data={
                    "phase": "preparation",
                    "plan": plan.to_dict(),
                    "resource_estimate": resource,
                },
            )
        ]

        if effort == "低":
            subtasks.append(Task(
                task_id=f"sub-core-{plan.plan_id}",
                title="核心实现",
                description=f"执行方案 '{plan.title}' 的核心步骤",
                task_type="execution",
                input_data={
                    "phase": "core",
                    "plan": plan.to_dict(),
                },
            ))
        elif effort == "高":
            for stage in ["设计收口", "核心改造", "验证回归"]:
                subtasks.append(Task(
                    task_id=f"sub-{stage}-{plan.plan_id}",
                    title=f"{stage}",
                    description=f"执行方案 '{plan.title}' 的{stage}阶段",
                    task_type="execution",
                    input_data={
                        "phase": stage,
                        "plan": plan.to_dict(),
                    },
                ))
        else:
            for stage in ["关键实现", "验证收尾"]:
                subtasks.append(Task(
                    task_id=f"sub-{stage}-{plan.plan_id}",
                    title=f"{stage}",
                    description=f"执行方案 '{plan.title}' 的{stage}阶段",
                    task_type="execution",
                    input_data={
                        "phase": stage,
                        "plan": plan.to_dict(),
                    },
                ))

        subtasks.append(Task(
            task_id=f"sub-test-{plan.plan_id}",
            title="验证测试",
            description="验证执行结果，确认是否达到预期",
            task_type="execution",
            input_data={
                "phase": "verification",
                "plan": plan.to_dict(),
                "expected_outcomes": plan.expected_outcomes,
            },
        ))

        return subtasks

    def _summarize(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "无子任务执行"

        success_count = sum(
            1 for r in results
            if isinstance(r, dict) and r.get("status") == "success"
        )
        total = len(results)
        brief_count = sum(
            1 for r in results
            if isinstance(r, dict) and r.get("output", {}).get("mode") == "manual-brief"
        )

        if success_count == total:
            if brief_count == total:
                return f"✅ 已生成 {total}/{total} 个执行任务卡，待人工或 Agent 落地"
            if brief_count > 0:
                return f"✅ 完成 {success_count}/{total} 个子任务（含 {brief_count} 个任务卡）"
            return f"✅ 完成 {success_count}/{total} 个子任务"
        elif success_count > 0:
            return f"⚠️ 部分完成 {success_count}/{total} 个子任务"
        else:
            return f"❌ 全部 {total} 个子任务失败"
