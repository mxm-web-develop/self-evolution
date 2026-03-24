#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DEFAULT_PROVIDER="${1:-duckduckgo}"

log() { printf "[self-evolution] %s\n" "$*"; }
fail() { printf "[self-evolution][error] %s\n" "$*" >&2; exit 1; }

command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "未找到 Python，请先安装 Python 3.10+"

log "项目目录: $PROJECT_ROOT"
log "创建虚拟环境: $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

log "升级 pip"
pip install --upgrade pip >/dev/null

log "安装基础依赖 requirements.txt"
pip install -r "$PROJECT_ROOT/requirements.txt"

if [[ "$DEFAULT_PROVIDER" == "brave" ]]; then
  log "尝试安装 Brave 可选依赖"
  pip install brave-search || log "Brave 依赖安装失败，可后续手动安装"
fi

if [[ ! -f "$PROJECT_ROOT/.env.example" ]]; then
  cat > "$PROJECT_ROOT/.env.example" <<'EOF'
# 搜索 Provider 相关配置
# 默认建议：duckduckgo（免费）或 tavily（质量更高）
TAVILY_API_KEY=
BRAVE_API_KEY=
SEARCH_PROVIDER=duckduckgo
EOF
fi

if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
  cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
  log "已生成 .env，可按需填写 API Key"
fi

log "运行安装验证"
python "$PROJECT_ROOT/scripts/verify_install.py" "$DEFAULT_PROVIDER"

cat <<EOF

✅ 安装完成

下一步：
1. source "$VENV_DIR/bin/activate"
2. 如需 Tavily / Brave，请编辑 "$PROJECT_ROOT/.env"
3. 查看用户手册：docs/user-manual.md
EOF
