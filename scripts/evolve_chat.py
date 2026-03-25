#!/usr/bin/env python3
"""/evolve 对话入口包装脚本"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.onboarding.chat_flow import EvolveChatFlow  # noqa: E402


def main() -> int:
    text = " ".join(sys.argv[1:]).strip()
    flow = EvolveChatFlow(str(ROOT))
    print(flow.handle(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
