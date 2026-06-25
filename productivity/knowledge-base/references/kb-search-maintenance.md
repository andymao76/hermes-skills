# kb-search.py 维护参考

## SQLite 游标批处理陷阱

`kb-search.py embed` 遍历 chunks 表时，如果使用 `for row in cursor.execute(...)` 并在循环内 `conn.commit()`，SQLite 游标会在 commit 后失效，循环只执行一次就退出。

**症状**：每次跑 embed 只处理 50 段就显示「✅ 嵌入完成: 50/72115」

**修复**：先将所有行读到内存再遍历：

```python
# ❌ 错误 — commit 使游标失效
for row in cursor.execute("SELECT ... WHERE embedding IS NULL"):
    batch.append(...)
    if len(batch) >= 50:
        conn.commit()  # ← 游标失效，循环退出

# ✅ 正确
all_rows = list(cursor.execute("SELECT ... WHERE embedding IS NULL"))
for row in all_rows:
    batch.append(...)
    if len(batch) >= 50:
        conn.commit()  # 安全，遍历的是内存列表
```

验证：`python3 ~/.hermes/scripts/kb-search.py status` 看嵌入数持续增长

## 嵌入耗时估算

- 分段总数: 72,115（608 文件）
- 批大小: 50 段/批
- 每批耗时: ~2-5 秒（SiliconFlow API）
- 总耗时: ~60-90 分钟
- 模型: Qwen/Qwen3-Embedding-8B (dim=1024)

## API 超时处理

SiliconFlow API 偶尔 Read timeout，嵌入进程退出。kb-search.py 可重入：
- 已嵌入的 chunk 自动跳过（`WHERE embedding IS NULL`）
- 直接重新运行 `embed` 继续剩余部分
- 建议后台运行：`python3 ~/.hermes/scripts/kb-search.py embed &`

## 增量更新流程

```bash
# 知识库新增文件后：
python3 ~/.hermes/scripts/kb-search.py refresh   # 重建 FTS5 索引（增量）
python3 ~/.hermes/scripts/kb-search.py embed      # 补嵌新分段的向量
```

## 搜索结果解读

- `🔑 关键词` — FTS5 全文匹配结果（按 BM25 排序）
- `🧠 语义` — 向量语义相似度结果（按 cos similarity 排序）
- 两者混合去重，优先展示关键词结果
- 语义搜索需要 API Key（SiliconFlow），纯 FTS5 离线可用
