# 用户手册（安装 / 配置 / 使用）

> 本手册面向"项目进化助手"的安装人员、配置人员和最终用户。
> 侧重于：如何让系统跑起来、如何配置、如何使用。

---

## 1. 快速开始（5 分钟跑起来）

### 1.1 环境要求

- Python 3.10+
- OpenClaw 已安装并运行
- 网络访问（用于搜索功能）
- 推荐 macOS / Linux / WSL 环境

> 为了避免手动步骤过多，1.1–1.3 推荐直接用自动脚本完成。

### 1.2 一键安装（推荐）

```bash
cd /Users/mxm_pro/.openclaw/workspace/project-evolution
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh duckduckgo
```

说明：
- `duckduckgo`：默认免费方案，无需 API Key，适合先跑通
- 如需更高质量搜索，可改成：
  ```bash
  ./scripts/bootstrap.sh tavily
  ```
- 如需 Brave，可使用：
  ```bash
  ./scripts/bootstrap.sh brave
  ```

脚本会自动完成：
1. 检查 Python 环境
2. 创建 `.venv`
3. 安装 `requirements.txt`
4. 生成 `.env.example` / `.env`
5. 自动执行安装验证

### 1.3 验证安装

如果你想单独验证，而不是在安装脚本里自动验证，可执行：

```bash
cd /Users/mxm_pro/.openclaw/workspace/project-evolution
source .venv/bin/activate
python scripts/verify_install.py duckduckgo
```

如果你已经配置了 Tavily API Key，也可以：

```bash
source .venv/bin/activate
python scripts/verify_install.py tavily
```


---

## 2. 配置指南

### 2.1 项目配置

每个项目有独立的配置文件：

```yaml
# projects/demo/config.yaml
project:
  id: demo
  name: Demo Project
  description: 示例项目

search:
  # 搜索 Provider：tavily | brave | duckduckgo
  provider: tavily

  # API Key（留空则从环境变量读取）
  tavily:
    api_key: ${TAVILY_API_KEY}
  brave:
    api_key: ${BRAVE_API_KEY}

  # Fallback 顺序（当前 Provider 失败时自动切换）
  fallback:
    - duckduckgo

  default_count: 5

notification:
  # 通知渠道：webchat（默认）
  channel: webchat
  target: main
```

### 2.2 搜索 Provider 选择建议

| 场景 | 推荐 Provider | 理由 |
|---|---|---|
| 正式使用 | tavily | AI 优化，结果质量高 |
| 预算有限 | duckduckgo | 免费，无需 API Key |
| 追求隐私 | brave | 隐私友好，无广告 |
| 高可靠性 | tavily + duckduckgo fallback | 主备自动切换 |

### 2.3 环境变量

| 变量名 | 必填 | 说明 |
|---|---|---|
| `TAVILY_API_KEY` | Tavily 时必填 | 从 tavily.com 获取 |
| `BRAVE_API_KEY` | Brave 时必填 | 从 brave.com/search/api 获取 |
| `SEARCH_PROVIDER` | 否 | 覆盖配置文件中的 provider |

---

## 3. 使用指南

### 3.1 基本使用流程

```
用户提交问题
    ↓
AI 调研（自动）
    ↓
AI 诊断（自动）
    ↓
AI 生成 3 个候选方案（自动）
    ↓
AI 评分（自动）
    ↓
人类审批（手动） ← 唯一需要人类介入的节点
    ↓
AI 执行（自动）
    ↓
AI 学习回写（自动）
    ↓
完成
```

### 3.2 启动一个新项目

在 OpenClaw 对话中输入：

```
/evolution 新建项目：优化网站加载速度，当前首屏加载需要 5 秒，希望控制在 2 秒内
```

系统将自动开始调研流程，并在每个阶段汇报进度。

### 3.3 查看项目状态

```
/evolution status demo
```

返回当前项目所在阶段、已完成的历史记录。

### 3.4 审批方案

系统会以如下格式发送审批请求：

```
📋 审批请求

项目：demo
方案：渐进式改进

评分结果：
- 业务价值：8.5
- 技术可行性：9.0
- 用户体验：7.5
- 总分：8.4

请回复：Approve / Reject / Revise
```

**回复方式**：
- `Approve` 或 `通过` → 执行该方案
- `Reject` 或 `拒绝` → 方案作废，可重新生成
- `Revise` 或 `修改` → 说明修改意见，系统调整后重新提交

### 3.5 中断与恢复

流程可随时中断（关闭对话、停止进程），重启后输入：

```
/evolution resume demo
```

系统从上次保存的 Phase 继续执行。

---

## 4. 文件结构参考

### 4.1 项目文件（自动生成）

```
projects/{project-id}/
├── config.yaml       # 项目配置（手动创建或自动生成）
├── state.json        # 当前状态（自动维护）
├── investigation.md  # 调研报告（自动生成）
├── diagnosis.json    # 诊断结果（自动生成）
├── scores.json       # 评分结果（自动生成）
└── plans/            # 候选方案目录
    ├── plan-A.md     # 方案 A
    ├── plan-B.md     # 方案 B
    └── plan-C.md     # 方案 C
```

### 4.2 案例库结构

```
cases/
├── index.json                    # 案例索引（自动维护）
├── feature_request/
│   └── case-xxx.md              # 具体案例
├── bug_fix/
│   └── case-yyy.md
├── optimization/
│   └── case-zzz.md
└── architecture/
    └── case-www.md
```

---

## 5. 常见问题排查

### 5.1 搜索返回空结果

**可能原因**：所有 Provider 都失败了

**排查步骤**：
```bash
# 1. 检查 API Key 是否设置
echo $TAVILY_API_KEY

# 2. 直接测试 Provider
python3 -c "
from providers import get_provider
p = get_provider('tavily')
print(p.health_check())
"

# 3. 查看 fallback 是否生效
#    系统应自动切换到 duckduckgo
```

### 5.2 状态文件损坏

**可能原因**：进程异常中断导致 JSON 不完整

**解决方案**：
```bash
# 每次 save_state 会自动备份 .bak 文件
cp projects/demo/state.json.bak projects/demo/state.json
```

### 5.3 子代理超时

**可能原因**：任务执行时间超过 5 分钟（默认超时）

**解决方案**：增加超时时间或在 `config.yaml` 中调整：
```yaml
execution:
  timeout_ms: 600000  # 10 分钟
```

### 5.4 审批请求没收到

**可能原因**：
1. `notification.channel` 配置错误
2. OpenClaw message 功能未启用

**排查**：检查 OpenClaw 配置中 `message` 插件状态

---

## 6. 命令参考

### 6.1 对话命令

| 命令 | 说明 |
|---|---|
| `/evolution new [问题]` | 新建项目，开始调研 |
| `/evolution status [project-id]` | 查看项目当前状态 |
| `/evolution plans [project-id]` | 查看所有候选方案 |
| `/evolution approve [project-id]` | 批准最优方案 |
| `/evolution reject [project-id]` | 拒绝，重新生成 |
| `/evolution resume [project-id]` | 从上次断点继续 |
| `/evolution cases` | 查看案例库统计 |

### 6.2 状态阶段说明

| Phase | 说明 | 人类介入 |
|---|---|---|
| IDLE | 空闲/等待输入 | — |
| INVESTIGATING | 调研中 | — |
| DIAGNOSING | 诊断中 | — |
| PLANNING | 方案生成中 | — |
| CRITIQUING | 评分中 | — |
| APPROVING | 等待审批 | ✅ |
| EXECUTING | 执行中 | — |
| LEARNING | 学习回写中 | — |

---

## 7. 性能与限制

| 指标 | 限制 |
|---|---|
| 单次搜索结果数 | 默认 5，最大 20 |
| 子代理超时 | 默认 5 分钟 |
| 项目并发数 | 无限制（文件系统隔离） |
| 案例库大小 | 无限制（按文件数） |
| 状态文件大小 | 建议 < 1MB |

---

## 8. 升级与迁移

### 8.1 升级项目进化助手

```bash
cd /Users/mxm_pro/.openclaw/workspace/project-evolution
git pull  # 或重新部署代码

# 重启 OpenClaw（如需要）
openclaw gateway restart
```

### 8.2 迁移项目到新机器

```bash
# 1. 复制整个 projects/ 目录
scp -r projects/ user@newmachine:/path/

# 2. 复制案例库
scp -r cases/ user@newmachine:/path/

# 3. 重新配置 API Keys
export TAVILY_API_KEY=tvly-xxxxx
```

---

## 9. 联系人与支持

- 项目代码：`~/openclaw/workspace/project-evolution`
- 文档：`docs/` 目录
- 问题反馈：在 OpenClaw 中输入 `/evolution help`
