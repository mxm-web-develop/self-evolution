# 搜索 Provider 设计

## 1. 概述

搜索层采用**策略模式**，支持多 Provider 插拔。通过配置文件选择 Provider，支持 fallback 链。

### Provider 列表

| Provider | 默认 | API 费用 | 说明 |
|---|---|---|---|
| Tavily | ✅ 默认 | 有免费额度 | AI 优化的搜索结果 |
| Brave Search | 备选1 | 有免费额度 | 隐私友好的搜索 |
| DuckDuckGo | Fallback | 免费 | 无需 API Key |

### 策略

- **默认**：Tavily
- **Fallback**：Tavily 失败 → Brave → DuckDuckGo
- 所有 Provider 均实现统一接口，调用方无感知

---

## 2. 接口定义

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class SearchResult:
    """统一的搜索结果格式"""
    def __init__(self, title: str, url: str, snippet: str,
                 source: str = "", raw: Optional[Dict] = None):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.raw = raw or {}

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source
        }

class BaseSearchProvider(ABC):
    """搜索 Provider 基类"""

    name: str = "base"
    requires_api_key: bool = False

    @abstractmethod
    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量（默认5）

        Returns:
            SearchResult 列表
        """
        pass

    @abstractmethod
    def fetch(self, url: str, max_chars: int = 5000) -> str:
        """
        抓取页面内容

        Args:
            url: 页面 URL
            max_chars: 最大字符数

        Returns:
            页面文本内容
        """
        pass

    def health_check(self) -> bool:
        """健康检查"""
        try:
            self.search("test", count=1)
            return True
        except Exception:
            return False
```

---

## 3. Tavily Provider（默认）

### 依赖

```bash
pip install tavily-python
```

### 环境变量

```bash
TAVILY_API_KEY=tvly-xxxxx
```

### 实现

```python
# providers/tavily.py
import os
from typing import List
from .base import BaseSearchProvider, SearchResult

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

class TavilySearchProvider(BaseSearchProvider):
    """Tavily 搜索 Provider（默认）"""

    name = "tavily"
    requires_api_key = True

    def __init__(self, api_key: str = None):
        if not TAVILY_AVAILABLE:
            raise ImportError("tavily-python 未安装：pip install tavily-python")
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Tavily API Key 未设置，请设置 TAVILY_API_KEY 环境变量")
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        response = self.client.search(
            query=query,
            search_depth="basic",
            max_results=count
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
        response = self.client.extract(urls=[url])
        texts = []
        for result in response.get("results", []):
            texts.append(result.get("raw_content", ""))
        return "\n".join(texts)[:max_chars]
```

---

## 4. Brave Search Provider（备选1）

### 依赖

```bash
pip install brave-search
```

### 环境变量

```bash
BRAVE_API_KEY=BSA...
```

### 实现

```python
# providers/brave.py
import os
from typing import List
from .base import BaseSearchProvider, SearchResult

try:
    from brave_search import BraveSearch
    BRAVE_AVAILABLE = True
except ImportError:
    BRAVE_AVAILABLE = False

class BraveSearchProvider(BaseSearchProvider):
    """Brave Search Provider"""

    name = "brave"
    requires_api_key = True

    def __init__(self, api_key: str = None):
        if not BRAVE_AVAILABLE:
            raise ImportError("brave-search 未安装：pip install brave-search")
        self.api_key = api_key or os.environ.get("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError("Brave API Key 未设置，请设置 BRAVE_API_KEY 环境变量")
        self.client = BraveSearch(api_key=self.api_key)

    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        response = self.client.search(q=query, count=count)
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
        # Brave 不提供直接 fetch，使用 web_fetch
        from openclaw import web_fetch
        return web_fetch(url=url, maxChars=max_chars)
```

---

## 5. DuckDuckGo Provider（Fallback）

### 依赖

```bash
pip install duckduckgo-search
```

### 环境变量

无需 API Key

### 实现

```python
# providers/duckduckgo.py
from typing import List
from .base import BaseSearchProvider, SearchResult

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

class DuckDuckGoSearchProvider(BaseSearchProvider):
    """DuckDuckGo 搜索 Provider（无需 API Key）"""

    name = "duckduckgo"
    requires_api_key = False

    def __init__(self):
        if not DDGS_AVAILABLE:
            raise ImportError("duckduckgo-search 未安装：pip install duckduckgo-search")

    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        results = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=count):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo",
                    raw=item
                ))
        return results

    def fetch(self, url: str, max_chars: int = 5000) -> str:
        from openclaw import web_fetch
        return web_fetch(url=url, maxChars=max_chars)
```

---

## 6. 统一入口（Provider 工厂）

```python
# providers/__init__.py
import os
from typing import List, Optional
from .base import BaseSearchProvider, SearchResult

# 延迟导入避免循环依赖
_providers = {}

def get_provider(name: str = None, config: dict = None) -> BaseSearchProvider:
    """
    获取搜索 Provider 实例

    Args:
        name: Provider 名称（tavily | brave | duckduckgo）
        config: Provider 配置（API Key 等）

    Returns:
        BaseSearchProvider 实例
    """
    name = name or os.environ.get("SEARCH_PROVIDER", "tavily")

    if name == "tavily":
        from .tavily import TavilySearchProvider
        api_key = (config or {}).get("api_key") or os.environ.get("TAVILY_API_KEY")
        return TavilySearchProvider(api_key=api_key)

    elif name == "brave":
        from .brave import BraveSearchProvider
        api_key = (config or {}).get("api_key") or os.environ.get("BRAVE_API_KEY")
        return BraveSearchProvider(api_key=api_key)

    elif name == "duckduckgo":
        from .duckduckgo import DuckDuckGoSearchProvider
        return DuckDuckGoSearchProvider()

    else:
        raise ValueError(f"未知的搜索 Provider：{name}")


def search_with_fallback(
    query: str,
    count: int = 5,
    preferred: str = "tavily",
    fallback_providers: List[str] = None
) -> List[SearchResult]:
    """
    带 Fallback 的搜索

    策略：preferred → fallback[0] → fallback[1] → ...
    只要有一个 Provider 成功就返回
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

    # 全部失败
    raise RuntimeError(
        f"所有搜索 Provider 均失败。"
        f"已尝试：{all_providers}。"
        f"最后错误：{last_error}"
    )
```

---

## 7. 配置文件示例

```yaml
# projects/demo/config.yaml
project:
  id: demo
  name: Demo Project

search:
  # 使用的搜索 Provider
  provider: tavily

  # 各 Provider 配置（按需填写）
  tavily:
    api_key: ${TAVILY_API_KEY}

  brave:
    api_key: ${BRAVE_API_KEY}

  # Fallback 顺序（Provider 名称列表）
  fallback:
    - duckduckgo    # 第二选择
    - brave         # 第三选择

  # 单次搜索返回结果数
  default_count: 5
```

---

## 8. 使用方式

### 初始化时注入

```python
from providers import get_provider

# 从配置读取 Provider 名称
provider = get_provider(name="tavily")

# Core 模块使用统一的 Provider 接口
investigator = Investigator(search_provider=provider, case_library=...)
```

### 直接搜索

```python
from providers import search_with_fallback

# 自动 fallback
results = search_with_fallback(
    query="Python 异步编程最佳实践",
    preferred="tavily",
    fallback=["duckduckgo"]
)
```

---

## 9. Provider 切换决策树

```
search(query)
    │
    ├─▶ [配置 provider] 可用？
    │       │
    │       ├─ YES → 使用该 Provider
    │       │
    │       └─ NO  → 尝试 fallback[0]
    │                   │
    │                   ├─ 成功 → 返回结果
    │                   │
    │                   └─ 失败 → 尝试 fallback[1]
    │                               │
    │                               └─ ... → 全部失败 → 抛异常
```

---

## 10. 各 Provider 限制

| Provider | 免费额度 | 频率限制 | API Key 申请 |
|---|---|---|---|
| Tavily | 1000次/月 | - | tavily.com |
| Brave | 2000次/月 | - | brave.com/search/api |
| DuckDuckGo | 无限制 | 速度限制 | 无需 |
