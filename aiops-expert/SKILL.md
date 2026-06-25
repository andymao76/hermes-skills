---
name: aiops-expert
description: AIOps 智能运维 — 自动巡检/异常检测/根因分析/趋势预判/自动化修复。
category: devops
priority: high
tags: [aiops, monitoring, auto-recovery, incident-response, root-cause-analysis, anomaly-detection, prometheus, grafana, systemd-journal, cron]
related_skills: [incident-runbook-templates, on-call-handoff-patterns, postmortem-writing, monitoring-expert, runbook, webhook-subscriptions]
---

# AIOps Expert — 智能运维专家

AIOps (Artificial Intelligence for IT Operations) — 覆盖智能日志分析、指标异常检测、告警降噪、自动恢复、根因追溯的全链路智能运维体系。

## 核心架构：四层工作模式

```
┌─────────────────────────────────────────────────────┐
│                    学习层 (Learning)                  │
│  记录恢复结果 → 改进检测模型 → 更新已知误报库         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                    行动层 (Action)                    │
│  自动执行预设恢复脚本 → 验证恢复效果 → 输出根因简报   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                    诊断层 (Diagnosis)                 │
│  模式匹配 → 关联规则 → 时序分析 → 定位根因          │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                    感知层 (Perception)                │
│  系统指标采集 → 日志采集 → 告警采集                  │
│  数据源: Prometheus/Datadog/CloudWatch/Grafana       │
│  日志源: systemd journal / 应用日志 / Syslog         │
│  告警源: PagerDuty / OpsGenie / Alertmanager         │
└─────────────────────────────────────────────────────┘
```

---

## 一、感知层 (Perception) — 采集与监控

### 1.1 系统指标采集

#### CPU 指标
```bash
# CPU 使用率（1m/5m/15m 基线偏离检测）
mpstat -P ALL 1 1 | awk 'NR>3 {print $NF}'

# CPU 负载基线对比
load=$(cat /proc/loadavg | awk '{print $1,$2,$3}')
echo "当前负载: $load"
echo "基线负载: 1m<cores*0.7, 5m<cores*0.6, 15m<cores*0.5"

# CPU 上下文切换（异常飙升标志）
vmstat 1 3 | tail -1 | awk '{print $12,$13}'
```

#### 内存指标
```bash
# 内存使用率 — OOM 风险检测
free -m | awk '/Mem:/ {printf "Used: %dMB (%.1f%%), Available: %dMB\n", $3, $3/$2*100, $7}'

# Swap 使用率 — 异常换页检测
swapon --show 2>/dev/null || swapon -s
vmstat 1 3 | awk 'END{printf "Active memory: %dMB\n", $6/1024}'
```

#### 磁盘指标
```bash
# 磁盘使用率 — 阈值警报（>=80% warning, >=90% critical）
df -h | grep -v tmpfs | awk '{if(NR>1 && $5+0>=80) print "WARN: "$NF" "$5; if($5+0>=90) print "CRIT: "$NF" "$5}'

# 磁盘 I/O 等待时间 — IO 瓶颈检测
iostat -x 1 3 | awk '/^[a-z]/ {if($NF>10) print "High IOWAIT: "$1" "$NF"%"}'

# inode 使用率 — inode 耗尽检测
df -i | grep -v tmpfs | awk '{if(NR>1 && $5+0>=80) print "WARN: "$NF" inode "$5}'
```

#### 网络指标
```bash
# 网络吞吐量异常检测
sar -n DEV 1 3 | awk '/Average/ {if($5>1000000 || $6>1000000) print "High traffic: "$2" RX="$5" TX="$6}'

# TCP 连接状态 — TIME_WAIT 风暴检测
ss -s
netstat -tan | awk '{print $6}' | sort | uniq -c | sort -rn

# 丢包率检测
netstat -i | awk '{if(NR>1) print $1": RX-Drop="$4" TX-Drop="$8}'

# DNS 解析耗时
time host example.com 2>&1 | grep real
```

### 1.2 日志采集与分析

#### systemd journal
```bash
# 最近 N 分钟的错误日志
journalctl --since "5 min ago" -p err --no-pager

# 特定 Unit 的异常
journalctl -u <service-name> --since "10 min ago" -p warning --no-pager

# 内核错误（OOM/PCIe/panic）
journalctl -k -p err --since "30 min ago" --no-pager
```

#### 应用日志模式匹配
```bash
# OOM 检测
grep -i "out of memory\|OOM\|killed process\|Exit code 137\|java.lang.OutOfMemoryError" <logfile>

# 连接超时
grep -i "timeout\|Connection refused\|Connection reset\|broken pipe" <logfile>

# 慢查询检测（自定义阈值，如 >5s）
grep -E "duration.*[5-9]\.[0-9]{3}s\|exec.*>[0-9]{3,}ms" <logfile>

# 重试风暴检测（同一错误短时间内反复出现）
awk 'BEGIN{window=300;last=0;count=0}
     /ERROR/{t=systime();if(t-last<window){count++}else{count=1};last=t}
     count>10{print "RETRY_STORM at "strftime("%H:%M:%S",t);count=0}' <logfile>
```

### 1.3 Prometheus/Grafana 集成

```bash
# 直接查询 Prometheus
curl -s "http://localhost:9090/api/v1/query?query=<promql>"

# 常见 PromQL
# CPU 使用率:  100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
# 内存使用率:  (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
# 磁盘预测:   predict_linear(node_filesystem_free_bytes{mountpoint="/"}[6h], 3600 * 24)
# 错误率:     rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Grafana API 告警查询
curl -s "http://admin:${GF_PASSWORD}@localhost:3000/api/alerts"
```

### 1.4 Hermes Cron 定期巡检

配置 Hermes cron job 进行自动巡检：

```yaml
# 示例：每日 8 点巡检全局系统
schedule: "0 8 * * *"
prompt: |
  执行全系统 aiops 巡检：
  1. 检查 CPU/内存/磁盘/网络指标，标记偏离基线的项目
  2. 扫描 systemd journal 最近 30 分钟的 err/warning 级别日志
  3. 检查 5 个关键服务的应用日志
  4. 汇总异常状态，输出巡检报告
  
  如果发现异常项，输出格式：
  【状态】🔴异常/🟡警告/🟢正常
  【指标】<指标名> 当前值 基线值
  【持续时间】<多久>
  【建议操作】<下一步>

skills: ["aiops-expert"]
```

---

## 二、诊断层 (Diagnosis) — 模式匹配与根因定位

### 2.1 异常模式识别矩阵

| 症状 | 可能根因 | 确认方法 | 严重度 |
|------|----------|----------|--------|
| CPU > 90%持续10min | 高并发/死循环/GC风暴 | `top -bn1` 看进程, `jstack` 看线程 | P2 |
| 内存使用率 > 95% | 内存泄漏/OOM | `ps aux --sort=-%mem`, dmesg OOM killer | P1 |
| DISK IOWAIT > 30% | 慢盘/IO 压测/日志暴增 | `iostat -x 1`, `iotop` | P2 |
| DISK 使用率 > 90% | 日志未轮转/数据暴增 | `du -sh /* 2>/dev/null \| sort -rh` | P1 |
| TIME_WAIT > 10000 | 短连接风暴/连接未复用 | `ss -tan state time-wait \| wc -l` | P2 |
| 内核 OOM 事件 | 内存超卖/应用泄漏 | `dmesg \| grep -i oom`, `journalctl -k` | P0 |
| 服务不可达/端口关闭 | 进程崩溃/依赖服务挂 | `systemctl status`, `ss -tlnp` | P0 |
| 错误日志暴增 (5min>100) | 上游异常/配置错误/限流 | `tail -n 1000 \| sort \| uniq -c \| sort -rn` | P1 |
| 文件句柄耗尽 | 连接泄漏 | `lsof -p <PID> \| wc -l`, `cat /proc/<PID>/fd \| wc -l` | P2 |

### 2.2 关联规则引擎

多指标关联推断：

```
规则 1: CPU高 + 内存高 + 磁盘IO低 = 计算密集型任务过载
规则 2: 磁盘IO高 + IOWAIT高 + 响应时间增加 = IO 瓶颈
规则 3: TIME_WAIT高 + CPU中 + 错误增多 = 短连接耗尽端口
规则 4: OOM + Swap高 + Mem低 = 内存泄漏或超卖
规则 5: 错误暴增 + 依赖服务TIME_WAIT高 = 上游服务雪崩
规则 6: 磁盘使用率激增 + 日志错误增多 = 日志风暴导致磁盘满
规则 7: CPU低 + IO低 + 服务不通 = 进程挂死或死锁
规则 8: 网络重传高 + 延迟增加 + 丢包 = 网络链路故障
```

### 2.3 时序基线偏离检测

```bash
# 核心检测函数 — 对比当前值与基线
detect_baseline_deviation() {
    local metric="$1"
    local current="$2"
    local baseline_avg="$3"
    local baseline_std="$4"
    local threshold=2  # 标准差倍数
    
    if (( $(echo "$current > $baseline_avg + $threshold * $baseline_std" | bc -l 2>/dev/null) )); then
        echo "ANOMALY: $metric 当前=$current 基线=$baseline_avg±$baseline_std (超 ${threshold}σ)"
    fi
}
```

### 2.4 服务依赖链追踪

```
故障传递模型: 按依赖关系构建上游→下游影响链

检测到: 服务 B 异常
  ├─ 检查 B 的上游依赖 A: A 正常 → B 自身问题
  └─ 检查 B 的上游依赖 A: A 异常 → 根因是 A
  
外溢检测: 服务 B 异常
  ├─ 影响下游 C: C 也异常 → 级联故障
  └─ 影响下游 D: D 正常 → B 问题范围有限
```

---

## 三、行动层 (Action) — 自动恢复与修复

### 3.1 预设恢复脚本模板

```bash
# 标准恢复流程:
# 1. 停止异常进程/服务
# 2. 清理残留资源
# 3. 重启服务
# 4. 验证恢复
auto_recover() {
    local service="$1"
    local wait_seconds=30
    
    echo "[ACTION] 尝试自动恢复: $service"
    
    # Step 1: 停止服务
    systemctl stop "$service" 2>/dev/null || killall "$service" 2>/dev/null
    sleep 2
    
    # Step 2: 清理（如果需要）
    # journalctl --rotate && journalctl --vacuum-size=500M
    
    # Step 3: 重启
    systemctl start "$service" 2>/dev/null || nohup $SERVICE_BIN >/dev/null 2>&1 &
    
    # Step 4: 等待并验证
    sleep "$wait_seconds"
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "[OK] $service 恢复成功"
        return 0
    fi
    echo "[FAIL] $service 恢复失败，需要人工介入"
    return 1
}
```

### 3.2 常见故障恢复映射

| 故障类型 | 自动恢复脚本 | 触发条件 |
|----------|-------------|----------|
| 进程挂死 | `systemctl restart <svc>; sleep 10; systemctl status` | 端口不通 + CPU/IO 低 |
| OOM/内存泄漏 | `systemctl restart <svc>; journalctl --vacuum-size=200M` | OOM 日志 + 内存 >95% |
| 磁盘满 | `find /var/log -name "*.log" -mtime +7 -delete; journalctl --vacuum-time=3d` | 磁盘 >90% + 日志目录大 |
| TIME_WAIT 耗尽 | `sysctl -w net.ipv4.tcp_tw_reuse=1; sysctl -w net.ipv4.tcp_fin_timeout=15` | TIME_WAIT >20000 |
| 文件句柄耗尽 | `sysctl -w fs.file-max=100000; ulimit -n 65535; systemctl restart <svc>` | `/proc/sys/fs/file-nr` 超限 |
| 服务依赖挂 | `systemctl restart <上游> <下游>` | 级联失败传播 |
| 日志风暴 | `mv /var/log/app/app.log /var/log/app/app.log.rotate; systemctl restart app` | 错误暴增 + 磁盘增速快 |

### 3.3 Hermes Cron 自动修复 Job 配置

```yaml
# 示例：磁盘自动清理 cron job
schedule: "*/30 * * * *"
prompt: |
  使用 aiops-expert 执行磁盘健康检查与自动恢复：
  1. 检查各分区磁盘使用率
  2. 如果 >85%，识别占用最大的日志/临时目录
  3. 执行安全清理（删除 7 天前的日志和临时文件）
  4. 重新检查磁盘使用率
  5. 如果仍 >90%，输出告警要求人工介入
skills: ["aiops-expert"]
```

---

## 四、学习层 (Learning) — 知识沉淀与模型改进

### 4.1 恢复结果记录

每次恢复后记录到 ~/knowledge/aiops/recovery-log/：

```markdown
---
date: 2026-06-12T14:30:00+08:00
incident: DISK_HIGH_/data
severity: P2
---

## 事件简报

### 现象
- /data 分区使用率: 92%
- 主要占用: /data/logs/nginx/access.log (45GB)

### 定位
nginx access.log 未配置 logrotate，连续运行 30 天

### 根因
配置遗漏 — 新部署的 nginx 实例未继承 logrotate 配置

### 恢复操作
1. 执行: `truncate -s 0 /data/logs/nginx/access.log`
2. 配置: logrotate 规则，每天轮转，保留 7 天
3. 验证: 使用率降至 38%

### 预防
- [ ] 在所有 nginx 实例审计 logrotate 配置
- [ ] 添加新服务部署清单项: 确认日志轮转策略
- [ ] 更新监控告警: 磁盘 >75% 时提前告警
```

### 4.2 已知误报库

```yaml
# 误报记录格式
false_positives:
  - pattern: "node_cpu_seconds_total > 90"
    reason: "批量任务触发 CPU 短暂飙升，属于正常行为"
    exception_window: "每次批量任务触发后 5 分钟内"
    added: "2026-06-01"
  
  - pattern: "OOM Killer on java"
    reason: "JVM Xmx 设置为 75% 内存，系统预留不足"
    exception_window: "仅当容器内存 limit 改变时触发"
    added: "2026-05-20"
  
  - pattern: "Connection refused on 3306"
    reason: "MySQL 主从切换时短暂不可达（<30s）"
    exception_window: "主从切换窗口 30s 内"
    added: "2026-04-15"
```

---

## 五、根因简报输出模板

```markdown
【根因简报】<简报编号> — <日期时间>

━━ 现象 —————————————————————————————
<告警内容 / 发现的异常现象>

━━ 定位 —————————————————————————————
<诊断过程 / 使用的命令和输出>

━━ 根因 —————————————————————————————
<根本原因分析>

━━ 恢复 —————————————————————————————
<已执行的恢复步骤>

━━ 预防 —————————————————————————————
<预防措施>
- [ ] <待办事项 1>
- [ ] <待办事项 2>
```

### 简报模板文件

实际输出模板：

```markdown
## 根因简报

【故障等级】P0/P1/P2/P3
【发现时间】2026-06-12T14:30:00+08:00
【持续时间】15 分钟
【影响范围】<受影响的业务/用户>

━━ 现象
- <异常现象 1>
- <异常现象 2>

━━ 定位过程
1. 检查 <指标/日志>: <命令> → <结果>
2. 关联 <其他指标>: <命令> → <结果>
3. 验证 <假设>: <命令> → <结论>

━━ 根因
<一句话根因说明>

━━ 恢复操作
1. `<命令>`
2. `<命令>`
3. 验证: `<命令>` → `<结果>`

━━ 预防措施
1. <短期措施>
2. <长期措施>
```

---

## 六、实战示例

### 示例 1：CPU 异常检测

```bash
# 感知层 — 发现异常
cpu_usage=$(mpstat 1 1 | awk 'END{print 100-$NF}')
echo "CPU: $cpu_usage%"

# 诊断层 — 定位进程
if (( $(echo "$cpu_usage > 90" | bc -l) )); then
    echo "=== CPU top 5 进程 ==="
    ps aux --sort=-%cpu | head -6
    
    echo "=== 线程级分析 ==="
    top -H -b -n 1 -p $(ps aux --sort=-%cpu | awk 'NR==2{print $2}')
    
    echo "=== 系统调用分析 ==="
    strace -c -p $(ps aux --sort=-%cpu | awk 'NR==2{print $2}') 2>&1 &
    sleep 5; kill %1 2>/dev/null
fi

# 行动层 — 恢复
if ps aux | grep -q "[i]dle_loop_check"; then
    echo "发现已知异常进程 idle_loop_check，执行自动恢复"
    kill $(pgrep idle_loop_check)
    echo "CPU 恢复: $(mpstat 1 1 | awk 'END{print 100-$NF}')%"
fi
```

### 示例 2：磁盘满自动恢复

```bash
# 感知层
disk_usage=$(df / | awk 'NR==2{print $5}' | tr -d '%')
growth_rate=$(sar -d 1 3 | awk 'END{print $NF}')

# 诊断层
if [ "$disk_usage" -gt 85 ]; then
    echo "磁盘告警: ${disk_usage}% 增长率: ${growth_rate}块/s"
    
    # 查找占用大户
    big_dirs=$(du -sh /* 2>/dev/null | sort -rh | head -5)
    echo "=== 空间占用 Top5 ==="
    echo "$big_dirs"
    
    # 关联规则匹配
    if echo "$big_dirs" | grep -q "log"; then
        echo "诊断: 日志目录占满"
        # 行动层
        find /var/log -name "*.log.*" -mtime +3 -delete 2>/dev/null
        journalctl --vacuum-time=3d 2>/dev/null
        fresh_usage=$(df / | awk 'NR==2{print $5}' | tr -d '%')
        echo "清理后磁盘: ${fresh_usage}%"
    fi
fi
```

### 示例 3：服务级联故障根因链

```
告警链: 用户报 502 → 网关超时 → API 服务无响应 → MySQL 连接池满

诊断过程:
1. 检查 MySQL: SHOW PROCESSLIST → 大量 Waiting for table metadata lock
2. 检查 DDL: SHOW FULL PROCESSLIST → 发现 DDL 长时间未提交
3. 检查业务: SELECT * FROM information_schema.innodb_trx → 长事务未提交

根因: 凌晨批量任务中的长事务 + DDL 导致 metadata lock 扩散
影响链: 长事务 → 元数据锁 → 连接池满 → API 502 → 网关超时

恢复: KILL 长事务 → DDL 完成 → 连接池恢复 → API 恢复
预防: DDL 执行前检查长事务，设置 lock_wait_timeout
```

---

## 七、已知误报与处理

| 模式 | 误报原因 | 处理方式 |
|------|----------|----------|
| CPU 瞬时飙升 >90% (<30s) | 定时任务触发 | 设置 5 分钟持续阈值 |
| OOM 日志 from JVM | JVM 内存预留不足 | 配置 Xmx 不超过物理 70% |
| MySQL 连接拒绝 | 主从切换 (<30s) | 增加重试机制 |
| 磁盘波动 85-90% | 日志轮转期间 | 设置 15 分钟持续阈值 |
| TIME_WAIT 突增 | 短连接池初始化 | 设置 1 分钟观察窗口 |
| Network RX 突增 | 镜像流量高峰期 | 排除镜像端口 |

---

## 八、巡检输出格式

### 每日巡检报告模板

```markdown
## AIOps 每日巡检报告

日期: 2026-06-12 08:00

### 系统概览
- CPU: 🟢 平均 35.2%（基线 30-60%）
- 内存: 🟢 68.3%（基线 60-80%）
- 磁盘 /: 🟡 82%（基线 <80%）⚠️
- 网络: 🟢 正常

### 服务状态
- nginx: 🟢 运行中
- mysql: 🟢 运行中（主从同步正常）
- redis: 🟢 运行中
- app-api: 🟢 运行中

### 异常日志扫描
- 最近 30min ERR 日志: 0 条
- 最近 30min WARN 日志: 3 条（已知误报，见误报库）

### 风险预警
1. 磁盘 / 使用率 82%，预计 14 天后到达 90%
   → 建议: 计划扩容或清理旧日志

### 自愈操作
- 今日未触发自愈

### 根因简报
- 昨日无新增根因简报
```

### Hermes Cron 巡检 Job 配置参考

```yaml
# 每日 8:00 全量巡检
schedule: "0 8 * * *"
prompt: "执行全系统 AIOps 巡检，输出巡检报告。检查项目: CPU/内存/磁盘/网络指标基线偏离、关键服务状态、应用日志异常扫描、风险趋势预测。发现异常按 aiops-expert 简报模板输出。"
skills: ["aiops-expert"]

# 每 30 分钟快速巡检（重点检查磁盘和关键服务）
schedule: "*/30 * * * *"
prompt: "快速检查: 1) 磁盘使用率是否 >85%  2) 关键服务进程是否存活  3) 是否有新的 OOM 事件。如有异常，执行自动恢复或输出简报。"
skills: ["aiops-expert"]

# 每日 22:00 日志轮转与清理
schedule: "0 22 * * *"
prompt: "执行日志维护: 1) 检查各日志目录大小  2) 执行 journalctl --vacuum-time=7d  3) find /var/log -name '*.log.*' -mtime +7 -delete  4) 确认清理后磁盘使用率恢复。"
skills: ["aiops-expert"]
```

---

## 九、快速参考命令卡片

```bash
# 一键全量巡检
echo "=== CPU ===" && mpstat 1 1 | awk 'END{print 100-$NF"%"}' && \
echo "=== Mem ===" && free -m | awk '/Mem/{printf "%.1f%%\n", $3/$2*100}' && \
echo "=== Disk ===" && df -h | grep "/$" | awk '{print $5}' && \
echo "=== Error Logs ===" && journalctl --since "5 min ago" -p err -q --no-pager | tail -5 && \
echo "=== OOM ===" && dmesg -T 2>/dev/null | grep -i oom | tail -3

# 快速健康检查脚本
health_check() {
    local threshold=${1:-85}
    local issues=0
    check_cmd() { echo "$3"; eval "$1" || { echo "  ✗ $2"; issues=$((issues+1)); }; }
    check_cmd "[ $(free -m | awk '/Mem/{print $3/$2*100}' | cut -d. -f1) -lt 90 ]" "内存 >90%" "  ✓ 内存正常"
    check_cmd "[ $(df / | awk 'NR==2{print $5}' | tr -d '%') -lt $threshold ]" "磁盘 >${threshold}%" "  ✓ 磁盘正常"
    check_cmd "! dmesg -T 2>/dev/null | grep -qi 'oom\|out of memory'" "OOM 事件" "  ✓ 无 OOM"
    check_cmd "systemctl is-active --quiet sshd" "SSH 服务异常" "  ✓ SSH 正常"
    return $issues
}
```
