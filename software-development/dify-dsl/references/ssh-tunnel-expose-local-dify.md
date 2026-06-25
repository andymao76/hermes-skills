# SSH 反向隧道暴露本地 Dify 到公网

当 Dify 运行在本地局域网（如 `192.168.1.49`），但需要公网访问时（微信公众号/webhook 回调等），可通过一台有公网 IP 的云服务器做 SSH 反向隧道。

## 架构

```
用户/公众号 → 云服务器 (公网IP:80) → Nginx → localhost:8888 → SSH 隧道 → 本地 Dify (80)
```

## 前置条件

| 条件 | 说明 |
|------|------|
| 云服务器 | 有公网 IP，Ubuntu 24.04 |
| SSH 密钥 | 云服务器的 .pem 私钥 |
| 本地 Dify | 运行在 `~/dify/docker/`，端口 80 |

## 步骤

### 1. 云服务器：安装 Nginx

```bash
sudo apt install -y nginx
```

### 2. 云服务器：启用 GatewayPorts

SSH 反向隧道默认只绑定到 `127.0.0.1`，需要开启 `GatewayPorts` 才能从外网访问：

```bash
sudo sed -i 's/#GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### 3. 云服务器：配置 Nginx 反向代理

```nginx
# /etc/nginx/sites-available/dify-tunnel
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -sf /etc/nginx/sites-available/dify-tunnel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

### 4. 云服务器：开放安全组端口

腾讯云/AWS/阿里云安全组需添加入站规则：

| 方向 | 端口 | 协议 | 来源 |
|:----:|:----:|:----:|:----:|
| 入站 | 80 | TCP | 0.0.0.0/0 |
| 入站 | 443 | TCP | 0.0.0.0/0 |

### 5. 本地：建立 SSH 反向隧道

```bash
ssh -i ~/.ssh/cloud-key.pem \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N \
    -R 8888:localhost:80 \
    ubuntu@<云服务器IP>
```

参数说明：
- `-R 8888:localhost:80` — 将云服务器的 8888 端口转发到本地的 80 端口
- `-N` — 不执行远程命令（仅做端口转发）
- `ServerAliveInterval=30` — 每 30 秒发心跳，防止隧道断开
- `ExitOnForwardFailure=yes` — 端口转发失败时立即退出

### 6. 验证

```bash
# 在云服务器上测试本地转发
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8888/

# 在云服务器上测试公网
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:80/

# 从外网测试（手机或另一台机器）
curl -s http://<公网IP>/
```

Dify 返回 `HTTP 307`（跳转到 `/apps`）即表示成功。

## 持久化隧道

### 方案一：systemd 用户服务（推荐）

```ini
# ~/.config/systemd/user/dify-tunnel.service
[Unit]
Description=Dify SSH Reverse Tunnel
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/ssh -i %h/.ssh/cloud-key.pem \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N \
    -R 8888:localhost:80 \
    ubuntu@<云服务器IP>
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable dify-tunnel
systemctl --user start dify-tunnel
```

### 方案二：autossh（自动重连）

```bash
sudo apt install -y autossh
autossh -M 0 -i ~/.ssh/cloud-key.pem \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N \
    -R 8888:localhost:80 \
    ubuntu@<云服务器IP>
```

## 多端口转发

需要转发多个本地服务时，指定多个 `-R`：

```bash
-R 8888:localhost:80     # Dify Web
-R 9999:localhost:5001   # Dify API
```

Nginx 端增加对应 `location` 块或不同端口：
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:9999/;
}
```

## 安全注意事项

- ⚠️ **腾讯云/阿里云安全组陷阱：** 添加 HTTP/HTTPS 入站规则时，如果控制台默认是「替换所有规则」，可能误删 SSH(22) 规则导致失联。**务必确认 SSH 22 端口规则存在**后再保存。
- ⚠️ `GatewayPorts yes` 会使端口暴露在所有网络接口上，建议配合云服务器安全组限制来源 IP
- ⚠️ SSH 密钥文件权限必须是 `600`，否则 SSH 拒绝使用
- ⚠️ 本地和云服务器的时间需要同步（NTP），否则 SSH 认证可能失败
- ✅ 使用 `StrictHostKeyChecking=no` 时首次连接会自动信任 host key
