# A1 项目 VNEID ↔ 实际网元映射速查

完整映射表存放在知识库：`knowledge/li/OWLS/A1项目ztlig.cfg-VNEID映射表.md`

## 运营商 operid 速查

| 运营商 | operid |
|--------|--------|
| SU (Sudatel) | 63407 |
| ZAIN | 63401 |
| MTN | 63402 |

## 当前在用网元（从未停控 — PSD 主站核心网元）

| ne_id | nename | 类型 | 运营商 | 备注 |
|-------|--------|------|--------|------|
| 1 | S-PSD-mAGCF | MSC | SU | PSD |
| 2 | S-PSD-GMSC | GMSC | SU | PSD |
| 10 | Z-PSD_mAGCF01 | MSC | ZAIN | PSD |
| 11 | Z-PSD_GMSC01 | GMSC | ZAIN | PSD |
| 15 | S-PSD_CloudUSN01 | MME | SU-PS | PSD |
| 16 | S-PSD_CloudCGW01 | SGW | SU-PS | PSD |
| 19 | Z-PSD_USN01 | MME | ZAIN-PS | PSD |
| 20 | Z-PSD_CGW01 | SGW | ZAIN-PS | PSD |

## 已停控网元（operation_type=8，无对应 type=9）

| 运营商 | 已停控 ne_id | 说明 |
|--------|--------------|------|
| SU (CS) | 3,4,5,6,17,18 | PSD 侧 SBC/OMU/VOBB/IMGW |
| SU (KHS) | 23,24,29,30,31,32 | 喀土穆全停 |
| SU (PS) | 33,34 | KHS PS MME/SGW |
| ZAIN (PSD) | 12 | PSD_SVC_OMU01 |
| ZAIN (KTN) | 25,26,27,28,29 | 喀土穆全停 |
| ZAIN (PS) | 41,42 | KTN PS MME/SGW |
| MTN | 7,8,9,21,22,35,36,37,38,39,40 | **全停** |

## GP rds_neid_info 列结构

| 字段 | 类型 | 说明 |
|------|------|------|
| ne_id | int | OWLS 内部网元 ID（CS 域 = VNEID，PS 域可能不同） |
| nename | varchar | 网元显示名（格式：运营商前缀-站点-功能） |
| ip | varchar | 空 |
| port | int | 空 |
| type | varchar | MSC/GMSC/OMU/SBC/AS/MME/SGW/PGW/OMD |
| ne_group_id | int | 分组 ID |
| ne_group_name | varchar | 运营商/站点分组名 |
| status | int | 1=A站, 2=B站 |
| technology | varchar | NORMAL(CS) / VOLTEL(IMS) |
| domain_name | varchar | IMS 域（仅 VOLTEL 有值） |
| ne_id_real | varchar | 实际网元标识（对应 ztlig.cfg 的 hi2_neid） |
| factory_name | varchar | 厂商（全为 hw） |

## GP vs ztlig.cfg 编号差异

| 差异项 | GP (rds_neid_info) | ztlig.cfg | 说明 |
|--------|-------------------|-----------|------|
| SU PS 域 ne_id | ne_id=15, 16 | VNEID=19, 20 | **两套编号**，OWLS 管理界面与 ztlig 配置不一致 |
| Z-KTN_SVC_OMU01 hi2_neid | ne_id_real=2049 | hi2_neid=249912090016 | 可能 B 站换过 hi2_neid 或配置未同步 |
| S-PSD-I-SBC hi2_neid | ne_id_real=5 | hi2_neid=7021 | 不一致 |
| GP-only 网元 | ne_id=33,34,37,38,39,40 | （无对应 VNE） | 仅 GP 有记录，ztlig.cfg 中无配置 |

**规则：** CS 域 `ne_id` = VNEID（完全匹配），PS 域和部分 hi2_neid 有出入。

## SYS_OPERATION_LOG 查询模式

```sql
-- 查所有停控记录（8=停控, 9=起控）
select * from SYS_OPERATION_LOG
where second_level_menu = 'neidManagement'
  and operation_type in (8, 9)
order by id desc;

-- 查当前 out-of-control 的网元（有停控无起控）
select param, max(create_time) as last_stop_time
from SYS_OPERATION_LOG
where second_level_menu = 'neidManagement'
  and operation_type = 8 and result = 1
  and param not in (
    select param from SYS_OPERATION_LOG
    where second_level_menu = 'neidManagement'
      and operation_type = 9 and result = 1
  )
group by param order by param;
```

## Redis INVALID_NET_INFO

```bash
redis-cli -h <REDIS_IP> -c -p 6379 hgetall INVALID_NET_INFO
# 返回 ne_id → 1 的键值对，列出所有 out-of-control 网元
```

## 夜间同步

```bash
# 查看 LIG 夜间同步状态
cat ztlig1 300 | grep night

# out-of-control/active 切换后手工同步
syn ztlig1 300 redis 0
```
