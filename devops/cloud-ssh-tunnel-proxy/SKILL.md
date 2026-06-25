---
name: cloud-ssh-tunnel-proxy
description: "云服务器 SSH 反向隧道 + Nginx 反向代理 — 打通本地服务到公网。覆盖 SSH 隧道(Nginx+autossh)、Nginx 反向代理、腾讯云安全组配置、GatewayPorts 设置、隧道保活。适用于 Tencent Cloud/AWS/阿里云等任意 Linux 云服务器。"
tags: [云服务器, SSH隧道, 反向代理, Nginx, 内网穿透]
---

# SSH Reverse Tunnel + Nginx 反向代理

将本地服务（Dify、Web 应用等）通过云服务器公网 IP 暴露到互联网。

## 架构

```
用户 → http://公网IP:80 → 云服务器 Nginx → localhost:8888
                                               ↑
                                        SSH 反向隧道
                                               ↑
                                    本地服务器 localhost:80
```

## 配置步骤

### 1. 云服务器准备

```bash
# 安装 Nginx
sudo apt install -y nginx
sudo systemctl enable nginx

# 开启 SSH GatewayPorts（让隧道绑定到 0.0.0.0）
sudo sed -i 's/#GatewayPorts no/GatewayPorts yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### 2. Nginx 反向代理配置

```nginx
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
sudo tee /etc/nginx/sites-available/tunnel << 'EOF'
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
EOF
sudo ln -sf /etc/nginx/sites-available/tunnel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### 3. SSH 反向隧道

**一次性测试：**

```bash
ssh -i ~/.ssh/云密钥.pem -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N -R 8888:localhost:80 用户@公网IP
```

**`-R` 参数格式：** `-R 云端口:本地地址:本地端口`

| 场景 | 命令 |
|------|------|
| 本地:80 → 云:8888 | `-R 8888:localhost:80` |
| 本地:5001 → 云:9999 | `-R 9999:localhost:5001` |
| 多个服务 | 多个 `-R` 参数 |

### 4. 隧道保活

**方法一：autossh（推荐）**

```bash
# 安装
sudo apt install -y autossh

# 启动
autossh -M 0 -i ~/.ssh/云密钥.pem \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N -R 8888:localhost:80 用户@公网IP
```

**方法二：SSH keepalive 脚本**

```bash
#!/bin/bash
while true; do
    ssh -i ~/.ssh/云密钥.pem \
        -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        -N -R 8888:localhost:80 用户@公网IP
    sleep 5
done
```

## 腾讯云安全组

需要在控制台开放入站规则：

| 协议 | 端口 | 来源 | 用途 |
|:----:|:----:|------|------|
| TCP | 22 | 0.0.0.0/0 | SSH |
| TCP | 80 | 0.0.0.0/0 | HTTP |
| TCP | 443 | 0.0.0.0/0 | HTTPS（可选） |

**注意：** 添加 HTTP 规则时不要误删 SSH 22 端口规则，否则会失去服务器连接。

## 验证

```bash
# 在云服务器上测试隧道
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8888/
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:80/
# 测试公网访问
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://公网IP/
```

## 排错

| 现象 | 原因 | 解决 |
|------|------|------|
| SSH 连接超时 | 安全组没开放 22 端口 | 检查云控制台安全组规则 |
| 公网 502 Bad Gateway | 隧道断了 | 重启隧道 |
| remote port forwarding failed | 云上端口被占用 | `fuser -k 8888/tcp` |
| Permission denied | SSH 密钥权限不对 | `chmod 600 ~/.ssh/*.pem` |
| SSH 间歇性断连 | 服务器重启后隧道丢失 | 重启隧道进程，或添加 systemd 自动重启 |

## 坑点

### 安全组规则覆盖

腾讯云安全组修改时，**添加 HTTP 规则可能会覆盖现有 SSH 规则**。如果配置 80 端口后 SSH 断开：

1. 先通过腾讯云控制台 VNC/管理终端进入服务器
2. 检查安全组入站规则是否包含 TCP 22
3. 如果丢失，重新添加 SSH 规则
4. 不要同时替换全部规则 — 先加再加，不要先删再加

### 服务器重启后隧道丢失

云服务器重启后，SSH 隧道进程自动终止。需要重新启动：

```bash
# 手动重启
ssh -i ~/.ssh/云密钥.pem -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -N -R 8888:localhost:80 用户@公网IP &
```

推荐用 systemd 用户服务实现隧道自动重启（见上方「隧道保活」章节）。

### 云上 Hermes 实例重启后恢复

如果云上运行 Hermes Agent，重启后需要：
1. 重新配置 `.env` 中的平台 Token（`QQ_APP_ID`、`TELEGRAM_BOT_TOKEN` 等）
2. 重新启用 Gateway：`systemctl --user restart hermes-gateway`
3. 验证平台连通性

## 相关参考

- `references/remote-hermes-cli-ssh.md` — 通过 SSH 远程调用 Hermes CLI 的完整命令与 bash 函数
- `references/sync-hermes-to-remote.md` — 将技能和 API Key 同步到远程 Hermes 服务器
