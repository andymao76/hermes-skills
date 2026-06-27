# feishu-hermes 重启风暴案例 (2026-06-25)

## 背景

`feishu-hermes` 是一个飞书桥接服务，通过 Node.js 连接飞书 API。项目所在目录 `/home/andymao/feishu-hermes/` 后来被删除（迁移到官方 API），但对应的 systemd 服务配置未同步停用。

## 服务配置

### feishu-hermes.service

```ini
[Unit]
Description=Feishu Hermes Bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=andymao
WorkingDirectory=/home/andymao/feishu-hermes
EnvironmentFile=/home/andymao/feishu-hermes/.env
ExecStart=/usr/bin/node /home/andymao/feishu-hermes/server.js
Restart=always
RestartSec=5
```

### feishu-hermes-tunnel.service

```ini
[Unit]
Description=Feishu Hermes Quick Cloudflare Tunnel
After=network-online.target feishu-hermes.service
Wants=network-online.target

[Service]
Type=simple
User=andymao
WorkingDirectory=/home/andymao/feishu-hermes
ExecStart=/home/andymao/feishu-hermes/start_cloudflared_quick.sh
Restart=always
RestartSec=8
```

## 故障数据

| 指标 | 值 |
|------|-----|
| 运行时长 | 28 小时（25 小时+ 另一启动 3 小时） |
| feishu-hermes 重启次数 | 19,120 + 1,294 = 20,414 |
| feishu-hermes-tunnel 重启次数 | 11,970 |
| **合计无效重启** | **31,195 次** |
| 重启策略 | `Restart=always`，无 `StartLimitBurst` |
| 初始化可执行文件 | 已不存在（目录已删除） |
| EnvironmentFile | 已不存在 |

## 系统日志中的关键行

```
# journald 内存压力（核心指标）
journalctl -b -1 --no-pager | grep "Under memory pressure, flushing caches"

# libinput 输入延迟
libinput error: event3 - SEM USB Keyboard: client bug: event processing lagging behind by 4791ms, your system is too slow

# 重启计数器
systemd[1]: feishu-hermes.service: Scheduled restart job, restart counter is at 19119.

# Docker 健康检查超时
dockerd: Health check for container ... timed out starting health check
```

## 死机过程

```
目录已删除 → Restart=always（无限制）→ 每 5~8 秒无效重启
    ↓ 重复 31,195 次
journald 日志洪水 → "Under memory pressure, flushing caches"
    ↓
system 进入 thrashing → libinput 输入事件延迟 4.7 秒
    ↓
鼠标/键盘无响应 → SSH 断连
    ↓
只能强制重启
```

## 修复

```bash
# 紧急停止
sudo systemctl stop feishu-hermes.service feishu-hermes-tunnel.service
sudo systemctl disable feishu-hermes.service feishu-hermes-tunnel.service

# 添加重启上限（永久预防）
mkdir -p /etc/systemd/system/feishu-hermes.service.d/
tee /etc/systemd/system/feishu-hermes.service.d/override.conf << 'EOF'
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
EOF

# 同样的操作对 feishu-hermes-tunnel.service 也做一次
systemctl daemon-reload
```

## 教训

1. 永远不要使用裸 `Restart=always` — 必须配合 `StartLimitBurst`
2. 删除服务目录前应 **先停用并禁用** 对应的系统服务
3. 建议的 systemd 服务安全模板：

```ini
[Unit]
Description=...
After=network.target
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Type=simple
ExecStart=...
Restart=on-failure
RestartSec=10
```
