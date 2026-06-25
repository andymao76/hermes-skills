---
name: systemd-service-restart-storm
description: 诊断和修复 systemd 服务无限重启导致的全系统冻结（鼠标/键盘/SSH 无响应）
category: devops
tags: [systemd, freeze, restart-storm, feishu-hermes, journald]
---

# systemd 服务重启风暴诊断与修复

## 适用场景

**表象：** 系统突然完全死机——鼠标死、键盘死、SSH 断连，只能强制重启。

**根因：** systemd 服务配置了 `Restart=always` 但可执行文件已不存在（或被删除/移动），导致无限无效重启，journald 被日志洪水淹没 → 系统 thrashing。

## 检测方法

### 1. 检查 journald 内存压力（核心指标）

```bash
journalctl -b -1 --no-pager | grep "Under memory pressure, flushing caches"
```

如果出现多条，说明 journald 已被日志淹没。

### 2. 检查 libinput 输入延迟

```bash
journalctl -b -1 --no-pager | grep -i "lagging behind"
```

输出示例：
```
libinput error: event3 - SEM USB Keyboard: client bug: event processing lagging behind by 4791ms
```

延迟 > 1000ms 说明系统严重过载。

### 3. 查找重启风暴的服务

```bash
# 统计各服务的重启次数
journalctl -b -1 --no-pager | grep "Scheduled restart job" | sed 's/.*service//' | sort | uniq -c | sort -rn

# 查看具体某个服务的重启计数器
systemctl status <service> --no-pager | grep "restart counter"
```

如果某个服务的重启计数器超过 1000，就是它了。

### 4. 确认服务状态

```bash
systemctl status <service> --no-pager | head -20
# 关注：restart counter 值
# 关注：Failed with result 'resources' / 'exit-code'
```

### 5. 确认可执行文件是否存在

```bash
# 查看服务的 ExecStart 路径
systemctl cat <service> | grep ExecStart
# 检查文件是否存在
file <ExecStart路径>
```

## 修复步骤

### 紧急停止

```bash
sudo systemctl stop <service>
sudo systemctl disable <service>
```

### 添加重启上限（永久预防）

```bash
sudo mkdir -p /etc/systemd/system/<service>.d/
sudo tee /etc/systemd/system/<service>.d/override.conf << 'EOF'
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
EOF
sudo systemctl daemon-reload
```

### 验证修复

```bash
systemctl cat <service>   # 确认 Drop-In 已加载
systemctl status <service> # 确认 inactive (dead) + disabled
```

## 最佳实践：systemd 服务配置安全规范

| 配置项 | ❌ 危险 | ✅ 安全 |
|--------|--------|--------|
| Restart | `Restart=always` 裸用 | `Restart=on-failure` |
| 重启间隔 | 不设 RestartSec | `RestartSec=10` |
| 重启次数限制 | 不设 StartLimitBurst | `StartLimitBurst=3` |
| 检测窗口 | 不设 StartLimitIntervalSec | `StartLimitIntervalSec=600` |

**安全组合：**
```
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
```

## 案例：feishu-hermes 重启风暴（2026-06-25）

| 项 | 值 |
|---|---|
| 服务 | `feishu-hermes.service` / `feishu-hermes-tunnel.service` |
| 原目录 | `/home/andymao/feishu-hermes/` |
| 目录状态 | ❌ 已不存在 |
| 重启策略 | `Restart=always` 无限制 |
| 28小时重试 | 31,195 次（19,120 + 11,970 + 1,294） |
| 关键日志 | `Under memory pressure, flushing caches` |
| 输入延迟 | `lagging behind by 4791ms` |
| 修复 | 禁用服务 + 添加 StartLimitBurst=3 |

## 排查流程速查

```
系统死机（鼠标/键盘/SSH 全卡）
    ↓
上次启动 journalctl -b -1
    ↓
有 "Under memory pressure"?    ───→  服务重启风暴
    ↓ 否                                  ↓
有 AER 错误?                    ───→    WiFi AER 风暴（见 ubuntu24-pcie-aer-iwlwifi-freeze-fix）
    ↓ 否
有 OOM / 内存不足?              ───→    内存 thrashing
    ↓ 否
其他内核问题
```

## 关联

- 知识库: `02_AREAS/ubuntu-ops/ubuntu24-system-freeze-diagnosis.md`
- 技能: `ubuntu24-pcie-aer-iwlwifi-freeze-fix` — AER 风暴排查
- 技能: `hardware-diagnostics` — 系统健康检查
