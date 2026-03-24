# providers/__init__.py
"""
搜索 Provider 统一入口

用法：
    from providers import get_provider, search_with_fallback

    # 获取单个 Provider
    provider = get_provider("tavily")
    results = provider.search("Python 异步", count=5)

    # 带 fallback 的搜索
    results = search_with_fallback("query", preferred="tavily", fallback=["duckduckgo"])
"""

import os
from typing import List

from .base import BaseSearchProvider, SearchResult

__all__ = [
    "BaseSearchProvider",
    "SearchResult",
    "get_provider",
    "search_with_fallback",
]


def get_provider(name: str = None, config: dict = None) -> BaseSearchProvider:
    """
    获取搜索 Provider 实例

    Args:
        name: Provider 名称（tavily | brave | duckduckgo）
        config: Provider 配置字典（可选）

    Returns:
        BaseSearchProvider 实例

    Raises:
        ValueError: 未知的 Provider 名称
        ImportError: 依赖包未安装
    """
    name = name or os.environ.get("SEARCH_PROVIDER", "tavily")
    config = config or {}

    if name == "tavily":
        from .tavily import TavilySearchProvider
        api_key = config.get("api_key") or os.environ.get("TAVILY_API_KEY")
        return TavilySearchProvider(api_key=api_key)

    elif name == "brave":
        from .brave import BraveSearchProvider
        api_key = config.get("api_key") or os.environ.get("BRAVE_API_KEY")
        return BraveSearchProvider(api_key=api_key)

    elif name == "duckduckgo":
        from .duckduckgo import DuckDuckGoSearchProvider
        return DuckDuckGoSearchProvider()

    else:
        raise ValueError(f"未知的搜索 Provider：{name}，可用：tavily | brave | duckduckgo")


def search_with_fallback(
    query: str,
    count: int = 5,
    preferred: str = "tavily",
    fallback_providers: List[str] = None
) -> List[SearchResult]:
    """
    带 Fallback 的搜索

    策略：preferred → fallback[0] → fallback[1] → ...
    只要有一个 Provider 成功就返回结果

    Args:
        query: 搜索关键词
        count: 返回结果数量
        preferred: 首选 Provider
        fallback_providers: Fallback Provider 列表

    Returns:
        SearchResult 列表

    Raises:
        RuntimeError: 所有 Provider 均失败
    """
    fallback_providers = fallback_providers or ["duckduckgo"]
    all_providers = [preferred] + fallback_providers

    last_error = None
    for provider_name in all_providers:
        try:
            provider = get_provider(provider_name)
            results = provider.search(query, count)
            if results:
                return results
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"所有搜索 Provider 均失败。"
        f"已尝试：{all_providers}。"
        f"最后错误：{last_error}"
    )
