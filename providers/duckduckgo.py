# providers/duckduckgo.py
"""
DuckDuckGo 搜索 Provider（Fallback Provider）

安装：pip install duckduckgo-search
申请：无需 API Key（免费）
限制：速度限制，不适合高频调用

用法：
    from providers import get_provider
    provider = get_provider("duckduckgo")
    results = provider.search("Python async", count=5)
"""

from typing import List

from .base import BaseSearchProvider, SearchResult

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """
    DuckDuckGo 搜索 Provider

    无需 API Key，适合作为 Fallback 或免费场景。
    注意：有速度限制，不建议高频使用。
    """

    name = "duckduckgo"
    requires_api_key = False

    def __init__(self):
        """
        初始化 DuckDuckGo Provider

        Raises:
            ImportError: duckduckgo-search 未安装
        """
        if not DDGS_AVAILABLE:
            raise ImportError(
                "duckduckgo-search 未安装，请运行：pip install duckduckgo-search"
            )

    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """
        使用 DuckDuckGo 执行搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量

        Returns:
            SearchResult 列表
        """
        results = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=min(count, 20)):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo",
                    raw=item
                ))
        return results

    def fetch(self, url: str, max_chars: int = 5000) -> str:
        """
        抓取页面内容（使用 OpenClaw web_fetch）

        Args:
            url: 页面 URL
            max_chars: 最大字符数

        Returns:
            页面纯文本内容
        """
        from openclaw import web_fetch
        return web_fetch(url=url, maxChars=max_chars)
