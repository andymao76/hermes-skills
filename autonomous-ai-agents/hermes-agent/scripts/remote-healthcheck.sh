#!/usr/bin/env bash
# 腾讯云服务器定时巡检脚本 — no_agent 模式
# 用法: bash remote-healthcheck.sh
# 适合 cron no_agent 模式：stdout 直接投递
# =============================================

SERVER="tencent"
DATE=$(date '+%Y-%m-%d %H:%M')
WARN=false

# 构造远程命令（用单引号 heredoc 防止变量展开）
CMDS=$(cat <<'HEREDOC'
echo '===UPTIME==='
uptime
echo '===DISK==='
df -h / | tail -1
echo '===MEM==='
free -m | awk 'NR==2{print $2,$3,int($3/$2*100)}'
echo '===PROCS==='
for p in nginx hermes caddy; do
  if [ "$p" = "hermes" ]; then
    pgrep -f hermes_cli.main >/dev/null 2>&1 && echo "$p:1" || echo "$p:0"
  else
    pgrep -x "$p" >/dev/null 2>&1 && echo "$p:1" || echo "$p:0"
  fi
done
echo '===PORTS==='
ss -tlnp 2>/dev/null | grep -E ':(80|443|3000|8080|9099|8642) ' | awk '{print $4}'
echo '===LOGS==='
journalctl -p err -n 5 --no-pager 2>/dev/null | tail -3
HEREDOC
)

RAW=$(echo "$CMDS" | ssh ${SERVER} -o ConnectTimeout=10 "bash" 2>&1)
RC=$?

if [ $RC -ne 0 ]; then
    echo "🔴 腾讯云巡检失败 — SSH 连接出错 (exit $RC)"
    exit 1
fi

# 解析结果
UPTIME=$(echo "$RAW" | sed -n '/^===UPTIME===/,/^===DISK===/p' | grep -v '===' | sed 's/.*up //;s/,.*//' | head -1)
LOAD=$(echo "$RAW" | sed -n '/^===UPTIME===/,/^===DISK===/p' | grep -v '===' | awk -F'load average:' '{print $2}' | xargs | head -1)

DISK_LINE=$(echo "$RAW" | sed -n '/^===DISK===/,/^===MEM===/p' | grep -v '===')
DISK_TOTAL=$(echo "$DISK_LINE" | awk '{print $2}')
DISK_USED=$(echo "$DISK_LINE" | awk '{print $3}')
DISK_PCT=$(echo "$DISK_LINE" | awk '{print $5}' | sed 's/%//')

MEM_LINE=$(echo "$RAW" | sed -n '/^===MEM===/,/^===PROCS===/p' | grep -v '===')
MEM_TOTAL=$(echo "$MEM_LINE" | awk '{print $1}')
MEM_USED=$(echo "$MEM_LINE" | awk '{print $2}')
MEM_PCT=$(echo "$MEM_LINE" | awk '{print $3}')

PROCS=$(echo "$RAW" | sed -n '/^===PROCS===/,/^===PORTS===/p' | grep -v '===')
NGINX=$(echo "$PROCS" | grep "^nginx:" | cut -d: -f2)
HERMES=$(echo "$PROCS" | grep "^hermes:" | cut -d: -f2)

PORTS=$(echo "$RAW" | sed -n '/^===PORTS===/,/^===LOGS===/p' | grep -v '===')
LOGS=$(echo "$RAW" | sed -n '/^===LOGS===/,$p' | grep -v '===')

# 构建报告
echo "## 腾讯云巡检 — ${DATE}"
echo ""
echo "### 系统"
echo "- 运行时间: ${UPTIME:-N/A}"
echo "- 负载: ${LOAD:-N/A}"
echo ""
echo "### 磁盘"
echo "- ${DISK_TOTAL:-?} 总量 / ${DISK_USED:-?} 已用 (${DISK_PCT:-0}%)"
[ "${DISK_PCT:-0}" -gt 85 ] 2>/dev/null && echo "- ⚠️ 磁盘超过 85%！" && WARN=true
echo ""
echo "### 内存"
echo "- ${MEM_TOTAL:-?}MB 总量 / ${MEM_USED:-?}MB 已用 (${MEM_PCT:-0}%)"
[ "${MEM_PCT:-0}" -gt 90 ] 2>/dev/null && echo "- ⚠️ 内存超过 90%！" && WARN=true
echo ""
echo "### 服务状态"
[ "$NGINX" = "1" ] && echo "- ✅ nginx: 运行中" || { echo "- ❌ nginx: 未运行"; WARN=true; }
[ "$HERMES" = "1" ] && echo "- ✅ hermes: 运行中" || { echo "- ❌ hermes: 未运行"; WARN=true; }
echo ""
echo "### 端口监听"
[ -n "$PORTS" ] && echo "\`\`\`" && echo "${PORTS}" && echo "\`\`\`" || echo "- 无关键端口"
echo ""
echo "### 系统错误日志"
[ -n "$LOGS" ] && [ "$LOGS" != "No entries" ] && echo "\`\`\`" && echo "${LOGS}" && echo "\`\`\`" || echo "- 无"
echo ""
echo "---"
[ "$WARN" = true ] && echo "🔴 **存在告警**" || echo "🟢 **一切正常**"
