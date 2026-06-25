# A1 — 多层 LI 整合项目真实案例

## 项目概况

A1 是非洲区域 LI 整合项目，三层架构：

```
ZTLIG (LI 前端)  →  X1 设控 / X2 IRI 报告 / X3 媒体流
OWLS  (后端分析) →  离线/实时处理、虚-实关联、报表
大数据平台        →  HDFS / HBase / Kafka / Flink / Redis / MySQL
```

覆盖 3 个运营商：MTN (苏丹)、ZAIN (苏丹)、SU (Sudatel)，均为华为 CS/IMS 网元。

## 最终目录结构

```
A1/
├── README.md                       项目全景说明
│
├── cfg/                            ZTLIG 配置文件
│   ├── B-MTN-CS-ztlig.cfg          MTN CS 域 (39K, 4TNE+4VNE)
│   ├── B-ZAIN-CS-ztlig.cfg         ZAIN CS 域 (67K, 6TNE+6VNE)
│   ├── B-SU-CS-ztlig.cfg           SU CS 域 (87K, 10TNE+10VNE)
│   └── README.md                   配置参数速查（段说明/关键参数/端口映射）
│
├── ztlig/
│   ├── 对接/                       空，待填充
│   ├── 工勘/                       空，待填充
│   ├── 巡检/                       空，待填充
│   ├── 方案/                       空，待填充
│   ├── 抓包/                       空，待填充
│   └── 解码/                       空，待填充
│
├── owls/
│   ├── architecture/
│   ├── dataflow/
│   ├── features/
│   ├── config/
│   ├── deployment/
│   └── troubleshooting/
│
├── bigdata/
│   ├── hdfs/
│   ├── hbase/
│   ├── kafka/
│   ├── flink/
│   ├── redis/
│   └── mysql/
│
├── integration/                    已填充
│   ├── topology.md                 三层拓扑 + 网元清单 (MTN 5, ZAIN 10, SU 14)
│   ├── kafka-topics.md             设控(TMC_TARGET_INFO) / 实时(OWLS_TMC_REALTIME) / 离线 等
│   ├── data-flow.md                4 条核心流：设控 / IRI 实时 / X3 媒体 / 离线处理
│   └── api-guide.md                X1/X2/X3/OWLS/大数据 各层接口，含 X1 ReturnCode 速查表
│
└── docs/
    ├── progress/                   空，待填充
    ├── meeting/                    空，待填充
    └── references/                 知识库索引（指向 Obsidian 已有 10+ 篇文档）
```

## 关键集成参数

### Kafka Topic 映射

| Topic | 角色 | 方向 |
|-------|------|------|
| TMC_TARGET_INFO | 设控请求 | OWLS → ZTLIG |
| TARGET_INFO_STATUS | 设控响应 | ZTLIG → OWLS |
| OWLS_TMC_REALTIME | 实时 IRI + Notice | ZTLIG → OWLS |
| OWLS_TMC_OFFLINE | 离线报告 | ZTLIG → OWLS |
| metric_report | 进程监控指标 | ZTLIG → Kafka |

### 数据端到端

```
设控下发:  LEA → OWLS → Kafka → ZTLIG1 → NE (X1)
IRI 报告:  NE → ZTLIG2 → Kafka → OWLS → HBase → Flink → 展示
X3 媒体:   NE → ZTLIG3(RVF) → 语音文件 + Notice → Kafka → OWLS
离线处理:   OWLS_TMC_OFFLINE → Flink 批处理 → HBase → 虚-实关联 → 报表
```

### ZTLIG 目标同步逻辑（三层同步链）

A1 项目中 ZTLIG1 模块的同步机制横跨所有三层：

```
GP (Greenplum) ──cron──→ Redis ──01:00-02:00──→ MySQL ──LIST对比──→ NE
     ↓                    ↓                      ↓                    ↓
  OWLS 设控          缓存层                 LIG 本地库          网元执行
```

| 同步段 | 调度 | 是否可配 |
|--------|------|---------|
| GP → Redis | 默认 00:10 每天 | ✅ `scheduling.config.tmcupdateToRedis` |
| Redis → MySQL | 01:00-02:00 | ❌ 固定 |
| MySQL → NE | 随 LIST 对比 | — |

手工命令：
- `start ztlig1 {id} hwmsc {leadid} {neid} list` — 查看 NE 目标
- `syn ztlig1 {id} hwmsc {leadid} {neid}` — 手工同步
- NE 目标丢失通过 X2 报告数量骤降检测

**详见** `integration/sync-logic.md`

## 与基础 LI 结构的区别

| 维度 | 基础 LI (A1) | 多层整合 (A2) |
|------|-------------|--------------|
| cfg 文件 | 根目录 | cfg/ 子目录 |
| 后端层 | 无 | owls/ (架构/流程/功能/部署/排错) |
| 大数据层 | 无 | bigdata/ (各组件子目录) |
| 跨层文档 | 无 | integration/ (拓扑/Topic/数据流/API) |
| 知识库链接 | 无 | docs/references/ |
