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

    def investigate(
        self,
        problem: str,
        project_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        执行调研，返回调研报告

        Args:
            problem: 用户描述的问题
            project_context: 项目上下文（可选，用于优化搜索查询）
        """
        project_context = project_context or {}
        ctx = project_context

        # 1. 检索相似案例
        similar_cases = self.case_library.search_similar(problem, limit=3)

        # 2. 优化搜索查询（基于项目上下文）
        search_query = self._build_search_query(problem, ctx)
        tech_stack = ctx.get("tech_stack", {})
        ts = tech_stack.get("frontend", "") if isinstance(tech_stack, dict) else str(tech_stack)

        # 3. 网络调研
        try:
            search_results = self.search_provider.search(search_query, count=5)
            web_findings = [r.to_dict() for r in search_results]
        except Exception as e:
            web_findings = [{"error": str(e), "results": []}]

        # 4. 组装调研报告
        report = {
            "problem": problem,
            "search_query_used": search_query,
            "tech_stack": ts,
            "similar_cases": similar_cases,
            "web_findings": web_findings,
            "recommendations": self._generate_recommendations(similar_cases, web_findings, ctx)
        }

        return report

    def _build_search_query(self, problem: str, ctx: Dict[str, Any]) -> str:
        """根据项目上下文构建更有针对性的搜索查询"""
        parts = [problem]
        goals = ctx.get("user_goals", "")
        benchmarks = ctx.get("competitor_benchmarks", "")
        ts = ctx.get("tech_stack", {})
        ts_str = ts.get("frontend", "") if isinstance(ts, dict) else str(ts)

        # 从 user_goals 中提取项目类型
        if "个人网站" in goals or "作品集" in goals or "portfolio" in goals.lower():
            parts.append("个人网站 portfolio")
        if "AI" in goals or "ai" in goals.lower():
            parts.append("AI developer portfolio")

        # 从技术栈补充搜索上下文
        tech_context = {
            "react": "React website",
            "next.js": "Next.js website",
            "vue": "Vue website",
            "vite": "Vite build optimization",
            "typescript": "TypeScript website",
        }
        for kw, context in tech_context.items():
            if kw.lower() in ts_str.lower():
                parts.append(context)

        # 从 competitor_benchmarks 提取标杆案例关键词
        if "Brittany Chiang" in benchmarks:
            parts.append("Brittany Chiang portfolio design")
        if "Felix Yseault" in benchmarks or "brutalist" in benchmarks.lower():
            parts.append("brutalist portfolio design")

        return " | ".join(parts)

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
        web_results: List[Dict],
        ctx: Dict[str, Any]
    ) -> List[str]:
        """根据调研结果 + 项目上下文生成建议"""
        recs = []

        # 从相似案例提取建议
        for c in cases[:2]:
            title = c.get("title", "unknown")
            category = c.get("category", "")
            recs.append(f"参考案例【{category}】：{title}")

        # 从网络结果提取建议（过滤无关结果）
        for r in web_results[:3]:
            if "error" not in r:
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                # 过滤明显不相关的结果
                skip_terms = ["SQL", "数据库", "sql", "database", "mysql", "postgresql"]
                if title and not any(term in title for term in skip_terms):
                    recs.append(f"网络参考：{title}")

        if not recs:
            recs.append("未找到直接相关案例，建议基于项目上下文和竞品分析进行改进")

        return recs
