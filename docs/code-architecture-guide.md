# 代码架构指南（面向开发/维护者）

> 本文档说明项目进化系统的代码架构、模块职责、接口契约和扩展点。

---

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     Human / User                        │
│              （审批节点、指令输入、结果查看）              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              adapter_openclaw/（平台适配层）              │
│   bridge.py · task_executor.py · state_manager.py       │
│   notifier.py · scheduler.py · orchestrator.py           │
└─────────────────────┬───────────────────────────────────┘
                      │ 注入依赖（Dependency Injection）
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    core/（业务逻辑层）                    │
│   investigator.py · diagnose.py · planner.py            │
│   critic.py · approver.py · executor.py                  │
│   learner.py · case_library.py · models.py              │
│   interfaces.py                                         │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   providers/（搜索能力层）                │
│   base.py（接口）· tavily.py · brave.py · duckduckgo.py │
└─────────────────────────────────────────────────────────┘
```

### 分层说明

| 层 | 目录 | 职责 | OpenClaw 依赖 |
|---|---|---|---|
| 平台适配层 | adapter_openclaw/ | OpenClaw 工具封装、流程编排 | ✅ 直接依赖 |
| 业务逻辑层 | core/ | 调研/诊断/方案/评分/审批/执行/学习 | ❌ 无依赖 |
| 搜索能力层 | providers/ | 多搜索 Provider 可插拔 | ❌ 无依赖 |

---

## 2. 模块职责详解

### 2.1 core/models.py — 数据模型

所有业务对象的定义，使用 `@dataclass` 便于序列化/反序列化。

| 类 | 职责 |
|---|---|
| `Phase` | 枚举，项目当前阶段（IDLE/INVESTIGATING/DIAGNOSING...） |
| `ProjectState` | 项目状态（phase、context、history） |
| `Task` | 任务单元（用于子代理执行） |
| `Plan` | 方案（描述、评分、审批状态） |
| `Case` | 案例（已完成的经验沉淀） |

**关键约定**：
- 所有 Model 都有 `to_dict()` / `from_dict()` 支持 JSON 序列化
- `ProjectState.context` 是自由字典，各阶段可读写上下文数据

### 2.2 core/interfaces.py — 抽象接口

为后续 Core 解耦准备的接口定义，当前 MVP 阶段未强制使用。

### 2.3 core/investigator.py — 调研模块

**依赖注入**：需要 `search_provider`（providers.base.BaseSearchProvider）和 `case_library`

**输入**：用户描述的问题（字符串）
**输出**：调研报告（dict），包含：
- `problem`：原始问题
- `similar_cases`：案例库检索结果
- `web_findings`：网络搜索结果
- `recommendations`：建议列表

**扩展点**：可注入不同的 search_provider 实现不同搜索能力

### 2.4 core/diagnose.py — 诊断引擎

**依赖**：无外部依赖
**输入**：调研报告（dict）
**输出**：诊断结果（dict），包含：
- `type`：问题类型（feature_request / bug_fix / optimization / architecture / unknown）
- `root_cause`：根因分析
- `priority`：优先级（1-10）
- `confidence`：置信度

**算法**：基于关键词的规则分类，后续可扩展为 ML 模型

### 2.5 core/planner.py — 方案生成

**依赖**：无外部依赖
**输入**：问题 + 诊断 + 调研报告
**输出**：Plan 对象列表（通常3个：保守/激进/折中）

**扩展点**：
- 可注入更多方案模板
- 可支持用户自定义方案生成 Prompt

### 2.6 core/critic.py — 评分模块

**依赖**：无外部依赖
**输入**：Plan 对象
**输出**：评分 dict（business / technical / ux / final / recommendation）

**权重**：business=0.3, technical=0.4, ux=0.3

**扩展点**：
- 可覆盖 `WEIGHTS` 调整权重
- 可注入人类反馈进行校准

### 2.7 core/approver.py — 审批模块

**依赖**：需要 `notifier`（发送消息给人类）
**职责**：仅负责发送审批请求，不做决策

**扩展点**：可接入邮件/Slack 等其他通知渠道

### 2.8 core/executor.py — 执行模块

**依赖**：需要 `bridge.get_executor()`（TaskExecutor）
**输入**：已批准的 Plan
**输出**：执行结果

**流程**：
1. 将 Plan 拆解为 3 个标准子任务
2. 逐个通过 `TaskExecutor.spawn()` 启动子代理
3. 等待结果并汇总

### 2.9 core/learner.py — 学习模块

**依赖**：需要 `case_library`
**输入**：Plan + 执行结果 + 诊断
**输出**：新建的 Case 或 None

**回写条件**：所有执行都值得记录为案例（`return True`）

### 2.10 core/case_library.py — 案例库

**存储**：文件系统（`cases_root/index.json` + `cases_root/{category}/{case_id}.md`）

**索引结构**（`index.json`）：
```json
{
  "cases": [
    {
      "case_id": "case-xxx",
      "category": "feature_request",
      "tags": ["性能", "异步"],
      "outcome": "success",
      "file": "cases/feature_request/case-xxx.md"
    }
  ]
}
```

**检索算法**：基于标签交集 + 关键词重叠计分

---

## 3. adapter_openclaw 模块

### 3.1 bridge.py — 桥接器（中心入口）

```
OpenClawBridge
├── state_manager: StateManager     # 文件状态管理
├── task_executor: TaskExecutor    # 子代理执行
├── notifier: Notifier             # 消息通知
├── scheduler: Scheduler           # 调度计划
└── search_provider: BaseSearchProvider  # 搜索能力
```

所有 Core 模块通过 Bridge 获取 Adapter 能力，实现**依赖倒置**。

### 3.2 task_executor.py — 子代理封装

| 方法 | 说明 |
|---|---|
| `spawn(task, context)` | 启动子代理，返回 session_id |
| `wait(session_id, timeout_ms)` | 等待并获取结果 |

**session_id**：OpenClaw sessions_spawn 返回的唯一标识

### 3.3 state_manager.py — 状态管理

| 方法 | 说明 |
|---|---|
| `save_state(project_id, state)` | 保存状态（带 .bak 备份） |
| `load_state(project_id)` | 加载状态 |
| `save_plan(project_id, plan)` | 保存方案为 Markdown |

**文件布局**：
```
projects/{project_id}/
├── state.json      # 当前状态
└── plans/
    └── {plan_id}.md  # 方案文件
```

### 3.4 orchestrator.py — 流程编排器

持有所有 Core 模块实例，按 Phase 顺序驱动流程：

```
IDLE → INVESTIGATING → DIAGNOSING → PLANNING
    → CRITIQUING → APPROVING → EXECUTING → LEARNING
    → IDLE
```

每次调用 `orchestrator.run()` 执行**一个阶段**，状态外置保证可中断/恢复。

---

## 4. providers 模块

### 4.1 统一接口契约

```python
class BaseSearchProvider:
    name: str                    # Provider 唯一标识
    requires_api_key: bool       # 是否需要 API Key

    def search(query: str, count: int) -> List[SearchResult]: ...
    def fetch(url: str, max_chars: int) -> str: ...
    def health_check() -> bool: ...
```

### 4.2 新增 Provider 步骤

1. 在 `providers/` 下创建 `{provider_name}.py`
2. 继承 `BaseSearchProvider`
3. 实现 `search()` 和 `fetch()`
4. 在 `providers/__init__.py` 的 `get_provider()` 中添加分支
5. 在 `projects/{id}/config.yaml` 中配置名称

---

## 5. 状态流转详解

```
┌──────────────────────────────────────────────────────────────┐
│                     Phase 状态机                              │
│                                                              │
│  ┌──────┐  run()   ┌────────────┐  run()   ┌──────────┐    │
│  │ IDLE │─────────▶│INVESTIGATING│─────────▶│DIAGNOSING │    │
│  └──┬───┘          └──────┬─────┘          └────┬─────┘    │
│     │                      │                    │           │
│     │  save_state           │  save_state        │ save_state│
│     ◀───────────────────────┴────────────────────┘           │
│     │                                                       │
│     │  run()                                                 │
│     ▼                                                       │
│  ┌──────────┐  run()   ┌───────────┐  run()   ┌─────────┐ │
│  │ PLANNING │─────────▶│ CRITIQUING │─────────▶│APPROVING│ │
│  └──────────┘          └───────────┘          └────┬────┘ │
│                                                      │      │
│     ◀──────────────── human approves ─────────────────┘      │
│     │                                                       │
│     │  run()                                                 │
│     ▼                                                       │
│  ┌──────────┐  run()   ┌──────────┐  run()                 │
│  │ EXECUTING│─────────▶│ LEARNING │───────────────────────▶│
│  └──────────┘          └──────────┘                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. 文件布局与加载顺序

```
# 1. 加载配置
projects/{id}/config.yaml
    └── 读取 search.provider, project.id 等

# 2. 初始化 Bridge
adapter_openclaw/bridge.py
    └── 注入 projects_root, cases_root, search_provider

# 3. 初始化 Core 模块
adapter_openclaw/orchestrator.py
    └── ProjectEvolutionOrchestrator.__init__()
        └── Investigator(search_provider, case_library)
        └── DiagnoseEngine()
        └── Planner()
        └── Critic()
        └── Approver()
        └── Executor(bridge)
        └── Learner(case_library)

# 4. 运行流程
orchestrator.run(project_id, problem, human_approved)
    └── 按 Phase 逐步执行，状态保存到 state.json
```

---

## 7. 错误处理约定

| 场景 | 处理策略 |
|---|---|
| Provider 搜索失败 | 自动尝试 fallback provider |
| 子代理超时 | sessions_yield timeout 后标记失败 |
| 文件状态损坏 | 读取 `.bak` 备份文件 |
| 配置缺失 | 抛出 ValueError，提示具体字段 |
| 阶段流转异常 | 状态不变，返回错误信息 |

---

## 8. 测试策略

### 8.1 Core 模块（无依赖测试）

```python
# tests/test_critic.py
from core.critic import Critic
from core.models import Plan

def test_score_plan():
    plan = Plan(
        plan_id="test", project_id="p",
        title="Test", description="",
        pros=["快速"], cons=["风险高"],
        resource_estimate={"days": 1, "people": 1, "cost": "low"},
        risks=["失败风险"], expected_outcomes=["上线"]
    )
    critic = Critic()
    scores = critic.score_plan(plan)
    assert 0 <= scores["final"] <= 10
```

### 8.2 Provider Mock 测试

```python
# tests/test_providers.py
from unittest.mock import patch
from providers.base import SearchResult

@patch("providers.tavily.TavilyClient")
def test_tavily_search(mock_client):
    mock_client.return_value.search.return_value = {
        "results": [{"title": "Test", "url": "http://x", "content": "..."}]
    }
    from providers.tavily import TavilySearchProvider
    provider = TavilySearchProvider(api_key="test")
    results = provider.search("test")
    assert len(results) == 1
```

---

## 9. 扩展点汇总

| 模块 | 扩展点 | 方式 |
|---|---|---|
| Investigator | 搜索能力 | 注入不同 search_provider |
| DiagnoseEngine | 诊断算法 | 覆盖 `_classify()` / `_analyze_root_cause()` |
| Planner | 方案生成 | 注入方案模板或 LLM Prompt |
| Critic | 评分权重 | 覆盖 `WEIGHTS` 字典 |
| CaseLibrary | 存储后端 | 实现 `IStateStore` 接口 |
| Notifier | 通知渠道 | 注入不同 Notifier 实现 |
| Executor | 任务拆分 | 覆盖 `_decompose()` |

---

## 10. 命名规范

| 规范 | 示例 |
|---|---|
| 类名 | PascalCase（`ProjectEvolutionOrchestrator`） |
| 函数/方法 | snake_case（`save_state`, `get_best_plan`） |
| 常量 | UPPER_SNAKE_CASE（`DEFAULT_COUNT`, `WEIGHTS`） |
| 文件名 | snake_case（`state_manager.py`） |
| 配置字段 | kebab-case（`search-provider`, `fallback-providers`） |
