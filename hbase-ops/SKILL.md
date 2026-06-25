---
name: hbase-ops
description: HBase 运维专家 — Region 管理/Compaction/Split/RegionServer 排障
priority: high
category: bigdata
---

# HBase 运维专家

HBase 运维技能 — Region 管理、Compaction 调优、Split 策略、RegionServer 宕机恢复

## 常用命令速查

### HBase Shell 运维命令

```bash
# 查看集群状态（RegionServer 数量、负载、请求数）
echo 'status' | hbase shell
echo 'status "detailed"' | hbase shell
echo 'status "simple"' | hbase shell

# 查看表信息
echo "describe 'table_name'" | hbase shell
echo "list" | hbase shell

# Region 相关
echo "locate_region 'table_name','rowkey'" | hbase shell
echo "get_table_regions 'table_name'" | hbase shell
echo "meta_table_regions" | hbase shell

# Compaction 操作
echo "major_compact 'table_name'" | hbase shell
echo "major_compact 'table_name','column_family'" | hbase shell
echo "compact 'table_name'" | hbase shell

# Split 操作
echo "split 'table_name','split_key'" | hbase shell

# Region 手动移动
echo "move 'encoded_region_name','server_name'" | hbase shell
echo "assign 'encoded_region_name'" | hbase shell
echo "unassign 'encoded_region_name'" | hbase shell

# Balance 控制
echo "balance_switch" | hbase shell           # 查看当前状态
echo "balance_switch true" | hbase shell      # 开启 balancer
echo "balance_switch false" | hbase shell     # 关闭 balancer
echo "balancer" | hbase shell                 # 手动触发负载均衡
echo "balancer_enabled" | hbase shell         # 查看 balancer 是否启用

# Region 合并
echo "merge_region 'encoded_region_name_1','encoded_region_name_2'" | hbase shell

# Memstore flush
echo "flush 'table_name'" | hbase shell
echo "flush 'region_name'" | hbase shell
```

### HBCK 工具（HBase 修复）

```bash
# 检测集群不一致状态
hbase hbck

# 详细诊断
hbase hbck -details

# 自动修复（谨慎使用）
hbase hbck -fix

# 修复元数据
hbase hbck -fixMeta

# 修复分配
hbase hbck -fixAssignments

# 修复空洞
hbase hbck -fixHoles

# 修复孤儿 Region
hbase hbck -fixOrphans

# HBCK2（HBase 2.x 新版修复工具）
hbase hbck2 -help
hbase hbck2 -setTableState <table_name> <state>
hbase hbck2 -fixMeta
hbase hbck2 -fixAssignments
hbase hbck2 -bypass
```

### WAL 日志管理

```bash
# 查看 WAL 日志
hbase hlog /hbase/WALs/<region_server>/<wal_file>

# WAL 分裂（RegionServer 宕机后）
hbase regionserver  # 重启时会自动进行 WAL split
# 手动检查 WAL 目录状态

# 查看 WAL 目录
hdfs dfs -ls /hbase/WALs/
hdfs dfs -ls /hbase/oldWALs/
```

### Region 大小与状态

```bash
# 查看 Region 大小（HDFS 层面）
hdfs dfs -du -h /hbase/data/default/<table_name>/

# HBase Shell 统计
echo "count 'table_name'" | hbase shell
echo "get_rsgroup 'table_name'" | hbase shell
```

## Region 热点问题

### 问题表现
- 少数 RegionServer 请求量远高于其他节点
- 写入集中在少数 Region 上
- 部分 RegionServer CPU/IO 飙高

### 解决方案

#### 1. 预分区设计
建表时预先创建多个 Region，避免所有写入集中在单个 Region 上：

```bash
echo "create 'table_name','cf', {SPLITS => ['split1','split2','split3','split4','split5','split6','split7','split8','split9','split10','split11','split12','split13','split14','split15']}" | hbase shell

# 或使用 HexStringSplit 自动分区
echo "create 'table_name','cf', {NUMREGIONS => 16, SPLITALGO => 'HexStringSplit'}" | hbase shell
```

#### 2. RowKey 散列设计

| 策略 | 方法 | 优点 | 缺点 |
|------|------|------|------|
| 哈希前缀 | `rowkey = MD5(原始Key).substring(0,4) + 原始Key` | 读写均衡 | 范围扫描不友好 |
| 反转 | `rowkey = 反转(原始Key)` | 均衡写入 | 失去有序性 |
| 加盐 | `rowkey = 分区id + 原始Key` | 灵活可控 | 增加复杂度 |
| 随机前缀 | `rowkey = Random.nextInt( partitions ) + 原始Key` | 简单 | 扫描困难 |

#### 3. Key 设计规范
- **避免 Monotonically Increasing RowKey**：时间戳、自增 ID 作为 RowKey 会导致所有新写入落在最后一个 Region
- **使用 Salt Bucket**：常见做法是 `hash_code % region_count` 作为前缀
- **利用 Value 设计**：热点数据可以通过加盐前缀强制分散

## Compaction 调优

### Compaction 类型

| 类型 | 触发方式 | 作用 | 影响 |
|------|---------|------|------|
| **Minor Compaction** | 自动（达到阈值） | 合并少量 HFile | 轻量，IO 消耗低 |
| **Major Compaction** | 自动/手动 | 合并所有 HFile + 清理删除标记 | 重量级，IO 和 CPU 消耗高 |

### 触发条件

- **Minor Compaction**：当 Store 中 HFile 数量达到 `hbase.hstore.compaction.min`（默认3）
- **Major Compaction**：距上次 Major Compaction 超过 `hbase.hregion.majorcompaction`（默认7天）
- **手动 Major Compaction**：慎选业务低峰期执行

### 关键配置参数

```
# MemStore 刷写大小（默认 128MB）
hbase.hregion.memstore.flush.size = 134217728

# 单个 Region 最大文件大小（触发 Split）
hbase.hregion.max.filesize = 10737418240  # 10GB

# RegionServer 全局 MemStore 上限（默认 40%）
hbase.regionserver.global.memstore.size = 0.4

# Compaction 线程数
hbase.hstore.compaction.threads = 2

# Compaction 输入文件最小数量
hbase.hstore.compaction.min = 3

# Compaction 输入文件最大数量
hbase.hstore.compaction.max = 10

# Major Compaction 周期（毫秒，0 表示禁用自动 Major Compaction）
hbase.hregion.majorcompaction = 604800000  # 7天
hbase.hregion.majorcompaction.jitter = 0.5
```

### 调优建议

- **高写入场景**：增大 `hbase.hregion.memstore.flush.size` 到 256MB，减少刷写频率
- **大 Region 场景**：增大 `hbase.hregion.max.filesize` 到 20-50GB，减少 Region 数量
- **内存紧张**：降低 `hbase.regionserver.global.memstore.size` 到 0.3
- **Major Compaction 策略**：建议设置 `hbase.hregion.majorcompaction = 0`，手动在低峰期执行
- **Minor Compaction 加速**：增加 `hbase.hstore.compaction.threads`，但不超过 CPU 核数的一半

## Split 策略

### 策略类型

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| **IncreasingToUpperBoundRegionSplitPolicy** | 默认策略，动态增加 Split 阈值 | 通用场景 |
| **ConstantSizeRegionSplitPolicy** | 固定阈值 Split | 大表、稳定负载 |
| **KeyPrefixRegionSplitPolicy** | 按 RowKey 前缀分组 | 特定聚合查询 |
| **DelimitedKeyPrefixRegionSplitPolicy** | 按分隔符前缀分组 | 类似 KeyPrefix 但使用分隔符 |
| **SteppingSplitPolicy** | 逐步增大 Split 阈值 | 新表预热 |
| **DisabledRegionSplitPolicy** | 禁用自动 Split | 手动管理 Region |

### 配置示例

```xml
<!-- hbase-site.xml -->
<property>
  <name>hbase.regionserver.region.split.policy</name>
  <value>org.apache.hadoop.hbase.regionserver.IncreasingToUpperBoundRegionSplitPolicy</value>
</property>

<!-- 手动管理 Region 时禁用自动 Split -->
<property>
  <name>hbase.regionserver.region.split.policy</name>
  <value>org.apache.hadoop.hbase.regionserver.DisabledRegionSplitPolicy</value>
</property>
```

### 手动 Split 策略

```bash
# 按指定 SplitKey 切分
echo "split 'table_name','split_point'" | hbase shell

# 指定 Region 切分
echo "split 'region_name'" | hbase shell

# 强制切分所有 Region（谨慎使用）
# 无直接命令，需遍历所有 Region 手动 split
```

## RegionServer 宕机恢复

### 恢复流程

1. **确认宕机**
   ```bash
   # 查看集群状态
   echo 'status' | hbase shell
   
   # 查看 RegionServer 日志
   tail -200 /var/log/hbase/hbase-hbase-regionserver-<host>.log
   
   # HDFS 层面确认数据完整性
   hdfs dfsadmin -report
   ```

2. **WAL 自动分裂与回放**
   - HMaster 检测到 RegionServer 宕机后，将宕机 RS 的 WAL 文件移动到 `/hbase/WALs/` 下
   - 该 WAL 会被**分裂（Split）**到各个 Region 的 `recovered.edits` 目录
   - 各 Region 打开时自动**回放（重演）**WAL 中的 Edit，恢复数据一致性
   - 这个过程称为 **WAL Split & Distribute**

3. **监控 WAL 分裂进度**
   ```bash
   # 查看 WAL 分裂状态
   hdfs dfs -ls /hbase/WALs/
   hdfs dfs -ls /hbase/splitWAL/
   
   # 检查 recovered.edits
   hdfs dfs -ls /hbase/data/default/<table_name>/<region>/recovered.edits/
   ```

4. **Region 重新分配**
   ```bash
   # 查看 Region 分配状态
   echo "hbase hbck -details" | bash
   
   # 强制重新分配（如有 Region 卡在 OPENING/CLOSING 状态）
   echo "assign 'encoded_region_name'" | hbase shell
   ```

5. **HBCK 修复**（如果 Region 状态不一致）
   ```bash
   hbase hbck -fixAssignments -fixMeta
   ```

### 宕机恢复关键参数

```
# WAL 分裂线程数（影响恢复速度）
hbase.hstore.splitlog.manager.threads = 6
hbase.hstore.splitlog.worker.threads = 6

# WAL 回放并行度
hbase.regionserver.wal.edits.replay.parallelism = 8

# 等待 RegionServer 心跳超时（判断是否宕机）
zookeeper.session.timeout = 180000      # 180秒
hbase.regionserver.region.rpc.timeout = 60000
```

### 常见问题

| 症状 | 根因 | 解决方案 |
|------|------|---------|
| Region 卡在 RIT（Region In Transition） | ZooKeeper session 超时或 HMaster 负载过高 | 重启 HMaster 或手动 assign |
| WAL 分裂失败 | HDFS 磁盘不足或权限问题 | 清理 HDFS 空间，检查权限 |
| Region 无法上线 | Meta 表损坏 | 使用 hbck -fixMeta 修复 |
| Recovered edits 过多 | 长期未 Major Compaction | 执行 Major Compaction 清理 |

## 内存与 GC 调优

### RegionServer 内存分配

```
# RegionServer 总堆内存（建议：物理内存的 50%-70%）
HBASE_REGIONSERVER_OPTS="-Xmx32g -Xms32g"

# MemStore 上限（RegionServer 级别全局）
hbase.regionserver.global.memstore.size = 0.4

# BlockCache 上限
hfile.block.cache.size = 0.4

# MemStore + BlockCache 最大总和（超出则刷写部分 MemStore）
hbase.regionserver.global.memstore.size.lower.limit = 0.95
```

> **注意**：`hbase.regionserver.global.memstore.size` + `hfile.block.cache.size` 不应超过 0.8，留出 20% 堆内存给其他操作。

### GC 优化建议

```
# G1GC 配置（推荐 JDK 11+）
HBASE_REGIONSERVER_OPTS="$HBASE_REGIONSERVER_OPTS -XX:+UseG1GC"
HBASE_REGIONSERVER_OPTS="$HBASE_REGIONSERVER_OPTS -XX:MaxGCPauseMillis=100"
HBASE_REGIONSERVER_OPTS="$HBASE_REGIONSERVER_OPTS -XX:ParallelGCThreads=8"
HBASE_REGIONSERVER_OPTS="$HBASE_REGIONSERVER_OPTS -XX:ConcGCThreads=4"
HBASE_REGIONSERVER_OPTS="$HBASE_REGIONSERVER_OPTS -XX:G1HeapRegionSize=32m"
```

## 监控与巡检

### 关键监控指标

| 指标 | 健康值 | 关注点 |
|------|--------|--------|
| Region 数量/RegionServer | 100-300 | 超过则需考虑 Split 或合并 |
| MemStore 堆占比 | < 40% | 过高需增大 flush 频率或内存 |
| StoreFile 数量 | < 50/Store | 过多需触发 Compaction |
| RIT 数 | 0 | 大于 0 表示 Region 状态异常 |
| 请求队列 | < 1000 | 堆积说明处理能力不足 |
| BlockCache Hit Ratio | > 85% | 缓存命中率低需调整 |

### 巡检脚本思路

```bash
#!/bin/bash
# HBase 健康巡检

echo "=== HBase Cluster Status ==="
echo 'status' | hbase shell

echo ""
echo "=== RegionServer 计数 ==="
echo 'status "detailed"' | hbase shell | grep "servers"

echo ""
echo "=== Balancer 状态 ==="
echo 'balance_switch' | hbase shell

echo ""
echo "=== HBCK 一致性检查 ==="
hbase hbck 2>/dev/null | tail -5

echo ""
echo "=== HDFS 使用 ==="
hdfs dfs -df -h /hbase

echo ""
echo "=== Region 分布 ==="
echo "list_regions" | hbase shell 2>/dev/null || echo "Command not available in this version"
```

## 故障排查思维导图

```
RegionServer 宕机
├── 确认宕机状态
│   ├── echo 'status' | hbase shell
│   └── 查看 RS 日志
├── 检查 WAL 分裂
│   ├── hdfs dfs -ls /hbase/splitWAL/
│   └── 等待分裂完成（监控恢复进度）
├── 检查 Region 分配
│   ├── 查看有无 RIT
│   └── 手动 assign 未上线 Region
├── HBCK 修复
│   ├── hbase hbck -details
│   └── hbase hbck -fixAssignments -fixMeta
└── 确认恢复
    ├── echo 'status' | hbase shell
    └── 验证数据读写

Region 热点
├── 识别热点 Region
│   ├── 监控 RegionServer 请求分布
│   └── 找出最大/最忙 Region
├── 优化 RowKey
│   ├── 哈希散列前缀
│   ├── 加盐策略
│   └── 反转 Key
└── 预分区 + Split
    ├── 预创建 Region
    └── 手动 Split 热点 Region

Compaction 压力
├── 查看 Compaction 队列
│   └── RegionServer Web UI
├── 调整触发阈值
│   ├── 增大 min/max 文件数
│   └── 调大 memstore.flush.size
└── 错峰执行
    ├── 禁用自动 Major Compaction
    └── 业务低峰期手动执行
```

## 最佳实践总结

1. **RowKey 设计决定一切** — 良好散列的 RowKey 可以避免 80% 的运维问题
2. **预分区在先** — 建表时预估数据规模并预分区，避免运行时频繁 Split
3. **禁用自动 Major Compaction** — 在 hbase-site.xml 设置 `hbase.hregion.majorcompaction = 0`，手动在低峰期执行
4. **监控 RIT** — Region In Transition 是异常的首要信号
5. **HBCK 修复有风险** — 生产环境优先使用 HBCK2，避免 HBCK 1.x 的自动修复破坏数据
6. **WAL 分裂期间不要强制 HMaster Failover** — 等待分裂完成后再操作
7. **定期执行 Major Compaction** — 清理删除标记和 tombstone，释放 HDFS 空间
