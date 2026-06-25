# hermes_ai 数据库完整表结构

## 1. hermes_sessions — Hermes Agent 会话记录

```sql
CREATE TABLE IF NOT EXISTS hermes_sessions (
    ts DATETIME,
    session_id VARCHAR(64),
    model VARCHAR(64),
    provider VARCHAR(32),
    tokens_in BIGINT,
    tokens_out BIGINT,
    tokens_cache BIGINT,
    latency_sec FLOAT,
    api_calls INT,
    tool_turns INT,
    turn_reason VARCHAR(64),
    response_len INT
)
DUPLICATE KEY(ts, session_id)
DISTRIBUTED BY HASH(session_id) BUCKETS 1
PROPERTIES("replication_num" = "1");
```

来源：解析 `~/.hermes/logs/agent.log` 中的 `Turn ended` 和 `API call` 行。

## 2. linux_logs — 系统日志

```sql
CREATE TABLE IF NOT EXISTS linux_logs (
    logtime DATETIME,
    service VARCHAR(64),
    host VARCHAR(32),
    level VARCHAR(16),
    message STRING
)
DUPLICATE KEY(logtime, service)
DISTRIBUTED BY HASH(service) BUCKETS 1
PROPERTIES("replication_num" = "1");
```

来源：`journalctl --no-pager --output=short-iso` 输出解析。注意系统 locale 为 zh_CN.UTF-8，必须用 `--output=short-iso` 避免中文月份解析失败。

## 3. knowledge_chunks — 通用知识库 + Hermes Skills

```sql
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id BIGINT,
    title VARCHAR(256),
    content TEXT,
    category VARCHAR(64),
    tags VARCHAR(256),
    source_path VARCHAR(512),
    created_at DATETIME
)
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 1
PROPERTIES("replication_num" = "1");
```

来源：`~/knowledge/`（Obsidian vault）+ `~/.hermes/skills/`。
Skills 标签统一前缀 `hermes-skills/{分类名}`。

## 4. telecom_skill — 电信/LI 专业知识

```sql
CREATE TABLE IF NOT EXISTS telecom_skill (
    id BIGINT,
    title VARCHAR(256),
    content TEXT,
    category VARCHAR(64),
    tags VARCHAR(256),
    source_path VARCHAR(512),
    li_level INT,
    created_at DATETIME
)
DUPLICATE KEY(id)
DISTRIBUTED BY HASH(id) BUCKETS 1
PROPERTIES("replication_num" = "1");
```

`li_level=5` 表示 LI 最高机密数据（仅存在于本地 Doris，绝不同步到云端）。

## 常用查询示例

```sql
-- 今日 token 消耗
SELECT DATE(ts) AS day, SUM(tokens_in)/1000000 AS million_in
FROM hermes_sessions GROUP BY day;

-- 最近 N 条 ERROR
SELECT logtime, service, LEFT(message, 200)
FROM linux_logs WHERE level='ERROR' ORDER BY logtime DESC LIMIT 20;

-- 按分类查知识库
SELECT tags, COUNT(*) FROM knowledge_chunks GROUP BY tags ORDER BY 2 DESC;

-- 知识库全文搜索
SELECT title, LEFT(content, 200) AS snippet
FROM knowledge_chunks WHERE content LIKE '%tcpdump%SIP%';

-- LI 机密数据
SELECT title, LEFT(content, 200) FROM telecom_skill WHERE li_level=5 AND content LIKE '%X2%';
```
