#!/usr/bin/env python3
"""
Self-Evolution Onboarding CLI

用法示例：
  cd /Users/mxm_pro/.openclaw/workspace/self-evolution
  python -m onboarding.cli --list
  python -m onboarding.cli --active
  python -m onboarding.cli --new --goal "AI 图片生成 SaaS" --name "PixGen" --benchmarks "Midjourney,Leonardo.ai"
  python -m onboarding.cli --existing /path/to/existing/project
  python -m onboarding.cli --switch pixgen
  python -m onboarding.cli --scan /path/to/project
"""

import argparse
import json
import sys
from pathlib import Path

# 将 src 加入 path（方便直接运行）
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.onboarding import OnboardingRouter


SELF_EVOLUTION_PATH = Path(__file__).parent.parent.parent.absolute()


def cmd_list(router: OnboardingRouter):
    print(router._format_project_list())


def cmd_active(router: OnboardingRouter):
    proj = router.get_active_project()
    if not proj:
        print("❌ 没有活跃项目")
        return
    print(f"""👉 当前活跃项目：{proj['name']}
   ID：{proj['id']}
   类型：{proj.get('type', '?')}
   阶段：{proj.get('phase', '?')}
   路径：{proj.get('path', '?')}
   Onboarding：{'✅ 完成' if proj.get('onboarding_completed') else '⏳ 进行中'}
""")


def cmd_new(router: OnboardingRouter, args):
    # 解析 benchmarks
    benchmarks = None
    if args.benchmarks:
        benchmarks = [b.strip() for b in args.benchmarks.split(",") if b.strip()]

    # 解析 priorities（简单 key:value 格式）
    priorities = None
    if args.priorities:
        priorities = []
        for p in args.priorities.split(","):
            parts = p.strip().split(":")
            dim = parts[0].strip()
            weight = float(parts[1].strip()) if len(parts) > 1 else 0.5
            priorities.append({"dimension": dim, "weight": weight, "reason": ""})

    # 解析 automation_boundaries
    boundaries = None
    if args.automation_boundaries:
        boundaries = [b.strip() for b in args.automation_boundaries.split(",") if b.strip()]

    session = router.init_new_project(
        goal=args.goal,
        name=args.name,
        benchmarks=benchmarks,
        priorities=priorities,
        automation_boundaries=boundaries,
    )

    print(f"""✅ 新项目初始化完成！

   项目ID：{session.project_id}
   项目名：{session.name}
   目标：{session.goal}
   已生成文件：
     projects/{session.project_id}/
       ├── profile.md
       ├── profile.md
       ├── profile.md
       ├── optimization-roadmap.md
       ├── state.json
       └── config.yaml
""")


def cmd_existing(router: OnboardingRouter, args):
    path = Path(args.path).expanduser().resolve()
    if not path.exists():
        print(f"❌ 路径不存在：{path}")
        return

    session, scan = router.init_existing_project(str(path))

    print(f"""✅ 已有项目接入完成！

   项目名：{session.name}
   项目ID：{session.project_id}
   技术栈：{', '.join(scan['tech_stack'].get('languages', [])) or '未知'}
   框架：{', '.join(scan['tech_stack'].get('frameworks', [])) or '未知'}
   健康度：
     README {'✅' if scan['health'].get('has_readme') else '❌'}
     测试目录 {'✅' if scan['health'].get('has_tests') else '❌'}
     CI/CD {'✅' if scan['health'].get('has_ci') else '❌'}
     Git {'✅' if scan['health'].get('has_git') else '❌'}
   已生成文件：
     projects/{session.project_id}/
       ├── profile.md
       ├── profile.md
       ├── profile.md
       ├── optimization-roadmap.md
       ├── state.json
       ├── config.yaml
       └── health-report.md
""")


def cmd_switch(router: OnboardingRouter, args):
    try:
        proj = router.switch_project(args.project_id)
        print(f"👉 已切换到项目：{proj['name']} [{proj['id']}]")
    except ValueError as e:
        print(f"❌ {e}")


def cmd_scan(router: OnboardingRouter, args):
    """仅扫描，不写入文件"""
    from src.onboarding.existing_project import ExistingProjectScanner
    scanner = ExistingProjectScanner(args.path)
    result = scanner.scan()
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_status(router: OnboardingRouter):
    print(router._format_project_list())


def main():
    parser = argparse.ArgumentParser(
        description="Self-Evolution Onboarding CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python -m onboarding.cli --list
  python -m onboarding.cli --active
  python -m onboarding.cli --new \\
    --goal "AI 图片生成 SaaS" \\
    --name "PixGen" \\
    --benchmarks "Midjourney,Leonardo.ai" \\
    --priorities "performance:0.4,conversion:0.3" \\
    --automation-boundaries "cost_approval,external_release"
  python -m onboarding.cli --existing /path/to/my-project
  python -m onboarding.cli --switch pixgen
  python -m onboarding.cli --scan /path/to/project
        """
    )

    # 操作命令
    parser.add_argument("--list", "-l", action="store_true", help="列出所有项目")
    parser.add_argument("--active", "-a", action="store_true", help="查看当前活跃项目")
    parser.add_argument("--status", "-s", action="store_true", help="查看所有项目状态")
    # Note: -h/--help is built-in to argparse

    # 新项目
    parser.add_argument("--new", "-n", action="store_true", help="初始化新项目")
    parser.add_argument("--goal", "-g", type=str, help="项目目标描述")
    parser.add_argument("--name", type=str, help="项目名称")
    parser.add_argument("--benchmarks", type=str, help="对标竞品，逗号分隔")
    parser.add_argument("--priorities", type=str, help="优化优先级，格式: dim:weight,dim:weight")
    parser.add_argument("--automation-boundaries", type=str, help="自动化边界，逗号分隔")

    # 已有项目
    parser.add_argument("--existing", "-e", action="store_true", help="接入已有项目")
    parser.add_argument("--path", "-p", type=str, help="项目路径（用于 --existing 或 --scan）")

    # 切换项目
    parser.add_argument("--switch", action="store_true", help="切换活跃项目")
    parser.add_argument("project_id", nargs="?", type=str, help="项目ID（用于 --switch）")

    # 扫描（只读）
    parser.add_argument("--scan", action="store_true", help="仅扫描项目，不写入文件")

    args = parser.parse_args()

    # 默认路径
    base = args.path or str(SELF_EVOLUTION_PATH)
    router = OnboardingRouter(str(SELF_EVOLUTION_PATH))

    # --help is handled automatically by argparse

    # 优先级：list > status > active > switch > scan > new > existing
    if args.list:
        cmd_list(router)
    elif args.status:
        cmd_status(router)
    elif args.active:
        cmd_active(router)
    elif args.switch and args.project_id:
        args.project_id = args.project_id.rstrip("/")
        cmd_switch(router, args)
    elif args.scan and (args.path or args.project_id):
        args.path = args.path or args.project_id
        cmd_scan(router, args)
    elif args.new:
        if not args.goal:
            print("❌ --new 需要 --goal 参数")
            parser.print_help()
            return
        if not args.name:
            args.name = args.goal.split()[0]  # fallback to first word
        cmd_new(router, args)
    elif args.existing and args.path:
        cmd_existing(router, args)
    else:
        # 无参数时显示项目列表
        cmd_status(router)


if __name__ == "__main__":
    main()
