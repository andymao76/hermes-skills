---
name: bigdata-systematic-knowledge-research
description: "系统性搜索并整理大数据组件知识（HDFS/Hive/HBase/Greenplum/Elasticsearch/Kafka）到本地知识库。多组件并行搜索 Google + GitHub 高星仓库/文档，聚合为结构化学习指南写入 knowledge/research/。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bigdata, research, knowledge-base, hdfs, hive, hbase, greenplum, elasticsearch, kafka]
    related_skills: [bigdata-ops-docs-audit, knowledge-base, self-learning]
---

# 大数据组件系统性知识调研注入知识库

## 适用场景

用户要求系统性学习一个或多个大数据组件（HDFS/Hive/HBase/Greenplum/ES/Kafka）的架构、原理、运维步骤、生命周期管理。

## 触发词

大数据、HDFS、Hive、HBase、Greenplum、Elasticsearch、Kafka、系统性知识、学习资料、查找资料、Google、GitHub

## 子场景：单组件问题回答（非全量调研）

当用户只问一个组件的具体问题（如"GP 常用命令"、"ES 健康检查"、"Kafka Consumer Lag 排查"），而不是要求系统性学习时：

### 步骤一：先查本地知识库

```bash
grep -rl "Greenplum\|greenplum\|gp" ~/knowledge/research/ --include="*.md"
```

已有知识库文件包括：
- `research/bigdata-systematic-knowledge-guide.md` — 完整资料索引和学习路径
- `research/greenplum-commands-cheatsheet.md` — GP 常用命令
- `research/greenplum-healthcheck-guide.md` — GP 健康检查指南
- `articles/bigdata-common-errors-handbook.md` — 故障排查手册
- `articles/bigdata-ops-english-glossary.md` — 英文术语

如果知识库已有相关内容，直接展示给用户，跳过搜索。

### 步骤二：知识库不足时联网补充

对缺失的部分用 `web_search` + `web_extract` 单组件精确搜索，聚焦用户问的具体主题。

### 步骤三：整理到知识库

新增内容写入 `~/knowledge/research/<component>-<topic>.md`，更新 enzyme 索引。

## 工作流（全量调研用）

### 阶段一：并行搜索（使用 delegate_task）

每个组件分配一个 sub-agent，并行搜索。每个 sub-agent 执行：

1. **Google 搜索**（4 组关键词，每组 5 条结果）：
   - `<component> architecture 2025 2026`
   - `<component> 架构原理 优化 调优`（中文）
   - `<component> administration best practices`
   - `<component> troubleshooting common issues`

2. **GitHub 搜索**（4 组关键词）：
   - `<component> best practices`
   - `awesome-<component>`
   - `<component> internals / migration`
   - `<component> operations guide`

3. **结果格式**：
   - 标题、URL（完整可访问链接）、简介摘要（50 字左右）
   - 来源标注（Google/GitHub）
   - 质量评分（高/中/低）

### 阶段二：聚合整理

将所有 sub-agent 的结果合并为一份统一的结构化 Markdown 笔记：

```
# 大数据组件系统性知识学习指南

## 总览表格（组件 × 资料数 × 核心主题）

## 各组件分类（官方文档/中文文章/GitHub/故障排查）

## 学习路径建议（阶段一原理筑基 → 阶段二运维 → 阶段三进阶 → 阶段四趋势）
```

### 阶段三：写入与刷新

1. 写入 `~/knowledge/research/bigdata-systematic-knowledge-guide.md`
2. 执行 `cd ~/knowledge && enzyme refresh` 更新语义索引

## 搜索关键词模板

### Google 中文搜索关键词

```
<组件> 架构原理 详解
<组件> 架构 优化 调优
<组件> 运维 实践 步骤
```

### Google 英文搜索关键词

```
<component> architecture <current_year>
<component> administration best practices
<component> troubleshooting guide
<component> performance tuning
```

### GitHub 搜索关键词

```
<component> best practices
awesome-<component>
<component> operations guide
<component> migration
```

## 高质量资源预检

| 组件 | 知道的高质量资源 |
|------|----------------|
| HDFS | hadoop.apache.org 官方架构文档、Cloudera Blog |
| Hive | cwiki.apache.org Hive 文档、Cloudera 调优指南 |
| HBase | hbase.apache.org Reference Guide、HubSpot G1GC Blog |
| Greenplum | techdocs.broadcom.com GP7 文档、github.com/pgcentralfoundation/gpdb |
| ES | elastic.co 官方 ILM 文档、github.com/dzharii/awesome-elasticsearch |
| Kafka | kafka.apache.org KRaft 文档、conduktor/awesome-kafka |

## 输出文件结构

```markdown
~/knowledge/research/
├── bigdata-systematic-knowledge-guide.md         # 六组件资料索引（全量调研产物）
├── greenplum-commands-cheatsheet.md              # GP 常用命令速查
├── greenplum-healthcheck-guide.md                # GP 健康检查指南
```

**单组件问题路径**（不是全量调研时）：
- 具体命令 → `research/<component>-commands-cheatsheet.md`
- 健康检查 → `research/<component>-healthcheck-guide.md`
- 故障排查 → `articles/bigdata-common-errors-handbook.md`（已有）

## Pitfalls

- **先查知识库再联网搜索**：用户问单组件具体问题时，先 grep 知识库已有文件，避免重复全量搜索
- **子场景单独产出**：非全量调研时，按主题产出单独文件（`<component>-<topic>.md`），不要合并到总索引
- **GP 相关知识库文件**：`greenplum-commands-cheatsheet.md`（13 类命令）、`greenplum-healthcheck-guide.md`（16 项巡检 + 一键脚本）

- **delegate_task 的 toolset 必须包含 `web`**：否则 sub-agent 无法调用 web_search
- **最大 3 个并行任务**：6 个组件分 2 批执行（HDFS/Hive/HBase 一批，GP/ES/Kafka 另一批）
- **搜索结果需去重**：同一个 awesome 列表可能在多个搜索关键词下重复出现
- **仅保留真实搜索结果**：sub-agent 可能编造搜索结果，要求只返回真实的结果
- **enzyme refresh 可能因 vault 路径问题失败**：检查 `ENZYME_VAULT_ROOT` 环境变量和 `~/.enzyme/config.toml` 中的路径是否正确
- **英文授课场景**：用户做英文培训时，关注结果中的"英文表达"内容
