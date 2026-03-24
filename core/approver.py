# core/approver.py
"""
审批模块

负责向人类发送审批请求，不做决策
"""

from typing import Optional, Dict, Any


class Approver:
    """审批模块（人类在环）"""

    def request_approval(
        self,
        plan_title: str,
        scores: Dict[str, Any],
        notifier,
        project_id: str = "current"
    ) -> None:
        """
        向人类发送审批请求

        Args:
            plan_title: 方案标题
            scores: 评分结果
            notifier: Notifier 实例（发送消息）
            project_id: 项目 ID
        """
        notifier.notify_approval_request(
            project_id=project_id,
            plan_title=plan_title,
            scores=scores
        )

    def parse_human_decision(self, response: str) -> Optional[bool]:
        """
        解析人类的决策

        Args:
            response: 用户输入的字符串

        Returns:
            True = 通过，False = 拒绝，None = 无效输入
        """
        if not response:
            return None

        response = str(response).lower().strip()

        approve_keywords = ["approve", "通过", "yes", "y", "好", "可以", "同意", "ok"]
        reject_keywords = ["reject", "拒绝", "no", "n", "不行", "否决", "不同意"]

        if any(kw in response for kw in approve_keywords):
            return True
        if any(kw in response for kw in reject_keywords):
            return False
        return None
