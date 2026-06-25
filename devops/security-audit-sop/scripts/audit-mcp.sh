#!/bin/bash
# audit-mcp.sh — 审计 MCP Server 配置
echo "=== MCP Server 审计 ==="

# 检查 MCP 配置文件
MCP_CONFIG=~/.hermes/mcp.json
if [ -f "$MCP_CONFIG" ]; then
  echo "✅ MCP 配置文件存在: $MCP_CONFIG"
  
  # 检查 MCP 配置中的网络端点
  grep -o '"url"[[:space:]]*:[[:space:]]*"[^"]*"' "$MCP_CONFIG" 2>/dev/null | while read url; do
    echo "ℹ️  MCP 端点: $url"
  done
  
  # 检查是否有 localhost 绑定
  grep -o '"127\.0\.0\.1\|"localhost' "$MCP_CONFIG" 2>/dev/null && echo "✅ MCP 绑定本地地址" \
    || echo "⚠️  检查 MCP 是否有外部地址绑定"
  
  # 检查认证配置
  grep -qi '"apiKey\|"token\|"auth' "$MCP_CONFIG" 2>/dev/null && echo "✅ MCP 配置含认证信息" \
    || echo "⚠️  MCP 配置未检测到显式认证"
else
  echo "ℹ️  MCP 配置文件不存在"
fi

# MCP 进程检查
echo "--- MCP 进程检查 ---"
ps aux | grep -i '[m]cp' && echo "ℹ️  MCP 相关进程运行中" || echo "ℹ️  无 MCP 进程运行"
