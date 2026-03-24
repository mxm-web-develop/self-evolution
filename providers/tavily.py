# providers/tavily.py
"""
Tavily 搜索 Provider（默认 Provider）

安装：pip install tavily-python
申请：https://tavily.com
免费额度：1000次/月

用法：
    from providers import get_provider
    provider = get_provider("tavily")
    results = provider.search("Python async", count=5)
"""

import os
from typing import List

from .base import BaseSearchProvider, SearchResult

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class TavilySearchProvider(BaseSearchProvider):
    """
    Tavily 搜索 Provider

    Tavily 是专为 AI 应用优化的搜索服务，
    返回结构化的搜索结果，适合作为默认 Provider。
    """

    name = "tavily"
    requires_api_key = True

    def __init__(self, api_key: str = None):
        """
        初始化 Tavily Provider

        Args:
            api_key: Tavily API Key，留空则从环境变量 TAVILY_API_KEY 读取

        Raises:
            ImportError: tavily-python 未安装
            ValueError: API Key 未设置
        """
        if not TAVILY_AVAILABLE:
            raise ImportError(
                "tavily-python 未安装，请运行：pip install tavily-python"
            )

        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API Key 未设置。"
                "请设置环境变量 TAVILY_API_KEY 或在配置文件中指定"
            )

        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """
        使用 Tavily 执行搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量（建议不超过10）

        Returns:
            SearchResult 列表
        """
        response = self.client.search(
            query=query,
            search_depth="basic",  # basic | advanced
            max_results=min(count, 10)
        )

        results = []
        for item in response.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source="tavily",
                raw=item
            ))

        return results

    def fetch(self, url: str, max_chars: int = 5000) -> str:
        """
        使用 Tavily Extract 抓取页面

        Args:
            url: 页面 URL
            max_chars: 最大字符数

        Returns:
            页面纯文本内容
        """
        response = self.client.extract(urls=[url])
        texts = []
        for result in response.get("results", []):
            raw = result.get("raw_content", "")
            if raw:
                texts.append(raw)

        full_text = "\n".join(texts)
        return full_text[:max_chars]
