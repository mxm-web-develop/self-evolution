# OpenClaw MVP 落地方案（OpenClaw-First）

> **定位**：本文档描述如何在 OpenClaw 环境下落地"项目进化助手" MVP。
> 通用 Core 层作为后续抽象目标，MVP 阶段以 OpenClaw 工具链为核心实现。

---

## 1. 设计原则

1. **OpenClaw-First**：优先直接使用 OpenClaw 工具（sessions_spawn / web_search / message 等）
2. **渐进抽象**：Core 模块先与 OpenClaw 紧耦合，后续再解耦为通用层
3. **配置驱动**：搜索 Provider 等能力通过配置文件切换，无需改代码
4. **文件持久化**：状态存于文件系统，MVP 阶段不引入数据库

---

## 2. 目录结构

```
project-evolution/
├── core/                          # 业务逻辑层（当前与 OpenClaw 紧耦合）
│   ├── __init__.py
│   ├── models.py                  # 数据模型（ProjectState, Task, Plan, Case）
│   ├── interfaces.py              # 抽象接口定义（为后续解耦准备）
│   ├── investigator.py            # 调研模块
│   ├── diagnose.py                # 诊断引擎
│   ├── planner.py                 # 方案生成
│   ├── critic.py                  # 评分
│   ├── approver.py                # 审批
│   ├── executor.py                # 执行
│   ├── learner.py                 # 学习回写
│   └── case_library.py            # 案例库
│
├── adapter_openclaw/              # OpenClaw 适配器
│   ├── __init__.py
│   ├── bridge.py                  # 桥接器
│   ├── task_executor.py           # sessions_spawn 封装
│   ├── scheduler.py               # cron 封装（记录调度计划）
│   ├── state_manager.py           # 文件状态管理
│   ├── notifier.py                # message 封装
│   └── orchestrator.py            # 主流程编排器
│
├── providers/                     # 搜索 Provider（可插拔）
│   ├── __init__.py
│   ├── base.py                    # 搜索接口定义
│   ├── tavily.py                  # Tavily 实现（默认）
│   ├── brave.py                   # Brave Search 实现（备选1）
│   └── duckduckgo.py              # DuckDuckGo 实现（备选2/fallback）
│
├── projects/                      # 项目工作区
│   └── {project-id}/
│       ├── config.yaml            # 项目配置
│       ├── state.json             # 当前状态
│       ├── investigation.md       # 调研报告
│       ├── diagnosis.json        # 诊断结果
│       ├── plans/                 # 候选方案
│       │   └── {plan-id}.md
│       ├── scores.json            # 评分结果
│       └── executions/            # 执行记录
│
├── cases/                         # 案例库
│   ├── index.json                 # 案例索引
│   ├── feature_request/
│   ├── bug_fix/
│   ├── optimization/
│   └── architecture/
│
├── skills/
│   └── project-evolution/
│       └── SKILL.md               # 触发词定义
│
└── docs/
    ├── architecture.md            # 架构设计
    ├── openclaw-mvp.md           # 本文档
    ├── search-provider-design.md  # 搜索层设计
    ├── code-architecture-guide.md # 代码架构指南
    ├── user-manual.md            # 用户手册
    └── roadmap.md                # 路线图
```

---

## 3. 数据模型

### 3.1 ProjectState

```python
# core/models.py
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime

class Phase(Enum):
    IDLE = "idle"
    INVESTIGATING = "investigating"
    DIAGNOSING = "diagnosing"
    PLANNING = "planning"
    CRITIQUING = "critiquing"
    APPROVING = "approving"
    EXECUTING = "executing"
    LEARNING = "learning"

@dataclass
class ProjectState:
    project_id: str
    phase: Phase
    created_at: str
    updated_at: str
    current_task: Optional[str] = None
    context: dict = field(default_factory=dict)
    history: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState": ...
```

### 3.2 Task

```python
@dataclass
class Task:
    task_id: str
    title: str
    description: str
    task_type: str  # investigation | planning | execution
    input_data: dict
    status: str = "pending"  # pending | running | done | failed
    result: Optional[dict] = None
    error: Optional[str] = None
```

### 3.3 Plan

```python
@dataclass
class Plan:
    plan_id: str
    project_id: str
    title: str
    description: str
    pros: List[str]
    cons: List[str]
    resource_estimate: dict
    risks: List[str]
    expected_outcomes: List[str]
    scores: Optional[dict] = None
    approved: Optional[bool] = None
    approver_notes: Optional[str] = None
```

### 3.4 Case

```python
@dataclass
class Case:
    case_id: str
    category: str
    tags: List[str]
    problem: str
    investigation_summary: str
    diagnosis: str
    plan_executed: str
    result: str
    lessons: str
    outcome: str  # success | failure | partial
    created_at: str
```

---

## 4. 搜索 Provider 层（可插拔）

> 详见 `docs/search-provider-design.md`

### 快速配置

```yaml
# projects/{id}/config.yaml
search:
  provider: tavily          # tavily | brave | duckduckgo
  tavily:
    api_key: ${TAVILY_API_KEY}
  brave:
    api_key: ${BRAVE_API_KEY}
  fallback:
    - provider: duckduckgo
      enabled: true
    - provider: brave
      enabled: true
```

---

## 5. OpenClaw 工具封装

### 5.1 TaskExecutor（sessions_spawn 封装）

```python
# adapter_openclaw/task_executor.py
import os
import json
from typing import Dict, Optional
from openclaw import sessions_spawn, sessions_yield

class TaskExecutor:
    """通过 sessions_spawn 启动子代理执行任务"""

    def __init__(self, bridge: "OpenClawBridge"):
        self.bridge = bridge

    def spawn(self, task: "Task", context: Dict) -> str:
        """启动子代理，返回 session_id"""
        prompt = self._build_prompt(task, context)
        session_id = sessions_spawn(
            prompt=prompt,
            model="minimax-portal/MiniMax-M2.7",
            instruction="你是一个专业的项目进化助手，执行任务并返回结构化结果。",
        )
        return session_id

    def wait(self, session_id: str, timeout_ms: int = 300000) -> Dict:
        """等待并获取子代理结果"""
        result = sessions_yield(session_id, timeout=timeout_ms)
        return self._parse_result(result)

    def _build_prompt(self, task: "Task", context: Dict) -> str:
        return f"""
任务类型：{task.task_type}
任务标题：{task.title}
任务描述：{task.description}

上下文：
{json.dumps(context, ensure_ascii=False, indent=2)}

请执行任务并返回以下格式的结果：
{{
    "status": "success" | "failure",
    "output": {{...}},
    "error": "错误信息（如有）"
}}
"""
```

### 5.2 StateManager（文件状态封装）

```python
# adapter_openclaw/state_manager.py
import os
import json
import shutil
from pathlib import Path
from typing import Optional

class StateManager:
    """基于文件的持久化状态管理"""

    def __init__(self, projects_root: str):
        self.projects_root = Path(projects_root)

    def save_state(self, project_id: str, state: "ProjectState") -> None:
        """保存项目状态，带备份"""
        state_file = self._state_file(project_id)
        if state_file.exists():
            shutil.copy(state_file, str(state_file) + ".bak")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

    def load_state(self, project_id: str) -> Optional["ProjectState"]:
        """加载项目状态"""
        state_file = self._state_file(project_id)
        if not state_file.exists():
            return None
        with open(state_file, encoding="utf-8") as f:
            data = json.load(f)
        return ProjectState.from_dict(data)

    def _state_file(self, project_id: str) -> Path:
        return self.projects_root / project_id / "state.json"

    def save_plan(self, project_id: str, plan: "Plan") -> None:
        """保存方案"""
        plan_file = self.projects_root / project_id / "plans" / f"{plan.plan_id}.md"
        plan_file.parent.mkdir(parents=True, exist_ok=True)
        with open(plan_file, "w", encoding="utf-8") as f:
            f.write(self._plan_to_md(plan))

    def _plan_to_md(self, plan: "Plan") -> str:
        return f"""# 方案：{plan.title}

## 描述
{plan.description}

## 优势
{chr(10).join(f"- {p}" for p in plan.pros)}

## 劣势
{chr(10).join(f"- {c}" for c in plan.cons)}

## 资源需求
{json.dumps(plan.resource_estimate, ensure_ascii=False, indent=2)}

## 风险
{chr(10).join(f"- {r}" for r in plan.risks)}

## 预期结果
{chr(10).join(f"- {o}" for o in plan.expected_outcomes)}

## 评分
{json.dumps(plan.scores, ensure_ascii=False, indent=2) if plan.scores else "待评分"}

## 审批
状态：{'✅ 通过' if plan.approved else '❌ 拒绝' if plan.approved is False else '⏳ 待审批'}
备注：{plan.approver_notes or '无'}
"""
```

### 5.3 Notifier（消息通知封装）

```python
# adapter_openclaw/notifier.py
from typing import Optional
from openclaw import message

class Notifier:
    """封装 message 工具"""

    def __init__(self, default_channel: str = "webchat"):
        self.default_channel = default_channel

    def notify_user(
        self,
        text: str,
        channel: str = "webchat",
        target: Optional[str] = None
    ) -> None:
        """向用户发送通知"""
        message(
            action="send",
            channel=channel,
            target=target or "main",
            message=text
        )

    def notify_approval_request(
        self,
        project_id: str,
        plan_title: str,
        scores: dict
    ) -> None:
        """发送审批请求"""
        text = f"""📋 **审批请求**

项目：{project_id}
方案：{plan_title}

评分结果：
- 业务价值：{scores.get('business', 'N/A')}
- 技术可行性：{scores.get('technical', 'N/A')}
- 用户体验：{scores.get('ux', 'N/A')}
- **总分：{scores.get('final', 'N/A')}**

请回复：Approve / Reject / Revise
"""
        self.notify_user(text)
```

### 5.4 Scheduler（定时任务封装）

```python
# adapter_openclaw/scheduler.py
from dataclasses import dataclass
from typing import Callable, Dict

@dataclass
class ScheduledJob:
    job_id: str
    cron_expr: str
    handler_name: str
    payload: Dict

class Scheduler:
    """调度器（记录调度计划，实际触发通过外部 cron）"""

    def __init__(self, state_manager: "StateManager"):
        self.state_manager = state_manager
        self.jobs: Dict[str, ScheduledJob] = {}

    def schedule(
        self,
        cron_expr: str,
        handler_name: str,
        payload: Dict
    ) -> str:
        """注册一个定时任务"""
        import uuid
        job_id = str(uuid.uuid4())[:8]
        job = ScheduledJob(
            job_id=job_id,
            cron_expr=cron_expr,
            handler_name=handler_name,
            payload=payload
        )
        self.jobs[job_id] = job
        return job_id

    def get_jobs(self) -> Dict[str, ScheduledJob]:
        return self.jobs

    def remove(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)
```

---

## 6. 桥接器（Bridge）

```python
# adapter_openclaw/bridge.py
"""OpenClaw Bridge：连接 Core 与 Adapter"""

class OpenClawBridge:
    """
    Core 与 OpenClaw Adapter 之间的桥梁
    持有所有 Adapter 实例，供 Core 调用
    """

    def __init__(
        self,
        projects_root: str,
        cases_root: str,
        search_provider,  # 注入搜索 Provider
        default_channel: str = "webchat"
    ):
        # 初始化各 Adapter
        self.state_manager = StateManager(projects_root)
        self.task_executor = TaskExecutor(self)
        self.notifier = Notifier(default_channel)
        self.scheduler = Scheduler(self.state_manager)
        self.search_provider = search_provider  # 统一搜索接口

    def get_executor(self) -> TaskExecutor:
        return self.task_executor

    def get_state_manager(self) -> StateManager:
        return self.state_manager

    def get_notifier(self) -> Notifier:
        return self.notifier

    def get_scheduler(self) -> Scheduler:
        return self.scheduler

    def get_search_provider(self):
        """获取搜索 Provider"""
        return self.search_provider
```

---

## 7. Core 模块实现

### 7.1 调研模块（使用搜索 Provider）

```python
# core/investigator.py
from typing import Dict, List
from .models import Task

class Investigator:
    """调研模块（使用注入的搜索 Provider）"""

    def __init__(self, search_provider, case_library):
        self.search_provider = search_provider
        self.case_library = case_library

    def investigate(self, problem: str) -> Dict:
        """
        执行调研，返回调研报告
        """
        # 1. 检索相似案例
        similar_cases = self.case_library.search_similar(problem, limit=3)

        # 2. 网络调研（通过 Provider）
        search_results = self.search_provider.search(problem, count=5)

        # 3. 组装调研报告
        report = {
            "problem": problem,
            "similar_cases": similar_cases,
            "web_findings": search_results,
            "recommendations": self._generate_recommendations(similar_cases, search_results)
        }
        return report

    def _generate_recommendations(
        self,
        cases: List[Dict],
        web_results: List[Dict]
    ) -> List[str]:
        recs = []
        for c in cases[:2]:
            recs.append(f"参考案例：{c.get('title', 'unknown')}")
        for r in web_results[:2]:
            recs.append(f"网络参考：{r.get('title', '')}")
        return recs
```

### 7.2 诊断引擎

```python
# core/diagnose.py
from typing import Dict

class DiagnoseEngine:
    """诊断引擎"""

    DIAGNOSE_TYPES = [
        "feature_request",
        "bug_fix",
        "optimization",
        "architecture",
        "unknown"
    ]

    def diagnose(self, investigation_report: Dict) -> Dict:
        problem = investigation_report.get("problem", "")
        diagnose_type = self._classify(problem)
        return {
            "type": diagnose_type,
            "root_cause": self._analyze_root_cause(problem, diagnose_type),
            "priority": self._estimate_priority(problem),
            "confidence": 0.7
        }

    def _classify(self, problem: str) -> str:
        problem_lower = problem.lower()
        if any(k in problem_lower for k in ["新功能", "需要", "希望", "feature"]):
            return "feature_request"
        elif any(k in problem_lower for k in ["bug", "错误", "修复", "问题"]):
            return "bug_fix"
        elif any(k in problem_lower for k in ["慢", "优化", "性能"]):
            return "optimization"
        elif any(k in problem_lower for k in ["架构", "重构", "设计"]):
            return "architecture"
        return "unknown"

    def _analyze_root_cause(self, problem: str, diag_type: str) -> str:
        return f"识别为 {diag_type} 类型，建议按标准流程处理"

    def _estimate_priority(self, problem: str) -> int:
        return min(10, max(1, len(problem) // 20))
```

### 7.3 方案生成

```python
# core/planner.py
from typing import Dict, List
from .models import Plan
import uuid

class Planner:
    """方案生成模块"""

    def generate_plans(
        self,
        problem: str,
        diagnosis: Dict,
        investigation: Dict
    ) -> List[Plan]:
        plans = []
        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="渐进式改进",
            description=f"以最小风险的方式逐步解决：{problem}",
            pros=["风险低", "可快速启动", "易于回滚"],
            cons=["可能不是最优解", "周期较长"],
            resource_estimate={"days": 3, "people": 1, "cost": "low"},
            risks=["可能需要二次迭代"],
            expected_outcomes=["问题缓解", "积累经验"]
        ))
        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="全面重构",
            description=f"从根本上解决：{problem}",
            pros=["一劳永逸", "架构更清晰"],
            cons=["成本高", "风险大", "周期长"],
            resource_estimate={"days": 14, "people": 2, "cost": "high"},
            risks=["可能影响现有功能"],
            expected_outcomes=["彻底解决问题", "提升可维护性"]
        ))
        plans.append(Plan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            project_id="current",
            title="折中方案",
            description=f"在成本和效果间取得平衡：{problem}",
            pros=["平衡风险和收益", "周期适中"],
            cons=["两边都不完美"],
            resource_estimate={"days": 7, "people": 1, "cost": "medium"},
            risks=["需要精细执行"],
            expected_outcomes=["较好解决问题", "可控风险"]
        ))
        return plans
```

### 7.4 评分模块

```python
# core/critic.py
from typing import Dict, List
from .models import Plan

class Critic:
    """评分/批判模块"""

    WEIGHTS = {
        "business": 0.3,
        "technical": 0.4,
        "ux": 0.3
    }

    def score_plan(self, plan: Plan, context: Dict = None) -> Dict:
        business = self._score_business(plan, context)
        technical = self._score_technical(plan)
        ux = self._score_ux(plan)
        final = (
            business * self.WEIGHTS["business"] +
            technical * self.WEIGHTS["technical"] +
            ux * self.WEIGHTS["ux"]
        )
        return {
            "business": round(business, 1),
            "technical": round(technical, 1),
            "ux": round(ux, 1),
            "final": round(final, 1),
            "recommendation": self._get_recommendation(final)
        }

    def _score_business(self, plan: Plan, context: Dict = None) -> float:
        outcome_count = len(plan.expected_outcomes)
        risk_count = len(plan.risks)
        return min(10, max(1, outcome_count * 3 - risk_count * 0.5))

    def _score_technical(self, plan: Plan) -> float:
        days = plan.resource_estimate.get("days", 7)
        people = plan.resource_estimate.get("people", 1)
        effort = days * people
        return max(1, min(10, 20 - effort * 0.5))

    def _score_ux(self, plan: Plan) -> float:
        return max(1, min(10, 10 - len(plan.cons) * 1.5))

    def _get_recommendation(self, final: float) -> str:
        if final >= 7:
            return "推荐通过"
        elif final >= 5:
            return "建议修改后重审"
        else:
            return "建议否决"
```

### 7.5 审批模块

```python
# core/approver.py
from typing import Optional

class Approver:
    """审批模块（人类在环）"""

    def request_approval(
        self,
        plan_title: str,
        scores: Dict,
        notifier
    ) -> None:
        notifier.notify_approval_request(
            project_id="current",
            plan_title=plan_title,
            scores=scores
        )

    def parse_human_decision(self, response: str) -> Optional[bool]:
        response = response.lower().strip()
        if response in ["approve", "通过", "yes", "y", "好", "可以"]:
            return True
        elif response in ["reject", "拒绝", "no", "n", "不行"]:
            return False
        return None
```

### 7.6 执行模块

```python
# core/executor.py
from typing import Dict, List
from .models import Task, Plan

class Executor:
    """执行模块"""

    def __init__(self, bridge):
        self.bridge = bridge

    def execute_plan(
        self,
        plan: Plan,
        task_executor
    ) -> Dict:
        subtasks = self._decompose(plan)
        results = []
        for task in subtasks:
            session_id = task_executor.spawn(task, context={"plan": plan.to_dict()})
            result = task_executor.wait(session_id)
            results.append(result)
        return {
            "status": "completed",
            "subtask_results": results,
            "summary": self._summarize(results)
        }

    def _decompose(self, plan: Plan) -> List[Task]:
        return [
            Task(
                task_id="sub-1",
                title="准备工作",
                description=f"为方案 '{plan.title}' 做准备",
                task_type="execution",
                input_data={}
            ),
            Task(
                task_id="sub-2",
                title="核心执行",
                description=f"执行方案的核心步骤",
                task_type="execution",
                input_data={}
            ),
            Task(
                task_id="sub-3",
                title="验证测试",
                description=f"验证执行结果",
                task_type="execution",
                input_data={}
            ),
        ]

    def _summarize(self, results: List[Dict]) -> str:
        success_count = sum(1 for r in results if r.get("status") == "success")
        return f"完成 {success_count}/{len(results)} 个子任务"
```

### 7.7 学习模块

```python
# core/learner.py
from typing import Dict, Optional
from .models import Case, Plan

class Learner:
    """学习回写模块"""

    def __init__(self, case_library):
        self.case_library = case_library

    def learn_from_execution(
        self,
        plan: Plan,
        execution_result: Dict,
        diagnosis: Dict
    ) -> Optional[Case]:
        if not self._should_learn(plan, execution_result):
            return None
        case = Case(
            case_id=f"case-{plan.plan_id}",
            category=diagnosis.get("type", "unknown"),
            tags=self._extract_tags(plan, diagnosis),
            problem=plan.description,
            investigation_summary="",
            diagnosis=diagnosis.get("root_cause", ""),
            plan_executed=plan.title,
            result=execution_result.get("summary", ""),
            lessons=self._extract_lessons(plan, execution_result),
            outcome=self._determine_outcome(execution_result),
            created_at=self._now()
        )
        self.case_library.add_case(case)
        return case

    def _should_learn(self, plan: Plan, result: Dict) -> bool:
        return True

    def _extract_tags(self, plan: Plan, diagnosis: Dict) -> list:
        tags = [diagnosis.get("type", "unknown")]
        tags.extend([p.lower()[:10] for p in plan.pros[:2]])
        return tags

    def _extract_lessons(self, plan: Plan, result: Dict) -> str:
        return f"执行结果：{result.get('summary', '未知')}"

    def _determine_outcome(self, result: Dict) -> str:
        summary = result.get("summary", "")
        if "completed" in summary.lower():
            return "success"
        return "partial"

    def _now(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
```

### 7.8 案例库

```python
# core/case_library.py
import json
from pathlib import Path
from typing import List, Dict, Optional
from .models import Case

class CaseLibrary:
    """案例库"""

    def __init__(self, cases_root: str):
        self.cases_root = Path(cases_root)
        self._index = self._load_index()

    def _load_index(self) -> Dict:
        index_file = self.cases_root / "index.json"
        if index_file.exists():
            with open(index_file, encoding="utf-8") as f:
                return json.load(f)
        return {"cases": []}

    def _save_index(self) -> None:
        index_file = self.cases_root / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

    def add_case(self, case: Case) -> None:
        category_dir = self.cases_root / case.category
        category_dir.mkdir(parents=True, exist_ok=True)
        case_file = category_dir / f"{case.case_id}.md"
        with open(case_file, "w", encoding="utf-8") as f:
            f.write(self._case_to_md(case))
        self._index["cases"].append({
            "case_id": case.case_id,
            "category": case.category,
            "tags": case.tags,
            "outcome": case.outcome,
            "file": str(case_file)
        })
        self._save_index()

    def search_similar(
        self,
        problem: str,
        limit: int = 3,
        category: Optional[str] = None
    ) -> List[Dict]:
        candidates = self._index["cases"]
        if category:
            candidates = [c for c in candidates if c["category"] == category]
        problem_words = set(problem.lower().split())
        scored = []
        for c in candidates:
            score = len(set(c.get("tags", [])) & problem_words)
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, c in scored[:limit]:
            if score > 0:
                case_file = Path(c["file"])
                if case_file.exists():
                    with open(case_file, encoding="utf-8") as f:
                        content = f.read()
                    results.append({
                        "case_id": c["case_id"],
                        "title": content.split("\n")[0].replace("# ", ""),
                        "score": score,
                        "category": c["category"]
                    })
        return results

    def _case_to_md(self, case: Case) -> str:
        return f"""# 案例：{case.problem[:50]}

## 元信息
- 日期：{case.created_at}
- 类别：{case.category}
- 标签：{", ".join(case.tags)}
- 结果：{case.outcome}

## 问题描述
{case.problem}

## 诊断结论
{case.diagnosis}

## 执行的方案
{case.plan_executed}

## 结果
{case.result}

## 教训/启发
{case.lessons}
"""
```

---

## 8. 主流程编排（Orchestrator）

```python
# adapter_openclaw/orchestrator.py
"""主流程编排器"""

from core.investigator import Investigator
from core.diagnose import DiagnoseEngine
from core.planner import Planner
from core.critic import Critic
from core.approver import Approver
from core.executor import Executor
from core.learner import Learner
from core.case_library import CaseLibrary
from core.models import Phase, Plan

class ProjectEvolutionOrchestrator:
    """项目进化主流程编排器"""

    def __init__(self, bridge):
        self.bridge = bridge
        self._init_core_modules()

    def _init_core_modules(self):
        cases_root = str(self.bridge.state_manager.projects_root.parent / "cases")
        self.investigator = Investigator(
            self.bridge.get_search_provider(),
            CaseLibrary(cases_root)
        )
        self.diagnose_engine = DiagnoseEngine()
        self.planner = Planner()
        self.critic = Critic()
        self.approver = Approver()
        self.executor = Executor(self.bridge)
        self.learner = Learner(CaseLibrary(cases_root))

    def run(self, project_id: str, problem: str, human_approved: bool = False) -> Dict:
        sm = self.bridge.get_state_manager()
        state = sm.load_state(project_id) or self._create_state(project_id, problem)

        # 阶段 1：调研
        if state.phase == Phase.IDLE:
            state.phase = Phase.INVESTIGATING
            sm.save_state(project_id, state)
            investigation = self.investigator.investigate(problem)
            state.context["investigation"] = investigation
            state.phase = Phase.IDLE
            sm.save_state(project_id, state)
            return {"phase": "investigating", "report": investigation}

        # 阶段 2：诊断
        if state.phase == Phase.IDLE:
            state.phase = Phase.DIAGNOSING
            sm.save_state(project_id, state)
            diagnosis = self.diagnose_engine.diagnose(state.context.get("investigation", {}))
            state.context["diagnosis"] = diagnosis
            state.phase = Phase.IDLE
            sm.save_state(project_id, state)
            return {"phase": "diagnosing", "diagnosis": diagnosis}

        # 阶段 3：方案生成
        if state.phase == Phase.IDLE:
            state.phase = Phase.PLANNING
            sm.save_state(project_id, state)
            plans = self.planner.generate_plans(
                problem,
                state.context.get("diagnosis", {}),
                state.context.get("investigation", {})
            )
            state.context["plans"] = [p.__dict__ for p in plans]
            state.phase = Phase.IDLE
            sm.save_state(project_id, state)
            for plan in plans:
                sm.save_plan(project_id, plan)
            return {"phase": "planning", "plans": len(plans)}

        # 阶段 4：评分
        if state.phase == Phase.IDLE:
            state.phase = Phase.CRITIQUING
            sm.save_state(project_id, state)
            scored_plans = []
            for plan_data in state.context.get("plans", []):
                plan = self._dict_to_plan(plan_data)
                scores = self.critic.score_plan(plan, state.context)
                plan.scores = scores
                scored_plans.append(plan)
                sm.save_plan(project_id, plan)
            state.context["scored_plans"] = [p.__dict__ for p in scored_plans]
            state.phase = Phase.IDLE
            sm.save_state(project_id, state)
            return {"phase": "critiquing", "scores": [p.scores for p in scored_plans]}

        # 阶段 5：审批
        if state.phase == Phase.IDLE and not human_approved:
            best_plan = self._get_best_plan(state.context.get("scored_plans", []))
            self.approver.request_approval(
                best_plan.title,
                best_plan.scores,
                self.bridge.get_notifier()
            )
            return {"phase": "approving", "waiting": True, "plan": best_plan.title}

        # 阶段 6：执行
        if state.phase == Phase.IDLE and human_approved:
            state.phase = Phase.EXECUTING
            sm.save_state(project_id, state)
            best_plan = self._get_best_plan(state.context.get("scored_plans", []))
            result = self.executor.execute_plan(
                best_plan,
                self.bridge.get_executor()
            )
            state.context["execution_result"] = result
            state.phase = Phase.LEARNING
            sm.save_state(project_id, state)
            return {"phase": "executing", "result": result}

        # 阶段 7：学习
        if state.phase == Phase.LEARNING:
            case = self.learner.learn_from_execution(
                self._dict_to_plan(state.context.get("scored_plans", [{}])[0]),
                state.context.get("execution_result", {}),
                state.context.get("diagnosis", {})
            )
            state.phase = Phase.IDLE
            sm.save_state(project_id, state)
            return {"phase": "learning", "case_created": case is not None}

        return {"status": "unknown_phase", "phase": state.phase}

    def _create_state(self, project_id: str, problem: str):
        from core.models import ProjectState
        state = ProjectState(
            project_id=project_id,
            phase=Phase.IDLE,
            created_at=self._now(),
            updated_at=self._now(),
            current_task=problem,
            context={"original_problem": problem}
        )
        self.bridge.get_state_manager().save_state(project_id, state)
        return state

    def _get_best_plan(self, plans_data: List[Dict]) -> Plan:
        if not plans_data:
            return Plan(
                plan_id="default", project_id="current",
                title="默认方案", description="",
                pros=[], cons=[], resource_estimate={}, risks=[], expected_outcomes=[]
            )
        best = max(plans_data, key=lambda p: p.get("scores", {}).get("final", 0))
        return self._dict_to_plan(best)

    def _dict_to_plan(self, data: Dict) -> Plan:
        return Plan(**{k: v for k, v in data.items() if k in Plan.__dataclass_fields__})

    def _now(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
```
