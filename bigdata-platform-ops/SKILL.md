---
name: bigdata-platform-ops
description: HDP 大数据平台全栈运维 — 集群巡检/健康检查/故障预判。覆盖 HDFS/YARN/Hive/HBase/Kafka/Flink/Ambari/ZooKeeper
category: bigdata
priority: highest
---

# bigdata-platform-ops — 大数据平台运维技能

## 概述

HDP 大数据平台全栈运维技能，覆盖以下场景：
- **集群巡检** — 定期检查各组件运行状态
- **日常健康检查** — 资源使用率、服务存活、关键指标监控
- **故障预判** — 基于趋势提前发现潜在风险

## 覆盖组件

| 组件 | 检查项 | 关键命令 |
|------|--------|----------|
| HDFS | NameNode HA、DataNode 存活、块副本、磁盘使用率 | `hdfs dfsadmin -report`, `hdfs fsck /` |
| YARN | ResourceManager、NodeManager、队列资源 | `yarn node -list`, `yarn application -list` |
| ZooKeeper | 集群 quorum、leader 选举 | `zkServer.sh status` |
| Ambari | 服务状态、告警 | `ambari-server status` |
| Hive | MetaStore、HiveServer2 | `hive --service metastore --status` |
| HBase | RegionServer、Master | `hbase hbck`, `status 'detailed'` |
| Kafka | Broker、Topic、消费者 lag | `kafka-broker-api-versions.sh`, `kafka-consumer-groups.sh` |
| Flink | JobManager、TaskManager、Job 状态 | `flink list`, `flink cancel` |

> **引用文件**: `references/web-search-sources-bdops.md` — 包含第 18 章网络搜索补充内容的原始来源和验证链接

## 集群巡检流程

### 1. Ambari 服务检查

```bash
# 检查 Ambari Server 是否运行
ambari-server status

# 通过 Ambari API 获取集群所有服务状态（需替换 host）
# curl -u admin:admin http://<ambari-host>:8080/api/v1/clusters/<cluster-name>/services
```

**预期输出**: `Ambari server is running`
**异常判定**: 进程不存在 / API 返回 503 / 服务显示 INSTALLED 而非 STARTED

### 2. HDFS 健康检查

```bash
# 整体集群报告 — DN 存活、容量、配置
hdfs dfsadmin -report

# 文件系统完整性 — 损坏块、缺失副本
hdfs fsck / -files -blocks -locations
```

**关键指标**：
- `Live datanodes` = 全部 datanode（失活的触发预警）
- `Missing blocks` = 0（>0 表示数据丢失风险）
- `Under-replicated blocks` = 尽量趋近于 0
- `Disk usage` — 单节点使用率 > 85% 警告，> 92% 紧急

### 3. YARN 资源检查

```bash
# NodeManager 存活状况
yarn node -list

# 正在运行的应用
yarn application -list
```

**关键指标**：
- 节点状态全部为 RUNNING（失活的标记异常）
- vCores / Memory 使用率 < 80% 为正常，> 90% 需要扩容或优化
- 排队应用数（ACCEPTED 状态）持续 > 0 说明资源不足

### 4. ZooKeeper 检查

```bash
# 每个 ZooKeeper 节点执行
zkServer.sh status
```

**预期输出**：一个 leader，其余为 follower
**异常判定**：出现「not running」或 split-brain（多个 leader）

### 5. 磁盘与系统层

```bash
df -h
iostat -x 1 3
free -h
uptime
```

**阈值**：
- 磁盘使用率 > 85% 告警
- 磁盘 iowait > 30% 持续 5min 以上
- 内存可用 < 10%

## 健康评分模型

| 维度 | 满分 | 扣分规则 |
|------|------|----------|
| HDFS 存活 | 25 | 每个失活 DN 扣 5 分；missing blocks 存在扣 10 分 |
| YARN 资源 | 25 | 失活 NM 每个扣 5 分；资源使用率 > 90% 扣 10 分 |
| ZooKeeper | 15 | 任一节点 not running 扣 15 分 |
| 磁盘使用率 | 20 | 单盘 > 85% 扣 5 分；> 92% 扣 10 分 |
| 系统负载 | 15 | load avg > CPU cores 扣 5 分；OOM 风险扣 10 分 |

**评分分级**：
- 90-100：健康 ✅
- 70-89：亚健康 ⚠️ — 需关注
- 50-69：异常 ❌ — 需处理
- < 50：严重 🚨 — 立即介入

## 故障预判规则

1. **HDFS 容量趋势** — 连续 3 次巡检磁盘增长 > 2%/天，预计 1 周内触发 > 85% 阈值
2. **YARN 队列积压** — ACCEPTED 应用数持续增长，需扩容或调整调度策略
3. **ZK 连接数** — ZooKeeper 连接数接近 `maxClientCnxns` 配置值，需扩容
4. **NN 堆内存** — NameNode JVM 堆使用率 > 75%，GC 频率增高，需调整 `-Xmx`

## 巡检报告模板

```
========================================
  大数据平台集群巡检报告
  时间：{datetime}
  集群：{cluster_name}
========================================

【健康评分】{score}/100 — {level}

【HDFS 状态】
  DataNode 存活: {live_dn}/{total_dn}
  Missing blocks: {missing}
  Under-replicated blocks: {under_rep}
  磁盘最高使用率: {max_disk_usage}%

【YARN 状态】
  NodeManager 存活: {live_nm}/{total_nm}
  已用 vCores: {used_vcores}/{total_vcores}
  已用内存: {used_mem}GB/{total_mem}GB
  排队应用: {pending_apps}

【ZooKeeper 状态】
  集群节点: {zk_nodes}
  Leader: {leader_node}
  状态: {zk_status}

【异常节点】
  {list_unhealthy_nodes}

【异常服务】
  {list_unhealthy_services}

【修复建议】
  1. {suggestion_1}
  2. {suggestion_2}
  ...

【本次巡检结论】
  {conclusion}
```

## 常用问题修复

| 问题 | 排查步骤 | 修复命令 |
|------|----------|----------|
| DataNode 失活 | `hdfs dfsadmin -report` 确认 | `systemctl start hadoop-hdfs-datanode` |
| NN 进入安全模式 | `hdfs dfsadmin -safemode get` | `hdfs dfsadmin -safemode leave` |
| YARN NM 失活 | `yarn node -list` | `systemctl start hadoop-yarn-nodemanager` |
| ZK 节点失效 | `zkServer.sh status` | `zkServer.sh start` |
| 磁盘空间不足 | `df -h` | 清理日志 / 扩容 / 迁移 HDFS 数据 |
| HDFS 块丢失 | `hdfs fsck /` | 从备份恢复 / `hdfs fsck -delete` 清理 |

## 注意事项

1. `hdfs fsck /` 扫描全量路径时对大集群耗时较长（数十分钟），建议定时巡检放在低峰期
2. 巡检命令需在集群任意管理节点（安装了客户端）执行
3. Kerberos 环境下需先 `kinit` 获取 ticket
4. 非 root 用户执行 `ambari-server status` 需有 sudo 权限
5. 巡检结果建议归档到文件，便于趋势分析

---

## 十一、Spark 作业调优速查

### 关键参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `spark.executor.memory` | 4GB-32GB | Executor 堆内存 |
| `spark.executor.memoryOverhead` | memory × 0.1-0.2 | 堆外内存，防止 Container killed |
| `spark.sql.shuffle.partitions` | 200-2000 | Shuffle 分区数 |
| `spark.sql.adaptive.enabled` | true | AQE（自适应查询），性能提升 20-30% |
| `spark.sql.autoBroadcastJoinThreshold` | 10MB-100MB | 广播 Join 阈值 |
| `spark.dynamicAllocation.enabled` | true | 动态资源分配 |

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Container Killed | 物理/虚拟内存超限 | 增大 memoryOverhead 或 `yarn.nodemanager.vmem-pmem-ratio` |
| Shuffle 慢 | 分区数不合理 | 启用 AQE 动态合并分区 |
| OOM | Executor 内存不足 | 增大 executor.memory，减少 executor 数 |
| 小文件多 | 输出分区太多 | `spark.sql.adaptive.coalescePartitions.enabled=true` |

---

## 十二、Flink Checkpoint 检查项

### 关键参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `execution.checkpointing.interval` | 60s-300s | Checkpoint 间隔 |
| `execution.checkpointing.mode` | EXACTLY_ONCE | 一致性语义 |
| `execution.checkpointing.timeout` | 10min-30min | 超时时间 |
| `state.checkpoints.num-retained` | 2 | 保留数，设为 2 防止最新 checkpoint 损坏导致恢复失败 |
| `state.backend` | rocksdb | 大状态场景推荐 RocksDB |

### 状态后端选择

| 类型 | 适用场景 | 特点 |
|------|---------|------|
| MemoryStateBackend | 测试/小状态 | 最快，仅限内存 |
| FsStateBackend | 中等状态(<100GB) | HDFS/S3，兼容性好 |
| RocksDBStateBackend | 大状态/长窗口(>100GB) | 磁盘溢写，增量 Checkpoint |

---

## 十三、监控告警体系

### Prometheus 配置（大数据组件）

```yaml
# prometheus.yml 示例
scrape_configs:
  - job_name: 'hadoop'
    static_configs:
      - targets: ['nn1:9001', 'nn2:9001', 'rm:8088']
  - job_name: 'kafka'
    static_configs:
      - targets: ['broker1:7071', 'broker2:7071']
  - job_name: 'hbase'
    static_configs:
      - targets: ['regionserver1:10101', 'regionserver2:10101']
```

### 核心告警规则

| 告警项 | PromQL 表达式 | 阈值 | 处理预案 |
|--------|--------------|------|---------|
| HDFS 容量高 | `hdfs_capacity_used/hdfs_capacity_total*100 > 85` | >85% | 清理旧数据，扩容 DN |
| NN RPC 延迟 | `rate(namenode_rpc_queue_time_ms[5m]) > 200` | >200ms | 增加 handler 线程、优化 GC |
| DataNode 失联 | `time()-hdfs_datanode_last_heartbeat > 120` | 无心跳 120s | 检查网络、重启 DN |
| Kafka 消费 Lag | `kafka_consumer_lag > 10000` | >10000 | 增加消费者、扩容分区 |
| RegionServer 异常 | `hbase_regionserver_num_regions > 200` | >200 | 手动分裂、重新均衡 |

---

## 十四、云原生大数据部署方案

| 方案 | 适用场景 | 优缺点 |
|------|---------|--------|
| Flink Kubernetes Operator | 大规模 Flink 作业调度 | 原生 K8s 集成、自动重启。需 K8s 基础设施 |
| Spark on K8s | Spark 批处理 | 动态资源分配、共享 HDFS。Job History 需单独部署 |
| Volcano 调度器 | 混合负载调度 | Job 内 Task 感知、公平调度。需额外部署 |
| Yunikorn 调度器 | 复杂队列管理 | 云原生队列、多租户隔离。社区较小 |

---

## 十五、AIOps 智能化运维

### 核心能力

| 能力域 | 实现方式 | 业务价值 |
|--------|---------|---------|
| 异常检测 | Prophet/Isolation Forest 时序异常检测 | 提前 5-30 分钟发现异常 |
| 根因分析 | 多维数据关联分析、因果推断 | 减少 MTTR 50%+ |
| 容量预测 | LSTM/ARIMA 时序预测 | 降低 SLA 风险 50%+ |
| 配置推荐 | 强化学习 | 性能提升 10-20% |
| 告警收敛 | 智能降噪与事件聚合 | 告警量减少 80%+ |

### SRE 自治闭环

感知 → 诊断 → 决策 → 执行 → 反馈 的自治闭环。通过自主感知、决策、执行能力的智能体，实现运维全链路自动化。

---

## 十六、面试高频题速查

| 类别 | 问题 | 核心考点 |
|------|------|---------|
| 资源评估 | 如何评估大数据项目资源需求？ | 容量规划：数据量增长率、保留周期、成本逐级评估 |
| 排查实战 | NN JVM 频繁 Full GC 如何处理？ | GC 日志分析、G1GC 调优、检查 FsImage 大小 |
| 性能排查 | Spark Shuffle 严重拖慢性能？ | AQE 动态分区、广播 Join、Kryo 序列化 |
| 高可用 | YARN RM 宕机怎么办？ | ZK-based HA，自动故障转移，定期备份状态 |
| 故障诊断 | 集群常见性能问题有哪些？ | 资源分配、数据倾斜、硬件瓶颈、配置不合理 |

---

## 十七、学习路线规划

| 阶段 | 主题 | 预计时长 |
|------|------|---------|
| 阶段 1 | 基础搭建（Hadoop 部署、基础命令） | 40h |
| 阶段 2 | 组件运维（HDFS/YARN 高可用、Capacity 调度） | 200h |
| 阶段 3 | 计算引擎（Spark/Flink 调优、Checkpoint、K8s 部署） | 180h |
| 阶段 4 | 生态集成（Kafka + HBase 运维） | 220h |
| 阶段 5 | 监控体系（Prometheus+Grafana、ELK、Jaeger） | 80h |
| 阶段 6 | 容器化（K8s + 大数据、Operator、Helm） | 120h |
| 阶段 7 | 自动化/智能化（Ansible/Terraform、AIOps、DataOps） | 140h |
| 阶段 8 | 项目实战（故障演练、性能压测、迁移升级） | 200h |

---

## 十八、生产环境核心经验（网络搜索补充）

### 18.1 故障三态模型与分级响应

| 故障类型 | 示例 | 响应机制 |
|----------|------|---------|
| **瞬时故障**（Transient） | 网络抖动、进程短暂无响应 | `dfs.namenode.avoid.stale.datanode` 自动迁移任务 |
| **间歇故障**（Intermittent） | 磁盘坏道、内存 ECC 错误 | DataNode 自动下线，触发副本补充 |
| **持久故障**（Persistent） | 节点宕机、磁盘完全损坏 | "健康度评分"体系自动隔离（HDD Used >85%且 Block Report Delay > 300s） |

**故障自愈原则（三七法则）：** 70% 异常通过自动化脚本自愈处理，30% 需人工介入。通过动态阈值（EWMA/季节性分解）将误报率从 42% 降到 6%。

### 18.2 参数调优黄金法则（实际生产验证）

| 参数 | 黄金法则 | 来源 |
|------|---------|------|
| `spark.dynamicAllocation.maxExecutors` | 不超过节点数 × 3 | 腾讯云实战 |
| `yarn.nodemanager.resource.memory-mb` | 预留 20% 系统开销（物理内存 × 0.8） | 腾讯云实战 |
| `mapreduce.map.memory.mb` : `mapreduce.reduce.memory.mb` | 建议 1 : 1.5 | 腾讯云实战 |
| `-XX:G1HeapRegionSize` | 4MB（大堆场景） | 金融行业实践 |
| `vm.swappiness` | 10 | 通用推荐 |
| `net.core.somaxconn` | 1024 | 高并发场景 |

### 18.3 四维调优法

| 维度 | 关键优化 | 效果 |
|------|---------|------|
| **计算** | JVM G1HeapRegionSize=4M | GC 停顿减少 58% |
| **存储** | SSD 缓存 EditLog | NameNode 吞吐量提升 3 倍 |
| **网络** | dfs.datanode.balance.bandwidthPerSec + tc-netem QoS | 跨区域迁移速度提升 400% |
| **操作系统** | vm.swappiness=10, deadline 调度器 | MR 任务完成时间缩短 22% |

### 18.4 扩容三段论

1. **预测** — 分析历史数据增长曲线（`hadoop job -history output-dir`）
2. **预检** — 提前调整 `dfs.namenode.handler.count` 等参数（NN 压力预热）
3. **预热** — 设置 `dfs.balance.bandwidthPerSec` 控制数据平衡流量，避免网络风暴

**三大门槛：** 节点镜像黄金标准（定制 AMI）、服务发现无缝衔接（ZK 动态注册）、数据再平衡流量控制。

### 18.5 监控四层立体化

| 层级 | 监控对象 | 典型指标 |
|------|---------|---------|
| L1 基础设施 | CPU / 内存 / 磁盘 | iowait, disk usage, mem avail |
| L2 组件健康 | HDFS / YARN / ZK | Live DN, Active RM, ZK quorum |
| L3 服务指标 | RPC 延迟 / Block 报告 | NN RPC queue, Block Report delay |
| L4 业务感知 | ETL 成功率 / 消费延迟 | Job success rate, Kafka consumer lag |

**Key Insight：** `UnderReplicatedBlocks` 需结合 `hadoop fsck / -files -blocks` 交叉验证；YARN `AvailableMB` 必须与 `spark.executor.memoryOverhead` 联动分析。

### 18.6 智能运维前沿（2025-2026）

- **LSTM 预测磁盘故障**：分析 `BlockReport` 傅里叶变换特征，提前 14 天预警磁盘故障潮
- **知识图谱根因定位**：将配置、指标、告警、日志构建图数据库，根因定位秒级，准确率 92%
- **混沌工程**：模拟 37 种故障场景（ZK 脑裂、NN 元数据损坏、DN 静默丢块），容灾能力提升 3 个 9
- **分层存储**：热数据→云 SSD，温数据→低频存储，冷数据→对象存储，存储成本下降 60%
- **弹性伸缩双循环**：外循环（小时级）基于存储增长趋势扩容，内循环（分钟级）基于 CPU 实时调度



