# self-evolution SKILL.md

## 适用场景

当用户在 OpenClaw 中想做下面这些事时，使用本技能：

- 开始一个新项目并建立持续跟进档案
- 接入一个已有项目，生成初始项目画像
- 查看项目列表 / 当前活跃项目
- 切换当前活跃项目
- 通过自然语言或 `/evolve` 入口继续 onboarding 流程
- 让助手把项目管理入口收敛成一个统一 skill

---

## 核心定位

`self-evolution` 在 OpenClaw 中的最终形态是一个**项目 onboarding / 项目上下文管理 skill**。

它当前负责的核心能力是：
1. 统一接住用户关于“项目管理/项目接入/项目切换”的表达
2. 把这些表达映射为标准 `/evolve` 行为
3. 将项目档案落盘到 `projects/{project-id}/`
4. 维护 `projects/index.json` 作为活跃项目索引

> 注意：当前 skill 的稳定能力重点是 onboarding 与项目上下文管理。
> 更完整的“调研 → 诊断 → 方案 → 审批 → 执行 → 学习”闭环仍属于后续迭代。

---

## 用户可说的话（中英双语）

### 显式命令
- `/evolve`
- `/evolve status`
- `/evolve active`
- `/evolve switch <project-id>`
- `/evolve <项目路径>`
- `/evolve new <一句话目标>`

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

---

## 当前支持能力

### 已支持
- 新项目 onboarding
- 已有项目接入
- 项目列表 / 活跃项目 / 切换项目
- 中英双语自然语言入口归一化
- 多轮状态保存在 `runtime/evolve-chat-state.json`
- 项目档案生成到 `projects/{project-id}/`

### 仍未完成
- 完整自然语言自由对话理解（目前是规则驱动，不是开放式 agent 路由）
- 调研 → 诊断 → 方案 → 审批 → 执行 全闭环
- 复杂多语言项目深度扫描
- 与 OpenClaw message / sessions / cron 的深度自动编排

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
