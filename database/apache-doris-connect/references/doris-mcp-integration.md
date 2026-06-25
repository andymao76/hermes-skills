# Doris MCP 集成参考

## `hermes mcp add` 注意事项

> ⚠️ **`--env` 陷阱**：用 `hermes mcp add --env KEY=VALUE` 添加后，环境变量会被写入 `args` 列表（以 `--env KEY=VALUE` 形式），**不会**变成 `env:` 字典。需手动编辑 config.yaml 修正。

### 添加命令（参考）

```bash
hermes mcp add doris \
  --command /home/andymao/.hermes/venv/bin/python3 \
  --args /home/andymao/.hermes/scripts/db_query_server.py \
  --env DATABASE_URL='mysql://root:***@127.0.0.1:9030/hermes_ai'
```

### 修正后的 config.yaml 格式

```yaml
  doris:
    args:
    - /home/andymao/.hermes/scripts/db_query_server.py
    command: /home/andymao/.hermes/venv/bin/python3
    env:
      DATABASE_URL: 'mysql://root:***@127.0.0.1:9030/hermes_ai'
    timeout: 120
```

参数说明：
- `name` = `doris` — MCP 服务名，自动成为工具名前缀
- `--command` = venv 的 Python 解释器
- `--args` = `db_query_server.py` 脚本路径
- `env:` 字典中的键值对为实际注入的环境变量

## `db_query_server.py` 数据库协议支持

该脚本位于 `~/.hermes/scripts/db_query_server.py`，通过 `DATABASE_URL` 环境变量判断数据库类型：

| URL 协议 | 支持 | Python 依赖 | 数据库 |
|----------|------|-------------|--------|
| `mysql://` | ✅ | `pymysql` | Doris、MySQL |
| `postgresql://` | ✅ | `psycopg2-binary` | PostgreSQL |
| 无（仅 `DB_PATH`） | ✅ | 内置 | SQLite（默认） |

## 工具清单

| 工具 | 用途 | 典型查询 |
|------|------|---------|
| `list_tables` | 列出所有表 | 无参数 |
| `describe_table` | 查看表结构 | `table_name` 参数 |
| `query` | SELECT 查询 | `sql` + 可选 `limit` |
| `execute` | 写操作 SQL | `sql` 参数 |
| `get_schemas` | 完整 Schema | 无参数 |

## 密码中的 URL 特殊字符

| 原字符 | 编码 | 原因 |
|--------|------|------|
| `@` | `%40` | 会被解析为主机分隔符 |
| `#` | `%23` | 会被解析为片段标识 |
| `?` | `%3F` | 会被解析为查询参数 |
| `&` | `%26` | 会被解析为参数分隔符 |
| 空格 | `%20` | 明显不能直接出现 |

示例（密码为 `P@ss#1`）：
```
DATABASE_URL='mysql://root:***@127.0.0.1:9030/hermes_ai'
```
