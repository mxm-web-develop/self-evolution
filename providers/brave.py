# providers/brave.py
"""
Brave Search Provider（备选 Provider）

安装：pip install brave-search
申请：https://brave.com/search/api/
免费额度：2000次/月

用法：
    from providers import get_provider
    provider = get_provider("brave")
    results = provider.search("Python async", count=5)
"""

import os
from typing import List

from .base import BaseSearchProvider, SearchResult

try:
    from brave_search import BraveSearch
    BRAVE_AVAILABLE = True
except ImportError:
    BRAVE_AVAILABLE = False


class BraveSearchProvider(BaseSearchProvider):
    """
    Brave Search Provider

    Brave 是隐私友好的搜索引擎，
    提供干净的搜索结果，无广告干扰。
    """

    name = "brave"
    requires_api_key = True

    def __init__(self, api_key: str = None):
        """
        初始化 Brave Search Provider

        Args:
            api_key: Brave API Key，留空则从环境变量 BRAVE_API_KEY 读取

        Raises:
            ImportError: brave-search 未安装
            ValueError: API Key 未设置
        """
        if not BRAVE_AVAILABLE:
            raise ImportError(
                "brave-search 未安装，请运行：pip install brave-search"
            )

        self.api_key = api_key or os.environ.get("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Brave API Key 未设置。"
                "请设置环境变量 BRAVE_API_KEY 或在配置文件中指定"
            )

        self.client = BraveSearch(api_key=self.api_key)

    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """
        使用 Brave Search 执行搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量

        Returns:
            SearchResult 列表
        """
        response = self.client.search(q=query, count=min(count, 20))
        results = []

        for item in response.get("web", {}).get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                source="brave",
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
        # Brave Search API 不提供页面抓取，使用 OpenClaw web_fetch
        from openclaw import web_fetch
        return web_fetch(url=url, maxChars=max_chars)
