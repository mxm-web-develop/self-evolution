# core/executor.py
"""
执行模块

将已批准的方案拆解为子任务，通过子代理执行
"""

from typing import Dict, List, Any
from .models import Task, Plan


class Executor:
    """执行模块"""

    def __init__(self, bridge):
        """
        Args:
            bridge: OpenClawBridge 实例（用于获取 TaskExecutor）
        """
        self.bridge = bridge

    def execute_plan(
        self,
        plan: Plan,
        task_executor
    ) -> Dict[str, Any]:
        """
        执行已批准的方案

        Args:
            plan: Plan 对象
            task_executor: TaskExecutor 实例

        Returns:
            执行结果 dict：
            - status: 执行状态
            - subtask_results: 各子任务结果
            - summary: 执行摘要
        """
        # 拆解为子任务
        subtasks = self._decompose(plan)

        results = []
        for task in subtasks:
            # 启动子代理执行
            session_id = task_executor.spawn(
                task,
                context={"plan": plan.to_dict()}
            )
            # 等待结果
            result = task_executor.wait(session_id)
            results.append(result)

        return {
            "status": "completed",
            "subtask_results": results,
            "summary": self._summarize(results)
        }

    def _decompose(self, plan: Plan) -> List[Task]:
        """
        将方案拆解为可执行的子任务

        Args:
            plan: Plan 对象

        Returns:
            Task 对象列表
        """
        plan_dict = plan.to_dict()
        resource = plan.resource_estimate
        days = resource.get("days", 3)
        people = resource.get("people", 1)

        subtasks = []

        # 任务 1：准备工作
        subtasks.append(Task(
            task_id=f"sub-prep-{plan.plan_id}",
            title="准备工作",
            description=f"为方案 '{plan.title}' 做准备，包括环境搭建、依赖安装、代码审查等",
            task_type="execution",
            input_data={
                "phase": "preparation",
                "plan": plan_dict,
                "resources": resource
            }
        ))

        # 任务 2：核心执行（根据工时调整）
        if days <= 2:
            # 短期方案：一步完成
            subtasks.append(Task(
                task_id=f"sub-core-{plan.plan_id}",
                title="核心实现",
                description=f"执行方案 '{plan.title}' 的核心步骤",
                task_type="execution",
                input_data={
                    "phase": "core",
                    "plan": plan_dict
                }
            ))
        else:
            # 长期方案：分阶段
            for day_phase in range(1, min(days, 4)):
                subtasks.append(Task(
                    task_id=f"sub-phase-{day_phase}-{plan.plan_id}",
                    title=f"核心实现（第{day_phase}阶段）",
                    description=f"执行方案 '{plan.title}' 第{day_phase}阶段",
                    task_type="execution",
                    input_data={
                        "phase": f"core_phase_{day_phase}",
                        "plan": plan_dict
                    }
                ))

        # 任务 3：验证测试
        subtasks.append(Task(
            task_id=f"sub-test-{plan.plan_id}",
            title="验证测试",
            description=f"验证执行结果，确认为预期效果",
            task_type="execution",
            input_data={
                "phase": "verification",
                "plan": plan_dict,
                "expected_outcomes": plan.expected_outcomes
            }
        ))

        return subtasks

    def _summarize(self, results: List[Dict[str, Any]]) -> str:
        """汇总执行结果"""
        if not results:
            return "无子任务执行"

        success_count = sum(
            1 for r in results
            if isinstance(r, dict) and r.get("status") == "success"
        )
        total = len(results)

        if success_count == total:
            return f"✅ 完成 {success_count}/{total} 个子任务"
        elif success_count > 0:
            return f"⚠️ 部分完成 {success_count}/{total} 个子任务"
        else:
            return f"❌ 全部 {total} 个子任务失败"
