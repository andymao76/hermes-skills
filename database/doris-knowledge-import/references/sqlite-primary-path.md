# SQLite 主存储查询路径

当前 rhino01 实际使用中，SQLite 是知识库主存储，Doris 已停。

## 数据库位置

```
~/.hermes/query_db.sqlite
```

## 表结构

| 表 | 条数 | 说明 |
|---|---|---|
| knowledge_chunks | ~31,000 | 知识库 + Skills（tags='hermes-skills/xxx'） |
| telecom_skill | ~71,000 | 电信/LI 知识 |
| knowledge_fts | FTS5 索引 | 全文搜索虚拟表 |
| telecom_fts | FTS5 索引 | 全文搜索虚拟表 |
| docs | 原 SQLite 已有 | 通用文档 |
| market_report | 原 SQLite 已有 | 市场报告 |
| task_results | 原 SQLite 已有 | 任务结果 |

## 查询方式

通过 `db-query` MCP server 查询（无需启动任何额外服务）：

```sql
-- 全文搜索知识库
SELECT title, source_path FROM knowledge_fts 
WHERE knowledge_fts MATCH 'tcpdump SIP' LIMIT 10;

-- 精确搜索 LI 知识
SELECT title, content FROM telecom_skill 
WHERE content LIKE '%X2接口%' LIMIT 5;

-- 统计技能分类
SELECT tags, COUNT(*) FROM knowledge_chunks 
WHERE tags LIKE 'hermes-skills/%'
GROUP BY tags ORDER BY COUNT(*) DESC;
```

## 与 Doris 的关系

```
文件系统 (~/knowledge/, ~/.hermes/skills/)
    │
    ├──→ SQLite (~/.hermes/query_db.sqlite)  ← 主存储，日常查询用
    │       └── FTS5 全文索引
    │
    └──→ Doris (Docker, 已停)  ← 学习平台，docker start 后可用
            └── Stream Load 导入
```

## 全量重建

当文件系统内容变更后，SQLite 重建顺序：

1. `~/knowledge/` 内容 → knowledge_chunks + telecom_skill（含 FTS5）
2. `~/.hermes/skills/` 内容 → knowledge_chunks（tags='hermes-skills/xxx'，含 FTS5）

使用 `scripts/` 下的脚本按顺序执行。

## 大小

~412 MB（含 FTS5 索引），原始文件 ~1.9 GB。
