#!/usr/bin/env python3
"""OpenClaw Skill 入口。

面向 OpenClaw skill 调用：直接接收用户原始输入，内部做自然语言归一化，
统一交给 EvolveChatFlow 处理。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.onboarding.chat_flow import EvolveChatFlow  # noqa: E402


def main() -> int:
    raw_text = " ".join(sys.argv[1:]).strip()
    flow = EvolveChatFlow(str(ROOT))
    print(flow.handle(raw_text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
