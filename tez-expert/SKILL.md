---
name: tez-expert
description: Tez 执行引擎专家 — DAG 分析/Container 诊断/性能调优/Hive on Tez 排障
priority: normal
category: bigdata
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bigdata, tez, hive, dag, yarn, container, shuffle, performance]
    related_skills: [yarn-expert, hdfs-ops, hive-ops]
---

# Tez Expert — Tez 执行引擎专家

## 适用场景

Tez 执行引擎出现以下问题时触发：

- **DAG 执行缓慢**：某个 Stage 耗时异常高，整体作业延迟
- **Container 反复失败**：Container 被 Kill / OOM / 异常退出导致任务重试
- **数据倾斜（Data Skew）**：部分 Task 处理大量数据，其他 Task 空闲
- **OOM**：Task/AM 内存不足，OutOfMemoryError
- **Shuffle 性能瓶颈**：Shuffle 阶段耗时占整个 DAG 的 70%+
- **Hive on Tez 查询慢**：SQL 语句使用 Tez 执行引擎但性能不如 MR

## 核心诊断命令速查

```bash
# 查看 Tez 应用列表（YARN 角度）
yarn application -list | grep -i tez

# 查看 Tez 应用详情
yarn application -status <application_id>

# 查看 Tez 应用聚合日志
yarn logs -applicationId <application_id> | less

# 查看特定 Container 日志
yarn logs -applicationId <application_id> -containerId <container_id>

# Tez 自带诊断工具（如果在 PATH 中）
tez top                          # 实时查看 Tez DAG 执行状态
tez top -session                 # 监控 Tez Session
tez log --metrics                # 打印 Tez 运行指标

# Tez UI 访问（如已部署）
echo "http://<tez-ui-host>:<port>/tez-ui/"
```

---

## 一、Tez DAG 结构理解

### 1.1 DAG 核心概念

| 概念 | 说明 | 对应 Hive 场景 |
|------|------|---------------|
| **DAG** | 有向无环图，Tez 执行计划的基本单位 | 一个 Hive 查询 = 一个 DAG |
| **Vertex** | DAG 中的计算节点/阶段 | Map / Reduce / Union / Join 等 |
| **Edge** | Vertex 之间的数据连接 | Shuffle / Broadcast / OneToOne |
| **Task** | Vertex 的一个并行执行单元 | 一个 Map Task / Reduce Task |
| **Processor** | Task 内部的实际计算逻辑 | Hive 的 HiveSplitGenerator 等 |

### 1.2 Edge 类型与数据传递方式

| Edge 类型 | 数据传递方式 | 使用场景 |
|-----------|-------------|---------|
| **SHUFFLE** | 分区后通过网络传输 | Reduce Join / Group By |
| **BROADCAST** | 全量复制到所有下游 Task | Map Join (小表) |
| **ONE_TO_ONE** | 上游 Task i 直连下游 Task i | Union / Filter-Project |
| **CUSTOM_EDGE** | 用户自定义 | 特殊计算逻辑 |

### 1.3 Tez DAG 生命周期

```
SUBMITTED → INITING → RUNNING → SUCCEEDED / FAILED / KILLED / ERROR
```

通过 `yarn application -status <app_id>` 查看 DAG 的当前状态。

---

## 二、Container 反复失败诊断

### 2.1 查看 Container 退出原因

```bash
# 获取应用诊断信息
yarn application -status <application_id> | grep -E "Diagnostics|State|Final-State"

# 查看失败 Task 列表
yarn logs -applicationId <application_id> 2>/dev/null | \
  grep -iE "failed|killed|error|exception|outofmemory" | tail -100
```

### 2.2 常见 Container 失败原因

| Exit Code | 含义 | Tez 典型原因 |
|-----------|------|-------------|
| **137** | SIGKILL — OOM Killer | Task 物理内存超过 container 限制 |
| **143** | SIGTERM — 正常终止 | AM 正常退出或被 YARN 回收 |
| **-1000** | Container 被抢占 | 高优先级作业抢占 Tez Container |
| **-100** | vmem 超限 | 虚拟内存超过 yarn.nodemanager.vmem-pmem-ratio 限制 |
| **-103** | pmem 超限 | 物理内存超过 yarn.nodemanager.resource.memory-mb |
| **1** | Java 异常 | Tez/Hive 代码未捕获异常，查看 stderr |

### 2.3 AM Container 反复重启

```bash
# 查看 AM 重启次数和原因
yarn application -status <application_id> | grep -i attempt

# 常见原因
# 1. AM 内存不足 → 增大 tez.am.resource.memory.mb
# 2. AM 所在节点故障 → 启用 AM 重试 tez.am.max.app.attempts
# 3. AM 初始化超时 → 增大 tez.am.am-robustness.heartbeat-delay
```

### 2.4 修复策略汇总

```yaml
# Container 反复失败修复模板

# 1. OOM / 内存不足
# 增大 Container 内存
hive.tez.container.size: 4096        # 从 2048 调大
tez.task.resource.memory.mb: 4096    # 与 container.size 保持一致

# 2. vmem 超限误杀
# 增大虚拟内存比率
yarn.nodemanager.vmem-pmem-ratio: 4  # 从默认 2.1 调大到 4

# 3. AM 不稳定
tez.am.resource.memory.mb: 2048      # 增大 AM 内存
tez.am.max.app.attempts: 4           # 增加重试次数

# 4. 日志查看详细原因
yarn logs -applicationId <app_id> -containerId <container_id> | grep -A 20 "Exception"
```

---

## 三、数据倾斜（Data Skew）诊断

### 3.1 数据倾斜识别

```bash
# Tez UI 中观察以下现象
# 1. 同 Vertex 下部分 Task 耗时远超平均（如 5min vs 30min）
# 2. Shuffle 数据量分布不均，某个 Task 处理 90%+ 数据
# 3. 进度条卡在 99% 很久（最后几个 Reduce Task 迟迟不结束）

# 命令行查看 DAG 各 Task 执行时间
tez top -session 2>/dev/null || echo "tez top 仅在 Tez 5.x+ 可用"
```

### 3.2 常见倾斜场景与修复

| 场景 | SQL 特征 | 修复方法 |
|------|---------|---------|
| **Group By 倾斜** | `GROUP BY col` 中某些值占比极高 | 启用倾斜优化：`hive.groupby.skewindata=true` |
| **Join 倾斜** | `JOIN ON key` 中某些 key 数据量极大 | 开启倾斜 Join：`hive.optimize.skewjoin=true` |
| **Count Distinct 倾斜** | `COUNT(DISTINCT col)` 对高基数字段 | 改用双层 GROUP BY + SUM |
| **Map Join 小表过大** | 小表超出内存限制 | 增大 `hive.auto.convert.join.noconditionaltask.size` |

### 3.3 倾斜调优参数

```sql
-- Hive on Tez 倾斜优化配置

-- Group By 倾斜优化
SET hive.groupby.skewindata=true;
-- 原理：先对 key 加随机前缀打散，再去除前缀聚合

-- Join 倾斜优化
SET hive.optimize.skewjoin=true;
SET hive.skewjoin.key=100000;
-- 当某个 key 的记录数超过 skewjoin.key 时，走倾斜处理逻辑

-- Map Join 内存控制
SET hive.auto.convert.join=true;
SET hive.auto.convert.join.noconditionaltask=true;
SET hive.auto.convert.join.noconditionaltask.size=512000000;  -- 512MB

-- 如果小表超过阈值但依然想用 Map Join
SET hive.mapjoin.smalltable.filesize=1024000000;  -- 1GB
```

---

## 四、OOM 诊断与修复

### 4.1 Tez OOM 类型

| OOM 类型 | 现象 | 根因 |
|----------|------|------|
| **Java Heap OOM** | `java.lang.OutOfMemoryError: Java heap space` | Task heap 不足 |
| **Direct Memory OOM** | `OutOfMemoryError: Direct buffer memory` | 直接内存 (Shuffle 缓冲区) 不足 |
| **GC Overhead** | `GC overhead limit exceeded` | GC 占用 >98% 时间 |
| **Container Kill (pmem)** | Exit Code -103 | 物理内存超过 Container 上限 |
| **Container Kill (vmem)** | Exit Code -100 | 虚拟内存超限 |

### 4.2 OOM 诊断命令

```bash
# 1. 查看是否 OOM
yarn logs -applicationId <application_id> | grep -i "OutOfMemoryError\|Java heap\|GC overhead"

# 2. 查看实际内存使用
# 从 RM UI 或 REST API
curl -s "http://<rm-host>:8088/ws/v1/cluster/apps/<application_id>" | \
  python -c "import sys,json;d=json.load(sys.stdin)['app'];print(f'memorySeconds={d.get(\"memorySeconds\")}, vcoreSeconds={d.get(\"vcoreSeconds\")}')"

# 3. 查看 GC 状态（SSH 到 NM 所在节点）
dmesg | grep -i "killed process" | tail -5

# 4. 开启 GC 日志
# 在 tez-env.sh 中添加：
# export TEZ_OPTS="-XX:+PrintGCDetails -XX:+PrintGCTimeStamps -Xloggc:/tmp/tez-gc.log"
```

### 4.3 OOM 修复策略

```yaml
# OOM 修复方案

# 方案一：增大 Container 内存（最直接）
tez.task.resource.memory.mb: 4096    # Java heap (-Xmx)
hive.tez.container.size: 4096        # Container 总内存（heap + overhead）
tez.task.launch.cmd-opts: "-Xmx3072m"  # 如果默认 Xmx 不足

# 方案二：增大 Tez AM 内存
tez.am.resource.memory.mb: 2048

# 方案三：优化 shuffle 缓冲区内存
tez.runtime.io.sort.mb: 256          # Shuffle 排序缓冲区
tez.runtime.unordered.output.buffer.size-mb: 128

# 方案四：降低并行度减少单 Task 负载
hive.tez.auto.reducer.parallelism: true
hive.tez.max.partition.factor: 16
hive.tez.min.partition.factor: 0.25
tez.grouping.min-size: 16777216      # 16MB，分组最小大小
tez.grouping.max-size: 1073741824    # 1GB，分组最大大小

# 方案五：调整 overhead（JVM 额外开销）
# Container Size = java heap + overhead
# overhead = max(0.2*heap, 384MB) 默认
# 可显式指定
hive.tez.java.opts: "-Xmx3072m"      # 使 heap 为 3072M，overhead 自动计算
```

---

## 五、Shuffle 性能瓶颈诊断

### 5.1 Shuffle 阶段分析

Shuffle 是 Tez 中最常见的性能瓶颈。理想情况下 Shuffle 时间不应超过总 DAG 时间的 30%。

```bash
# 在 Tez UI 中查看 Shuffle 指标
# 1. 点击对应 Vertex → 查看 Shuffle 阶段耗时
# 2. Shuffle Bytes — 数据传输量
# 3. Shuffle Errors — 失败重试次数

# 从日志中分析 Shuffle
yarn logs -applicationId <application_id> 2>/dev/null | \
  grep -iE "shuffle|fetch|merge|sort|spill" | tail -50
```

### 5.2 Shuffle 性能指标解读

| 指标 | 正常范围 | 异常信号 |
|------|---------|---------|
| **Shuffle Bytes** | 取决于数据量 | 超过预期 2x+，检查中间结果膨胀 |
| **Shuffle Time** | 占 DAG 总时间 <30% | >50% 说明 Shuffle 是瓶颈 |
| **Shuffle Errors** | 0~少量 | 持续出现说明网络/磁盘有问题 |
| **Spill Count** | 少或无 | 频繁 Spill 说明排序缓冲区太小 |
| **Merge 次数** | <3 轮 | 过多 Merge 说明碎片化严重 |

### 5.3 Shuffle 调优参数

```yaml
# Shuffle 调优核心参数

# 1. 排序缓冲区加大 — 减少 Spill
tez.runtime.io.sort.mb: 512           # 默认 256M，大任务可调至 1024M
tez.runtime.io.sort.factor: 100       # 合并因子，默认 10，调大减少 merge 轮次

# 2. 并行拉取 — 加快数据传输
tez.runtime.shuffle.parallel.copies: 20  # 默认 10，大集群可调至 40

# 3. 连接超时 — 避免慢节点拖慢整体
tez.runtime.shuffle.connect.timeout: 30000    # 30s
tez.runtime.shuffle.read.timeout: 120000      # 120s

# 4. 压缩 — 减少网络传输量
tez.runtime.compress: true
tez.runtime.compress.codec: org.apache.hadoop.io.compress.SnappyCodec

# 5. 传输缓冲区
tez.runtime.shuffle.memory.limit.percent: 0.25     # shuffle 可用内存比例
tez.runtime.shuffle.buffer.percent: 0.70            # 日志段缓存比例
tez.runtime.shuffle.inputbuffer.percent: 0.70       # 输入缓存比例

# 6. 输出合并
tez.runtime.merge.max-merged-events-per-round: 500
```

---

## 六、Hive on Tez 排障

### 6.1 Hive on Tez 配置验证

```sql
-- 确认当前引擎
SET hive.execution.engine;
-- 应返回 tez

-- 查看 Tez 关键配置
SET tez.am.resource.memory.mb;
SET hive.tez.container.size;
SET tez.task.resource.memory.mb;
SET tez.grouping.split-count;
```

### 6.2 常见 Hive on Tez 问题

#### 6.2.1 查询慢 — 启动延迟大

```sql
-- 现象：查询提交后长时间无响应
-- 原因：Tez AM 启动慢、Session 初始化慢

-- 配置 Session 复用
SET hive.server2.tez.session.lifetime=86400;       -- Session 存活时间（秒）
SET hive.server2.tez.sessions.init.threads=64;     -- 预初始化 Session 线程数
SET hive.server2.tez.initialize.default.sessions=true;  -- 启动时预创建 Session
```

#### 6.2.2 查询慢 — Reducer 数不合理

```sql
-- 现象：Reducer 过多（几千个写小文件）或过少（一个 Reducer 处理几十分钟）

-- 自动 Reducer 并行度
SET hive.tez.auto.reducer.parallelism=true;

-- 每个 Reducer 处理数据量
SET hive.tez.max.partition.factor=8;     -- 允许最大 Reducer 数倍数
SET hive.tez.min.partition.factor=0.25;  -- 最小 Reducer 数倍数
SET hive.tez.reduces.per.partition=1;    -- 每个分区启动的 Reducer 数

-- 手动指定（调试用）
SET mapreduce.job.reduces=50;
```

#### 6.2.3 数据膨胀 — Map 输出过大

```sql
-- 现象：Map 端输出远大于输入，Shuffle 数据量巨大

-- 在 Map 端尽早过滤
-- 使用谓词下推（Predicate Pushdown）
SET hive.optimize.ppd=true;              -- 默认开启

-- 使用列裁剪
SET hive.io.file.read.all.columns=false; -- 只读取需要的列
SET hive.fetch.task.conversion=more;     -- 简单查询不走 MR/Tez

-- 尽早聚合（Map 端聚合）
SET hive.map.aggr=true;                  -- Map 端聚合
SET hive.groupby.mapaggr.checkinterval=100000;
```

#### 6.2.4 文件数过多 — Small File 问题

```sql
-- 现象：Map 数暴增（几万个），每个 Task 处理几 KB

-- 文件合并
SET hive.merge.mapfiles=true;            -- Map 输出合并
SET hive.merge.mapredfiles=true;         -- Reduce 输出合并
SET hive.merge.size.per.task=256000000;  -- 256MB 目标大小
SET hive.merge.smallfiles.avgsize=16000000;  -- 阈值 16MB

-- 输入合并
SET hive.input.format=org.apache.hadoop.hive.ql.io.CombineHiveInputFormat;  -- 默认
SET mapreduce.input.fileinputformat.split.maxsize=256000000;   -- 256MB
SET mapreduce.input.fileinputformat.split.minsize=1;
```

---

## 七、核心调优参数全景

### 7.1 内存配置

| 参数 | 默认值 | 推荐范围 | 说明 |
|------|--------|---------|------|
| `tez.am.resource.memory.mb` | 1024 | 2048~4096 | Application Master 内存 |
| `hive.tez.container.size` | 1024 | 2048~8192 | Tez Container 总内存 |
| `tez.task.resource.memory.mb` | 1024 | 2048~8192 | Task JVM heap（与 container.size 配合使用） |
| `hive.tez.java.opts` | 自动 | -Xmx<80% container.size> | JVM 启动参数 |

### 7.2 分组与并行度

| 参数 | 默认值 | 推荐范围 | 说明 |
|------|--------|---------|------|
| `tez.grouping.split-count` | -1 (自动) | 10~200 | 强制分组数，覆盖自动分组 |
| `tez.grouping.min-size` | 16MB (16,777,216) | 16~64MB | 分组最小大小 |
| `tez.grouping.max-size` | 1GB (1,073,741,824) | 256MB~1GB | 分组最大大小 |
| `hive.tez.auto.reducer.parallelism` | false | true | 自动 Reducer 并行度 |
| `hive.tez.max.partition.factor` | 2 | 5~16 | 最大 Reducer 数 = 分区数 × factor |
| `hive.tez.min.partition.factor` | 0.25 | 0.25~2 | 最小 Reducer 数 = 分区数 × factor |

### 7.3 Shuffle 与 IO

| 参数 | 默认值 | 推荐范围 | 说明 |
|------|--------|---------|------|
| `tez.runtime.io.sort.mb` | 256 | 256~1024 | 排序缓冲区大小 (MB) |
| `tez.runtime.io.sort.factor` | 10 | 64~200 | 合并因子，越大 merge 轮次越少 |
| `tez.runtime.shuffle.parallel.copies` | 10 | 10~40 | 并行 Shuffle 线程数 |
| `tez.runtime.compress` | true | true | 启用压缩 |
| `tez.runtime.compress.codec` | Snappy | Snappy/LZ4 | 压缩编解码器 |

### 7.4 分组策略详解

`tez.grouping.split-count` 是 Tez 调优中非常关键的参数：

```sql
-- 场景：Mapper 数过多（几万个 Task），调度开销 > 计算开销

-- 强制分组数（推荐先用这个）
SET tez.grouping.split-count=50;
-- 将输入数据分成最多 50 个分组，降低 Task 数
-- 注意：split-count 最大值受 tez.grouping.max-size 限制

-- 通过大小控制分组
SET tez.grouping.min-size=268435456;   -- 256MB
SET tez.grouping.max-size=536870912;   -- 512MB
-- Tez 自动在每个分组中调度 min-size~max-size 的数据

-- 关闭分组（不推荐）
SET tez.grouping.split-count=0;
```

```bash
# 验证分组效果
# 在 Tez UI 中查看：
# 1. 每个 Vertex 的 Task 数
# 2. 每个 Task 处理的数据量
# 3. Task 处理时间分布

# 命令式查看
yarn logs -applicationId <application_id> | \
  grep -E "Number of tasks|Splits|Grouping" | head -10
```

---

## 八、Tez UI 指标解读

### 8.1 DAG 级别

| 指标 | 含义 | 正常值 | 告警阈值 |
|------|------|-------|---------|
| **DAG Duration** | DAG 总耗时 | 视数据量而定 | 超过 SLA 阈值 |
| **Vertex Count** | DAG 中 Stage 数量 | 1~20 | >30 个说明查询复杂，可优化 SQL |
| **Edge Count** | 边数量 | 0~30 | 过多边说明 DAG 结构复杂 |
| **Task Count** | 总 Task 数 | 100~5000 | >10000 时调度开销大 |
| **Succeeded/Failed/Killed** | 各状态 Task 数 | Failed=0 | 任何 Failed 都需要排查 |

### 8.2 Vertex 级别

| 指标 | 含义 | 诊断方向 |
|------|------|---------|
| **Duration** | Vertex 执行时间 | 最长的 Vertex 就是瓶颈 |
| **Tasks** | 并行 Task 数 | 过多 → split-count 问题；过少 → 倾斜可能 |
| **Shuffle Bytes** | 网络传输数据量 | 远超输入 → 检查 Map 端聚合 |
| **Shuffle Duration** | Shuffle 耗时 | > 总时间 50% → 见第五章 |
| **CPU Time** | 实际 CPU 计算时间 | << Duration → IO 或 GC 瓶颈 |
| **GC Time** | GC 消耗时间 | >15% → 内存不足或堆太小 |
| **Spilled Records** | 溢写记录数 | >0 → sort.mb 太小 |
| **Input Records** | 输入记录数 | 判断数据量是否合理 |

### 8.3 关键诊断规则

```
瓶颈判断规则：

1. 单个 Vertex 耗时占 DAG 的 70%+
   → 进入该 Vertex，分析是计算密集、Shuffle 密集还是 GC 密集

2. Task 耗时方差大（max/avg > 3）
   → 数据倾斜，检查 key 分布

3. Shuffle Bytes >> Input Bytes
   → Map 端未做聚合，或中间结果膨胀

4. Spilled Records > 10^6
   → tez.runtime.io.sort.mb 太小

5. Failed Tasks > 0
   → 检查 Container 退出原因（见第二章）
```

---

## 九、综合排障工作流

### 9.1 "Hive 查询跑得慢" — 标准排查路线

```
1. 确认执行引擎
   SET hive.execution.engine;  → 应为 tez

2. 查看 DAG 耗时
   进入 Tez UI → DAG Duration
   ├── 总时长 > SLA → 继续
   └── 总时长正常 → 优化 SQL 逻辑

3. 找到最慢的 Vertex
   按 Duration 排序，定位最长 Vertex
   ├── Shuffle Duration 占比大 → 走 Shuffle 优化（第五章）
   ├── Task 耗时差异大 → 走数据倾斜（第三章）
   ├── GC Time > 15% → 走 OOM 修复（第四章）
   └── 平均 Task 时间正常但 Task 数过多 → 调 grouping

4. 检查 Container 健康
   看 Failed / Killed Task 数
   ├── 有失败 → 查看退出原因（第二章）
   └── 无失败 → 调整并行度和内存
```

### 9.2 快照采集（故障升级用）

```bash
# 收集 Tez 故障快照
{
  echo "=== YARN APPLICATION STATUS ==="
  yarn application -status <application_id> 2>/dev/null

  echo ""
  echo "=== TEZ CONFIGURATION ==="
  echo "tez.am.resource.memory.mb: $(curl -s http://<hive-server>:10002/system 2>/dev/null | grep tez.am.resource.memory.mb || echo 'N/A')"
  echo "hive.tez.container.size: $(curl -s http://<hive-server>:10002/system 2>/dev/null | grep hive.tez.container.size || echo 'N/A')"

  echo ""
  echo "=== CONTAINER LOGS (failed tasks) ==="
  yarn logs -applicationId <application_id> 2>/dev/null | grep -iE "failed|error|exception|oom|outofmemory|killed" | tail -50

  echo ""
  echo "=== CLUSTER RESOURCE ==="
  yarn cluster -status 2>/dev/null

  echo ""
  echo "=== NODE STATUS ==="
  yarn node -list -all 2>/dev/null | head -30

} | tee /tmp/tez-snapshot-$(date +%Y%m%d-%H%M%S).log
```

---

## 十、推荐基线配置

### 10.1 按集群规模分类

#### 小型集群（<100TB 数据量，10~20 节点）

```ini
# hive-tez-tuning-small.ini
tez.am.resource.memory.mb=2048
hive.tez.container.size=2048
tez.task.resource.memory.mb=2048
tez.runtime.io.sort.mb=256
tez.runtime.io.sort.factor=64
tez.runtime.shuffle.parallel.copies=10
tez.grouping.min-size=16777216
tez.grouping.max-size=268435456
```

#### 中型集群（100TB~1PB，20~100 节点）

```ini
# hive-tez-tuning-medium.ini
tez.am.resource.memory.mb=4096
hive.tez.container.size=4096
tez.task.resource.memory.mb=4096
tez.runtime.io.sort.mb=512
tez.runtime.io.sort.factor=100
tez.runtime.shuffle.parallel.copies=20
tez.grouping.min-size=33554432
tez.grouping.max-size=536870912
hive.tez.auto.reducer.parallelism=true
hive.tez.max.partition.factor=8
```

#### 大型集群（1PB+，100+ 节点）

```ini
# hive-tez-tuning-large.ini
tez.am.resource.memory.mb=8192
hive.tez.container.size=8192
tez.task.resource.memory.mb=8192
tez.runtime.io.sort.mb=1024
tez.runtime.io.sort.factor=200
tez.runtime.shuffle.parallel.copies=40
tez.runtime.shuffle.connect.timeout=60000
tez.grouping.min-size=67108864
tez.grouping.max-size=1073741824
hive.tez.auto.reducer.parallelism=true
hive.tez.max.partition.factor=16
hive.tez.min.partition.factor=0.25
```

### 10.2 常见场景配置速查

| 场景 | 关键调整 |
|------|---------|
| **Container 频繁 OOM** | 增大 `tez.task.resource.memory.mb` + `hive.tez.container.size` |
| **Task 数暴多** | 设置 `tez.grouping.split-count=50~200` |
| **Shuffle 慢** | 调大 `tez.runtime.io.sort.mb`, `tez.runtime.shuffle.parallel.copies` |
| **数据倾斜** | `hive.groupby.skewindata=true`, `hive.optimize.skewjoin=true` |
| **AM 频繁重启** | 增大 `tez.am.resource.memory.mb`, `tez.am.max.app.attempts` |
| **启动延迟大** | 启用 `hive.server2.tez.initialize.default.sessions=true` |
| **中间结果膨胀** | 增大 `tez.runtime.io.sort.mb`，启用 Snappy 压缩 |
| **GC 压力大** | 增大 heap 或减少单 Task 处理数据量 |

---

## Pitfalls

- **`tez.task.resource.memory.mb` vs `hive.tez.container.size` 的关系**：`container.size` 是 YARN Container 总大小（包含 heap + overhead），`task.resource.memory.mb` 是 JVM heap（-Xmx）。推荐将两者设为相同值，这样 overhead 由 YARN 自动计算。
- **`tez.grouping.split-count` 不是绝对值**：它是分组数的上限（soft cap），实际分组数受 `tez.grouping.max-size` 和输入数据量共同限制。例如 split-count=200，但 max-size=1GB，总输入 10GB → 实际分组 ~10 个。
- **Session 复用不是万能药**：`hive.server2.tez.session.lifetime` 设置过长会导致内存泄漏，需要配合 `hive.server2.tez.sessions.restricted.config` 限制 Session 配置变更。
- **不要在生产环境同时开 `skewindata` 和大量 Reducer**：`skewindata=true` 会开启两阶段聚合（加随机前缀），Reducer 数过多时中间结果膨胀反而更慢。
- **`tez.runtime.compress` 在 CPU 密集任务上可能适得其反**：如果 CPU 已经是瓶颈（CPU Time ≈ DAG Duration），压缩会加剧 CPU 压力，此时应禁用压缩或换更轻量的 LZ4。
- **Tez UI 数据延迟**：Tez UI 数据来自 Timeline Server (ATS)，ATS 有 15~30s 的聚合延迟。实时查看请用 `yarn logs -applicationId`。
- **`yarn logs -applicationId` 对运行中的应用不生效**：日志聚合只在应用结束后进行。运行中看日志需 SSH 到对应 NM 节点查看本地日志。
- **Hive on Tez 中 `mapreduce.job.reduces` 不一定生效**：Tez 有自己的 Reducer 自动并行度计算逻辑。建议用 `hive.tez.auto.reducer.parallelism` + `hive.tez.max.partition.factor` 控制。
- **多个 Tez Session 同时运行可能产生资源竞争**：检查 `tez.am.resource.memory.mb` × 最大并发 Session 数是否超过队列容量。
- **不要盲目调大 Container Size**：节点总资源 (/ yarn.nodemanager.resource.memory-mb) 固定，Container 过大导致并行度下降，可能抵消单 Task 的性能提升。
