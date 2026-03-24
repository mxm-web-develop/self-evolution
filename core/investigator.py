# core/investigator.py
"""
调研模块

使用注入的搜索 Provider 执行调研，
并从案例库检索相似案例
"""

from typing import Dict, List, Any
from .case_library import CaseLibrary


class Investigator:
    """调研模块"""

    def __init__(self, search_provider, case_library: CaseLibrary):
        """
        Args:
            search_provider: 搜索 Provider（实现 ISearchProvider 接口）
            case_library: 案例库实例
        """
        self.search_provider = search_provider
        self.case_library = case_library

    def investigate(self, problem: str) -> Dict[str, Any]:
        """
        执行调研，返回调研报告

        Args:
            problem: 用户描述的问题

        Returns:
            调研报告 dict，包含：
            - problem: 原始问题
            - similar_cases: 案例库检索结果
            - web_findings: 网络搜索结果
            - recommendations: 建议列表
        """
        # 1. 检索相似案例
        similar_cases = self.case_library.search_similar(problem, limit=3)

        # 2. 网络调研
        try:
            search_results = self.search_provider.search(problem, count=5)
            web_findings = [r.to_dict() for r in search_results]
        except Exception as e:
            web_findings = [{"error": str(e), "results": []}]

        # 3. 组装调研报告
        report = {
            "problem": problem,
            "similar_cases": similar_cases,
            "web_findings": web_findings,
            "recommendations": self._generate_recommendations(similar_cases, web_findings)
        }

        return report

    def _generate_recommendations(
        self,
        cases: List[Dict],
        web_results: List[Dict]
    ) -> List[str]:
        """根据调研结果生成建议"""
        recs = []

        # 从相似案例提取建议
        for c in cases[:2]:
            title = c.get("title", "unknown")
            category = c.get("category", "")
            recs.append(f"参考案例【{category}】：{title}")

        # 从网络结果提取建议
        for r in web_results[:3]:
            if "error" not in r:
                title = r.get("title", "")
                if title:
                    recs.append(f"网络参考：{title}")

        if not recs:
            recs.append("未找到直接相关案例，建议深入调研")

        return recs
