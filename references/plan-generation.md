# Plan Generation Prompt Template

## 目的
用于基于诊断结果生成可执行候选方案，为后续审批、执行与复盘提供结构化输入。

## 输入变量
- `project_profile`: 项目画像，包含目标、约束、资源边界、项目类型。
- `investigation_result`: 调研结果，提供现状与参考信号。
- `diagnosis_result`: 诊断结果，提供成熟度判断、差距维度与优先级。
- `historical_memory`: 历史记忆，包含跨项目洞察与同类项目经验。

## 推理要求
1. 以差距维度为主轴生成方案，而不是套用固定业务模板。
2. 每个方案要明确：目标维度、动作、收益、成本、风险、预期结果。
3. 若历史记忆中存在同类项目经验，应在方案备注中体现参考来源。
4. 输出结构必须稳定，便于程序落盘、评分、审批和执行。

## 输出格式
请严格输出 JSON：

```json
{
  "plans": [
    {
      "title": "方案标题",
      "target_dimension": "目标维度",
      "description": "方案描述",
      "action_items": ["行动项1", "行动项2"],
      "pros": ["优势1"],
      "cons": ["限制1"],
      "risks": ["风险1"],
      "resource_estimate": {
        "effort": "low|medium|high",
        "scope": "影响范围说明",
        "automation": "low|medium|high"
      },
      "expected_outcomes": ["预期结果1"],
      "memory_reference": "如有同类经验，这里写引用说明；否则为空字符串"
    }
  ]
}
```

## 约束
- 不要预设某个具体行业的最佳实践。
- 不要写死网站、量化、写作、AI 产品等场景。
- 保持为通用推理框架。
