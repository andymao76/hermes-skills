# 网元控制状态诊断

## 概述

OWLS 前端网元管理界面中，网元有「停控」和「起控」两种状态。停控后网元对于 ZTLIG 表现为 out-of-control，停止一切 LI 操作。

## 1. Redis INVALID_NET_INFO（所有无效网元清单）

```bash
redis-cli -h 215.152.1.11 -c -p 6379
# 查看所有标记为无效(out-of-control)的网元
hgetall INVALID_NET_INFO
```

返回格式：`key=ne_id, value=1`（1=已停控）。

### 验证已停控清单

```bash
redis-cli -h 215.152.1.11 -c -p 6379 hgetall INVALID_NET_INFO | grep -v "^-" | paste - - | sort -n
```

### 单网元状态

```bash
redis-cli -h 215.152.1.11 -c -p 6379 hexists INVALID_NET_INFO <ne_id>
# 返回 1 = 无效/停控, 0 = 有效/起控
```

## 2. GP 操作日志审计（SYS_OPERATION_LOG）

```sql
-- operation_type: 8=停控, 9=起控
SELECT id, user_id, result, operation_type, client_ip,
       substring(operation from 'param=(\\d+)') AS ne_id,
       to_timestamp(create_time / 1000) AS op_time
FROM SYS_OPERATION_LOG
WHERE second_level_menu = 'neidManagement'
  AND operation_type IN (8, 9)
ORDER BY create_time DESC;

-- 查被停控但从未起控的网元
WITH stopped AS (
  SELECT DISTINCT substring(operation from 'param=(\\d+)') AS ne_id
  FROM SYS_OPERATION_LOG
  WHERE second_level_menu = 'neidManagement'
    AND operation_type = 8
    AND result = 1
), restarted AS (
  SELECT DISTINCT substring(operation from 'param=(\\d+)') AS ne_id
  FROM SYS_OPERATION_LOG
  WHERE second_level_menu = 'neidManagement'
    AND operation_type = 9
    AND result = 1
)
SELECT s.ne_id
FROM stopped s LEFT JOIN restarted r ON s.ne_id = r.ne_id
WHERE r.ne_id IS NULL
ORDER BY s.ne_id::int;
```

### 操作人映射

| user_id | 来源 IP | 角色 |
|---------|---------|------|
| 1 | 192.168.123.150 | 管理员 admin |
| 10032 | 192.168.123.18 | 操作员 |
| 10041 | 192.168.123.4/.13/.18 | 操作员 |

## 3. ZTLIG out-of-control 行为

| 行为 | 说明 |
|------|------|
| LIG 夜间同步 | 跳过 out-of-control 网元 |
| OWLS 前端展示 | 该网元下绑定的 target 不可见 |
| NE-target 关系 | OWLS 自动删除网元与目标的对应关系 |
| Redis | ne_id 写入 INVALID_NET_INFO hash |

典型场景：客户将 1514 个 target 设控到网元 25（Z-KTN_mAGCF01），但该网元因 LI 对接未完成而被设为 out-of-control。客户在前端看不到结果，反复尝试设控。

## 4. 状态切换后的恢复

**out-of-control / active 切换后必须手工触发 LIG 同步：**

```bash
# 1. OWLS 前端起控
# 2. 手工执行同步
syn ztlig1 300 redis 0
# 3. 确认同步
grep "ne syn handle succ" ztlig1.300.txt | tail -5
```

### syn 命令格式

```
syn ztlig<进程号> <超时秒> redis <0/1>
```

- `ztlig1` — X1 接口设置进程
- `300` — 超时秒数
- `redis 0` — 跳过差距检测，强制执行三方同步

## 5. 快速诊断流程

```bash
# Step 1: Redis 确认无效网元
redis-cli -h 215.152.1.11 -c -p 6379 hgetall INVALID_NET_INFO

# Step 2: GP 确认停控时间线
psql -h 215.152.1.13 -p 5432 -U daedb -d bigdata -c "
  SELECT substring(operation from 'param=(\\d+)') AS ne_id,
         operation_type,
         to_timestamp(create_time/1000) AS t
  FROM SYS_OPERATION_LOG
  WHERE second_level_menu='neidManagement'
    AND operation_type IN (8,9)
  ORDER BY create_time DESC LIMIT 20;"

# Step 3: ztlig.cfg 确认网元配置
grep "valid_fg" ztlig.cfg

# Step 4: 同步日志确认
grep -E "Lig1NightSync|ne syn handle" ztlig1.300.txt | tail -10
```

## 关联参考

- `references/vneid-neid-gp-query.md` — GP rds_neid_info 列结构
- `references/ztlig-cfg-vneid-extraction.md` — ztlig.cfg 网元定义提取
- `~/knowledge/li/ZTLIG/ZTLIG运维手册.md` — 完整运维命令
