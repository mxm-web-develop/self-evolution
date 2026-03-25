#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from providers import get_provider  # noqa: E402


def main() -> int:
    provider_name = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SEARCH_PROVIDER", "duckduckgo")
    print(f"[verify] provider={provider_name}")
    try:
        provider = get_provider(provider_name)
        print(f"[verify] Provider 初始化成功: {provider}")
    except Exception as exc:
        print(f"❌ 安装验证失败: {exc}")
        print("提示：如果你没有 API Key，先用 duckduckgo 作为默认 provider。")
        return 1

    try:
        results = provider.search("OpenClaw project evolution", count=2)
        print(f"[verify] 搜索返回 {len(results)} 条结果")
        if results:
            print(f"[verify] 第一条标题: {results[0].title}")
        else:
            print("[verify] 搜索已执行，但本次没有返回结果")
    except Exception as exc:
        print(f"[verify] 搜索检查跳过/失败: {exc}")
        print("[verify] 依赖与 Provider 初始化正常，可稍后再检查网络/API 可用性")

    print("✅ 安装验证成功")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
