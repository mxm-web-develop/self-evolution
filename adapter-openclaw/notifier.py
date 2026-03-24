# adapter-openclaw/notifier.py
"""
Notifier — 消息通知封装

封装 OpenClaw message 工具，向用户发送通知
"""

from typing import Optional

try:
    from openclaw import message as openclaw_message
    OPENCLAW_MESSAGE_AVAILABLE = True
except ImportError:
    OPENCLAW_MESSAGE_AVAILABLE = False


class Notifier:
    """封装 OpenClaw message 工具"""

    def __init__(self, default_channel: str = "webchat"):
        """
        Args:
            default_channel: 默认通知渠道
        """
        self.default_channel = default_channel

    def notify_user(
        self,
        text: str,
        channel: Optional[str] = None,
        target: Optional[str] = None
    ) -> None:
        """
        向用户发送通知

        Args:
            text: 通知文本
            channel: 渠道（webchat/discord 等）
            target: 接收目标
        """
        if not OPENCLAW_MESSAGE_AVAILABLE:
            print(f"[Notifier] {text}")
            return

        channel = channel or self.default_channel

        try:
            openclaw_message(
                action="send",
                channel=channel,
                target=target or "main",
                message=text
            )
        except Exception as e:
            print(f"[Notifier] 发送失败：{e}，降级为打印：{text}")

    def notify_approval_request(
        self,
        project_id: str,
        plan_title: str,
        scores: dict
    ) -> None:
        """
        发送审批请求

        Args:
            project_id: 项目 ID
            plan_title: 方案标题
            scores: 评分结果
        """
        text = self._format_approval_request(project_id, plan_title, scores)
        self.notify_user(text)

    def _format_approval_request(
        self,
        project_id: str,
        plan_title: str,
        scores: dict
    ) -> str:
        """格式化审批请求消息"""
        emoji_scores = []
        final = scores.get("final", "N/A")
        if isinstance(final, (int, float)):
            if final >= 7:
                emoji = "🟢"
            elif final >= 5:
                emoji = "🟡"
            else:
                emoji = "🔴"
        else:
            emoji = "⚪"

        lines = [
            f"📋 **审批请求**",
            "",
            f"**项目**：{project_id}",
            f"**方案**：{plan_title}",
            "",
            "**评分结果**：",
            f"  - 业务价值：{scores.get('business', 'N/A')}",
            f"  - 技术可行性：{scores.get('technical', 'N/A')}",
            f"  - 用户体验：{scores.get('ux', 'N/A')}",
            f"  - **{emoji} 总分：{final}**",
            "",
            f"**建议**：{scores.get('recommendation', 'N/A')}",
            "",
            "---",
            "请回复以下之一进行审批：",
            "  ✅ `Approve` / `通过` — 批准执行",
            "  ❌ `Reject` / `拒绝` — 拒绝方案",
            "  🔄 `Revise` / `修改` — 说明修改意见"
        ]

        return "\n".join(lines)

    def notify_phase_complete(
        self,
        project_id: str,
        phase: str,
        summary: str = ""
    ) -> None:
        """通知阶段完成"""
        emoji_map = {
            "investigating": "🔍",
            "diagnosing": "🩺",
            "planning": "📝",
            "critiquing": "📊",
            "approving": "✅",
            "executing": "🚀",
            "learning": "📚"
        }
        emoji = emoji_map.get(phase, "📌")
        text = f"{emoji} **{phase}** 阶段完成"
        if summary:
            text += f"\n\n{summary}"
        self.notify_user(text)

    def notify_error(
        self,
        project_id: str,
        phase: str,
        error: str
    ) -> None:
        """通知错误"""
        text = (
            f"❌ **错误**\n\n"
            f"项目：{project_id}\n"
            f"阶段：{phase}\n"
            f"错误：{error}"
        )
        self.notify_user(text)
