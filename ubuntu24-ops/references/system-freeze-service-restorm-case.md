# systemd 服务重启风暴导致 Ubuntu 24 整机冻结

## 案例信息

- **日期：** 2026-06-25
- **主机：** rhino01 (Intel UHD620, Intel AC3165 WiFi, Ubuntu 24.04, 
  Kernel 6.17.0-35-generic, GNOME Wayland)
- **症状：** 鼠标键盘无响应 → SSH 无法连接 → 只能强制重启
- **根因：** feishu-hermes 服务目录被删除，systemd `Restart=always` 无限重试

---

## 异常信号数据集

### 1. journald 内存压力（核心信号）

```
6月 25 15:35:45 rhino01 systemd-journald[410]: Under memory pressure, flushing caches.
6月 25 15:35:49 rhino01 systemd-journald[410]: Under memory pressure, flushing caches.
6月 25 15:35:51 rhino01 systemd-journald[410]: Under memory pressure, flushing caches.
6月 25 15:35:58 rhino01 systemd-journald[410]: Under memory pressure, flushing caches.
```

`journalctl -b -1 --no-pager | grep -c "Under memory pressure, flushing caches"` 返回多次。

### 2. libinput 输入滞后

```
6月 25 15:35:46 rhino01 nxpreload.sh[2108]: libinput error: event3 - SEM USB Keyboard:
  client bug: event processing lagging behind by 4791ms, your system is too slow
6月 25 15:35:41 rhino01 nxpreload.sh[2108]: libinput error: client bug: timer event6
  debounce: scheduled expiry is in the past (-46ms)
6月 25 15:35:41 rhino01 nxpreload.sh[2108]: libinput error: WARNING: log rate limit
  exceeded (5 msgs per 3600000ms). Discarding future messages.
```

滞后 4791ms ≈ 5 秒。鼠标键盘操作延迟 5 秒用户感知就是"死机"。

### 3. 服务重启计数器（确凿证据）

```
feishu-hermes.service:      restart counter = 19120  (28小时内)
feishu-hermes-tunnel.service: restart counter = 11970  (28小时内)
合计: ~31,000 次无效重启
```

### 4. 服务配置（根因）

```
[Service]
ExecStart=/usr/bin/node /home/andymao/feishu-hermes/server.js
Restart=always
RestartSec=5
```

- 未设置 `StartLimitIntervalSec` / `StartLimitBurst`
- 可执行文件 `/home/andymao/feishu-hermes/server.js` **不存在**
- 整个 `/home/andymao/feishu-hermes/` 目录已被删除

### 5. 其他并发异常

- Docker 容器健康检查超时
- `copy stream failed: reading from a closed fifo`
- `user@1000.service: Failed with result 'timeout'`

---

## 死机过程还原

```
feishu-hermes 目录被删除/移动
    ↓
systemd: Restart=always, RestartSec=5  （无限制）
    ↓
每 5-8 秒尝试启动 → 失败 → 写日志
    ↓ 重复 31,000 次
journald 被日志洪水填满
    ↓
"Under memory pressure, flushing caches" 反复出现
    ↓
内存压力扩散 → 系统进入 thrashing 状态
    ↓
libinput 输入处理延迟 5 秒
    ↓
鼠标键盘无响应 → SSH 中断
    ↓
用户强制重启
```

## 修复方法

```bash
# 停止失效服务
sudo systemctl stop feishu-hermes.service
sudo systemctl stop feishu-hermes-tunnel.service

# 添加重启限制 override
sudo mkdir -p /etc/systemd/system/feishu-hermes.service.d/
sudo tee /etc/systemd/system/feishu-hermes.service.d/override.conf << 'EOF'
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
EOF

sudo mkdir -p /etc/systemd/system/feishu-hermes-tunnel.service.d/
sudo tee /etc/systemd/system/feishu-hermes-tunnel.service.d/override.conf << 'EOF'
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
EOF

sudo systemctl daemon-reload
# 或直接禁用：sudo systemctl disable --now feishu-hermes.service
```

## 经验教训

1. **`Restart=always` 是无限制重试**，必须搭配 `StartLimitIntervalSec` + `StartLimitBurst`
2. **journald "Under memory pressure" 是日志洪水的红色警报**
3. **libinput 滞后 > 1 秒 = 系统已严重过载**，不是单独的输入问题
4. **服务重启计数器上万不需要等待，直接 kill -9 + disable**
5. 配置 `kernel.hung_task_panic=1` + `kernel.panic=30` 可让系统在类似情况下自动恢复
