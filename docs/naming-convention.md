# 命名规范（Naming Convention）

## 仓库命名

| 维度 | 旧名称 | 新名称 | 说明 |
|---|---|---|---|
| GitHub 仓库 | project-evolution | self-evolution | GitHub URL: github.com/mxm-web-develop/self-evolution |
| 本地目录 | project-evolution/ | self-evolution/ | 工作区子目录 |
| Skill 目录 | skills/project-evolution/ | skills/self-evolution/ | OpenClaw skill 触发目录 |
| Skill ID | project-evolution | self-evolution | SKILL.md 文件 ID |
| Skill 触发词 | /evolution | /evolve | 更短、更中性 |
| 项目代号 | project-evolution | self-evolution | 框架本身的项目代号 |

## 内部概念澄清

| 概念 | 英文 | 中文 | 说明 |
|---|---|---|---|
| 本框架 | Self-Evolution | 项目进化助手 / 自进化框架 | 框架本身 |
| 单个项目 | Project | 项目 | 用户业务项目 |
| 案例库 | Case Library | 案例库 | 成功/失败经验库 |

## 文档引用规范

所有文档中统一使用：

```
self-evolution / 项目进化助手
```

不再使用：
- ❌ `project-evolution`（GitHub repo 改名后不再适用）
- ❌ `project evolution`（空格形式）

## 迁移清单

1. 本地目录重命名：`project-evolution/` → `self-evolution/`
2. Skill 目录重命名：`skills/project-evolution/` → `skills/self-evolution/`
3. bootstrap.sh 中的日志前缀：`[project-evolution]` → `[self-evolution]`
4. README.md、docs、SKILL.md 中的所有引用更新
5. .git/config 中如记录了目录路径需更新

## 生效条件

- Skill 安装路径：由 `skills/self-evolution/SKILL.md` 决定
- 本地目录名：不影响 Git（git clone 后可任意命名），但为一致性建议与 repo 同名
