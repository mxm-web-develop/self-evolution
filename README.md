# Self-Evolution / 项目进化助手

> An OpenClaw-first self-evolution system that helps analyze, diagnose, plan, score, approve, execute, and learn from product/project improvements.
>
> 一个 **OpenClaw-first** 的项目进化（自进化）系统，用于帮助项目完成：**调研 → 诊断 → 方案 → 评分 → 审批 → 执行 → 学习回写** 的完整闭环。

---

## English

### What is this?

**Self-Evolution** is a lightweight project optimization and self-improvement framework.

It is designed to:
- research a problem or opportunity
- diagnose the root cause or project type
- generate multiple solution plans
- score plans from business / UX / technical perspectives
- ask for human approval before execution
- execute selected work through OpenClaw-compatible workflows
- write learnings back into a local case library

The current version is built **for OpenClaw first**, while keeping a structure that can later evolve into:
- a generic core layer
- multiple platform adapters

### Core Features

- **OpenClaw-first architecture**
  - built to work inside OpenClaw first
  - later extractable into a generic Core + Adapter system

- **Three-dimensional optimization model**
  - Business optimization
  - Interaction / UX optimization
  - Functional / engineering optimization

- **Closed-loop workflow**
  - Investigation
  - Diagnosis
  - Planning
  - Critique / scoring
  - Human approval
  - Execution
  - Learning

- **Search provider abstraction**
  - default: **Tavily**
  - supported alternatives: **Brave**, **DuckDuckGo**
  - fallback strategy supported

- **Case library**
  - stores successful and failed project cases
  - reusable for future diagnosis and planning

- **OpenClaw adapter layer**
  - task execution
  - state management
  - scheduling
  - notification
  - orchestration

### Directory Structure

```text
self-evolution/
├── core/                 # generic business logic layer
├── adapter_openclaw/     # OpenClaw adapter layer
├── providers/            # search providers (Tavily / Brave / DuckDuckGo)
├── docs/                 # architecture, MVP, manual, guides
├── projects/             # per-project working state
├── cases/                # learned cases and examples
├── scripts/              # bootstrap and verification scripts
└── skills/               # OpenClaw skill definition
```

### Quick Start

```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh duckduckgo
```

This script will automatically:
1. create a Python virtual environment
2. install dependencies
3. generate `.env` files
4. run a verification test

### Manual Installation

```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_install.py duckduckgo
```

### Search Providers

| Provider | Type | Cost | Notes |
|---|---|---:|---|
| Tavily | API | Paid / low-cost | Best default for AI-oriented search |
| Brave | API | Paid / low-cost | Good quality and privacy-friendly |
| DuckDuckGo | community/free | Free | Good fallback / free option |

### Main Documents

- `docs/openclaw-mvp.md` — OpenClaw-first MVP design
- `docs/search-provider-design.md` — search provider strategy
- `docs/code-architecture-guide.md` — developer architecture guide
- `docs/user-manual.md` — user installation and usage guide
- `docs/roadmap.md` — roadmap and milestones

### Current Status

Current repository status:
- architecture docs completed
- OpenClaw-first MVP documented
- bootstrap automation added
- search providers scaffolded
- integrated with `money-machine` for first round validation

### Next Steps

- connect the orchestrator to actual OpenClaw command flows
- improve provider reliability and fallback quality
- make `money-machine` use Self-Evolution for real optimization reports
- continue extracting a generic core after OpenClaw validation succeeds

---

## 中文

### 这是什么？

**项目进化助手（Self-Evolution）** 是一个轻量级的项目优化与自进化框架。

它用来帮助项目完成以下流程：
- 对问题或机会进行调研
- 诊断问题类型和根因
- 生成多个候选方案
- 从 **业务 / 交互 / 技术** 三个维度评分
- 在执行前要求人工审批
- 通过 OpenClaw 工作流执行方案
- 将结果回写到本地案例库，形成可复用经验

当前版本优先面向 **OpenClaw 落地**，同时保留未来演进为：
- 通用 Core 层
- 多平台 Adapter 层

### 核心功能

- **OpenClaw-first 架构**
  - 当前优先在 OpenClaw 中可用
  - 后续再抽离成通用 Core + Adapter 双层结构

- **三维优化模型**
  - 业务优化
  - 交互 / 用户体验优化
  - 功能 / 工程优化

- **完整闭环流程**
  - 调研
  - 诊断
  - 方案生成
  - 评分
  - 人工审批
  - 执行
  - 学习回写

- **搜索 Provider 抽象**
  - 默认：**Tavily**
  - 兼容：**Brave**、**DuckDuckGo**
  - 支持 fallback 策略

- **案例库机制**
  - 记录成功和失败案例
  - 为后续调研、诊断、规划提供参考

- **OpenClaw 适配层**
  - 任务执行
  - 状态管理
  - 调度
  - 通知
  - 流程编排

### 目录结构

```text
self-evolution/
├── core/                 # 通用业务逻辑层
├── adapter_openclaw/     # OpenClaw 适配层
├── providers/            # 搜索 Provider（Tavily / Brave / DuckDuckGo）
├── docs/                 # 架构、MVP、手册、说明文档
├── projects/             # 每个项目的运行状态
├── cases/                # 已学习的案例库
├── scripts/              # 安装与验证脚本
└── skills/               # OpenClaw Skill 定义
```

### 快速开始

```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh duckduckgo
```

这个脚本会自动完成：
1. 创建 Python 虚拟环境
2. 安装依赖
3. 生成 `.env` 文件
4. 执行安装验证

### 手动安装

```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_install.py duckduckgo
```

### 搜索 Provider 说明

| Provider | 类型 | 成本 | 说明 |
|---|---|---:|---|
| Tavily | API | 付费 / 低成本 | AI 搜索友好，推荐默认使用 |
| Brave | API | 付费 / 低成本 | 质量稳定，偏隐私友好 |
| DuckDuckGo | 社区 / 免费 | 免费 | 适合 fallback 或低成本验证 |

### 主要文档

- `docs/openclaw-mvp.md` — OpenClaw-first MVP 方案
- `docs/search-provider-design.md` — 搜索 Provider 设计
- `docs/code-architecture-guide.md` — 面向开发者的代码架构指南
- `docs/user-manual.md` — 面向用户的安装与使用手册
- `docs/roadmap.md` — 路线图与阶段目标

### 当前状态

当前仓库已经完成：
- 架构文档
- OpenClaw-first MVP 文档
- 自动安装脚本
- 搜索 Provider 骨架
- 与 `money-machine` 的第一轮接入验证

### 下一步

- 把 orchestrator 接入真实 OpenClaw 调用链
- 提升 provider 可靠性和 fallback 效果
- 让 `money-machine` 真正使用 Self-Evolution 生成优化报告
- 在 OpenClaw 验证成功后，再逐步抽离通用 Core

---

## Repository

GitHub: <https://github.com/mxm-web-develop/self-evolution>

## License / 许可

Currently internal / in active development.

---

## 🚀 Onboarding 模块（Beta）

项目初始化和接入模块，支持新项目和已有项目的快速接入。

### CLI 快速使用

```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution

# 列出所有项目
PYTHONPATH=. python3 -m src.onboarding.cli --list

# 查看当前活跃项目
PYTHONPATH=. python3 -m src.onboarding.cli --active

# 初始化新项目
PYTHONPATH=. python3 -m src.onboarding.cli --new \
  --goal "做一个 AI 图片生成 SaaS" \
  --name "PixGen" \
  --benchmarks "Midjourney,Leonardo.ai" \
  --priorities "performance:0.4,conversion:0.3" \
  --automation-boundaries "cost_approval,external_release"

# 接入已有项目
PYTHONPATH=. python3 -m src.onboarding.cli --existing /path/to/project

# 仅扫描（不写入）
PYTHONPATH=. python3 -m src.onboarding.cli --scan /path/to/project

# 切换活跃项目
PYTHONPATH=. python3 -m src.onboarding.cli --switch pixgen
```

### Python 代码使用

```python
import sys
sys.path.insert(0, '/path/to/self-evolution')

from src.onboarding import OnboardingRouter

router = OnboardingRouter('/path/to/self-evolution')

# 初始化新项目
session = router.init_new_project(
    goal="做一个 AI 图片生成 SaaS",
    name="PixGen",
    benchmarks=["Midjourney", "Leonardo.ai"],
    priorities=[
        {"dimension": "performance", "weight": 0.4, "reason": "用户关心速度"},
        {"dimension": "conversion", "weight": 0.3, "reason": "提升转化"},
    ],
    automation_boundaries=["cost_approval"],
)

# 接入已有项目
session, scan = router.init_existing_project("/path/to/existing/project")

# 列出 / 切换项目
router.list_projects()
router.switch_project("pixgen")
router.get_active_project()
```

### 生成的文件

每个项目在 `projects/{project-id}/` 下生成：

| 文件 | 说明 |
|---|---|
| `profile.md` | 项目画像 |
| `user-goals.md` | 用户目标文档 |
| `competitor-benchmarks.md` | 竞品分析 |
| `optimization-roadmap.md` | 优化路线图 |
| `state.json` | 运行时状态 |
| `config.yaml` | 项目配置 |
| `health-report.md` | 健康度报告（仅已有项目） |

### Demo 脚本

```bash
PYTHONPATH=. python3 scripts/demo_onboarding.py
```

### 当前进度

✅ 已完成：
- 项目索引管理（projects/index.json）
- OnboardingSession / OnboardingState 数据结构
- 新项目初始化器（完整）
- 已有项目初始化器（扫描部分）
- 统一入口 OnboardingRouter
- CLI（完整）
- Demo 脚本

⏳ 本轮未完成（待后续迭代）：
- 多轮对话真正接入 OpenClaw message 回路
- 自然语言意图识别路由
- 复杂项目结构深度扫描（多语言混合项目）
- OpenClaw skill 集成（SKILL.md）


当前处于内部开发与快速迭代阶段。
