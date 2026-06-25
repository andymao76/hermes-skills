---
name: hermes-openwebui-caddy-docker-deepseek
description: >-
  Open WebUI Docker 部署 + Caddy HTTPS 反代 + DeepSeek 400 排错的完整实战记录。
  覆盖 Docker daemon 代理配置、Caddy 内部证书、Clash 直连规则、Hermes brain_pin
  dict→DeepSeek 400 的根因定位与修复。
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [open-webui, caddy, docker, deepseek, troubleshooting, reverse-proxy, ssl]
    related_skills: [open-webui, network-proxy-diagnostics]
---

# Hermes Skill: Open WebUI Docker + Caddy HTTPS + DeepSeek 400 排错

## 适用场景

用于 Ubuntu 单机环境中排查和修复：

- Open WebUI 旧 venv 安装损坏，`open-webui` 命令不存在。
- 改用 Docker 部署 Open WebUI。
- Caddy 反向代理 `https://openwebui.local:8443` 到 `127.0.0.1:3001`。
- Docker 拉取镜像失败，daemon 代理端口错误。
- 浏览器访问 `openwebui.local` 被 Clash/浏览器代理劫持。
- Caddy/curl 正常但浏览器 `ERR_CONNECTION_CLOSED`。
- Hermes 使用 DeepSeek Provider 报：`messages[n]: content should be a string or a list`。
- Hermes `brain_pin` 读取 `Brain/pinned.md` 缺失，tool result content 被塞成 dict，导致 DeepSeek API 400。

> **层次关系**：本技能是 `open-webui` 伞技能下的 Docker + Caddy 部署变体专项。在同一台机器上使用 pip 安装的开发者请参考 `open-webui` 伞技能（含 HF 镜像、多 Provider 配置、API 初始化等专项）。

## 推荐架构

```text
浏览器
  ↓
https://openwebui.local:8443
  ↓
Caddy on host
  ↓
127.0.0.1:3001
  ↓
Open WebUI Docker container: 8080

Hermes Agent: host machine
DeepSeek / Qwen / Nous provider: external API
```

关键原则：Open WebUI 用 Docker；Hermes Agent 留在宿主机；Caddy 留在宿主机；Docker 只绑定 `127.0.0.1:3001`。

---

## 1. 判断 Open WebUI 是否正常

```bash
curl -I http://127.0.0.1:3001
```

成功标志：

```text
HTTP/1.1 200 OK
server: uvicorn
```

如果这个能访问，Open WebUI 本体已经正常。

---

## 2. 清理旧非容器 Open WebUI

检查旧 venv：

```bash
source ~/open-webui/venv/bin/activate
python -m pip show open-webui
which open-webui
```

若没有 Open WebUI 包，备份旧目录：

```bash
mkdir -p ~/BACKUP/open-webui-cleanup
[ -d ~/open-webui ] && mv ~/open-webui ~/BACKUP/open-webui-cleanup/open-webui.bak.$(date +%F_%H%M%S)
```

清理旧服务：

```bash
sudo systemctl stop open-webui 2>/dev/null
sudo systemctl disable open-webui 2>/dev/null
systemctl --user stop open-webui 2>/dev/null
systemctl --user disable open-webui 2>/dev/null
sudo rm -f /etc/systemd/system/open-webui.service
rm -f ~/.config/systemd/user/open-webui.service
sudo systemctl daemon-reload
systemctl --user daemon-reload
```

---

## 3. 修复 Docker daemon 代理

检查：

```bash
env | grep -i proxy
docker info | grep -i proxy
```

如果 shell 是 `7897`，Docker 却是 `33331`，查旧配置：

```bash
sudo grep -R "33331" /etc/systemd/system/docker.service.d /etc/docker /lib/systemd/system/docker.service /usr/lib/systemd/system/docker.service 2>/dev/null
```

若在 `/etc/docker/daemon.json`，保留原字段，只把 proxies 改成：

```json
{
  "iptables": true,
  "ipv6": false,
  "registry-mirrors": [],
  "proxies": {
    "http-proxy": "http://127.0.0.1:7897",
    "https-proxy": "http://127.0.0.1:7897",
    "no-proxy": "localhost,127.0.0.1,::1,192.168.1.0/24"
  }
}
```

重启：

```bash
sudo systemctl restart docker
docker info | grep -i proxy
```

目标：

```text
HTTP Proxy: http://127.0.0.1:7897
HTTPS Proxy: http://127.0.0.1:7897
```

---

## 4. Docker 安装 Open WebUI

不要再测试 Docker Hub `hello-world`，若匿名额度耗尽，会报：

```text
You have reached your unauthenticated pull rate limit
```

直接拉 GHCR：

```bash
docker pull ghcr.io/open-webui/open-webui:main
```

启动：

```bash
docker rm -f open-webui 2>/dev/null

docker run -d \
  --name open-webui \
  --restart always \
  -p 127.0.0.1:3001:8080 \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

验证：

```bash
docker ps | grep open-webui
curl -I http://127.0.0.1:3001
```

第一次启动可能 `health: starting` 或短暂连接重置，查看日志：

```bash
docker logs -f open-webui
```

---

## 5. Caddy HTTPS 反向代理

推荐最终 `/etc/caddy/Caddyfile`：

```caddy
{
    auto_https disable_redirects
}

https://openwebui.local:8443 {
    tls internal
    reverse_proxy 127.0.0.1:3001
}
```

写入并重载：

```bash
sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.$(date +%F_%H%M%S)

sudo tee /etc/caddy/Caddyfile >/dev/null <<'CADDYEOF'
{
    auto_https disable_redirects
}

https://openwebui.local:8443 {
    tls internal
    reverse_proxy 127.0.0.1:3001
}
CADDYEOF

sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

验证：

```bash
curl --noproxy '*' -vk https://openwebui.local:8443
```

成功标志：

```text
HTTP/2 200
server: Caddy
server: uvicorn
<title>Open WebUI</title>
```

---

## 6. hosts 配置

确认真实 IP：

```bash
ip -4 addr show | grep -oP 'inet \K[\d.]+'
```

`/etc/hosts` 不要保留旧 IP，例如错误的 `192.168.1.77`。推荐：

```text
192.168.1.53 openwebui.local rhino01
```

修复：

```bash
sudo cp /etc/hosts /etc/hosts.bak.$(date +%F_%H%M%S)
sudo sed -i '/openwebui.local/d' /etc/hosts
sudo sed -i '/192\.168\.1\.77/d' /etc/hosts
echo '192.168.1.53 openwebui.local rhino01' | sudo tee -a /etc/hosts
```

---

## 7. 浏览器打不开但 curl 正常

若浏览器 `ERR_CONNECTION_CLOSED`，但：

```bash
curl --noproxy '*' -vk https://openwebui.local:8443
```

返回 `HTTP/2 200`，说明服务端正常，是 Clash/浏览器代理没有直连。

Clash 规则在 `rules:` 最前面加入：

```yaml
- DOMAIN,openwebui.local,DIRECT
- DOMAIN-SUFFIX,local,DIRECT
- IP-CIDR,127.0.0.1/32,DIRECT
- IP-CIDR,192.168.1.53/32,DIRECT
- IP-CIDR,192.168.0.0/16,DIRECT
```

Chrome 清理：

```text
chrome://net-internals/#dns
chrome://net-internals/#sockets
```

点击 `Clear host cache` 和 `Flush socket pools`。

---

## 8. 信任 Caddy 本地证书

Caddy 日志中：

```text
failed to install root certificate
caddy : user NOT in sudoers
```

不是服务失败，只是 Caddy 无法自动安装本地 CA。手工导入：

```bash
sudo cp /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt \
  /usr/local/share/ca-certificates/caddy-local.crt
sudo update-ca-certificates
```

然后重启浏览器。

---

## 9. Hermes + DeepSeek 400 定位与修复

报错：

```text
BadRequestError [HTTP 400]
Provider: deepseek
messages[8]: content should be a string or a list
```

深度扫描 request dump：

```bash
python3 - <<'PY'
import json
p="/home/andymao/.hermes/sessions/request_dump_替换成实际文件名.json"
with open(p, "r", encoding="utf-8") as f:
    d=json.load(f)

def walk(obj, path="root"):
    if isinstance(obj, dict):
        if "messages" in obj and isinstance(obj["messages"], list):
            print("FOUND messages at:", path + ".messages", "len=", len(obj["messages"]))
            for i,m in enumerate(obj["messages"]):
                if not isinstance(m, dict):
                    print("BAD message object:", i, type(m), repr(m)[:300])
                    continue
                c=m.get("content")
                if not isinstance(c, (str, list)):
                    print("\nBAD content")
                    print("path:", path + f".messages[{i}].content")
                    print("role:", m.get("role"))
                    print("type:", type(c))
                    print("preview:", repr(c)[:1000])
        for k,v in obj.items():
            walk(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            walk(v, path + f"[{i}]")
walk(d)
PY
```

已确认坏消息：

```text
root.request.body.messages[8].content
role: tool
type: dict
path: Brain/pinned.md
present: false
```

根因：Hermes 的 `brain_pin` 工具读取 `Brain/pinned.md`，文件不存在时返回 dict 类型 tool result；DeepSeek API 要求 content 必须是 string 或 list。

快速修复：

```bash
mkdir -p "/home/andymao/Documents/Obsidian Vault/Brain"

cat > "/home/andymao/Documents/Obsidian Vault/Brain/pinned.md" <<'PINEOF'
# Pinned Memory

- Open WebUI 已改用 Docker 部署。
- Open WebUI 本机端口：127.0.0.1:3001
- Caddy HTTPS 地址：https://openwebui.local:8443
- Caddy 反代：127.0.0.1:3001
PINEOF
```

再试：

```bash
hermes chat
```

临时绕过：

```bash
hermes chat --ignore-user-config
```

---

## 10. 快速健康检查

```bash
docker ps | grep open-webui
docker logs --tail 80 open-webui
curl -I http://127.0.0.1:3001
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl status caddy --no-pager
sudo journalctl -u caddy -n 50 --no-pager
curl --noproxy '*' -vk https://openwebui.local:8443
env | grep -i proxy
docker info | grep -i proxy
grep openwebui.local /etc/hosts
ip -4 addr show | grep -oP 'inet \K[\d.]+'
```
