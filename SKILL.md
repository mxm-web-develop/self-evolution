---
name: self-evolution
description: 项目自进化分析，从活跃项目出发的调研→诊断→规划→执行→学习闭环。当用户想分析、诊断、规划、优化一个项目时触发。
---

# self-evolution

当用户希望分析、诊断、规划、优化一个项目时，进入该 skill。

## 工作流

1. 识别或接入活跃项目。
2. 基于项目画像、代码/结构线索与历史分析，先执行调研（investigate）。
3. 在调研结果之上做差距诊断（diagnose），判断成熟度、关键缺口与优先维度。
4. 基于诊断生成候选方案（plan），等待用户选择并确认。
5. 用户确认后进入执行（execute），并将结果沉淀为可复用经验。
6. 每轮结束后把洞察写入统一记忆库，供后续项目复用。

## references/ 目录加载规则

- `references/maturity-assessment.md`：在评估项目成熟度、判断所处阶段与成功标准时加载。
- `references/gap-analysis.md`：在分析调研结果、识别差距维度、生成诊断结构时加载。
- `references/plan-generation.md`：在生成候选方案、整理行动项与输出结构化方案时加载。

按需加载即可，不需要一次性全部加载。

## 目录约定

- `memory/`：跨项目共享的统一记忆库。
- `projects/{project-id}/`：项目隔离数据与分析产物。
- `scripts/`：可执行入口脚本。
- `references/`：推理框架 prompt 模板。
