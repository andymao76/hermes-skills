---
name: hive-expert
description: Hive 数据仓库专家 — Metastore 诊断/Partition 管理/Tez 排障/权限审计
category: bigdata
priority: high
---

# hive-expert — Hive 数据仓库专家

## 概述

Hive 数据仓库运维与排障技能，覆盖日常检查、元数据管理、查询优化、异常排查全流程。

## 覆盖范围

| 模块 | 内容 |
|------|------|
| 基础查询 | show databases, show tables, show partitions, desc formatted, show create table |
| Metastore 诊断 | 连接失败排查、表结构不一致修复、元数据版本冲突 |
| Partition 管理 | 分区丢失修复（MSCK REPAIR TABLE）、动态分区调优、大量分区场景优化 |
| Tez 排障 | 容器内存溢出（OOM）、DAG 执行失败、数据倾斜、Reducer 数量调优 |
| 权限审计 | Hive 授权模型（SQL Std / Ranger / Sentry）、角色权限查询、用户授权检查 |
| SQL 调优 | mapjoin 优化、vectorization、Tez grouping、文件格式选择、分区裁剪 |

---

## 1. 基础信息查询

### 1.1 数据库与表清单

```sql
-- 列出所有数据库
SHOW DATABASES;

-- 切换数据库
USE <database_name>;

-- 查看当前数据库下的所有表
SHOW TABLES;

-- 模糊匹配表名
SHOW TABLES LIKE '*order*';
```

### 1.2 表结构详情

```sql
-- 查看字段信息、分区键、存储格式、SerDe、位置等完整元数据
DESC FORMATTED <table_name>;

-- 精简版（仅字段 + 分区键）
DESC <table_name>;

-- 查看建表 DDL，包含 TBLPROPERTIES、LOCATION、SERDE 等完整定义
SHOW CREATE TABLE <table_name>;
```

**DESC FORMATTED 关键字段解读**：

| 输出行 | 含义 |
|--------|------|
| `Location` | HDFS 上的表数据路径 |
| `Table Type` | MANAGED_TABLE（内部表）或 EXTERNAL_TABLE（外部表） |
| `Partition Provider` | `Catalog`（使用 HMS分区）/ `filesystem`（HiveStreaming）|
| `Num Buckets` | 分桶数，-1 表示未分桶 |
| `InputFormat` | TextInputFormat / ParquetInputFormat / OrcInputFormat |
| `OutputFormat` | 对应的输出格式 |
| `SerDe Library` | 序列化/反序列化类（LazySimpleSerDe / ParquetHiveSerDe / OrcSerde）|
| `Storage Desc Params` | SerDe 参数（field.delim, line.delim, serialization.format）|
| `Table Parameters` | TBLPROPERTIES 中的关键属性（transient_lastDdlTime, numFiles, totalSize）|

### 1.3 分区信息

```sql
-- 查看表的所有分区
SHOW PARTITIONS <table_name>;

-- 查看指定分区值
SHOW PARTITIONS <table_name> PARTITION(dt='2024-01-01');

-- 统计分区数量
SHOW PARTITIONS <table_name> | wc -l

-- 查看分区字段定义
DESC FORMATTED <table_name> PARTITION(dt='2024-01-01');
```

---

## 2. Metastore 异常排查

### 2.1 连接失败排查

**现象**：`FAILED: SemanticException org.apache.hadoop.hive.ql.metadata.HiveException: java.lang.RuntimeException: Unable to instantiate org.apache.hadoop.hive.ql.metadata.SessionHiveMetaStoreClient`

**排查步骤**：

| 步骤 | 命令/操作 | 预期 |
|------|-----------|------|
| 1. 检查 HMS 进程 | `ps aux | grep HiveMetaStore` | 进程存在 |
| 2. 检查 HMS 端口 | `netstat -tlnp | grep 9083` | 端口监听（默认 9083） |
| 3. 检查后端 DB | `mysql -h<host> -u<hive_user> -p -e "SELECT 1"` | 返回 1 |
| 4. 检查 HMS 日志 | `tail -100 /var/log/hive/hive-metastore.log` | 无 ERROR/Exception |
| 5. 测试 Thrift 连通 | `telnet <metastore_host> 9083` | 连接成功 |
| 6. 检查 Kerberos（若启用）| `klist -e` | Ticket 未过期 |

**常见根因**：

- **HMS 后端数据库连接池耗尽** → `hive.metastore.pool.max.connections` 调大（默认 20）
- **HMS 进程 OOM** → 增大 `METASTORE_HEAPSIZE`（推荐 4G-8G）
- **MySQL 连接超时** → `wait_timeout` / `interactive_timeout` 调大至 28800
- **Kerberos ticket 过期** → `kinit -kt /etc/security/keytabs/hive.service.keytab hive/<FQDN>`
- **Thrift 超时** → `hive.metastore.client.socket.timeout` 调大（默认 600s）

### 2.2 表结构不一致

**现象**：DESC 看到的字段与实际 HDFS 文件 schema 不匹配，或 `SELECT *` 报错

**排查流程**：

```bash
# 1. 确认 HMS 中的 schema
hive -e "DESC FORMATTED <db>.<table>" | grep -E "col_name|data_type|Location"

# 2. 确认 HDFS 文件实际 schema（以 Parquet 为例）
parquet-tools schema /path/to/table/part-00000.parquet

# 3. 检查 ORC 文件 schema
hive --orcfiledump /path/to/table/part-00000.orc | head -50

# 4. 检查 HDFS 文件头与 partition spec 是否一致
hadoop fs -ls /path/to/table/

# 5. 对比 SHOW CREATE TABLE 与文件 schema
```

**修复手段**：

```sql
-- 方案 A：安全 — 重建表定义匹配文件 schema（ALTER TABLE REPLACE COLUMNS）
ALTER TABLE <table_name> REPLACE COLUMNS (
  col1 STRING,
  col2 INT,
  col3 DECIMAL(18,6)
);

-- 方案 B：交换分区 — 修正单个分区的字段定义
ALTER TABLE <table_name> EXCHANGE PARTITION(dt='2024-01-01') WITH TABLE <temp_table>;

-- 方案 C：完全重建（适用于外部表，数据不动）
DROP TABLE <table_name>;
CREATE EXTERNAL TABLE <table_name> (...) PARTITIONED BY (...) STORED AS PARQUET LOCATION '...';
MSCK REPAIR TABLE <table_name>;
```

**⚠️ 警示**：`ALTER TABLE REPLACE COLUMNS` 会替换整个表的 schema 定义而非逐字段增删改。建议在操作前备份 `SHOW CREATE TABLE` 的输出。

### 2.3 元数据版本冲突

**现象**：`MetaException(message: Version information not found in metastore.)`

**修复**：

```sql
-- 查看 HMS schema 版本
SELECT * FROM VERSION;

-- 查看 hive 版本与 HMS 期望版本是否匹配
hive --version

-- 升级 HMS schema（需停机维护）
schematool -dbType mysql -upgradeSchemaFrom <old_version> -userName hive -passWord <pwd>
```

---

## 3. Partition 管理

### 3.1 分区丢失修复

**症状**：手动在 HDFS 上创建或移入分区目录后，Hive 无法查询到该分区（SHOW PARTITIONS 不显示）

```sql
-- 全量修复：扫描 HDFS 路径并自动添加缺失分区
MSCK REPAIR TABLE <table_name>;

-- 仅添加缺失分区（不删除多余分区元数据）
MSCK REPAIR TABLE <table_name> ADD PARTITIONS;

-- 仅删除多余分区元数据（HDFS 中已删除但 HMS 中仍有记录）
MSCK REPAIR TABLE <table_name> DROP PARTITIONS;

-- 同步分区元数据（Hive 3+，适用于大量分区场景，效率更高）
ALTER TABLE <table_name> RECOVER PARTITIONS;
```

**参数优化**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `hive.msck.repair.batch.size` | 3000 | 每批修复的分区数，表有 10 万+分区时调小至 500 |
| `hive.msck.partition.discovery.interval.ms` | 60000 | 分区发现间隔（ms），配合 Recover Partitions 使用 |
| `hive.metastore.disallow.incompatible.col.type.changes` | false | 设为 false 允许 MSCK REPAIR 时自动兼容字段类型变化 |

### 3.2 手动添加/删除分区

```sql
-- 手动添加分区
ALTER TABLE <table_name> ADD PARTITION(dt='2024-01-01') LOCATION '/path/to/table/dt=2024-01-01';

-- 手动删除分区（删除元数据 + HDFS 数据）
ALTER TABLE <table_name> DROP PARTITION(dt='2024-01-01');

-- 仅删除元数据，保留 HDFS 数据
ALTER TABLE <table_name> DROP PARTITION(dt='2024-01-01') PURGE;

-- 批量删除多个分区
ALTER TABLE <table_name> DROP PARTITION(dt<'2023-01-01');
```

### 3.3 动态分区写入调优

```sql
-- 启用动态分区
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;

-- INSERT 动态分区写入
INSERT OVERWRITE TABLE <target_table> PARTITION(dt)
SELECT col1, col2, dt
FROM <source_table>;
```

**动态分区关键参数**：

| 参数 | 建议值 | 说明 |
|------|--------|------|
| `hive.exec.max.dynamic.partitions` | 1000-10000 | 单任务最大生成分区数，超限报错 |
| `hive.exec.max.dynamic.partitions.pernode` | 100-1000 | 单节点最大生成分区数 |
| `hive.exec.max.created.files` | 100000 | 单任务最大文件数，动态分区容易产生大量小文件 |

---

## 4. Tez 执行异常分析

### 4.1 容器 OOM / 内存溢出

**现象**：`Container killed by the ApplicationMaster. Container killed on request. Exit code is 143` 或 `Container [pid=xxxxx] is running beyond physical memory limits. Current usage: ...`

**排查步骤**：

```bash
# 1. 查看 Tez session 日志
yarn logs -applicationId <app_id> | grep -i "outofmemory\|OOM\|killed"

# 2. 检查 Container 实际内存使用
yarn logs -applicationId <app_id> -containerId <container_id> | tail -200

# 3. 查看 Tez AM 内存
yarn application -status <app_id> | grep -i memory
```

**修复方案**：

```sql
-- 方案 1：增大 Container 内存
SET hive.tez.container.size = 4096;          -- 单位 MB
SET hive.tez.java.opts = -Xmx3276m;          -- 通常为 container.size 的 80%
SET hive.auto.convert.join.noconditionaltask.size = 1000;  -- 缩小 mapjoin 阈值

-- 方案 2：增大 reducer 内存
SET hive.tez.reducer.memory.mb = 2048;

-- 方案 3：启用 Container 重用减少开销
SET hive.tez.container.reuse = true;
SET tez.am.container.reuse.enabled = true;

-- 方案 4：启用 Mapjoin 避免 Join 阶段的 Shuffle
SET hive.auto.convert.join = true;
SET hive.mapjoin.smalltable.filesize = 25000000;  -- 小表 25MB 以内走 mapjoin
```

### 4.2 DAG 执行失败

**现象**：`Status: Failed: Execution failed, return code 2 from org.apache.hadoop.hive.ql.exec.tez.TezTask`

**排查流程**：

```bash
# 1. 获取 Application ID
yarn application -list | grep -i <query_name|user_name>

# 2. 查看详细日志
yarn logs -applicationId <app_id> > /tmp/tez_logs.txt

# 3. 检查 Tez UI（如果有）查看 DAG 各 vertex 状态
# http://<tez-ui-host>:<port>

# 4. 统计各 stages 的异常
grep -i "FAILED\|ERROR\|KILLED\|Exception" /tmp/tez_logs.txt | sort | uniq -c | sort -rn
```

**常见 DAG 失败原因及处理**：

| 错误 | 根因 | 解决 |
|------|------|------|
| `Vertex failed, vertexName=Map 1` | 输入路径不存在或权限不足 | `hadoop fs -ls <input_path>` 检查 |
| `TezSessionPoolManager: ... timed out` | Session 池资源不足 | 增大 `tez.session.client.timeout.secs` |
| `java.lang.OutOfMemoryError: Java heap space` | Container 内存不足 | 增大 `hive.tez.container.size` |
| `Container killed for exceeding memory limits` | 物理内存超限 | 增大 `yarn.scheduler.maximum-allocation-mb` |
| `Unable to read data from container` | 网络或 shuffle 超时 | 增大 `tez.runtime.max.task.failures.per.node` |

### 4.3 数据倾斜

**现象**：Reduce 阶段某些 task 长时间运行，其他 task 很快完成，总耗时远高于预期

```sql
-- 方案 1：自动倾斜处理
SET hive.groupby.skewindata = true;
-- 启用后会产生额外的 MR/Tez job，先进行一次随机分区再去重聚合

-- 方案 2：设置倾斜键手动处理
SET hive.optimize.skewjoin = true;
SET hive.skewjoin.key = 100000;  -- 某个 key 超过此行数视为倾斜

-- 方案 3：分桶 Map Join（适用于大表 join 大表但特定 key 倾斜）
SET hive.optimize.bucketmapjoin = true;
SET hive.optimize.bucketmapjoin.sortedmerge = true;
```

**数据倾斜的 SQL 层排查**：

```sql
-- 排查有问题的 SQL 模式
-- 危险模式：COUNT(DISTINCT) + GROUP BY 大量不同值
-- 危险模式：JOIN 在低基数或分布不均的列上（如 NULL 值）
-- 危险模式：笛卡尔积 JOIN（无 ON 条件）

-- 手动排查倾斜 key：
-- 对 join 列做分布统计
SELECT key_column, COUNT(*) AS cnt
FROM table_name
GROUP BY key_column
ORDER BY cnt DESC
LIMIT 10;
```

### 4.4 Reducer 数量调优

```sql
-- 手动设置 reducer 数量
SET hive.exec.reducers.bytes.per.reducer = 268435456;  -- 每个 reducer 处理 256MB
SET hive.exec.reducers.max = 1009;                     -- 最大 reducer 数

-- 强制指定 reducer 数
SET mapred.reduce.tasks = 50;

-- 禁用 reducer（某些聚合查询可以 map-only）
SET hive.exec.reducers.bytes.per.reducer = 1073741824;  -- 1GB 触发合并
```

**经验公式**：
- `reducer 数 = 输入数据量 / hive.exec.reducers.bytes.per.reducer`
- 单个 reducer <= 1GB 数据（Tez 下建议 256MB-512MB）

---

## 5. 权限审计

### 5.1 Hive 授权模型

Hive 主要支持三种授权方式：

| 模型 | 说明 | 适用场景 |
|------|------|----------|
| **SQL Standards Based** | Hive 内置，基于 SQL 标准授权 | 小集群、无 Ranger |
| **Ranger** | 统一权限管理，细粒度控制 | 企业级生产环境 |
| **Sentry** | 旧版（Apache），角色权限模型 | 已逐步被 Ranger 取代 |

### 5.2 SQL Std 授权审计

```sql
-- 查看当前用户
SELECT current_user();

-- 查看当前用户角色
SHOW CURRENT ROLES;

-- 查看所有角色（需要管理员）
SHOW ROLES;

-- 查看角色拥有的权限
SHOW GRANT ROLE <role_name>;

-- 查看某个用户对某个表的权限
SHOW GRANT USER <user_name> ON TABLE <db_name>.<table_name>;

-- 查看某个角色对某个表的权限
SHOW GRANT ROLE <role_name> ON TABLE <db_name>.<table_name>;

-- 查看当前用户对当前数据库的权限
SHOW GRANT;

-- 授予角色给用户
GRANT ROLE <role_name> TO USER <user_name>;

-- 撤销角色
REVOKE ROLE <role_name> FROM USER <user_name>;
```

### 5.3 HDFS 权限检查

Hive 查询底层依赖 HDFS 的读/写权限：

```bash
# 检查表数据路径的 HDFS 权限
hadoop fs -ls /apps/hive/warehouse/<db>.db/<table>

# 检查 partition 目录权限（分区表）
hadoop fs -ls /apps/hive/warehouse/<db>.db/<table>/dt=2024-01-01

# 递归检查目录权限（大量分区时慎用）
hadoop fs -ls -R /apps/hive/warehouse/<db>.db/<table> | head -20
```

**常见权限异常**：
- `Permission denied: user=xxx, access=READ, inode="/apps/hive/warehouse/..."` → 表路径无读权限
- `SemanticException: Unable to construct partition` → HDFS 无 list 权限
- `AuthorizationException: User xxx does not have privileges` → Hive 授权层面拒绝

### 5.4 Ranger/Sentry 审计查询

```bash
# Ranger 审计（通过 API 或界面）
# http://<ranger-host>:6080/index.html#!/reports/audit/bigData?serviceType=hive

# 查看 Ranger 策略（API）
# curl -u admin:admin "http://<ranger-host>:6080/service/plugins/policies/service/<service_id>"

# Sentry 角色查看
beeline -u "jdbc:hive2://<hs2-host>:10000/default;principal=hive/_HOST@REALM" \
  -e "SHOW ROLE GRANT USER <user_name>;"
```

---

## 6. SQL 性能调优

### 6.1 MapJoin 优化

MapJoin 将小表全量加载到内存中，在 Map 阶段直接完成 Join，避免 Shuffle。

```sql
-- 启用自动 MapJoin
SET hive.auto.convert.join = true;
SET hive.auto.convert.join.noconditionaltask = true;

-- 小表阈值（默认 10MB，根据集群内存调整）
SET hive.auto.convert.join.noconditionaltask.size = 52428800;  -- 50MB
SET hive.mapjoin.smalltable.filesize = 52428800;

-- 手动指定 MapJoin
SELECT /*+ MAPJOIN(b) */ a.key, a.value, b.desc
FROM large_table a
JOIN small_table b ON a.key = b.key;
```

**何时无效**：
- 两张表都很大（无法加载到内存）
- Join 条件是复杂表达式而非等值连接
- 小表超过 `hive.auto.convert.join.noconditionaltask.size` 阈值

### 6.2 Vectorization（向量化执行）

向量化执行批量处理数据而非逐行处理，对 ORC 格式尤为有效。

```sql
-- 启用向量化
SET hive.vectorized.execution.enabled = true;
SET hive.vectorized.execution.reduce.enabled = true;

-- 检查是否生效（explain 输出中应有 Vectorized 字样）
EXPLAIN SELECT COUNT(*) FROM <table_name>;
```

**前置条件**：
- 存储格式必须为 ORC（Parquet 不支持向量化！）
- SQL 中某些函数不支持向量化（如自定义 UDF、正则表达式）
- Hive 2.3+ 支持向量化 GroupBy
- Hive 3.1+ 支持向量化 JOIN（有限支持）

### 6.3 Tez Grouping / 聚合优化

```sql
-- 启用 Tez Grouping（优化多级聚合）
SET hive.tez.auto.reducer.parallelism = true;
SET hive.tez.max.partition.factor = 2;
SET hive.tez.min.partition.factor = 0.25;

-- 将中间结果写入本地磁盘而非 HDFS
SET hive.optimize.union.remove = true;
SET hive.merge.tezfiles = true;

-- 小文件合并（Tez 输出）
SET hive.merge.mapfiles = true;
SET hive.merge.mapredfiles = true;
SET hive.merge.size.per.task = 268435456;  -- 256MB per task output
SET hive.merge.smallfiles.avgsize = 16777216;  -- 小于 16MB 的文件会合并
```

### 6.4 ORC 与文件格式选择

| 格式 | 压缩比 | 读取性能 | 写入性能 | 适用场景 |
|------|--------|----------|----------|----------|
| ORC | 极高（~75%） | 极快 | 中等 | 数仓分析、聚合查询（首选） |
| Parquet | 高（~65%） | 快 | 快 | Spark 交叉使用、列存场景 |
| Avro | 低 | 中等 | 快 | 数据摄取、行级更新场景 |
| Text | 无压缩 | 慢 | 快 | 临时数据、外部导入导出 |

```sql
-- 建表推荐配置（ORC + ZSTD 压缩）
CREATE TABLE <table_name> (
  col1 STRING,
  col2 INT
)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES (
  'orc.compress' = 'ZSTD',
  'orc.compress.size' = '65536',
  'orc.stripe.size' = '268435456',    -- 256MB per stripe
  'orc.row.index.stride' = '10000'
);
```

### 6.5 分区裁剪

```sql
-- 务必在 WHERE 中过滤分区键，避免全表扫描
-- 差（全表扫描 + 全量分区扫描）
SELECT * FROM orders WHERE order_date >= '2024-01-01';

-- 好（利用分区裁剪，快速定位分区）
SELECT * FROM orders WHERE dt >= '2024-01-01';

-- 查看执行计划确认分区裁剪生效
EXPLAIN SELECT * FROM orders WHERE dt = '2024-01-01';
-- 输出中应有 Partition Pruner 相关的信息
```

**分区数量建议**：
- 单表分区数 < 10,000（超过后 HMS 性能下降）
- 每天一个分区即可，避免按小时分区（除非数据量极大）
- 使用 `MSCK REPAIR TABLE` 定期同步元数据

### 6.6 执行计划解读

```sql
-- 查看执行计划
EXPLAIN <query>;

-- 查看详细执行计划（包含 Tez DAG 结构）
EXPLAIN EXTENDED <query>;

-- 查看带依赖关系的执行计划
EXPLAIN DEPENDENCY <query>;
```

**执行计划关键点**：

| 注意点 | 说明 |
|--------|------|
| `MapReduce` 出现 | 说明 Tez Vectorization 未生效 |
| `Reduce Sink` 行数 | 处于 Reduce 前的数据量，过大可能表示倾斜 |
| `TableScan` 的分区 | 确认分区裁剪是否生效 |
| `Join` 后的数据量 | 大表 join 小表应走 MapJoin（Stage-1 无 Reduce） |
| `Statistics` 行 | 查看 numRows / totalSize 是否准确（影响优化器决策） |

---

## 7. 快速诊断命令清单

```bash
# 1. 检查 HiveServer2 状态
sudo systemctl status hive-server2

# 2. 检查 MetaStore 状态
sudo systemctl status hive-metastore

# 3. 查看 Hive 日志
tail -100 /var/log/hive/hive-server2.log
tail -100 /var/log/hive/hive-metastore.log

# 4. 查看 Tez AM 日志
yarn application -list | grep -i tez
yarn logs -applicationId <app_id> | tail -300

# 5. 执行简单的 Hive 查询测试连通性
beeline -u "jdbc:hive2://localhost:10000/default" -e "SHOW DATABASES;"

# 6. 检查 HDFS 上表目录
hadoop fs -du -h /apps/hive/warehouse/<db>.db/<table>

# 7. 检查元数据表（MySQL 直连）
mysql -h<host> -u<hive_user> -p<pass> hive -e "
  SELECT tbl_name, t_id, create_time, last_access_time
  FROM TBLS
  ORDER BY last_access_time DESC
  LIMIT 20;
"
```

## 8. 常见问题速查表

| 问题 | 原因 | 解决 |
|------|------|------|
| SHOW TABLES 为空但 HDFS 有目录 | HMS 元数据未同步 | `MSCK REPAIR TABLE` |
| INSERT 报 `Dynamic partition strict mode` | 动态分区未配 nonstrict | `SET hive.exec.dynamic.partition.mode = nonstrict` |
| `SemanticException [Error 10072]` | 数据库不存在或无权限 | `SHOW DATABASES` 确认后 `GRANT` |
| Tez `Vertex failed` 无详细错误 | Tez 日志级别不够 | 设置 `tez.am.log.level=DEBUG` |
| `ParquetDecodingException` | ORC 与 Parquet 混淆 | 确认 `STORED AS` 与文件格式一致 |
| `Table not found` 但表存在 | 数据库前缀缺失 | 使用 `db.table` 全路径引用 |
| Query 一直卡在 Map 0% | Input split 超大 / 资源不足 | 检查 YARN 队列资源 + Container 数 |

## 注意事项

1. MSCK REPAIR TABLE 在大量分区表上耗时较长（10 万+ 分区可能数十分钟），建议在低峰期操作
2. ALTER TABLE REPLACE COLUMNS 会替换全量字段定义，而非逐字段操作，务必先备份 DDL
3. TEZ Container 内存设置需配合 YARN 配置：`yarn.scheduler.maximum-allocation-mb` 必须 >= `hive.tez.container.size`
4. Hive 3.x 中部分命令有变化（如 RECOVER PARTITIONS 替代 MSCK REPAIR TABLE 的部分功能）
5. Kerberos 环境下执行 Hive 查询前需先 `kinit` 获取有效的 service ticket
6. Desc Formatted 输出的 Location 带 `hdfs://` schema 时表示开启了 HDFS Federation 或 HA
7. SHOW CREATE TABLE 的输出可用于重建表，但外部表需特别注意 LOCATION 路径
