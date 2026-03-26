---
name: self-evolution
description: 项目自进化分析，从活跃项目出发的调研→诊断→规划→执行→学习闭环。当用户想分析、诊断、规划、优化一个项目时触发。
---

# self-evolution

当用户希望分析、诊断、规划、优化一个项目时，进入该 skill。

---

## 项目意图识别规则

### 第一步：识别项目

用户说出项目名字（如"mxmaiwebsite"、"我的xx项目"、"跟进下xxx"）
→ 扫描 workspace 所有目录，匹配项目名（精确优先、模糊匹配其次）
→ 列出匹配的项目供用户确认

### 第二步：用户确认

对话确认："你说的是 `{项目根目录路径}` 这个项目吗？"
→ 用户确认或纠正

### 第三步：检查项目状态

用户确认后，检查 `projects/{project-id}/` 是否有记录：
- **有记录** → 检查 onboarding 信息是否完整（user-goals / 竞品 / 优先级）
  - 完整 → 直接进入分析流程
  - 不完整 → 补充对话收集缺失的 onboarding 信息
- **没有记录** → 开始完整的 onboarding 对话

### 第四步：新建项目（从0开始）

用户说"做一个xx项目"、"我想开发一个xxx"、"新项目xxx"
→ 检查 workspace 是否已有同名项目
  - 有 → 走第二步确认
  - 没有 → 新建 `projects/{project-id}/`，开始 onboarding 对话

---

## 工作流

1. **识别/接入项目** — 按上方规则确认项目和项目状态
2. **调研（investigate）** — 基于代码结构 + onboarding 信息 + 历史分析，执行调研
3. **诊断（diagnose）** — 判断成熟度、关键缺口与优先维度
4. **规划（plan）** — 生成候选方案，等待用户选择并确认
5. **执行（execute）** — 用户确认后执行，结果沉淀为经验
6. **学习（learn）** — 每轮结束后把洞察写入统一记忆库

---

## references/ 目录加载规则

- `references/maturity-assessment.md`：评估项目成熟度、判断所处阶段与成功标准时加载
- `references/gap-analysis.md`：分析调研结果、识别差距维度、生成诊断结构时加载
- `references/plan-generation.md`：生成候选方案、整理行动项与输出结构化方案时加载

按需加载，不需要一次性全部加载。

---

## 目录约定

| 目录 | 用途 |
|------|------|
| `memory/` | 跨项目共享的统一记忆库 |
| `projects/{project-id}/` | 项目隔离数据与分析产物 |
| `scripts/` | 可执行入口脚本 |
| `references/` | 推理框架 prompt 模板 |
