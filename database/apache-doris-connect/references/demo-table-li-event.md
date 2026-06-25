# LI 事件演示表（hermes_ai.li_event_demo）

> 本表用于 Hermes Agent + Doris 的 LI 事件查询演示。
> 建表于 2026-06-17，环境 rhino01 本机 Docker Doris。

## 建表 DDL

```sql
CREATE DATABASE IF NOT EXISTS hermes_ai;

USE hermes_ai;

CREATE TABLE li_event_demo (
    liid VARCHAR(64),
    msisdn VARCHAR(32),
    event_type INT,
    event_time DATETIME,
    cell_id VARCHAR(64),
    source_system VARCHAR(64)
)
DUPLICATE KEY(liid, msisdn, event_type)
DISTRIBUTED BY HASH(liid) BUCKETS 4
PROPERTIES ("replication_num" = "1");
```

## 测试数据

```sql
INSERT INTO li_event_demo VALUES
('2676','915637674',1,NOW(),'CELL_001','ztlig'),
('2676','915637674',10,NOW(),'CELL_001','ztlig'),
('2676','915637674',15,NOW(),'CELL_002','ztlig');
```

## 验证查询

```sql
SELECT liid, event_type, COUNT(*)
FROM li_event_demo
GROUP BY liid, event_type
ORDER BY liid, event_type;
```

预期结果：

| liid | event_type | COUNT(*) |
|------|------------|----------|
| 2676 | 1          | 1        |
| 2676 | 10         | 1        |
| 2676 | 15         | 1        |
