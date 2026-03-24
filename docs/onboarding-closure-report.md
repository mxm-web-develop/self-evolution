# Onboarding 收尾报告

> 日期：2026-03-24  
> 状态：✅ 完成

---

## 一、本轮已完成内容

### 1. 文档审核

| 文档 | 状态 | 备注 |
|---|---|---|
| `docs/naming-convention.md` | ✅ 完整 | 清晰，无问题 |
| `docs/onboarding-design.md` | ✅ 完整 | 补充了产物路径约定（第 10 节） |
| `docs/multi-project-support.md` | ✅ 完整 | 清晰，无问题 |
| `docs/user-manual.md` | ✅ 已修订 | 触发词 `/evolution` → `/evolve` 全部替换 |
| `docs/openclaw-mvp.md` | ✅ 完整（已有） | 无需修改 |

### 2. 触发词统一

- 全文搜索 `project-evolution` 目录：所有 `/evolution` 已替换为 `/evolve`
- 影响文件：`docs/user-manual.md`（唯一含触发词的文件）
- README.md：无旧触发词，无需修改

### 3. Onboarding 产物模板（新增）

| 文件 | 说明 |
|---|---|
| `docs/onboarding-templates/project-profile.md` | 项目画像模板 |
| `docs/onboarding-templates/user-goals.md` | 用户目标模板 |
| `docs/onboarding-templates/competitor-benchmarks.md` | 竞品对比模板 |
| `docs/onboarding-templates/optimization-roadmap.md` | 优化路线图模板 |
| `docs/onboarding-templates/state.json` | 运行时状态 JSON 模板 |
| `docs/onboarding-templates/README.md` | 模板索引说明 |

### 4. Onboarding 路径约定（补充到 onboarding-design.md）

在 `docs/onboarding-design.md` 新增第 10 节：
- 明确 `projects/{project-id}/` 下各文件的存放位置
- 指向 `docs/onboarding-templates/` 中的模板文件
- 区分"用户输入生成"vs"系统自动生成"文件

---

## 二、命名统一方案

### 结论：建议将本地目录 `project-evolution` 重命名为 `self-evolution`

### 决策依据

| 维度 | 当前状态 | 建议 |
|---|---|---|
| GitHub 仓库名 | `self-evolution` | ✅ 保持不变 |
| 本地目录名 | `project-evolution` | ⚠️ 建议改为 `self-evolution` |
| Skill 目录 | `skills/project-evolution/` | ⚠️ 建议改为 `skills/self-evolution/` |
| Skill 触发词 | `/evolution` → `/evolve` | ✅ 已更新为 `/evolve` |
| 文档内引用 | 多数已用 `self-evolution` | ✅ 基本一致 |

### 迁移影响评估

| 影响项 | 程度 | 说明 |
|---|---|---|
| Git 历史 | 无 | git clone 后目录名不影响历史 |
| Skill 安装 | **有** | Skill ID 从 `project-evolution` 变为 `self-evolution`，需重新注册 |
| OpenClaw 配置 | **有** | 如有配置引用了 `project-evolution` 路径，需同步更新 |
| 正在运行的进程 | 低 | 无状态，仅目录名引用 |

### 迁移步骤

```bash
# 1. 确认当前工作目录不是 project-evolution（否则 mv 会出问题）
cd /Users/mxm_pro/.openclaw/workspace

# 2. 重命名目录
mv project-evolution self-evolution

# 3. 更新 Skill 目录
mv self-evolution/skills/project-evolution self-evolution/skills/self-evolution

# 4. 更新 Skill SKILL.md 中的 id 和引用
#    （skills/self-evolution/SKILL.md 内的 id 字段改为 self-evolution）

# 5. 检查 .env 和其他配置中的路径引用
grep -r "project-evolution" self-evolution/

# 6. 如 OpenClaw 有 skill 路径配置，更新它
openclaw skill list   # 确认 skill 状态
```

### 若暂时不重命名

可以接受。GitHub repo 名已确定为 `self-evolution`，本地目录名仅影响人类阅读体验。框架代码中引用目录的地方已尽量使用相对路径或配置变量，影响可控。

---

## 三、统一 Onboarding 流程（结论版）

```
用户发起 /evolve
    │
    ▼
STEP 0: 判断意图
    │
    ├── 给路径 → 进入"已有项目流程"
    ├── 说"新建" → 进入"新项目流程"
    ├── 说"看项目" → 显示项目列表
    └── 闲聊 → 轻量响应
    │
    ▼
【已有项目流程】
    扫描 → 生成项目画像 → 用户确认
    │
    ▼
【新项目流程】（多轮对话）
    1. 项目目标
    2. 项目名称
    3. 对标产品
    4. 优化优先级
    5. 自动化边界
    │
    ▼
生成 profile.md / user-goals.md / state.json 等产物
    │
    ▼
进入 ONBOARDED 状态
    │
    ▼
可随时通过 /evolve status 查看所有项目
```

### 入口统一
- 唯一入口：`/evolve`
- 不再区分新用户引导脚本 vs 已有项目接入脚本

### 多项目支持
- `projects/index.json` 维护所有项目索引
- `projects/{id}/state.json` 维护各项目状态
- 支持 `/evolve switch [id]` 切换活跃项目

---

## 四、修改文件清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `docs/user-manual.md` | 修改 | `/evolution` → `/evolve`（7处） |
| `docs/onboarding-design.md` | 修改 | 新增第 10 节：产物路径约定 |
| `docs/onboarding-templates/project-profile.md` | 新增 | 项目画像模板 |
| `docs/onboarding-templates/user-goals.md` | 新增 | 用户目标模板 |
| `docs/onboarding-templates/competitor-benchmarks.md` | 新增 | 竞品对比模板 |
| `docs/onboarding-templates/optimization-roadmap.md` | 新增 | 优化路线图模板 |
| `docs/onboarding-templates/state.json` | 新增 | 运行时状态模板 |
| `docs/onboarding-templates/README.md` | 新增 | 模板索引说明 |
| `docs/onboarding-closure-report.md` | 新增 | 本收尾报告 |

---

## 五、未完成内容

以下内容在本轮scope之外，属于后续开发迭代：

| 项目 | 说明 | 优先级 |
|---|---|---|
| Skill 代码实现 | SKILL.md 已定义，但无对应 Python/onboarding 逻辑实现 | P1 |
| 项目索引 `projects/index.json` 初始化 | 目录已存在，但无初始化脚本 | P1 |
| 已有项目扫描自动化 | 文档已设计，代码未实现 | P1 |
| 多轮对话状态机实现 | `state.json` 结构已定义，实现由 Skill 代码负责 | P1 |
| 本地目录重命名执行 | 建议已给出，需瀚峰手动执行 | — |

---

## 六、推荐下一步

### 立即可做（无技术依赖）

1. **执行目录重命名**（可选，但建议）
   - `mv project-evolution self-evolution`（见第三节迁移步骤）
   - 更新 Skill 路径引用

2. **创建第一个真实项目**
   - 运行 `/evolve new 我的项目目标`
   - 验证 onboarding 多轮对话流程

### 短期（本周内）

3. **实现 Skill 逻辑**（将 docs/onboarding-design.md 落地为可执行代码）
   - 意图判断路由
   - 项目扫描逻辑
   - 多轮对话状态机
   - `projects/index.json` 维护

4. **连接 money-machine**
   - 将现有 `money-machine` 接入 self-evolution 作为第一个已有项目案例

---

## 七、总结

本轮完成了：
- ✅ 文档审核与修订（user-manual 触发词统一）
- ✅ Onboarding 产物模板完整交付
- ✅ Onboarding 路径约定写入文档
- ✅ 命名方案明确（建议本地目录重命名，已给出迁移方案）
- ✅ 统一 onboarding 流程完整闭环文档

**本轮产出现已完成，可以结束。**
