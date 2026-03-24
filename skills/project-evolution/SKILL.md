# project-evolution SKILL.md

## 触发词

使用以下任一方式触发项目进化流程：

- `/evolution [问题描述]` - 启动完整项目进化流程
- `/analyze [问题]` - 仅执行调研+诊断
- `/plan [问题]` - 执行到方案生成
- `/score` - 对当前方案进行评分
- `/cases [关键词]` - 搜索相关案例

## 流程说明

### 完整流程：/evolution
```
用户输入 → 调研 → 诊断 → 方案 → 评分 → 审批 → 执行 → 学习
```

### 流程各阶段说明

| 阶段 | 说明 | 耗时（估算） |
|---|---|---|
| 调研 | 搜索相关案例 + 网络调研 | 1-2分钟 |
| 诊断 | 分析问题类型和根因 | 30秒 |
| 方案 | 生成 2-3 个候选方案 | 1分钟 |
| 评分 | 三维度评分（业务/技术/UX） | 30秒 |
| 审批 | 等待用户确认 | 用户决定 |
| 执行 | 通过子代理执行 | 按方案复杂度 |
| 学习 | 回写到案例库 | 30秒 |

## 输出格式

### 调研报告
```
## 调研报告

### 相似案例
- [案例1] (相似度: X)
- [案例2]

### 网络发现
- [发现1]
- [发现2]

### 建议
- [建议1]
```

### 方案输出
```
## 候选方案

### 方案 A：[名称]
- 描述：...
- 优势：...
- 劣势：...
- 资源：...
- 风险：...

[方案 B、C 类似]
```

### 评分结果
```
## 评分

| 方案 | 业务价值 | 技术可行 | 用户体验 | 总分 | 建议 |
|---|---|---|---|---|---|
| A | 8.0 | 7.5 | 8.0 | 7.8 | 推荐通过 |
| B | 9.0 | 5.0 | 7.0 | 6.7 | 建议修改 |
```

## 配置文件

项目配置位于 `projects/{project-id}/config.yaml`：

```yaml
project:
  id: demo
  name: 示例项目
  created: 2026-03-24

phases:
  auto_approve_threshold: 8.0  # 超过此分数自动通过（仍需确认）
  require_human_approval: true

scoring:
  weights:
    business: 0.3
    technical: 0.4
    ux: 0.3

storage:
  state_file: state.json
  plans_dir: plans/
  cases_root: ../cases/
```

## 状态文件

`projects/{project-id}/state.json` 记录当前进度：

```json
{
  "project_id": "demo",
  "phase": "planning",
  "created_at": "2026-03-24T14:00:00",
  "updated_at": "2026-03-24T14:05:00",
  "current_task": "用户问题描述",
  "context": {
    "investigation": {...},
    "diagnosis": {...},
    "plans": [...],
    "scores": [...]
  }
}
```

## 案例库格式

详见 `cases/{category}/{case-id}.md`

## 依赖

此 Skill 依赖以下模块：
- `core/*` - 核心业务逻辑
- `adapter_openclaw/*` - OpenClaw 工具适配

## 错误处理

| 错误类型 | 处理方式 |
|---|---|
| 调研失败 | 跳过网络调研，仅用案例库 |
| 评分异常 | 标记为"待人工评估" |
| 执行失败 | 回退到上一状态，提示用户 |
| 状态文件损坏 | 使用 .bak 备份恢复 |
