#!/bin/bash
# ==============================================================================
# 每日启动健康检查
# 检查项：
#   1. Clash Verge 代理是否运行且代理功能正常
#   2. 所有配置的大模型是否可用
# 退出码: 0=全部通过, 1=临时警告, >=2=需要人工处理
# ==============================================================================

set -o pipefail

FAILED=0; WARN=0

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log_ok()   { echo -e "  ${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "  ${YELLOW}[⚠️]${NC} $1"; }
log_fail() { echo -e "  ${RED}[❌]${NC} $1"; }
log_hr()   { echo ""; echo -e "${BOLD}$1${NC}"; echo "──────────────────────────────────────────────────────────────"; }

load_dotenv() {
  local f="$1"; [ ! -f "$f" ] && return
  while IFS='=' read -r k v; do
    [ -z "$k" ] && continue; [[ "$k" =~ ^#.* ]] && continue
    k="${k//\"/}"; k="${k//\'/}"; v="${v//\"/}"; v="${v//\'/}"
    export "$k=$v" 2>/dev/null || true
  done < "$f"
}

# ── 1. Clash Verge 代理检查 ─────────────────────────────────────────────────
log_hr "1. Clash Verge 代理检查"

pgrep -f "clash-verge" > /dev/null 2>&1 && log_ok "Clash Verge GUI 进程运行中" || { log_fail "Clash Verge GUI 进程未运行"; FAILED=$((FAILED+1)); }
pgrep -f "verge-mihomo" > /dev/null 2>&1 && log_ok "Mihomo 内核进程运行中" || { log_fail "Mihomo 内核进程未运行"; FAILED=$((FAILED+1)); }
ss -tln 2>/dev/null | grep -q ":7897 " && log_ok "代理端口 7897 正常监听" || { log_fail "代理端口 7897 未监听"; FAILED=$((FAILED+1)); }

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -x "http://127.0.0.1:7897" "https://www.google.com/generate_204" 2>&1)
if [[ "$HTTP_CODE" =~ ^(204|200|301|302)$ ]]; then
  log_ok "代理功能测试通过（Google 返回 $HTTP_CODE）"
else
  HTTP_CODE2=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -x "http://127.0.0.1:7897" "https://api.openrouter.ai" 2>&1)
  if [[ "$HTTP_CODE2" =~ ^(200|404|401|429)$ ]]; then
    log_ok "代理功能测试通过（OpenRouter 返回 $HTTP_CODE2）"
  else
    log_fail "代理功能测试失败（Google=$HTTP_CODE, OpenRouter=$HTTP_CODE2）"
    FAILED=$((FAILED+1))
  fi
fi

GATEWAY_PID=$(pgrep -f "hermes_cli.main gateway" | head -1)
if [ -n "$GATEWAY_PID" ] && [ -r "/proc/$GATEWAY_PID/environ" ]; then
  NO_PROXY_VAL=$(cat "/proc/$GATEWAY_PID/environ" 2>/dev/null | tr '\0' '\n' | grep "^NO_PROXY=" | head -1)
  echo "$NO_PROXY_VAL" | grep -q "aliyuncs.com" && log_ok "NO_PROXY 配置正确（含国内域名）" || log_warn "NO_PROXY 可能未含国内域名: $NO_PROXY_VAL"
else
  log_warn "无法读取 Gateway 进程环境变量"
fi

# ── 2. 大模型健康检查 ──────────────────────────────────────────────────────
log_hr "2. 大模型健康检查"
load_dotenv "/home/andymao/.hermes/.env"

PYTHON_EXEC="/home/andymao/.hermes/hermes-agent/venv/bin/python3"
CHECK_SCRIPT="/home/andymao/.hermes/scripts/.check_models.py"

cat > "$CHECK_SCRIPT" << 'PYEOF'
import yaml, os, json, requests, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    config = yaml.safe_load(f)
providers = config.get('providers', {})
failed = 0; warn = 0; results = []
def test(name, info):
    base_url = info.get('base_url', ''); api_key = info.get('api_key', '')
    key_env = info.get('api_key_env', ''); model = info.get('default_model') or info.get('default') or info.get('model', '')
    if not api_key and key_env: api_key = os.environ.get(key_env, '')
    if not api_key: return name, model, 'SKIP', '无API Key'
    try:
        resp = requests.post(base_url.rstrip('/') + '/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'model': model, 'messages': [{'role': 'user', 'content': 'say OK'}], 'max_tokens': 50}, timeout=20)
        if resp.status_code == 200:
            return name, model, 'OK', resp.json()['choices'][0]['message']['content'][:20]
        elif resp.status_code in (401, 402): return name, model, 'FATAL', f'HTTP {resp.status_code}'
        else: return name, model, 'TEMP', f'HTTP {resp.status_code}'
    except Exception as e: return name, model, 'TEMP', f'{type(e).__name__}'
with ThreadPoolExecutor(max_workers=6) as executor:
    for f in as_completed({executor.submit(test, n, info): n for n, info in providers.items()}):
        results.append(f.result())
for name in ['deepseek', 'siliconflow', 'siliconflow-cn', 'bailian', 'gemini', 'openrouter']:
    found = [r for r in results if r[0] == name]
    if found:
        n, m, s, d = found[0]
        if s == 'OK': print(f"{'✅':12s} {n:20s} {m:40s} {d}")
        elif s == 'FATAL': print(f"{'❌':12s} {n:20s} {m:40s} {d}"); failed += 1
        elif s == 'TEMP': print(f"{'⚠️':12s} {n:20s} {m:40s} {d}"); warn += 1
        else: print(f"{'⏭️':12s} {n:20s} {m:40s} {d}")
sys.exit(2 if failed > 0 else (1 if warn > 0 else 0))
PYEOF

echo ""; echo "  正在测试各 Provider API（并发 6 路）..."; echo ""
"$PYTHON_EXEC" "$CHECK_SCRIPT"
CHECK_EXIT=$?
[ $CHECK_EXIT -eq 2 ] && log_fail "部分大模型检查失败（需人工处理）" && FAILED=$((FAILED+1))
[ $CHECK_EXIT -eq 1 ] && log_warn "部分大模型临时不可用" && WARN=$((WARN+1))
[ $CHECK_EXIT -eq 0 ] && log_ok "所有大模型健康检查通过"

# ── 3. 汇总 ────────────────────────────────────────────────────────────────
log_hr "3. 检查汇总"
if [ $FAILED -eq 0 ] && [ $WARN -eq 0 ]; then echo -e "  ${GREEN}${BOLD}✅ 全部项目通过 — 系统健康，所有大模型可用${NC}"
elif [ $FAILED -eq 0 ]; then echo -e "  ${YELLOW}${BOLD}⚠️  仅临时问题 ($WARN)，系统基本正常${NC}"
else echo -e "  ${RED}${BOLD}❌ $FAILED 项失败 + $WARN 项临时问题，需要人工排查${NC}"
fi
echo ""; echo -e "  ${CYAN}检查时间:${NC} $(date '+%Y-%m-%d %H:%M:%S %Z')"; echo ""

rm -f "$CHECK_SCRIPT"
exit $((FAILED * 10 + WARN))
