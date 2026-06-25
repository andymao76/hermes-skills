#!/bin/bash
# Hermes 轻量版诊断 — 跳过 26 个 API Connectivity 并发检查，只测真正用的
# 安装: cp ~/.hermes/skills/devops/hermes-system-maintenance/scripts/hermes-doctor-fast.sh ~/bin/hermes-doctor-fast && chmod +x ~/bin/hermes-doctor-fast
# 安装 alias: echo "alias hermes-doctor='~/bin/hermes-doctor-fast'" >> ~/.bashrc

# 加载 ~/.hermes/.env 中的 API key
if [ -f "$HOME/.hermes/.env" ]; then
    set -a
    source "$HOME/.hermes/.env" 2>/dev/null || true
    set +a
fi

# 从 config.yaml 读取 custom provider 的 API key（siliconflow 等 key 在 config 里不在 .env）
if command -v python3 &>/dev/null; then
    SILICONFLOW_API_KEY="${SILICONFLOW_API_KEY:-$(python3 -c "
import yaml; c = yaml.safe_load(open('$HOME/.hermes/config.yaml'));
p = (c.get('providers') or {}).get('siliconflow', {});
k = p.get('api_key', '') or '';
print(k)
" 2>/dev/null)}"
fi

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; DIM='\033[2m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1${NC}"; }
info() { echo -e "    ${CYAN}→${NC} $1"; }

echo
echo -e "${CYAN}┌─────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│            🩺 Hermes Fast Doctor                        │${NC}"
echo -e "${CYAN}└─────────────────────────────────────────────────────────┘${NC}"

# ── 1. 版本 ──
echo -e "\n${CYAN}◆${NC} Version"
VER=$(hermes --version 2>&1 | head -1)
ok "Hermes $VER"

# ── 2. 代理 ──
echo -e "\n${CYAN}◆${NC} Proxy"
env | grep -qi proxy && env | grep -i proxy | while read -r line; do info "$line"; done || warn "No proxy env"

# ── 3. API Connectivity（只测实际在用的 provider，剔除已注释的无效 key）──
echo -e "\n${CYAN}◆${NC} API Connectivity (selected)"
test_api() {
    local name="$1" url="$2" key="$3" mode="$4"
    [ -z "$key" ] && { warn "$name (not configured)"; return; }
    [ "$mode" = "query" ] \
        && HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "${url}?key=${key}" 2>/dev/null || echo "timeout") \
        || HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$url" -H "Authorization: Bearer $key" 2>/dev/null || echo "timeout")
    case "$HTTP" in
        200)     ok "$name";;
        401)     warn "$name (invalid API key)";;
        timeout) warn "$name (timeout)";;
        *)       warn "$name (HTTP $HTTP)";;
    esac
}
test_api "DeepSeek"    "https://api.deepseek.com/v1/models"          "$DEEPSEEK_API_KEY"     "bearer"
test_api "SiliconFlow" "https://api.siliconflow.com/v1/models"       "$SILICONFLOW_API_KEY"  "bearer"
test_api "OpenRouter"  "https://openrouter.ai/api/v1/models"         "$OPENROUTER_API_KEY"   "bearer"

# ── 4. 磁盘和数据库 ──
echo -e "\n${CYAN}◆${NC} Disk Usage & State"
info "Sessions:  $(du -sh ~/.hermes/sessions 2>/dev/null | cut -f1)"
info "Skills:    $(du -sh ~/.hermes/skills 2>/dev/null | cut -f1)"
info "Logs:      $(du -sh ~/.hermes/logs 2>/dev/null | cut -f1)"
info "Total:     $(du -sh ~/.hermes/ 2>/dev/null | cut -f1)"
sessions=$(sqlite3 ~/.hermes/state.db 'SELECT COUNT(*) FROM sessions' 2>/dev/null || echo '?')
info "State DB:  ${sessions} sessions"

# ── 5. 模型 ──
echo -e "\n${CYAN}◆${NC} Model Config"
hermes model --current 2>/dev/null || warn "Could not get current model (run in interactive terminal)"

# ── 6. 禁用工具集 ──
echo -e "\n${CYAN}◆${NC} Disabled Toolsets"
grep -A5 "^disabled_toolsets:" ~/.hermes/config.yaml 2>/dev/null | grep -v "^--$" || info "Not set (default: all enabled)"

# ── 7. 系统服务 ──
echo -e "\n${CYAN}◆${NC} System Services"
systemctl --user is-active hermes-gateway.service     2>/dev/null && ok "hermes-gateway.service"      || warn "hermes-gateway.service (inactive)"
systemctl --user is-active hermes-chrome-cdp.service  2>/dev/null && ok "hermes-chrome-cdp.service"   || warn "hermes-chrome-cdp.service (inactive)"
systemctl --user is-active xiaohongshu-mcp.service    2>/dev/null && ok "xiaohongshu-mcp.service"     || warn "xiaohongshu-mcp.service (inactive)"

echo
echo -e "${GREEN}─${NC}${YELLOW}─${NC}${CYAN}──${NC} Fast Doctor Complete ${CYAN}──${NC}${YELLOW}─${NC}${GREEN}─${NC}"
echo -e "${DIM}  Run 'timeout 45s hermes doctor' for full (slow) check.${NC}"
echo
