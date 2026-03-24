# Onboarding 设计方案（Unified Onboarding）

> 版本：v1.0 | 目标：一个入口，同时支持已有项目和新建项目

## 1. 设计原则

1. **单入口**：不区分"新用户引导"和"老用户使用"，统一为 onboarding 流程
2. **先诊断，再行动**：先判断用户是什么状态，再决定走哪条路径
3. **多项目友好**：始终维护项目列表，支持随时切换
4. **渐进披露**：不一次性要求填写大量信息，按需收集

## 2. 决策树

```
用户发起 /evolve
    │
    ▼
┌─────────────────────────────────────────┐
│  STEP 0: 上下文判断                      │
│  "你想做什么？"                          │
│                                         │
│  A. 输入了项目路径  → 已有项目流程        │
│  B. 说"新建项目"      → 新项目流程        │
│  C. 说"看一下项目们" → 多项目列表        │
│  D. 纯对话/闲聊      → 轻量响应          │
└─────────────────────────────────────────┘
```

## 3. 流程 A：已有项目（已有路径）

### 3.1 扫描阶段

用户给出路径后，系统自动：

```python
# 扫描内容
扫描项目目录结构（语言/框架）
读取 package.json / pyproject.toml / Cargo.toml 等
读取 README.md（了解项目目标）
扫描已有测试目录（了解测试覆盖）
查看 .git/logs 了解活跃度
```

### 3.2 输出项目画像

```
## 🔍 项目扫描报告

项目路径：/path/to/project
项目名：super-mxm-ai
语言：TypeScript + Python
框架：Next.js / FastAPI
测试：Vitest（部分覆盖）
活跃度：高（3天前有提交）
README：✅ 有完整说明

风险点：
- 无 CI/CD 配置
- 依赖较旧（3个包有安全警告）
- 测试覆盖率 < 40%

优化建议优先级：
1. 🔴 升级安全警告依赖（高优）
2. 🟡 增加测试覆盖（中优）
3. 🟢 引入 CI/CD（低优）
```

### 3.3 用户确认

```
这个项目画像准确吗？有需要补充或纠正的吗？
```

## 4. 流程 B：新项目（从 0 开始）

### 4.1 多轮信息收集

```
┌──────────────────────────────────────────────┐
│ STEP 1: 项目目标                              │
│ "想做什么？一句话描述你的项目目标"              │
│                                              │
│ 用户输入：类似"我要做一个 AI 图片生成 SaaS"    │
│ → 记录到 profile.goal                        │
└──────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────┐
│ STEP 2: 项目名称                              │
│ "给项目起个名字？"                            │
│                                              │
│ 用户输入：PixGen                              │
│ → 记录到 profile.name                        │
│ → 初始化目录：projects/pixgen/               │
└──────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────┐
│ STEP 3: 对标产品                              │
│ "有没有参考产品？比如某个竞品或类似产品"        │
│                                              │
│ 用户输入：Midjourney / Leonardo.ai           │
│ → 记录到 profile.benchmarks[]                │
│ → 自动调研竞品，生成对比表                    │
└──────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────┐
│ STEP 4: 优化优先级                            │
│ "你最关心哪方面？（多选）"                    │
│                                              │
│ 选项：                                        │
│ [1] 🚀 速度/性能    [2] 💰 成本控制           │
│ [3] 🎯 转化率        [4] 🛡️ 安全性            │
│ [5] 📈 可扩展性      [6] 👥 用户体验           │
│ [7] 🔧 维护性        [8] 📊 数据驱动           │
│                                              │
│ 用户选择：1, 3, 5                             │
│ → 记录到 profile.priorities[]                │
│ → 权重影响后续方案评分                        │
└──────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────┐
│ STEP 5: 自动化边界                            │
│ "有哪些事情你想自己控制、不想全自动？"         │
│                                              │
│ 选项（可多选或自定义）：                       │
│ [1] 💰 费用审批  [2] 📢 对外发布              │
│ [3] 🔑 密钥配置  [4] 📦 依赖升级              │
│ [5] 🔀 合并PR    [6] ☁️ 云资源配置            │
│ [自定义]                                       │
│                                              │
│ 用户选择：1, 2                                │
│ → 记录到 profile.automation_boundaries[]    │
│ → 这些节点在流程中会触发人工审批              │
└──────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────┐
│ STEP 6: 初始化完成                             │
│ "好的，项目 PixGen 已初始化。                 │
│  接下来你可以：                               │
│  - /evolve pixgen 优化 XX                    │
│  - /evolve status    查看所有项目             │
│  - /evolve resume     继续上次进度"            │
└──────────────────────────────────────────────┘
```

## 5. 多项目支持

### 5.1 项目索引

每次初始化新项目或接入已有项目时，更新索引文件：

```json
// projects/index.json
{
  "projects": [
    {
      "id": "pixgen",
      "name": "PixGen",
      "path": "/path/to/pixgen",
      "type": "new",
      "created_at": "2026-03-24T16:00:00",
      "last_active": "2026-03-24T16:00:00",
      "phase": "IDLE",
      "profile": { ... }
    },
    {
      "id": "money-machine",
      "name": "Money Machine",
      "path": "/Users/mxm_pro/.openclaw/workspace/money-machine",
      "type": "existing",
      "created_at": "2026-03-10T10:00:00",
      "last_active": "2026-03-24T14:30:00",
      "phase": "PLANNING",
      "profile": { ... }
    }
  ],
  "active_project": "pixgen"
}
```

### 5.2 多项目对话上下文

```
# 在 OpenClaw 对话中维护：
- 当前活跃项目（active_project）
- 项目切换命令：/evolve switch [project-id]
```

## 6. Onboarding 状态机

```
                    ┌──────────┐
                    │   IDLE   │◄─────────────────┐
                    └────┬─────┘                   │
                         │ /evolve                 │
              ┌──────────▼──────────┐             │
              │    CONTEXT_CHECK    │             │
              └──────────┬──────────┘             │
                         │                        │
          ┌──────────────┴──────────────┐        │
          ▼                             ▼        │
  ┌───────────────┐           ┌───────────────┐  │
  │ EXISTING_SCAN │           │  NEW_GATHER    │  │
  │               │           │  (multi-turn)  │  │
  └───────┬───────┘           └───────┬───────┘  │
          │                           │            │
          ▼                           ▼            │
  ┌───────────────┐           ┌───────────────┐  │
  │ PROFILE_BUILD │           │ PROFILE_BUILD │  │
  └───────┬───────┘           └───────┬───────┘  │
          │                           │            │
          └──────────────┬────────────┘            │
                         ▼                          │
                 ┌───────────────┐                 │
                 │  ONBOARDED    │─────────────────┘
                 └───────────────┘  /evolve（新项目或切换）
```

## 7. 项目画像数据结构

```json
// projects/{project-id}/profile.json
{
  "id": "pixgen",
  "name": "PixGen",
  "type": "new",
  "created_at": "2026-03-24T16:00:00Z",
  "updated_at": "2026-03-24T16:30:00Z",
  
  "goal": "做一个 AI 图片生成的 SaaS 产品",
  "benchmarks": ["Midjourney", "Leonardo.ai"],
  "priorities": [
    { "dimension": "performance", "weight": 0.4 },
    { "dimension": "conversion", "weight": 0.3 },
    { "dimension": "scalability", "weight": 0.3 }
  ],
  "automation_boundaries": [
    { "action": "cost_approval", "require_human": true },
    { "action": "external_release", "require_human": true }
  ],
  
  "tech_stack": {
    "languages": ["TypeScript", "Python"],
    "frameworks": ["Next.js", "FastAPI"],
    "inferred": true
  },
  
  "onboarding_phase": "COMPLETED",
  "onboarding_history": [
    { "step": "goal", "value": "...", "at": "2026-03-24T16:01:00Z" },
    ...
  ]
}
```

## 8. 触发命令设计

| 命令 | 说明 |
|---|---|
| `/evolve` | 启动 onboarding（自动判断已有/新建） |
| `/evolve [项目路径]` | 对已有项目进行 onboarding |
| `/evolve new [目标描述]` | 直接新建项目（跳过询问） |
| `/evolve status` | 查看所有项目状态 |
| `/evolve switch [project-id]` | 切换活跃项目 |
| `/evolve profile [project-id]` | 查看项目画像 |
| `/evolve help` | 显示帮助 |

## 9. 集成方式

### 9.1 统一入口（推荐）

在 OpenClaw 中安装 skill 后，用户只需说 `/evolve` 或自然语言触发：

```
# 自然语言入口
"帮我优化一下网站"
"我们来做个新项目"
"看看现在有哪些项目在跟踪"
```

系统自动解析意图，判断是已有项目还是新项目。

### 9.2 不再需要两个独立脚本

旧方案（两个脚本）：
- `onboarding-new.sh` - 新用户引导
- `onboarding-existing.sh` - 已有项目接入

新方案：统一 `/evolve` 入口，根据上下文自动路由。

## 10. Onboarding 产物路径约定

所有 onboarding 流程产生的文件，统一存放在以下位置：

```
projects/{project-id}/
├── profile.md              # 项目画像（见 docs/onboarding-templates/project-profile.md）
├── user-goals.md            # 用户目标（见 docs/onboarding-templates/user-goals.md）
├── competitor-benchmarks.md # 竞品分析（见 docs/onboarding-templates/competitor-benchmarks.md）
├── optimization-roadmap.md  # 优化路线图（见 docs/onboarding-templates/optimization-roadmap.md）
├── state.json               # 运行时状态（见 docs/onboarding-templates/state.json）
├── investigation.md        # 自动生成
├── diagnosis.json           # 自动生成
├── scores.json              # 自动生成
└── plans/
    ├── plan-A.md
    ├── plan-B.md
    └── plan-C.md
```

各模板文件位于 `docs/onboarding-templates/` 目录，可直接参考。

## 11. 实施优先级

| 优先级 | 内容 | 说明 |
|---|---|---|
| P0 | 统一 SKILL.md 触发设计 | 让用户能用起来 |
| P0 | 项目索引 (projects/index.json) | 多项目支持基础 |
| P0 | Profile 数据结构 | 画像落盘结构 |
| P1 | 多轮对话收集逻辑 | 核心 onboarding |
| P1 | 已有项目扫描 | 快速接入现有代码 |
| P2 | 自然语言理解路由 | 更智能的意图判断 |
