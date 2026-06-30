# kb-index 语义索引刷新指南

## 背景

`kb-index` 是知识库的本地语义索引工具，基于 TF-IDF + LSA，零网络调用。已完全替代旧版 Enzyme 刷新流程。

**旧版 Enzyme**（已废弃）：`enzyme refresh` 依赖云端信用额度（3 credits/task），余额不足时静默失败。2026-06-26 从 Hermes 技能列表移除，二进制残留 `~/.local/bin/enzyme` 建议手动删除。

## 刷新命令

### 增量刷新（推荐，日常使用）
```bash
kb-index
# 自动检测变更文件，只重新索引有变动的部分
```

### 全量重建（目录结构变更后使用）
```bash
kb-index --full
# 丢弃旧索引，完全重新构建
```

### 语义搜索
```bash
kb-index search "关键词"
# 返回 TF-IDF + LSA 相似度排序的文档列表
```

### 查看状态
```bash
kb-index status
# 显示文档数、索引分片数、最后刷新时间
```

## 故障排查

### `kb-index: command not found`
```bash
# kb-index 是一个本地脚本，检查是否在 ~/.local/bin/
ls -la ~/.local/bin/kb-index

# 如果不存在，从知识备份恢复
cp ~/knowledge/_system/scripts/kb-index ~/.local/bin/
chmod +x ~/.local/bin/kb-index
```

### 依赖缺失：`ModuleNotFoundError: No module named 'sklearn'`
```bash
# kb-index 依赖 Hermes venv 中的 scikit-learn
source ~/.hermes/venv/bin/activate
pip install scikit-learn numpy scipy
```

### 索引搜索无结果
```bash
kb-index --full   # 全量重建后重试
kb-index status   # 确认文档数 > 0
```

## 回退方案：FTS5 全文搜索

如果 kb-index 不可用，回退到 FTS5：

```bash
cd ~/knowledge && python3 ~/.hermes/scripts/kb-search.py refresh
python3 ~/.hermes/scripts/kb-search.py search "关键词"
```

FTS5 的局限：不支持中文分词，中文搜索需用英文字词或单字匹配。
