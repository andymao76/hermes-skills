#!/usr/bin/env bash
set -euo pipefail
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.$(date +%F_%H%M%S)
sudo tee /etc/caddy/Caddyfile >/dev/null <<'CADDY'
{
    auto_https disable_redirects
}

https://openwebui.local:8443 {
    tls internal
    reverse_proxy 127.0.0.1:3001
}
CADDY
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
curl --noproxy '*' -vk https://openwebui.local:8443 | head -40
