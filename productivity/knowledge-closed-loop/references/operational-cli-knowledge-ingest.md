# 操作型 CLI/SQL 知识入库工作流

用户分段粘贴原始运维命令、SQL 查询、CLI 操作步骤，Agent 结构化后写入知识库。

## 触发特征

用户消息包含以下任意内容：
- shell 命令（`./kafka-console-consumer.sh`、`psql -h ...`、`gpstop -a`）
- SQL/Gremlin 查询（`SELECT * FROM lims_bds_target`、`g.V().has('msisdn')...`）
- 运维操作步骤（"重启 Gremlin Server"、"查看消费情况"）
- 系统输出/报错信息附在命令后面

## 工作流

### 第一步：检查已有知识

```python
# 伪代码
ls ~/knowledge/ 下相关目录，查找匹配的笔记
search_files(pattern="关键表名|命令名|组件名")
```

**决策树：**

| 已有知识情况 | 动作 |
|-------------|------|
| 通用速查表存在且覆盖大部分内容 | **patch 补充缺失行**到速查表 |
| 已有项目专属笔记但缺部分内容 | **patch 追加**到该笔记对应章节 |
| 完全新内容 | **create new note** |

### 第二步：识别项目归属

每段 CLI/SQL 知识都来自特定项目环境。检查以下标志：
- IP 地址（如 215.152.1.x → A1 苏丹）
- 服务器名（如 rhino01/rhino05 → A1）
- 用户名（如 daedb → A1）
- 库名（如 bigdata → A1）
- Topic 名（如 TMC_TARGET_INFO → A1）
- 表名（如 lims_bds_target → A1）

### 第三步：结构化笔记模板

```markdown
---
tags:
  - telecom/lawful_interception
  - <component> (e.g. kafka / janusgraph / greenplum / mysql)
  - <project> (e.g. a1-project)
  - ops / cli / sql
created: YYYY-MM-DD
---

# <项目名> <组件> 操作手册

> ⚠️ **项目专属说明**
> 本文档中的 IP 地址、端口、表名/Topic 名为 **<项目名>** 专属...

## 1. 连接方式

```bash
# 连接命令
```

| 参数 | 说明 | 项目值 |
|------|------|--------|

## 2. 核心命令速查

| 命令/查询 | 说明 |
|-----------|------|

## 3. 业务查询工作流

步骤式描述，如：
1. 查 A → 2. 根据 A 查 B → 3. 根据 B 查 C

## 4. 快速查询模板表

| 场景 | 命令/SQL |
|------|----------|

## 关联文档
- [[其他项目笔记]] — wikilink
```

### 第四步：内容组织原则

| 内容类型 | 组织方式 |
|---------|---------|
| **命令** | 表格：`命令 \| 说明` |
| **SQL/Gremlin 查询** | 代码块 + 步骤式说明 |
| **参数说明** | 表格：`参数 \| 含义 \| 项目值` |
| **输出解读** | 块引用 + 字段含义表 |
| **工作流** | 编号步骤 1→2→3 |
| **报错/排障** | 症状→原因→解决 三段式 |

### 第五步：入库与索引

```bash
# 写入知识库后
enzyme_refresh()
```

## 常见 CLI 类型速查

| CLI 类型 | 目录 | 常见命令 |
|----------|------|---------|
| Kafka CLI | `telecom/lawful_interception/` | `kafka-console-consumer.sh`, `kafka-consumer-groups.sh` |
| Gremlin/JanusGraph | `telecom/lawful_interception/` | `gremlin.sh`, `g.V().has()` |
| Greenplum psql | `research/`(通用) + `telecom/`(项目) | `psql -h`, `gpstart`, `\dt` |
| MySQL | `telecom/lawful_interception/` | `mysql -u`, `mysqldump` |

## 重复检查技巧

在创建新笔记前检查：
1. `search_files` 搜索关键表名/命令名
2. 检查通用速查表（`research/` 下的 cheatsheet/commands 类笔记）
3. 如果通用部分已存在，**只创建项目专属部分**，并将通用部分 patch 到通用笔记中（\dt、\d 等属于 psql 通用知识，不放在项目笔记中）
