---
name: sre-incident-response
description: SRE 故障应急响应 — 服务器宕机/磁盘写满/内存OOM/进程hang/网络中断/容器异常的标准处置流程。
category: devops
priority: high
---

# SRE 故障应急响应

SRE 故障应急响应手册。覆盖 6 大故障场景的标准处置流程：告警确认→影响评估→日志采集→根因定位→应急恢复→复盘记录。

## 通用应急流程

```
告警确认 → 影响评估 → 日志采集 → 根因定位 → 应急恢复 → 复盘记录
   |           |           |           |           |           |
   v           v           v           v           v           v
 确认级别    通知干系人  采集现场    找到原因    止损/恢复   录入知识库
```

### 故障分级

| 级别 | 定义 | 响应时间 | 处理时限 |
|------|------|----------|----------|
| P0 | 核心业务中断/数据丢失 | 即时 | 30分钟 |
| P1 | 部分功能不可用 | 15分钟 | 2小时 |
| P2 | 非关键功能异常 | 1小时 | 8小时 |
| P3 | 咨询/小问题 | 24小时 | 可排期 |

## 场景 1：服务器宕机

### 确认与影响评估
```bash
ping -c 3 <ip>
ssh <ip> "uptime"                     # SSH 是否可达
ipmitool power status                  # IPMI 检查电源状态
ipmitool sel list | tail -20           # 查看系统事件日志
```

### 根因定位
```bash
# 查看最后关机原因
last -x | grep shutdown | tail -5
journalctl -k -b -1 --no-pager | tail -50   # 上一次内核日志

# 硬件诊断（若可远程）
dmesg -T | grep -i -E "error|fail|panic|hung|oops" | tail -30
```

### 恢复操作
```bash
# 强制重启
ipmitool power cycle
# 或
ipmitool power reset

# 系统盘故障时
ipmitool chassis bootdev pxe          # 设为 PXE 启动
```

## 场景 2：磁盘写满

### 诊断
```bash
df -h
du -sh /* 2>/dev/null | sort -rh | head -10   # 根目录大目录
find / -xdev -size +100M -exec ls -lh {} \;   # >100M 大文件
lsof | grep deleted | wc -l                   # 已删除但未释放的文件句柄
```

### 紧急恢复
```bash
# 找到并 kill 持有已删文件句柄的进程
lsof | grep deleted | awk '{print $2}' | sort -u | xargs kill -9

# 清理日志
journalctl --vacuum-size=500M         # 清理 journal 日志到 500M
truncate -s 0 /var/log/syslog         # 清空但不删除文件

# HDP 场景：HDFS 空间检查
hdfs dfsadmin -report | grep -E "Configured|DFS Used|Non DFS"
du -sh /hadoop/hdfs/data/current/     # DataNode 数据目录
```

### 根因与预防
```bash
# 查看磁盘增长趋势
sar -F 1 5
# 设置告警阈值
# /etc/fstab: /dev/sda1 / xfs defaults,usrquota 0 1
```

## 场景 3：内存 OOM

### 确认
```bash
dmesg -T | grep -i "out of memory" | tail -10    # 内核 OOM killer 记录
journalctl -u systemd-oomd --no-pager | tail -20  # systemd oomd
free -h
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree"
```

### 根因定位
```bash
ps aux --sort=-%mem | head -10        # 内存 Top 10 进程
top -b -n 1 -o %MEM | head -20
cat /proc/buddyinfo                    # 内存碎片情况
vmstat 1 5                             # 系统内存状态
```

### 紧急恢复
```bash
# 先杀大内存进程（快速释放）
kill -9 <PID>

# 调整 OOM 优先级（限制某个进程不被优先 kill）
echo -1000 > /proc/<PID>/oom_score_adj

# 调整 vm.overcommit_memory
sysctl -w vm.overcommit_memory=2        # 禁止超卖
sysctl -w vm.overcommit_ratio=80        # 限制 overcommit 比例
```

### 长期修复
```bash
# 增加 swap
fallocate -l 8G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
# /etc/fstab: /swapfile none swap sw 0 0
```

## 场景 4：进程 Hang

### 诊断
```bash
strace -p <PID> -c -S time            # 系统调用耗时统计
strace -p <PID> -e trace=network -f   # 网络调用追踪
cat /proc/<PID>/stack                  # 内核栈（进程在内核态做什么）
gdb -p <PID> -batch -ex "thread apply all bt"  # 全线程堆栈

# Java 进程
jstack <PID> | grep -A 20 "BLOCKED"    # 死锁检测
jcmd <PID> Thread.print
```

### 恢复
```bash
kill -3 <PID>                          # 先打 dump
kill -15 <PID>                         # 优雅终止
kill -9 <PID>                          # 强制 kill（最后手段）
```

## 场景 5：网络中断

### 确认
```bash
ip addr show | grep -E "state|inet"   # 网卡状态
ping -c 3 <gateway>                   # 网关连通性
ping -c 3 8.8.8.8                     # 外网连通性
nslookup baidu.com                    # DNS 解析
```

### 诊断
```bash
ss -lntp                              # 本机监听端口
ip route show                         # 路由表
mtr -r -c 10 <target>                 # 路径追踪
ethtool eth0                          # 网卡参数
ethtool -S eth0 | grep -i error      # 网卡错误计数
```

### 恢复
```bash
systemctl restart networking          # 重启网络服务
ip link set eth0 down && ip link set eth0 up   # 重置网卡
arping -D -I eth0 <ip>               # 检查 IP 冲突
```

## 场景 6：Docker 容器异常

### 诊断
```bash
docker ps -a | grep -v "Up"          # 非运行中容器
docker logs --tail 100 <container>   # 容器日志
docker inspect <container> | jq '.[0].State'  # 容器状态
docker stats <container> --no-stream  # 容器资源占用
```

### 恢复
```bash
docker restart <container>
docker-compose down && docker-compose up -d
# HDP 组件容器
docker exec <container> ambari-agent restart
```

## 复盘记录模板

```markdown
## 故障复盘

### 基本信息
- 故障编号: INC-XXXXX
- 发生时间: YYYY-MM-DD HH:MM
- 持续时间: X 分钟
- 影响范围: [描述]
- 严重级别: P0/P1/P2/P3

### 时间线
| 时间 | 事件 | 操作人 |
|------|------|--------|
| HH:MM | 告警触发 | 系统 |
| HH:MM | 确认影响 | 值班 |
| HH:MM | 开始排查 | 工程师 |
| HH:MM | 定位根因 | 工程师 |
| HH:MM | 实施恢复 | 工程师 |
| HH:MM | 确认恢复 | 值班 |

### 根因
- 直接原因: [是什么直接导致的]
- 根本原因: [为什么会发生]
- 触发条件: [什么条件下触发的]

### 处理措施
1. 紧急恢复: [临时做了什么]
2. 长期修复: [后续要改什么]

### 改进项
- [ ] 监控补充
- [ ] 自动化恢复
- [ ] 文档更新
- [ ] 代码修复
```
