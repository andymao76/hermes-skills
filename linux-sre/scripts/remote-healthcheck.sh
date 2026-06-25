#!/bin/bash
# Hermes 远程服务器健康检查脚本
# 用于 cron 定时巡检远端服务器
# 用法: ./remote-healthcheck.sh [server_name]
# 默认: tencent

SERVER="${1:-tencent}"

# SSH 可达性检查
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$SERVER" "echo ok" 2>/dev/null; then
  echo "❌ $SERVER: 无法连接"
  exit 1
fi

ssh "$SERVER" bash -s <<'REMOTE'
echo "========================================"
echo "  服务器: $(hostname)"
echo "  时间:   $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""
echo "--- 系统运行时间 ---"
uptime
echo ""
echo "--- CPU 信息 ---"
lscpu | grep -E 'Model name|^CPU\(s\)' | head -2
echo ""
echo "--- 内存 ---"
free -h
echo ""
echo "--- 磁盘 ---"
df -h / 2>/dev/null | tail -1
echo ""
echo "--- 监听端口 ---"
ss -tlnp 2>/dev/null | grep -E ':(80|443|3000|8080|9099|8642) ' || echo "(无关键端口)"
echo ""
echo "--- 最耗 CPU 的 5 个进程 ---"
ps aux --sort=-%cpu 2>/dev/null | head -6
echo ""
echo "--- 最耗内存的 5 个进程 ---"
ps aux --sort=-%mem 2>/dev/null | head -6
echo ""
echo "--- 最近登录 ---"
last -5 2>/dev/null || echo "(无记录)"
REMOTE

exit_code=$?
if [ $exit_code -eq 0 ]; then
  echo ""
  echo "✅ $SERVER: 巡检完成"
else
  echo ""
  echo "⚠️  $SERVER: 巡检异常退出 (exit=$exit_code)"
fi
exit $exit_code
