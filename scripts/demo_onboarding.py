#!/usr/bin/env python3
"""
Self-Evolution Onboarding Demo Script

演示如何使用 onboarding 模块的各个功能。
运行前确保在 self-evolution 根目录。

用法：
  cd /Users/mxm_pro/.openclaw/workspace/self-evolution
  PYTHONPATH=. python3 scripts/demo_onboarding.py
"""

import sys
from pathlib import Path

# 确保 src 在 path 中
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.onboarding import OnboardingRouter


BASE = Path(__file__).parent.parent.parent.absolute()


def demo_list_projects():
    print("\n" + "="*50)
    print("📋 演示：列出所有项目")
    print("="*50)
    router = OnboardingRouter(str(BASE))
    print(router._format_project_list())


def demo_new_project():
    print("\n" + "="*50)
    print("🚀 演示：初始化新项目")
    print("="*50)
    router = OnboardingRouter(str(BASE))

    session = router.init_new_project(
        goal="做一个 AI 个人助手 SaaS",
        name="AI Buddy",
        benchmarks=["ChatGPT Plus", "Claude.ai"],
        priorities=[
            {"dimension": "user_experience", "weight": 0.4, "reason": "体验决定留存"},
            {"dimension": "performance", "weight": 0.3, "reason": "响应速度影响满意度"},
            {"dimension": "cost", "weight": 0.3, "reason": "成本控制很重要"},
        ],
        automation_boundaries=["cost_approval"],
    )
    print(f"✅ 项目 '{session.name}' 初始化完成！")
    print(f"   ID: {session.project_id}")
    print(f"   目标: {session.goal}")
    print(f"   竞品: {', '.join(session.benchmarks)}")
    print(f"   文件已生成到 projects/{session.project_id}/")


def demo_existing_project():
    print("\n" + "="*50)
    print("🔍 演示：接入已有项目")
    print("="*50)
    router = OnboardingRouter(str(BASE))

    # 用 demo 目录（已有）演示
    demo_path = str(BASE / "projects" / "demo")
    session, scan = router.init_existing_project(demo_path)
    print(f"✅ 已有项目接入完成！")
    print(f"   项目名: {session.name}")
    print(f"   ID: {session.project_id}")
    print(f"   技术栈: {', '.join(scan['tech_stack'].get('languages', []))}")
    print(f"   框架: {', '.join(scan['tech_stack'].get('frameworks', []))}")
    print(f"   健康度: README={'✅' if scan['health']['has_readme'] else '❌'}, "
          f"测试={'✅' if scan['health']['has_tests'] else '❌'}, "
          f"CI/CD={'✅' if scan['health']['has_ci'] else '❌'}")


def demo_switch():
    print("\n" + "="*50)
    print("🔄 演示：切换活跃项目")
    print("="*50)
    router = OnboardingRouter(str(BASE))
    projects = router.list_projects()
    if len(projects) >= 2:
        # 切换到非当前项目
        current = router.index.get_active_project_id()
        other = next(p["id"] for p in projects if p["id"] != current)
        proj = router.switch_project(other)
        print(f"已切换到: {proj['name']} [{proj['id']}]")
        # 切换回去
        proj = router.switch_project(current)
        print(f"已切回: {proj['name']} [{proj['id']}]")
    else:
        print("项目不足 2 个，跳过切换演示")


def demo_scan():
    print("\n" + "="*50)
    print("🔬 演示：扫描已有项目（只读，不写入）")
    print("="*50)
    import json
    router = OnboardingRouter(str(BASE))
    # 扫描 demo 项目
    from src.onboarding.existing_project import ExistingProjectScanner
    scanner = ExistingProjectScanner(str(BASE / "projects" / "demo"))
    result = scanner.scan()
    print(f"项目: {result['project_name']}")
    print(f"技术栈: {result['tech_stack']}")
    print(f"健康度: {result['health']}")


def main():
    print("🤖 Self-Evolution Onboarding Demo")
    print(f"Base path: {BASE}")

    demo_scan()
    demo_new_project()
    demo_existing_project()
    demo_switch()
    demo_list_projects()

    print("\n" + "="*50)
    print("✅ Demo 完成！")
    print("="*50)
    print("\n试试 CLI 命令：")
    print("  python -m src.onboarding.cli --list")
    print("  python -m src.onboarding.cli --active")
    print("  python -m src.onboarding.cli --new --goal '做XX' --name 'MyApp'")
    print("  python -m src.onboarding.cli --scan /path/to/project")


if __name__ == "__main__":
    main()
