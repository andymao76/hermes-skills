# 案例：feishu-hermes 服务重启风暴（31,195 次）

## 时间线

- **2026-06-24 12:17** — Boot -2 开始，3.5 小时后用户重启
- **2026-06-24 12:17 → 2026-06-25 15:36** — Boot -1 运行 27 小时，死机
- **2026-06-25 15:36** — 用户强制重启，Boot 0 开始

## 根因

`/home/andymao/feishu-hermes/` 整个目录已被删除/迁移，但 systemd 保持：

```ini
Restart=always
RestartSec=5     # feishu-hermes.service
RestartSec=8     # feishu-hermes-tunnel.service
RestartSec=5     # feishu-hermes.service 当前启动
```

未设置 `StartLimitIntervalSec` 和 `StartLimitBurst`，systemd 无限重试。

## 统计数据

| 服务 | 重启计数器 | 时间段 |
|------|-----------|--------|
| feishu-hermes.service | 19,120 次 | Boot -1 (27h) |
| feishu-hermes-tunnel.service | 11,970 次 | Boot -1 (27h) |
| feishu-hermes.service | 1,294 次 | Boot 0 (前2h) |
| **合计** | **31,195 次** | |

## 关键日志（Boot -1 最后时刻）

```
15:35:41  libinput: timer event6 debounce: scheduled expiry in past (-107ms)
15:35:45  systemd-journald: Under memory pressure, flushing caches
15:35:46  libinput: SEM USB Keyboard lagging behind by 4791ms
15:35:48  Docker health check timed out
15:35:51  feishu-hermes: 重启计数器 19119
15:35:53  systemd-journald: Under memory pressure, flushing caches
15:35:59  feishu-hermes: 重启计数器 19120
```

## 死机过程还原

```
feishu-hermes 目录已删除 → systemd 每5~8秒尝试重启
    ↓ 重复 31,000 次
journald 被日志洪水淹没
    ↓
"Under memory pressure, flushing caches" 反复出现
systemd 自身资源耗尽 → feishu-hermes 报 "Failed with result 'resources'"
    ↓
libinput 输入事件延迟从 46ms → 107ms → 4,791ms
    ↓
鼠标 → 键盘 → SSH 依次无响应
    ↓
只能强制重启
```

## 修复

```bash
# 1. 停止并禁用
systemctl stop feishu-hermes.service feishu-hermes-tunnel.service
systemctl disable feishu-hermes.service feishu-hermes-tunnel.service

# 2. 添加重启上限（即使被误启用也不会风暴）
mkdir -p /etc/systemd/system/feishu-hermes.service.d/
cat > /etc/systemd/system/feishu-hermes.service.d/override.conf << 'EOF'
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
EOF

mkdir -p /etc/systemd/system/feishu-hermes-tunnel.service.d/
cat > /etc/systemd/system/feishu-hermes-tunnel.service.d/override.conf << 'EOF'
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
EOF

systemctl daemon-reload
```

## 教训

- `Restart=always` 裸用 = 隐患。必须配 `StartLimitBurst`。
- 服务文件被删除后必须 `systemctl disable` 停掉，否则在后台无限重试。
- journald 的 `"Under memory pressure"` 是比 dmesg 更早的预警信号——它会先于任何 OOM 或 panic 出现。
- feishu-hermes 已废弃，飞书通信改用官方 API（lark_oapi SDK）。
