# Compression Loop 诊断参考

## Database Schema（state.db 相关表）

```sql
-- compression_locks 表结构
CREATE TABLE compression_locks (
    session_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);

-- sessions 表（相关字段）
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at INTEGER,
    last_active INTEGER
);

-- messages 表（相关字段）
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    created_at INTEGER,
    role TEXT
);
```

## 时间戳说明

- `compression_locks.expires_at` / `created_at`：`strftime('%s','now')` — Unix timestamp（秒）
- `sessions.last_active` / `created_at`：毫秒级 timestamp，需要 `/1000` 转换
- `messages.created_at`：毫秒级 timestamp，需要 `/1000` 转换

## 孤儿锁判断流程

```
1. sqlite3 ~/.hermes/state.db "SELECT * FROM compression_locks;"
   → session_id | agent_id=pid=NNNN:... | created_at | expires_at

2. 提取 PID: agent_id 字段以 "pid=NNNN:" 开头，substr 取 pid= 后的第一个冒号前的数字
   SQL: SELECT substr(agent_id, 5, instr(substr(agent_id,5),':')-1) FROM compression_locks

3. ps -p $PID 检查进程是否存在
   - 不存在 → 孤儿锁，可强制删除
   - 存在 → 运行中的压缩任务，应等待过期
```

## 实际案例

- **日期：** 2026-07-01
- **症状：** sessions=1084（阈值 300），messages=41046（阈值 10000），compression_locks=1
- **锁详情：** agent=`pid=6701:tid=129187515987648:agent=757f1a0e4fb0:nonce=55f7262e`
- **当前时间：** 1782899889
- **锁过期时间：** 1782900088（约 199 秒后）
- **PID 6701 状态：** 不存在（孤儿锁）
- **处理：** 用 `delete from compression_locks` 强制清理（跳过时间检查，因已确认为孤儿锁）

## 健康阈值

| 指标 | 健康 | 需关注 | 需紧急处理 |
|------|------|--------|-----------|
| sessions | < 300 | 300-500 | > 500 |
| messages | < 10000 | 10000-30000 | > 30000 |
| compression_locks | 0 | 1（孤儿） | > 1 |

## 运维 SOP 路径

完整的 Compression Loop 运维流程见：
`~/upload/Hermes Agent 运维 SOP.md`（企业内部文档）

核心步骤：备份 DB → 查表统计 → 锁检查 → PID 确认 → 清理 → 验证
