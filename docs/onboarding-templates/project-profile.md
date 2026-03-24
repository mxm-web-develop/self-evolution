# {{ project-name }} — 项目画像

> 由 `/evolve` onboarding 自动生成  
> 生成时间：{{ created_at }}  
> 最后更新：{{ updated_at }}

## 基本信息

| 字段 | 值 |
|---|---|
| 项目 ID | {{ project-id }} |
| 项目名称 | {{ project-name }} |
| 项目类型 | {{ new / existing }} |
| 项目路径 | {{ path }} |
| 状态 | {{ NEW / ONBOARDING / ACTIVE / ARCHIVED }} |

## 项目目标

{{ 一句话描述项目要做什么 }}

## 技术栈（推断）

| 类型 | 值 |
|---|---|
| 主语言 | {{ language }} |
| 框架 | {{ framework }} |
| 包管理 | {{ package-manager }} |
| 测试框架 | {{ test-framework }} |
| CI/CD | {{ yes / no }} |

## 对标产品（Benchmarks）

{{ 竞品列表及简要说明 }}

## 优化优先级

| 优先级维度 | 权重 | 说明 |
|---|---|---|
| {{ dimension }} | {{ weight }} | {{ reason }} |

## 自动化边界

以下节点在执行时需要人工审批，不会自动执行：

| 操作 | 需要审批 |
|---|---|
| {{ action }} | {{ yes }} |

## Onboarding 历史

| 步骤 | 输入值 | 时间 |
|---|---|---|
| goal | {{ user input }} | {{ timestamp }} |
| name | {{ user input }} | {{ timestamp }} |
| benchmarks | {{ user input }} | {{ timestamp }} |
| priorities | {{ user input }} | {{ timestamp }} |
| automation_boundaries | {{ user input }} | {{ timestamp }} |

## 健康度快照

| 指标 | 状态 |
|---|---|
| README 完整性 | {{ ✅ / ⚠️ / ❌ }} |
| 测试覆盖 | {{ % }} |
| CI/CD | {{ 有 / 无 }} |
| 依赖安全警告 | {{ 数量 }} |
| 文档完整度 | {{ 高 / 中 / 低 }} |
