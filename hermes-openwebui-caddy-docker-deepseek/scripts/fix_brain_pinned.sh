#!/usr/bin/env bash
set -euo pipefail
PIN_DIR="/home/andymao/Documents/Obsidian Vault/Brain"
PIN_FILE="$PIN_DIR/pinned.md"
mkdir -p "$PIN_DIR"
if [ ! -f "$PIN_FILE" ]; then
  cat > "$PIN_FILE" <<'PIN'
# Pinned Memory

- Open WebUI 已改用 Docker 部署。
- Open WebUI 本机端口：127.0.0.1:3001
- Caddy HTTPS 地址：https://openwebui.local:8443
- Caddy 反代：127.0.0.1:3001
PIN
fi
echo "OK: $PIN_FILE"
ls -lh "$PIN_FILE"
