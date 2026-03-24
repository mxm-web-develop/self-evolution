# 多项目支持设计（Multi-Project Support）

> 版本：v1.0 | 目标：同时跟踪和管理多个业务项目

## 1. 核心概念

```
self-evolution 框架
    │
    ├── projects/          # 所有业务项目的元数据
    │   ├── index.json    # 项目索引（项目列表 + 活跃项目）
    │   ├── pixgen/       # 项目 A
    │   │   ├── config.yaml
    │   │   ├── profile.json
    │   │   └── state.json
    │   ├── money-machine/ # 项目 B
    │   └── another-project/
    │
    └── cases/            # 跨项目的共享案例库
        ├── index.json
        └── ...
```

**关键点**：`projects/` 下是**业务项目**的元数据，不是 self-evolution 框架本身的代码。

## 2. 项目索引（index.json）

```json
{
  "version": "1.0",
  "updated_at": "2026-03-24T16:00:00Z",
  "active_project_id": "pixgen",
  
  "projects": [
    {
      "id": "pixgen",
      "name": "PixGen",
      "description": "AI 图片生成 SaaS",
      "path": "/Users/mxm_pro/Projects/pixgen",
      "type": "new",
      "status": "active",
      "created_at": "2026-03-24T16:00:00Z",
      "last_active_at": "2026-03-24T16:30:00Z",
      "phase": "PLANNING",
      "onboarding_completed": true
    },
    {
      "id": "money-machine",
      "name": "Money Machine",
      "description": "自动化赚钱流水线",
      "path": "/Users/mxm_pro/.openclaw/workspace/money-machine",
      "type": "existing",
      "status": "active",
      "created_at": "2026-03-10T10:00:00Z",
      "last_active_at": "2026-03-24T14:30:00Z",
      "phase": "LEARNING",
      "onboarding_completed": true
    }
  ]
}
```

## 3. 项目元数据目录结构

每个项目在 `projects/{project-id}/` 下有以下文件：

```
projects/{project-id}/
├── config.yaml          # 项目配置（搜索 Provider、审批阈值等）
├── profile.json         # 项目画像（目标、优先级、自动化边界等）
├── state.json           # 当前进化状态（Phase、进度）
├── investigation.md     # 最近一次调研报告
├── diagnosis.json       # 最近一次诊断结果
├── plans/               # 候选方案
│   ├── plan-A.md
│   ├── plan-B.md
│   └── plan-C.md
├── scores.json          # 评分结果
└── executions/         # 执行记录
    └── {timestamp}/
        ├── plan.md
        └── result.md
```

## 4. 活跃项目上下文

### 4.1 上下文维护

在 OpenClaw 对话中，系统维护以下上下文：

```python
# 每次对话开始时加载
active_project_id = index["active_project_id"]
active_project = load_project_profile(active_project_id)

# 上下文变量（会话级）
ctx.current_project = active_project
ctx.onboarding_step = None  # 或当前 onboarding 步骤
```

### 4.2 切换活跃项目

```
用户输入：/evolve switch money-machine

系统响应：
```
已切换到项目：Money Machine
当前阶段：LEARNING（学习中）
最后活跃：2026-03-24 14:30

当前执行中的任务：无

你可以：
- /evolve money-machine 优化 XX
- /evolve status money-machine
```
```

## 5. 项目生命周期

```
NEW ──→ ONBOARDING ──→ ACTIVE ──→ (可能多次) ──→ ARCHIVED
 │         │             │
 │         │             └── 正常运行，持续优化
 │         │
 │         └── 收集项目画像（目标、优先级、自动化边界）
 │
 └── 尚未完成 onboarding
```

| 状态 | 说明 |
|---|---|
| `NEW` | 创建了目录但未完成 onboarding |
| `ONBOARDING` | onboarding 进行中 |
| `ACTIVE` | onboarding 完成，正常工作 |
| `ARCHIVED` | 暂停/归档，不再主动推进 |

## 6. 跨项目案例共享

案例库 (`cases/`) 是跨项目共享的：

```
cases/
├── index.json
├── feature_request/
├── bug_fix/
├── optimization/
└── architecture/
```

- 案例按**类型**组织（不是按项目）
- 新项目调研时优先检索案例库
- 成功/失败案例学习后写入案例库，供后续项目参考

## 7. 多项目对话示例

```
用户：/evolve
系统：检测到当前活跃项目：PixGen
      当前阶段：PLANNING
      
      你想优化什么？
      （或输入 /evolve switch [项目名] 切换项目）
```

```
用户：/evolve status
系统：
```
📊 项目总览

🏃 活跃项目（2）

1. PixGen        ONBOARDING  → 方案生成中
2. Money Machine ACTIVE      → 等待审批（方案 B）

💤 已归档（0）
```
```

```
用户：/evolve switch pixgen
系统：已切换到 PixGen（新建项目）

请描述项目目标：
（你想做什么？）
```

## 8. 已有项目接入

对于不在 `projects/` 目录下的已有项目：

```bash
# 方式 1：命令行指定路径
/evolve /path/to/existing-project

# 方式 2：移动已有项目到 projects/
mv /path/to/my-app ~/openclaw/workspace/projects/my-app
/evolve switch my-app
```

接入后系统会：
1. 扫描项目结构
2. 尝试推断技术栈
3. 提示用户确认画像
4. 补充业务目标

## 9. 配置文件作用域

```
项目级配置（优先级高）
  projects/{project-id}/config.yaml
  
用户级配置（默认）
  self-evolution/.env 或 ~/.self-evolution/config.yaml
  
系统级配置（兜底）
  self-evolution/core/default_config.yaml
```

### 9.1 配置合并规则

```python
config = merge_configs(
    default_config,      # 系统兜底
    user_config,         # 用户偏好
    project_config,      # 项目定制（最高优先级）
)
```

## 10. 数据迁移

如果从单项目升级到多项目：

```python
# 脚本：migrate_to_multi_project.py
import json
import os

OLD_STATE = "projects/demo/state.json"  # 旧结构

# 读取旧状态
with open(OLD_STATE) as f:
    old = json.load(f)

# 初始化 index.json
index = {
    "version": "1.0",
    "active_project_id": "demo",
    "projects": [{
        "id": "demo",
        "name": old["project_name"],
        "type": "existing",
        "status": "active",
        ...
    }]
}

# 写入新结构
os.makedirs("projects/demo", exist_ok=True)
with open("projects/index.json", "w") as f:
    json.dump(index, f, indent=2)
```

## 11. 命令汇总

| 命令 | 说明 |
|---|---|
| `/evolve` | 当前活跃项目继续 |
| `/evolve [path]` | 接入已有项目（扫描+画像） |
| `/evolve new [目标]` | 新建项目 |
| `/evolve status` | 查看所有项目状态 |
| `/evolve switch [id]` | 切换活跃项目 |
| `/evolve archive [id]` | 归档项目 |
| `/evolve profile [id]` | 查看项目画像 |
| `/evolve delete [id]` | 删除项目（需确认） |
