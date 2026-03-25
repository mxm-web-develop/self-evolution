# self-evolution SKILL.md

## 适用场景

当用户在 OpenClaw 中想做下面这些事时，使用本技能：

- 开始一个新项目并建立持续跟进档案
- 接入一个已有项目，生成初始项目画像
- 查看项目列表 / 当前活跃项目
- 切换当前活跃项目
- **从当前活跃项目出发，触发调研 → 诊断（甚至生成方案）最小闭环**
- 通过自然语言或 `/evolve` 入口继续 onboarding 流程
- 让助手把项目管理入口收敛成一个统一 skill

---

## 核心定位

`self-evolution` 在 OpenClaw 中承担两大能力层：

**已稳定的底层：项目管理上下文**
1. 统一接住用户关于"项目管理/项目接入/项目切换"的表达
2. 把这些表达映射为标准 `/evolve` 行为
3. 将项目档案落盘到 `projects/{project-id}/`
4. 维护 `projects/index.json` 作为活跃项目索引

**本次新增（Beta）：项目自进化分析入口**
5. 从当前活跃项目出发，接收一个问题/优化方向描述
6. 自动执行**调研（investigate）→ 诊断（diagnose）→ 方案（plan）**完整闭环
7. 生成格式化分析报告，包含：相似案例、网络发现、问题类型、根因、优先级
8. 生成多个候选方案（A/B/C），支持审批和执行

> 当前闭环边界：调研→诊断→方案 已完成（BETA）。审批→执行 仍在实现中。

---

## 用户可说的话（中英双语）

### 显式命令
- `/evolve`
- `/evolve status`
- `/evolve active`
- `/evolve switch <project-id>`
- `/evolve <项目路径>`
- `/evolve new <一句话目标>`
- `/evolve analyze <问题描述>`
- `/evolve plan [问题描述]`

### 自然语言表达
也支持直接说：

- `帮我新建一个项目：AI 写作工作流平台`
- `看看我现在有哪些项目`
- `切换到 pixgen`
- `接入这个项目 /Users/xxx/my-app`
- `当前活跃项目是哪个`
- `start a new project for AI image workflow`
- `list my projects`
- `switch to flowforge`
- `onboard existing project /Users/xxx/repo`

### 分析/诊断类表达（新！Beta）

用户想分析当前活跃项目时，直接说：

- `帮我分析当前项目`
- `分析一下这个项目有什么可以优化的地方`
- `诊断一下 pixgen 的性能问题`
- `帮我调研这个项目的用户体验`
- `优化建议有哪些`
- `帮我看看这个项目适合做什么功能`
- `analyze the current project`
- `run a diagnosis on performance issues`
- `investigate UX improvements for this project`

### 方案/规划类表达（新！Beta）

用户想基于诊断生成方案时，直接说：

- `帮我生成方案`
- `帮我规划一下`
- `制定计划`
- `有哪些解决方案`
- `下一步我应该做什么`
- `give me some options`
- `what should i do next`

> **前提**：必须先有一个活跃项目（通过 `/evolve new` 或 `/evolve <path>` 建立）。如果没有，会提示用户先建立项目。

---

## 助手内部执行方式

在仓库根目录执行：

```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution
python3 scripts/evolve_skill.py "<用户原始输入>"
```

### 为什么用这个入口

因为 `scripts/evolve_skill.py` 会：

1. 接收用户原始输入
2. 做自然语言归一化（中英双语意图识别）
3. 统一交给 `EvolveChatFlow` 处理
4. 复用 `runtime/evolve-chat-state.json` 维护多轮状态

所以**不要让用户手动记内部脚本差异**；统一走这个 skill 入口即可。

---

## 处理规则

### 1. 有明确路径
如果用户给的是存在的目录路径：
- 视为“接入已有项目”
- 扫描项目结构并生成画像
- 在 `projects/{project-id}/` 下产出档案

### 2. 想新建项目
如果用户表达的是“新建项目 / 创建项目 / new project”：
- 进入新项目 onboarding
- 逐步收集：目标、项目名、竞品、优先级、自动化边界

### 3. 想看项目状态
如果用户问：
- 有哪些项目
- 项目列表
- 当前项目
- 切换项目

直接映射到：
- `/evolve status`
- `/evolve active`
- `/evolve switch <id>`

### 4. 有进行中的多轮对话
如果 `runtime/evolve-chat-state.json` 显示当前 onboarding 进行中：
- 优先把用户普通回复当作下一轮输入
- 不要重复讲内部机制
- 继续往下问，直到完成落盘

### 5. 想分析当前项目（Beta）
如果用户表达的是"分析/诊断/调研/优化建议"类意图：
- 检查当前是否有活跃项目
- 没有 → 提示用户先建立项目
- 有 → 从 `EvolutionAnalyzer` 出发执行调研+诊断，生成报告
- 结果包含：相似案例、网络发现、问题类型、根因、优先级
- 结束时提示用户"下一步可以生成方案"

### 6. 想生成方案（Beta）
如果用户表达的是"生成方案/规划/下一步做什么"类意图：
- 检查当前是否有活跃项目
- 没有 → 提示用户先建立项目
- 有 → 自动执行调研+诊断+方案生成完整闭环
- 返回 3 个候选方案（A/B/C），标注执行画像（复杂度 / 落地节奏 / 自动化适配度）
- 提示用户"回复「执行方案A」开始审批"

---

## 当前支持能力

### 已支持
- 新项目 onboarding
- 已有项目接入
- 项目列表 / 活跃项目 / 切换项目
- 中英双语自然语言入口归一化
- 多轮状态保存在 `runtime/evolve-chat-state.json`
- 项目档案生成到 `projects/{project-id}/`
- **从活跃项目出发的调研 → 诊断 → 方案 完整闭环（Beta）**
- **`/evolve analyze <问题>` 命令入口（调研+诊断）**
- **`/evolve plan [问题]` 命令入口（调研+诊断+方案）**
- **自然语言触发方案生成："帮我生成方案" / "下一步做什么"（Beta）**

### 仍未完成
- 完整自然语言自由对话理解（目前是规则驱动，不是开放式 agent 路由）
- 审批 → 执行 闭环（方案已可生成，审批执行往后迭代）
- 复杂多语言项目深度扫描
- 与 OpenClaw sessions / cron 的深度自动编排

---

## 对用户的回答风格

- 默认用自然中文回答
- 不要一上来暴露内部脚本命令
- 只有当用户明确问“怎么手动运行 / 怎么部署”时，再展示命令
- 如果用户只是说“帮我接入项目”“看看我有哪些项目”，就直接当作 skill 入口处理

---

## 产物位置

- `projects/index.json`：项目索引
- `projects/{project-id}/profile.md`
- `projects/{project-id}/user-goals.md`
- `projects/{project-id}/competitor-benchmarks.md`
- `projects/{project-id}/optimization-roadmap.md`
- `projects/{project-id}/state.json`
- `projects/{project-id}/config.yaml`
- `projects/{project-id}/health-report.md`（已有项目）
- `runtime/evolve-chat-state.json`：多轮 onboarding 对话状态

---

## 推荐测试用例

按下面顺序做烟雾测试：

1. `python3 scripts/evolve_skill.py "/evolve status"`
2. `python3 scripts/evolve_skill.py "看看我有哪些项目"`
3. `python3 scripts/evolve_skill.py "切换到 pixgen"`
4. `python3 scripts/evolve_skill.py "帮我新建一个项目：AI 图片工作流平台"`
5. 连续回复项目名 / 竞品 / 优先级 / 自动化边界
6. `python3 scripts/evolve_skill.py "接入这个项目 /path/to/project"`

如果这些都通，说明 skill 入口已基本可用。

---

## 相关说明书

完整使用说明见：
- `docs/openclaw-skill-manual.md`
