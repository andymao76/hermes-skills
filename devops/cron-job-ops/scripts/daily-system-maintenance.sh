#!/bin/bash
# ==============================================================================
# 每日系统维护 — 在 Hermes 每日第一次启动时自动运行
# 可作为 no_agent cron job 使用 (schedule="30 1 * * *", script="daily-system-maintenance.sh")
# 检查项：
#   1. 检查 Hermes 更新并自动更新
#   2. 清理僵尸/孤儿进程（特别清理 xiaohongshu MCP 残留 headless Chrome）
#   3. 清理旧会话以释放磁盘空间
#   4. 清理日志、临时文件和缓存
#   5. 检查 Cron 作业健康状态
#   6. 磁盘空间检查
# ==============================================================================

set -o pipefail

SCRIPT_NAME="每日系统维护"
FAILED=0
WARN=0

# ── 颜色 ──
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log_info()  { echo -e "  ${CYAN}[INFO]${NC} $1"; }
log_ok()    { echo -e "  ${GREEN}[✅]${NC} $1"; }
log_warn()  { echo -e "  ${YELLOW}[⚠️]${NC} $1"; }
log_fail()  { echo -e "  ${RED}[❌]${NC} $1"; }
log_hr()    { echo ""; echo -e "${BOLD}$1${NC}"; echo "──────────────────────────────────────────────────────────────"; }
log_sub()   { echo -e "  ${CYAN}└─${NC} $1"; }

# ── 头部 ──
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  🛠️  $SCRIPT_NAME${NC}"
echo -e "${BOLD}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── 1. 检查 Hermes 更新 ──────────────────────────────────────────────────────
log_hr "1️⃣  检查 Hermes 更新"

HERMES_BIN=$(command -v hermes)
if [ -z "$HERMES_BIN" ]; then
  log_fail "hermes 命令未找到，跳过检查"
  FAILED=$((FAILED+1))
else
  log_info "Hermes 路径: $HERMES_BIN"
  UPDATE_CHECK=$(hermes update --check 2>&1)
  EXIT_CODE=$?

  if echo "$UPDATE_CHECK" | grep -qi "update available\|new version\|behind\|ahead of\|outdated"; then
    log_warn "发现可用更新，正在执行更新..."
    UPDATE_RESULT=$(hermes update -y 2>&1)
    if echo "$UPDATE_RESULT" | grep -qi "error\|failed"; then
      log_fail "更新失败"; echo "$UPDATE_RESULT" | while IFS= read -r line; do log_sub "$line"; done
      FAILED=$((FAILED+1))
    else
      log_ok "Hermes 已更新到最新版本"
      echo "$UPDATE_RESULT" | grep -v "^$" | head -5 | while IFS= read -r line; do log_sub "$line"; done
    fi
  elif echo "$UPDATE_CHECK" | grep -qi "already up to date\|up-to-date\|up to date"; then
    log_ok "Hermes 已是最新版本"
  else
    log_warn "无法检查更新（退出码: $EXIT_CODE）"
    log_sub "$(echo "$UPDATE_CHECK" | head -3)"
    WARN=$((WARN+1))
  fi
fi

# ── 2. 清理僵尸/孤儿进程 ────────────────────────────────────────────────────
log_hr "2️⃣  清理僵尸进程与孤儿进程"

# 2a. 僵尸进程（仅供记录，内核自动回收）
ZOMBIE_COUNT=$(ps aux | awk '{if ($8 == "Z") print}' | wc -l)
[ "$ZOMBIE_COUNT" -gt 0 ] && log_warn "发现 $ZOMBIE_COUNT 个僵尸进程" || log_ok "无僵尸进程"

# 2b. 清理残留 headless Chrome 进程（小红书 MCP 常见，每次搜索会启动 Chrome）
ORPHAN_CHROME=$(ps aux | grep -i "chrome" | grep -v "grep\|defunct\|chrome-cdp" | wc -l)
if [ "$ORPHAN_CHROME" -gt 5 ]; then
  log_warn "检测到 $ORPHAN_CHROME 个 Chrome 进程残留"
  pkill -f "chrome.*--headless" 2>/dev/null && log_sub "已清理 headless Chrome 进程" || log_sub "无 headless Chrome 进程需清理"
  WARN=$((WARN+1))
else
  log_ok "Chrome 进程状态正常（$ORPHAN_CHROME 个）"
fi

# 2c. 清理 systemd 失败服务
FAILED_SERVICES=$(systemctl --user list-units --failed --no-legend 2>/dev/null | wc -l)
if [ "$FAILED_SERVICES" -gt 0 ]; then
  log_warn "发现 $FAILED_SERVICES 个失败的 systemd 用户服务"
  systemctl --user list-units --failed --no-legend 2>/dev/null | while IFS= read -r line; do
    SERVICE_NAME=$(echo "$line" | awk '{print $1}')
    echo "$SERVICE_NAME" | grep -q "hermes" && systemctl --user reset-failed "$SERVICE_NAME" 2>/dev/null
  done
  WARN=$((WARN+1))
else
  log_ok "无失败的 systemd 服务"
fi

# ── 3. 清理旧会话 ────────────────────────────────────────────────────────────
log_hr "3️⃣  清理旧会话"

SESSIONS_STATS=$(hermes sessions stats 2>&1)
TOTAL_SESSIONS=$(echo "$SESSIONS_STATS" | grep -oP 'Total sessions: \K\d+')
DB_SIZE=$(echo "$SESSIONS_STATS" | grep -oP 'Database size: \K[0-9.]+ [A-Z]+')
log_info "当前会话数: $TOTAL_SESSIONS | 数据库大小: $DB_SIZE"

PRUNE_RESULT=$(hermes sessions prune --older-than 30 --yes 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  if echo "$PRUNE_RESULT" | grep -qi "removed\|deleted\|cleaned\|pruned\|0 session"; then
    DELETED=$(echo "$PRUNE_RESULT" | grep -oP '\d+ session' | head -1)
    log_ok "会话清理完成（删除 $DELETED）"
  else
    log_ok "无需清理的旧会话"
  fi
else
  log_warn "会话清理异常"
  WARN=$((WARN+1))
fi

SESSIONS_STATS_AFTER=$(hermes sessions stats 2>&1)
DB_SIZE_AFTER=$(echo "$SESSIONS_STATS_AFTER" | grep -oP 'Database size: \K[0-9.]+ [A-Z]+')
log_info "清理后数据库大小: $DB_SIZE_AFTER"

# ── 4. 清理日志与临时文件 ──────────────────────────────────────────────────
log_hr "4️⃣  清理日志与临时文件"

# 4a. 日志轮转（删除 7 天前的轮转日志，截断超过 50MB 的）
LOG_DIR="$HOME/.hermes/logs"
if [ -d "$LOG_DIR" ]; then
  LOG_SIZE_BEFORE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
  find "$LOG_DIR" -name "*.log" -type f -mtime +7 2>/dev/null | while IFS= read -r f; do
    BASENAME=$(basename "$f")
    echo "$BASENAME" | grep -qE '\.\d+\.log$' && rm -f "$f" && log_sub "删除过期日志: $BASENAME"
  done
  find "$LOG_DIR" -name "*.log" -type f -size +50M 2>/dev/null | while IFS= read -r f; do
    log_warn "截断大日志: $(basename "$f") ($(du -h "$f" | cut -f1))"
    tail -c 10M "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
  done
  LOG_SIZE_AFTER=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
  log_ok "日志目录: $LOG_SIZE_BEFORE → $LOG_SIZE_AFTER"
fi

# 4b. 清理临时目录
TMP_CLEANED=0
for tmpdir in "$HOME/.cache/pip" "/tmp/hermes_*" "/var/tmp/hermes_*"; do
  # shellcheck disable=SC2086
  ls $tmpdir 2>/dev/null | head -1 | grep -q . && {
    find /tmp -maxdepth 1 -name "hermes_*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null
    TMP_CLEANED=1
  }
done
[ "$TMP_CLEANED" -eq 1 ] && log_ok "临时文件已清理" || log_ok "无可清理的临时文件"

# 4c. 清理 Hermes 音频/图片缓存
HERMES_CACHE="$HOME/.cache/hermes"
if [ -d "$HERMES_CACHE" ]; then
  CACHE_SIZE=$(du -sh "$HERMES_CACHE" 2>/dev/null | cut -f1)
  find "$HERMES_CACHE" -type f \( -name "*.mp3" -o -name "*.png" -o -name "*.jpg" \) -mtime +7 -delete 2>/dev/null
  CACHE_SIZE_AFTER=$(du -sh "$HERMES_CACHE" 2>/dev/null | cut -f1)
  log_ok "音频/图片缓存: $CACHE_SIZE → $CACHE_SIZE_AFTER"
fi

# ── 5. 检查 Cron 作业健康状态 ──────────────────────────────────────────────
log_hr "5️⃣  检查 Cron 作业健康状态"

FAILED_JOBS=$(hermes cron list 2>&1 | grep -c "error:" || true)
if [ "$FAILED_JOBS" -gt 0 ]; then
  log_warn "检测到 $FAILED_JOBS 个异常的 Cron 作业"
  hermes cron list 2>&1 | grep -B2 "error:" | while IFS= read -r line; do [ -n "$line" ] && log_sub "$line"; done
  WARN=$((WARN+1))
else
  log_ok "所有 Cron 作业运行正常"
fi

# ── 6. 磁盘空间检查 ─────────────────────────────────────────────────────────
log_hr "6️⃣  磁盘空间检查"

DISK_USAGE=$(df -h "$HOME" | tail -1)
DISK_PCT=$(echo "$DISK_USAGE" | awk '{print $5}' | sed 's/%//')
DISK_AVAIL=$(echo "$DISK_USAGE" | awk '{print $4}')
log_info "磁盘使用率: ${DISK_PCT}% | 可用空间: ${DISK_AVAIL}"

if [ "$DISK_PCT" -gt 85 ]; then
  log_fail "磁盘空间不足（${DISK_PCT}%），建议尽快清理"
  FAILED=$((FAILED+1))
elif [ "$DISK_PCT" -gt 70 ]; then
  log_warn "磁盘使用率较高（${DISK_PCT}%），请注意"
  WARN=$((WARN+1))
else
  log_ok "磁盘空间充足"
fi

# ── 汇总 ──
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ "$FAILED" -gt 0 ]; then
  echo -e "${RED}  ❌ 维护完成: $FAILED 个失败, $WARN 个警告${NC}"
elif [ "$WARN" -gt 0 ]; then
  echo -e "${YELLOW}  ⚠️  维护完成: $WARN 个警告（无严重问题）${NC}"
else
  echo -e "${GREEN}  ✅ 维护完成: 一切正常${NC}"
fi
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
exit $FAILED
