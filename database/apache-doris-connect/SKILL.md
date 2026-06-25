---
name: apache-doris-connect
description: Apache Doris Docker Quick Start 部署的连接配置、root 密码设置、专用账号创建
trigger: 当用户提到 Apache Doris、Doris 连接、Doris 账号、Doris 配置、Doris 建表、Doris 表设计时加载
---

# Apache Doris 连接与账号配置（Docker Quick Start）

## 连接默认信息

- **用户名**: `root`
- **密码**: 空（无密码）
- **端口**: 9030（MySQL 协议）
- **主机**: `127.0.0.1`（本地 Docker 部署）

## 连接测试

```bash
mysql -h 127.0.0.1 -P 9030 -u root
# 或
mysql -h 127.0.0.1 -P 9030 -u root -p
# 提示输入密码时直接回车
```

## 查看当前用户与权限

```sql
SELECT USER();
SHOW ALL GRANTS;
SHOW PROC '/access_resource';
```

## 设置 root 密码（生产环境必做）

```sql
ALTER USER 'root' IDENTIFIED BY 'YourStrongPassword123!';
```

## 角色账号设计（实际环境：rhino01 + Hermes Agent + HDP/GP）

| 账号 | 角色 | 权限 | 用途 |
|------|------|------|------|
| `root` | 管理员 | ADMIN_PRIV | 集群管理、账号管理 |
| `hermes` | AI 查询 | SELECT_PRIV ON telecom_ai.* | Hermes Agent 数据查询 |
| `flink_writer` | Flink 写入 | LOAD_PRIV / INSERT | Flink CDC/ETL 写入 |
| `kafka_loader` | Routine Load | LOAD_PRIV | Kafka Routine Load 导入 |
| `grafana` | 可视化 | SELECT_PRIV | Grafana 监控面板 |

### root（管理员）

```sql
ALTER USER 'root' IDENTIFIED BY 'YourStrongPassword123!';
```

### hermes（AI 查询）

```sql
CREATE USER 'hermes' IDENTIFIED BY 'Hermes@2026';
GRANT SELECT_PRIV ON telecom_ai.* TO 'hermes';
FLUSH PRIVILEGES;
```

### flink_writer（Flink 写入）

```sql
CREATE USER 'flink_writer' IDENTIFIED BY 'Flink@Doris2026';
GRANT LOAD_PRIV ON telecom_ai.* TO 'flink_writer';
FLUSH PRIVILEGES;
```

> 如只需 INSERT（不涉及 Stream Load），可用 `ALTER_PRIV + INSERT_PRIV`。

### kafka_loader（Routine Load）

```sql
CREATE USER 'kafka_loader' IDENTIFIED BY 'Kafka@Doris2026';
GRANT LOAD_PRIV ON telecom_ai.* TO 'kafka_loader';
FLUSH PRIVILEGES;
```

### grafana（可视化）

```sql
CREATE USER 'grafana' IDENTIFIED BY 'Grafana@Doris2026';
GRANT SELECT_PRIV ON telecom_ai.* TO 'grafana';
FLUSH PRIVILEGES;
```

## Hermes 配置

```yaml
doris:
  host: 127.0.0.1
  port: 9030
  user: hermes
  password: Hermes@2026
  database: telecom_ai
```

## Doris MCP 连接配置

通过 `hermes mcp add` 将 Doris 作为 MCP 服务器接入 Hermes：

> ⚠️ **`hermes mcp add --env` 陷阱**：`--env KEY=VALUE` 参数会被写入 `args` 列表中的 `--env KEY=VALUE` 参数，**而不是** `env:` 字典格式。Hermes MCP 服务器要求环境变量写在 `env:` 字典下才能正确传递到进程环境变量。
>
> 正确做法：先用 `hermes mcp add` 添加，然后手动编辑 `config.yaml` 将 `--env` args 改为 `env:` 字典格式：
>
> ```yaml
> # ❌ hermes mcp add 自动生成的错误格式（env 变为了 argv 参数）
>   doris:
>     command: /path/to/venv/bin/python3
>     args:
>     - /path/to/server.py
>     - --env
>     - KEY=VALUE      # 这只是 argv 参数，进程读不到环境变量
>
> # ✅ 需要手动修正为 dict 格式
>   doris:
>     args:
>     - /path/to/server.py
>     command: /path/to/venv/bin/python3
>     env:
>       KEY: VALUE     # 真正的进程环境变量
> ```
>
> 修正后重启 Hermes 或执行 `/reload-mcp` 使其生效。

通过通用 `db_query_server.py` 接入：

```bash
hermes mcp add doris \
  --command /home/andymao/.hermes/venv/bin/python3 \
  --args /home/andymao/.hermes/scripts/db_query_server.py \
  --env DATABASE_URL='mysql://root:PASSWORD@127.0.0.1:9030/hermes_ai'
```

连接成功后会注册 5 个 MCP 工具：
- `list_tables` — 列出所有表
- `describe_table` — 查看表结构
- `query` — 执行 SELECT 查询
- `execute` — 执行 INSERT/UPDATE/DELETE
- `get_schemas` — 获取完整 Schema

> 前提：`db_query_server.py` 已存在且支持 MySQL 协议（依赖 `pymysql`）。

密码含 `@`、`#`、`?`、`&` 等 URL 特殊字符时需 URL 编码（如 `@` → `%40`）。

添加后 `hermes mcp list` 确认状态，然后新建会话使用 MCP 工具。

## Doris SQL 语法注意事项

### 保留字需要反引号

一些 MySQL 保留字在 Doris 中也是保留字，用作列名/表名时必须反引号转义：

```sql
-- `join` 是 Doris 保留字
SELECT host, `join`, alive FROM frontends();
```

### FLUSH PRIVILEGES 不需要

Doris 权限变更即时生效，不支持 `FLUSH PRIVILEGES`：

```sql
-- ✅ 正确：GRANT 后直接生效
GRANT SELECT_PRIV ON hermes_ai.* TO 'hermes';

-- ❌ 错误：Doris 不支持 FLUSH PRIVILEGES
FLUSH PRIVILEGES;  -- syntax error
```

## 建表规范与常见陷阱

### DUPLICATE KEY 必须按列定义顺序前缀

Doris 的 DUPLICATE KEY 中的列必须是表定义列的**有序前缀**（从左到右连续），**不能跳过中间列**。

```
-- 表定义列顺序：liid, msisdn, event_type, event_time, cell_id
-- ✅ 正确：DUPLICATE KEY(liid, msisdn, event_type)
-- ❌ 错误：DUPLICATE KEY(liid, msisdn, event_time)  -- 跳过了 event_type
-- ❌ 错误：DUPLICATE KEY(liid, event_type)           -- 跳过了 msisdn
```

错误信息：`Key columns should be a ordered prefix of the schema.`

### 表结构参考

```sql
CREATE TABLE table_name (
    liid VARCHAR(64),
    msisdn VARCHAR(32),
    event_type INT,
    event_time DATETIME,
    cell_id VARCHAR(64),
    source_system VARCHAR(64)
)
DUPLICATE KEY(liid, msisdn, event_type)           -- 前3列，保持定义顺序
DISTRIBUTED BY HASH(liid) BUCKETS 4
PROPERTIES ("replication_num" = "1");              -- 单机版必须设1
```

> `replication_num`：单机版必须设为 `"1"`（默认 3），否则 BE 不足会导致建表失败。

## Doris SQL 查询注意事项

### UNION ALL 不支持混合类型

Doris 的 UNION ALL 要求所有分支返回相同列数和类型，**不支持在 SELECT 中混用字符串字面量和列值**：

```sql
-- ❌ 错误
SELECT 'hermes_sessions' AS table_name, COUNT(*) AS rows FROM hermes_sessions
UNION ALL
SELECT 'linux_logs', COUNT(*) FROM linux_logs;

-- ✅ 正确：分别查询
SELECT COUNT(*) AS hermes_sessions FROM hermes_sessions;
SELECT COUNT(*) AS linux_logs FROM linux_logs;
```

### 聚合查询中 GROUP BY 字段必须在 SELECT 中

```sql
-- ❌ 错误：tags not in aggregate's output
SELECT COUNT(*) AS chunks FROM knowledge_chunks WHERE tags = 'articles_baidu';

-- ✅ 正确：去掉 GROUP BY
SELECT COUNT(*) AS chunks FROM knowledge_chunks WHERE tags = 'articles_baidu';
```

### 聚类统计用 CASE WHEN 替代 GROUP BY + LEFT()

```sql
-- GROUP BY LEFT(message,180) 每条时间戳不同，结果全是 1
-- ✅ 用 CASE WHEN 聚类
SELECT
  CASE
    WHEN message LIKE '%Unavailable%' THEN 'Write failed'
    WHEN message LIKE '%timeout%' THEN 'Timeout'
    ELSE '其他'
  END AS error_type,
  COUNT(*) AS cnt
FROM linux_logs WHERE level='ERROR'
GROUP BY error_type;
```

### 中文模糊匹配用 LIKE 而非 REGEXP

Doris 的 `REGEXP` 运算符对中文多字节字符支持有限，中文模糊匹配推荐用 `LIKE`。

## 数据导入：使用 Stream Load（不支持 LOAD DATA）

Doris **不支持** MySQL 的 `LOAD DATA LOCAL INFILE` 语法。数据导入必须用 **Stream Load**（HTTP API）：

```bash
curl --location-trusted -u root:<PASSWORD> \
  -H "column_separator:," \
  -H "enclose:\"" \
  -H "columns: col1,col2,col3" \
  -T /path/to/data.csv \
  "http://127.0.0.1:8030/api/<database>/<table>/_stream_load"
```

关键参数：
- `enclose:\"` — CSV 字段用双引号包裹时必需
- `columns:` — 映射 CSV 列到表字段
- 大文件（>25MB）需分片导入，避免 Docker 单机内存溢出

详见 `doris-knowledge-import` 技能。

### 状态验证命令

```bash
# 查看 FE 状态
mysql -h127.0.0.1 -P9030 -uroot -e "SELECT host, \`join\`, alive FROM frontends();"

# 查看 BE 状态（注意 `join` 是保留字，需反引号）
mysql -h127.0.0.1 -P9030 -uroot -e "SELECT host, alive FROM backends();"
```

## 生产环境注意事项

- 不要对 root 使用空密码
- 各服务使用专用账号，不混用
- 按需授予最小权限
- flink_writer / kafka_loader 只需写入权限，不授予 SELECT 以外的查询权限
- 密码使用强密码，定期轮换
