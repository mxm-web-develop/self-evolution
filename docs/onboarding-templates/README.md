# Onboarding 落盘产物模板

这些文件是 `/evolve` onboarding 流程完成后的标准产出。

## 文件对照表

| 文件 | 位置 | 说明 |
|---|---|---|
| `project-profile.md` | `projects/{id}/profile.md` | 项目画像首页 |
| `user-goals.md` | `projects/{id}/user-goals.md` | 用户目标文档 |
| `competitor-benchmarks.md` | `projects/{id}/competitor-benchmarks.md` | 竞品对比分析 |
| `optimization-roadmap.md` | `projects/{id}/optimization-roadmap.md` | 优化路线图 |
| `state.json` | `projects/{id}/state.json` | 运行时状态 |

## 目录结构

```
projects/
└── {project-id}/
    ├── profile.md
    ├── user-goals.md
    ├── competitor-benchmarks.md
    ├── optimization-roadmap.md
    ├── state.json
    ├── investigation.md      # 自动生成
    ├── diagnosis.json        # 自动生成
    ├── scores.json           # 自动生成
    └── plans/
        ├── plan-A.md
        ├── plan-B.md
        └── plan-C.md
```

## 说明

- 用户目标文件由 onboarding 多轮对话收集后生成
- 竞品分析由 `/evolve` 自动调研填充（用户可补充）
- 路线图在方案审批后由系统生成
- `state.json` 由框架运行时自动维护，**不要手动编辑**
