---
name: doris-knowledge-import
description: 知识库全量导入与查询——SQLite 主存储 + Doris 学习平台。覆盖 CSV 导入/导出、FTS5 全文索引、Stream Load、中文字节截断、内存限制处理、全量重建。
---

# Knowledge Database Pipeline

将 ~/knowledge/（Obsidian vault）和 ~/.hermes/skills/ 切片后导入数据库，支持 SQLite 和 Doris 两种后端。

## 数据库选型

| 场景 | 推荐 | 原因 |
|---|---|---|
| 个人单机（≤100万条） | **SQLite + FTS5** | 0 守护进程、0 内存占用、毫秒级全文搜索 |
| 学习/试验 Doris | **Doris Docker** | 单机版（1 FE + 1 BE），不分离 |
| 生产集群（百亿级 CDR） | **Doris 3 FE + 3 BE** | 需负载均衡，Observer 节点 |
| 向量检索 + SQL 混合 | **Doris 4.x+** | 向量索引 + 全文检索 + Hybrid Search |

**当前 rhino01 配置：** SQLite 主存储（412MB, 102K 条），Doris Docker 已停作为学习平台。

## 触发条件

- 用户说"重建知识库索引"、"更新知识库"、"把知识导入 Doris/SQLite"
- 知识库文件（~/knowledge/）或技能文件（~/.hermes/skills/）新增或修改后需要同步
- 需要查询本地知识/技能内容

## 前置条件

- Doris Docker 运行中（端口 9030 MySQL, 8030 HTTP Stream Load）
- `root` 密码在 memory 中（Doris root 密码: tgehltb5）
- 表结构已存在：`knowledge_chunks`（通用知识）、`telecom_skill`（电信/LI 知识）、`hermes_sessions`（会话日志）、`linux_logs`（系统日志）
- pymysql 可用（用 `~/.hermes/venv/bin/python3`）

## 步骤

### 1. 准备 CSV

```python
# gen_csv.py — 遍历 ~/knowledge/ 生成 CSV
import csv, os, re, hashlib

KB = os.path.expanduser("~/knowledge")
TELECOM_PREFIXES = ["/telecom/", "/li/", "/移动通信相关/", "/3gpp-references/", "/3gpp-ts33108/", "/hi2/", "/A1/"]
EXCLUDE_DIRS = {".obsidian", ".git", "_system", "secrets", "cache", "__pycache__", ".trash", "04_ARCHIVE", "00_INBOX"}
TEXT_EXT = {".md", ".txt", ".json", ".yaml", ".yml", ".cfg", ".conf", ".ini"}

def truncate_bytes(s, max_bytes=250):
    """按字节截断，确保不截断多字节字符（中文 3 字节/字）"""
    encoded = s.encode('utf-8')[:max_bytes]
    while encoded and (encoded[-1] & 0xC0) == 0x80:
        encoded = encoded[:-1]
    return encoded.decode('utf-8', errors='replace')

def is_telecom(path):
    rel = path.replace(KB, "")
    return any(p in rel for p in TELECOM_PREFIXES)

def chunk_content(content, title, source_path, max_chars=3000):
    chunks = []
    content = content.strip()
    if len(content) < 20:
        return chunks
    sections = re.split(r'\n(?=##\s)', content)
    if len(sections) <= 1:
        chunks.append((truncate_bytes(title, 250), content[:max_chars], source_path))
    else:
        for sec in sections:
            sec = sec.strip()
            if len(sec) < 20:
                continue
            h2 = re.search(r'^##\s+(.+)', sec, re.MULTILINE)
            subtitle = title[:200]
            if h2:
                subtitle = f"{title[:100]} > {h2.group(1).strip()[:180]}"[:200]
            for i in range(0, len(sec), max_chars):
                chunk_text = sec[i:i+max_chars]
                chunk_title = subtitle if i == 0 else f"{subtitle[:180]} (续{i//max_chars+1})"[:200]
                chunks.append((truncate_bytes(chunk_title, 250), chunk_text, source_path))
    return chunks

seen_hashes = set()
total_files = 0

with open("/tmp/knowledge_chunks.csv", "w", newline="", encoding="utf-8") as f_kb, \
     open("/tmp/telecom_skill.csv", "w", newline="", encoding="utf-8") as f_tel:
    w_kb = csv.writer(f_kb, quoting=csv.QUOTE_ALL)
    w_tel = csv.writer(f_tel, quoting=csv.QUOTE_ALL)
    for root, dirs, files in os.walk(KB):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            if os.path.splitext(fname)[1].lower() not in TEXT_EXT:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except:
                continue
            if len(content.strip()) < 20:
                continue
            total_files += 1
            title = fname.replace(".md", "").replace(".txt", "")[:200]
            path_parts = fpath.replace(KB, "").strip("/").split("/")
            tags = path_parts[0] if path_parts else "unknown"
            rel_path = fpath.replace(KB, "~")
            for chunk_title, chunk_text, src in chunk_content(content, title, rel_path):
                h = hashlib.md5(chunk_text.encode()).hexdigest()
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                if is_telecom(fpath):
                    li_level = "5" if ("/li/" in rel_path or "/A1/" in rel_path) else "0"
                    w_tel.writerow([chunk_title, chunk_text, tags, rel_path, li_level])
                else:
                    w_kb.writerow([chunk_title, chunk_text, tags, rel_path])

print(f"总文件: {total_files}")
print(f"knowledge_chunks.csv: {os.path.getsize('/tmp/knowledge_chunks.csv')/1024/1024:.1f} MB")
print(f"telecom_skill.csv: {os.path.getsize('/tmp/telecom_skill.csv')/1024/1024:.1f} MB")
```

### 2. 清空旧数据

```bash
mysql -h127.0.0.1 -P9030 -uroot -p<PASSWORD> -D hermes_ai \
  -e "TRUNCATE TABLE knowledge_chunks; TRUNCATE TABLE telecom_skill;"
```

### 3. Stream Load 导入

**knowledge_chunks**（通常一次成功）：
```bash
curl --location-trusted -u root:<PASSWORD> \
  -H "column_separator:," \
  -H "enclose:\"" \
  -H "columns: title,content,tags,source_path" \
  -T /tmp/knowledge_chunks.csv \
  "http://127.0.0.1:8030/api/hermes_ai/knowledge_chunks/_stream_load"
```

**telecom_skill**（数据量大，需要分片）：
```bash
# 按 20000 行分片
python3 -c "
import csv, os
rows = []
with open('/tmp/telecom_skill.csv') as f:
    for row in csv.reader(f):
        rows.append(row)
SPLIT = 20000
for part in range(0, len(rows), SPLIT):
    out = f'/tmp/telecom_skill_part{part//SPLIT+1}.csv'
    with open(out, 'w', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        for r in rows[part:part+SPLIT]:
            w.writerow(r)
    print(f'{out}: {os.path.getsize(out)/1024/1024:.1f} MB')
"

# 逐片导入
for f in /tmp/telecom_skill_part*.csv; do
  echo "=== $f ==="
  curl --location-trusted -u root:<PASSWORD> \
    -H "column_separator:," -H "enclose:\"" \
    -H "columns: title,content,tags,source_path,li_level" \
    -T "$f" "http://127.0.0.1:8030/api/hermes_ai/telecom_skill/_stream_load" \
    2>&1 | grep -E '"Status"|"NumberLoadedRows"'
  sleep 2
done
```

### 4. 验证

```bash
mysql -h127.0.0.1 -P9030 -uroot -p<PASSWORD> -D hermes_ai -e "
SELECT 'knowledge_chunks' AS t, COUNT(*) AS r FROM knowledge_chunks
UNION ALL SELECT 'telecom_skill', COUNT(*) FROM telecom_skill;
"
```

## 表结构

### knowledge_chunks
```sql
CREATE TABLE knowledge_chunks (
    id BIGINT, title VARCHAR(256), content TEXT,
    category VARCHAR(64), tags VARCHAR(256),
    source_path VARCHAR(512), created_at DATETIME
) DUPLICATE KEY(id) DISTRIBUTED BY HASH(id) BUCKETS 1
PROPERTIES("replication_num"="1");
```

### telecom_skill
```sql
CREATE TABLE telecom_skill (
    id BIGINT, title VARCHAR(256), content TEXT,
    category VARCHAR(64), tags VARCHAR(256),
    source_path VARCHAR(512), li_level INT, created_at DATETIME
) DUPLICATE KEY(id) DISTRIBUTED BY HASH(id) BUCKETS 1
PROPERTIES("replication_num"="1");
```

---

## 参考文件

- `references/sqlite-primary-path.md` — SQLite 主存储查询路径（当前 rhino01 使用中）
- `references/sqlite-fallback.md` — Doris → SQLite 降级迁移的完整脚本
- `references/full-table-schemas.md` — hermes_ai 库完整 4 表结构
- `references/hermes-skills-import.md` — Skills 导入变体（扫描 `~/.hermes/skills/`）
- `references/li-vendor-map.md` — LI 产品厂商对照（ZTLIG = Sinovatio 中新赛克）
- `scripts/gen_kb_csv.py` — CSV 生成脚本（knowledge 源）
- `scripts/gen_skills_csv.py` — CSV 生成脚本（skills 源）

## 全量重建

当文件系统已修正（如 ZTLIG 厂商名修改），需要重建 Doris 知识库时：

```bash
# 1. 确认磁盘文件已修正（Doris 数据只是副本，源文件 ~/knowledge/ 和 ~/.hermes/skills/）
# 2. 生成 knowledge CSV + telecom_skill CSV
SKILL_DIR=$(dirname $(dirname $(dirname $(realpath \$0 2>/dev/null)))) 2>/dev/null
# 或用绝对路径:
/home/andymao/.hermes/venv/bin/python3 ~/.hermes/skills/database/doris-knowledge-import/scripts/gen_kb_csv.py
# 3. 生成 hermes skills CSV
/home/andymao/.hermes/venv/bin/python3 ~/.hermes/skills/database/doris-knowledge-import/scripts/gen_skills_csv.py
# 4. 清空并导入 knowledge_chunks（两轮 Stream Load）
mysql -h127.0.0.1 -P9030 -uroot -p<PASSWORD> -D hermes_ai -e "TRUNCATE TABLE knowledge_chunks;"
curl -u root:<PASSWORD> -H "column_separator:," -H "enclose:\"" -H "columns: title,content,tags,source_path" \
  -T /tmp/knowledge_chunks.csv "http://127.0.0.1:8030/api/hermes_ai/knowledge_chunks/_stream_load"
curl -u root:<PASSWORD> -H "column_separator:," -H "enclose:\"" -H "columns: title,content,tags,source_path" \
  -T /tmp/hermes_skills.csv "http://127.0.0.1:8030/api/hermes_ai/knowledge_chunks/_stream_load"
# 5. telecom_skill 分片导入 + INSERT 回退
# 分片 Stream Load 不成功时，用以下 Python 补入：
python3 -c "
import pymysql, csv
conn = pymysql.connect(host='127.0.0.1', port=9030, user='root', password='<PASSWORD>', database='hermes_ai', autocommit=True)
cur = conn.cursor()
rows = []
with open('/tmp/failed_chunk.csv') as f:
    for r in csv.reader(f):
        rows.append(r)
BATCH=50
for i in range(0, len(rows), BATCH):
    batch = rows[i:i+BATCH]
    vals = []
    for r in batch:
        vals.extend(r)
    sql = 'INSERT INTO telecom_skill (title, content, tags, source_path, li_level) VALUES ' + \
          ','.join('(%s,%s,%s,%s,%s)' for _ in batch)
    cur.execute(sql, vals)
print(f'补入 {len(rows)} 条')
conn.close()
"
```

### 磁盘优先原则

Doris 数据是文件系统的副本。**永远先修正磁盘文件**，再重新生成 CSV 覆盖导入。Doris DUPLICATE KEY 不支持直接 UPDATE。

正确顺序：
```
磁盘文件修正 (sed/patch)
  → 重新生成 CSV (gen_kb_csv.py / gen_skills_csv.py)
  → TRUNCATE 旧表
  → Stream Load 覆盖
```

## 坑

1. **Doris DUPLICATE KEY 必须是最左前缀列** — 定义的列顺序必须与 CREATE TABLE 中前 N 列一致
2. **VARCHAR(n) 是字节限制** — 中文 UTF-8 占 3 字节/字，标题需要用 `truncate_bytes()` 截断到 ≤250 字节
3. **Docker 单机内存 13 GB 限制** — Doris BE 内存软限约 12.5GB，大文件（>30MB CSV）需分片导入（每片 ≤20,000 行或 ≤25MB）
4. **CSV 引号** — 内容含逗号和换行的字段必须用 `quoting=csv.QUOTE_ALL` + Stream Load 传 `enclose:\"`
5. **`li_level=5` 的 LI 机密数据永远不出 Doris** — 只存在于 telecom_skill 表，Hermes 可在本地查询但不外发到在线 LLM
6. **Stream Load 偶发 MEM_LIMIT_EXCEEDED** — Docker 单机 13GB 限制下，即使 25MB 分片也可能被拒绝。拆到 ≤1,000 行/片，仍失败则用 INSERT 追加（见 5. 的 Python 回退脚本）
7. **磁盘优先原则** — Doris DUPLICATE KEY 不支持 UPDATE/DELETE。修正数据必须：修磁盘文件 → 重新生成 CSV → TRUNCATE → Stream Load。不要尝试在 Doris 里直接 UPDATE。