# VNEID ↔ 实际网元 GP 查询方法

## 映射原理

```
ZTLIG 配置层:
  vneid (虚拟网元编号) → tneid (ZTLIG 物理网元 ID) → hi2_neid (实际网元标识)
       ↓
hts_lig_hi2 分区表中 neid = VNEID
       ↓
rds_neid_info.neid = OWLS 中创建的网元记录 (neid = VNEID)
```

关键理解：**在 GP 中 `hts_lig_hi2` 分区表的 `neid` 字段就是 ZTLIG 的 VNEID。** 不是物理网元 ID，而是 ZTLIG 配置中定义的虚拟网元编号。

## 查询方法

### 1. 查看分区表中有哪些 VNEID（按数据量排序）

```sql
SELECT neid, count(*) AS cnt
FROM hts_lig_hi2_1_prt_part_YYYYMMDD_2_prt_cdr
GROUP BY neid
ORDER BY cnt DESC;
```

### 2. 查 `rds_neid_info` 获取网元别名

```sql
SELECT * FROM rds_neid_info WHERE neid = <VNEID>;
```

`rds_neid_info` 实际列结构（2026-06-24 确认）：

```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='rds_neid_info' ORDER BY ordinal_position;
```

| 列名 | 类型 | 说明 |
|------|------|------|
| `ne_id` | integer | **网元 ID，大部分 CS 域 = ZTLIG VNEID** |
| `nename` | text | 网元显示名（格式：`{运营商前缀}-{站点}-{功能}`） |
| `ip` | text | IP 地址（CS 域为空） |
| `port` | integer | 端口（CS 域为空） |
| `type` | text | 网元类型：MSC/GMSC/OMU/SBC/AS/MME/SGW/PGW/OMD |
| `ne_group_id` | integer | 所属网元组 ID（100000=Sudani, 100001=Zain 等） |
| `ne_group_name` | text | 网元组名：Sudani/Sudani-CS/Sudani-PS/Zain/Zain-CS 等 |
| `status` | integer | 状态：1(PSD/A站), 2(KHS/KTN/B站) |
| `technology` | text | NORMAL(CS域) / VOLTEL(IMS域) |
| `domain_name` | text | IMS 域名（仅 VOLTEL 类型有值） |
| `ne_id_real` | text | **实际网元标识，对应 ztlig.cfg 的 hi2_neid** |
| `factory_name` | text | 厂商：hw / zte |

> **重要发现：** `ne_id` 在 CS 域全量 = VNEID，但 **PS 域不匹配**（如 SU PS: ne_id=15/16 vs VNEID=19/20）。少数 hi2_neid 与 GP 的 ne_id_real 不符（如 Z-KTN_SVC_OMU01 ne_id_real=2049 vs hi2=249912090016）。详见 `references/ztlig-cfg-vneid-extraction.md` 输出解读中的差异说明。

### 3. 两表 JOIN 统计

```sql
SELECT h.neid, r.*, count(*) AS cnt
FROM hts_lig_hi2_1_prt_part_YYYYMMDD_2_prt_cdr h
LEFT JOIN rds_neid_info r ON h.neid = r.neid
GROUP BY h.neid, r.*;
```

### 4. 查看 ZTLIG 配置中的完整映射链

在 LIG 服务器上查 ztlig.cfg：

```bash
# 查某个 VNEID 的完整配置块
grep -A 5 "ztlig.vne.*vneid=<你的VNEID>" ztlig.cfg

# 列出所有 VNEID 映射
grep "ztlig.vne" ztlig.cfg | grep -E "vneid|hi2_neid"
```

配置示例（ZTE V4 LIS）：
```ini
# NE 定义
ztlig.ne.683.tneid = 26;
ztlig.ne.683.vendor = zte;
ztlig.ne.683.x1_ip = 10.197.24.217;

# VNE 定义——将 hi2_neid 映射为 vneid
ztlig.vne.791.tneid=26;
ztlig.vne.791.vneid=40;
ztlig.vne.791.hi2_neid = 251971200361;
```

### 5. 通过 `rds_source_define` 查 NEID 字段含义

```sql
SELECT * FROM rds_source_define
WHERE sourceno = 'DST_014031' AND field_name = 'NEID';
```

### 6. 按 VNEID + 时间范围查命中明细

```sql
SELECT tid, clue_id, msisdn, imsi, capturetime, sourceno
FROM hts_lig_hi2_1_prt_part_YYYYMMDD_2_prt_cdr
WHERE neid = <VNEID>
  AND capturetime BETWEEN 1750839600 AND 1750843199;
```

## 数据源编号

| sourceno | 类型 |
|----------|------|
| DST_014031 | CDR（通话） |
| DST_014001 | SMS |
| DST_014032 | 位置更新 |

## 注意事项

- `hts_lig_hi2` 是分区表，表名含日期后缀，查询时需替换为对应日期
- VNEID 在 ZTLIG 同一进程内不可重复，不同进程之间可重复
- ZTLIG 配置中的 `ztlig.vne.x.vneid` 需匹配 GP `hts_lig_hi2.neid` 的值
- **CS 域：ne_id = VNEID**，全量匹配。**PS 域：两套编号**（如 SU PS ne_id=15/16 对应 VNEID=19/20）
- `ne_id_real` 基本 = ztlig.cfg 的 `hi2_neid`，少数例外（需人工确认）

### 核对已确认的差异

| ne_id | nename | GP ne_id_real | ztlig hi2_neid | 差异类型 |
|-------|--------|---------------|----------------|---------|
| 4 | S-PSD-I-SBC | 5 | 7021 | ne_id_real ≠ hi2 |
| 27 | Z-KTN_SVC_OMU01 | 2049 | 249912090016 | ne_id_real ≠ hi2 |
| 15/16 | S-PSD_CloudUSN/CGW | 10.55.114.x | 10.23.136.x | PS域编号不同 |
| 33/34 | S-KHS PS MME/SGW | 10.53.120.x | — | GP-only，ztlig无对应 |

### 通过 SYS_OPERATION_LOG 审计网元停控状态

```sql
-- operation_type: 8=停控, 9=起控
SELECT * FROM SYS_OPERATION_LOG
WHERE second_level_menu = 'neidManagement'
  AND operation_type IN (8, 9)
ORDER BY create_time DESC;

-- 查哪些网元被停控过但从未起控
SELECT DISTINCT split_part(param, E'\\r', 1) AS ne_param
FROM SYS_OPERATION_LOG
WHERE second_level_menu = 'neidManagement'
  AND operation_type = 8    -- 停控
  AND result = 1            -- 成功
  AND ne_param NOT IN (
    SELECT DISTINCT split_part(param, E'\\r', 1)
    FROM SYS_OPERATION_LOG
    WHERE second_level_menu = 'neidManagement'
      AND operation_type = 9
      AND result = 1
  );
```

## 关联参考

- `~/knowledge/li/OWLS/Listener数据库表描述.md` — OWLS 全部 17 个功能域 50+ 张表
- `~/knowledge/li/ZTLIG/ZTLIG运维手册.md` — tneid/vneid/hi2_neid 三层映射详解
- `~/knowledge/li/projects/a1-project/A1项目Greenplum-psql查询手册.md` — GP 设控查询工作流
- `~/knowledge/li/projects/a1-project/A1项目重要数据表信息.md` — A1 项目数据表清单
