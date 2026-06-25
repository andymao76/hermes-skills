# 每周系统健康检查 (Cron + Boot Catchup)

> 适用于 `hardware-diagnostics` skill 的自动化调度参考

## 架构

双重保障机制：定时 cron + 开机补检 systemd service。

```
触发方式:
  1. Cron: 每周五 23:00 → 强制运行
  2. Systemd: 每次开机 → 检测是否 > 6 天未运行 → 补检
```

## 文件清单

| 文件 | 位置 | 用途 |
|------|------|------|
| 检查脚本 | `~/.hermes/scripts/health-check.sh` | 核心逻辑 |
| Cron 包装 | `~/.hermes/scripts/weekly-health-check.sh` | 传入 `force` 参数 |
| Systemd 服务 | `~/.config/systemd/user/hermes-healthcheck.service` | 开机触发 |

## 检查脚本结构

7 大类检查 + 日志老化：

| 类别 | 命令/来源 | 检查项 |
|------|----------|--------|
| 系统健康 | `lscpu`, `free`, `df`, `uptime`, `ps` | CPU/内存/SWAP/磁盘/运行时间/僵尸 |
| 磁盘 SMART | `sudo smartctl -H /dev/sd*` | 重分配扇区、待处理扇区、温度 |
| 传感器 | `sensors`, `/sys/class/thermal/` | CPU Package/Core、NVMe、PCH、WiFi |
| 内核错误 | `sudo dmesg --since "7 days ago"` | IO 错误、坏块、媒体错误 |
| Hermes 服务 | `systemctl --user is-active` | gateway + bridge 状态 |
| 网络连通 | `nc -z`, `ping` | 代理 :7897、外网 8.8.8.8 |
| 日志清理 | `find -mtime +60 -delete` | 60 天老化 |

## Cron 配置

```bash
# cron job: 每周五 23:00 强制运行
cronjob action=create \
  name="每周系统健康检查" \
  schedule="0 23 * * 5" \
  script="weekly-health-check.sh" \
  no_agent=true \
  deliver=local
```

## Systemd 开机补检

`~/.config/systemd/user/hermes-healthcheck.service`:

```ini
[Unit]
Description=Hermes Health Check (weekly, on-boot catchup)
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash /home/andymao/.hermes/scripts/health-check.sh boot
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

启用: `systemctl --user enable hermes-healthcheck.service`

## 补检逻辑

脚本维护时间戳文件 `/mnt/backup/hermes-backup/.last-health-check`。
每次运行后更新。如果距离上次运行 > 6 天，且本次为非 force 触发（即开机自检），则自动执行补检。

```bash
# 核心判断
DIFF_DAYS=$(( (NOW_EPOCH - LAST_EPOCH) / 86400 ))
if [ "$DIFF_DAYS" -gt 6 ]; then
    NEED_CHECK=true
fi
```

## 日志管理

- 位置: `/mnt/backup/hermes-backup/logs/YYYYMMDD_HHMMSS-healthcheck.log`
- 老化: 60 天自动清理（`find -mtime +60 -delete`）
- 双输出: 文件 + systemd journal (`journalctl --user -t hermes-backup`)
