# Self-Evolution OpenClaw Skill 使用说明书

> 版本：Skill Beta v1
> 定位：在 OpenClaw 中作为统一的项目 onboarding / 项目上下文管理入口使用

---

## 1. 这是什么

`self-evolution` 现在可以作为一个 **OpenClaw skill** 使用，主要负责：

- 新项目 onboarding
- 已有项目接入
- 项目列表管理
- 活跃项目切换
- 通过自然语言和 `/evolve` 统一进入项目管理流程

它的目标不是替代完整项目管理平台，而是先在 OpenClaw 里成为：

> **“我想开始/接入/切换/查看项目”时的统一入口 skill。**

---

## 2. 当前能力边界

### 已完成
- `/evolve` 对话入口
- 新项目 onboarding 多轮流程
- 已有项目扫描与接入
- 项目索引 `projects/index.json`
- 活跃项目管理
- 中英双语规则式意图识别
- Skill 入口脚本：`scripts/evolve_skill.py`

### 尚未完成
- 真正自由对话级别的复杂语义理解
- 完整调研 → 诊断 → 方案 → 执行闭环
- 深度代码理解与复杂项目扫描
- 自动编排 OpenClaw 子代理执行复杂任务

所以当前最准确的说法是：

> **它已经是一个可用的 OpenClaw skill Beta，但能力重点在 onboarding 和项目上下文管理。**

---

## 3. 用户怎么触发

### 3.1 直接命令

```text
/evolve
/evolve status
/evolve active
/evolve switch pixgen
/evolve new AI 写作工作流平台
/evolve /Users/xxx/my-project
```

### 3.2 自然语言

中文：
- 帮我新建一个项目：AI 生成海报平台
- 看看我有哪些项目
- 当前活跃项目是哪个
- 切换到 flowforge
- 接入项目 /Users/xxx/my-project

英文：
- start a new project for AI poster generation
- list my projects
- what is the active project
- switch to pixgen
- onboard existing project /Users/xxx/my-project

---

## 4. 内部工作原理

Skill 内部统一走下面这个入口：

```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution
python3 scripts/evolve_skill.py "<用户原始输入>"
```

这个脚本会：

1. 接收用户原始文本
2. 用 `src/onboarding/intent_parser.py` 做意图归一化
3. 把它转换成标准 `/evolve` 命令
4. 交给 `src/onboarding/chat_flow.py` 执行
5. 读写 `runtime/evolve-chat-state.json` 维持多轮状态

---

## 5. 目录结构（与 skill 相关）

```text
self-evolution/
├── scripts/
│   ├── evolve_chat.py
│   └── evolve_skill.py        # OpenClaw skill 统一入口
├── skills/
│   └── self-evolution/
│       └── SKILL.md
├── src/onboarding/
│   ├── chat_flow.py
│   ├── intent_parser.py
│   ├── router.py
│   ├── new_project.py
│   ├── existing_project.py
│   └── index_manager.py
├── projects/
│   ├── index.json
│   └── {project-id}/
└── runtime/
    └── evolve-chat-state.json
```

---

## 6. 生成的产物

### 新项目
在 `projects/{project-id}/` 下生成：

- `profile.md`
- `user-goals.md`
- `competitor-benchmarks.md`
- `optimization-roadmap.md`
- `state.json`
- `config.yaml`

### 已有项目
除以上文件外，还会多生成：

- `health-report.md`

### 全局索引
- `projects/index.json`

### 多轮对话状态
- `runtime/evolve-chat-state.json`

---

## 7. 推荐使用方式

### 场景 A：从 0 开始一个新项目
1. 用户说：`帮我新建一个项目：AI 图片 SaaS`
2. skill 自动进入 onboarding
3. 继续问：项目名、竞品、优先级、自动化边界
4. 落盘生成项目档案

### 场景 B：把已有代码仓接进来
1. 用户说：`接入项目 /Users/xxx/my-repo`
2. skill 扫描项目目录
3. 生成初始项目画像和健康度报告
4. 写入项目索引

### 场景 C：切换工作上下文
1. 用户说：`切换到 pixgen`
2. skill 更新 `projects/index.json`
3. 后续讨论默认围绕该项目继续

---

## 8. 本地手动测试

### 8.1 查看项目列表
```bash
cd /Users/mxm_pro/.openclaw/workspace/self-evolution
python3 scripts/evolve_skill.py "看看我有哪些项目"
```

### 8.2 切换项目
```bash
python3 scripts/evolve_skill.py "切换到 pixgen"
```

### 8.3 开始新项目
```bash
python3 scripts/evolve_skill.py "帮我新建一个项目：AI 设计工作流平台"
```

### 8.4 接入已有项目
```bash
python3 scripts/evolve_skill.py "接入项目 /Users/xxx/my-project"
```

---

## 9. 常见问题

### Q1：为什么有时自然语言没命中？
因为当前是**规则式语义归一化**，不是全开放 agent 理解。建议在下面几类表达里说得更明确：
- 新建项目
- 查看项目列表
- 当前活跃项目
- 切换项目
- 接入已有项目 + 路径

### Q2：为什么还要保留 `/evolve`？
因为 `/evolve` 是稳定的 canonical command。自然语言只是更友好的外层包装。

### Q3：它现在是不是完整的 self-evolution 系统？
不是。现在完成的是 **OpenClaw skill 入口层 + onboarding/project context 管理层**。
完整闭环还要继续做。

---

## 10. 后续迭代建议

建议下一阶段按顺序继续：

1. 把规则式意图识别升级为更稳的语义路由
2. 接入更完整的项目分析能力
3. 把活跃项目上下文自动注入后续分析任务
4. 再接研究 / 诊断 / 方案 / 审批 / 执行闭环

---

## 11. 结论

现在的 `self-evolution` 已经可以在 OpenClaw 中作为一个 **可用的 Beta skill** 来承担：

- 项目 onboarding
- 已有项目接入
- 项目上下文管理

如果你想继续扩展，它的下一步就不再是“有没有 skill”，而是：

> **把这个 skill 从 onboarding 管理器，升级成真正的项目自进化引擎。**
