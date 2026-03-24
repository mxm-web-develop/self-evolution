# core/diagnose.py
"""
诊断引擎

基于规则的诊断，分析问题类型和根因
"""

from typing import Dict, Any


class DiagnoseEngine:
    """诊断引擎"""

    DIAGNOSE_TYPES = [
        "feature_request",
        "bug_fix",
        "optimization",
        "architecture",
        "unknown"
    ]

    # 关键词映射
    KEYWORD_MAP = {
        "feature_request": [
            "新功能", "需要", "希望", "想要", "feature",
            "增加", "添加", "支持", "实现"
        ],
        "bug_fix": [
            "bug", "错误", "修复", "问题", "异常", "崩溃",
            "不对", "坏了", "失效", "fails", "error"
        ],
        "optimization": [
            "慢", "优化", "性能", "卡顿", "延迟", "瓶颈",
            "提高", "提升", "加快", "slow", "optimize"
        ],
        "architecture": [
            "架构", "重构", "设计", "拆解", "解耦", "迁移",
            "重写", "清理", "refactor", "architecture"
        ]
    }

    def diagnose(self, investigation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析调研报告，输出诊断结果

        Args:
            investigation_report: 调研报告 dict

        Returns:
            诊断结果 dict，包含：
            - type: 问题类型
            - root_cause: 根因分析
            - priority: 优先级（1-10）
            - confidence: 置信度
        """
        problem = investigation_report.get("problem", "")
        diagnose_type = self._classify(problem)

        return {
            "type": diagnose_type,
            "root_cause": self._analyze_root_cause(problem, diagnose_type),
            "priority": self._estimate_priority(problem),
            "confidence": self._estimate_confidence(problem, investigation_report)
        }

    def _classify(self, problem: str) -> str:
        """根据关键词判断问题类型"""
        problem_lower = problem.lower()
        scores = {}

        for diag_type, keywords in self.KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw.lower() in problem_lower)
            scores[diag_type] = score

        # 选得分最高的类型
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "unknown"

    def _analyze_root_cause(self, problem: str, diag_type: str) -> str:
        """分析根因"""
        templates = {
            "feature_request": f"识别为功能需求类型，建议按需求流程处理：{problem[:50]}...",
            "bug_fix": f"识别为缺陷修复类型，需要定位问题根因：{problem[:50]}...",
            "optimization": f"识别为性能优化类型，需要分析瓶颈：{problem[:50]}...",
            "architecture": f"识别为架构调整类型，需要评估影响面：{problem[:50]}...",
            "unknown": f"无法自动分类，建议人工介入确认：{problem[:50]}..."
        }
        return templates.get(diag_type, templates["unknown"])

    def _estimate_priority(self, problem: str) -> int:
        """估算优先级（1=最低，10=最高）"""
        # 基于问题描述长度（越长通常越复杂）
        length_score = min(5, len(problem) // 50)
        # 基于关键词强度
        intensity_keywords = ["紧急", "重要", "严重", " critical", "urgent", "major"]
        intensity_score = sum(2 for kw in intensity_keywords if kw.lower() in problem.lower())
        return min(10, max(1, length_score + intensity_score + 3))

    def _estimate_confidence(self, problem: str, report: Dict[str, Any]) -> float:
        """估算诊断置信度"""
        # 有相似案例 → 高置信度
        cases = report.get("similar_cases", [])
        if cases:
            return 0.85
        # 有网络搜索结果 → 中置信度
        web = report.get("web_findings", [])
        if web and not any("error" in str(r) for r in web):
            return 0.7
        return 0.5
