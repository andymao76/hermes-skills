# OWLS GP 数据库查询模式（A1项目）

> OWLS Listener 系统的 Greenplum 数据库查询方法集。围绕 `hts_lig_hi2` 核心命中表和 VNEID ↔ 网元名映射展开。

## 数据源编号

| 编号 | 类型 | 说明 |
|------|------|------|
| DST_014031 | CDR | 通话详单 |
| DST_014001 | SMS | 短信 |
| DST_014032 | 位置更新 | LCT/LBS |

## 命中数据查询

### 基础查询

```sql
-- 按 tid + clue_id 精确定位
SELECT * FROM hts_lig_hi2
WHERE tid = '15_8e2598c1db7667c0a133d8b1495616a1_1750840299'
  AND clue_id = 11085;

-- 按 clue_id 批量
SELECT * FROM hts_lig_hi2 WHERE clue_id IN (11085, 11086, 11099);

-- 时间范围（capturetime 是 Unix 秒时间戳）
SELECT * FROM hts_lig_hi2
WHERE clue_id = 11085
  AND capturetime BETWEEN 1750839600 AND 1750843199;
```

### 分区表查询

`hts_lig_hi2` 是按日期分区的（`hts_lig_hi2_1_prt_part_YYYYMMDD_2_prt_cdr`），查询必须带分区后缀：

```sql
-- 查看所有分区
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE 'hts_lig_hi2%prt_cdr' ORDER BY table_name;

-- 按 VNEID（= neid 字段）统计
SELECT neid, count(*) AS cnt
FROM hts_lig_hi2_1_prt_part_20250623_2_prt_cdr
GROUP BY neid ORDER BY cnt DESC;

-- 按数据源统计
SELECT sourceno, count(*) AS cnt
FROM hts_lig_hi2_1_prt_part_20250623_2_prt_cdr
GROUP BY sourceno;

-- 查询无语音文件的话单
SELECT neid, count(*) AS cnt
FROM hts_lig_hi2_1_prt_part_20250623_2_prt_cdr
WHERE file_path IS NULL AND duration > 5
GROUP BY neid;
```

### 字段含义查询

```sql
SELECT * FROM rds_source_define
WHERE sourceno = 'DST_014031' AND field_name = 'CALLER_MSISDN';
```

## VNEID ↔ 实际网元名映射

### 映射链

```
hts_lig_hi2.neid (= VNEID)
  → ztlig.vne.X.vneid     (VNE 块中定义的虚拟网元编号)
  → ztlig.vne.X.tneid     (指向物理网元编号)
  → ztlig.vne.X.hi2_neid  (X2 报告中的网元标识)
  → ztlig.ne.Y.tneid=N    (物理网元定义)
  → ztlig.ne.Y.alias      (华为网元别名/名字)
  → ztlig.ne.Y.vendor     (厂商)
  → ztlig.ne.Y.x1_ip      (对接 IP)
```

### GP 端查询

```sql
-- rds_neid_info 存储了 OWLS 前端创建的网元
SELECT * FROM rds_neid_info;
SELECT * FROM rds_neid_info WHERE neid = <VNEID>;

-- 查看所属网元组
SELECT g.*, n.*
FROM rds_neid_info n
LEFT JOIN rds_neid_group_info g ON n.group_id = g.id
WHERE n.neid = <VNEID>;
```

> ⚠️ `rds_neid_info` 列结构需在 GP 中 `\d rds_neid_info` 确认。

### ZTLIG 服务器端查询

在 LIG 服务器上执行：

```bash
cd /home/ZTLIG/bin

# 1. 格式化输出所有 VNE 记录
awk -F'[=;]' '
  /^ztlig\.vne\./ {
    split($1, a, ".")
    i = a[3]; k = a[4]; gsub(/^ +| +$/, "", k)
    v = $2; gsub(/^ +| +$/, "", v)
    d[i,k] = v
  }
  END {
    printf "%-7s  %-7s  %-20s  %-5s\n", "VNEID", "TNEID", "HI2_NEID", "OPERID"
    for (k in d) {
      split(k, b, SUBSEP)
      if (b[2] == "vneid")
        printf "%-7s  %-7s  %-20s  %-5s\n",
          d[b[1],"vneid"], d[b[1],"tneid"], d[b[1],"hi2_neid"], d[b[1],"operid"]
    }
  }
' ztlig.cfg | sort -k1 -n

# 2. 关联网元配置（含别名）
echo "=== VNEID + NE 完整映射 ==="
awk -F'[=;]' '
  /^ztlig\.vne\./ {
    split($1, a, ".")
    i = a[3]; k = a[4]; gsub(/^ +| +$/, "", k)
    v = $2; gsub(/^ +| +$/, "", v)
    vd[i,k] = v
  }
  /^ztlig\.ne\./ {
    split($1, a, ".")
    i = a[3]; k = a[4]; gsub(/^ +| +$/, "", k)
    v = $2; gsub(/^ +| +$/, "", v)
    nd[i,k] = v
  }
  END {
    printf "%-6s  %-6s  %-20s  %-8s  %-20s\n", "VNEID", "TNEID", "HI2_NEID", "VENDOR", "ALIAS"
    for (k in vd) {
      split(k, b, SUBSEP)
      if (b[2] == "vneid") {
        tn = vd[b[1],"tneid"]
        a = nd[tn,"alias"] ? nd[tn,"alias"] : "-"
        ve = nd[tn,"vendor"] ? nd[tn,"vendor"] : "-"
        printf "%-6s  %-6s  %-20s  %-8s  %-20s\n",
          vd[b[1],"vneid"], tn, vd[b[1],"hi2_neid"], ve, a
      }
    }
  }
' ztlig.cfg | sort -k1 -n

# 3. 只查有效网元
grep "valid_fg" ztlig.cfg | grep "=1"

# 4. 统计
echo "VNE 总数:  $(grep -c 'ztlig\.vne\..*\.vneid' ztlig.cfg)"
echo "NE 总数:    $(grep -c '^ztlig\.ne\.[0-9]' ztlig.cfg)"
echo "有效 NE 数: $(grep 'valid_fg' ztlig.cfg | grep -c '=1')"
```

## 关联知识库文档

- `knowledge/li/OWLS/Listener数据库表描述.md` — OWLS 全部数据库表清单
- `knowledge/li/OWLS/owls-tmc-data-processing.md` — TMC 数据处理流
- `knowledge/li/projects/a1-project/A1项目重要数据表信息.md` — A1 项目核心表汇总
- `knowledge/li/projects/a1-project/A1项目Greenplum-psql查询手册.md` — PSQL 查询手册
- `knowledge/li/ZTLIG/ZTLIG运维手册.md` — ZTLIG 配置详解（tneid/vneid/hi2_neid 关系）
