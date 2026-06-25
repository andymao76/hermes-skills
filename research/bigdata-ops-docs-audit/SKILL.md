---
name: bigdata-ops-docs-audit
description: "Audit Big Data ops documentation quality: review CSDN/知乎/博客园 articles for HDFS, Hive, HBase, Greenplum, ES, Kafka, identify outdated/incorrect/misleading content. NOT a learning/reference skill — use this for vetting existing docs, not for systematic study."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bigdata, ops, audit, CSDN, zhihu, review]
    related_skills: [knowledge-base, bigdata-systematic-knowledge-research]
---

# Big Data Ops Documentation Audit

Reviews CSDN / 知乎 / 博客园 Big Data ops articles, flags version-dependent errors and outdated advice, and archives structured findings to `~/knowledge/research/`.

## When to use

User mentions reviewing/auditing/fact-checking Big Data ops docs, or asks about HDFS/Hive/HBase/Greenplum/ES/Kafka maintenance. Also when user wants to "整理无效和错误部分" for these components.

## Trigger keywords

运维文档、踩坑、调优、故障排查、CSDN 上关于 (HDFS|Hive|HBase|Greenplum|ES|Kafka)、无效和错误部分

## Workflow

### Phase 1: Parallel search (use delegate_task)

Create one sub-agent per component (up to 3 at a time). Each searches:

1. **CSDN** — `site:blog.csdn.net <component> 运维 故障` or `<component> 调优 踩坑`
2. **知乎** — `site:zhihu.com <component> 运维 故障` or `<component> 踩坑`
3. **博客园** — `site:cnblogs.com <component> 运维` for fallback content

Each sub-agent extracts 3-5 representative articles with title, author, link, core claims.

### Phase 2: Fact-checking (do NOT delegate — needs model knowledge)

For each article, evaluate against known production truths:

| Component | Common outdated patterns to flag |
|-----------|----------------------------------|
| **HDFS** | SecondaryNameNode as failover (deprecated 3.x), missing EC, missing disk-balanancer, wrong handler.count defaults |
| **Hive** | MR engine as default (should be Tez/Spark), vendor-specific params passed as Apache Hive, missing LLAP/ACID/Iceberg |
| **HBase** | CMS GC recommendation (use G1GC), RegionTooBusyException old logic, missing In-Memory Compaction/Off-Heap |
| **Greenplum** | `gprecoverseg -r` (deprecated in GP7), Resource Queue (deprecated → Resource Group), missing Differential Recovery, Zstd compression |
| **Elasticsearch** | Zen Discovery tuning (removed in 8.x → Raft), CMS GC, "20 shards per GB" rule (outdated in 8.3+), `allocate_stale_primary` misuse |
| **Kafka** | `--zookeeper` flag (deprecated in 3.x → KRaft), RangeAssignor as default (now StickyAssignor), manual `log.flush.*` tuning, missing Cooperative Rebalancing (KIP-429) / KIP-848 |

### Phase 4: Cross-component comparison (when user asks for 对比/交叉/选型)

After individual component audits, produce a cross-comparison analysis when the user asks for 交叉对比、选型、对比分析. This is a separate deliverable:

1. **Search**: `web_search("HDFS Hive HBase Greenplum ES Kafka comparison 2026")`, also search for specific pair comparisons (StarRocks vs ClickHouse, Iceberg vs Delta Lake, Redpanda vs Pulsar vs Kafka, S3 vs HDFS).
2. **Identify misconceptions**: Common wrong "compare apples to oranges" patterns:
   - Kafka vs RabbitMQ (wrong category — Kafka's competitors are Pulsar/Redpanda)
   - HDFS vs S3 (not same category — S3 *replaces* HDFS)
   - HBase as OLAP (wrong — only random point reads)
   - Greenplum as "only MPP" (StarRocks/ClickHouse have overtaken it)
   - ES as OLAP (wrong — search/retrieval domain)
   - Hive vs HBase as alternatives (wrong — they're complementary stack layers)
3. **Capture 2026 trends**: Lakehouse architecture, Iceberg/Delta replacing Hive Metastore, StarRocks/ClickHouse replacing Greenplum, Diskless Kafka (Redpanda/WarpStream), S3/OSS replacing HDFS.
4. **Produce decision tree**: Based on data type, query pattern, and data source.
5. **Score component health**: Community activity, new-project recommendation, migration urgency.
6. **Save to**: `~/knowledge/research/bigdata-component-cross-comparison-2026.md`

### Phase 5: Save & deliver

Save both outputs:
- Per-component audit → `~/knowledge/research/bigdata-ops-docs-errors-review.md`
- Cross-component comparison → `~/knowledge/research/bigdata-component-cross-comparison-2026.md`

### Phase 3: Structure output (per-component audit)

Format findings into a knowledge-base markdown file at `~/knowledge/research/bigdata-ops-docs-errors-review.md`:

```markdown
# 大数据组件运维文档 —— CSDN & 知乎无效/错误内容整理

## 一、<Component>

### 🔴 高危错误
| 错误内容 | 来源文章 | 正确做法 | 风险等级 |
### 🟡 中等过时
| 错误内容 | 来源 | 正确做法 |
### 知乎方面
### 系统性缺失

## 七、跨组件共性过时问题
```

For cross-component comparison output at `~/knowledge/research/bigdata-component-cross-comparison-2026.md`:

```markdown
# 2026年大数据核心组件交叉对比分析

## 〇、组件定位速览
## 一、交叉对比矩阵
### 1.1 数据模型
### 1.2 性能特征
### 1.3 运维与生态
## 二、常见概念混淆与选型误区
### ❌ 误区1：「Kafka和RabbitMQ是同品类」
### ❌ 误区2：「HDFS和S3是同类竞品」
### ❌ 误区3：「HBase可以当OLAP用」
### ❌ 误区4：「Greenplum是唯一的MPP方案」
### ❌ 误区5：「ES可以替代OLAP数据库做分析」
### ❌ 误区6：「Hive和HBase可以二选一」
## 三、2026年新趋势冲击
### 3.1 Iceberg/Delta → Hive Metastore
### 3.2 StarRocks/ClickHouse → Greenplum
### 3.3 Redpanda/Pulsar/Diskless Kafka → Kafka
### 3.4 S3/OSS → HDFS
### 3.5 Lakehouse → Hadoop数仓
## 四、选型决策树
## 五、组件健康度评分
## 六、跟踪议题
## 七、已筛选的无效/过时知识清单
```

### Pitfalls

- **CSDN 反爬严重**: web_extract usually times out or returns 403. Rely on search result snippets for summary — you won't get full article text. For full content, try Tencent Cloud mirror (cloud.tencent.com/developer/article/) or the original author's blog.
- **版本标注缺失**: most CSDN articles don't state which version they cover. Flag this as a systemic issue.
- **AI-generated content**: 2023-2025 CSDN articles on Big Data topics are increasingly LLM-generated. Low-effort lists of generic parameters are a red flag — skip them.
- **Vendor lock-in params**: Huawei FusionInsight / Alibaba EMR custom params are frequently passed off as Apache Hive/HBase native. Verify against Apache docs.
