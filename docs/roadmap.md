# 路线图：从 MVP 到通用 Core

## 1. 当前状态

**已完成**：
- [x] 架构设计稿（Core/Adapter 边界）
- [x] OpenClaw MVP 方案/骨架（含 OpenClaw-first 修订）
- [x] 核心模块伪代码实现
- [x] **搜索 Provider 层设计**（Tavily / Brave / DuckDuckGo 可插拔）
- [x] **代码架构指南**（开发/维护者文档）
- [x] **用户手册**（安装/配置/使用文档）
- [x] **providers/ 目录骨架**（base.py, tavily.py, brave.py, duckduckgo.py）

**进行中**：
- [ ] roadmap.md 完成/待完成标记（本文档）
- [ ] 实际 Python 代码文件（core/ 和 adapter_openclaw/ 的真实实现）
- [ ] 配置文件初始化

**待完成**：
- [ ] Core 各模块的完整实现
- [ ] Adapter 各模块的完整实现
- [ ] Orchestrator 完整实现
- [ ] SKILL.md 完善
- [ ] 端到端集成测试

---

## 2. 分阶段路线图

### Phase 0：环境准备

**状态：已完成**
- [x] 创建目录结构
- [x] 初始化 Python 模块（`__init__.py`）
- [x] 配置文件模板
- [x] providers/ 搜索层骨架

---

### Phase 1：Core MVP

**状态：部分完成（代码在 docs/ 中为伪代码，需转为真实 .py 文件）**

```
tasks:
  - id: p1-1
    title: 实现数据模型
    status: pending
    description: models.py 完整实现

  - id: p1-2
    title: 实现接口定义
    status: pending
    description: interfaces.py 完整实现

  - id: p1-3
    title: 实现案例库
    status: pending
    description: case_library.py

  - id: p1-4
    title: 实现调研模块
    status: pending
    description: investigator.py

  - id: p1-5
    title: 实现诊断引擎
    status: pending
    description: diagnose.py

  - id: p1-6
    title: 实现方案生成
    status: pending
    description: planner.py

  - id: p1-7
    title: 实现评分模块
    status: pending
    description: critic.py

  - id: p1-8
    title: 实现审批模块
    status: pending
    description: approver.py

  - id: p1-9
    title: 实现执行模块
    status: pending
    description: executor.py

  - id: p1-10
    title: 实现学习模块
    status: pending
    description: learner.py

  - id: p1-11
    title: 单元测试
    status: pending
    description: 为各模块编写基础测试
```

**验收标准**：
- Core 模块可独立 import，不依赖 OpenClaw
- 所有接口正确抽象，可 mock 测试

---

### Phase 2：OpenClaw Adapter

**状态：部分完成（代码在 docs/ 中为伪代码，需转为真实 .py 文件）**

```
tasks:
  - id: p2-1
    title: 实现 TaskExecutor
    status: pending
    description: sessions_spawn/wait 封装

  - id: p2-2
    title: 实现 StateManager
    status: pending
    description: 文件系统状态存储

  - id: p2-3
    title: 实现 Bridge
    status: pending
    description: 桥接器，持有所有 Adapter 实例

  - id: p2-4
    title: 实现 Notifier
    status: pending
    description: message 封装，审批通知

  - id: p2-5
    title: 实现 Scheduler
    status: pending
    description: cron 任务注册

  - id: p2-6
    title: 实现 Orchestrator
    status: pending
    description: 主流程编排器

  - id: p2-7
    title: 集成测试
    status: pending
    description: 端到端流程测试
```

---

### Phase 3：交互优化

**状态：未开始**

```
tasks:
  - id: p3-1
    title: 优化输出格式
    status: pending
    description: 方案、评分等以更友好的格式展示

  - id: p3-2
    title: 添加进度反馈
    status: pending
    description: 各阶段完成时发送进度通知

  - id: p3-3
    title: 错误处理优化
    status: pending
    description: 优雅处理各阶段可能的错误

  - id: p3-4
    title: 帮助/提示系统
    status: pending
    description: 用户输入 help 时显示可用命令
```

---

### Phase 4：案例库充实

**状态：未开始**

```
tasks:
  - id: p4-1
    title: 手工添加种子案例
    status: pending
    description: 手动输入 5-10 个高质量案例

  - id: p4-2
    title: 自动案例回写
    status: pending
    description: 每次执行后自动生成案例

  - id: p4-3
    title: 案例检索优化
    status: pending
    description: 引入 TF-IDF 或简单向量检索
```

---

### Phase 5：评分校准

**状态：未开始**

```
tasks:
  - id: p5-1
    title: 收集评分反馈
    status: pending
    description: 记录人类对 AI 评分的修正

  - id: p5-2
    title: 分析偏差模式
    status: pending
    description: 找出常见偏差，调整权重

  - id: p5-3
    title: 更新评分算法
    status: pending
    description: 基于反馈迭代 Critic 模块
```

---

### Phase 6：Core 抽象（解耦）

**状态：未来目标**

```
tasks:
  - id: p6-1
    title: 移除 OpenClaw 依赖
    status: pending
    description: Core 模块完全不引用 OpenClaw

  - id: p6-2
    title: 引入协议层
    status: pending
    description: 定义标准协议，Adapter 通过协议通信

  - id: p6-3
    title: 状态存储抽象
    status: pending
    description: IStateStore 接口，支持多种存储后端

  - id: p6-4
    title: 文档化 Core API
    status: pending
    description: 编写 Core 独立使用的文档
```

---

### Phase 7：多 Adapter 支持

**状态：未来目标**

```
tasks:
  - id: p7-1
    title: 设计 LangChain Adapter
    status: pending

  - id: p7-2
    title: 设计 CrewAI Adapter
    status: pending

  - id: p7-3
    title: Adapter 切换机制
    status: pending

  - id: p7-4
    title: 跨平台测试
    status: pending
```

---

### Phase 8：独立发布

**状态：未来目标**

```
tasks:
  - id: p8-1
    title: 整理项目结构
    status: pending

  - id: p8-2
    title: 编写完整文档
    status: pending

  - id: p8-3
    title: 发布 PyPI
    status: pending

  - id: p8-4
    title: 建立社区
    status: pending
```

---

## 3. 里程碑

| 里程碑 | 状态 | 交付物 |
|---|---|---|
| M1: 骨架完成 | ✅ 已完成 | 目录结构 + 配置文件 + providers 骨架 |
| M2: Core MVP | 🔄 进行中 | 可运行的 Core 模块（待实现真实 .py 文件）|
| M3: Adapter 完成 | 🔄 进行中 | OpenClaw 可用版本 |
| M4: 首次演示 | ⏳ 待开始 | 端到端运行演示 |
| M5: 案例库充实 | ⏳ 待开始 | 20+ 案例 |
| M6: Core 独立 | ⏳ 未来 | 无 OpenClaw 依赖的 Core |
| M7: 多平台 | ⏳ 未来 | LangChain/CrewAI Adapter |
| M8: 开源发布 | ⏳ 未来 | PyPI 包 |

---

## 4. 资源估算

| 阶段 | 人工天 | 状态 |
|---|---|---|
| Phase 0-1 | 8天 | 🔄 进行中（文档完成，代码待实现）|
| Phase 2 | 5天 | 🔄 进行中 |
| Phase 3 | 3天 | ⏳ 待开始 |
| Phase 4-5 | 持续 | ⏳ 待开始 |
| Phase 6-8 | 15天 | ⏳ 未来 |

---

## 5. 下一步行动

### 立即可执行（今天/本周）

1. **将 docs/ 中的伪代码转为真实 .py 文件**
   - `core/models.py`
   - `core/interfaces.py`
   - `core/investigator.py` ~ `core/case_library.py`
   - `adapter_openclaw/task_executor.py` ~ `adapter_openclaw/orchestrator.py`

2. **完成首次端到端演示**
   - 创建一个 demo 项目
   - 运行完整流程（调研→诊断→方案→评分→审批→执行→学习）

3. **完善 SKILL.md**
   - 定义触发词
   - 编写使用示例

### 短期内

1. 实现 Core 模块（Phase 1）
2. 实现 OpenClaw Adapter（Phase 2）
3. 完成首次端到端演示（Phase 3-4）

---

## 6. 风险与缓解

| 风险 | 缓解策略 |
|---|---|
| OpenClaw 工具能力变化 | 接口隔离（interfaces.py），随时替换 Adapter |
| 项目范围蔓延 | 严格按 MVP 范围交付 |
| 评分系统主观性 | 人工校准 + 案例参照 |
| 状态文件膨胀 | 设计分片存储 + SQLite 迁移计划 |
| Provider API 变更 | 统一接口，可快速替换 Provider 实现 |
