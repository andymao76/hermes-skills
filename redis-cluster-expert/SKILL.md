---
name: redis-cluster-expert
description: Redis Cluster 运维专家 — Slot 管理/主从切换/故障恢复/性能调优
category: bigdata
priority: high
---

# redis-cluster-expert — Redis Cluster 运维专家

## 概述

Redis Cluster 运维技能，覆盖集群全生命周期管理：部署配置、Slot 管理、主从切换、故障恢复、性能调优、内存管理、持久化策略。

## 关键检查命令

### 1. 集群健康检查

```bash
# 集群基本信息 — cluster_state, cluster_slots_assigned/ok/fail/pfail
redis-cli -h <host> -p <port> cluster info

# 节点拓扑 — 每个节点的 ID、角色、地址、状态、所属 slot 范围
redis-cli -h <host> -p <port> cluster nodes

# 节点存活
redis-cli -h <host> -p <port> ping
# 预期输出: PONG

# 详细节点统计
redis-cli -h <host> -p <port> info

# Redis Cluster 完整性检查（内置工具）
redis-cli --cluster check <host>:<port>
```

**cluster info 关键字段**:

| 字段 | 正常值 | 异常判定 |
|------|--------|----------|
| `cluster_state` | `ok` | `fail` — 集群不可用（某部分 slots 未覆盖） |
| `cluster_slots_assigned` | `16384` | `< 16384` — slot 未分配完全 |
| `cluster_slots_ok` | `16384` | `< 16384` — 有 slot 异常 |
| `cluster_slots_pfail` | `0` | `> 0` — 有节点疑似故障（少数派） |
| `cluster_slots_fail` | `0` | `> 0` — 有节点已确认为故障 |
| `cluster_known_nodes` | 所有节点数 | — |
| `cluster_size` | master 节点数 | — |
| `cluster_current_epoch` | 单调递增 | 突变需关注 |

### 2. Redis Cluster 集群管理命令

```bash
# 完整集群检查（推荐）
redis-cli --cluster check <host>:<port>

# 集群信息摘要
redis-cli --cluster info <host>:<port>

# 查看 key 所在 slot
redis-cli -h <host> -p <port> cluster keyslot <key>

# 查看某 slot 被哪个节点服务
redis-cli -h <host> -p <port> cluster slots

# 统计每个节点的 key 数量
redis-cli --cluster info <host>:<port>
```

## MOVED / ASK 重定向

### MOVED 重定向

当客户端向错误的节点请求某个 key 时，节点返回 MOVED 错误指示正确的节点地址：

```
MOVED <slot> <ip>:<port>
```

**典型场景用户遇到过**：`MOVED 8892 215.152.1.17:6379`

这意味着 slot 8892 归属 215.152.1.17:6379，客户端需重新路由请求。

**处理方式**：
- Redis Cluster 客户端（如 JedisCluster、lettuce）自动处理 MOVED 重定向
- 手动验证：`redis-cli -c -h <host> -p <port>`（-c 开启 cluster 模式自动跟随重定向）
- 如果频繁收到 MOVED，说明客户端未维护最新的 slots 映射缓存，应定期刷新

### ASK 重定向

在 resharding（slot 迁移中）时出现，表示 slot 正在迁移：

```
ASK <slot> <ip>:<port>
```

**与 MOVED 的区别**：
| 特征 | MOVED | ASK |
|------|-------|-----|
| 含义 | Slot 已经永久迁移 | Slot 正在临时迁移中 |
| 客户端行为 | 更新 slots 映射缓存 | 发送 ASKING 命令后再请求，不更新缓存 |
| 产生场景 | 迁移完成 | 迁移过程中 |
| 后续 | 不再发往旧节点 | 下次可能仍在旧节点 |

**验证迁移状态**：
```bash
redis-cli -h <host> -p <port> cluster slots
# 同一 slot 出现在两个节点表示正在迁移
```

## Slot 管理

### Slot 分布查看

```bash
# 查看每个节点负责的 slot 范围
redis-cli --cluster check <host>:<port>

# 更简洁的 slot 分配信息
redis-cli -h <host> -p <port> cluster slots
```

### Slot 丢失恢复（fix-slots）

当集群因节点故障、网络分区、或手工操作导致 slot 未被覆盖时，`cluster_state` 变为 `fail`，集群拒绝写入。

**恢复步骤**：

1. **确认哪些 slot 丢失**：
   ```bash
   redis-cli --cluster check <host>:<port>
   # 输出中显示 "[ERR] Not all 16384 slots are covered by nodes."
   ```

2. **尝试自动修复**（将丢失的 slot 分配给指定节点）：
   ```bash
   # 方法一：使用 fix 命令
   redis-cli --cluster fix <host>:<port>
   
   # 方法二：手工将丢失的 slot 分配给主节点
   redis-cli -h <target-host> -p <target-port> cluster addslots <slot1> <slot2> ...
   ```

3. **如果主节点挂了但副本在**：
   ```bash
   # 提升副本为主节点
   redis-cli -h <replica-host> -p <replica-port> cluster failover
   ```

4. **如果节点彻底失联（需清理）**：
   ```bash
   # 确认节点确实失联后，从集群中删除
   redis-cli -h <any-host> -p <any-port> cluster forget <node-id>
   
   # 注意：需要超过 node-timeout 时间后再执行，否则被删除节点会再次被 gossip 传播回来
   ```

**重要原则**：`cluster fix` 可能把 slot 分配给已经数据的节点造成数据不一致 —— 优先用 `cluster failover` 恢复原节点关系。

### Resharding（在线迁移 Slot）

```bash
# 交互式 resharding
redis-cli --cluster reshard <host>:<port>

# 非交互式 resharding（适用于脚本化）
# --from <node-id> --to <node-id> --slots <count> --yes
redis-cli --cluster reshard <host>:<port> \
  --from <source-node-id> \
  --to <target-node-id> \
  --slots <number> \
  --yes
```

**resharding 失败常见原因**：
| 原因 | 现象 | 解决方法 |
|------|------|----------|
| 网络抖动 | 迁移中途卡住 | 重新执行 reshard，支持断点续传 |
| 目标节点内存不足 | OOM 或 eviction | 先扩容目标节点，再继续迁移 |
| 大 Key 迁移超时 | 单 Key 超过 `migrate-covesize-limit` | 拆分大 Key 或调整 `--cluster-migrate-covesize-limit` |
| 源节点压力过大 | 迁移拖慢线上请求 | 限速迁移：`redis-cli --cluster reshard --cluster-pipeline <N>` |

## 主从切换与 Failover

### Failover 触发条件

Redis Cluster 自动 Failover 的判定流程：

1. **节点超时判定**（`cluster-node-timeout`）：
   - PING/PONG 超时未响应 → 标记为 PFAIL（疑似故障）
   - 超过半数主节点在 `cluster-node-timeout` 时间内都标记该节点为 PFAIL → 升级为 FAIL
   - 默认 `cluster-node-timeout = 15000ms`

2. **副本选举**：
   - 数据尽量新（replica 的 offset 与主节点相差不超过指定范围）
   - 在 `cluster-node-timeout * 2` 时间内未参与过投票
   - 先到先得，获得大多数主节点投票的 replica 成为新主

3. **触发流程**：
   ```
   主节点宕机 → 标记 PFAIL → 多数确认 → 标记 FAIL → 副本竞选 → 投票 → 副本晋升为主
   ```

### 手动触发 Failover

```bash
# 在从节点上执行，触发安全的主从切换
redis-cli -h <replica-host> -p <replica-port> cluster failover

# 强制切换（不等主节点响应）
redis-cli -h <replica-host> -p <replica-port> cluster failover force

# 接管切换（忽略主从数据不一致，数据可能丢失）
redis-cli -h <replica-host> -p <replica-port> cluster failover takeover
```

**三种模式对比**：

| 模式 | 说明 | 数据一致性 |
|------|------|-----------|
| `failover`（默认） | 等待主节点同步最新数据后切换 | 强一致 |
| `failover force` | 不等主节点，强制提升 | 可能丢少量数据 |
| `failover takeover` | 忽略集群共识，单方面接管（手破坏 split-brain 保护） | 不保证 |

### 主从关系管理

```bash
# 将节点设为某主节点的从
redis-cli -h <host> -p <port> cluster replicate <master-node-id>

# 取消复制，将自己变为主（如果该主节点 slot 没有丢失）
redis-cli -h <host> -p <port> cluster failover
# 或 
redis-cli -h <host> -p <port> cluster replicate ""
```

## Slot 与批量写入问题

### 批量写入 Slot 错（CROSSSLOT）

**问题**：在事务（MULTI/EXEC）、管道（pipeline）或 Lua 脚本中操作多个 key，但 key 不在同一 slot。

```
CROSSSLOT Keys in request don't hash to the same slot
```

**解决方案**：

1. **使用 Hash Tag** 强制 key 落入同一 slot：
   ```
   {user:1000}.name 和 {user:1000}.age → 同一 slot
   ```
   花括号 `{}` 内的内容决定 slot 归属。

2. **拆分操作** — 按 slot 分组后分别请求。

3. **MSET/MGET 的支持** — Redis Cluster 6.2+ 支持 `MSET`/`MGET` 跨 slot（内部拆分为多个子请求）。

4. **Lua 脚本改造**：
   ```lua
   -- 错误：多个 key 可能不在同一 slot
   EVAL "return redis.call('MGET', KEYS[1], KEYS[2])" 2 key1 key2
   
   -- 正确：使用 hash tag 保证同一 slot
   EVAL "return redis.call('MGET', KEYS[1], KEYS[2])" 2 {tag}key1 {tag}key2
   ```

## Cluster 总线与 Gossip 协议

### 总线端口偏移

- Redis Cluster 节点间通信使用**专门的总线端口** = 服务端口 + 10000
- 例如：6379 → 总线端口 16379
- 防火墙和安全组**必须同时开放**服务端口和总线端口

**原理**：总线连接通过二进制协议（不同于客户端-服务器的 RESP 协议）高效交换集群元数据。

### Gossip 协议原理

Redis Cluster 使用 Gossip 协议进行节点发现和故障传播：

1. **节点间周期通信**：每 100ms 随机选取几个节点发送 PING
2. **消息内容**：包含发送者自身状态 + 随机若干个其他节点的状态信息
3. **传播时效**：故障信息在 `O(log N)` 轮内扩散到全集群
4. **去中心化**：无需中心节点，所有节点地位对等

**关键配置参数**：
```bash
# 集群节点超时（毫秒）
cluster-node-timeout 15000
# 节点间 PING 间隔（毫秒）— 影响故障发现速度
# 不可直接配置，由 node-timeout 决定
# node-timeout / 10 到 node-timeout / 2 之间
```

### 节点握手

```bash
# 将新节点加入集群
redis-cli -h <new-node-host> -p <new-node-port> cluster meet <existing-node-host> <existing-node-port>
```

**注意**：只需与任一已有节点握手，gossip 协议会自动广播到全集群。

## 内存管理

### maxmemory-policy 配置

Redis Cluster 每个节点独立配置逐出策略：

```bash
# 查看当前逐出策略
redis-cli -h <host> -p <port> CONFIG GET maxmemory-policy

# 在线修改
redis-cli -h <host> -p <port> CONFIG SET maxmemory-policy volatile-lru

# 持久化到配置文件
redis-cli -h <host> -p <port> CONFIG SET maxmemory-policy allkeys-lru
redis-cli -h <host> -p <port> CONFIG REWRITE
```

**策略选择指南**：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `noeviction` | 不驱逐，写入时报错 | 缓存不可丢弃的场景 |
| `allkeys-lru` | 所有 key 中淘汰最近最少使用 | 通用缓存（推荐） |
| `allkeys-lfu` | 所有 key 中淘汰最不经常使用 | 访问频率差异大的缓存 |
| `volatile-lru` | 仅带 TTL 的 key 中 LRU | 部分数据需要持久保留 |
| `volatile-lfu` | 仅带 TTL 的 key 中 LFU | 同上，频率优先 |
| `volatile-ttl` | 淘汰剩余 TTL 最短的 key | 优先保留新数据 |
| `volatile-random` | 带 TTL 的 key 中随机淘汰 | 负载均匀的场景 |

**注意**：Redis Cluster 每个节点独立驱逐 —— 不同节点内存使用不均时，部分节点可能先触发 eviction 而其他节点仍有空间。

### 内存碎片整理

```bash
# 查看内存碎片率
redis-cli -h <host> -p <port> info memory | grep mem_fragmentation_ratio

# 手动触发碎片整理
redis-cli -h <host> -p <port> CONFIG SET activedefrag yes

# 碎片整理参数
redis-cli -h <host> -p <port> CONFIG SET active-defrag-threshold-lower 10
redis-cli -h <host> -p <port> CONFIG SET active-defrag-threshold-upper 100
redis-cli -h <host> -p <port> CONFIG SET active-defrag-cycle-min 25
redis-cli -h <host> -p <port> CONFIG SET active-defrag-cycle-max 75
```

**碎片率解读**：
| 碎片率范围 | 含义 | 操作 |
|-----------|------|------|
| < 1.0 | 内存已被过度使用（可能 swap） | 检查内存，加大 maxmemory |
| 1.0 - 1.5 | 正常范围 | 无需操作 |
| > 1.5 | 碎片过多 | 启用 `activedefrag yes` 或重启节点 |
| > 2.0 | 严重碎片化 | 立即启用整理，考虑重启 |

### Big Key 发现

```bash
# 扫描大 key（在从节点执行避免影响主节点性能）
redis-cli -h <host> -p <port> --bigkeys

# 自定义采样大小（默认 250）
redis-cli -h <host> -p <port> --bigkeys --sampling 500

# 内存分析（RDB 方式，需要安装 redis-rdb-tools）
# rdb -c memory dump.rdb --bytes
```

**Big Key 影响**：
- 网络传输延迟（一个大 key 延迟 = 大量小 key 总和延迟）
- Resharding 时大 key 迁移超时
- 导致集群数据倾斜
- 阻塞删除（需用 `UNLINK` 替代 `DEL`）

**处理策略**：
```bash
# 用 UNLINK 异步删除大 key
UNLINK bigkey_name
# 对比：DEL 同步阻塞，UNLINK 后台回收内存

# 大集合拆分方案
# 1. 对大 Hash/List/Set 拆分为多个小 key
# 2. 使用 HSCAN/SSCAN/ZSCAN 分批处理
# 3. 使用 hash tag 保证拆分后的 key 在同意 slot
```

## 持久化策略

### RDB 模式

```bash
# 查看当前 RDB 配置
redis-cli -h <host> -p <port> CONFIG GET save

# 配置默认（900秒至少1个key变化/300秒10/60秒10000）
save 900 1
save 300 10
save 60 10000
```

**优点**：文件紧凑、恢复快、适合全量备份
**缺点**：最后一次保存后可能丢数据

### AOF 模式

```bash
# 启用 AOF
redis-cli -h <host> -p <port> CONFIG SET appendonly yes

# 同步策略
# always — 每条命令 fsync（最安全，最慢）
# everysec — 每秒 fsync（推荐，最多丢1秒数据）
# no — 由 OS 决定
redis-cli -h <host> -p <port> CONFIG SET appendfsync everysec

# AOF 重写触发
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

### 混合持久化（推荐）

Redis 4.0+ 支持 RDB + AOF 混合持久化：

```bash
# 启用混合持久化
redis-cli -h <host> -p <port> CONFIG SET aof-use-rdb-preamble yes
```

**原理**：AOF 重写后文件头部为 RDB 格式（全量快照），后续追加 AOF 增量日志。
**优点**：既有 RDB 的快速加载，又有 AOF 的数据安全保障。

### 持久化策略对比

| 策略 | 数据安全 | 恢复速度 | 文件大小 | 适用场景 |
|------|---------|---------|---------|----------|
| 仅 RDB | 最后快照点 | 最快 | 最小 | 缓存、可容忍丢数据 |
| 仅 AOF (everysec) | 最多丢 1 秒 | 较慢 | 最大 | 数据安全要求高 |
| AOF + RDB 混合（推荐） | 最多丢 1 秒 | 较快 | 中等 | 通用推荐 |
| 关闭持久化 | 无 | N/A | N/A | 纯缓存、数据可重建 |

## 集群分裂（Split-Brain）

### 现象

因网络分区导致集群分为两个或多个子集群，各自选举主节点，产生数据冲突。

**典型场景**：
1. 网络分区将集群切成两半
2. 两个分区各自认为对方死掉
3. 从节点被提升为主节点
4. 网络恢复后出现冲突

### 预防机制

Redis Cluster 通过**仲裁机制**防止 split-brain：

1. **多数派原则**：一个节点只有被超过半数主节点确认 FAIL 后，才会被标记为 FAIL
2. **Min Slaves to Write**：限制写入条件

```bash
# 设置写入必须满足的最小从节点数（防止分区后写入）
redis-cli -h <host> -p <port> CONFIG SET min-replicas-to-write 1
redis-cli -h <host> -p <port> CONFIG SET min-replicas-max-lag 10
```

### 恢复步骤

1. **确认集群状态**：
   ```bash
   redis-cli -h <any-node> -p <port> cluster info | grep cluster_state
   redis-cli -h <any-node> -p <port> cluster nodes
   ```

2. **选择保留的数据**：
   - 保留多数派一侧的数据（epoch 较大的那一侧）
   - 选择数据最新的节点为主

3. **修复流程**：
   ```bash
   # 1. 停止所有节点的 Redis 服务（保留数据）
   
   # 2. 备份数据目录
   # cp -r /data/redis /data/redis-backup
   
   # 3. 确定主节点列表（保留 epoch 较大的一方）
   
   # 4. 重启主节点集群
   
   # 5. 逐个加入从节点
   redis-cli -h <replica> -p <port> cluster replicate <master-node-id>
   
   # 6. 检查一致性
   redis-cli --cluster check <host>:<port>
   ```

4. **数据合并策略**：
   - 如果冲突的 key 可以被覆盖：直接让一方覆盖
   - 如果冲突的 key 不能丢失：手动从备份中提取冲突 key 合并
   - 使用 `redis-cli --cluster fix` 尝试自动修复（不保证数据正确）

## 节点宕机恢复流程

### 1. 主节点宕机

**自动恢复流程**（如果有副本）：
1. 集群自动检测 FAIL
2. 副本发起选举并提升为主
3. 原主节点恢复后以副本身份加入

**手工恢复步骤**：
```bash
# 1. 启动原主节点
redis-server /path/to/redis.conf

# 2. 确认节点已上线
redis-cli -h <recovered-host> -p <port> ping

# 3. 自动跟随为主（如果 slot 已被接管，需做从）
redis-cli -h <recovered-host> -p <port> cluster replicate <new-master-node-id>

# 4. 检验集群状态
redis-cli --cluster check <any-host>:<port>
```

### 2. 从节点宕机

```bash
# 启动从节点后自动同步
redis-server /path/to/redis.conf

# 查看同步进度
redis-cli -h <replica-host> -p <port> info replication | grep master_link_status

# 如果大量从节点同时宕机，限制全量同步的并发
# 分批启动从节点，避免同时触发 RDB 传输
```

### 3. 批量节点宕机（如断电）

```bash
# 1. 检查数据目录完整性
ls -la /data/redis/
ls -la /data/redis/appendonlydir/

# 2. 检查 AOF 文件完整性
redis-check-aof /data/redis/appendonly.aof
# 如有问题可以修复：
redis-check-aof --fix /data/redis/appendonly.aof

# 3. 检查 RDB 文件完整性
redis-check-rdb /data/redis/dump.rdb

# 4. 恢复节点后检查集群
redis-cli --cluster check <host>:<port>

# 5. 如果集群 slot 丢失（多数主节点同时挂掉）
redis-cli --cluster fix <host>:<port>
```

### 4. 节点彻底无法恢复（替换节点）

```bash
# 1. 从集群中移除死节点
redis-cli -h <any-host> -p <port> cluster forget <dead-node-id>

# 2. 准备新节点的配置文件（ip/port 可以不同）
# 3. 启动新节点
redis-server /path/to/redis.conf

# 4. 加入集群
redis-cli -h <new-node> -p <port> cluster meet <existing-node> <existing-port>

# 5. 如果原节点是 master，需要 reshard slot 到新节点
redis-cli --cluster reshard <existing-host>:<port>

# 6. 如果原节点是 slave，指定主节点
redis-cli -h <new-node> -p <port> cluster replicate <master-node-id>
```

## 调优参数速查

### 性能调优

```bash
# 减少RDB/AOF对性能的影响
# RDB 生成不再 fork（避免大页内存导致的延迟 spike）
CONFIG SET rdb-del-sync-files yes

# AOF rewrite 期间不阻塞写入
# 默认 already non-blocking，可以调整 rewrite 触发的频率

# 客户端输出缓冲区
CONFIG SET client-output-buffer-limit "normal 0 0 0 slave 268435456 67108864 60 pubsub 33554432 8388608 60"

# 慢查询日志
CONFIG SET slowlog-log-slower-than 10000    # 微秒，默认 10000（10ms）
CONFIG SET slowlog-max-len 128

# 查看慢查询
SLOWLOG GET 10
```

### 集群相关内核参数

```bash
# 系统层面调整（/etc/sysctl.conf）
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
vm.overcommit_memory = 1
# 禁用透明大页（THP） — 重要！
# echo never > /sys/kernel/mm/transparent_hugepage/enabled
```

## 日志排查指南

```bash
# 查看 Redis 日志关键字
grep -i "fail\|error\|moved\|ask\|reshard\|slot\|cluster" /var/log/redis/redis*.log

# 查看集群状态变化历史
redis-cli -h <host> -p <port> cluster nodes | grep -E "master|slave"

# 监控集群事件
redis-cli -h <host> -p <port> --stat
```

## 快速诊断流程

当接到 Redis Cluster 告警时，按以下顺序排查：

```
1. 先看 cluster info → cluster_state 是 ok 还是 fail？
   ├── ok: 集群可用，继续检查性能问题
   └── fail: slot 覆盖不全 → 执行 cluster check 定位丢失的 slot

2. cluster nodes → 所有节点状态正常？
   ├── 所有节点 connected: 继续
   └── 有 disconnected/fail? 定位故障节点

3. info memory → 内存使用率？
   ├── used_memory < maxmemory: 正常
   └── used_memory ≈ maxmemory: 触发 eviction 或需要扩容

4. 如果有 MOVED 报错 → 检查客户端 slots 缓存是否过期
5. 如果有 ASK 报错 → 检查 resharding 是否进行中
6. 如果有 CROSSSLOT 报错 → 检查批量操作是否正确使用 hash tag
7. 如果有大 key 告警 → 运行 --bigkeys 扫描
```

## 常见问题速查

| 问题 | 原因 | 解决 |
|------|------|------|
| `CLUSTERDOWN The cluster is down` | Slot 未完全覆盖 | `redis-cli --cluster fix` 或 `cluster addslots` |
| `MOVED` 频繁 | 客户端缓存过期 | 更新客户端 slot 缓存 |
| `CROSSSLOT` | 跨 slot 操作 | 使用 hash tag `{}` |
| `LOADING Redis is loading` | 节点重启加载数据中 | 等待加载完成 |
| `MASTERDOWN` | 主节点挂了且无可用从节点 | 恢复主节点或提升从节点 |
| `BUSYKEY` | 迁移时目标 key 已存在 | 删除目标 key 或加 `REPLACE` 选项 |
| `ERR Slot <slot> is already busy` | 添加 slot 时冲突 | 先清空该 slot 再添加 |
| 内存碎片率 > 1.5 | 频繁修改/删除 | 启用 `activedefrag yes` |
| 集群 split-brain | 网络分区 | 以 epoch 较大的一方为准重建 |
| Resharding 卡住 | 网络/大 key/目标节点内存不足 | 检查网络，拆分大 key，扩容后再试 |
