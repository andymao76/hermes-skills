---
name: yarn-expert
description: YARN 资源管理专家 — Container 诊断/Queue 管理/Scheduler 调优/应用日志分析
priority: normal
category: bigdata
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bigdata, yarn, hadoop, resource-manager, scheduler, queue, container]
    related_skills: [hdfs-ops, flink-ops, kafka-ops]
---

# YARN Expert — YARN 资源管理专家

## 适用场景

YARN 集群出现以下问题时触发：

- **AM Container Exit Code 异常**：Application Master 异常退出，任务反复失败
- **Queue 异常**：队列资源分配异常、用户提交被拒、ACL 权限问题
- **Scheduler 异常**：资源分配不均、Deadlock、公平性失衡
- **资源不足（Insufficient Resources）**：集群资源充足但 job 无法获取资源

## 核心诊断命令速查

```bash
# 查看所有运行中的应用（含状态、队列、资源使用）
yarn application -list

# 查看特定状态的应用
yarn application -list -appStates FAILED,KILLED
yarn application -list -appStates RUNNING,ACCEPTED

# 查看应用详细信息（含诊断信息）
yarn application -status <application_id>

# 查看 NodeManager 状态与资源
yarn node -list -all
yarn node -status <node_id>

# 查看队列状态（资源分配、用户限制、ACL）
yarn queue -status root
yarn queue -status root.<queue_name>

# 查看应用日志（诊断 Container 退出原因）
yarn logs -applicationId <application_id>
yarn logs -applicationId <application_id> -containerId <container_id>

# 查看集群资源使用概览
yarn cluster -status

# RM 管理命令
yarn rmadmin -getServiceState        # 查看 RM HA 状态
yarn rmadmin -refreshQueues          # 刷新队列配置
yarn rmadmin -refreshNodes           # 刷新节点列表（graceful decommission）
yarn rmadmin -transitionToActive ... # 手动切换 RM
yarn rmadmin -transitionToStandby ...
```

---

## 一、AM Container Exit Code 诊断

### 1.1 常见 Exit Code 含义

| Exit Code | 含义 | 典型原因 |
|-----------|------|---------|
| **-1000** | Container 被抢占 | 高优先级队列/应用抢占了该 Container |
| **-100** | 内存不足被 Kill | `yarn.nodemanager.vmem-pmem-ratio` 超限，物理或虚拟内存超过 Container 限制 |
| **-103** | 被 NodeManager 监控 Kill | 物理内存使用超过 `yarn.nodemanager.resource.memory-mb` 限制 |
| **-104** | 虚拟内存超限 | vmem 超过 `yarn.scheduler.maximum-allocation-mb` 比例 |
| **137** / **SIGKILL** | OOM Killer 杀死 | 进程实际内存超过 cgroup limit，被内核 OOM Killer 杀掉 |
| **143** / **SIGTERM** | 正常终止 | 应用自行退出或被 graceful shutdown |
| **1** | 用户代码异常 | Java 进程抛未捕获异常退出，通常是业务代码 bug |
| **50** | 集群节点 Label 不匹配 | Node Label 约束导致 Container 无法分配到匹配节点 |

### 1.2 诊断步骤

```bash
# Step 1: 找到失败的应用
yarn application -list -appStates FAILED 2>/dev/null | grep -i "FAILED"

# Step 2: 查看失败诊断信息
yarn application -status <application_id> | grep -E "Diagnostics|State|Final-State|Queue|User"

# Step 3: 获取 Container 级别的日志
yarn logs -applicationId <application_id> | grep -iE "exit|error|outofmemory|killed" | tail -50

# Step 4: 查看对应 NodeManager 日志（SSH 到该节点）
grep -i "container.*killed\|OutOfMemory\|vmem\|pmem" \
  /opt/hadoop/logs/yarn-hadoop-nodemanager-*.log | tail -100
```

### 1.3 修复策略

| 原因 | 修复方法 |
|------|---------|
| vmem 超限 | 增大 `yarn.nodemanager.vmem-pmem-ratio`（默认 2.1），或调大 Container 内存 |
| pmem 超限 | 增大 Container 内存请求值（`-Xmx`、`spark.executor.memory` 等） |
| OOM Kill | 检查 `dmesg` 确认：`dmesg | grep -i "killed process"`；增大 cgroup limit |
| 抢占导致 | 调整抢占策略：`yarn.scheduler.reservation-policy`，或关闭抢占 |
| 代码异常 | 拉取 stderr 日志定位堆栈：`yarn logs -applicationId <id> -containerId <cid>` |

---

## 二、Queue 异常诊断

### 2.1 队列状态查看

```bash
# 查看根队列及子队列完整状态
yarn queue -status root

# 查看特定子队列
yarn queue -status root.<queue_name>

# 输出字段含义
# - numPendingApplications: 等待中的应用数
# - numActiveApplications: 运行中的应用数
# - absoluteCapacity: 队列绝对容量（占总资源百分比）
# - absoluteUsedCapacity: 已使用容量
# - absoluteMaxCapacity: 最大可用容量
# - userLimits: 各用户在当前队列的限制
# - numContainers: 当前运行的 Container 数
# - reservedContainers: 预留 Container 数
```

### 2.2 常见队列异常

| 现象 | 可能原因 | 排查命令 |
|------|---------|---------|
| 任务提交被拒绝（AccessControlException） | ACL 配置限制 | `yarn queue -status root.<queue>` 检查 ACL 字段 |
| 队列中排队应用数持续增长 | 队列容量不足 / 资源被大应用占据 | `yarn queue -status root` 对比 `usedCapacity` 与 `capacity` |
| 用户任务无法提交到指定队列 | 用户不在队列 ACL 中 | 检查 `yarn.scheduler.capacity.root.<queue>.acl_submit_applications` |
| 队列资源使用率异常低 | 节点 Label 不匹配 / 调度器配置错误 | `yarn node -list -all` 检查节点 Label 映射 |

### 2.3 容量调度器配置检查

```bash
# 检查 capacity-scheduler.xml 中的关键配置
grep -E "capacity|maximum-capacity|user-limit-factor|ordering-policy|acl" \
  /opt/hadoop/etc/hadoop/capacity-scheduler.xml | head -60

# 关键参数
# yarn.scheduler.capacity.root.<queue>.capacity           — 队列保证容量 (%)
# yarn.scheduler.capacity.root.<queue>.maximum-capacity    — 队列最大容量 (%)
# yarn.scheduler.capacity.root.<queue>.user-limit-factor   — 用户资源上限倍数
# yarn.scheduler.capacity.root.<queue>.ordering-policy     — 排序策略 (fifo/fair)
# yarn.scheduler.capacity.root.<queue>.acl_submit_applications — 提交 ACL
# yarn.scheduler.capacity.root.<queue>.state               — 队列状态 (RUNNING/STOPPED/PAUSED)
```

### 2.4 队列问题快速复位

```bash
# 1. 刷新队列配置（无需重启 RM）
yarn rmadmin -refreshQueues

# 2. 检查刷新是否生效
yarn queue -status root | grep -E "State|Capacity"

# 3. 紧急情况下停用队列（排空后恢复）
#    将 queue state 设为 STOPPED，等待已在运行的任务完成
#    手动迁移应用到其他队列：不支持直接迁移，需 kill 后重提
```

---

## 三、Scheduler 异常诊断

### 3.1 调度器类型识别

```bash
# 查看当前使用的调度器
yarn cluster -status | grep "Resource Manager"

# 或从 Web UI 确认
#    容量调度器 (CapacityScheduler) — 默认，企业常用
#    公平调度器 (FairScheduler) — 多租户公平共享
#    比例调度器 (DominantResourceCalculator) — 多维资源公平
```

### 3.2 常见调度异常

| 现象 | 可能原因 |
|------|---------|
| 应用一直处于 `ACCEPTED` 状态不调度 | 资源碎片化 / 调度器 Deadlock / Node Label 不满足 |
| 某些队列即使有空闲资源也不分配 | `maximum-capacity` 限制 / `user-limit-factor` 限制 |
| 资源分配倾斜（某些节点满载、某些空闲） | 节点 Label 策略 / 调度器本地性偏向 |
| 调度延迟高（`schedulingMillis` 持续上升） | `scheduler.maximum-allocation-mb` 配置过大 / 心跳频率低 |
| 应用提交后 RM 无响应 | RM 堆外内存泄漏 / GC 压力大 / ZK 会话超时 |

### 3.3 调度器诊断命令

```bash
# 1. RM Web UI Scheduler 页面（REST API 方式）
curl -s "http://<rm-host>:8088/ws/v1/cluster/scheduler" | python -m json.tool

# 2. 查看调度器核心指标
#    从 JSON 输出中关注：
#    - `schedulerInfo.type` — 调度器类型
#    - `schedulerInfo.queueName` — 队列名
#    - `schedulerInfo.capacity` / `maxCapacity`
#    - `schedulerInfo.queues.queue` — 子队列详情

# 3. 查看 RM 日志中的调度器状态
grep -i "scheduler\|allocation\|preemption" \
  /opt/hadoop/logs/yarn-hadoop-resourcemanager-*.log | tail -200 | head -100

# 4. 查看调度器 Metrics
curl -s "http://<rm-host>:8088/ws/v1/cluster/metrics" | python -m json.tool
#    关注：appsSubmitted, appsRunning, appsPending, 
#           reservedMB, availableMB, allocatedMB, pendingMB
```

### 3.4 调度器调优参数

```yaml
# capacity-scheduler.xml 调优建议

# 1. 队列最小容量保证（百分比）
yarn.scheduler.capacity.root.<queue>.capacity: 20

# 2. 队列弹性上限（可借用其他队列资源）
yarn.scheduler.capacity.root.<queue>.maximum-capacity: 60

# 3. 用户资源限制倍率（防止单个用户独占队列）
yarn.scheduler.capacity.root.<queue>.user-limit-factor: 2

# 4. 排序策略（控制队列内任务分配）
#    fifo — 先入先出（不推荐）
#    fair — 公平共享（推荐多租户）
yarn.scheduler.capacity.root.<queue>.ordering-policy: fair

# 5. 抢占超时（秒）
yarn.resourcemanager.scheduler.monitor.enable: true
yarn.resourcemanager.scheduler.monitor.policies: 
  org.apache.hadoop.yarn.server.resourcemanager.monitor.capacity.ProportionalCapacityPreemptionPolicy
yarn.resourcemanager.monitor.capacity.preemption.observe_only: false
yarn.resourcemanager.monitor.capacity.preemption.max_ignored_over_capacity: 10
yarn.resourcemanager.monitor.capacity.preemption.monitoring_interval: 3000
```

---

## 四、资源不足（Insufficient Resources）诊断

### 4.1 典型场景

```bash
# 现象：应用提交后一直显示 ACCEPTED，分配不到 Container
# RM UI 或 -status 可以看到类似：
# "Application is being scheduled by the scheduler, 
#  but there is no available resource to allocate"
```

### 4.2 诊断流程

```bash
# Step 1: 查看集群总资源
yarn cluster -status | grep -E "Total Memory|Total VCores|Total Nodes"

# Step 2: 查看各节点资源使用
yarn node -list -all | grep -E "RUNNING|INITIALIZING|DECOMMISSIONED"
yarn node -list -all 2>/dev/null | awk -F'[:,\t ]+' '
  /Node-Id/ {next}
  /RUNNING/ {
    mem_avail=$(NF-5); vcore_avail=$(NF-3)
    printf "%-30s  mem_avail=%-5d  vcore_avail=%-3d\n", $1, mem_avail, vcore_avail
  }'

# Step 3: 查看每个队列的资源分配
yarn queue -status root | grep -E "Capacity|Absolute|Used|Available|Pending"

# Step 4: 确认是否存在预留资源
yarn queue -status root | grep -i "reserved"
```

### 4.3 资源不足的三大原因

#### 4.3.1 显式资源不足

集群总资源（`yarn.nodemanager.resource.memory-mb` × 节点数）确实不够。

**修复：**
```bash
# 临时方案：降低单个 Container 内存请求
# Spark: --executor-memory 4g → 2g
# MR: -Dmapreduce.map.memory.mb=2048

# 扩容节点或增加单节点资源
yarn.nodemanager.resource.memory-mb: 32768  # 从 16G 提升到 32G
yarn.nodemanager.resource.cpu-vcores: 16    # 从 8 core 提升到 16 core
```

#### 4.3.2 资源碎片化

总体资源充足但单 Container 需求无法被任何一个节点满足（类似内存碎片）。

**识别：**
```bash
# 查看各节点剩余资源是否能满足待调度 Container 需求
yarn node -list -all 2>/dev/null | awk '
  /RUNNING/ {
    # 解析内存/VCore 可用量
    for(i=1;i<=NF;i++) {
      if($i ~ /[0-9]+MB/) mem_avail=substr($i,1,length($i)-2);
      if($i ~ /vCores/) vcore_avail=$(i-1);
    }
    printf "%-30s mem_avail=%-5d MB  vcore_avail=%-3d\n", $1, mem_avail, vcore_avail
  }'
```

**修复：**
```bash
# 调低 Container 最大尺寸允许更灵活的分配
yarn.scheduler.maximum-allocation-mb: 8192   # 默认值过大时调小
yarn.scheduler.minimum-allocation-mb: 512    # 调大最小值减少碎片
yarn.scheduler.increment-allocation-mb: 512  # 分配粒度
```

#### 4.3.3 队列/用户资源限制

集群总资源充足，但目标队列或用户已达到上限。

**识别：**
```bash
# 查看队列资源限制
yarn queue -status root.<queue> | grep -E "UsedCapacity|AbsoluteUsed|UserLimit"

# 当满足以下条件时说明是队列限制问题：
# 1. 集群总 alloc MB < total MB
# 2. 目标队列 absoluteUsedCapacity == absoluteMaxCapacity 或 capacity
# 3. 其他队列有闲置可借用资源
```

**修复：**
```bash
# 方案一：动态调整队列容量（临时）
# 修改 capacity-scheduler.xml 中对应队列的 capacity/maximum-capacity
yarn rmadmin -refreshQueues

# 方案二：借用其他队列空闲资源
# 设置 maximum-capacity 大于 capacity，允许弹性借用
yarn.scheduler.capacity.root.<queue>.maximum-capacity: 80

# 方案三：增大 user-limit-factor 允许单个用户使用更多资源
yarn.scheduler.capacity.root.<queue>.user-limit-factor: 4
```

---

## 五、综合故障排查流程

### 5.1 用户报 "任务跑不起来" — 标准排查路线

```
1. yarn application -list -appStates FAILED,RUNNING,ACCEPTED
   ├── 没有该用户的应用 → 检查提交脚本和队列 ACL
   └── 有 ACCEPTED 但不跑 → 走第 2 步

2. yarn queue -status root.<queue>
   ├── 队列 full / pendingApp > 0 → 资源不足，扩容或调小任务
   └── 队列有空闲 → 走第 3 步

3. yarn node -list -all
   ├── 所有节点 RUNNING → 检查碎片化（见 4.3.2）
   └── 部分节点不在线 → 检查 NodeManager 健康

4. yarn application -status <app_id>
   ├── Diagnostics 有错误信息 → 按 Exit Code 排查
   └── 正常但慢 → 检查调度器配置和抢占策略
```

### 5.2 RM 健康检查

```bash
# RM HA 状态
yarn rmadmin -getServiceState

# RM JVM 健康
jstat -gcutil <rm_pid> 1000 5    # GC 状态
jmap -heap <rm_pid>               # 堆使用
top -p <rm_pid>                   # CPU / 内存

# ZK 会话（HA 模式）
zkCli.sh -server <zk_host>:2181 get /yarn-leader-election/<cluster_id>/ActiveStandbyElectorLock
```

### 5.3 快照采集（故障升级用）

```bash
# 收集故障快照信息，供 DBA/平台团队分析
{
  echo "=== CLUSTER STATUS ==="
  yarn cluster -status

  echo "=== NODE LIST ==="
  yarn node -list -all

  echo "=== QUEUE STATUS ==="
  yarn queue -status root

  echo "=== FAILED APPLICATIONS ==="
  yarn application -list -appStates FAILED 2>/dev/null | head -20

  echo "=== RUNNING/ACCEPTED APPS ==="
  yarn application -list -appStates RUNNING,ACCEPTED 2>/dev/null | head -50
} | tee /tmp/yarn-snapshot-$(date +%Y%m%d-%H%M%S).log
```

---

## 六、配置模板与最佳实践

### 6.1 生产环境推荐配置

```xml
<!-- capacity-scheduler.xml 关键配置 -->
<property>
  <name>yarn.scheduler.capacity.maximum-applications</name>
  <value>10000</value>
</property>
<property>
  <name>yarn.scheduler.capacity.maximum-am-resource-percent</name>
  <value>0.1</value>
  <description>AM 占用资源上限，默认 10%，大集群可降至 5%</description>
</property>
<property>
  <name>yarn.scheduler.capacity.node-locality-delay</name>
  <value>40</value>
  <description>节点本地性延迟，避免跳过本机调度机会</description>
</property>
<property>
  <name>yarn.scheduler.capacity.queue-mappings</name>
  <value>u:user1:root.engineering</value>
</property>
```

### 6.2 资源比例参考

| 集群规模 | 单节点内存 | 单节点 vCore | 总内存 | 队列数量 |
|---------|-----------|-------------|-------|---------|
| 小型 | 32G | 8 | 512G | 3~5 |
| 中型 | 64G | 16 | 4T | 5~10 |
| 大型 | 128G | 32 | 32T+ | 10~20 |

---

## Pitfalls

- **`yarn queue -status` 不要在 RM HA 切换期间执行**：可能返回旧主节点数据
- **`yarn rmadmin -refreshQueues` 可能失败**：如果更改了队列层次结构（新增/删除队列），需要重启 RM 才能生效；仅修改容量参数时 refresh 可用
- **虚拟内存超限退出的误判**：`ExitCode -100` 不一定是真的 OOM，先检查 `yarn.nodemanager.vmem-pmem-ratio`（默认 2.1），调大到 4~10 可解决大部分误杀
- **NodeManager 心跳间隔影响调度延迟**：`yarn.nodemanager.heartbeat.interval-ms` 默认 1000ms，业务有实时性要求时可调至 500ms
- **抢占策略需谨慎**：`observe_only: true` 只观察不抢占，先观察再开启；生产环境建议从 `max_ignored_over_capacity: 20` 开始逐步调低
- **资源碎片化排查**：不要只看集群总已分配内存，一定要用 `yarn node -list` 逐个节点看剩余资源是否能满足单个 Container 请求
- **日志收集需要配置**：`yarn.log-aggregation-enable` 必须为 true（默认 true），且 `yarn.nodemanager.log-dirs` 有足够磁盘空间
- **`yarn logs -applicationId` 失败**：确认应用已 finished，正在运行的应用日志不会聚合
