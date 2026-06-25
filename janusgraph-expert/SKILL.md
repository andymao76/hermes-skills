---
name: janusgraph-expert
description: JanusGraph 图数据库专家 — Gremlin 查询优化/索引管理/事务调优/运维
priority: normal
category: bigdata
---

# JanusGraph Expert — JanusGraph 图数据库专家

## 概述

JanusGraph 是一个可水平扩展的分布式图数据库，底层支持多种存储后端（HBase/Cassandra/BerkeleyJE）和索引后端（Elasticsearch/Solr）。本技能覆盖 Gremlin 查询优化、索引管理、事务调优及日常运维。

---

## 1. 核心 Gremlin 查询模式

### 1.1 基础遍历

```groovy
// 获取所有顶点
g.V()

// 获取所有边
g.E()

// 按 ID 查询
g.V('vertex-id')
g.E('edge-id')

// 按属性过滤
g.V().has('name', 'Alice')
g.V().has('age', gt(30))
g.V().hasLabel('person')

// 多条件过滤
g.V().has('name', 'Alice').has('age', 30)
g.V().hasLabel('person').has('city', 'Beijing')
```

### 1.2 遍历与路径

```groovy
// 邻居遍历
g.V().has('name', 'Alice').out('knows')
g.V().has('name', 'Alice').in('knows')
g.V().has('name', 'Alice').both('knows')

// 多跳遍历
g.V().has('name', 'Alice').out('knows').out('knows')      // 二度好友
g.V().has('name', 'Alice').repeat(out('knows')).times(3)   // 三度遍历

// tree() — 树形结构遍历
g.V().has('name', 'CEO').repeat(out('manages')).times(5).tree()
// 输出组织架构树

// tree().by(...) — 自定义树节点属性
g.V().has('name', 'CEO').repeat(out('manages')).times(5).tree().by('name')

// path() — 获取遍历路径
g.V().has('name', 'Alice').out('knows').out('knows').path()
// 返回 [v[Alice], v[Bob], v[Charlie]] 完整路径

// path().by(...) — 路径属性投影
g.V().has('name', 'Alice').out('knows').out('knows').path().by('name')
// 返回 [Alice, Bob, Charlie]
```

### 1.3 聚合与计算

```groovy
// 计数
g.V().count()
g.V().hasLabel('person').count()

// group().by()
g.V().hasLabel('person').group().by('city').by(count())
g.V().hasLabel('person').group().by('age').by(values('name').fold())

// 排序
g.V().hasLabel('person').order().by('age', desc)
g.V().hasLabel('person').order().by('age', desc).limit(10)

// 去重
g.V().out('knows').dedup()
g.V().values('city').dedup()

// 投影
g.V().has('name', 'Alice').project('name', 'friends')
  .by('name')
  .by(out('knows').count())
```

### 1.4 子图与过滤

```groovy
// 子图
subgraph = g.V().has('age', gt(18)).bothE().subgraph('adults').cap('adults').next()

// 组合过滤
g.V().where(out('knows').count().is(gte(5)))   // 好友 >= 5 的人
g.V().not(has('status', 'inactive'))            // 非 inactive 状态

// 属性存在性检查
g.V().has('email')                              // 有 email 属性的顶点
g.V().hasNot('phone')                           // 没有 phone 属性的顶点
```

---

## 2. 索引管理

JanusGraph 支持多种索引类型，正确使用索引是查询性能的关键。

### 2.1 Composite Index（复合索引）

用于**精确等值查询**，完全基于存储后端，无需外部索引后端。

```groovy
// 创建复合索引 — 单属性
mgmt = graph.openManagement()
nameIndex = mgmt.buildIndex('byName', Vertex.class)
  .addKey(mgmt.getPropertyKey('name'))
  .buildCompositeIndex()
mgmt.commit()

// 创建复合索引 — 多属性（联合索引，需要用 AND 组合）
mgmt = graph.openManagement()
nameAgeIndex = mgmt.buildIndex('byNameAndAge', Vertex.class)
  .addKey(mgmt.getPropertyKey('name'))
  .addKey(mgmt.getPropertyKey('age'))
  .buildCompositeIndex()
mgmt.commit()

// 唯一约束索引
mgmt = graph.openManagement()
uniqueIndex = mgmt.buildIndex('uniqueEmail', Vertex.class)
  .addKey(mgmt.getPropertyKey('email'))
  .unique()
  .buildCompositeIndex()
mgmt.commit()
```

**复合索引适用查询：**
```groovy
g.V().has('name', 'Alice')                    // ✅ 命中
g.V().has('name', 'Alice').has('age', 30)     // ✅ 命中（联合索引）
g.V().has('name', 'Alice').has('city', 'BJ')  // ❌ 不命中（city 不在索引中）
g.V().has('age', 30)                          // ❌ 不命中（需要 age 作为前缀键）
```

### 2.2 Mixed Index（混合索引）

支持**范围查询、全文搜索、模糊匹配**，需与 Elasticsearch 或 Solr 配合。

```groovy
// Elasticsearch 混合索引
mgmt = graph.openManagement()
mixedIndex = mgmt.buildIndex('mixedByNameAndAge', Vertex.class)
  .addKey(mgmt.getPropertyKey('name'), Mapping.TEXTSTRING.asParameter())    // 全文搜索
  .addKey(mgmt.getPropertyKey('age'), Mapping.DEFAULT.asParameter())
  .buildMixedIndex("search")
mgmt.commit()

// 文本索引 — 支持模糊和通配符
mgmt = graph.openManagement()
textIndex = mgmt.buildIndex('textSearch', Vertex.class)
  .addKey(mgmt.getPropertyKey('description'), Mapping.TEXT.asParameter())  // TEXT 支持全文搜索
  .buildMixedIndex("search")
mgmt.commit()
```

**混合索引适用查询：**
```groovy
// 范围查询
g.V().has('age', between(20, 40))
g.V().has('age', gte(18)).has('age', lte(60))

// 文本搜索
g.V().has('description', textContains('machine learning'))
g.V().has('description', textContainsFuzzy('algorith'))
g.V().has('name', textContainsRegex('Ali.*'))

// 取反
g.V().has('name', textNotContains('test'))
g.V().has('age', without(0, -1))
```

### 2.3 Edge Index（边索引）

```groovy
// 边属性索引
mgmt = graph.openManagement()
edgeIndex = mgmt.buildIndex('edgesByWeight', Edge.class)
  .addKey(mgmt.getPropertyKey('weight'))
  .buildMixedIndex("search")
mgmt.commit()

// 边标签上的属性索引
mgmt = graph.openManagement()
edgeLabelIndex = mgmt.buildIndex('edgesByKnowsDate', Edge.class)
  .addKey(mgmt.getPropertyKey('since'))
  .indexOnly(mgmt.getEdgeLabel('knows'))
  .buildMixedIndex("search")
mgmt.commit()
```

### 2.4 索引管理命令

```groovy
// 查看所有索引
mgmt = graph.openManagement()
mgmt.getGraphIndexes(Vertex.class).each { println it.name }
mgmt.getGraphIndexes(Edge.class).each { println it.name }

// 查看索引详情
mgmt = graph.openManagement()
idx = mgmt.getGraphIndex('byName')
println idx.name
println idx.backingIndex       // internal (Composite) / search (Mixed)
println idx.fieldKeys
println idx.indexOnlyConstraint

// 索引状态检查
mgmt = graph.openManagement()
idx = mgmt.getGraphIndex('byName')
idx.getIndexStatus(mgmt.getPropertyKey('name'))
// 返回: ENABLED / REGISTERED / INSTALLED / DISCARDED

// 等待索引生效（异步操作）
mgmt.awaitGraphIndexStatus(graph, 'byName').status(SchemaStatus.ENABLED).call()

// 删除索引
mgmt = graph.openManagement()
idx = mgmt.getGraphIndex('byName')
mgmt.dropIndex(idx)
mgmt.commit()
```

### 2.5 索引命中检查

```groovy
// 使用 profile() 检查索引是否命中
g.V().has('name', 'Alice').profile()

// 输出中查找：
//   Traversal Metrics
//   Step Count  Traversers  Time (ms)  % Dur
//   JanusGraphStep([name.eq(Alice)])  →  查询条件
//     condition=name.eq(Alice)
//     orders=[]
//     isFitted=true              ← 关键！true=索引命中
//     isOrdered=true
//     query=[]
//     indices=[byName]           ← 命中的索引名称
//     backend-query=...

// 使用 explain() 查看查询计划
g.V().has('name', 'Alice').explain(true)
```

---

## 3. Gremlin 性能分析

### 3.1 profile() — 性能剖析

```groovy
// 基本用法
g.V().has('name', 'Alice').out('knows').profile()

// 输出解读：
// Traversal Metrics
// Step                                                               Count  Traversers       Time (ms)    % Dur
// -------------------------------------------------------------------------------------------------------------
// JanusGraphStep([name.eq(Alice)])@1                                   1           1         235.560    40.32  ← 这里慢
//   \\ condition=name.eq(Alice)
//   \\ indices=[byName]                                                   ← 索引已命中
//   \\ backend-query=...                                                 ← 后端耗时
// JanusGraphVertexStep(OUT,[knows])@2                                   5           5         348.390    59.68  ← 边遍历
//   \\ condition=VERTEX
//   \\ backend-query=...
//       >TOTAL                     -           -         583.950        -
```

**profile() 关键指标：**
| 指标 | 说明 | 阈值 |
|------|------|------|
| `Time(ms)` | 该步骤耗时 | 单步 > 1000ms 需优化 |
| `% Dur` | 耗时占比 | 某步 > 50% 为重点优化对象 |
| `isFitted` | 是否命中索引 | false 表示全表扫描 |
| `Count` | 遍历的元素数 | 大量数据无过滤是危险信号 |
| `backend-query` | 后端查询详情 | 检查 HBase/Cassandra 响应时间 |

### 3.2 explain() — 查询计划

```groovy
// 查看查询计划（不实际执行）
g.V().has('name', 'Alice').out('knows').explain(true)

// 输出显示优化器如何重写查询
// 举例：条件下推、索引选择、遍历策略
```

### 3.3 遍历优化策略

**策略 1：尽早过滤（下推谓词）**
```groovy
// ❌ 低效 — 先遍历再过滤
g.V().out('knows').has('age', gt(18))

// ✅ 高效 — 先过滤再遍历
g.V().has('age', gt(18)).out('knows')
```

**策略 2：使用 hasStep 替代 where**
```groovy
// ✅ 推荐 — has() 可以利用索引
g.V().has('name', 'Alice')

// ❌ 避免 — where 可能无法利用索引
g.V().where(values('name').is('Alice'))
```

**策略 3：order + range 优化**
```groovy
// 大量排序时使用 range() 限制数据量
g.V().hasLabel('person').order().by('age', desc).range(0, 20)

// 注意：order().range() 可能在内存中排序全部数据
// 建议在 Mixed Index 中用 Elasticsearch 排序（指定 sort 参数）

// 使用 localLimit 替代 limit（性能更好）
g.V().localLimit(100)
```

**策略 4：避免重复遍历**
```groovy
// ❌ 重复计算
g.V().has('name', 'Alice')
  .out('knows').has('age', gt(18))

// ✅ 使用 sideEffect 缓存中间结果
g.V().has('name', 'Alice').fold()
  .unfold().out('knows').has('age', gt(18))
```

**策略 5：batchSize 调优**
```groovy
// 调整每次从后端读取的批大小
graph.tx().readWrite()  // 确认事务是否活跃

// 在 Gremlin Server 配置中调整
// gremlin.graph.janusgraph-optimizer.batch-size = 100
```

---

## 4. 事务管理

### 4.1 基本事务操作

```groovy
// 自动事务（ThreadedTransactionalGraph）
graph.tx().commit()    // 提交
graph.tx().rollback()  // 回滚

// 检查事务状态
graph.tx().isOpen()

// 检查事务是否有未提交更改
graph.tx().hasChanges()

// 读取时创建新事务
traversal = graph.tx().createThreadedTx().traversal()
```

### 4.2 事务最佳实践

```groovy
// ✅ 正确 — 批量写入时定期提交
for (i in 0..10000) {
  vertex = graph.addVertex(T.label, 'person', 'name', "user_${i}")
  if (i % 1000 == 0) {
    graph.tx().commit()  // 每 1000 条提交一次
  }
}
graph.tx().commit()

// ❌ 错误 — 大量写入后不提交
for (i in 0..100000) {
  graph.addVertex(...)
}
// 不提交会导致 OOM，所有修改在内存中累积

// ✅ 正确 — 失败时回滚
try {
  vertex = graph.addVertex(...)
  // ... 操作 ...
  graph.tx().commit()
} catch (Exception e) {
  println "Error: ${e.message}"
  graph.tx().rollback()  // 清理脏数据
}
```

### 4.3 事务与查询

```groovy
// 查询事务隔离
g.tx().isOpen()  // 只读事务默认不开启

// 手动开启事务后执行查询
g.V().has('name', 'Alice').next()  // 自动事务
// 后续修改操作在同一个事务中

// 大型查询使用 separate thread tx
tx = graph.newTransaction()
try {
  v = tx.traversal().V().has('name', 'Alice').next()
  // ... 操作 ...
  tx.commit()
} catch (Exception e) {
  tx.rollback()
} finally {
  tx.close()
}
```

### 4.4 超时设置

```groovy
// 全局超时（在 janusgraph-server.yaml 中）
// host: 0.0.0.0
// evaluationTimeout: 30000  ← 毫秒

// 或通过 graph configuration
graph.tx().commit()  // 隐含了 transaction timeout 检查

// 在配置文件中：
// storage.lock.wait-time = 10000         # 锁等待超时（毫秒）
// ids.block-size = 10000                 # ID 块大小
// query.evaluate-timeout = 30000         # 查询超时（毫秒）
// query.fast-property = true
```

---

## 5. 运维命令

### 5.1 JanusGraph Server 管理

```bash
# 启动 JanusGraph Server
janusgraph.sh start

# 停止
janusgraph.sh stop

# 查看状态
janusgraph.sh status

# 查看进程列表
ps aux | grep janusgraph

# 日志文件位置
# $JANUSGRAPH_HOME/log/janusgraph.log
# $JANUSGRAPH_HOME/log/server.log

# 实时查看日志
tail -f $JANUSGRAPH_HOME/log/janusgraph.log
tail -f $JANUSGRAPH_HOME/log/gremlin-server.log
```

### 5.2 Gremlin Server 控制台

```bash
# 启动 Gremlin 控制台
bin/gremlin.sh

# 在控制台中连接远程服务器
:remote connect tinkerpop.server conf/remote.yaml

# 切换到远程模式
:remote console

# 发送查询
g.V().count()

# 退出控制台
:exit
```

### 5.3 配置文件位置

| 配置项 | 默认路径 | 说明 |
|--------|----------|------|
| janusgraph.sh 配置 | `conf/janusgraph.sh.env` | 环境变量，JAVA_OPTIONS |
| 图配置 | `conf/janusgraph-${backend}.properties` | 存储后端、索引后端配置 |
| Gremlin Server | `conf/gremlin-server.yaml` | 端口、超时、线程池 |
| 远程连接 | `conf/remote.yaml` | Gremlin Console 远程连接配置 |
| 日志 | `conf/log4j-server.properties` | 日志级别和输出 |

---

## 6. 后端存储检查

### 6.1 HBase 后端

```bash
# 检查 HBase 表
echo "list" | hbase shell | grep janusgraph

# JanusGraph 默认创建的表：
#   janusgraph (EDGESTORE)
#   janusgraph_idstore (IDSTORE)
#   janusgraph_graphindex_ts (TITAN_INDEXSTORE)

# 检查 RegionServer 状态
echo "status 'detailed'" | hbase shell

# HDFS 存储使用
hdfs dfs -du -h /hbase/data/default/janusgraph
```

### 6.2 Cassandra 后端

```bash
# 连接 CQLSH
cqlsh

# 查看键空间
DESC KEYSPACES;

# JanusGraph 默认键空间：janusgraph
USE janusgraph;
DESC TABLES;

# 主要表：
#   edgestore
#   graphindex
#   system_properties
#   systemlog
#   txlog

# 查看表大小（约）
SELECT keyspace_name, table_name, 
  round(sum(mean_partition_size) / 1024, 2) as size_kb
FROM system.size_estimates
WHERE keyspace_name = 'janusgraph';
```

### 6.3 BerkeleyJE 后端

```bash
# BerkeleyJE 是嵌入式后端，数据文件在配置的目录
ls -lh /path/to/berkeleydb/
#   je.lck              — 锁文件
#   00000000.jdb        — 数据文件
#   je.config.csv       — JE 配置导出

# 使用 db_dump 工具查看（需 je.jar）
# java -jar je.jar DbDump -h /path/to/berkeleydb/
```

---

## 7. 常见问题排查

### 7.1 索引未命中导致全表扫描

**现象：** 查询非常缓慢，profile() 显示 `isFitted=false`

**排查步骤：**
```groovy
// 1. 检查索引是否存在
mgmt = graph.openManagement()
mgmt.getGraphIndexes(Vertex.class).each { idx ->
  println "Index: ${idx.name}, Type: ${idx.backingIndex}"
  idx.fieldKeys.each { key ->
    status = idx.getIndexStatus(key)
    println "  Key: ${key.name}, Status: ${status}"
  }
}

// 2. 检查索引状态是否为 ENABLED
// 如果状态为 REGISTERED 或 INSTALLED，需要等待或重新索引

// 3. 确认查询条件与索引键匹配
// 复合索引需要等值条件完全匹配索引键前缀

// 4. 对于重新打开已有图的索引，可能需要重建
mgmt = graph.openManagement()
mgmt.updateIndex(mgmt.getGraphIndex('byName'), SchemaAction.REINDEX).get()
mgmt.commit()
```

### 7.2 查询超时

**现象：** `java.util.concurrent.TimeoutException` 或 `ScriptTimeoutException`

**解决方法：**
```groovy
// 方法 1：增加超时时间（在 gremlin-server.yaml 中）
// evaluationTimeout: 60000  // 增加到 60 秒

// 方法 2：在查询前设置（仅当前脚本有效）
graph.configuration().setProperty('query.evaluate-timeout', 60000)

// 方法 3：分解大查询
// 不要一次查全部，分批查询
batch = g.V().hasLabel('person').fold().next()
batch.collate(1000).each { chunk ->
  chunk.each { v ->
    // 处理每个顶点
  }
}
```

### 7.3 事务冲突与死锁

**现象：** `StorageException: Lock wait timeout exceeded`

**原因：** 并发写入相同数据时锁竞争

**解决方法：**
```groovy
// 1. 减小事务粒度
// 将大批量写入拆分为小批次

// 2. 调整锁超时（在 properties 中）
// storage.lock.wait-time = 5000       # 减小等待时间
// storage.lock.retry-count = 10       # 重试次数

// 3. 使用悲观锁或乐观锁（取决于后端）
// HBase: 默认使用悲观锁
// Cassandra: 使用轻量级事务

// 4. 避免跨分区事务（HBase）
// 尽量让相关数据在相同的 row key 范围内
```

### 7.4 OLTP vs OLAP 模式选择

| 维度 | OLTP（联机事务处理） | OLAP（联机分析处理） |
|------|---------------------|---------------------|
| **查询类型** | 短查询，毫秒~秒级 | 长查询，秒~分钟级 |
| **数据量** | 单个/少量顶点 | 全图扫描 |
| **索引要求** | 必须命中索引 | 可全表扫描 |
| **典型操作** | `g.V().has('name','A').out()` | `g.V().both().groupCount()` |
| **执行引擎** | JanusGraph 内置 | SparkGraphComputer |
| **事务模式** | 自动事务 | 只读快照 |
| **建议** | `query.evaluate-timeout=30000` | 使用 Spark OLAP 模式单独集群 |

**OLAP 配置示例：**
```groovy
// SparkGraphComputer 配置
// 需要部署 Spark 集群并配置 spark-hadoop 连接
graph.compute(SparkGraphComputer.class)
  .vertices(g.V().hasLabel('person'))
  .program(PageRankVertexProgram.build().create(graph))
  .submit()
  .get()
```

### 7.5 ID Block 耗尽

**现象：** `IDPoolExhaustedException`

**解决方法：**
```groovy
// 查看当前 ID 分配情况
mgmt = graph.openManagement()
mgmt.getOpenInstances()  // 查看实例
mgmt.getPropertyKey('id')  // ID 相关属性

// 增加 ID 块大小（在 properties 中）
// ids.block-size = 50000      # 默认 10000，增大可减少 ID 竞争
// ids.renew-timeout = 60000   # ID 续租超时
```

---

## 8. 存储后端对比

| 维度 | HBase | Cassandra | BerkeleyJE |
|------|-------|-----------|------------|
| **部署方式** | 分布式（依赖 HDFS+ZK） | 分布式（P2P） | 嵌入式（单机） |
| **一致性** | 强一致性（CP） | 最终一致性（AP） | 强一致性 |
| **容错性** | GA + HDFS 副本 | Gossip + 副本因子 | 无容错 |
| **写入吞吐** | 中等（受 HDFS 延迟影响） | 高 | 极高 |
| **OLTP 查询** | 优秀（row key 范围查询） | 优秀（分区键查询） | 极优 |
| **全局遍历** | 慢（需要 scan） | 中等 | 快 |
| **事务支持** | 乐观锁 + 行锁 | 轻量级事务（LWT） | 完整 ACID |
| **运维复杂度** | 高（HDFS+ZK+HBase） | 中等 | 低 |
| **推荐场景** | 生产环境，大集群 | 高可用多机房 | 学习/开发/测试 |
| **配置示例** | `storage.backend=hbase` | `storage.backend=cassandra` | `storage.backend=berkeleyje` |
| | `storage.hostname=zk1,zk2` | `storage.hostname=192.168.1.1` | `storage.directory=/data/janusgraph` |

### 存储后端配置模板

**HBase 配置：**
```properties
storage.backend=hbase
storage.hostname=zk1.example.com,zk2.example.com,zk3.example.com
storage.hbase.table=janusgraph
storage.hbase.ext.zookeeper.znode.parent=/hbase

index.search.backend=elasticsearch
index.search.hostname=es1.example.com,es2.example.com
index.search.elasticsearch.client-only=true
index.search.elasticsearch.index-name=janusgraph_index
```

**Cassandra 配置：**
```properties
storage.backend=cassandra
storage.hostname=192.168.1.10,192.168.1.11,192.168.1.12
storage.cassandra.keyspace=janusgraph
storage.cassandra.replication-factor=3
storage.cassandra.read-consistency-level=LOCAL_QUORUM
storage.cassandra.write-consistency-level=LOCAL_QUORUM

index.search.backend=elasticsearch
index.search.hostname=es1.example.com
```

**BerkeleyJE 配置：**
```properties
storage.backend=berkeleyje
storage.directory=/var/lib/janusgraph/data

# BerkeleyJE 不支持外部索引，使用 internal 索引
index.search.backend=elasticsearch
index.search.hostname=localhost
```

---

## 9. Elasticsearch 索引维护

### 9.1 基本操作

```bash
# 查看 JanusGraph 在 ES 中的索引
curl -X GET "http://localhost:9200/_cat/indices?v" | grep janusgraph

# 查看索引映射
curl -X GET "http://localhost:9200/janusgraph_index/_mapping?pretty"

# 查看索引设置
curl -X GET "http://localhost:9200/janusgraph_index/_settings?pretty"
```

### 9.2 索引重建（Reindex）

```bash
# 场景 1：在 JanusGraph 中触发 REINDEX
# 当添加新索引或修改现有索引时
mgmt = graph.openManagement()
mgmt.updateIndex(mgmt.getGraphIndex('myNewIndex'), SchemaAction.REINDEX).get()

# 场景 2：ES 内部 reindex（转移数据）
curl -X POST "http://localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "janusgraph_index_v1"
  },
  "dest": {
    "index": "janusgraph_index_v2"
  }
}'
```

### 9.3 Mapping 更新

```groovy
// JanusGraph 使用 schema 管理 mapping，不直接在 ES 修改
// 正确的做法是通过 ManagementSystem 修改

// 添加新的属性并映射到 ES
mgmt = graph.openManagement()
newProp = mgmt.makePropertyKey('new_field').dataType(String.class).make()
mixedIndex = mgmt.getGraphIndex('mixedSearch')
mgmt.addIndexKey(mixedIndex, newProp, Mapping.TEXTSTRING.asParameter())
mgmt.commit()

// 等待索引状态
mgmt.awaitGraphIndexStatus(graph, 'mixedSearch').status(SchemaStatus.ENABLED).call()

// 重新索引现有数据
mgmt = graph.openManagement()
mgmt.updateIndex(mgmt.getGraphIndex('mixedSearch'), SchemaAction.REINDEX).get()
mgmt.commit()
```

### 9.4 ES 性能调优

```bash
# 刷新间隔（频繁写入时调大）
curl -X PUT "http://localhost:9200/janusgraph_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "refresh_interval": "30s"
  }
}'

# 副本数
curl -X PUT "http://localhost:9200/janusgraph_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "number_of_replicas": 1
  }
}'

# 分片数（创建时设置，不可更改）
# index.search.elasticsearch.create.ext.number_of_shards=5
```

### 9.5 Mixed Index 故障排查

```groovy
// 检查 Mixed Index 状态
mgmt = graph.openManagement()
idx = mgmt.getGraphIndex('mixedSearch')
println "Index backend: ${idx.backingIndex}"  // 应为 "search"
idx.fieldKeys.each { key ->
  println "Key: ${key.name}, Mapping: ${key.mapping}, Status: ${idx.getIndexStatus(key)}"
}

// 确保 ES 索引名正确
// 默认索引名前缀：janusgraph_index
// 对应 ES index: janusgraph_index
// 可通过以下配置更改：
// index.search.elasticsearch.index-name=my_custom_index
```

---

## 10. 配置最佳实践

### 10.1 生产环境推荐配置

```properties
# janusgraph-hbase-es.properties

# 存储后端
storage.backend=hbase
storage.hostname=zk1,zk2,zk3
storage.hbase.table=janusgraph

# ID 分配
ids.block-size=50000
ids.renew-timeout=600000

# 缓存
cache.db-cache=true
cache.db-cache-clean-wait=20
cache.db-cache-time=180000
cache.db-cache-size=0.5

# 查询
query.evaluate-timeout=30000
query.fast-property=true

# 索引后端
index.search.backend=elasticsearch
index.search.hostname=es1,es2,es3
index.search.elasticsearch.client-only=true
index.search.elasticsearch.index-name=janusgraph_index
index.search.elasticsearch.create.ext.number_of_shards=5
index.search.elasticsearch.create.ext.number_of_replicas=1

# 事务
storage.lock.wait-time=10000
storage.lock.retry-count=10

# 存储后端特定
storage.hbase.ext.hbase.client.connection.impl=org.apache.hadoop.hbase.client.ConnectionFactory
storage.hbase.ext.hbase.client.retries.number=3
```

### 10.2 Gremlin Server 配置

```yaml
# conf/gremlin-server.yaml
host: 0.0.0.0
port: 8182
evaluationTimeout: 30000
channelizer: org.apache.tinkerpop.gremlin.server.channel.WsAndHttpChannelizer
graphManager: org.janusgraph.graphdb.management.JanusGraphManager
graphs:
  graph: conf/janusgraph-hbase-es.properties
scriptEngines:
  gremlin-groovy:
    plugins:
      org.janusgraph.graphdb.tinkerpop.plugin.JanusGraphGremlinPlugin: {}
      org.apache.tinkerpop.gremlin.server.jsr223.GremlinServerGremlinPlugin: {}
      org.apache.tinkerpop.gremlin.tinkergraph.jsr223.TinkerGraphGremlinPlugin: {}
      org.apache.tinkerpop.gremlin.jsr223.ExecutorScriptEngine: {}
serializer:
  - className: org.apache.tinkerpop.gremlin.driver.ser.GraphBinaryMessageSerializerV1
  - className: org.apache.tinkerpop.gremlin.driver.ser.GraphSONMessageSerializerV3
processors:
  - className: org.apache.tinkerpop.gremlin.server.op.session.SessionOpProcessor
    config:
      sessionTimeout: 300000
  - className: org.apache.tinkerpop.gremlin.server.op.traversal.TraversalOpProcessor
    config:
      cacheExpirationTime: 600000
      cacheMaxSize: 10000
metrics:
  consoleReporter:
    enabled: true
    interval: 180000
```

---

## 11. 故障排查速查表

| 症状 | 可能原因 | 排查命令 | 修复 |
|------|----------|----------|------|
| 查询极慢 | 索引未命中 | `profile()` 查看 `isFitted` | 创建/重建索引 |
| 查询超时 | `evaluationTimeout` 太小 | 检查 gremlin-server.yaml | 增大 timeout |
| 写入失败 | 事务冲突/锁超时 | `graph.tx().hasChanges()` | `tx.rollback()` 重试 |
| 连接拒绝 | Server 未启动 | `janusgraph.sh status` | `janusgraph.sh start` |
| ID 耗尽 | `ids.block-size` 太小 | 日志中搜 `IDPoolExhausted` | 增大 block size |
| ES 查询失败 | Mixed Index 配置错误 | `curl ES health` | 检查 ES 连通性 |
| OOM | 事务未提交 | `graph.tx().isOpen()` | 定期 `tx.commit()` |
| Schema 冲突 | 并发 Schema 修改 | 同一实例避免并发 mgmt | 串行化 Schema 变更 |
| Cassandra 超时 | 一致性级别太高 | `nodetool tpstats` | 降低 read/write CL |
| HBase Region 过热 | 热点 Region | `hbase hbck` | 预分区 / 散列 row key |

---

## 12. 快速参考命令

### 项目参考文件
本 skill 包含项目特定参考文件，加载后按需查看：

| 文件 | 说明 |
|------|------|
| `references/a1-project-gremlin.md` | A1 项目(苏丹) JanusGraph 数据模型、查询模式、运维命令 |

```bash
# ---- Server 管理 ----
janusgraph.sh start
janusgraph.sh stop
janusgraph.sh status
tail -f log/janusgraph.log

# ---- Gremlin Console ----
bin/gremlin.sh
:remote connect tinkerpop.server conf/remote.yaml
:remote console

# ---- 后端检查（HBase）----
echo "list" | hbase shell | grep janusgraph
echo "status 'detailed'" | hbase shell

# ---- 后端检查（Cassandra）----
cqlsh -e "DESC KEYSPACES;"
cqlsh -e "USE janusgraph; DESC TABLES;"

# ---- ES 索引检查 ----
curl localhost:9200/_cat/indices?v
curl localhost:9200/janusgraph_index/_mapping?pretty

# ---- 进程和端口 ----
ss -tlnp | grep 8182           # Gremlin Server 端口
ss -tlnp | grep 9200           # ES HTTP 端口
ps aux | grep janusgraph
```

---

## 注意事项

1. **索引是查询的命脉** — 始终使用 `profile()` 确认索引命中
2. **事务要短小** — 大批量操作定期 `commit()`，避免 OOM
3. **Schema 变更需谨慎** — 生产环境 Schema 变更在维护窗口执行
4. **复合索引 vs 混合索引** — 精确等值用 Composite，范围/文本用 Mixed
5. **OLTP ≠ OLAP** — 短查询务必命中索引，全图扫描走 Spark OLAP
6. **HBase 后端** — row key 设计决定查询性能，避免热点
7. **Cassandra 后端** — 分区键设计影响跨分区查询效率
8. **BerkeleyJE** — 仅用于单机/开发/测试，不支持分布式
9. **ES Mapping** — 不直接修改 ES mapping，通过 JanusGraph ManagementSystem 变更
10. **版本兼容性** — 注意 JanusGraph 与 HBase/Cassandra/ES 的版本匹配
