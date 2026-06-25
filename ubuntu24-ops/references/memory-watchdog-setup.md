# 内存压力监控脚本（mem-watchdog）

## 用途

每 10 分钟检测系统内存和 swap 使用率，超过阈值时写入系统日志，以便事后排查死机原因。

## 脚本内容

安装位置：`/usr/local/bin/mem-watchdog.sh`

```bash
#!/bin/bash
MEM_PCT=$(free | awk '/Mem/{printf "%d", $3/$2 * 100}')
SWAP_PCT=$(free | awk '/Swap/{if($2>0) printf "%d", $3/$2 * 100; else print "0"}')
if [ "$MEM_PCT" -gt 90 ] || [ "$SWAP_PCT" -gt 80 ]; then
  logger -p daemon.warning "MEMORY WARNING: ${MEM_PCT}% RAM used, ${SWAP_PCT}% swap used"
  ps aux --sort=-%mem | head -5 | logger -p daemon.warning
fi
```

## 安装

```bash
sudo cp mem-watchdog.sh /usr/local/bin/mem-watchdog.sh
sudo chmod +x /usr/local/bin/mem-watchdog.sh

# 每 10 分钟执行
(crontab -l 2>/dev/null | grep -v 'mem-watchdog'; echo '*/10 * * * * /usr/local/bin/mem-watchdog.sh') | crontab -
```

## 验证

```bash
crontab -l | grep mem-watchdog
# 输出: */10 * * * * /usr/local/bin/mem-watchdog.sh

# 手动触发（不会写入 crontab）
sudo /usr/local/bin/mem-watchdog.sh

# 查看是否有告警记录
grep "MEMORY WARNING" /var/log/syslog
```

## 查看历史告警

```bash
grep "MEMORY WARNING" /var/log/syslog
# 无输出 = 从未触发（内存从未超过阈值）
# 有输出 = 某时刻内存或 swap 超过了 90%/80%
```

## 联动

配合 `kernel.hung_task_panic=1` + `kernel.panic=30`，即使内存耗尽导致死锁，系统也能在 2 分钟内自动重启。
