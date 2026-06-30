# `.env` 文件 source 陷阱

## 问题

Hermes 的 `~/.hermes/.env` 可能包含含特殊字符的值，例如：
```
WHATSAPP_ALLOWED_USERS=+!^)#%%&#%$^...
```

bash 的 `source .env` 会将其当作 shell 代码执行，特殊字符 `)` 导致语法错误：
```
未预期的记号 ")" 附近有语法错误
```

导致整个脚本挂死（同时 `set -e` 生效时）。

## 影响范围

- 任何需要读取 `.env` 中变量的 bash 脚本
- 涉及 `kb-index`、`hermes cron` 的自定义脚本
- `source ~/.hermes/.env` 的旧版 scripts

## 解决方案

### 方案 A：Python 解析（推荐）

用 Python 的 `splitlines()` + `partition("=")` 逐行解析，天然避免 shell 解释：

```python
HOME = Path.home()
env_file = HOME / ".hermes" / ".env"
for line in env_file.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    if k.strip() == key:
        return v.strip().strip("\"'").strip()
```

参见 `~/.local/bin/kb-index` (Python 版 Qdrant 索引脚本)。

### 方案 B：grep + cut（bash 安全版）

```bash
# 只取特定 key，不 source 整个文件
DEEPSEEK_API_KEY=*** '^DEEPSEEK_API_KEY=*** ~/.hermes/.env \
  | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '[:space:]')
```

### 方案 C：set +e 绕过

```bash
set +e
source ~/.hermes/.env 2>/dev/null
set -e
```

不推荐，因为错误只是被静音了，特殊字符仍可能导致未定义行为。

## 检查方法

```bash
# 快速测试 .env 是否能被安全 source
timeout 3 bash -c 'source ~/.hermes/.env && echo OK' 2>&1 || echo "FAILED"
```

## 已知受影响文件

| 文件 | 修复状态 |
|------|---------|
| *(旧脚本已全部删除，由 `kb-index` 取代)* | ✅ 已完成迁移 |
