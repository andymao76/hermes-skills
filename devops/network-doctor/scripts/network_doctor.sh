#!/bin/bash
# Hermes 网络医生 — 一键诊断脚本
# 用法: bash ~/.hermes/skills/network-doctor/scripts/network_doctor.sh
# 输出: 诊断报告，含建议修复命令

PASS=0 FAIL=0 TOTAL=0

ok()   { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  [✓] $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  [✗] $1"; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║    Hermes 网络医生 — 诊断报告       ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. 代理进程
echo "── 1. 代理进程 ──"
ss -lntp 2>/dev/null | grep -q 7897 && ok "代理端口 7897 LISTEN" || fail "代理端口 7897 未监听"

# 2. 代理环境变量
echo "── 2. 代理环境变量 ──"
[[ "$HTTP_PROXY" == "http://127.0.0.1:7897" ]] && ok "HTTP_PROXY 正确" || fail "HTTP_PROXY: ${HTTP_PROXY:-未设置}"
[[ "$HTTPS_PROXY" == "http://127.0.0.1:7897" ]] && ok "HTTPS_PROXY 正确" || fail "HTTPS_PROXY: ${HTTPS_PROXY:-未设置}"
[[ -z "$ALL_PROXY" ]] && ok "无 ALL_PROXY（无冲突）" || fail "ALL_PROXY 存在: $ALL_PROXY（建议清除）"

# 3. 外网连通性
echo "── 3. 外网连通性 ──"
[[ $(curl -s -o /dev/null -w "%{http_code}" https://www.baidu.com --max-time 5) == "200" ]] && ok "百度可达（国内）" || fail "百度不可达"
[[ $(curl -s -o /dev/null -w "%{http_code}" https://www.google.com --max-time 5) == "200" ]] && ok "Google 可达（海外）" || fail "Google 不可达（无代理/代理故障）"

# 4. DNS
echo "── 4. DNS ──"
host google.com 8.8.8.8 &>/dev/null && ok "DNS 解析正常 (8.8.8.8)" || fail "DNS 解析失败"

# 5. Provider 连通性
echo "── 5. Provider ──"
for provider in "DeepSeek:https://api.deepseek.com" "SiliconFlow:https://api.siliconflow.cn" "Gemini:https://generativelanguage.googleapis.com" "Nous:https://inference-api.nousresearch.com"; do
  name="${provider%%:*}"
  url="${provider##*:}"
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 5)
  if [[ "$code" == "401" || "$code" == "404" || "$code" == "200" ]]; then
    ok "$name API 可达 ($code)"
  else
    fail "$name API 不可达 ($code)"
  fi
done

# 6. 网络模式判断
echo "── 6. 网络模式 ──"
baidu_ok=$(curl -s -o /dev/null -w "%{http_code}" https://www.baidu.com --max-time 5)
google_ok=$(curl -s -o /dev/null -w "%{http_code}" https://www.google.com --max-time 5)
if [[ "$google_ok" == "200" ]]; then echo "  → 海外模式 (Gemini/OpenAI优先)"
elif [[ "$baidu_ok" == "200" ]]; then echo "  → 中国模式 (DeepSeek/SiliconFlow优先)"
else echo "  → 无网络连接"
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  诊断完成: $PASS/$TOTAL 通过"
echo "╚══════════════════════════════════════╝"

if [[ $FAIL -gt 0 ]]; then
  echo ""
  echo "建议操作:"
  [[ $(ss -lntp 2>/dev/null | grep -c 7897) -eq 0 ]] && echo "  • 重启代理: pkill clash-meta && ~/Applications/clash-verge.AppImage &"
  [[ -n "$ALL_PROXY" ]] && echo "  • 清除 ALL_PROXY: unset ALL_PROXY"
  exit 1
fi
exit 0
