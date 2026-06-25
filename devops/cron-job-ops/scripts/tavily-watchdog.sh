#!/bin/bash
# tavily-watchdog.sh — Check Tavily API usage and alert when running low
# Intended for use as a no_agent cron job (e.g. weekly Friday 20:00)
# Exit codes: 0=OK, 1=warning (100-199 left), 2=critical (<100 left)
#
# Usage: bash tavily-watchdog.sh

TAVILY_KEY=$(grep TAVILY_API_KEY /home/andymao/.hermes/.env | cut -d= -f2)
RESP=$(curl -s --request GET --url https://api.tavily.com/usage \
  --header "Authorization: Bearer ${...USAGE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['key']['usage'])" 2>/dev/null)
LIMIT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['key']['limit'] or d['account']['plan_limit'])" 2>/dev/null)

if [ -z "$USAGE" ] || [ -z "$LIMIT" ]; then
  echo "Tavily 用量查询失败，API 可能不可用"
  exit 1
fi

REMAIN=$((LIMIT - USAGE))

echo ""
echo "Tavily API 用量检查"
echo "已用: $USAGE / $LIMIT"
echo "剩余: $REMAIN"

if [ "$REMAIN" -ge 200 ]; then
  echo "状态：充足"
  exit 0
elif [ "$REMAIN" -ge 100 ]; then
  echo ""
  echo "Tavily 用量预警！仅剩 $REMAIN 次"
  echo "建议准备替代方案：Google 搜索或注册 Serper key"
  exit 1
else
  echo ""
  echo "Tavily 即将用完！仅剩 $REMAIN 次"
  echo "需要处理："
  echo "  1. 切换为 Google 搜索替代"
  echo "  2. 去 https://serper.dev 注册新 API Key"
  exit 2
fi
