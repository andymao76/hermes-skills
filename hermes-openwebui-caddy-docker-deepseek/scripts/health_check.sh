#!/usr/bin/env bash
set -euo pipefail

echo "== Docker Open WebUI =="
docker ps | grep open-webui || true
curl -I -m 5 http://127.0.0.1:3001 || true

echo
echo "== Caddy =="
sudo caddy validate --config /etc/caddy/Caddyfile || true
sudo systemctl status caddy --no-pager || true

echo
echo "== HTTPS via Caddy =="
curl --noproxy '*' -vk -m 10 https://openwebui.local:8443 2>&1 | tail -80 || true

echo
echo "== Proxy =="
env | grep -i proxy || true
docker info | grep -i proxy || true

echo
echo "== hosts / IP =="
grep openwebui.local /etc/hosts || true
ip -4 addr show | grep -oP 'inet \K[\d.]+' || true
