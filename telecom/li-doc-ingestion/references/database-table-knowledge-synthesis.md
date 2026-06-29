# 数据库表知识综合文档模式 (Database Table Knowledge Synthesis)

## 触发场景

用户要求「保存 [表名] 的完整说明到知识库」或「把 [表名] 的信息整理成文档」，且相关信息分散在多个已有的知识库源文件中（DDL 表结构、数据流文档、分区配置、运维手册等）。

## 与标准入库的区别

| 维度 | 标准文档入库 (li-doc-ingestion) | 数据库表知识综合 (本模式) |
|------|-------------------------------|------------------------|
| **输入** | 外部厂商文档/PCAP/配置文件 | 知识库中已有的多个源文件 |
| **动作** | 解析→结构化→写入 | 搜索→多源聚合→合成→写入 |
| **产出** | 对原始文档的精炼笔记 | 跨源综合参考文档 |
| **源文件** | 原始文档（厂商格式） | 已有 `.md` 知识库笔记 |

## 标准工作流

### Step 1: 全源搜索

在知识库中搜索表名，覆盖所有可能包含信息的文件类型：

```
search_files(pattern="<表名>", path="~/knowledge/", output_mode="files_only")
```

关键搜索范围：
- DDL/建表语句 → 故障排查文档、AIC 现场文档
- 数据流 → 架构文档、数据流图
- 分区配置 → `base_addpart_config` 相关文档
- 使用说明 → runbook、运维手册
- 查询示例 → 技术文章、NISS 文档、排障笔记

### Step 2: 读取关键源文件

对每个匹配的源头文件，按优先级读取：

| 优先级 | 文件类型 | 提取的信息 |
|--------|---------|-----------|
| 1 | 含 DDL 的文件 | 完整 CREATE TABLE、字段列表、分区子句、存储参数、分布键 |
| 2 | 数据流文档 | 数据的上下游链路（Kafka → Flink → ES → GP 等） |
| 3 | 分区配置表 | keep_time, part_mode, tablespace, pre_time |
| 4 | 运维 runbook | 表的用途说明、常用查询 |
| 5 | 排障/技术文章 | 实际查询案例、空间占用信息、重建流程 |

使用 `read_file` 读取匹配行附近的上下文（`context` 参数或 offset/limit），不要只读匹配行。

### Step 3: 合成结构化文档

产出文档包含以下标准章节：

1. **概述** — 表名含义、核心定位
2. **数据库位置** — 数据库类型、schema、分布键、存储类型、压缩方式
3. **完整 DDL** — 格式化后的 CREATE TABLE 语句
4. **字段分类说明** — 按语义分组（目标标识/事件信息/号码标识/位置信息），每组一个 Markdown 表格
5. **分区与索引** — 分区策略（一级/二级）、子分区类型、索引列表、分区配置表
6. **数据流** — 架构图（ASCII 或文字流）、关键流程说明、相关组件表
7. **数据规模与存储** — 行数、空间占用、保留策略
8. **常用查询** — 基本查询、空间排查、业务分析示例
9. **维护流程** — 重建表、分区管理、空间回收
10. **关联表** — 相关表名及关系说明
11. **注意事项** — 陷阱、易错点、版本差异

### Step 4: 写入知识库

- LI 领域表 → `knowledge/telecom/lawful_interception/`
- 运维手册表 → `知识/电信专家包v4/`
- 文件名：`<表名>_full_description.md`
- 必须包含 YAML frontmatter（title, tags, source, aliases, related）
- 使用 `[[wikilinks]]` 关联相关笔记

### Step 5: 验证

```
kb-index
kb-index search "<表名>"
```

## 字段分类模板

### 3 套号码标识

| 组 | 字段前缀 | 说明 |
|----|---------|------|
| 主目标 | TRGT | TRGTIMEI / TRGTNUM / TRGTIMSI |
| 主叫方 | CALLER_ / 无前缀 | CALLER_MSISDN / MSISDN / IMSI / IMEI_ESN_MEID |
| 被叫方 | CALLED_ | CALLED_MSISDN / CALLED_IMSI / CALLED_IMEI_ESN_MEID |
| 第三方 | third_ | third_imsi / third_imei / third_msisdn |

### 4 类位置信息

| 组 | 字段前缀 | 说明 |
|----|---------|------|
| 当前位置 | 无前缀 | SITE_ID / LONGITUDE / LATITUDE / AZIMUTH / LAC / ENODEBID / CELLID |
| 主叫位置 | CALLER_ | CALLER_SITE_ID / CALLER_LATITUDE / ... |
| 被叫位置 | CALLED_ | CALLED_SITE_ID / CALLED_LATITUDE / ... |
| 旧位置 | OLD_ | OLD_SITE / OLD_LONGITUDE / OLD_LATITUDE / ... |

## 注意事项模板

```
1. **时间戳单位：** CAPTURETIME 是毫秒级 Unix 时间戳（13 位），不是秒级。
2. **字段 X 不存在：** 该表不包含 `X` 字段。`X` 是 Kafka/其他系统的字段。
3. **重建注意事项：** 重建后只需保留常用索引，过多索引影响写入性能。
4. **分区对齐：** 重建临时表后，历史分区范围必须覆盖原表所有数据，否则 INSERT 会失败。
```
