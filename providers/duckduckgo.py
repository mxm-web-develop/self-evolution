# providers/duckduckgo.py
"""
DuckDuckGo 搜索 Provider（Fallback Provider）

优先兼容新版 `ddgs`，同时兼容旧包 `duckduckgo-search`。
"""

from typing import List

from .base import BaseSearchProvider, SearchResult

DDGS = None
_DDGS_IMPORT_ERROR = None

try:
    from ddgs import DDGS  # 新包
except ImportError as exc_new:
    try:
        from duckduckgo_search import DDGS  # 旧包兼容
    except ImportError as exc_old:
        _DDGS_IMPORT_ERROR = exc_old
        DDGS = None

DDGS_AVAILABLE = DDGS is not None


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """DuckDuckGo 搜索 Provider"""

    name = "duckduckgo"
    requires_api_key = False

    def __init__(self):
        if not DDGS_AVAILABLE:
            raise ImportError(
                "DuckDuckGo 搜索依赖未安装，请运行：pip install ddgs"
            ) from _DDGS_IMPORT_ERROR

    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        results = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=min(count, 20)):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo",
                    raw=item,
                ))
        return results

    def fetch(self, url: str, max_chars: int = 5000) -> str:
        try:
            from openclaw import web_fetch
            return web_fetch(url=url, maxChars=max_chars)
        except ImportError:
            return f"[页面抓取暂不可用，请在 OpenClaw 环境中使用：{url}]"
