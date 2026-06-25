#!/bin/bash
# WhatsApp Bridge Baileys Proxy Patch — 适用于国内网络环境
# 用法: bash ~/.hermes/skills/devops/hermes-whatsapp-bridge/scripts/apply-proxy-patch.sh
# 说明: 修改 bridge.js 使 Baileys WebSocket 通过 Clash 代理连接
# 注意: hermes update 会覆盖 bridge.js，升级后需重新执行此脚本

set -euo pipefail

BRIDGE_JS="$HOME/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js"
BRIDGE_DIR="$HOME/.hermes/hermes-agent/scripts/whatsapp-bridge"

if [ ! -f "$BRIDGE_JS" ]; then
    echo "❌ bridge.js 不存在: $BRIDGE_JS"
    exit 1
fi

echo "=== WhatsApp Bridge Baileys 代理补丁 ==="

# 1. 检查 https-proxy-agent 是否已安装
if [ ! -d "$BRIDGE_DIR/node_modules/https-proxy-agent" ]; then
    echo "📦 安装 https-proxy-agent..."
    cd "$BRIDGE_DIR"
    npm install https-proxy-agent
    echo "✅ 安装完成"
else
    echo "✅ https-proxy-agent 已安装"
fi

# 2. 检查 import 是否已添加
if grep -q "HttpsProxyAgent" "$BRIDGE_JS"; then
    echo "✅ 代理 import 已存在，跳过"
else
    echo "📝 添加 HttpsProxyAgent import..."
    sed -i "s/import qrcode from 'qrcode-terminal';/import qrcode from 'qrcode-terminal';\nimport { HttpsProxyAgent } from 'https-proxy-agent';/" "$BRIDGE_JS"
    echo "✅ import 已添加"
fi

# 3. 检查 makeWASocket 中是否有 proxyAgent
if grep -q "proxyAgent" "$BRIDGE_JS"; then
    echo "✅ 代理配置已存在，跳过"
else
    echo "📝 添加代理配置到 makeWASocket..."
    # 在 sock = makeWASocket({ 之前添加代理 agent 创建
    sed -i "s/sock = makeWASocket({/\/\/ Create proxy agent for Baileys WebSocket\n  const PROXY_URL = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || 'http:\/\/127.0.0.1:7897';\n  const proxyAgent = PROXY_URL ? new HttpsProxyAgent(PROXY_URL) : undefined;\n\n  sock = makeWASocket({/" "$BRIDGE_JS"
    # 在 logger, 行后添加 agent 配置
    sed -i "/logger,/a\    agent: proxyAgent,\n    fetchAgent: proxyAgent," "$BRIDGE_JS"
    echo "✅ 代理配置已添加"
fi

echo ""
echo "=== 补丁完成 ==="
echo "应用路径: $BRIDGE_JS"
echo "验证: grep -c 'HttpsProxyAgent' $BRIDGE_JS -> 应有 2 处匹配"
