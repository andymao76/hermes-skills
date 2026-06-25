# Hermes 持久记忆架构

## 两种记忆存储

Hermes 有两套独立的持久记忆系统，**数据不互通**：

### 1. `memory` 工具 → `~/.hermes/memory_store.db`（facts 表）

通过 `memory(action='add'/'replace'/'remove', target='memory'/'user')` 操作。
条目存储在 SQLite `facts` 表的 `content` 字段中，每个事实是一个独立行。
`replace` 通过 `old_text` 参数在 `content` 字段中模糊匹配查找（在匹配的条目内搜索，不是全表扫描）。
查询方式：`sqlite3 ~/.hermes/memory_store.db "SELECT fact_id, content FROM facts WHERE content LIKE '%xxx%';"`

### 2. 持久注入记忆文件 → `~/.hermes/memories/`（flat markdown）

| 文件 | 用途 | 对应工具 target |
|------|------|----------------|
| `~/.hermes/memories/MEMORY.md` | 系统笔记（环境事实、运维经验） | `memory(target='memory')` |
| `~/.hermes/memories/USER.md` | 用户画像（身份、偏好、规则） | `memory(target='user')` |

每轮对话系统提示词顶部的 `MEMORY` 和 `USER PROFILE` 段即来自这两个文件。

**重要：这两个文件的内容由 Hermes 会话启动时自动注入，但它们不是 `memory_store.db` 的一部分。** `memory` 工具完全操作 `memory_store.db`，**不接触**这两个 flat 文件。

### 故障场景：`memory replace` 返回 "No entry matched"

**可能原因：** 要修改的条目实际上在 `~/.hermes/memories/*.md` 中，不在 `memory_store.db` 的事实表中。

**排查步骤：**

```bash
# 1. 确认条目在 memory_store.db 中
sqlite3 ~/.hermes/memory_store.db "SELECT fact_id, content FROM facts WHERE content LIKE '%关键词%';"

# 2. 如果无结果，检查 flat 文件
grep "关键词" ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md

# 3. 如果条目在 flat 文件中，直接用 patch 或 sed 修改
sed -i 's/旧词/新词/g' ~/.hermes/memories/USER.md
sed -i 's/旧词/新词/g' ~/.hermes/memories/MEMORY.md
```

### 格式约定

两个 flat 文件使用 `§` 分隔符分行存储条目，每个条目独占一段：
```
关键事实一
§
关键事实二
§
关键事实三
```

格式转换由 Hermes 核心负责，agent 直接编辑文件时保持 `§` 分隔即可。

### 记忆容量

这两个文件合计有 ~2200 字符的容量上限（从系统提示词区域推断）。超限后需要清理/合并旧条目腾出空间。
