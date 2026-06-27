# 系统冻结预防加固措施

在修复了重启风暴或 AER 风暴之后，添加以下内核和系统级加固，防止未来再发生冻结时无法自动恢复。

## 1. 内核 panic 自动重启

```bash
# /etc/sysctl.d/99-panic.conf
kernel.softlockup_panic=1    # 软锁死 120 秒后 panic
kernel.hung_task_panic=1     # D 状态进程堆积超时后 panic
kernel.panic=30              # panic 后 30 秒自动重启
kernel.sysrq=1               # 启用 Magic SysRq（全部功能）
```

```bash
sudo tee /etc/sysctl.d/99-panic.conf << 'EOF'
kernel.softlockup_panic=1
kernel.hung_task_panic=1
kernel.panic=30
kernel.sysrq=1
EOF
sudo sysctl -p /etc/sysctl.d/99-panic.conf
```

> **注意：** 默认 `kernel.panic=0` 意味着内核 panic 后不自动重启，会一直死在那里直到手动断电。`panic=30` 改为 30 秒自动重启。

## 2. 增加 swap 空间

```bash
# 新增 8G swap（已有 4G，合计 12G）
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 3. Magic SysRq 硬重启（死机时手动救命）

启用后（`sysrq=1`），即使系统完全冻结，仍可通过键盘组合键硬重启：

```
Alt + SysRq + R  — 切换键盘为原始模式
Alt + SysRq + E  — 发送 SIGTERM 到所有进程
Alt + SysRq + I  — 发送 SIGKILL 到所有进程
Alt + SysRq + S  — 同步文件系统
Alt + SysRq + U  — 重新挂载为只读
Alt + SysRq + B  — 重启

记忆口诀: REISUB (BUSIER 倒过来)
```

## 4. 内存压力监控

```bash
# /usr/local/bin/mem-watchdog.sh
#!/bin/bash
MEM_PCT=$(free | awk '/Mem/{printf "%d", $3/$2 * 100}')
SWAP_PCT=$(free | awk '/Swap/{if($2>0) printf "%d", $3/$2 * 100; else print "0"}')
if [ "$MEM_PCT" -gt 90 ] || [ "$SWAP_PCT" -gt 80 ]; then
  logger -p daemon.warning "MEMORY WARNING: ${MEM_PCT}% RAM used, ${SWAP_PCT}% swap used"
  ps aux --sort=-%mem | head -5 | logger -p daemon.warning
fi
```

每 10 分钟执行：
```bash
echo '*/10 * * * * /usr/local/bin/mem-watchdog.sh' | crontab -
```

## 5. 验证加固生效

```bash
# 内核参数
sysctl kernel.softlockup_panic kernel.hung_task_panic kernel.panic kernel.sysrq

# swap
swapon --show
free -h | grep Swap

# 监控脚本
grep "MEMORY WARNING" /var/log/syslog
```

## 关联

- 知识库: `02_AREAS/ubuntu-ops/ubuntu24-system-freeze-diagnosis.md`
- 技能: `systemd-service-restart-storm`
- 技能: `ubuntu24-pcie-aer-iwlwifi-freeze-fix`
