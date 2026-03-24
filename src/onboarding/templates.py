"""
模板填充工具
将 onboarding 收集的数据填入 Markdown 模板
"""

import re
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


def fill_template(template: str, variables: Dict[str, Any]) -> str:
    """将 {{ var }} 占位符替换为变量值"""
    result = template
    for key, value in variables.items():
        placeholder = "{{ " + key + " }}"
        # Handle list/dict values
        if isinstance(value, (list, dict)):
            value_str = str(value)
        else:
            value_str = str(value) if value is not None else ""
        result = result.replace(placeholder, value_str)
    return result


def format_timestamp(dt: datetime = None) -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ── Profile.md ──────────────────────────────────────────────────────────────

PROFILE_TEMPLATE = """# {project_name} — 项目画像

> 由 `/evolve` onboarding 自动生成
> 生成时间：{created_at}
> 最后更新：{updated_at}

## 基本信息

| 字段 | 值 |
|---|---|
| 项目 ID | {project_id} |
| 项目名称 | {project_name} |
| 项目类型 | {project_type} |
| 项目路径 | {project_path} |
| 状态 | {status} |

## 项目目标

{goal}

## 技术栈（推断）

| 类型 | 值 |
|---|---|
| 主语言 | {lang} |
| 框架 | {framework} |
| 包管理 | {package_manager} |
| 测试框架 | {test_framework} |
| CI/CD | {ci_cd} |

## 对标产品（Benchmarks）

{benchmarks}

## 优化优先级

{priorities}

## 自动化边界

{automation_boundaries}

## Onboarding 历史

| 步骤 | 输入值 | 时间 |
|---|---|---|
{history_rows}
"""


def build_profile_md(session: "OnboardingSession", context: Dict[str, Any] = None) -> str:
    """从 OnboardingSession 构建 profile.md"""
    ctx = context or {}
    now = format_timestamp()

    benchmarks_str = "\n".join(
        f"- {b}" for b in session.benchmarks
    ) or "_（未填写）_"

    priorities_rows = []
    for p in session.priorities:
        dim = p.get("dimension", "")
        weight = p.get("weight", "")
        reason = p.get("reason", "")
        priorities_rows.append(f"| {dim} | {weight} | {reason} |")
    priorities_str = (
        "| 维度 | 权重 | 说明 |\n|---|---|---|\n" + "\n".join(priorities_rows)
        if priorities_rows else "_（未填写）_"
    )

    boundaries_rows = []
    for action in session.automation_boundaries:
        boundaries_rows.append(f"| {action} | 是 |")
    boundaries_str = (
        "| 操作 | 需要审批 |\n|---|---|\n" + "\n".join(boundaries_rows)
        if boundaries_rows else "_（无自动化边界限制）_"
    )

    history_rows = "\n".join(
        f"| {h['step']} | {h['value']} | {h['at']} |"
        for h in session.history
    ) or "_（无历史记录）_"

    return PROFILE_TEMPLATE.format(
        project_id=session.project_id,
        project_name=session.name or session.project_id,
        project_type=session.project_type,
        project_path=session.project_path or "_（新项目）_",
        status="ONBOARDING",
        goal=session.goal or "_（未填写）_",
        created_at=session.created_at,
        updated_at=now,
        lang=ctx.get("lang", "_（未知）_"),
        framework=ctx.get("framework", "_（未知）_"),
        package_manager=ctx.get("package_manager", "_（未知）_"),
        test_framework=ctx.get("test_framework", "_（未知）_"),
        ci_cd=ctx.get("ci_cd", "_（未知）_"),
        benchmarks=benchmarks_str,
        priorities=priorities_str,
        automation_boundaries=boundaries_str,
        history_rows=history_rows,
    )


# ── User Goals.md ────────────────────────────────────────────────────────────

GOALS_TEMPLATE = """# 用户目标文档

> 项目：{project_name}
> 生成时间：{timestamp}

## 核心目标（Goal）

**一句话目标：**
{goal}

## 用户故事（User Stories）

| # | 身份 | 想要 | 以便 |
|---|---|---|---|
| 1 | {project_author} | {goal} | 达成业务目标 |

## 成功标准（Success Metrics）

| 指标 | 当前值 | 目标值 | 测量方式 |
|---|---|---|---|
| 业务指标 | - | - | 待补充 |

## 约束条件（Constraints）

- 技术限制：待评估
- 时间限制：待定
- 预算限制：待定
- 其他限制：待补充

## 已知风险（Known Risks）

| 风险 | 影响 | 缓解方案 |
|---|---|---|
| 待评估 | - | - |
"""


def build_user_goals_md(session: "OnboardingSession") -> str:
    return GOALS_TEMPLATE.format(
        project_name=session.name or session.project_id,
        timestamp=format_timestamp(),
        goal=session.goal or "_（未填写）_",
        project_author="项目负责人",
    )


# ── Competitor Benchmarks.md ────────────────────────────────────────────────

BENCHMARKS_TEMPLATE = """# 竞品对比分析

> 项目：{project_name}
> 生成时间：{timestamp}
> 生成方式：手动补充（竞品调研可选）

## 竞品列表

| # | 竞品名称 | 类型 | 网址 |
|---|---|---|---|
{competitor_rows}

## 核心功能对比

| 功能 | {project_name} | 竞品 A | 竞品 B |
|---|---|---|---|
| 待补充 | - | - | - |

## 我方差异化机会

> TODO: 由后续竞品调研补充
"""


def build_competitor_benchmarks_md(session: "OnboardingSession") -> str:
    rows = []
    for i, b in enumerate(session.benchmarks, 1):
        rows.append(f"| {i} | {b} | 直接竞品 | _待补充_ |")
    return BENCHMARKS_TEMPLATE.format(
        project_name=session.name or session.project_id,
        timestamp=format_timestamp(),
        competitor_rows="\n".join(rows) if rows else "| 1 | _待补充_ | - | - |",
    )


# ── Optimization Roadmap.md ────────────────────────────────────────────────�

ROADMAP_TEMPLATE = """# 优化路线图

> 项目：{project_name}
> 制定时间：{timestamp}
> 优先级维度：{priority_dims}

---

## 阶段一：快速修复（1-2 周）

### 高优先级

| # | 优化项 | 当前状态 | 目标 | 工作量 |
|---|---|---|---|---|
| 1 | 待诊断后生成 | - | - | - |

---

## 阶段二：能力提升（1-2 月）

| # | 优化项 | 当前状态 | 目标 | 工作量 |
|---|---|---|---|---|
| 1 | 待诊断后生成 | - | - | - |

---

## 阶段三：长期演进（3+ 月）

| # | 优化项 | 当前状态 | 目标 | 工作量 |
|---|---|---|---|---|
| 1 | 待诊断后生成 | - | - | - |

---

> ⚠️ 路线图详细内容将在 Onboarding 完成后，通过 `/evolve` 诊断阶段自动生成。
"""


def build_optimization_roadmap_md(session: "OnboardingSession") -> str:
    dims = ", ".join(p.get("dimension", "") for p in session.priorities) or "待确定"
    return ROADMAP_TEMPLATE.format(
        project_name=session.name or session.project_id,
        timestamp=format_timestamp(),
        priority_dims=dims,
    )


# ── State.json ───────────────────────────────────────────────────────────────

def build_state_json(session: "OnboardingSession", context: Dict[str, Any] = None) -> dict:
    """构建 state.json 数据"""
    from .state import OnboardingState
    now = datetime.now().isoformat()
    steps = [h["step"] for h in session.history]
    return {
        "schema_version": "1.0",
        "project_id": session.project_id,
        "project_name": session.name or session.project_id,
        "phase": "IDLE",
        "created_at": session.created_at,
        "updated_at": now,
        "current_goal": session.goal,
        "started_at": session.created_at,
        "last_active_at": now,
        "onboarding": {
            "completed": True,
            "completed_at": now,
            "steps_collected": steps,
        },
        "context": {
            "project_path": session.project_path,
            "tech_stack": (context or {}).get("tech_stack", {}),
            "benchmarks": session.benchmarks,
            "priorities": session.priorities,
            "automation_boundaries": [
                {"action": a, "require_human": True}
                for a in session.automation_boundaries
            ],
        },
        "progress": {
            "investigation_completed": False,
            "diagnosis_completed": False,
            "plans_generated": 0,
            "approved_plan_id": None,
            "execution_completed": False,
            "learning_written": False,
        },
        "last_error": None,
    }
