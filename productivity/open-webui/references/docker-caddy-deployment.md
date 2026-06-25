# Docker + Caddy HTTPS 部署变体

适用于局域网内通过 Caddy 提供 HTTPS 加密访问的场景（与 cloud 服务器上 pip 安装的方式互补）。

## 架构

```
浏览器
  ↓ https://openwebui.local:8443
Caddy (宿主机, TLS internal)
  ↓ http://127.0.0.1:3001
Open WebUI Docker (容器内 :8080 → 宿主机 :3001)
```

## 核心步骤

### 1. Docker 安装 Open WebUI

```bash
docker pull ghcr.io/open-webui/open-webui:main
docker rm -f open-webui 2>/dev/null
docker run -d \
  --name open-webui \
  --restart always \
  -p 127.0.0.1:3001:8080 \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

### 2. Caddy HTTPS 反代

```caddy
{
    auto_https disable_redirects
}
https://openwebui.local:8443 {
    tls internal
    reverse_proxy 127.0.0.1:3001
}
```

### 3. Clash 直连规则

若浏览器 `ERR_CONNECTION_CLOSED` 但 curl 正常，是本地代理劫持，在 Clash `rules:` 开头加：

```yaml
- DOMAIN,openwebui.local,DIRECT
- DOMAIN-SUFFIX,local,DIRECT
- IP-CIDR,127.0.0.1/32,DIRECT
- IP-CIDR,192.168.0.0/16,DIRECT
```

### 4. 证书信任

```bash
sudo cp /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt \
  /usr/local/share/ca-certificates/caddy-local.crt
sudo update-ca-certificates
```

## 相比 pip 安装的区别

| 维度 | pip 安装 | Docker + Caddy |
|------|----------|----------------|
| 隔离性 | 宿主机 Python 环境 | 容器隔离 |
| HTTPS | 需额外配置 | Caddy 自动管理内部证书 |
| 端口 | 直接监听 | 通过反代暴露不同端口 |
| 适用场景 | 云服务器直接访问 | 局域网通过域名访问 |
| 内存开销 | ~1GB | 与 pip 安装相当 |

## 参见

完整排错记录详见技能 `hermes-openwebui-caddy-docker-deepseek`。
