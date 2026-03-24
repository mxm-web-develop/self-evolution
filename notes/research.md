# 研究笔记

## 1. OpenClaw 能力图谱（用于 Adapter 设计）

### 核心工具映射

| OpenClaw 能力 | 对应 Adapter 插槽 | 用途 |
|---|---|---|
| `sessions_spawn` | 执行引擎 | 启动子代理执行专项任务 |
| `cron` | 定时调度器 | 周期性健康检查、进度追踪 |
| `memory/文件` | 知识存储 | 案例库、评分历史、项目状态 |
| `skills` | 技能扩展 | 加载专用处理模块 |
| `message` | 通信适配 | 向用户/频道推送通知 |
| `web_search` | 外部调研 | 收集竞品信息、市场数据 |
| `web_fetch` | 内容抓取 | 读取文档、页面内容 |
| `exec` | 本地执行 | 操作文件系统、运行脚本 |
| `canvas` | 可视化 | 项目进度展示、图表渲染 |

### OpenClaw 限制与边界

- **无内置数据库**：依赖文件（JSON/Markdown）做持久化
- **无原生工作流引擎**：需要自己实现状态机
- **子会话隔离**：sessions_spawn 的结果需通过 `sessions_yield` 回收
- **消息有长度限制**：大内容需分片或存储到文件

---

## 2. 现有 AI Agent 架构参考

### AutoGPT / BabyAGI 模式
- 任务链式执行（Task → Execution → Result → Next Task）
- 简单但缺乏：评估、审批、学习机制

### MetaGPT / ChatDev 模式
- 角色扮演 + SOP 流程
- 过于复杂，不适合轻量级项目

### 我们的定位
- **轻量级、可插拔**：Core 极简，Adapter 做厚
- **人类在环**：调研→诊断→方案后需人类审批
- **学习闭环**：执行结果回写到知识库

---

## 3. 关键设计决策记录

### Decision 1: Core/Adapter 分离原则
- **Core** 不引用任何 OpenClaw 特有工具
- **Adapter** 只做工具映射，不含业务逻辑
- 未来可替换为 LangChain Adapter / CrewAI Adapter

### Decision 2: 状态存储
- **MVP 阶段**：JSON 文件 + Markdown
- **演进方向**：SQLite → PostgreSQL
- 状态文件命名：`{project-id}/state.json`

### Decision 3: 评分体系
- 三维度：业务价值、技术可行性，用户体验
- 10分制，权重可配置
- 审批阈值：默认 >= 7 分可通过

### Decision 4: 案例库格式
- 每个案例：`cases/{category}/{slug}.md`
- 结构：问题描述 → 诊断 → 方案 → 结果 → 标签
- 支持按标签检索

---

## 4. OpenClaw 工具深度分析

### sessions_spawn
```
用途：启动子代理执行任务
限制：需要 sessions_yield 回收结果
adapter 设计：TaskExecutor 模块封装
```

### cron
```
用途：定时任务（健康检查、提醒）
限制：定时精度依赖系统 cron
adapter 设计：Scheduler 模块封装
```

### memory 文件系统
```
用途：持久化状态
限制：无事务保证
adapter 设计：StateManager 模块封装，写入前做备份
```

### skills
```
用途：动态加载专用技能
限制：skill 路径需预先配置
adapter 设计：SkillLoader 模块，按需加载
```

---

## 5. 风险与备选

| 风险 | 概率 | 影响 | 应对 |
|---|---|---|---|
| OpenClaw 工具能力变化 | 低 | 高 | 抽象接口隔离，Adapter 可替换 |
| 大项目状态文件膨胀 | 中 | 中 | 分片存储 + SQLite 迁移计划 |
| 子会话结果丢失 | 低 | 高 | sessions_yield 强制等待，设置 timeout |
| 评分主观性强 | 高 | 低 | 多人校准 + 历史案例参照 |
