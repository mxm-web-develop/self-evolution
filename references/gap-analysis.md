# Gap Analysis Prompt Template

## 目的
用于从项目画像、调研结果与历史记忆中提炼关键差距维度，识别当前状态与成熟标准之间的核心缺口。

## 输入变量
- `project_profile`: 项目画像，描述目标、边界、优先级、项目类型、已知约束。
- `investigation_result`: 调研结果，包含现状证据、扫描摘要、外部参考、历史分析摘要。
- `historical_memory`: 历史记忆，包含通用洞察、同类项目经验、近期分析结论。

## 推理要求
1. 根据证据提炼若干“差距维度”，不要预设固定业务分类。
2. 每个维度都要写清：当前状态、成熟标准、证据、差距分数、为何重要。
3. 结合项目优先级与历史经验，对差距维度排序。
4. 输出必须稳定、可解析、适合后续方案生成模块直接消费。

## 输出格式
请严格输出 JSON：

```json
{
  "summary": "一句话概述主要差距",
  "root_cause": "对整体根因的结构化说明",
  "dimensions": [
    {
      "dimension": "差距维度名称",
      "gap_score": 0,
      "priority": "high|medium|low",
      "current_state": "当前状态",
      "mature_standard": "成熟标准",
      "evidence": ["证据1", "证据2"],
      "why_it_matters": "为什么重要",
      "recommended_actions": ["建议动作1", "建议动作2"]
    }
  ]
}
```

## 约束
- 不要输出具体执行命令。
- 不要注入任何领域专属知识库。
- 只描述通用差距分析框架与结构化结果。
