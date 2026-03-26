# Self-Evolution

An AI-powered project evolution system that guides projects through **investigation → diagnosis → planning → execution → learning** — a complete closed loop.

---

## Installation

### Step 1: Download

**Option A: Git clone**
```bash
cd ~/.openclaw/skills
git clone https://github.com/mxm-web-develop/self-evolution.git
```

**Option B: Download ZIP**
Download the ZIP from the [GitHub repo](https://github.com/mxm-web-develop/self-evolution) and extract to `~/.openclaw/skills/self-evolution/`

### Step 2: Place in the correct location

OpenClaw searches for skills in three locations (in order of precedence):

| Location | Scope | Command |
|----------|-------|---------|
| `~/.openclaw/workspace/skills/` | Current workspace only | `mkdir -p ~/.openclaw/workspace/skills` |
| `~/.openclaw/skills/` | All agents on this machine | `mkdir -p ~/.openclaw/skills` |
| Built-in bundled skills | OpenClaw internal | No action needed |

**Recommended: put it in `~/.openclaw/skills/`** so any workspace can use it:

```bash
mv self-evolution ~/.openclaw/skills/
```

To verify installation, just talk to OpenClaw naturally:
```
analyze my mxmaiwebsite project
what projects do I have
help me set up a new project
```

---

## How It Works

### Step 1: Tell me your project name

No commands to memorize. Just say what you want:

```
optimize mxmaiwebsite
check on pixgen
look at supermxmai
```

**What happens:**
1. I scan the workspace to find matching projects
2. I ask you to confirm: "You mean the project at `/path/to/mxmaiwebsite`?"
3. I check whether this project already has a record

---

### Step 2: Answer a few questions (first time only)

If it's a new project or information is incomplete, I'll ask specific questions based on what I found in your code:

```
I see your site uses React + Vite,
and the hero currently says "Full-stack Developer".
1. Do you want visitors to immediately understand what you do? Or is showcasing work more important?
2. You have a fox mascot — do you want to strengthen it or tone it down?
3. How's the page load speed in your experience?
```

Each question is grounded in your actual code, not generic. After you answer, I build a project profile.

---

### Step 3: I research and diagnose

I will:
- Scan your code structure
- Research what mature projects in your category look like
- Assess your project's current maturity level
- Identify the highest-priority gaps

You get a clear report:

```
Project maturity: Relatively mature

Highest priority gaps (by order):
1. Brand expression & positioning clarity (gap: high)
2. Visual system & consistency (gap: high)
3. Performance & load quality (gap: high)
4. Interaction feedback & browsing smoothness (gap: medium-high)
...
```

---

### Step 4: I present multiple plans to choose from

Each improvement direction gets its own plan, containing:
- Current state vs. maturity standard
- Concrete action items

```
📋 Plan A: Brand Expression & Positioning
  Current: Brand signals are fragmented, visitors can't pin down your positioning
  Target: Visitors understand what you do and why you're trustworthy within 5 seconds
  Actions:
  • Rewrite the hero value proposition
  • Define signature projects and capability tags
  • Add clear collaboration/contact entry point
```

---

### Step 5: You approve, I execute

```
approve plan A
```

After you confirm, I start executing. Results get written back to the project record.

---

### Step 6: I learn automatically

After each round, insights are written to the shared memory:
- Which improvements had the most impact
- Which approaches worked best for this project type

Future projects can draw on this without starting from scratch.

---

## Example Commands

| You say | I do |
|---------|------|
| `optimize mxmaiwebsite` | Identify project → Confirm → Start analysis |
| `check on pixgen` | Identify project → Check records → Continue |
| `build a new AI writing backend` | New project → Onboarding → Start |
| `what projects do I have` | List all projects with status |
| `approve plan B` | Execute plan B |
| `don't run it yet, what else needs work` | Continue analysis |

---

## Directory Structure

```
~/.openclaw/skills/self-evolution/
├── SKILL.md                  # OpenClaw Skill entry point
├── README.md                 # This file
├── README_zh.md              # 中文版 / Chinese version
├── memory/                   # Shared cross-project memory
│   ├── insights/            # General insights
│   ├── project-types/        # Experience by project type
│   └── sessions/            # Per-session analysis records
├── projects/                # Project-isolated data
│   └── {project-id}/
│       ├── profile.md        # Project profile
│       ├── config.yaml      # Project config
│       ├── state.json       # Runtime state
│       └── analysis/
│           ├── investigation.md
│           ├── gaps.md
│           ├── plans/
│           └── outcomes/
├── scripts/                # Executable scripts
└── references/             # Reasoning framework prompt templates
```

---

## How the Skill Triggers

OpenClaw automatically scans all directories under `~/.openclaw/skills/` and loads the `SKILL.md` in each one.

The `description` field in the YAML frontmatter controls when the skill activates:

```yaml
---
name: self-evolution
description: Project self-evolution analysis... triggers when the user wants to analyze, diagnose, plan, or optimize a project.
---
```

When you say something like "analyze", "optimize", "research", or "check on" a project, OpenClaw loads the self-evolution skill automatically.

---

## FAQ

**Q: Do I need to type `/evolve xxx` every time?**
No. Just describe what you want naturally, like "check on my mxmaiwebsite project".

**Q: Can I track multiple projects at once?**
Yes. I keep track of each project's state and history. Just mention the project name and I'll pick up where we left off.

**Q: My project is on GitHub — how do I connect it?**
Just tell me, like "connect my GitHub project mxm-web-develop/somerepo" and I'll scan it to understand the structure.

**Q: Can I start from scratch with a new project?**
Yes. Tell me what you want to build, I'll ask a few key questions to understand your goals, then start the analysis.

**Q: Nothing happened after I installed the skill. What do I do?**
Say "reload skills" or "refresh skills" in OpenClaw, or restart the OpenClaw gateway.

---

## Maintainer

Zhang Hanfeng (mxmai)


# Self-Evolution 项目进化助手

帮助项目完成 **调研 → 诊断 → 规划 → 执行 → 学习** 完整闭环的智能体。

---

## 安装

### 第一步：下载

**方式一：Git clone**
```bash
cd ~/.openclaw/skills
git clone https://github.com/mxm-web-develop/self-evolution.git
```

**方式二：下载 ZIP**
在 [GitHub 仓库](https://github.com/mxm-web-develop/self-evolution) 下载 ZIP，解压到 `~/.openclaw/skills/self-evolution/`

### 第二步：放到正确位置

OpenClaw skill 搜索三个位置（按优先级）：

| 位置 | 说明 | 命令 |
|------|------|------|
| `~/.openclaw/workspace/skills/` | 仅当前 workspace 可见 | `mkdir -p ~/.openclaw/workspace/skills` |
| `~/.openclaw/skills/` | 所有 agent 共享 | `mkdir -p ~/.openclaw/skills` |
| 内置 bundled skills | OpenClaw 内置 | 无需操作 |

**推荐放到 `~/.openclaw/skills/`**（共享位置，任何 workspace 都能用）：

```bash
# 把下载的 self-evolution 放到 ~/.openclaw/skills/
mv self-evolution ~/.openclaw/skills/
```

验证是否安装成功：
直接跟 OpenClaw 说：
```
告诉我有哪些项目
```

---

## 快速开始

### 第一步：告诉我项目名字

不需要记任何命令，直接说你想做什么：

```
优化一下 mxmaiwebsite
帮我看看 supermxmai 这个项目
跟进一下 pixgen
```

**我会做：**
1. 扫描 workspace 找到匹配的项目
2. 问你"你说的是 xxx 这个项目吗？"确认
3. 检查有没有这个项目的记录

---

### 第二步：回答我的问题（首次接入）

如果是新项目或者信息不完整，我会基于代码扫描结果问你几个具体问题：

```
我看你的网站用了 React + Vite，
英雄区目前写着 'Full-stack Developer'。
1. 你希望访客第一眼就理解你做什么吗？还是更希望展示作品？
2. 目前有狐狸吉祥物，你希望继续强化还是弱化？
3. 你觉得现在的页面加载速度怎么样？
```

每个问题都基于代码实际情况，不是泛泛而谈。回答完我整理成项目画像。

---

### 第三步：我做调研和诊断

我会：
- 扫描你的代码结构
- 搜索同类成熟项目的做法
- 分析你的项目当前成熟度
- 找出最需要优先改进的地方

输出是一份清晰的分析报告：

```
项目成熟度：相对成熟

最需要改进的地方（按优先级排序）：
1. 品牌表达与定位清晰度（gap: 高）
2. 视觉系统与一致性（gap: 高）
3. 性能与加载质量（gap: 高）
4. 交互反馈与浏览流畅度（gap: 中高）
...
```

---

### 第四步：我给你多个方案选择

每个需要改进的方向生成一个方案，包含：
- 现状是什么
- 成熟的标准是什么
- 具体要做什么（行动清单）

```
📋 方案A：品牌表达与定位清晰度
  现状：品牌碎片化，访客不清楚你的定位
  目标：访客5秒内理解你做什么、为什么值得信任
  行动：
  • 重写首屏价值主张
  • 明确代表作和能力标签
  • 补齐合作入口
```

---

### 第五步：你批准，我执行

```
批准方案A
```

你确认后我开始执行，完成后把结果写回项目记录。

---

### 第六步：自动沉淀经验

每轮结束后，这次分析学到的洞察会写入记忆库：
- 哪些方向改进效果最好
- 哪些做法在同类项目里有效

下次分析新项目时可以参考，不用从零开始。

---

## 完整对话示例

| 你说 | 我做 |
|------|------|
| `优化一下 mxmaiwebsite` | 识别项目 → 确认 → 开始分析 |
| `跟进一下 pixgen` | 识别项目 → 检查记录 → 继续 |
| `做一个 AI 写作后端项目` | 新建项目 → onboarding → 开始 |
| `看看我有哪些项目` | 列出所有项目及状态 |
| `批准方案B` | 执行方案B |
| `先不执行，说说还有什么要改的` | 继续分析 |

---

## 技术细节

### 目录结构

```
~/.openclaw/skills/self-evolution/
├── SKILL.md                  # OpenClaw Skill 入口
├── README.md                 # 英文版
├── README_zh.md             # 中文版
├── memory/                   # 跨项目共享记忆
│   ├── insights/            # 通用洞察
│   ├── project-types/        # 按项目类型积累的经验
│   └── sessions/              # 每轮分析历史
├── projects/                 # 项目隔离数据
│   └── {project-id}/
│       ├── profile.md        # 项目画像
│       ├── config.yaml      # 配置文件
│       ├── state.json        # 运行状态
│       └── analysis/
│           ├── investigation.md
│           ├── gaps.md
│           ├── plans/
│           └── outcomes/
├── scripts/               # 可执行脚本
└── references/            # 推理框架 prompt 模板
```

### Skill 触发原理

OpenClaw 会自动扫描 `~/.openclaw/skills/` 下的所有目录，加载每个目录里的 `SKILL.md`。

`SKILL.md` 里的 `description` 字段决定了什么时候触发：

```yaml
---
name: self-evolution
description: Project self-evolution... 当用户想分析、诊断、规划、优化一个项目时触发。
---
```

当你说出"analyze"、"optimize"、"research"、"check on"等关键词时，OpenClaw 会自动加载 self-evolution skill。

---

## 常见问题

**Q：需要我每次都说 `/evolve xxx` 吗？**
不需要。直接说你想做什么就行，比如"帮我看看 mxmaiwebsite"。

**Q：我有多个项目，可以同时跟进吗？**
可以。我会记住每个项目的状态和历史，下次说项目名字就能继续。

**Q：我的项目在 GitHub 上，怎么接入？**
告诉我就行，比如"帮我接入 GitHub 上的 mxm-web-develop/someproject"，我会扫描项目结构来了解它。

**Q：完全从零开始可以吗？**
可以。告诉我你想做什么项目，我会先问几个关键问题来了解你的目标，再开始分析。

**Q：skill 安装后没反应怎么办？**
在 OpenClaw 对话里说"reload skills"或"refresh skills"，或者重启 OpenClaw gateway。

---

## 项目发起人

张瀚峰（mxmai）
