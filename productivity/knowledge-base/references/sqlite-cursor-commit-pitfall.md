# SQLite 游标在迭代中 commit 会失效

## 问题

在 Python sqlite3 中，**在 for 循环迭代 cursor.execute() 的过程中调用 `conn.commit()`，会导致游标失效**，循环被静默截断只执行一次。

## 症状

```python
# ❌ 错误写法 — 游标只取到第一批数据就退出
for row in cursor.execute("SELECT id, content FROM chunks WHERE embedding IS NULL"):
    batch.append(row)
    if len(batch) >= BATCH_SIZE:
        # ... 处理 batch
        conn.commit()  # ⚠️ 这里 commit 导致 cursor 失效
        batch = []
# 循环提前结束，只处理了第一批
```

## 修复

```python
# ✅ 正确写法 — 先把所有数据读到内存
all_rows = list(cursor.execute("SELECT id, content FROM chunks WHERE embedding IS NULL"))
for row in all_rows:
    batch.append(row)
    if len(batch) >= BATCH_SIZE:
        # ... 处理 batch
        conn.commit()  # ✅ 安全了，游标已释放
        batch = []
# 循环正常处理所有数据
```

## 原理

SQLite3 的游标在迭代期间持有内部事务锁。`conn.commit()` 会释放该锁，导致游标被标记为"已耗尽"。Python 的 `for row in cursor` 在内部通过 `fetchone()` 逐行迭代——一旦游标耗尽，迭代器就返回 StopIteration。

用 `list(cursor.execute(...))` 会在迭代开始前将全部数据加载到内存，释放游标，后续的 commit 不再影响已加载的数据。

## 适用范围

- 批量处理大量数据（数千行+）
- 需要在处理过程中定期 commit（防内存暴涨 + 断电保护）
- 任何 `for row in cursor: ... conn.commit()` 的代码

## 测试方法

```python
# 在 commit 前后检查游标状态
cursor = conn.execute("SELECT COUNT(*) FROM big_table")
count_before = cursor.fetchone()[0]  # 正常
conn.commit()
try:
    count_after = cursor.fetchone()[0]  # ❌ 抛出异常或返回错误值
except Exception as e:
    print(f"游标已死: {e}")
```
