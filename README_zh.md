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
（我会识别并加载 self-evolution skill）

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
