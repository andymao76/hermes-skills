---
name: flink-sre-expert
description: Flink 流计算 SRE — Job 监控/Checkpoint 诊断/背压分析/内存调优/HDP YARN 模式排障。
category: devops
priority: high
---

# Flink SRE 专家

Flink 流计算作业的 SRE 运维。覆盖 HDP 3.1 YARN 模式 / Kubernetes 模式的全链路运维场景。

## 一、标准检查命令

```bash
# Job 列表
flink list -r                         # 运行中 Job
flink list -s                         # 已完成 Job
flink list                            # 所有 Job

# YARN 应用检查
yarn application -list | grep -i flink
yarn application -status <app_id>

# 获取 Job 详情
flink info <job_id>

# Flink on Kubernetes
kubectl get pods -n <namespace> | grep flink
kubectl logs -n <namespace> -l app=flink --tail=50
kubectl exec -n <namespace> <pod> -- flink list -r

# 资源使用概览
curl -s http://<jm>:8081/jobs/overview | jq .
curl -s http://<jm>:8081/taskmanagers | jq '.taskmanagers[] | {id, slotsNumber, freeSlots, dataPort}'
```

## 二、Checkpoint 配置参数详解

### 核心参数说明

```yaml
# === checkpointing 基础 ===
checkpointing.interval: 60000           # 单位 ms，两次 checkpoint 之间的间隔
                                        # 经验值：正常处理延迟的 2~5 倍
                                        # 太短 → 频繁触发，I/O 压力大
                                        # 太长 → 故障恢复损失大

checkpointing.mode: EXACTLY_ONCE        # EXACTLY_ONCE | AT_LEAST_ONCE
                                        # EXACTLY_ONCE：严格要求所有算子到达 barrier 后才提交
                                        # AT_LEAST_ONCE：更快但可能重复处理
                                        # 推荐：绝大多数场景用 EXACTLY_ONCE

checkpointing.timeout: 600000           # 单位 ms，checkpoint 从触发到完成的最大等待时间
                                        # 超触发起 → 取消本次 checkpoint 并标记失败
                                        # 环境值：10min（跟作业状态大小成正比）
                                        # 排查依据：日志中 "Checkpoint expired" 事件

checkpointing.min-pause: 30000          # 单位 ms，两次 checkpoint 之间最短等待时间
                                        # 防止连续触发导致系统过载
                                        # 建议配置 >= interval / 3

checkpointing.max-concurrent: 1         # 最大并发 checkpoint 数
                                        # 生产环境通常保持 1，不再增并行

checkpointing.checkpoints-after-tasks-finish: false
                                        # 所有 task 结束后是否继续触发 checkpoint
```

### 状态保留与清理

```yaml
# === 保留与清理 ===
state.checkpoints.num-retained: 10           # 保留最近 N 个 completed checkpoint
                                             # 配合 savepoint 做长期保留
                                             # 旧 checkpoint 自动删除

state.checkpoints.max-retained: 20           # RETAINED 模式下的最大保留数（含 failed）
                                             # 超量后删除最早的

checkpointing.unaligned: false               # 非对齐 checkpoint（Flink 1.11+）
                                             # 大状态/背压严重 → true
                                             # 减少对齐延迟，但增加 I/O

# 实际保留策略：
# cleanup = false → 取消 job 时保留 checkpoint 目录，用于恢复
# cleanup = true  → 取消 job 时自动删除
```

### 对齐方式选择

| 模式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| Aligned (对齐) | 小状态、低背压 | 精确一次语义严格 | 背压时对齐时间长 |
| Unaligned (非对齐) | 大状态、高背压 | 避免 barrier 对齐等待 | 写入体积增大 ~30% |
| Hybrid (混合) | 一般生产环境 | 自动选择最优 | Flink 1.15+ 支持 |

### 诊断命令

```bash
# 查看 checkpoint 统计
curl -s http://<jm>:8081/jobs/<job_id>/checkpoints | jq .
# 注意 recent failed、history 中的持续时间

# 失败原因排查
grep -i "checkpoint" /var/log/flink/*.log | grep -i "fail\|expired\|declined" | tail -30

# 手动触发一次性 checkpoint
curl -X POST http://<jm>:8081/jobs/<job_id>/checkpoints

# 列出所有已完成的 checkpoint
curl -s http://<jm>:8081/jobs/<job_id>/checkpoints | jq '.histories[] | select(.status=="COMPLETED") | {id, triggered_timestamp, duration, state_size}'
```

**失败根因对照表：**

| 错误 | 根因 | 修复 |
|------|------|------|
| Checkpoint expired | 对齐时间超长 | 增大 `checkpoint.timeout` 或开启 unaligned |
| Checkpoint declined by Task | TM OOM 或网络抖动 | 检查 TM 日志，增大 TM 内存 |
| Not all required tasks finished | Source/Sink 卡住 | 检查外部系统（Kafka/HBase/ES） |
| Size exceeds max | State 体积过大 | `state.checkpoints.max-retained` 减小或优化 state |
| File not found | 持久化存储目录问题 | 检查 HDFS/K8s PVC 状态 |
| Serialization error | 自定义状态类型未注册 | 注册 TypeSerializer / 使用 POJO |

## 三、状态后端选择指南

| 维度 | MemoryStateBackend | FsStateBackend | RocksDBStateBackend |
|------|-------------------|----------------|---------------------|
| 存储位置 | TM Heap（JVM 堆内） | TM 本地临时文件 → 持久化到文件系统 | TM 本地 RocksDB（LSM-Tree）→ 持久化到文件系统 |
| 状态上限 | 受 JVM 堆大小限制，通常 < 几百 MB | 受磁盘容量限制 | 受本地磁盘限制，可支撑 TB 级 |
| 异步快照 | 支持（默认开启） | 支持（默认开启） | 支持（增量 checkpoint 可选） |
| 增量 checkpoint | 不支持 | 不支持 | 支持（Flink 1.11+） |
| GC 影响 | 高（Full GC 频繁） | 中等 | 低（RocksDB 在堆外管理内存） |
| 读取性能 | 最快（直接从堆内读取） | 快 | 中等（序列化/反序列化开销） |
| 写入性能 | 快 | 快 | 中等（LSM 写入放大） |
| 推荐场景 | 开发测试、小状态 demo | 中等状态 < 50 GB | 大状态 > 10 GB、All-at-Least-Once 生产作业 |

### 配置示例

```yaml
# MemoryStateBackend（仅开发用）
state.backend: memory
state.backend.memory.write-buffer-size: 5mb

# FsStateBackend（中等状态）
state.backend: filesystem
state.backend.fs.checkpointdir: hdfs:///flink/checkpoints

# RocksDBStateBackend（生产推荐）
state.backend: rocksdb
state.backend.incremental: true
state.backend.rocksdb.localdir: /data/flink/rocksdb   # TM 本地 RocksDB 目录
state.checkpoints.dir: hdfs:///flink/checkpoints
```

**选型建议：**
- **开发/小状态 (< 1 GB)**：MemoryStateBackend 快速验证
- **中状态 (1 ~ 50 GB)**：FsStateBackend 平衡性能与稳定性
- **大状态 (> 50 GB)**：RocksDBStateBackend + 增量 checkpoint
- **有容灾需求**：必须配置 `state.checkpoints.dir` 为 HDFS/S3/GCS
- **有精确一次保证需求**：必须使用 RocksDB + 增量 checkpoint

## 四、RocksDB 调优参数

```yaml
# === 内存控制 ===
state.backend.rocksdb.memory.managed: true           # 受 Flink managed memory 控制（推荐）
                                                      # true → 自动在所有 column family 间分配
                                                      # false → 手动配置 block cache

state.backend.rocksdb.memory.write-buffer-ratio: 0.5 # write buffer 占 managed memory 比例
                                                      # 大状态写频繁 → 增大此比例
state.backend.rocksdb.memory.high-prio-pool-ratio: 0.1 # index/filter block 高优保留比例

# === 写相关 ===
state.backend.rocksdb.writebuffer.size: 64mb         # 每个 memtable 大小
                                                      # 增大减少 flush 频率
state.backend.rocksdb.writebuffer.count: 2            # memtable 数量（含冻结中）
                                                      # 增大提高写吞吐

# === 读相关 ===
state.backend.rocksdb.block.cache-size: 256mb         # block cache 大小
                                                      # 读密集型作业增大此值
state.backend.rocksdb.block.blocksize: 4kb            # SST 文件块大小
                                                      # 小值 → 随机读好；大值 → 顺序读好

# === 压缩与 IO ===
state.backend.rocksdb.compaction.style: LEVEL         # LEVEL | UNIVERSAL | FIFO
                                                      # LEVEL → 最常用的逐层压缩
                                                      # UNIVERSAL → 写放大低，适合写密集
                                                      # FIFO → TTL 过期删除，适合时间窗口

state.backend.rocksdb.thread.num: 4                   # 后台 flush/compaction 线程数
                                                      # 推荐 = 机器物理核数 / 2

# === 性能调优建议 ===
# 1. 监控 disk I/O: iostat -x 1，观察 await / %util
# 2. write-stall 指标: "Stalls" 出现说明写入跟不上
#    解决：增大 writebuffer 或 count
# 3. compaction 慢：增大 thread.num、换 SSD
# 4. block cache miss 率高：增大 block.cache-size
```

### RocksDB 监控指标

```bash
# Flink Web UI → TaskManager → Metrics → RocksDB 相关指标
# 核心指标：
# - rocksdb.block.cache.hit
# - rocksdb.block.cache.miss
# - rocksdb.write.stall
# - rocksdb.compaction.pending
# - rocksdb.mem.table.compaction

# 通过 REST API 获取
curl -s http://<jm>:8081/taskmanagers/<tm_id>/metrics | grep rocksdb | jq .
```

## 五、Savepoint 管理

### 触发与恢复

```bash
# === 触发 Savepoint ===
# 手动触发（默认方式：asynchronous）
flink savepoint <job_id> [hdfs:///flink/savepoints]

# 带触发 ID，方便追踪
flink savepoint <job_id> hdfs:///flink/savepoints -jobId <job_id>

# 停止 Job 并自动触发 Savepoint（推荐）
flink stop --savepointPath hdfs:///flink/savepoints <job_id>

# === 从 Savepoint 恢复 ===
flink run -s hdfs:///flink/savepoints/savepoint-xxxxx -c MainClass app.jar

# 从 Savepoint 恢复 + 修改并行度
flink run -s hdfs:///flink/savepoints/savepoint-xxxxx -p 8 \
  -c MainClass app.jar

# === Savepoint 管理 ===
# 列出 savepoints 目录
hdfs dfs -ls hdfs:///flink/savepoints/

# 删除指定 savepoint
flink savepoint -d hdfs:///flink/savepoints/savepoint-xxxxx

# 查看 savepoint 元数据
flink savepoint -s hdfs:///flink/savepoints/savepoint-xxxxx
```

### 恢复时跳过不兼容的状态

```bash
# 场景：代码修改后部分算子 ID/状态结构变更
# 恢复时自动跳过错配的算子，保留兼容的部分

# 全局跳过（不推荐）
flink run -s hdfs:///flink/savepoints/savepoint-xxxxx \
  --allowNonRestoredState \
  -c MainClass app.jar

# 精确控制：在代码中通过 UID 维精确匹配
DataStream<String> stream = env
  .addSource(kafkaConsumer)
  .uid("kafka-source")             # 显式设置 UID
  .keyBy(...)
  .uid("keyed-process")
  .process(...)
  .uid("sink-process");

# 验证 savepoint 兼容性（不恢复，只检查）
flink run -s hdfs:///flink/savepoints/savepoint-xxxxx \
  --savepointRestoreMode NO_RESTORE \
  -c MainClass app.jar
```

### Savepoint 最佳实践

```
1. 升级作业前必须手动触发 Savepoint
2. Savepoint 路径命名规范：savepoint-<job_name>-<YYYYMMDD-HHmmss>
3. Savepoint 是冷备份，Checkpoint 是热备份
4. 大状态 Savepoint 耗时可能 30min+，请在低峰期执行
5. 定期清理老旧 Savepoint（保留最近 5 个即可）
6. 修改作业拓扑结构后恢复，使用 --allowNonRestoredState 需谨慎
```

## 六、Flink on Kubernetes 部署配置

### 资源配置

```yaml
# flink-config.yaml — K8s 部署专用配置

# === 资源声明 ===
kubernetes.cluster-id: flink-streaming-job
kubernetes.namespace: flink-prod
kubernetes.container.image: registry.company.com/flink:1.16.2

jobmanager.memory.process.size: 2048m
taskmanager.memory.process.size: 8192m
taskmanager.memory.managed.size: 4096m       # RocksDB 托管内存

jobmanager.cpu.cores: 1.0
taskmanager.cpu.cores: 2.0

# === K8s 集群配置 ===
kubernetes.jobmanager.replicas: 1             # JobManager 高可用建议 2+
kubernetes.rest-service.exposed.type: LoadBalancer
kubernetes.taskmanager.replicas: -1           # yarn-application 模式自动匹配 slot

# === 文件系统（推荐用 S3/GCS，避免 HDFS 复杂的网络穿透）===
state.backend: rocksdb
state.backend.incremental: true
state.checkpoints.dir: s3a://flink-bucket/checkpoints
state.savepoints.dir: s3a://flink-bucket/savepoints
high-availability.storageDir: s3a://flink-bucket/ha/
high-availability.type: kubernetes

s3.access-key: *****                          # 使用 K8s Secret 管理
s3.secret-key: *****
s3.endpoint: https://s3.cn-north-1.amazonaws.com.cn
s3.path.style.access: true                    # 兼容 MinIO / Ceph

# === 高可用 ===
high-availability: kubernetes                 # K8s 原生 HA
# 或 ZK / HDFS
# high-availability: zookeeper
# high-availability.zookeeper.quorum: zk1:2181,zk2:2181,zk3:2181
```

### 核心调度命令

```bash
# === 部署 Flink 作业到 K8s ===
# application 模式（推荐生产）
kubectl apply -f flink-operator-job.yaml

# session 模式提交
kubectl exec -n flink-prod <jm-pod> -- flink run \
  -p 8 \
  -c com.company.MainClass \
  /opt/flink/apps/streaming-job.jar

# === K8s 运维 ===
kubectl get pods -n flink-prod -w
kubectl describe pod <pod-name> -n flink-prod
kubectl logs -n flink-prod <pod-name> --tail=100

# 查看 pod 资源使用
kubectl top pod -n flink-prod

# 修改并行度后重建
kubectl delete pod <jm-pod> -n flink-prod

# 资源不够时查看事件
kubectl get events -n flink-prod --sort-by='.lastTimestamp'
```

### K8s 常见问题

```
1. ImagePullBackOff → 检查镜像地址、registry 认证、拉取策略
2. CrashLoopBackOff → 查看日志: kubectl logs <pod> --previous
3. OOMKilled → taskslot 分配过多或 managed memory 不足
4. Pending → 资源不足，增加 node 或调整 request/limit
5. NodeAffinity 调度失败 → nodeSelector / taints 配置冲突
6. PVC 挂载失败 → 检查 storageClass / PV 状态
```

## 七、背压分析增强

```bash
# === 基础背压 ===
curl -s http://<jm>:8081/jobs/<job_id> | jq '.vertices[] | {name, backpressureStatus}'
# OK → 正常 | LOW → 轻微 | HIGH → 严重

# === 高级背压诊断（Flink 1.13+）===
curl -s http://<jm>:8081/jobs/<job_id>/vertices/<vertex_id>/backpressure | jq .
# 输出包含每个 subtask 的：
# - backpressureLevel: OK / LOW / HIGH
# - backpressureRatio: 0.0 ~ 1.0 （背压时间比例）

# === 逐 subtask 详细背压 ===
curl -s http://<jm>:8081/jobs/<job_id>/vertices/<vertex_id>/subtasks/backpressure | jq .

# === 端到端延迟监控 ===
curl -s http://<jm>:8081/jobs/<job_id>/metrics?get=latencyTracker_gauge_CurrentLatency | jq .

# === 判断瓶颈方向 ===
# Source 出现 HIGH 背压 → 下游算子处理慢，需优化算子或加资源
# Sink 出现 HIGH 背压 → 外部系统写入慢（Kafka / HBase / ES）
# 中间算子 HIGH → 业务逻辑 cpu 密集 / state 操作慢 / 网络 shuffle 瓶颈
```

### 背压处理决策树

```
观察 Web UI 背压颜色：
  ├─ Source 红色（HIGH）
  │   └─ 非 Source 问题，是下游瓶颈传导到 Source
  │       └─ 定位第一个出现 HIGH 的算子（瓶颈点）
  │
  ├─ 中间算子红色（HIGH）
  │   ├─ CPU 密集 → 增加并行度、优化逻辑、使用异步 I/O
  │   ├─ State 操作慢 → RocksDB 调优、增大 managed memory
  │   └─ 网络 shuffle → 检查 taskmanager.network.memory、启用 针对键的网络缓冲区
  │
  └─ Sink 红色（HIGH）
      ├─ Kafka 写入慢 → batch.size 调大、linger.ms 增加
      ├─ HBase 写入慢 → 检查 RegionServer 负载、增大 hbase.client.write.buffer
      └─ ES 写入慢 → 使用 bulk processor、调整 refresh_interval
```

### 背压数据收集脚本

```python
#!/usr/bin/env python3
"""背压实时采集脚本 — 可集成到告警系统"""

import requests, json, sys, time

JM_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081"

def get_backpressure(job_id, vertex_id):
    url = f"{JM_URL}/jobs/{job_id}/vertices/{vertex_id}/backpressure"
    r = requests.get(url)
    return r.json()

def get_jobs():
    r = requests.get(f"{JM_URL}/jobs/overview")
    return [j for j in r.json()['jobs'] if j['state'] == 'RUNNING']

while True:
    for job in get_jobs():
        jid = job['jid']
        verts = requests.get(f"{JM_URL}/jobs/{jid}").json()['vertices']
        for v in verts:
            bp = get_backpressure(jid, v['id'])
            bp_ratio = bp.get('backpressureRatio', 0)
            if bp_ratio > 0.8:
                print(f"ALERT: job={job['name']} vertex={v['name']} ratio={bp_ratio:.2f}")
    time.sleep(30)
```

## 八、大状态恢复优化

### 恢复流程与瓶颈分析

```
Savepoint / Checkpoint → 恢复过程：
  Step 1: 读取元数据，校验状态兼容性
  Step 2: 分布式读取状态文件
  Step 3: 在每个 TM 上反序列化状态
  Step 4: 开始处理数据

瓶颈通常在 Step 2（网络 I/O）和 Step 3（RocksDB 加载）
```

### 恢复优化参数

```yaml
# === 恢复并行度 ===
# 恢复时使用更大的并行度（前提：state key 分布均匀）
# 通过 rescaling 并行读取，加快速度
cluster.evenly-spread-out-slots: true

# === RocksDB 恢复优化 ===
state.backend.rocksdb.predefined-options: FLASH_SSD_OPTIMIZED  # SSD 环境预调优
  # SPINNING_DISK_OPTIMIZED → HDD
  # FLASH_SSD_OPTIMIZED   → SSD（推荐）
  # DEFAULT               → 默认

# === 恢复时跳过对齐 ===
# 从 savepoint 恢复时直接快照读取，不经过对齐检查
execution.savepoint-restore-mode: CLAIM    # Flink 1.18+
  # CLAIM → 直接接管，不等待
  # NONE  → 不恢复
  # LEGACY → 老版本兼容
```

### 大状态恢复分步检查清单

```
[ ] 1. 确认状态大小
    curl -s <jm>:8081/jobs/<job_id>/checkpoints | jq '.latest.completed.stateSize'

[ ] 2. 确认网络带宽足够
    状态 100 GB / 网络 1 Gbps → 理论至少 800s
    考虑增大 taskmanager.network.memory 或启用压缩

[ ] 3. 确认本地磁盘充足（RocksDB）
    预留 2x 状态大小的磁盘空间
    检查 df -h /data/flink/rocksdb

[ ] 4. 调大 TM 堆内内存
    taskmanager.memory.process.size × 1.5 倍
    因为反序列化 stage 需要额外内存

[ ] 5. 增加恢复超时
    taskmanager.registration.timeout: 300s
    jobmanager.execution.time: 1800000     # 30min 恢复大状态

[ ] 6. 使用增量恢复
    如果支持，只恢复完整状态的差异部分
    需要增量 checkpoint 提前开启

[ ] 7. 首选恢复方式：先恢复到测试环境验证
    flink run -s <savepoint_path> -c MainClass app.jar --mode testing
```

### 恢复失败排查

```bash
# 恢复失败常见原因
# 1. 状态不兼容 → 代码变更后算子 UID 变化 / 状态类型变化
#    解决：添加 --allowNonRestoredState（谨慎使用）
#
# 2. TM 内存不足 → 恢复时 Java heap / off-heap 溢出
#    解决：增大 taskmanager.memory.process.size + taskmanager.memory.managed.size
#
# 3. RocksDB 加载慢 → compaction 成为瓶颈
#    解决：增大 state.backend.rocksdb.thread.num，
#          或使用 state.backend.rocksdb.predefined-options: FLASH_SSD_OPTIMIZED
#
# 4. 文件系统限流 → S3/HDFS 带宽不足
#    解决：检查对象存储的请求限流(Throttling)，
#          考虑使用 fs.s3a.connection.maximum: 1000

# 关键恢复日志定位
grep -i "restoring\|rescaled\|checkpoint\|savepoint" /var/log/flink/*.log \
  | grep -i "total size\|from url\|loaded in\|took" | tail -20
```

## 九、核心调优参数汇总

```yaml
# === 内存配置 ===
jobmanager.memory.process.size: 2048m       # JM 总进程内存
taskmanager.memory.process.size: 8192m      # TM 总进程内存
taskmanager.memory.managed.size: 4096m      # 托管内存（RocksDB + 排序缓冲）
taskmanager.memory.framework.heap: 256m     # 框架堆内存
taskmanager.memory.task.heap: 2048m         # 任务堆内存

# === 并发配置 ===
parallelism.default: 8
taskmanager.numberOfTaskSlots: 4            # 每个 TM 的 slot 数
                                            # parallelism / slots ≈ TM 数量

# === Checkpoint ===
state.backend: rocksdb
state.checkpoints.dir: hdfs:///flink/checkpoints
state.backend.incremental: true
checkpointing.interval: 60000
checkpointing.timeout: 600000
checkpointing.min-pause: 30000
checkpointing.unaligned: false              # 大状态背压时启用

# === 网络 ===
taskmanager.network.memory.min: 512mb
taskmanager.network.memory.max: 1024mb
taskmanager.network.request-backoff.max: 10000

# === 容错 ===
restart-strategy: fixed-delay
restart-strategy.fixed-delay.attempts: 3
restart-strategy.fixed-delay.delay: 10s

# === 文件系统 ===
state.checkpoints.dir: hdfs:///flink/checkpoints
state.savepoints.dir: hdfs:///flink/savepoints
high-availability.storageDir: hdfs:///flink/ha/
high-availability: zookeeper
high-availability.zookeeper.quorum: zk1:2181,zk2:2181,zk3:2181
```

## 十、Savepoint 综合管理

```bash
# === 作业升级流程（零数据丢失）===
# Step 1: 触发 Savepoint
flink stop --savepointPath hdfs:///flink/savepoints <job_id>

# Step 2: 确认 Savepoint 完成
hdfs dfs -ls hdfs:///flink/savepoints/savepoint-latest

# Step 3: 部署新版作业，从 Savepoint 恢复
flink run -s hdfs:///flink/savepoints/savepoint-latest \
  -c MainClass app-new.jar

# Step 4: 观察新作业状态
flink list -r | grep <job_name>
curl -s http://<jm>:8081/jobs/<new_job_id>/checkpoints | jq '.counts'

# === 跨版本升级注意 ===
# Flink 小版本升级（1.14 → 1.15）：Savepoint 兼容
# Flink 大版本升级（1.x → 2.x）：Savepoint 不兼容，推荐重新启动作业
# 状态类型变更：确保 TypeSerializer 兼容
# 算子拓扑变更：UID-based mapping 保持一致
```

---

## 十、Flink 内存池详解（生产调优核心）

### 10.1 TaskManager 五大内存池

Flink 内存配置是生产环境最常见故障源。TaskManager 内存分为 5 个池：

| 内存池 | 用途 | 配置项 | 默认占比 |
|--------|------|--------|---------|
| **Framework Heap** | Flink 框架自身开销 | `taskmanager.memory.framework.heap.size` | 可手动设，通常 128-256MB |
| **Task Heap** | 算子状态（HashMapStateBackend） | `taskmanager.memory.task.heap.size` | 总堆剩余部分 |
| **Managed Memory** | RocksDB 状态 / 排序缓冲 | `taskmanager.memory.managed.size` | 堆外，默认 total - network - framework 后剩余 |
| **Network** | Shuffle/数据交换缓冲区 | `taskmanager.memory.network.min/max` | total × 0.1 |
| **Framework Off-Heap** | Flink 框架堆外内存（Metaspace 等） | `taskmanager.memory.framework.off-heap.size` | 通常不调 |

### 10.2 调优原则

```yaml
# 大状态 RocksDB 场景：
taskmanager.memory.process.size: 8192m     # 总进程内存 8G
taskmanager.memory.network.min: 640mb       # 网络缓冲（总 × 0.1）
taskmanager.memory.network.max: 1024mb
taskmanager.memory.managed.size: 4096m      # Managed Memory 给 RocksDB 用
# Task Heap = 8G - Framework(256m) - Network(640m) - Managed(4096m) ≈ 3G

# 小状态低延迟场景（HashMapStateBackend）：
taskmanager.memory.managed.fraction: 0.2     # Managed Memory 只占 20%
# 更多内存留给 Task Heap → 算子处理更快
```

**常见错误：** `taskmanager.memory.process.size` 设了但没配 `managed.size`，导致 JVM 堆过小从而 OOM。建议手动配 managed fraction 或 size。

### 10.3 Barrier 机制原理

Flink 的故障恢复基于 **分布式快照**（Chandy-Lamport 算法）。核心是 barrier 机制：

1. **Barrier 注入**：JobManager 控制，Source 算子周期性向数据流中注入 checkpoint barrier
2. **Barrier 对齐**（EXACTLY_ONCE）：
   - 算子收到某个通道的 barrier 后，将后续数据缓存到 input buffer
   - 等待所有输入通道的 barrier 到齐
   - 所有 barrier 到齐后进行状态快照
   - 快照完成后释放缓存数据
3. **Barrier 传递**：快照完成后，barrier 继续向下游传递
4. **恢复**：从最近成功 checkpoint 的 barrier 位置重置 Source 偏移量

```yaml
# 非对齐 Checkpoint（Unaligned Checkpoints）
# 适用于数据倾斜或网络延迟大的场景，不等待 barrier 对齐
execution.checkpointing.alignment-timeout: 0   # 0 = 强制非对齐
# 取消对齐时间上限 = 一旦超过该毫秒数，自动切换为非对齐模式
```

### 10.4 Checkpoint 与 Savepoint 对比

| 维度 | Checkpoint | Savepoint |
|------|-----------|-----------|
| 触发方式 | Flink 自动 | 人工手动 |
| 生命周期 | Flink 管理，自动清理 | 持久保留，手动删除 |
| 目的 | 故障恢复 | 版本升级/迁移/回滚 |
| 格式 | 优化速度，不可跨版本 | 可移植，跨版本兼容 |
| 状态兼容性 | 严格—同一 Job | 可兼容小范围变更 |
| 典型场景 | 日常容错 | 升级、A/B测试、迁移 |

---

## 十一、生产环境关键监控指标

```bash
# 最重要的两个指标
# 1. Consumer Lag（Source 端消费延迟）
# 2. Checkpoint Duration（Checkpoint 耗时）

# 通过 REST API 获取
curl -s http://<jm>:8081/jobs/<job_id>/checkpoints | jq '.mostRecentCompleted'
# recentCompleted.duration 应 < checkpoint.interval × 0.5

# 查看 TaskManager 状态
curl -s http://<jm>:8081/taskmanagers | jq '.taskmanagers[] | {id, dataPort, slotsNumber, freeSlots}'

# Metric Reporters 配置
# flink-conf.yaml
metrics.reporters: prom
metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporter
metrics.reporter.prom.port: 9250
```

