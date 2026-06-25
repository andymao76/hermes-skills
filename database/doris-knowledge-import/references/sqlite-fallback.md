# Doris → SQLite 降级迁移

当 Doris 占用资源过多（FE ~41% CPU + 5.8G 内存，BE ~14% CPU + 1G 内存），而日常只需要知识库查询时，可将数据迁移到 SQLite FTS5，停掉 Doris。

## 适用场景

- 个人单机环境，Doris 杀鸡用牛刀
- 机器内存/CPU 不足（如 i7-8550U 4核8线程）
- 只需要全文搜索，不需要实时分析
- 准备升级硬件前暂存索引数据

## 前置条件

- Doris 仍在运行（需要从中导出数据）
- db-query MCP 连接指向 `~/.hermes/query_db.sqlite`
- SQLite 支持 FTS5（Python 3 内置）

## 迁移步骤

### 1. 从 Doris 导出数据

使用 MySQL 客户端以 tab 分隔导出（注意替换内容中的换行符和逗号）：

```bash
# knowledge_chunks（不含 hermes-skills 前缀）
mysql -h127.0.0.1 -P9030 -uroot -p<PASSWORD> -D hermes_ai -N -e "
SELECT id, REPLACE(title,',','，'), REPLACE(REPLACE(content,'\n',' '),',','，'), tags, source_path
FROM knowledge_chunks
WHERE tags NOT LIKE 'hermes-skills/%'
" > /tmp/kb_export.csv

# telecom_skill
mysql -h127.0.0.1 -P9030 -uroot -p<PASSWORD> -D hermes_ai -N -e "
SELECT id, REPLACE(title,',','，'), REPLACE(REPLACE(content,'\n',' '),',','，'), tags, source_path, li_level
FROM telecom_skill
" > /tmp/tel_export.csv
```

注意：`REPLACE(content,'\n',' ')` 去掉换行避免破坏 tab 分隔。
MySQL `-N -e` 输出是 tab 分隔的，如果 content 本身包含 tab 会破坏列结构。
如果导入 sqlite3 时报 `datatype mismatch`，检查 id 列是否有 NULL。

### 2. 创建 SQLite 表 + FTS5 索引

```python
import sqlite3, os

DB = os.path.expanduser("~/.hermes/query_db.sqlite")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 建表（不含强制 id，让 SQLite 自增）
cur.executescript("""
DROP TABLE IF EXISTS knowledge_chunks;
DROP TABLE IF EXISTS telecom_skill;
CREATE TABLE knowledge_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, content TEXT, tags TEXT, source_path TEXT
);
CREATE TABLE telecom_skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, content TEXT, tags TEXT, source_path TEXT,
    li_level INTEGER DEFAULT 0
);
""")

# 导入 knowledge_chunks
with open("/tmp/kb_export.csv") as f:
    for line in f:
        parts = line.strip().split("\t", 4)
        if len(parts) >= 5:
            cur.execute("INSERT INTO knowledge_chunks (title, content, tags, source_path) VALUES (?,?,?,?)",
                        (parts[1] if parts[1] != 'NULL' else '', parts[2], parts[3], parts[4]))

# 导入 telecom_skill
with open("/tmp/tel_export.csv") as f:
    for line in f:
        parts = line.strip().split("\t", 5)
        if len(parts) >= 6:
            li_level = int(parts[5]) if parts[5].isdigit() else 0
            cur.execute("INSERT INTO telecom_skill (title, content, tags, source_path, li_level) VALUES (?,?,?,?,?)",
                        (parts[1] if parts[1] != 'NULL' else '', parts[2], parts[3], parts[4], li_level))
conn.commit()

# FTS5 全文索引
cur.execute("CREATE VIRTUAL TABLE knowledge_fts USING fts5(title, content, tags, source_path)")
cur.execute("INSERT INTO knowledge_fts SELECT title, content, tags, source_path FROM knowledge_chunks")

cur.execute("CREATE VIRTUAL TABLE telecom_fts USING fts5(title, content, tags, source_path)")
cur.execute("INSERT INTO telecom_fts SELECT title, content, tags, source_path FROM telecom_skill")
conn.commit()
conn.close()
```

### 3. 验证迁移

```bash
# 检查表可见性
sqlite3 ~/.hermes/query_db.sqlite ".tables" | grep -E "knowledge|telecom"

# 测试全文搜索
sqlite3 ~/.hermes/query_db.sqlite "SELECT title FROM knowledge_fts WHERE knowledge_fts MATCH 'tcpdump' LIMIT 5;"
sqlite3 ~/.hermes/query_db.sqlite "SELECT title FROM telecom_fts WHERE telecom_fts MATCH 'VoLTE X2' LIMIT 5;"

# 检查行数
sqlite3 ~/.hermes/query_db.sqlite "SELECT 'knowledge', COUNT(*) FROM knowledge_chunks UNION ALL SELECT 'telecom', COUNT(*) FROM telecom_skill;"
```

### 4. 停掉 Doris

```bash
docker stop doris-fe-1 doris-be-1
# 数据在 Docker 数据卷上，docker start 即可恢复
```

## 恢复 Doris

将来升级硬件或需要分析能力时：

```bash
docker start doris-fe-1 doris-be-1
# 等待 FE/BE 就绪后，用 skills/base 下的 gen_csv.py 重新导入
# 或者从 SQLite 导出后 Stream Load 回去
```

## 已知问题

1. **中文 FTS5 分词** — SQLite FTS5 默认按 unicode 文本分割，中文按字索引（不按词）。对中文关键词搜索需要全词匹配，不像 Doris 的 ngram。影响不大，LI 文档中英文混写为主。
2. **内容截断** — Doris 导出时 `REPLACE(content,'\n',' ')` 会丢失换行结构，但全文搜索匹配不受影响。查看完整原文应直接打开 `source_path`。
3. **CSV 大小** — 85K 条数据约 130MB CSV/6分钟导入。如果 SQLite 插入慢，可用 `conn.execute("PRAGMA synchronous=OFF")` 加速。
