#!/usr/bin/env bash
# =============================================================================
# dsh-draftbox 一键端到端回归测试
#
# 自动：探测/拉起 media_draftbox 后端 -> 校验依赖 -> 跑工具层自测
#       （可选 --with-agent 再跑真实 dsh agent 调用）。
#
# 用法：
#   bash test-e2e.sh                     # 工具层自测（快，无 LLM 成本）
#   bash test-e2e.sh --with-agent        # 额外跑真实 dsh agent（需 DEEPSEEK_API_KEY）
#   bash test-e2e.sh --keep-backend      # 测试后不关闭它拉起/复用的后端
#
# 退出码：0=全通过，1=有失败，2=前置缺失
# =============================================================================
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/../backend"
BACKEND_URL="${DRAFTBOX_BASE_URL:-http://127.0.0.1:8502}"
WITH_AGENT=0
KEEP_BACKEND=0
STARTED_BACKEND=0

for a in "$@"; do
  case "$a" in
    --with-agent) WITH_AGENT=1 ;;
    --keep-backend) KEEP_BACKEND=1 ;;
    *) echo "[WARN] 忽略未知参数: $a" ;;
  esac
done

PASS=0; FAIL=0
ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }

log()  { echo ""; echo "== $1 =="; }

log "环境检查"
if ! command -v node >/dev/null 2>&1; then bad "未找到 node (需 >=22.19)"; else ok "node $(node --version)"; fi
if ! command -v pnpm >/dev/null 2>&1; then bad "未找到 pnpm (npm i -g pnpm)"; else ok "pnpm $(pnpm --version)"; fi
if ! command -v dsh >/dev/null 2>&1; then bad "未找到 dsh (npm i -g @deepseek-ai/dsh)"; else ok "dsh $(dsh --version 2>&1 | head -1)"; fi

if [ "$FAIL" -gt 0 ]; then
  echo "[ERROR] 前置缺失，无法继续。"
  exit 2
fi

log "插件依赖 (dsh-plugin/node_modules)"
if [ ! -d "$ROOT/node_modules/@deepseek-ai/dsh-tools" ]; then
  echo "  -- 需要 @deepseek-ai/dsh-tools，执行 pnpm install ..."
  (cd "$ROOT" && pnpm install) || { bad "pnpm install 失败"; echo "[ERROR] 中止。"; exit 2; }
  ok "pnpm install 完成"
else
  ok "已安装 @deepseek-ai/dsh-tools"
fi

# ---------------------------------------------------------------------------
log "media_draftbox 后端"
health() {
  curl -sf --noproxy '*' -m 3 "$BACKEND_URL/health" >/dev/null 2>&1
}
if ! health; then
  echo "  -- $BACKEND_URL 未监听，尝试启动 uvicorn ..."
  if [ -d "$BACKEND_DIR" ] && [ -f "$BACKEND_DIR/main.py" ]; then
    (cd "$BACKEND_DIR" && uvicorn main:app --host 127.0.0.1 --port 8502 --log-level warning >/dev/null 2>&1 &)
    STARTED_BACKEND=1
    for _ in $(seq 1 20); do
      health && break; sleep 1
    done
  fi
fi
if health; then ok "后端在线 ($BACKEND_URL)"
else bad "后端不可用（$BACKEND_URL）。请先手动启动，或确认 BACKEND_DIR=$BACKEND_DIR 存在"; fi

# ---------------------------------------------------------------------------
log "工具层自测 (无 LLM)"
# git-bash 下 node 需 Windows 原生路径（/c/... 会被误解析）
WIN_ROOT="$(command -v cygpath >/dev/null 2>&1 && cygpath -w "$ROOT" || echo "$ROOT")"
if ! node "$WIN_ROOT\\scripts\\tool-smoke.mjs" --base-url="$BACKEND_URL"; then
  FAIL=$((FAIL+1))
else
  PASS=$((PASS+1))
fi

# ---------------------------------------------------------------------------
if [ "$WITH_AGENT" -eq 1 ]; then
  log "dsh agent 端到端（需 DEEPSEEK_API_KEY）"
  # 若未设置 DEEPSEEK_API_KEY，尝试从常见 Hermes/本地 .env 自动读取
  if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    for ENV_FILE in "$HOME/AppData/Local/hermes/.env" "$HOME/.dsh/.env" "$PWD/.env"; do
      if [ -f "$ENV_FILE" ] && grep -qE '^DEEPSEEK_API_KEY=' "$ENV_FILE"; then
        export DEEPSEEK_API_KEY="$(grep -E '^DEEPSEEK_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)"
        echo "  -- 已从 $ENV_FILE 读取 DEEPSEEK_API_KEY"
        break
      fi
    done
  fi
  if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "  -- 未设置 DEEPSEEK_API_KEY，跳过 agent 测试。"
    echo "     可用: export DEEPSEEK_API_KEY=... 或放在 \$HOME/.dsh/.env"
    bad "跳过 agent 测试（无 DEEPSEEK_API_KEY）"
  else
    if [ ! -d "$HOME/.dsh/profiles/headless/node_modules/dsh-draftbox" ]; then
      echo "  -- 插件未装入 headless profile，执行: dsh plugin --profile headless add $ROOT"
      (cd "$ROOT/.." && dsh plugin --profile headless add "$ROOT") || { bad "装入 profile 失败"; FAIL=$((FAIL+1)); }
    fi
    OUT="$(cd "$ROOT" && timeout 180 dsh --profile headless \
        "调用 draftbox_list_drafts 工具，列出草稿箱标题。若工具调用成功，回复'AGENT_TOOL_OK'开头，再列标题。")"
    RC=$?
    echo "$OUT" | tail -8
    if [ $RC -eq 0 ] && printf '%s' "$OUT" | grep -q "AGENT_TOOL_OK"; then
      ok "agent 调用工具成功"
    else
      bad "agent 调用工具失败 (rc=$RC)"
      FAIL=$((FAIL+1))
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 清理
if [ "$STARTED_BACKEND" -eq 1 ] && [ "$KEEP_BACKEND" -eq 0 ]; then
  echo "  -- 关闭测试期间启动的后端 ..."
  # 仅关掉启动脚本自己拉起的 uvicorn（按 8502 端口找进程；netstat 字段: TCP addr_local addr_foreign STATE PID）
  PID="$(netstat -ano 2>/dev/null | awk '$2 ~ /:8502/ && /LISTENING/ {print $5; exit}')"
  # MSYS_NO_PATHCONV 防止 git-bash 把 /PID 当路径转换
  [ -n "$PID" ] && MSYS_NO_PATHCONV=1 taskkill /F /PID "$PID" >/dev/null 2>&1 && ok "后端已关闭 (pid $PID)" || echo "  -- 未找到 8502 监听进程（可能已关闭）"
fi

log "汇总"
echo "  通过 $PASS 项 / 失败 $FAIL 项"
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "  ✅ dsh-draftbox 端到端测试全部通过"
  exit 0
else
  echo "  ❌ 存在失败项，请检查上方日志"
  exit 1
fi
