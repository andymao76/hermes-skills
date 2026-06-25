---
name: elasticsearch-ops
description: Elasticsearch 运维专家 — 集群健康/Shard 管理/索引优化/性能调优
priority: high
category: bigdata
---

# Elasticsearch Ops

Elasticsearch 运维专家 — 集群健康检查、分片管理、索引优化、性能调优与故障排查。

## 适用场景

- 集群健康状态诊断（Green/Yellow/Red）
- 分片未分配/异常排查
- 索引写入与查询性能优化
- 堆内存与 GC 调优
- 线程池与水位线配置
- 节点掉线恢复与集群稳定运维

## 前置条件

- 任意节点可执行 `curl` 访问 ES HTTP 端口（默认 `9200`）
- 建议设置超时：`--connect-timeout 5 --max-time 10`
- 有 `cluster:monitor/*` 权限（默认 `xpack.monitoring.collection.enabled: true`）

## 1. 集群健康检查

### 1.1 基础状态

```bash
# 集群健康总览
curl -s "http://localhost:9200/_cluster/health?pretty"

# 紧凑输出
curl -s "http://localhost:9200/_cluster/health" | jq '{status, timed_out, number_of_nodes, number_of_data_nodes, active_primary_shards, active_shards, relocating_shards, initializing_shards, unassigned_shards, delayed_unassigned_shards}'
```

**状态含义：**
| 状态 | 含义 | 严重程度 |
|------|------|----------|
| Green  | 所有主分片和副本分片均正常分配 | ✅ 健康 |
| Yellow | 所有主分片已分配，但部分副本未分配 | ⚠️ 需关注 |
| Red    | 至少一个主分片未分配 | ❌ 紧急处理 |

### 1.2 节点信息

```bash
# 节点列表及角色
curl -s "http://localhost:9200/_cat/nodes?v"

# 节点资源详情
curl -s "http://localhost:9200/_cat/nodes?v&h=name,nodeRole,disk.used_percent,heap.current,heap.max,ram.current,ram.max,cpu,load_1m,load_5m,load_15m"
```

### 1.3 索引概览

```bash
# 所有索引状态
curl -s "http://localhost:9200/_cat/indices?v"

# 按大小排序（最大的在前）
curl -s "http://localhost:9200/_cat/indices?v&s=pri.store.size:desc"

# 健康度筛选
curl -s "http://localhost:9200/_cat/indices?v&health=red"
curl -s "http://localhost:9200/_cat/indices?v&health=yellow"
```

## 2. 分片（Shard）管理

### 2.1 查看分片分配

```bash
# 全部分片
curl -s "http://localhost:9200/_cat/shards?v"

# 仅未分配的分片
curl -s "http://localhost:9200/_cat/shards?v&h=index,shard,prirep,state,node,unassigned.reason,unassigned.details&s=state" | grep UNASSIGNED

# 按索引查看分片详情
curl -s "http://localhost:9200/_cat/shards/my-index-*?v"
```

### 2.2 未分配原因排查

```bash
# 查看未分配分片的详细原因
curl -s "http://localhost:9200/_cluster/allocation/explain?pretty"
```

**常见 `unassigned.reason` 及处理：**

| 原因 | 含义 | 处理方案 |
|------|------|----------|
| `ALLOCATION_FAILED` | 分配失败（磁盘满/配置错误） | 检查磁盘空间和节点配置，手动 reroute |
| `CLUSTER_RECOVERED` | 集群恢复中 | 等待集群自动恢复，或检查 `gateway.recover_after_nodes` |
| `NODE_LEFT` | 持有分片的节点离线 | 等节点回归，或手动分配副本 |
| `REINITIALIZED` | 分片在重启后重新初始化 | 观察等待，通常自动完成 |
| `REROUTE_CANCELLED` | 路由被取消 | 重新触发分配或手动 reroute |
| `DECOUPLED_EXPECTED` | 节点离开后预期状态 | 观察等待自动恢复 |
| `INDEX_CREATED` | 索引刚创建 | 等待分配完成 |
| `EXISTING_INDEX_RESTORED` | 从快照恢复 | 等待 restore 完成 |
| `NEW_INDEX_RESTORED` | 从快照创建新索引 | 等待完成 |
| `NO_ATTEMPT` | 尚未尝试分配 | 检查分配策略及节点容量 |
| `DANGLING_INDEX_IMPORTED` | 导入 dangling 索引 | 手动清理或分配 |

### 2.3 手动分片分配

```bash
# 将未分配的分片分配到指定节点
curl -s -XPOST "http://localhost:9200/_cluster/reroute?pretty" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "allocate_empty_primary": {
        "index": "my-index",
        "shard": 0,
        "node": "my-node",
        "accept_data_loss": true
      }
    }
  ]
}'

# 移动分片到另一节点（负载均衡）
curl -s -XPOST "http://localhost:9200/_cluster/reroute?pretty" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "move": {
        "index": "my-index",
        "shard": 0,
        "from_node": "node-a",
        "to_node": "node-b"
      }
    }
  ]
}'

# 取消分片分配
curl -s -XPOST "http://localhost:9200/_cluster/reroute?pretty" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "cancel": {
        "index": "my-index",
        "shard": 0,
        "node": "my-node"
      }
    }
  ]
}'
```

### 2.4 分片分配策略配置

```yaml
# elasticsearch.yml 或动态 API
# 设置磁盘水位线
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.disk.watermark.low": "85%",
    "cluster.routing.allocation.disk.watermark.high": "90%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "95%"
  }
}

# 总分片数限制（每个节点）
PUT _cluster/settings
{
  "persistent": {
    "cluster.max_shards_per_node": 1000
  }
}

# 分配并发控制
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.node_concurrent_incoming_recoveries": 2,
    "cluster.routing.allocation.node_concurrent_outgoing_recoveries": 2,
    "cluster.routing.allocation.node_initial_primaries_recoveries": 4
  }
}
```

## 3. 索引优化

### 3.1 Refresh 策略

```bash
# 查看当前 refresh 间隔
curl -s "http://localhost:9200/my-index/_settings?pretty" | jq '.[].index.refresh_interval'

# 批量写入时禁用自动 refresh（大幅提升写入性能）
PUT my-index/_settings
{
  "index": {
    "refresh_interval": "-1"
  }
}

# 写入完成后恢复
PUT my-index/_settings
{
  "index": {
    "refresh_interval": "30s"
  }
}
```

### 3.2 Translog 配置

```yaml
# translog 影响写入可靠性及性能
PUT my-index/_settings
{
  "index": {
    "translog": {
      "durability": "async",      # async 提升写入性能（有数据丢失风险）
      "sync_interval": "5s",      # 异步刷盘间隔
      "flush_threshold_size": "512mb"  # translog 达到该大小触发 flush
    }
  }
}
```

### 3.3 Segment Merge 管理

```bash
# 强制合并（只对只读索引执行！）
POST my-index/_forcemerge?max_num_segments=1

# 查看段合并线程状态
GET _cat/segments/my-index?v

# 合并调度器设置
PUT _cluster/settings
{
  "persistent": {
    "indices.store.throttle.max_bytes_per_sec": "150mb"
  }
}
```

### 3.4 索引模板与生命周期

```bash
# 创建索引模板（管控分片数与副本数）
PUT _template/logs_template
{
  "index_patterns": ["logs-*"],
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "routing.allocation.total_shards_per_node": 500
  },
  "mappings": {
    "date_detection": true,
    "dynamic": "strict"
  }
}
```

### 3.5 索引只读与关闭

```bash
# 设置索引为只读（用于维护或降级保护）
PUT my-index/_settings
{
  "index.blocks.read_only_allow_delete": true
}

# 关闭索引（释放内存）
POST my-index/_close

# 重新打开
POST my-index/_open
```

## 4. 集群调优

### 4.1 堆内存（HEAP）配置

**50% 黄金法则：**
- 最大堆内存 = 机器物理内存的 50%（不超过 32GB）
- 剩余 50% 留给操作系统 Page Cache / 文件系统缓存
- 单节点堆内存上限 **31GB**（超过后 Java 指针压缩失效，浪费内存）

```bash
# ES_HEAP_SIZE 环境变量或 jvm.options
# jvm.options:
-Xms16g
-Xmx16g
```

### 4.2 GC 配置

**推荐 GC：G1GC**（ES 7.x+ 默认）

```bash
# jvm.options 中的 GC 配置
-XX:+UseG1GC
-XX:G1ReservePercent=25
-XX:InitiatingHeapOccupancyPercent=30

# 查看 GC 情况（通过 API）
GET _nodes/stats/jvm?pretty

# 重点关注指标：
# - jvm.gc.collectors.young.collection_time_in_millis
# - jvm.gc.collectors.old.collection_time_in_millis
# - 如果 old GC 耗时 > 1s 或频繁触发，需排查堆内存泄漏或调整堆大小
```

### 4.3 线程池调优

```bash
# 查看线程池状态（核心指标）
GET _cat/thread_pool?v

# 更详细的线程池统计
GET _nodes/stats/thread_pool?pretty

# 查看等待队列情况
GET _cat/thread_pool?v&h=id,name,active,queue,rejected,largest,completed
```

**常见线程池参数：**

| 线程池 | 默认队列大小 | 说明 | 调优建议 |
|--------|-------------|------|----------|
| `search` | 1000 | 搜索请求处理 | 搜索密集型可增大 queue 到 2000 |
| `bulk` | 200 | 批量写入处理 | 写入密集型可增大 queue 到 1000 |
| `index` | 200 | 单文档写入 | 一般保持默认 |
| `get` | 1000 | 文档 GET 请求 | GET 密集型可适当增大 `thread_pool.get.queue_size` |
| `write` | 200 | 写入请求合并 | 写入量大时关注 rejected 计数 |

```bash
# 动态调整线程池参数
PUT _cluster/settings
{
  "persistent": {
    "thread_pool.search.queue_size": 2000,
    "thread_pool.bulk.queue_size": 1000,
    "thread_pool.write.queue_size": 500
  }
}
```

**队列饱和标识：** 如果 `_cat/thread_pool` 的 `rejected` 计数持续增长，表示队列饱和，请求被丢弃。处理方案：
1. 增大 `queue_size`
2. 增加集群节点
3. 降低客户端并发量并启用重试机制

### 4.4 磁盘水位线

```yaml
# 三档水位线
low:        85%    # 超过此水位，ES 不再向该节点分配新分片
high:       90%    # 超过此水位，ES 开始将分片迁出该节点
flood_stage: 95%   # 超过此水位，所有索引设为只读（blocks.read_only_allow_delete）
```

```bash
# 查看当前水位线
GET _cluster/settings?include_defaults=true&filter_path=*.cluster.routing.allocation.disk.watermark*

# 紧急处理：flood_stage 触发后解除只读
PUT _all/_settings
{
  "index.blocks.read_only_allow_delete": null
}
```

### 4.5 Indexing 与 Search 隔离

```yaml
# 通过节点角色分离写入与查询节点
# 写入节点 node.roles: [data, ingest]
# 查询节点 node.roles: [data]
# 专用协调节点 node.roles: []  # 仅做请求路由
```

## 5. 常见问题排查

### 5.1 分片过多（Shard Bloat）

**症状：** 集群状态频繁 Yellow，节点负载高，段合并 I/O 上升，写入/查询延迟增加。

**诊断：**
```bash
# 统计每个节点的分片数
curl -s "http://localhost:9200/_cat/shards?v" | awk '{print $NF}' | sort | uniq -c | sort -rn

# 查看每个索引的分片数
curl -s "http://localhost:9200/_cat/indices?v&h=index,pri,rep,docs.count,store.size"
```

**推荐分片计算：**
- 每个分片大小：**10GB ~ 50GB**
- 每个节点总分片数：**不超过 1000（每 GB 堆内存约 20-25 个分片）**
- 公式：`total_shards = (数据总量 / 期望单分片大小) × (1 + 副本数)`

**处理方案：**
```bash
# 重建索引（重新分片）
POST _reindex
{
  "source": {
    "index": "old-over-sharded-index"
  },
  "dest": {
    "index": "new-proper-sharded-index"
  }
}
# 删除旧索引后，用 alias 切换
```

### 5.2 段合并问题

**症状：** I/O 高、CPU 高、查询变慢、merge 线程长期繁忙。

```bash
# 查看合并状态
GET _nodes/stats/indices/merge?pretty

# 检查当前合并队列长度
GET _cat/thread_pool/force_merge?v
```

**处理方案：**
1. 对只读索引执行 `_forcemerge`
2. 调大 `indices.store.throttle.max_bytes_per_sec`
3. 避免频繁 update/delete（导致大量小段）
4. 设置合理的 `refresh_interval`（不要太短）

### 5.3 慢查询排查

#### 慢查询日志

```yaml
# 启用慢查询日志（动态配置）
PUT _settings
{
  "index.search.slowlog.threshold.query.warn": "5s",
  "index.search.slowlog.threshold.query.info": "2s",
  "index.search.slowlog.threshold.query.debug": "500ms",
  "index.search.slowlog.threshold.query.trace": "200ms",
  "index.search.slowlog.threshold.fetch.warn": "2s",
  "index.search.slowlog.threshold.fetch.info": "1s",
  "index.search.slowlog.threshold.fetch.debug": "500ms",
  "index.search.slowlog.threshold.fetch.trace": "200ms"
}
```

#### 慢写入日志

```yaml
PUT _settings
{
  "index.indexing.slowlog.threshold.index.warn": "5s",
  "index.indexing.slowlog.threshold.index.info": "1s",
  "index.indexing.slowlog.threshold.index.debug": "500ms",
  "index.indexing.slowlog.threshold.index.trace": "200ms"
}
```

#### 热点线程分析

```bash
# 查看各节点繁忙线程（定位慢查询来源）
GET _nodes/hot_threads
```

### 5.4 节点掉线恢复

**诊断步骤：**
```bash
# 1. 检查集群状态
GET _cluster/health

# 2. 查看当前节点列表（确认哪些节点离线）
GET _cat/nodes?v

# 3. 查看未分配分片
GET _cat/shards?v&h=index,shard,prirep,state,node,unassigned.reason

# 4. 检查掉线原因
GET _cluster/allocation/explain?pretty

# 5. 查看集群恢复状态
GET _recovery?pretty
```

**恢复步骤：**

1. **节点可恢复：** 重启节点，等待集群自动重新分配分片
2. **节点不可恢复（硬件故障）：**
   ```bash
   # 将掉线节点从集群中踢出
   PUT _cluster/settings
   {
     "persistent": {
       "cluster.routing.allocation.exclude._name": "failed-node-name"
     }
   }
   ```
3. **加速恢复：**
   ```bash
   PUT _cluster/settings
   {
     "persistent": {
       "cluster.routing.allocation.node_concurrent_recoveries": 4,
       "indices.recovery.max_bytes_per_sec": "200mb"
     }
   }
   ```
4. **如果主分片丢失且无法恢复（Red 状态）：**
   ```bash
   # 使用 API 重新分配空主分片（接受数据丢失）
   POST _cluster/reroute
   {
     "commands": [
       {
         "allocate_empty_primary": {
           "index": "my-index",
           "shard": 0,
           "node": "surviving-node",
           "accept_data_loss": true
         }
       }
     ]
   }
   ```

### 5.5 Circuit Breaker 触发

**症状：** 请求返回 `429 CircuitBreakingException`

```bash
# 查看断路器状态
GET _nodes/stats/breakers?pretty

# 重点关注 parent tripped（父断路器）和 fielddata tripped
# 处理：加大堆内存，优化查询（减少 fielddata/内存聚合），增加节点
```

## 6. 日常巡检命令速查

```bash
# 一句话巡检（组合命令）
echo "=== 集群健康 ===" && \
curl -s "localhost:9200/_cluster/health?pretty" && \
echo "=== 节点 ===" && \
curl -s "localhost:9200/_cat/nodes?v&h=name,nodeRole,disk*,heap*,cpu,load_1m,load_5m" && \
echo "=== 索引 ===" && \
curl -s "localhost:9200/_cat/indices?v&h=health,status,index,pri,rep,docs.count,docs.deleted,store.size,pri.store.size" && \
echo "=== 未分配分片 ===" && \
curl -s "localhost:9200/_cat/shards?v&h=index,shard,prirep,state,node,unassigned.reason" | grep UNASSIGNED && \
echo "=== 线程池拒绝 ===" && \
curl -s "localhost:9200/_cat/thread_pool?v&h=id,name,active,queue,rejected,largest,completed" | grep -v "0$"
```

## 7. 最佳实践总结

| 领域 | 建议 |
|------|------|
| 分片大小 | 10-50GB/分片 |
| max_shards_per_node | 每 GB 堆内存 ≤ 25 个分片 |
| 堆内存 | 物理内存的 50%，≤ 31GB |
| GC | G1GC，`InitiatingHeapOccupancyPercent=30` |
| 副本数 | 生产环境 1 副本（高可用），写入密集可暂时降为 0 |
| refresh_interval | 写入密集时设为 30s 或 -1 |
| 水位线 | low: 85%, high: 90%, flood_stage: 95% |
| 快照 | 定期做快照备份到 S3/HDFS |
| 监控 | 部署 cerebro / elastic-hq / Kibana Stack Monitoring |

## 注意事项

- 执行 `allocate_empty_primary` 会导致数据丢失，务必确认
- `_forcemerge` 只能在只读索引上执行（写入中会报错）
- 动态修改 `thread_pool.*` 参数只在集群重启后持久化
- 磁盘水位达到 `flood_stage` 时恢复只读后需手动解除
- 跨版本升级前先查阅 ES 官方升级路径文档
