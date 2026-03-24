# providers/base.py
"""
搜索 Provider 接口定义
所有 Provider 必须实现这些抽象方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class SearchResult:
    """
    统一的搜索结果格式

    Attributes:
        title: 结果标题
        url: 结果链接
        snippet: 结果摘要
        source: 来源 Provider 名称
        raw: 原始响应（Provider 特定）
    """
    title: str
    url: str
    snippet: str
    source: str = ""
    raw: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source
        }


class BaseSearchProvider(ABC):
    """
    搜索 Provider 抽象基类

    所有搜索 Provider 必须继承此类并实现：
    - search(): 执行关键词搜索
    - fetch(): 抓取页面内容

    可选覆盖：
    - health_check(): 健康检查
    """

    name: str = "base"
    """Provider 名称（唯一标识）"""

    requires_api_key: bool = False
    """是否需要 API Key"""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"

    @abstractmethod
    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """
        执行关键词搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量（默认5，最大不超过20）

        Returns:
            SearchResult 列表，按相关性排序

        Raises:
            Exception: 搜索失败时抛出具体异常
        """
        ...

    @abstractmethod
    def fetch(self, url: str, max_chars: int = 5000) -> str:
        """
        抓取页面正文内容

        Args:
            url: 页面 URL（必须是 http/https）
            max_chars: 最大返回字符数（默认5000）

        Returns:
            页面纯文本内容（去 HTML 标签）

        Raises:
            Exception: 抓取失败时抛出具体异常
        """
        ...

    def health_check(self) -> bool:
        """
        健康检查

        默认行为：执行一次 search("test", count=1)
        子类可覆盖实现更精确的检查

        Returns:
            True = 健康可用，False = 不可用
        """
        try:
            results = self.search("test", count=1)
            return len(results) >= 0  # 只要不抛异常就认为健康
        except Exception:
            return False

    def search_with_retry(
        self,
        query: str,
        count: int = 5,
        retries: int = 2
    ) -> List[SearchResult]:
        """
        带重试的搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量
            retries: 重试次数

        Returns:
            SearchResult 列表
        """
        last_error = None
        for attempt in range(retries + 1):
            try:
                return self.search(query, count)
            except Exception as e:
                last_error = e
                continue
        raise last_error
