# MCP 数据库查询服务器 — 完整配置指南

## 概述

一个自制的数据库查询 MCP 服务器，通过 stdio 传输注册到 Hermes，让 Agent 能直接查询 SQLite / PostgreSQL / MySQL 数据库。

## 脚本位置

`/home/andymao/.hermes/scripts/db_query_server.py`

## 前置依赖

MCP Python SDK 需安装在 Hermes venv 中：

```bash
~/.hermes/venv/bin/pip install "mcp>=1.6.0"
```

## 配置（config.yaml）

```yaml
mcp_servers:
  db-query:
    command: "/home/andymao/.hermes/venv/bin/python3"
    args: ["/home/andymao/.hermes/scripts/db_query_server.py"]
    env:
      DB_PATH: "~/.hermes/query_db.sqlite"
    timeout: 120
    connect_timeout: 30
    supports_parallel_tool_calls: true
```

## 数据库连接方式

### SQLite（默认）

通过 `DB_PATH` 环境变量指定 SQLite 文件路径。留空则默认 `~/.hermes/query_db.sqlite`。

```yaml
env:
  DB_PATH: "/path/to/database.db"
```

### PostgreSQL

```bash
~/.hermes/venv/bin/pip install psycopg2-binary
```

```yaml
env:
  DATABASE_URL: "postgresql://user:password@localhost:5432/dbname"
```

### MySQL

```bash
~/.hermes/venv/bin/pip install pymysql
```

```yaml
env:
  DATABASE_URL: "mysql://user:password@localhost:3306/dbname"
```

## 验证连接

```bash
hermes mcp test db-query
```

预期输出：`✓ Connected` + `✓ Tools discovered: 5` 并列出 5 个工具。

## 可用工具

| 工具 | 说明 | 参数 |
|------|------|------|
| `list_tables` | 列出所有表名 | 无 |
| `describe_table` | 查看表结构 | `table_name` |
| `query` | 执行 SELECT 查询 | `sql`（SQL语句）, `limit`（最大行数，默认100，上限1000） |
| `execute` | 执行 INSERT/UPDATE/DELETE | `sql` |
| `get_schemas` | 获取完整 Schema | 无 |

## 使用示例

会话中 Agent 自动获得这些工具。典型用法：

```
用户: 查询用户表中最近注册的5个用户
Agent: 调用 list_tables → 发现 users 表
       调用 describe_table(table_name="users") → 查看字段
       调用 query(sql="SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
```

## 重启生效

MCP 服务器在 Hermes 启动时加载。配置修改后：

- CLI 模式：退出重开 `hermes`，或当前会话执行 `/reset`
- Gateway 模式：`hermes gateway restart` 或 `/restart`
- 热重载：`/reload-mcp`

## 故障排查

### "Connection closed"

最常见原因：`command` 用了系统 `python3` 而非 venv python3。

```bash
# 诊断：直接启动服务器看是否有错误
/home/andymao/.hermes/venv/bin/python3 /home/andymao/.hermes/scripts/db_query_server.py
```

预期输出应包含 `"Starting MCP server on stdio..."`。如果报 `ModuleNotFoundError: No module named 'mcp'`，就是 python 路径问题。

### 数据库文件问题

SQLite 数据库不存在时会自动创建。如果想用已有数据库，确保路径正确。

### 超时

大型查询可以增加 `timeout`（默认 120s）和 `connect_timeout`（默认 30s）。
