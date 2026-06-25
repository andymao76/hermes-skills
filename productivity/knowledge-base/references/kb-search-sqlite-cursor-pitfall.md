# SQLite 游标陷阱：循环内 commit() 导致游标失效

## 问题

在 Python `sqlite3` 中，**在 `for row in cursor.execute(...)` 循环体内调用 `conn.commit()` 会导致游标被隐式关闭**，循环只处理一批数据就退出。

```python
# ❌ 错误写法：只处理第一行就退出
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for row in cursor.execute("SELECT id, content FROM chunks WHERE embedding IS NULL"):
    batch.append(row)
    if len(batch) >= BATCH_SIZE:
        # ... 处理 batch ...
        conn.commit()           # ← 这行杀死游标
        batch = []
# 永远不会进入第二次循环
```

## 原因

SQLite 在 `commit()` 时会关闭所有打开的 `SELECT` 语句的游标。这是 SQLite 的行为规范，不是 Python 的 bug。Python 的 `cursor.execute()` 返回的迭代器会检测游标已关闭，于是 `for` 循环静默结束。

## 修复

**方案 A（推荐）：先将所有结果读到内存**

```python
# ✅ 正确写法：先把所有行拉到列表，再遍历处理
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

all_rows = list(cursor.execute("SELECT id, content FROM chunks WHERE embedding IS NULL"))
for row in all_rows:             # ← 遍历内存列表，而非游标
    batch.append(row)
    if len(batch) >= BATCH_SIZE:
        # ... 处理 batch ...
        conn.commit()            # ← commit() 安全，因为游标已耗尽
        batch = []
```

**方案 B：不在循环内 commit，改为循环结束后统一 commit**

仅适用于小数据量（几百行以内）。大数据量时内存占用和中断风险过高。

## 可用于侦测此问题的 SQLite 设置

```python
conn.execute("PRAGMA journal_mode=WAL")  # WAL 模式下 commit 不阻塞读
```

但这不影响游标关闭行为 — WAL 只影响并发读写，不改变事务提交时的游标语义。

## 来源

在 `kb-search.py` 的 `cmd_embed()` 函数中发现并修复。该函数遍历 72,115 个文本分段，每批 50 段调用一次 SiliconFlow embedding API，循环内 `commit()` 保存进度。修复前每次只处理 50 段（1 批），修复后正确处理全部 72,115 段。
