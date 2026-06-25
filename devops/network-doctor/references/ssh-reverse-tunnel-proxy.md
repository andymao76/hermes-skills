# SSH 反向隧道 + Nginx 反向代理

通过一台有公网 IP 的云服务器，将本地服务暴露到公网。

## 适用场景

| 场景 | 说明 |
|------|------|
| 本地 Dify 需要微信公众号 Webhook | 公众号要求公网 80/443 |
| Hermes Gateway 需要在云上稳定运行 | 云上长连接更可靠 |
| 临时演示本地开发的 Web 服务 | 无需部署即可公网访问 |

## 架构

```
用户 → 公网 IP:80 → 云服务器 Nginx → localhost:8888 → SSH 隧道 → 本地服务:80
```

## 一、云服务器准备

### 1.1 安装 Nginx

```bash
ssh ubuntu@<云IP> "sudo apt update && sudo apt install -y nginx"
```

### 1.2 配置 Nginx 反向代理

```bash
ssh ubuntu@<云IP> "sudo tee /etc/nginx/sites-available/local-tunnel << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/local-tunnel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx"
```

### 1.3 开启 SSH GatewayPorts

SSH 反向端口转发默认只绑定 `127.0.0.1`。要让外部访问，需开启 GatewayPorts：

```bash
ssh ubuntu@<云IP> "sudo sed -i 's/#GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config && sudo systemctl restart sshd"
```

### 1.4 开放安全组端口

| 协议 | 端口 | 来源 | 用途 |
|:----:|:----:|------|------|
| TCP | 22 | 0.0.0.0/0 | SSH |
| TCP | 80 | 0.0.0.0/0 | HTTP |
| TCP | 443 | 0.0.0.0/0 | HTTPS（可选） |

**腾讯云路径：** 云服务器 → 实例 → 安全组 → 入站规则

⚠️ **重要：** 添加 HTTP 规则时不要覆盖现有 SSH 规则（22 端口）。腾讯云安全组默认只有 SSH，加 HTTP 规则时必须同时保留 SSH 规则，否则会失去连接。

## 二、本地建立 SSH 隧道

### 2.1 直接 SSH 方式

```bash
ssh -i ~/.ssh/cloud-key.pem \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N \
    -R 8888:localhost:80 \
    ubuntu@<云IP>
```

- `-R 8888:localhost:80` — 云上的 8888 端口 → 本地的 80 端口
- `-N` — 不执行命令，只做端口转发
- `ServerAliveInterval=30` — 每 30 秒发心跳保活
- `ExitOnForwardFailure=yes` — 端口转发失败时立即退出（便于重连）

### 2.2 验证隧道

从云服务器确认端口已监听：

```bash
ssh ubuntu@<云IP> "ss -tlnp | grep 8888"
```

期望输出：`LISTEN 0 128 0.0.0.0:8888 0.0.0.0:*`

测试转发是否生效：

```bash
ssh ubuntu@<云IP> "curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8888/"
```

期望输出：`HTTP 307`（Dify 重定向）或 `HTTP 200`

### 2.3 验证公网访问

```bash
curl -s --noproxy '*' -o /dev/null -w "HTTP %{http_code}\n" http://<云IP>/
```

或通过代理：

```bash
curl -s --proxy http://127.0.0.1:7897 -o /dev/null -w "HTTP %{http_code}\n" http://<云IP>/
```

期望：`HTTP 200` 或 `HTTP 307`

## 三、持久化隧道（可选）

### 3.1 使用 autossh（推荐）

```bash
# 安装
sudo apt install -y autossh

# 建立持久隧道
autossh -M 0 \
    -i ~/.ssh/cloud-key.pem \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N \
    -R 8888:localhost:80 \
    ubuntu@<云IP>
```

`autossh` 会自动检测 SSH 断连并重新连接。

### 3.2 systemd 服务

```bash
sudo tee /etc/systemd/system/ssh-tunnel.service << 'EOF'
[Unit]
Description=SSH Reverse Tunnel
After=network-online.target

[Service]
User=andymao
ExecStart=/usr/bin/ssh -i /home/andymao/.ssh/cloud-key.pem \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N -R 8888:localhost:80 ubuntu@<云IP>
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now ssh-tunnel
```

## 四、故障排查

### 4.1 连接超时

| 现象 | 根因 | 解决 |
|------|------|------|
| `ssh: connect to host port 22: Connection timed out` | 安全组删了 SSH 规则 | 去云控制台恢复 22 端口 |
| `curl` 超时 | 安全组未开放 80 端口 | 添加入站规则 TCP 80 |
| 云上 `curl localhost:8888` 工作但公网不行 | GatewayPorts 未开启 | 开启后重启 sshd |
| Nginx 返回 502 | 隧道断了 | 检查 `ss -tlnp \| grep 8888`，重连隧道 |

### 4.2 多端口转发

需要暴露多个本地服务时，增加 `-R` 参数：

```bash
ssh -N \
    -R 8888:localhost:80 \    # Dify Web
    -R 9999:localhost:5001 \  # Dify API
    ubuntu@<云IP>
```

然后在 Nginx 中用不同的 `location` 或 `server_name` 分发。

### 4.3 SSH 隧道被本地代理劫持

本地有 Clash/TUN 代理时，SSH 可能走代理导致异常。确保 SSH 直连：

```bash
# SSH config 中加上
Host <云IP>
  ProxyCommand none
```
