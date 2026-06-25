---
name: greenplum-sre
description: Greenplum 数仓 SRE — 段节点管理/分布键优化/VACUUM 策略/资源队列调优/AOCO 表维护/vmem limit reached 排查。
priority: normal
category: bigdata
---

# Greenplum 数仓 SRE

Greenplum MPP 数据仓库 SRE 运维指南。覆盖 GP6/GP7，聚焦集群状态检查、Segment 管理、资源队列调优、分布键优化、VACUUM 策略、vmem limit reached 排查、AOCO 异常恢复。

## 标准检查命令

```sql
-- 1. 集群整体状态
SELECT * FROM gp_segment_configuration ORDER BY content, role;

-- 2. 活跃查询
SELECT pid, sess_id, usename, state, query_start, wait_event, query
FROM pg_stat_activity
WHERE state != 'idle' AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;

-- 3. 资源组状态
SELECT * FROM gp_toolkit.gp_resgroup_status;

-- 4. 资源组配置
SELECT * FROM gp_toolkit.gp_resgroup_config;

-- 5. Segment 磁盘空间
SELECT * FROM gp_toolkit.gp_disk_free ORDER BY dfsegment;

-- 6. 数据倾斜系数
SELECT schemaname, tablename, skewcoeff
FROM gp_toolkit.gp_skew_coefficients
ORDER BY skewcoeff DESC LIMIT 20;

-- 7. 表膨胀诊断
SELECT * FROM gp_toolkit.gp_bloat_diag;

-- 8. 缺少统计信息的表
SELECT * FROM gp_toolkit.gp_stats_missing;

-- 9. 分布式查询测试（确认所有 Segment 可达）
SELECT gp_segment_id, count(*) AS cnt
FROM gp_dist_random('pg_class')
GROUP BY gp_segment_id
ORDER BY gp_segment_id;

-- 10. 阻塞查询
SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid,
       blocked_activity.usename AS blocked_user, blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_query, blocking_activity.query AS blocking_query
FROM pg_locks blocked_locks
JOIN pg_locks blocking_locks ON blocked_locks.transactionid = blocking_locks.transactionid
JOIN pg_stat_activity blocked_activity ON blocked_locks.pid = blocked_activity.pid
JOIN pg_stat_activity blocking_activity ON blocking_locks.pid = blocking_activity.pid;
```

## 命令行检查（gpstate）

```bash
# 基本状态
gpstate -s           # 详细状态（Segment 状态、镜像、角色）
gpstate -e           # 故障/降级 Segment
gpstate -f           # Standby Coordinator 信息
gpstate -b           # 简要状态摘要
gpstate -c           # 主/镜像映射关系
gpstate -m           # 镜像状态
gpstate -Q           # 查询状态
```

## 一、Segment 管理

### 1.1 Segment 状态检测

```sql
-- 所有 Segment
SELECT dbid, content, role, preferred_role, mode, status, hostname, port
FROM gp_segment_configuration ORDER BY content, role;

-- 异常 Segment（status != 'u'）
SELECT * FROM gp_segment_configuration WHERE status <> 'u';

-- 降级 Segment（mode = 'c' = change tracking）
SELECT * FROM gp_segment_configuration WHERE mode = 'c';

-- 角色非最优（需要 rebalance）
SELECT * FROM gp_segment_configuration WHERE preferred_role <> role;
```

**状态解读：**
| 字段 | 正常值 | 异常值 |
|------|--------|--------|
| `status` | `u` (up) | `d` (down) |
| `mode` | `s` (synchronized) | `c` (change tracking, 降级)、`r` (resyncing) |
| `role` / `preferred_role` | 相同 | 不同（需 rebalance）|

### 1.2 Segment 恢复

```bash
# 检查故障 Segment
gpstate -e

# 增量恢复
gprecoverseg -a

# 检查恢复状态
gpstate -s

# 全量恢复（增量恢复失败时使用）
gprecoverseg -a -F

# 恢复后重新平衡角色
gprecoverseg -r

# 指定并行恢复数（默认最多 16）
gprecoverseg -a -B 8
```

### 1.3 Segment 宕机常见原因

1. **磁盘空间满** → 清理/扩容后恢复
2. **网络中断** → 检查网络连通性后恢复
3. **内存耗尽（OOM）** → 检查 gp_vmem_protect_limit / 资源组配置
4. **文件系统损坏** → 检查 `pg_log`，必要时全量恢复
5. **内核参数问题** → 检查 vm.overcommit 等 sysctl 设置

## 二、分布键优化（DISTRIBUTED BY）

### 2.1 分布键选择原则

1. **选择高基数（distinct values 多）的列** — 确保数据均匀分布
2. **选择经常出现在 JOIN/WHERE 条件中的列** — 减少数据重分布
3. **避免使用 boolean、date 等低基数列** — 会导致严重数据倾斜
4. **多列分布键可提高均匀度** — `DISTRIBUTED BY (col1, col2)`
5. **随机分布（DISTRIBUTED RANDOMLY）** — 适用于无合适分布键或不需要 JOIN 优化的场景

### 2.2 检查当前分布键

```sql
-- 查看表的分布键
SELECT tablename, attname, attnum
FROM pg_class c
JOIN pg_attribute a ON c.oid = a.attrelid AND a.attnum > 0
WHERE c.relname = 'table_name' AND a.attisdistkey = 't';

-- 查看全库所有表的分布键
SELECT n.nspname AS schema_name, c.relname AS table_name,
       string_agg(a.attname, ', ' ORDER BY a.attnum) AS distkey
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
JOIN pg_attribute a ON c.oid = a.attrelid AND a.attisdistkey = 't'
WHERE c.relstorage IN ('h', 'a', 'c') AND n.nspname NOT IN ('pg_catalog', 'information_schema')
GROUP BY n.nspname, c.relname
ORDER BY n.nspname, c.relname;
```

### 2.3 检查数据倾斜

```sql
-- 单表倾斜（每个 Segment 的行数）
SELECT gp_segment_id, count(*) FROM table_name GROUP BY 1 ORDER BY 1;

-- 全库倾斜系数
SELECT schemaname, tablename, skewcoeff
FROM gp_toolkit.gp_skew_coefficients
ORDER BY skewcoeff DESC LIMIT 20;
```

**阈值判断：** `skewcoeff` 越接近 1 越好。段间行数差异 > 10% 说明分布键选择不当。

### 2.4 修复分布键

```sql
-- 重建表并指定新的分布键
BEGIN;
CREATE TABLE table_name_new (LIKE table_name INCLUDING ALL)
WITH (APPENDONLY=true, ORIENTATION=column, COMPRESSTYPE=zlib, COMPRESSLEVEL=5)
DISTRIBUTED BY (high_cardinality_column);
INSERT INTO table_name_new SELECT * FROM table_name;
DROP TABLE table_name;
ALTER TABLE table_name_new RENAME TO table_name;
END;

-- 或使用 CTAS 方式
CREATE TABLE table_name_rebuilt WITH (APPENDONLY=true, ORIENTATION=column)
DISTRIBUTED BY (high_cardinality_column)
AS SELECT * FROM table_name;
DROP TABLE table_name;
ALTER TABLE table_name_rebuilt RENAME TO table_name;
```

## 三、VACUUM 策略

### 3.1 检查需要 VACUUM 的表

```sql
-- 查看死元组比例
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
       round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_ratio DESC;

-- 查看 autovacuum 未启用的表
SELECT relnamespace::regnamespace AS schema_name, relname
FROM pg_class
WHERE 'autovacuum_enabled=false' = ANY(reloptions);
```

### 3.2 VACUUM 执行策略

| 场景 | 命令 | 说明 |
|------|------|------|
| 日常清理 | `VACUUM table_name;` | 标记空间可重用，不锁表 |
| 回收空间 | `VACUUM FULL table_name;` | 回收空间给 OS，锁表 |
| 清理+统计 | `VACUUM (VERBOSE, ANALYZE) table_name;` | 推荐日常使用 |
| AO 表 | `VACUUM table_name;` | AO 表不需要 FULL |
| 全库 | `VACUUM;` | 清理当前库所有表 |

**热表策略：** 高频更新的表建议每 15-30 分钟执行 `VACUUM`（可结合 autovacuum）。

**系统表维护（每周）：**
```sql
VACUUM pg_statistic;
VACUUM pg_class;
VACUUM pg_attribute;
REINDEX SYSTEM database_name;
analyzedb -s pg_catalog -d database_name;
```

**GP7 注意：** `autovacuum` 默认开启，但大表仍建议定期手动 VACUUM。

## 四、资源队列/资源组管理

### 4.1 查看资源组状态

```sql
-- 资源组配置
SELECT * FROM gp_toolkit.gp_resgroup_config;

-- 资源组实时使用情况
SELECT * FROM gp_toolkit.gp_resgroup_status;

-- 查询所属资源组
SELECT rsgname, query, waiting, state FROM pg_stat_activity;
```

### 4.2 资源组调优

```sql
-- 修改资源组 CPU 和内存限制
ALTER RESOURCE GROUP default_group SET memory_limit 0.7;
ALTER RESOURCE GROUP default_group SET concurrency 20;
ALTER RESOURCE GROUP admin_group SET memory_limit 0.9;

-- 创建新资源组
CREATE RESOURCE GROUP etl_group WITH (
    concurrency=10,
    cpu_rate_limit=30,
    memory_limit=0.5,
    memory_shared_quota=0.6
);

-- 将角色绑定到资源组
ALTER ROLE etl_user RESOURCE GROUP etl_group;
```

### 4.3 关键 GUC 参数

| 参数 | 说明 | 推荐设置 |
|------|------|---------|
| `statement_mem` | 单个查询的 Segment 内存 | 根据查询复杂度和并发调整 |
| `max_statement_mem` | 单个查询最大内存 | 不应超过资源组限制 |
| `gp_resgroup_memory_limit` | 资源组总内存比例 | 通常 0.7-0.9 |
| `gp_vmem_protect_limit` | 每个 Segment 进程内存保护值 | 根物理内存/segment 数计算 |
| `optimizer` | 查询优化器（GPORCA） | `on`（GP7 默认） |

## 五、vmem limit reached 排查

### 5.1 问题现象

查询日志中出现 `ERROR: vmem limit reached` 或 `VMEM limit exceeded` 错误，SQL 执行被终止。

### 5.2 诊断步骤

```sql
-- 1. 查看资源组内存使用
SELECT * FROM gp_toolkit.gp_resgroup_status;

-- 2. 查看当前资源组配置
SELECT * FROM gp_toolkit.gp_resgroup_config;

-- 3. 查看当前活跃查询及其资源组
SELECT pid, rsgname, query, state, waiting
FROM pg_stat_activity WHERE state != 'idle';

-- 4. 查看 statement_mem 配置
SHOW statement_mem;
SHOW max_statement_mem;
SHOW gp_resgroup_memory_limit;
```

```bash
# 5. 查看每节点物理内存
gpssh -f hostfile -e 'free -g'

# 6. 查看 gp_vmem_protect_limit 配置
gpconfig -s gp_vmem_protect_limit
```

### 5.3 解决方案

**方案 A：临时调大资源组内存（立即可用）**
```sql
ALTER RESOURCE GROUP default_group SET memory_limit 0.8;
-- 或调大 concurrency（减少并发）
ALTER RESOURCE GROUP default_group SET concurrency 15;
```

**方案 B：调大 segment 级别 memory 限制**
```bash
gpconfig -c gp_vmem_protect_limit -v 16384
gpstop -u   # reload 生效
```

**方案 C：优化单个查询内存**
```sql
-- 在会话级别调大 statement_mem
SET statement_mem = '2GB';

-- 在查询级别设置
SELECT /*+  Set(statement_mem 2GB) */ ...
```

**方案 D：检查并发**
```sql
-- 减少并发连接数
ALTER RESOURCE GROUP default_group SET concurrency 10;
```

### 5.4 根本原因分析

1. **并发过高** → 同时运行大量消耗内存的查询
2. **统计信息过期** → GPORCA 错误估计内存需求
3. **资源组配置不当** → memory_limit 设置过低
4. **物理内存不足** → 需要扩容或减少每节点 Segment 数
5. **分布键倾斜** → 某些 Segment 处理更多数据，需要更多内存

## 六、AOCO 异常恢复

### 6.1 AOCO 文件损坏

**现象：** 查询 AO/CO 表时出现文件读取错误、校验和错误、或段页错误。

**诊断：**
```bash
# Catalog 一致性检查
gpcheckcat -O

# 持久化表检查（需停机窗口）
gpcheckcat -R persistent database_name

# 查看 AO 表状态
SELECT relname, relstorage, reloptions FROM pg_class
WHERE relstorage IN ('a', 'c');
```

**恢复步骤：**

```sql
-- 1. 尝试 VACUUM
VACUUM table_name;

-- 2. 如果 VACUUM 失败，从备份恢复
-- gprestore --dbname database_name --timestamp <ts>

-- 3. 无备份时的紧急方案：跳过损坏行
-- 设置 gp_skip_corrupt_data 为临时跳过
SET gp_skip_corrupt_data = on;
SELECT count(*) FROM table_name;

-- 4. 导出可用数据
CREATE TABLE table_name_good AS
SELECT * FROM table_name
DISTRIBUTED BY (key_column);

-- 5. 重建原表
DROP TABLE table_name;
ALTER TABLE table_name_good RENAME TO table_name;
```

### 6.2 AOCO 膨胀处理

```sql
-- 检查 AO 表膨胀
SELECT relname, pg_relation_size(oid) AS size,
       pg_total_relation_size(oid) AS total_size
FROM pg_class
WHERE relstorage IN ('a', 'c')
ORDER BY pg_total_relation_size(oid) DESC;

-- AO 表 VACUUM（回收空间，不锁表）
VACUUM table_name;

-- 彻底回收空间（重建 AO 表）
ALTER TABLE table_name SET WITH (REORGANIZE=true);
```

### 6.3 AOCO 压缩参数

```sql
-- 创建 AOCO 表时指定压缩
CREATE TABLE sales (
    id INT,
    amount DECIMAL,
    sale_date DATE
) WITH (
    APPENDONLY=true,
    ORIENTATION=column,
    COMPRESSTYPE=zlib,
    COMPRESSLEVEL=5
) DISTRIBUTED BY (id);

-- 查看 AO 表压缩率
SELECT get_ao_compression_ratio('table_name');
-- 压缩率 > 1 表示有压缩效果
```

### 6.4 gpdbrestore / gpcheckcat 工具

```bash
# Catalog 快速检查
gpcheckcat -O

# 完整检查
gpcheckcat database_name

# 持久化表专项（需停机，严重）
gpcheckcat -R persistent database_name

# 特定检查项
gpcheckcat -R pgclass database_name
gpcheckcat -R namespace database_name
gpcheckcat -R dependency database_name
gpcheckcat -R distribution_policy database_name
```

## 七、性能调优

### 7.1 优化器配置

```sql
-- 启用 GPORCA（GP7 默认开启）
SHOW optimizer;

-- 会话级别开启
SET optimizer = on;

-- 查询级别 hint
SELECT /*+ Set(optimizer on) */ ...
```

### 7.2 关键性能参数

```bash
# 查看当前配置
gpconfig -s statement_mem
gpconfig -s max_statement_mem
gpconfig -s gp_resgroup_memory_limit
gpconfig -s optimizer

# 修改配置
gpconfig -c statement_mem -v 2GB
gpconfig -c optimizer -v on
gpstop -u   # reload
```

### 7.3 慢查询诊断

```sql
-- 查看慢查询
SELECT pid, usename, query_start, now() - query_start AS duration,
       wait_event, state, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 minutes'
ORDER BY query_start;

-- 查看查询执行计划
EXPLAIN (ANALYZE) SELECT ...;

-- 查看查询的内存使用
SELECT * FROM gp_toolkit.gp_workload_manager_stats;
```

### 7.4 统计信息维护

```bash
# 全库统计信息更新
analyzedb -d database_name -a

# 指定表更新
analyzedb -d database_name -t schema_name.table_name -a

# 系统表统计信息
analyzedb -s pg_catalog -d database_name
```

## 八、GP7 新特性与变更

| GP6 | GP7 | 说明 |
|-----|-----|------|
| Master | Coordinator | 命名变更 |
| xlog | WAL | WAL 命名统一 |
| 默认无 autovacuum | autovacuum 默认开启 | 注意大表仍建议手动 |
| 资源队列 | 资源组（资源队列已 deprecated） | 建议迁移到资源组 |
| checkpoint_segments | min_wal_size/max_wal_size | checkpoint 参数变更 |
| gpperfmon/GPCC | gpsupport | 统一支持工具 |

## 常见问题速查

| 问题 | 诊断命令 | 处理措施 |
|------|---------|---------|
| Segment down | `gpstate -e` | `gprecoverseg -a` → 增量恢复 |
| Segment 恢复 stuck | 检查 pg_log | `gprecoverseg -a -F` 全量恢复 |
| 角色非最优 | 查询 gp_segment_configuration | `gprecoverseg -r` rebalance |
| vmem limit reached | gp_resgroup_status + gp_resgroup_config | 调大 memory_limit / 降并发 |
| AOCO 文件损坏 | gpcheckcat / log 中的 I/O 错误 | 跳过损坏行 → 导出 → 重建 |
| 数据倾斜 | gp_skew_coefficients / 按 segment 计数 | 重建表、换分布键 |
| 表膨胀 | gp_bloat_diag | VACUUM / VACUUM FULL |
| 查询慢 | pg_stat_activity + EXPLAIN ANALYZE | 检查统计信息、分布键、资源组 |
| 磁盘满 | gp_toolkit.gp_disk_free | 清理/扩容/删除历史分区 |
| Catalog 不一致 | gpcheckcat -O | 根据检查结果修复 |
