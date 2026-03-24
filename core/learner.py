# core/learner.py
"""
学习回写模块

从执行结果中提取经验，生成案例存入案例库
"""

from typing import Dict, Optional, Any
from .models import Case, Plan
from datetime import datetime


class Learner:
    """学习回写模块"""

    def __init__(self, case_library):
        """
        Args:
            case_library: CaseLibrary 实例
        """
        self.case_library = case_library

    def learn_from_execution(
        self,
        plan: Plan,
        execution_result: Dict[str, Any],
        diagnosis: Dict[str, Any]
    ) -> Optional[Case]:
        """
        从执行结果中学习，生成案例

        Args:
            plan: 执行的方案
            execution_result: 执行结果
            diagnosis: 诊断结果

        Returns:
            新建的 Case 对象，或 None（不值得记录）
        """
        if not self._should_learn(plan, execution_result):
            return None

        case = Case(
            case_id=f"case-{plan.plan_id}",
            category=diagnosis.get("type", "unknown"),
            tags=self._extract_tags(plan, diagnosis),
            problem=plan.description,
            investigation_summary="",
            diagnosis=diagnosis.get("root_cause", ""),
            plan_executed=plan.title,
            result=execution_result.get("summary", ""),
            lessons=self._extract_lessons(plan, execution_result),
            outcome=self._determine_outcome(execution_result),
            created_at=self._now()
        )

        self.case_library.add_case(case)
        return case

    def _should_learn(self, plan: Plan, result: Dict[str, Any]) -> bool:
        """
        判断是否值得记录为案例

        当前策略：所有执行都值得记录
        后续可精细化：仅成功案例，或仅失败但有教训的案例
        """
        # 所有执行都值得记录
        return True

    def _extract_tags(self, plan: Plan, diagnosis: Dict[str, Any]) -> list:
        """从方案和诊断中提取标签"""
        tags = [diagnosis.get("type", "unknown")]

        # 从优势中提取标签
        for pro in plan.pros[:2]:
            # 取前10个字符作为标签
            tag = pro.lower().strip()[:10]
            if tag and tag not in tags:
                tags.append(tag)

        # 从预期结果中提取标签
        for outcome in plan.expected_outcomes[:1]:
            tag = outcome.lower().strip()[:10]
            if tag and tag not in tags:
                tags.append(tag)

        return tags

    def _extract_lessons(self, plan: Plan, result: Dict[str, Any]) -> str:
        """从执行结果中提取教训"""
        summary = result.get("summary", "未知")
        risks = plan.risks

        lessons = []
        lessons.append(f"执行结果：{summary}")

        if risks:
            lessons.append(f"已知风险：{'、'.join(risks[:2])}")

        return "；".join(lessons)

    def _determine_outcome(self, result: Dict[str, Any]) -> str:
        """判断执行结果"""
        summary = result.get("summary", "").lower()

        if "✅" in summary or "完成" in summary and "失败" not in summary:
            if "部分" in summary:
                return "partial"
            return "success"
        elif "❌" in summary or "失败" in summary:
            return "failure"
        elif "⚠️" in summary:
            return "partial"

        return "partial"

    def _now(self) -> str:
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M")
