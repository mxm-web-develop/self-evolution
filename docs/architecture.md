# 架构设计稿：通用 Core + OpenClaw Adapter 双层架构

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Human / User                            │
│              （审批节点、指令输入、结果查看）                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  OpenClaw Adapter Layer                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ TaskExec │ │Scheduler │ │StateMgr  │ │  Notifier        │ │
│  │(sessions │ │ (cron)   │ │(memory/  │ │  (message)       │ │
│  │ _spawn)  │ │          │ │ files)  │ │                  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │SkillLoader│ │WebFetch  │ │Canvas    │ │  (extensible)    │ │
│  │(skills)  │ │(web_fetch│ │Renderer  │ │                  │ │
│  └──────────┘ │ /search) │ │          │ │                  │ │
│               └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │ 标准化接口（协议层）
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │Investigat│ │Diagnose  │ │Planner   │ │  Critic          │ │
│  │or        │ │Engine    │ │          │ │  (Scorer)        │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │Approver  │ │Executor  │ │Learner   │ │  CaseLibrary    │ │
│  │(Human)   │ │          │ │(Feedback)│ │                  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core/Adapter 边界定义

### Core（平台无关层）

**职责**：业务逻辑、决策流程、数据结构
**依赖**：纯 Python 标准库 + JSON，无外部依赖
**可移植性**：可独立运行，不引用任何 AI 框架

```
core/
├── investigator.py     # 调研模块
├── diagnose.py         # 诊断引擎
├── planner.py          # 方案生成
├── critic.py           # 评分/批判
├── approver.py         # 审批接口（抽象）
├── executor.py         # 执行接口（抽象）
├── learner.py          # 学习回写
├── case_library.py     # 案例库
├── state.py            # 状态机定义
├── models.py           # 数据模型（Pydantic/dataclass）
└── interfaces.py       # Adapter 抽象接口
```

### Adapter（平台适配层）

**职责**：工具映射、协议转换、平台特性
**依赖**：OpenClaw SDK / 工具接口

```
adapter-openclaw/
├── task_executor.py    # sessions_spawn 封装
├── scheduler.py        # cron 封装
├── state_manager.py    # memory/文件 封装
├── notifier.py         # message 封装
├── skill_loader.py     # skills 封装
├── web_researcher.py   # web_search/web_fetch 封装
├── canvas_renderer.py  # canvas 封装
├── openclaw_bridge.py   # Core ↔ Adapter 粘合剂
└── config.py           # OpenClaw 特定配置
```

### 通信协议（Core ↔ Adapter）

```python
# interfaces.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class ITaskExecutor(ABC):
    @abstractmethod
    def spawn(self, task: Task, context: Dict) -> str:
        """返回 session_id"""
        pass

    @abstractmethod
    def wait(self, session_id: str, timeout_ms: int) -> TaskResult:
        pass

class IScheduler(ABC):
    @abstractmethod
    def schedule(self, cron_expr: str, handler: str, payload: Dict) -> str:
        """返回 job_id"""
        pass

class IStateStore(ABC):
    @abstractmethod
    def save(self, key: str, state: ProjectState) -> None:
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[ProjectState]:
        pass

class INotifier(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str, channel: str) -> None:
        pass

class IWebResearcher(ABC):
    @abstractmethod
    def search(self, query: str, depth: int) -> SearchResult:
        pass

    @abstractmethod
    def fetch(self, url: str) -> str:
        pass
```

---

## 3. 三维优化框架

项目进化系统需要同时优化三个维度：

### 3.1 业务维度（Business）

**目标**：解决真实问题，创造可衡量价值

| 指标 | 说明 | 优化方向 |
|---|---|---|
| 问题覆盖率 | 多少用户问题被解决 | 扩大案例库 |
| 方案采纳率 | 生成的方案被审批通过的比例 | 提高评分准确性 |
| 执行成功率 | 方案执行后达成目标的比例 | 改进 Executor |
| 价值交付速度 | 从问题到解决的时间 | 优化流程瓶颈 |

### 3.2 交互维度（Interaction）

**目标**：人类在环流程中的体验

| 指标 | 说明 | 优化方向 |
|---|---|---|
| 调研信息完整度 | 背景/竞品/约束是否充分 | 丰富 Investigator |
| 方案可读性 | 格式清晰度、语言易懂度 | 改进 Planner 输出格式 |
| 审批效率 | 每次审批所需信息是否齐全 | 减少信息噪音 |
| 反馈体验 | 拒绝/修改时是否有清晰指引 | 改进 Critic 反馈质量 |

### 3.3 功能维度（Functionality）

**目标**：系统本身的工程质量

| 指标 | 说明 | 优化方向 |
|---|---|---|
| 召回率 | 相关案例被检索到的比例 | 优化 CaseLibrary 检索 |
| 评分校准度 | AI 评分与人类评分的一致性 | 持续校准 Critic |
| 工具可用率 | Adapter 层工具调用成功率 | 增强 error handling |
| 状态一致性 | 并发操作不会导致状态损坏 | 引入锁机制 |

---

## 4. 核心闭环流程

```
┌──────────────────────────────────────────────────────────────┐
│                     完整闭环                                  │
│                                                              │
│   ┌─────────┐    ┌──────────┐    ┌─────────┐                │
│   │调研Invest│───▶│诊断Diagn │───▶│方案Plan │                │
│   └─────────┘    └──────────┘    └─────────┘                │
│        │              │              │                      │
│        │              │              ▼                      │
│        │              │         ┌─────────┐                  │
│        │              │         │评分Crit │                  │
│        │              │         └─────────┘                  │
│        │              │              │                      │
│        │              │              ▼                      │
│        │              │         ┌─────────┐                  │
│        │              │         │审批Appr │◀── 人类节点      │
│        │              │         └───┬─────┘                  │
│        │              │             │                        │
│        │              │     拒绝────┘ │通过                   │
│        │              │             ▼                        │
│        │              │        ┌─────────┐                  │
│        │              │        │执行Exec │                  │
│        │              │        └────┬────┘                  │
│        │              │             │                        │
│        └──────────────┴─────────────┘                        │
│                           │                                  │
│                           ▼                                  │
│                    ┌───────────┐                            │
│                    │学习Learner │──▶ 案例库回写              │
│                    └───────────┘                            │
└──────────────────────────────────────────────────────────────┘
```

### 各阶段详细说明

#### 4.1 调研（Investigation）

**输入**：用户问题描述
**输出**：结构化调研报告
**工具**：WebResearcher（Adapter）、CaseLibrary 检索

**调研清单**：
- [ ] 问题背景
- [ ] 相关案例（CaseLibrary 搜索相似案例）
- [ ] 竞品/行业参考（WebResearcher）
- [ ] 约束条件（时间/资源/技术）
- [ ] 成功标准定义

#### 4.2 诊断（Diagnosis）

**输入**：调研报告
**输出**：问题分类 + 根因分析
**工具**：CaseLibrary 模式匹配

**诊断类型**：
- `feature_request`：新功能需求
- `bug_fix`：问题修复
- `optimization`：性能/体验优化
- `architecture`：架构调整
- `unknown`：需要更多信息

#### 4.3 方案规划（Planning）

**输入**：诊断结果
**输出**：候选方案列表（通常 2-3 个）

**方案结构**：
```markdown
## 方案 A：[名称]
- 描述：[一句话]
- 优势：[list]
- 劣势：[list]
- 资源需求：[时间/人力/技术]
- 风险：[list]
- 预期结果：[可衡量指标]
```

#### 4.4 评分（Critique）

**输入**：方案列表
**输出**：每个方案的评分 + 排序

**评分维度**（10分制）：
- 业务价值（Business）：30% 权重
- 技术可行性（Technical）：40% 权重
- 用户体验（UX）：30% 权重

**评分公式**：
```
最终分 = B_score × 0.3 + T_score × 0.4 + U_score × 0.3
```

#### 4.5 审批（Approval）

**输入**：评分后的方案
**输出**：Approved / Rejected / Revise

**审批规则**：
- 最高分 >= 7：推荐通过
- 最高分 5-7：需要修改后重审
- 最高分 < 5：建议否决，说明原因

#### 4.6 执行（Execution）

**输入**：已批准的方案
**输出**：执行状态 + 结果

**执行模式**：
- 简单任务：直接执行
- 复杂任务：拆解为子任务，通过 TaskExecutor 分配

#### 4.7 学习（Learning）

**输入**：执行结果
**输出**：案例回写到 CaseLibrary

**回写条件**（满足任一）：
- 执行成功，效果显著
- 执行失败，教训有价值
- 审批被拒，有启发性

---

## 5. 案例库机制

### 5.1 案例结构

```markdown
# 案例：{标题}

## 元信息
- 日期：YYYY-MM-DD
- 类别：{diagnose_type}
- 标签：[tag1, tag2, tag3]
- 结果：success | failure | partial

## 问题描述
[详细描述]

## 调研摘要
[关键发现]

## 诊断结论
[根因分析]

## 方案
[执行的方案]

## 结果
[可衡量指标的变化]

## 教训/启发
[学到了什么]

## 关联案例
- 相关：{slug1}
- 参考：{slug2}
```

### 5.2 检索机制

**检索字段**：
- 类别（精确匹配）
- 标签（多标签交集）
- 关键词（全文搜索）
- 时间范围（过滤）

**相似度计算**：
- 基于标签重叠 + 关键词 TF-IDF
- 返回 Top-N 最相似案例

---

## 6. 评分体系

### 6.1 评分卡

```
方案：[名称]
评分人：AI_Critic / Human

| 维度 | 分值 (0-10) | 理由 |
|---|---|---|
| 业务价值 | X | ... |
| 技术可行性 | X | ... |
| 用户体验 | X | ... |
| **加权总分** | **X.X** | |

审批意见：[Approved / Rejected / Revise]
备注：[...]
```

### 6.2 评分校准

- 初始：使用预设权重
- 迭代：根据人类反馈调整权重
- 长期：积累评分历史，训练校准模型

---

## 7. OpenClaw 适配点详解

| Core 模块 | OpenClaw 工具 | Adapter 实现 |
|---|---|---|
| Investigator | web_search, web_fetch | WebResearcher |
| Executor | sessions_spawn, exec | TaskExecutor |
| Scheduler | cron | Scheduler |
| CaseLibrary | memory 文件读写 | StateManager |
| Notifier | message | Notifier |
| SkillLoader | skills | SkillLoader |
| Renderer | canvas | CanvasRenderer |

---

## 8. 通用 Core 演进路径

### 阶段 1：OpenClaw MVP（当前）
- Core 和 Adapter 强耦合
- 基于文件的状态存储
- 单实例运行

### 阶段 2：Core 抽象
- Core 完全去除 OpenClaw 依赖
- Adapter 实现接口协议
- 引入 SQLite 状态存储

### 阶段 3：多 Adapter
- LangChain Adapter
- CrewAI Adapter
- 自定义企业 Adapter

### 阶段 4：Core 独立发布
- PyPI 包发布
- 与平台无关的 Core
- 文档 + 教程

---

## 9. 关键设计原则

1. **接口隔离**：Core 不知道 Adapter 存在
2. **依赖倒置**：Adapter 实现 Core 定义的接口
3. **状态外置**：Core 无状态，状态全在 Adapter 层
4. **可插拔**：任何 Adapter 可替换，不影响 Core
5. **人类在环**：关键节点必须人类审批
6. **学习闭环**：每次执行都回写到案例库
