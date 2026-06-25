#!/usr/bin/env bash
# Comprehensive network & proxy diagnostics script
# Requires: curl, dig, git, ss
# No external dependencies — uses stdlib only
# Usage: bash network-doctor/references/full-diag.sh
# Or run each step individually

echo "=== 代理环境变量 ==="
env | grep -i proxy | sort || echo "  （未设置）"

echo ""
echo "=== 代理端口连通性 ==="
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/7897' 2>/dev/null && echo "  HTTP  127.0.0.1:7897 → 可达 ✅" || echo "  HTTP  127.0.0.1:7897 → 不可达 ❌"
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/7898' 2>/dev/null && echo "  SOCKS 127.0.0.1:7898 → 可达 ✅" || echo "  SOCKS 127.0.0.1:7898 → 不可达"

echo ""
echo "=== DNS 解析 ==="
for host in "github.com" "google.com" "baidu.com" "cnb.cool"; do
  ip=$(dig +short "$host" 2>/dev/null | head -1)
  if [ -z "$ip" ]; then
    echo "  $host → 解析失败 ❌"
  else
    echo "  $host → $ip ✅"
  fi
done

echo ""
echo "=== 外网连通性（通过代理） ==="
for site_url in "https://github.com" "https://google.com" "https://www.baidu.com" "https://cnb.cool"; do
  status=$(curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" --max-time 10 "$site_url" 2>&1)
  echo "  $site_url → $status"
done

echo ""
echo "=== 延迟对比（代理 vs 直连） ==="
echo "  站点          代理延迟     直连延迟"
echo "  ─────────────────────────────────────"
for entry in "GitHub|https://github.com" "Google|https://google.com" "百度|https://www.baidu.com" "cnb.cool|https://cnb.cool"; do
  name="${entry%%|*}"
  url="${entry##*|}"
  via=$(curl -s -o /dev/null -w "%{time_total}s" --max-time 10 "$url" 2>&1)
  direct=$(curl -s -o /dev/null -w "%{time_total}s" --noproxy '*' --max-time 10 "$url" 2>&1)
  printf "  %-12s %-13s %s\n" "$name" "$via" "$direct"
done

echo ""
echo "=== Hermes Git 远程连通性 ==="
HERMES_DIR="$HOME/.hermes/hermes-agent"
if [ -d "$HERMES_DIR" ]; then
  cd "$HERMES_DIR"
  echo "  origin (GitHub):"
  git fetch origin main --dry-run 2>&1 | head -2
  echo "  mirror (cnb.cool):"
  git fetch mirror main --dry-run 2>&1 | head -2
else
  echo "  Hermes Agent 目录不存在: $HERMES_DIR"
fi

echo ""
echo "=== Clash 进程 ==="
ps aux | grep -E "clash|mihomo" | grep -v grep || echo "  未找到 Clash 进程"

echo ""
echo "=== 监听端口 ==="
ss -tlnp 2>/dev/null | grep -E "789[0-9]|909[0-9]" || echo "  未找到相关端口"

echo ""
echo "=== 诊断完成 ==="
