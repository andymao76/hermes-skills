# 百度网盘导入 → 知识库 事后核查协议

在 `baidupan_convert.py` 完成导入后，执行以下三步标准核查。

## 核查流程

### 第一步：检查遗漏

```python
from pathlib import Path

baidu = Path.home() / "baidupan_docs"
knowledge = Path.home() / "knowledge"

# 百度网盘可转换文件（去扩展名）
src_stems = set()
for ext in ['*.pdf', '*.doc', '*.docx', '*.txt', '*.htm', '*.html']:
    for f in baidu.rglob(ext):
        if "excluded" not in str(f):
            src_stems.add(f.stem)

# 知识库已导入文件（去扩展名）
kb_stems = set()
for ext in ['*.md', '*.txt']:
    for f in knowledge.rglob(ext):
        kb_stems.add(f.stem)

missing = src_stems - kb_stems
if missing:
    print(f"遗漏 {len(missing)} 个: {sorted(missing)}")
else:
    print("零遗漏 ✓")
```

### 第二步：检查 FTS5 索引

```python
import sqlite3, os
db = '/home/andymao/.hermes/knowledge_index.db'

# 1) 索引必须存在
assert os.path.exists(db), "索引文件不存在"

conn = sqlite3.connect(db)

# 2) 索引记录数应与知识库 .md 文件数一致
kb_count = len(list(Path.home().joinpath("knowledge").rglob("*.md")))
fts_count = conn.execute('SELECT COUNT(*) FROM knowledge_fts').fetchone()[0]
print(f"知识库文件: {kb_count}, 索引记录: {fts_count}")

# 3) 搜索测试
for kw in ['3GPP', 'IMS', 'VoLTE', '5G', 'SIP', 'LTE']:
    c = conn.execute('SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH ?', (kw,)).fetchone()[0]
    print(f"  '{kw}': {c} 条")
```

### 第三步：确认 index 已优化（搜索应在毫秒级）

```python
import time
t0 = time.time()
_ = conn.execute("SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH 'IMS'").fetchone()
print(f"搜索耗时: {(time.time()-t0)*1000:.0f}ms")
# 应 < 10ms；若超时 → 执行优化：
conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('optimize')")
conn.commit()
```

## 核查通过标准

| 检查项 | 预期值 |
|--------|--------|
| 遗漏数 | 0 |
| 索引记录 vs .md 文件数 | 一致 |
| 搜索耗时 | < 10ms |
| 各关键词命中 | > 0 |

## 增量导入场景

如果只是补充下载了几个新文件，只需：

```bash
python3 ~/.hermes/scripts/baidupan_convert.py --input ~/baidupan_docs/xxx/ 2>&1
```

脚本自动跳过已存在文件。然后执行上面的三步核查确认无遗漏。
