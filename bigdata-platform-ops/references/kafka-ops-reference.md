---
name: kafka-ops-expert
description: Kafka 集群运维专家 — Topic 管理/ISR 诊断/Consumer 堆积排查/Broker 故障恢复/性能调优/数据倾斜/分区重分配/JMX监控。
category: devops
priority: high
---

# Kafka 集群运维专家

Kafka 集群的日常运维、故障排查和性能调优。覆盖 HDP 3.1 环境中 Kafka 的全链路运维场景，涵盖参数配置、数据倾斜处理、消费者组管理、分区重分配、故障恢复增强及监控集成。

## 标准检查命令

```bash
# 主题检查
kafka-topics.sh --describe --zookeeper <zk>:2181
kafka-topics.sh --list --zookeeper <zk>:2181

# 消费者组积压
kafka-consumer-groups.sh --all-groups --bootstrap-server <broker>:9092 --describe

# 集群健康
kafka-broker-api-versions.sh --bootstrap-server <broker>:9092

# 日志段查看
kafka-log-dirs.sh --describe --bootstrap-server <broker>:9092

# 生产/消费测试
kafka-producer-perf-test.sh --topic test --num-records 100 --record-size 1024
kafka-consumer-perf-test.sh --topic test --messages 100
```

## 一、核心运维参数配置表（server.properties）

| 分类 | 参数 | 推荐值 | 说明 |
|------|------|--------|------|
| 基础 | broker.id | 唯一整数 | 每个 Broker 唯一标识，从 0 开始递增 |
| 基础 | listeners | PLAINTEXT://0.0.0.0:9092 | 监听地址和端口 |
| 基础 | advertised.listeners | PLAINTEXT://<host>:9092 | 对外暴露地址，需与客户端网络可达 |
| 基础 | zookeeper.connect | <zk1>:2181,<zk2>:2181 | ZK 连接串，多节点逗号分隔 |
| 线程 | num.network.threads | 8 | 网络线程数，建议 CPU 核数×2 |
| 线程 | num.io.threads | 8 | IO 线程数，建议 CPU 核数×2 |
| 线程 | num.replica.fetchers | 2 | 副本拉取线程数，大集群可调高到 4-8 |
| 网络 | socket.send.buffer.bytes | 1024000 | 发送缓冲区(约1MB) |
| 网络 | socket.receive.buffer.bytes | 1024000 | 接收缓冲区(约1MB) |
| 网络 | socket.request.max.bytes | 104857600 | 最大请求大小(100MB) |
| 日志 | log.dirs | /data1/kafka,/data2/kafka | 数据目录，多盘逗号分隔提升 IO |
| 日志 | log.segment.bytes | 1073741824 | 日志段大小(1GB)，过小增加文件数，过大延迟回收 |
| 日志 | log.retention.hours | 168 | 日志保留时间(7天) |
| 日志 | log.retention.bytes | -1 | 按容量保留(-1为不限)，可配合 retention.hours 双限 |
| 日志 | log.retention.check.interval.ms | 300000 | 日志清理检查间隔(5分钟) |
| 日志 | log.cleaner.enable | true | 启用日志清理器，支持 compact 策略 |
| 分区 | num.partitions | 3 | 默认分区数，建议根据吞吐量调大 |
| 分区 | auto.create.topics.enable | false | 生产环境建议关闭，防止自动创建主题 |
| 副本 | default.replication.factor | 2 | 默认副本因子，生产环境至少 2，建议 3 |
| 副本 | replica.lag.time.max.ms | 30000 | ISR 超时(30s)，抖动环境可调至 60000 |
| 副本 | replica.fetch.max.bytes | 1048576 | 副本拉取最大字节(1MB) |
| 副本 | replica.fetch.wait.max.ms | 500 | 副本拉取最大等待(500ms) |
| 副本 | min.insync.replicas | 2 | 最小同步副本数，配合 acks=all 保证写入可靠 |
| 控制器 | unclean.leader.election.enable | false | 不允许非 ISR 副本选为 Leader，保一致性 |
| 控制器 | leader.imbalance.check.interval.seconds | 300 | Leader 平衡检查间隔(5分钟) |
| 压缩 | compression.type | producer | 由 Producer 决定压缩方式 |
| 压缩 | log.cleaner.min.cleanable.ratio | 0.5 | 清理最小可清理比例 |
| 压缩 | log.cleaner.threads | 2 | 清理线程数 |
| 删除 | delete.topic.enable | true | 允许删除主题 |

## 二、数据倾斜处理方案

数据倾斜指部分分区数据量远超其他分区，导致少数 Broker 负载过高、消费端处理瓶颈。

### 2.1 分区增加（扩容缓解倾斜）

```bash
# 为倾斜主题增加分区，将数据分散到更多分区
kafka-topics.sh --bootstrap-server <broker>:9092 \
  --alter --topic <topic_name> --partitions <new_count>

# 验证分区分布
kafka-topics.sh --bootstrap-server <broker>:9092 \
  --describe --topic <topic_name>
```

**注意：**
- Kafka 对已有 key 的消息会根据 key 决定分区，增加分区后**旧的 key-to-partition 映射不变**
- 新分区只影响后续消息，无法使已有数据重新分布
- 增加分区后需同步增加 Consumer 实例以利用新增分区
- 建议新增分区数为偶数，且是原分区数的整数倍

### 2.2 分区键优化（从源头解决）

```yaml
# 生产端策略
# 1. 避免使用单一或高基数不均匀的 key
# 不良示例：key = 用户ID（大客户产生海量消息）→ 单分区倾斜
# 改进方案：key = 用户ID % N + 分桶后缀

# 2. 自定义分区器（Custom Partitioner）
# 实现 org.apache.kafka.clients.producer.Partitioner 接口
public class AntiSkewPartitioner implements Partitioner {
    public int partition(String topic, Object key, byte[] keyBytes,
                         Object value, byte[] valueBytes, Cluster cluster) {
        List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
        int numPartitions = partitions.size();
        // 对 key 加盐后取模，分散热点 key
        String saltedKey = key + "_" + (System.currentTimeMillis() % 100);
        return Math.abs(saltedKey.hashCode()) % numPartitions;
    }
}

# 3. Producer 配置使用自定义分区器
# props.put("partitioner.class", "com.example.AntiSkewPartitioner");

# 4. 不使用 key：轮询（round-robin）天然均匀
# props.put("linger.ms", 5);   // 小批量积攒提升吞吐
# props.put("batch.size", 32768);
```

### 2.3 消费端倾斜处理

```bash
# 1. 查看各分区消费积压是否不均
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --describe

# 输出示例（关注各分区 LAG 差异）：
# TOPIC  PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
# topic  0          5000            10000           5000
# topic  1          9000            10000           1000    ← 明显倾斜
# topic  2          9500            10000           500

# 2. 消费端处理策略
# - 增加总分区数并扩容 Consumer 实例
# - 使用 Consumer 端自定义分配策略（如 CooperativeStickyAssignor）
# - 对倾斜分区单独监控报警
```

**倾斜判断标准：**
- 最大分区 LAG / 最小分区 LAG > 3 → 轻度倾斜
- 最大分区 LAG / 最小分区 LAG > 10 → 严重倾斜
- 单个分区 LAG 持续增长且其他分区稳定 → 确认倾斜

## 三、消费者组管理

### 3.1 查看消费者组

```bash
# 列出所有消费者组
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 --list

# 查看组详情（包含成员、分区分配、积压）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --describe

# 查看组详情（含成员信息）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --describe --members --verbose

# 查看所有组的积压概览
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --all-groups --describe
```

### 3.2 重置消费者组位移（Offset）

```bash
# 前置条件：消费者组必须处于 INACTIVE 状态（无运行中的 Consumer）

# 重置到最早偏移（重新消费所有数据）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --topic <topic> --reset-offsets --to-earliest --execute

# 重置到最新偏移（跳过已有数据）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --topic <topic> --reset-offsets --to-latest --execute

# 重置到指定时间戳（时间点重放）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --topic <topic> \
  --reset-offsets --to-datetime 2026-06-12T00:00:00.000 --execute

# 重置到指定偏移
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --topic <topic>:0,<topic>:1 \
  --reset-offsets --to-offset 1000 --execute

# 按策略位移（shift forward/backward）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --topic <topic> \
  --reset-offsets --shift-by -5000 --execute

# 支持多主题
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --topic <topic1> --topic <topic2> \
  --reset-offsets --to-earliest --execute

# 支持所有主题
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --all-topics \
  --reset-offsets --to-earliest --execute

# 保存重置计划（先不执行，评估影响）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --topic <topic> \
  --reset-offsets --to-earliest --dry-run
```

### 3.3 删除消费者组

```bash
# 删除消费者组（仅限 INACTIVE 组）
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --delete

# 批量删除偏移过期的消费者组
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 --list | \
  xargs -I {} sh -c 'kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group {} --describe &>/dev/null || \
  kafka-consumer-groups.sh --bootstrap-server <broker>:9092 --group {} --delete'
```

### 3.4 消费者组故障排查

```bash
# GroupCoordinator 不在线
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <group_id> --describe 2>&1 | grep "Coordinator"

# 输出 "The group member is not coordinated" → 重启 Consumer 或等待 Rebalance
# 输出 "The group coordinator is not available" → 检查 Broker 健康

# Rebalance 日志监控
grep "Rebalance\|Joined group\|Stopped rebalance" /var/log/kafka/server.log
```

## 四、分区重分配（Partition Reassignment）

### 4.1 触发场景

- Broker 上下线后分区分布不均
- 磁盘空间不均导致部分 Broker 磁盘满
- 新加 Broker 后需要移入分区
- 退役 Broker 前需要移出分区

### 4.2 生成重分配方案

```bash
# 1. 生成分区迁移 JSON（由 Kafka 自动计算最优分布）
kafka-reassign-partitions.sh --bootstrap-server <broker>:9092 \
  --generate --topics-to-move-json-file topics.json \
  --broker-list "1,2,3,4" > reassign.json

# topics.json 内容格式：
# {
#   "topics": [{"topic": "my_topic"},
#              {"topic": "my_topic2"}],
#   "version":1
# }
```

### 4.3 执行分区重分配

```bash
# 2. 执行重分配
kafka-reassign-partitions.sh --bootstrap-server <broker>:9092 \
  --execute --reassignment-json-file reassign.json

# 3. 查看重分配进度
kafka-reassign-partitions.sh --bootstrap-server <broker>:9092 \
  --verify --reassignment-json-file reassign.json

# 输出详解：
# Status of partition reassignment:
# Reassignment of partition my_topic-0 is complete
# Reassignment of partition my_topic-1 is in progress
# Reassignment of partition my_topic-2 is in progress
```

### 4.4 手动指定重分配方案

```json
// 手动编写 re-assign.json 实现精确控制
{
  "version": 1,
  "partitions": [
    {"topic": "my_topic", "partition": 0, "replicas": [1,2,3]},
    {"topic": "my_topic", "partition": 1, "replicas": [2,3,4]},
    {"topic": "my_topic", "partition": 2, "replicas": [3,4,1]}
  ]
}
```

```bash
# 执行手动方案
kafka-reassign-partitions.sh --bootstrap-server <broker>:9092 \
  --execute --reassignment-json-file manual-reassign.json
```

### 4.5 取消重分配

```bash
# 取消正在进行的重分配（不推荐，仅紧急场景使用）
# 原理：逐一取消各分区移动，需先获取当前分区分配状态
kafka-reassign-partitions.sh --bootstrap-server <broker>:9092 \
  --execute --reassignment-json-file current-assign.json
```

**重分配注意事项：**
- 重分配期间会有**跨 Broker 数据复制**，占用网络和磁盘 IO
- 可通过 `replica.fetch.max.bytes` 和 `num.replica.fetchers` 控制复制速度
- 大分区（TB 级）重分配可能耗时数小时，建议业务低峰期执行
- 可通过减少 `replica.fetch.response.max.bytes` 降低对生产流量的影响
- 重分配完成后务必执行 `--verify` 确认全部完成

## 五、ISR 异常诊断（增强版）

```bash
# 全面扫描 ISR 状态
kafka-topics.sh --describe --zookeeper <zk>:2181 | \
  awk -F'[ ,\t]+' '{for(i=1;i<=NF;i++) if($i~/Isr/) isr=$i; if($i~/Replicas/) rep=$i} \
  {if(isr && rep && rep!=isr) print $0}'

# 正常：Replicas=3, Isr=3 → 所有副本同步
# 异常：Isr < Replicas → 存在落后副本
# 严重：Leader=-1 → 无 Leader，分区不可用
```

**增强修复策略：**
```bash
# 1. 手动触发 Leader 选举
kafka-leader-election.sh --bootstrap-server <broker>:9092 \
  --election-type preferred --all-topic-partitions

# 2. 针对特定主题选举
kafka-leader-election.sh --bootstrap-server <broker>:9092 \
  --election-type preferred --topic <topic_name>

# 3. 紧急情况：允许非 ISR 副本成为 Leader（可能丢数据）
# server.properties: unclean.leader.election.enable=true（临时开启后重启）
# 恢复后立即改为 false

# 4. 增加 ISR 超时防止频繁抖动
# server.properties: replica.lag.time.max.ms=60000（从默认30s调大到60s）

# 5. 增加副本 fetcher 加速追赶
# server.properties: num.replica.fetchers=4（从默认1调高）
```

**ISR 持续收缩根因排查：**
```bash
# 检查落后副本的网络延迟
ping <slow_broker>
# 检查磁盘 IO 是否成为瓶颈
iostat -x 1 | grep <kafka_data_disk>
# 检查 GC 是否频繁
grep "Full GC\|CMS\|G1" /var/log/kafka/kafka-gc.log | tail -20
# 检查副本拉取请求是否超时
grep "ReplicaFetcherThread\|Failed to get" /var/log/kafka/server.log | tail -20
```

## 六、Controller 故障恢复增强

```bash
# 查看当前 Controller
zookeeper-shell.sh <zk>:2181 get /controller

# 返回示例：
# {"version":1,"brokerid":1,"timestamp":"2026-06-12T10:00:00Z"}

# 查看 Controller 选举历史
zookeeper-shell.sh <zk>:2181 ls /controller_epoch
zookeeper-shell.sh <zk>:2181 get /controller_epoch

# 如果没有 Active Controller
# 1. 检查 ZK 连接：确保 ZooKeeper 集群正常
echo stat | nc <zk> 2181

# 2. 查看所有 Broker 的 Controller 状态
for broker in broker1 broker2 broker3; do
  echo "=== $broker ==="
  ssh $broker "grep 'Controller' /var/log/kafka/server.log | tail -5"
done

# 3. 手动触发 Controller 选举
# 方式 A：重启当前 Controller Broker（触发重新选举）
# 方式 B：如果 ZK 中的 /controller 节点残留，手动删除
zookeeper-shell.sh <zk>:2181 rmr /controller

# 4. 强杀 Controller（不推荐，仅 ZooKeeper 节点残留时）
zookeeper-shell.sh <zk>:2181 delete /controller

# 5. 确认新 Controller 生效
kafka-topics.sh --describe --zookeeper <zk>:2181 | head -5
# 应能看到 Leader 分区被重新分配
```

**Controller 故障典型原因：**
- ZK 会话过期 → 检查 ZK 超时配置 `zookeeper.session.timeout.ms`
- Full GC 导致 Controller 失联 → 检查 GC 日志，调整堆内存
- 网络分区导致双 Controller（脑裂）→ 检查网络和 ZK 选举机制
- 元数据变更压力过大 → `num.controller.message.threads` 调大

```bash
# Controller 相关关键参数
# server.properties:
# controller.socket.timeout.ms=30000
# controller.message.queue.size=10
# num.controller.message.threads=8（大集群调至 16）
# zookeeper.session.timeout.ms=18000
# zookeeper.connection.timeout.ms=15000
```

## 七、监控集成（JMX 指标）

### 7.1 启用 JMX

```bash
# Kafka 启动时启用 JMX（在 kafka-server-start.sh 中配置）
export JMX_PORT=9999
export KAFKA_JMX_OPTS="-Dcom.sun.management.jmxremote \
  -Dcom.sun.management.jmxremote.authenticate=false \
  -Dcom.sun.management.jmxremote.ssl=false \
  -Dcom.sun.management.jmxremote.port=9999 \
  -Dcom.sun.management.jmxremote.rmi.port=9999 \
  -Djava.rmi.server.hostname=<broker_ip>"

# 验证 JMX 端口是否监听
netstat -tlnp | grep 9999
```

### 7.2 核心 JMX 指标（用于 Prometheus + Grafana）

| 分类 | MBean 名称 | 指标属性 | 说明 | 告警阈值 |
|------|-----------|---------|------|---------|
| 系统 | kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec | Count | 每秒入流量(字节) | 突降 50% |
| 系统 | kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec | Count | 每秒出流量(字节) | 异常突增 |
| 系统 | kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec | Count | 每秒消息入量 | 持续为零 |
| 分区 | kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions | Value | 分区副本不同步数 | > 0 告警 |
| 分区 | kafka.server:type=ReplicaManager,name=OfflineReplicaCount | Value | 离线副本数 | > 0 告警 |
| 分区 | kafka.controller:type=KafkaController,name=ActiveControllerCount | Value | Active Controller 数 | != 1 告警 |
| 分区 | kafka.controller:type=KafkaController,name=OfflinePartitionsCount | Value | 离线分区数 | > 0 告警 |
| 分区 | kafka.controller:type=KafkaController,name=PreferredReplicaImbalanceCount | Value | Leader 不平衡分区数 | > 0 优化 |
| 请求 | kafka.server:type=RequestMetrics,name=TotalTimeMs,request=Produce | Mean/999th | 生产请求延迟(ms) | p99 > 500ms |
| 请求 | kafka.server:type=RequestMetrics,name=TotalTimeMs,request=FetchConsumer | Mean/999th | 消费请求延迟(ms) | p99 > 500ms |
| 请求 | kafka.server:type=RequestMetrics,name=RequestsPerSec,request=Produce | Count | 生产请求速率 | 同比突降 |
| 网络 | kafka.network:type=SocketServer,name=NetworkProcessorAvgIdle | Value | 网络处理器空闲率 | < 0.3 |
| 网络 | kafka.network:type=RequestChannel,name=RequestQueueSize | Value | 请求队列大小 | > 1000 |
| 日志 | kafka.log:type=LogFlushStats,name=FlushRateAndTimeMs | Count | 日志刷盘频率 | 过高调优 |
| 线程 | java.lang:type=Threading,name=ThreadCount | Value | JVM 线程数 | 突增异常 |
| GC | java.lang:type=GarbageCollector,name=G1 Young Generation | CollectionCount | Young GC 次数 | 打印调试 |
| GC | java.lang:type=GarbageCollector,name=G1 Old Generation | CollectionCount | Old GC 次数 | > 3次/小时 |

### 7.3 JMX 指标采集命令

```bash
# 使用 jmxterm 直接从命令行查询 JMX 指标
# 安装：curl -LO https://github.com/jiaqi/jmxterm/releases/download/v1.0.4/jmxterm-1.0.4-uber.jar

# 查看所有 MBean
echo "beans" | java -jar jmxterm-1.0.4-uber.jar -l <broker>:9999 -n

# 查询 UnderReplicatedPartitions
echo "get -b kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions Value" | \
  java -jar jmxterm-1.0.4-uber.jar -l <broker>:9999 -n

# 批量查询关键指标
cat <<'EOF' | java -jar jmxterm-1.0.4-uber.jar -l <broker>:9999 -n
get -b kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions Value
get -b kafka.server:type=ReplicaManager,name=OfflineReplicaCount Value
get -b kafka.controller:type=KafkaController,name=ActiveControllerCount Value
get -b kafka.controller:type=KafkaController,name=OfflinePartitionsCount Value
get -b kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec OneMinuteRate
get -b kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec OneMinuteRate
EOF
```

### 7.4 Prometheus 集成（JMX Exporter）

```bash
# 下载 JMX Exporter
wget https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.20.0/jmx_prometheus_javaagent-0.20.0.jar

# 创建 prometheus-jmx-config.yaml（含 Kafka 规则）
cat > /etc/kafka/prometheus-jmx-config.yaml <<'CONFIG'
---
lowercaseOutputName: true
rules:
- pattern: kafka.server<type=BrokerTopicMetrics, name=(BytesInPerSec|BytesOutPerSec|MessagesInPerSec)><>OneMinuteRate
  name: kafka_broker_$1
- pattern: kafka.server<type=ReplicaManager, name=(UnderReplicatedPartitions|OfflineReplicaCount)><>Value
  name: kafka_replica_$1
- pattern: kafka.controller<type=KafkaController, name=(ActiveControllerCount|OfflinePartitionsCount)><>Value
  name: kafka_controller_$1
- pattern: kafka.server<type=RequestMetrics, name=TotalTimeMs, request=(Produce|FetchConsumer)><>999thPercentile
  name: kafka_request_$1_p99
- pattern: java.lang<type=GarbageCollector, name=(.*)><>(CollectionCount|CollectionTime)
  name: jvm_gc_$1_$2
CONFIG

# 在 Kafka 启动脚本中添加 javaagent
# KAFKA_OPTS="$KAFKA_OPTS -javaagent:/etc/kafka/jmx_prometheus_javaagent-0.20.0.jar=8080:/etc/kafka/prometheus-jmx-config.yaml"
```

### 7.5 Grafana 告警规则参考

```yaml
# Prometheus AlertManager 规则示例
groups:
  - name: kafka_alerts
    rules:
      - alert: UnderReplicatedPartitions
        expr: kafka_replica_UnderReplicatedPartitions > 0
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Broker {{ $labels.instance }} 有同步落后分区"

      - alert: OfflinePartitions
        expr: kafka_controller_OfflinePartitionsCount > 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "集群存在离线分区"

      - alert: NoActiveController
        expr: kafka_controller_ActiveControllerCount != 1
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "Controller 异常，当前数: {{ $value }}"

      - alert: HighP99ProduceLatency
        expr: kafka_request_Produce_p99 > 500
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "生产请求 p99 延迟超过 500ms"
```

## 八、故障速查表

| 症状 | 根因 | 修复 |
|------|------|------|
| UnderReplicatedPartitions > 0 | ISR 不同步 | 检查网络/磁盘，重启慢副本，调大 replica.lag.time.max.ms |
| ActiveControllerCount = 0 | Controller 挂了 | 检查 ZK 连接，重启 Broker，清除 ZK /controller 残留 |
| ActiveControllerCount > 1 | Controller 脑裂 | 检查网络分区，确认 ZK 集群一致性 |
| OfflinePartitions > 0 | Leader 不可用 | 手动 Leader 选举，检查是否有 Broker 宕机 |
| RequestsPerSec 突降 | Broker 忙/Full GC | 调整堆内存(-Xms=-Xmx)，增加 Broker 节点 |
| NetworkProcessorAvgIdle < 0.3 | 网络瓶颈 | 增加 num.network.threads，升级网卡 |
| Consumer LAG 持续增长 | 消费者处理慢 | 增加分区+Consumer 实例，检查业务处理逻辑 |
| 单分区 Disk 使用率 100% | 分区倾斜 | 增加分区，优化分区键，执行分区重分配 |
| 生产者超时异常频繁 | 请求队列积压 | 调大 acks 降低为 1，增加 Broker，调整 batch.size |
| 消息丢失 | unclean.leader.election | 检查是否设为了 true，生产端启用 acks=all + min.insync.replicas |
| Rebalance 频繁 | session.timeout 过小 | 调大 session.timeout.ms 和 max.poll.interval.ms |
