---
name: li-system-ops
category: telecom
description: 合法监听(LI)系统全栈日常运维 — 系统基础信息、大数据平台CLI速查、日常巡检项、系统重启流程、ZTLIG二进制/配置分析、ZTLIG/SICMS运维、问题排查案例库
platform: Hermes Agent
severity: high
verified: true
author: Hermes
date: 2026-06-16
---

# LI系统全栈日常运维

合法监听(Lawful Interception)系统日常运维技能。覆盖已部署LI系统的日常检查、CLI操作、故障排查、系统恢复全流程。适用于北苏丹等LI/LIG运维项目。

当用户提及以下内容时触发：
- LI系统日常维护、巡检、故障排查
- LI系统断电恢复、重启流程
- 谛听系统、OWLS运维
- 站点A/站点B双站架构维护
- SICMS、LIG前台后台运维

---

## 一、设控逻辑速查

| 运营商 | 呼叫类型 | 设控号码格式 |
|--------|---------|-------------|
| MTN / ZAIN | 出局呼叫 | **ISDN** |
| SU | 出局和本地呼叫 | **MSISDN** |
| MTN / ZAIN / SU | 国漫 | **ISDN** |

## 二、常用CLI速查

### HDFS

```bash
# 巡检目录
hdfs dfs -ls /zxsk/lis/
hdfs dfs -ls /zxsk/lis/owls_wide_table/table=trs_hi3_ipdr/date_partition=YYYYMMDDHH

# 批量检查分区
for p in 2024120914 2025083008; do
  echo "=== Checking partition: $p ==="
  hdfs dfs -ls /zxsk/lis/owls_wide_table/table=trs_hi3_ipdr/date_partition=$p || echo "Partition $p does not exist."
done

# HDFS修复
hdfs fsck / -list-corruptfileblocks
hdfs fsck / -files -blocks -locations
hdfs fsck / -delete                   # 清理损坏块
hdfs dfsadmin -report
hdfs fsck / -replicate                # 触发副本恢复

# NameNode Checkpoint
hdfs haadmin -getServiceState nn1
hdfs haadmin -getServiceState nn2
hdfs dfsadmin -rollEdits             # 手动触发EditLog滚动
hdfs dfsadmin -safemode enter        # 进入安全模式
```

### YARN

```bash
yarn application -list
yarn application -kill <app_id>
yarn node -list
```

### Kafka

```bash
# 预创建topic（ZTLIG场景）
bin/kafka-topics.sh --create --zookeeper localhost:2181 \
  --replication-factor 1 --partitions 1 --topic TARGET_INFO

bin/kafka-topics.sh --create --zookeeper localhost:2181 \
  --replication-factor 1 --partitions 1 --topic TARGET_INFO_STATUS

# 查看topic列表
bin/kafka-topics.sh --list --zookeeper localhost:2181

# 消费消息
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic TARGET_INFO --from-beginning

# 按CIN查询business topic（排查话单时最常用）
# 替换参数：<KAFKA_IP:PORT>、<BUSINESS_TOPIC>、<CIN值>
./kafka-console-consumer.sh --bootstrap-server <KAFKA_IP>:<PORT> \
  --topic <BUSINESS_TOPIC> \
  --from-beginning | grep <CIN值>
# 注意：--from-beginning 数据量大时建议去掉，或加 --max-messages N 限制
```

### Redis

```bash
redis-cli -h <REDIS_IP> -c -p 6379

# 查目标详细信息（返回JSON）
hget TMC_TARGET_INFO <targetId>
# 输出: {"account":"249909802630","editFlag":4,"mapId":23487,
#         "officesIds":"10","protocol":"MSISDN",...}

# 查所有 out-of-control 网元
hgetall INVALID_NET_INFO
# key=ne_id (对应 rds_neid_info.ne_id), value=1 (无效)
# 可以通过比对该列表与 rds_neid_info 判断哪些停控网元已同步到Redis

# 查目标设控的网元列表
# TMC_TARGET_INFO 中的 officesIds 字段用逗号分隔的 ne_id 列表
# hget TMC_TARGET_INFO {targetId} → officesIds:"10" 或 "14,12,13"
```

### JanusGraph / Gremlin

```bash
# 重启Gremlin Server
ps -ef|grep gremlin|grep -v grep|awk '{print $2}'|xargs kill -9
export JANUSGRAPH_YAML=/home/websrv/janusgraph/conf/gremlin-server/socket-gremlin-server.yaml
cd /home/websrv/janusgraph/bin && ./gremlin-server.sh start
```

### Greenplum

```bash
psql -d bigdata -U daedb

# 查看分区保留天数
select * from base_addpart_config;

# 修改分区保留天数
update base_addpart_config set keep_time = 720 where lower(table_name) = 'hts_lig_hi2';

# 查看表结构
\d rds_neid_info
\d rds_source_define
\d hts_lig_hi2

# 列出所有分区表
\d+
SELECT table_name FROM information_schema.tables
WHERE table_name LIKE 'hts_lig_hi2%prt_cdr' ORDER BY table_name;

# 查看网元停控/起控操作记录（8=停控, 9=起控）
select * from SYS_OPERATION_LOG
where second_level_menu = 'neidManagement'
  and operation_type in (8, 9)
order by id desc;
-- operation_type: 8=停控(停止控制), 9=起控(恢复控制)
-- param 字段格式: "param=XX\r\n"，XX 为 ne_id
-- result: 0=失败, 1=成功

# 查当前所有 out-of-control 的网元（有停控记录且无起控记录）
select param, max(create_time) as last_stop_time
from SYS_OPERATION_LOG
where second_level_menu = 'neidManagement' and operation_type = 8 and result = 1
  and param not in (
    select param from SYS_OPERATION_LOG
    where second_level_menu = 'neidManagement' and operation_type = 9 and result = 1
  )
group by param order by param;

# 查看某时间段停控汇总
select param, count(*) as cnt, min(create_time), max(create_time)
from SYS_OPERATION_LOG
where second_level_menu = 'neidManagement' and operation_type = 8
  and result = 1
group by param order by param;
```

#### OWLS GP 数据库查询模式（A1项目）

见参考文件 `references/owls-gp-query-patterns.md`，核心查询包括：

| 场景 | 核心表 | SQL / 命令 |
|------|--------|-----------|
| 命中数据查询 | `hts_lig_hi2` 分区表 | `SELECT * FROM hts_lig_hi2_1_prt_part_YYYYMMDD_2_prt_cdr WHERE clue_id=N;` |
| VNEID → 网元名映射（GP端） | `rds_neid_info` | `SELECT * FROM rds_neid_info WHERE neid=VNEID;` |
| VNEID → 网元名映射（ZTLIG端） | `ztlig.cfg` | `grep -E "ztlig\\.vne\\.|ztlig\\.ne\\..*\\.(tneid|alias)" ztlig.cfg` |
| 字段含义 | `rds_source_define` | `SELECT * FROM rds_source_define WHERE sourceno='DST_014031' AND field_name='CALLER_MSISDN';` |
| 数据源编号 | `rds_source_info` | DST_014031=CDR, DST_014001=SMS, DST_014032=位置 |

**VNEID 映射链概要：**
```
hts_lig_hi2.neid → ztlig.vne.X.vneid → ztlig.vne.X.tneid → ztlig.ne.Y.alias (网元名)
```

### 其他组件

| 组件 | 巡检命令 |
|------|---------|
| Zookeeper | `zkServer.sh status` |
| HBase | `hbase hbck` |
| Hive/Beeline | `beeline -u jdbc:hive2://...` |
| Spark | `yarn application -list | grep spark` |
| Tez | Tez UI / `yarn application -list | grep tez` |
| Presto | `presto-cli --server ...` |
| Flink | `flink list` |

## 三、日常巡检项

### 3.1 防火墙检查
- 检查防火墙状态（图形界面或 CLI）
- 确认关键端口未阻塞

### 3.2 Keepalived 检查
- 检查VIP漂移状态
- 确认主备节点正常

### 3.3 Secpass / Zabbix 检查
- Secpass：确认组件运行状态
- Zabbix：检查告警面板，确认无异常告警

### 3.4 业务模块进程检查
检查所有关键进程：
- ZTLIG1/ZTLIG2/ZTLIG3
- SSF / RVF / CMF
- SICMS
- OWLS 后台模块
- Kafka / ZK / HDFS NN/DN

### 3.5 离线任务检查
```bash
# 检查离线任务文件
ls -la /home/rhino/RelationGraph/bin/process/

# 检查MPP Loader日志
tail -f /home/rhino/log/mpploader.log
```

### 3.6 定时任务检查
```bash
crontab -l
```

## 四、系统重启流程（断电恢复）

```
步骤1: 检查硬件状态
步骤2: 检查防火墙状态
步骤3: 检查NTP服务器状态
步骤4: 重启Secpass/Zabbix
步骤5: 前台LIG系统重启 (install cmf → install PSM → 检查进程)
步骤6: 前台SICMS系统重启
步骤7: 后台系统重启 (Secpass/OWLS)
```

### 关键检查点
- 系统挂载检查
- OWLS模块启动顺序
- 各组件启动后确认进程状态

## 五、问题排查案例库

### 5.1 HDFS Missing Blocks
**现象**：Total Blocks: 1254992, Missing Blocks: 32
**排查**：
```bash
hdfs fsck / -list-corruptfileblocks
hdfs fsck / -files -blocks -locations -replicaDetails | grep -i 'MISSING|CORRUPT'
```
**修复**：
```bash
hdfs fsck / -replicate    # 触发副本恢复
hdfs fsck / -delete       # 清理包含损坏块的文件
```

### 5.2 HDFS Checkpoint 不执行
**排查**：
```bash
hdfs haadmin -getServiceState nn2    # 确认Standby在运行
ls -ltr /data01/hadoop/hdfs/namenode/current/fsimage_*
grep -i checkpoint /data01/var/log/hadoop/hdfs/hadoop-hdfs-namenode-*.log
```
**触发**：
```bash
hdfs dfsadmin -rollEdits
```

### 5.3 I-Analysis关系图为空
**排查链路**：
1. 检查 Gremlin Server 是否运行 → `ps -ef|grep gremlin`
2. 检查离线任务结果 → `/home/rhino/RelationGraph/bin/process/`
3. 检查 MPP Loader 日志 → `tailf mpploader.log`
4. 检查 UnknownHostException → 添加 `/etc/hosts` 映射
5. 重新执行离线任务 → `sh /home/rhino/RelationGraph/timetaskall/allmissiontwo.sh`

### 5.4 站点B查询昨天数据为空
**检查**：
```bash
# 检查定时任务中的脚本路径
sh /home/rhino/RelationGraph/timetaskall/allmission.sh
```
**常见原因**：脚本路径错误（站点B使用 `bin/dt/processD.sh` 而非 `bin/processD.sh`）

### 5.5 登录Web系统失败
- 检查系统服务是否正常运行
- 检查数据库连接
- 参考管理员密码重置

### 5.6 数据无法入库
- 检查 HDFS 空间
- 检查 Kafka 消费状态
- 检查 OWLS 模块进程

### 5.7 语音丢失/播放异常
- 检查 RVF 进程
- 检查语音文件目录 `/data01/voice/`
- 检查 X3 口连通性
- 检查 SIP-I 会话状态

### 5.8 数据老化配置
```sql
-- GP 分区保留天数
select * from base_addpart_config;
update base_addpart_config set keep_time = 720 where lower(table_name) = 'hts_lig_hi2';

-- 数据清理工具配置
/home/rhino/data-aging-2.0.0/config/config.json
-- 需拷贝 hbase-site.xml / hdfs-site.xml / core-site.xml / hive-site.xml
```

### 5.9 管理员密码重置
```sql
select * from sys_user where user_name = 'admin';
update sys_user set password = 'UH0QX2DWWhba0jYVAalarA==' where user_name = 'admin';
```

### 5.10 SSH登录被锁定
```bash
faillock --user root --reset
# 检查 /etc/security/access.conf
# 检查 /etc/hosts.deny
# 检查 /etc/hosts.allow
```

## 六、ZTLIG 调试参考

### ZTLIG 发行包分析方法

当拿到新版本 ZTLIG 发行包（如 `ZTLIG_Bin_X86Centos_YYYYMMDD_hash.tar.gz`）时，按以下步骤分析版本差异和结构变化：

```bash
# 0. 对比 BuildID 确认是否同一编译版本
file bin/ztlig2                        # 查看 BuildID[sha1]=...
# 与现有可执行文件的 BuildID 对比，相同说明是同一构建

# 1. 对比动态库清单变化
tar tzf pkg.tar.gz | grep '\.so$' | sort > pkg_so.list
ls tmp_so/ | sort > current_so.list
diff pkg_so.list current_so.list       # 发现新增/移除的厂商插件

# 2. 对比版本号
cat bin/shell/version                  # LISTENER V1.1.02_LIG_T11

# 3. 查看进程数量变化（是否新增子进程）
tar tzf pkg.tar.gz | grep -E 'ztlig[0-9]$|cmf|psm|rvf|ssf'
```

### ZTLIG 配置对比方法（站点 A/B 双站架构分析）

当需要排查两个站点间的配置差异时，使用系统化的 diff 分析方法：

```bash
# 1. 全量对比
diff SU-A-CS-ztlig.cfg SU-B-CS-ztlig.cfg | wc -l   # 总差异行数

# 2. 批量统计进程/网元数量差异
grep -c '^\[ZTLIG2_' SU-A-CS-ztlig.cfg              # X2 实例数
grep -c '^\[SSF_' SU-A-CS-ztlig.cfg                  # SSF 实例数
grep -c '^\[NE_' SU-A-CS-ztlig.cfg                   # 网元数量
grep -c '^\[RVF_' SU-A-CS-ztlig.cfg                  # RVF 实例数

# 3. 过滤已知的 IP/leaid 差异，找真正的结构差异
diff SU-A-CS.cfg SU-B-CS.cfg | grep -E '^[<>]' | \
  grep -vE '(215\.152\.|192\.172\.|10\.55\.2\.11|10\.171\.2\.11|leaid|x1_user|redis|kafka.*broker)' | \
  head -20
# 如果只输出空白/SSF 块头，说明只有 IP/leaid 差异——结构相同
# 如果输出完整的 NE 段、SSF 段等，说明有结构差异

# 4. 交叉验证 — 提取结构差异
# 进入统计计数不一致的段落，逐项对比
```

**经验：** A/B 站配置通常完全镜像（仅 IP/leaid/DBAuth 不同）。唯一的结构差异往往指向**网络拓扑差异**——如某个站点多一个 SSF 实例，是因为该站点的 VoWiFi SIP 信令出口需要独立会话管理。

### ZTLIG 二进制分析方法（ELF 分析）

当拿到 ZTLIG 发行包（如 `ZTLIG_Bin_X86Centos_YYYYMMDD_hash.tar.gz`）时，按以下步骤分析：

```bash
# 0. 查看包内容结构
tar tzf *.tar.gz | grep -E '/$'           # 目录结构
tar tzf *.tar.gz | grep -E '\.so$'        # 动态库清单
tar tzf *.tar.gz | grep -E 'ztlig[0-9]$|cmf|psm|rvf|ssf'  # 可执行文件

# 1. 查看可执行文件基本信息
file bin/ztlig2                             # ELF 64-bit x86-64 / ARM
size bin/ztlig2                              # text/data/bss

# 2. 符号分析（含 C++ demangle）
nm -C bin/ztlig2 | grep ' T ' | awk '{print $3}'    # 所有函数
nm -C bin/ztlig2 | grep ' D \| B ' | awk '{print $3}' # 全局变量
nm -C bin/ztlig2 | grep ' U ' | awk '{print $3}' | sort -u  # 外部引用(依赖)

# 3. 字符串提取找配置/消息/错误码
strings bin/ztlig2 | grep -iE 'MSG_|ERROR|failed|succ|ztlig\.' | sort -u

# 4. 依赖分析
ldd bin/ztlig2                               # 动态链接依赖
# 注意：tmp_so/ 中的 .so 需要 LD_LIBRARY_PATH 才能解析

# 5. 比较不同版本的二进制
diff <(strings bin/ztlig2 | sort) <(strings other/ztlig2 | sort) | head -50

# 6. 厂商/协议插件分类
# 命名规则: lib<厂商>_<接口><版本>.so
# X1: lib*hi1*.so, lib*x1*.so, lib*liclis*.so
# X2: lib*x2*.so
# X3: lib*x3*.so, lib*hi3*.so
# 厂商: hw/eric/zte/nsn/alu/mavenir/utimaco/zeel/group2k/uag
```

### 关键日志命令
```bash
# 查询 MAP_ID 和 TARGET_ID 对应关系
# ztlig_target.txt 中查看

# 查询2口日志
cat ztlig2.*.txt | grep EncodeToJson | grep '\\\"LIID\\\":\\\"<liid>\\\"'

# Kafka 状态检查
show ztlig2 {id} kafka stat

# X2 口统计
show ztlig2 {id} x2 stat
```

### LigCdr 日志提取（V1.2 工具）

见参考文件 `references/ztlig-ligcdr-extraction.md`，核心用法：

```bash
cd ~/PCAP/20260623-A1-VOWIFI
# 按 LIID 过滤 + 非JSON行自动捕获
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --liid 14029 --unique -o /tmp/out
# 统计分布
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --liid 14029 --stats
# 按 CIN 过滤，捕获 P-Charging-Vector 等关联行
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --cin "psdpcscf02.194.6cbd.20260607125301" -o /tmp/out
```

关键特性：
- 双模式过滤：JSON 结构精确匹配 + 非JSON行文本子串匹配
- 输出 `raw_matches_filtered.txt` 捕获 SIP 信令、调试日志等关联行
- 跨文件 LIID 分析：多文件 symlink + `--stats` 快速全景，再到 `--unique` 全量提取

### LigCdr 综合分析工作流（LIID / MSISDN 维度）

当需要全面分析某个 LIID 或 MSISDN 在所有日志中的行为，按以下 5 步流程执行。一个完整的分析周期（扫描→分析→提取→报告）典型耗时约 1-3 分钟（取决于日志量）。

**Step 1 — 文件定位**

扫描所有 txt 文件，找包含目标值的文件：

```bash
# 快速文本扫描定位
grep -l '120120415' A1-ztlig/ztlig2.*.txt
```

注意：`list_input_files()` 会扫到 `.gz` 假文件（实际是纯文本）导致 `BadGzipFile` 崩溃。
解决方案：指定 `.txt` 文件列表，或创建仅含 `.txt` 的 symlink 目录：

```bash
mkdir -p /tmp/myfiles
for f in ztlig2.461.txt ztlig2.462.txt ztlig2.465.txt ztlig2.466.txt ztlig2.467.txt; do
    ln -sf "A1-ztlig/$f" "/tmp/myfiles/$f"
done
```

**Step 2 — 快速统计**

跑 `--stats` 得到每个文件的 LIID 分布、EventDetail、时间范围、CIN 数。注意 `--stats` 只统计 JSON 字段。

一次性扫描全部文件（含去重）并输出汇总时，建议用 `execute_code` 写 Python 统计脚本替代逐文件跑 `--stats`。核心模式：

```python
from collections import Counter
import json, re

for fpath in txt_files:
    with open(fpath, 'r', errors='replace') as f:
        for line in f:
            for m in re.finditer(rb'\{[^{}]*\}', line.encode('utf-8')):
                obj = json.loads(m.group())
                if obj.get('CdrType') == 'LigCdr' and str(obj.get('LIID','')) == '14029':
                    # 统计字段...
```

**Step 3 — 深度分析**

关键分析维度：

**MSISDN 角色分析（重要）：**
同一号码可能在三个字段中以不同角色出现：
- `MSISDN` 字段 — 该号码是被监听目标（LIID 关联对象）
- `CallingNum` / `CalledNum` 字段 — 该号码是通话对方，属于其他 LIID 的记录

这意味着一份日志中同一个号码可能关联 5+ 个 LIID，分析时必须区分角色，不能只看 MSISDN 字段。

**过滤注意事项：**
- `--msisdn 249120120415` 只精确匹配 MSISDN 字段，不会匹配 `CallingNum` / `CalledNum`
- 要捕获作为对方号码出现的场景，需改搜 `CallingNum` / `CalledNum` 字段
- 号码可能有本地格式（`0120120415`）和国际格式（`249120120415`），需分别匹配

**CIN 分组：**
按 CidNum（唯一呼叫标识）分组统计每通呼叫的事件序列：
- `10→11→13→14`（Begin→Answer→Release→T38）为完整 IMS 呼叫，通常占 ~44.8%
- `10→13→14` / `10→13` 为未接通呼叫
- `10 仅` 为 SMS 或 Bearer 事件

**站点判定：**
CIN 前缀 `psdpcscf*` = PSD 站（苏丹港），`atbpcscf*` = ATB 站（阿特巴拉）

**NetworkType：**
`13` = IMS，`11` = VoWiFi。同个 LIID 可能在 VoWiFi 和 IMS 间切换（通过时间线判断）

**关联号码分析：**
当号码作为目标时，提取 `CallingNum` / `CalledNum` 中非自己的号码，就是通话对方。同一目标可能与 8+ 个不同对方号码通话。

**方向判定：**
- `EventDirection = 1` = MO（主叫）
- `EventDirection = 2` = MT（被叫）
- MO 通常多于 MT（~60:40）

**分析脚本模板（适用于 `execute_code` 或独立 py 文件）：**

```python
# 分析脚本核心结构
import json, re
from collections import Counter, defaultdict

all_objs = []
seen_sigs = set()

for fpath in files:
    with open(fpath, 'r', errors='replace') as f:
        for line in f:
            if '120120415' not in line:             # 快速过滤
                continue
            for m in re.finditer(rb'\{[^{}]*\}', line.encode('utf-8')):
                try:
                    obj = json.loads(m.group())
                    if not isinstance(obj, dict) or obj.get('CdrType') != 'LigCdr':
                        continue
                    sig = json.dumps(obj, sort_keys=True)
                    if sig in seen_sigs: continue     # 去重
                    seen_sigs.add(sig)
                    all_objs.append(obj)
                except: pass

# 1. 号码角色分析
for obj in all_objs:
    if '120120415' in str(obj.get('MSISDN','')):   # 作为目标
    elif '120120415' in str(obj.get('CallingNum','')):  # 作为主叫方
    elif '120120415' in str(obj.get('CalledNum','')):   # 作为被叫方

# 2. LIID 维度分组
liid_data = defaultdict(list)
for obj in all_objs:
    liid_data[str(obj.get('LIID',''))].append(obj)

# 3. 关联对方号码
peers = Counter()
for obj in all_objs:
    # 120120415 是目标 → 提取通话对方
    # 120120415 是对方 → 提取目标号码

# 4. EventDetail 序列
cin_groups = defaultdict(list)
for obj in all_objs:
    cin_groups[str(obj.get('CidNum',''))].append(obj)
for cin, objs in cin_groups.items():
    seq = tuple(sorted([o.get('EventDetail') for o in objs]))
    seq_count[seq] += 1
```

**Step 4 — 去重提取**

```bash
# symlink 目录绕过多文件限制
python3 extract_ligcdr.py /tmp/myfiles/ --liid 14029 --unique -o /tmp/ztlig_14029
# 或按 MSISDN 过滤
python3 extract_ligcdr.py /tmp/myfiles/ --msisdn 249120120415 --unique -o /tmp/ztlig_msisdn
```

`--unique` 按 JSON 内容摘要去重，`-o` 指定输出目录。输出包含 4564 个分组（按 LIID_CIN_时间）和 `raw_matches_filtered.txt`。

**Step 5 — TXT 报告生成**

报告用纯文本格式（TXT），不用 Markdown。约定：

**标题分隔：** `=` 用于一级标题，`-` 用于二级标题

**章节编号：** 一、二、三... / 4.1 / 4.2

**表格格式：** 空格/制表符对齐，固定宽度：

```
  指标                    数值
  ----                    ----
  涉及 LIID              5 个
  去重记录               56 条
```

**10 章节模板（按顺序）：**
1. 总体概况 — 文件数、记录数、CIN 数、LIID 数、非JSON行数
2. 文件分布 — 每个文件的记录数、时间范围
3. 号码角色分析（MSISDN 维度时）— 角色分布、格式分布
  或 被监听号码（LIID 维度时）— 关联 MSISDN 列表
4. 涉及 LIID（按 LIID 展开每个的场景）
5. 通话方向 — MO/MT 比率
6. 时间分布 — 按日统计
7. EventDetail 分布 — Code + 描述 + 数量
8. 网元与厂商 — NEID、Vendor、NetworkType
9. 关联号码 — 通话对方号码列表
10. 关键发现 — 3-6 条结构化结论
11. 输出文件 — 输出路径和清单

### ZTLIG LIG 同步命令

```bash
# 手动触发 LIG 与 Redis 同步（out-of-control/active 切换后必须执行）
syn ztlig1 300 redis 0
# 格式: syn ztlig<进程号> <超时秒数> redis <0/1>
# redis: 0=同步到数据库, 1=同步到LIG（通常用0）

# 查看夜间同步状态
cat ztlig1 300 | grep night

# 验证同步后 target 信息\nredis-cli -h <REDIS_IP> -c -p 6379 hget TMC_TARGET_INFO <targetId>\n```

### out-of-control 网元行为

当网元被标记为 out-of-control 后：

| 影响 | 说明 |
|------|------|
| LIG 夜间同步 | **不往该网元同步** — 所有 target 设控信息不会下发 |
| OWLS 页面展示 | **不显示** — 设控在该网元的 target 在管理页面不可见 |
| NE-target 关系 | **自动删除** — 网元与 target 的对应关系被清除 |
| 后续设控 | 客户设控 target 到该网元后，页面上看不到，以为没设上 |
| 恢复流程 | 先取消 out-of-control → 手工执行 `syn ztlig1 300 redis 0` |

**如何查看当前哪些网元 out-of-control：**\n```bash\n# Redis 端\nredis-cli -h <REDIS_IP> -c -p 6379 hgetall INVALID_NET_INFO\n\n# GP 端 — 查操作日志中最后一次 operation_type=8 且无对应 type=9 的 ne_id\n#（param 字段含 \\r\\n 换行，注意文本截取）\nselect param, max(create_time) as last_stop_time\nfrom SYS_OPERATION_LOG\nwhere second_level_menu = 'neidManagement' and operation_type = 8 and result = 1\n  and param not in (\n    select param from SYS_OPERATION_LOG\n    where second_level_menu = 'neidManagement' and operation_type = 9 and result = 1\n  )\ngroup by param order by param;\n\n# 查看单网元停控/起控历史\nselect * from SYS_OPERATION_LOG\nwhere second_level_menu = 'neidManagement'\n  and param like 'param=XX%'  -- XX=ne_id\n  and operation_type in (8, 9)\norder by id;\n```

**GP vs ZTLIG 网元编号差异：**
- CS 域网元：`rds_neid_info.ne_id` = `ztlig.cfg` 中的 VNEID（全匹配）
- PS 域（SU）：`ne_id=15/16` ≠ VNEID=19/20（两套编号）
- 部分网元仅存在于 GP 中，ztlig.cfg 中无对应 VNE 配置
- 少数网元的 `ne_id_real`（hi2_neid）与 ztlig.cfg 不一致（如 ne_id=27 KTN-OMU）

## 七、系统关键信息

### 站点架构
- **站点A**: 215.152.1.x 网段
- **站点B**: 192.172.16.x 网段（通过站点A 10.171.2.x 内网访问）
- 服务器主机名 rhino01~rhino09（大数据）、LIG01~LIG07（前台LIG）

### 关键端口
- Web UI: 8890
- Secpass: 8080
- Zabbix: 默认
- Kafka Manager: 9000

### Utimaco LIMS 用户/LEA 管理

```bash
# 用户管理
userlist                                 # 查所有用户
userlist userid=o1                       # 查单个用户
useradd userid=o1 username=Operator1 password=aysx6z7u usertype=O state=active lea=Lea1 functions=0
userdel userid=o1                        # 删用户（无输出）
usermod userid=o1 password=1q2w3e4r      # 改密码（无输出）

# 用户类型：A=Administrator, O=Operator, K=Auditor
# userlist 输出格式：
# user userid=o1 username=Operator1 usertype=O state=active lea=Lea1,Lea2 functions=0

# LEA 管理
lealist                                  # 查所有 LEA
lealist lea=auth1                        # 查单个 LEA
leaadd lea=LeaId leaname=LeaName maxtno=500 icddur=30 country=0
# 成功输出：lea_created lea=LeaId

# lealist 输出字段：lea(15字符)/leaname(60字符)/maxtno/icddur/country
# enckey/account/groupname/ipaddress (HSM/SSL加密，仅管理员参数)
# leaadd 参数：lea(M)+leaname(M) → maxtno/icddur/country/enckey/account/password/groupname/ipaddress 均为 O
```

## 八、厂商远程管理接口速查

| 厂商 | 系统 | 管理方式 | 端口 | 关键命令/协议 |
|------|------|---------|------|-------------|
| **中兴 CS** | ZXUN LIG | Telnet/SSH CLI | 23/22 | 65xx 系列：`ADD LITGT`(6505)、`SHW TGTINF`(6510)、`SET BARRING`(6529) |
| **Utimaco** | LIMS | **RAI 二进制 TCP 协议** | **52134** | RAI-SP: LOGIN(PDU1)/COMMAND(PDU4)/REPLY(PDU5)；RAI-CL: `tadd`/`tlist`/`tdel(tno_id)`/`tmod(tno_id)`/`tstate`/`tnelist`/`mclist`/`mcadd`/`mcdel`/`mcmod`/`nelist`/`neadd`/`nedel`/`nemod`/`necheck`/`nepurge`/`plist`/`alarmlist`/`nodeactionlist`/`arealist`/`userlist`/`useradd`/`userdel`/`usermod`/`lealist`/`leaadd` |
| **华为 5GC** | SVC-5GC LIG | X1 接口 (TCP+ASN.1 BER) | 自定义 | X1 SET_TARGET / DELETE_TARGET / QUERY_TARGET |

### ZTE CS HI1 CLI 常用命令

```bash
# 设控
ADD LITGT: MCID=1: LIID=1: TT=5: TI=<IMSI>: IT=3: FD=0: NENo=52:
# 6505:1=1:2=1:3=5:4=460030927640001:5=3:6=0:

# 查目标状态（含位置、IMSI、IMEI、MSISDN、STATE、BARRING）
SHW TGTINF: TT=5: TI=<IMSI>:

# 设限制
SET BARRING:MCID=1:LIID=use1:BARRING=1:
```

### Utimaco LIMS RAI 常用命令

```bash
# 设控（必须先 icdadd → icdact → tadd）
icdadd lea=auth1 fileref="case1" doo=20260618 start=202606180000 stop=202606302359 class=3
icdact icd=00302
tadd icd=00302 tno=<MSISDN> ttype=MSISDN liid=LI01 net=GSM dtype=VOICE,IRI mc_voice=2 mc_iri=27 doo=20260618

# 查目标
tlist icd=00302

# 删目标（用 tno_id，必填 tno_id + doo，成功无输出）
tdel tno_id=1 doo=20260618

# 改目标（不传则保留，传入则替换，doo 必填）
tmod tno_id=1 liid="" doo=20260618                     # 清空 LIID
tmod tno_id=1 mc_voice=5 doo=20260618                  # 替换语音 MC
tmod tno_id=2 net=GSM,GPRS mc_data=42 doo=20020501     # 改网络+数据MC
tmod tno_id=3 dtype=VOICE mc_data=none mcflags=423 area=1,4 doo=20100404  # 区域拦截+Flags
tmod tno_id=4 fix_neid=UTFN_2 doo=20100404              # 改固网网元
tmod tno_id=6 cmts_neid=CMTS_123_2 doo=20100404         # 改Cable网元

# 位置请求（LBS 网络，用 icd+tno 而非 tno_id，3个M参数，成功无输出）
tstate icd=00302 tno=0031223 doo=20020730

# 查询网元上的所有目标（仅Nokia/Huawei/Broadsoft/Starent/Sonus/Ericsson NE支持，非确定性结果）
tnelist neid=NOLI_1,NOCS_1
# 输出示例：
# netarget neid=NOLI_1 tno=003122357654765
# netarget neid=NOCS_1 tno="Communication Error"
# netarget neid=NOCS_1 tno="Parsing Error"

# MC 管理
mclist mc=34                               # 查单个MC（38个输出字段）
mcadd lea="Lea1" mctype=FTP ipaddr=192.168.23.112 user=anonymous pwd=anonymous dir=/srec  # 创建FTP MC
mcadd lea="auth3" mctype=ISDN isdn=72118227                                                    # 创建ISDN MC
mcadd lea="Lea1" mctype=TCP ipaddr=192.168.23.113 port=54321 keepalive=yes                     # 创建TCP MC
mcdel mc=23                                # 删除MC（被目标引用时失败码630）
mcmod mc=23 pwd=1q2w3e4r                   # 修改MC密码

# ⚠️ Utimaco tmod 参数精确语义：
# mc_voice: "If the argument is not present, the existing MC assignment is kept.
#   Otherwise, McVoice must be the Id of an existing monitoring center, and will replace the existing voice MC."
# mc_iri: "If the argument is not present, the existing MC assignment is kept.
#   Otherwise, McIri must be the Id of an existing monitoring center, and will replace the existing IRI MC."
# mc_data: "If the argument is not present, the existing MC assignment is kept.
#   Otherwise, McData must be the Id of an existing monitoring center, and will replace the existing data MC."
# mc_iri_po: "If not present, IRI delivery has been requested for this target by IRI-MC."
# liid: "To delete the LI identification of a target, use liid=\"\"."
# doo (tmod): "The date of order for the ICD change. Same format as in icdadd (cf. 4.5.2)"
# net: comma-separated list of network IDs (cf. 4.1.3), e.g. GSM,GPRS
# dtype: comma-separated list of data types (VOICE,IRI,DATA) (cf. 4.1.4)
# ⚠️ net/dtype/mc_xxx 必须遵循 LIMS 业务规则 (cf. 4.2.2/4.2.3)
```

## 九、Ericsson X1 SOAP 接口测试（SoapUI + Python Mock）

当需要测试 Ericsson IMS LI External API (X1) 的 WarrantService / SessionService SOAP 接口时使用。

### 项目文件

- **SoapUI 项目**: `/home/andymao/SmartBear/ericsson-x1-init.xml`（WSDL 引用版，适合 GUI 使用）
- **WSDL/XSD**: `/home/andymao/SmartBear/x1-test/`（External_API_WS_1dot8 版，WSDL 端点已指向 mock 端口 19090）
- **Python Mock 模拟器**: `/tmp/ericsson-li-mock.py`

### X1 初始化流程

```
1. SessionService.login             → sessionID
2. WarrantService.createWarrant     → warrantID（关键 X1 操作）
   ├── header (requestType=CREATE=1, userID, sessionID)
   ├── item (warrantItem: warrantID=-1, targetNumber, neName, lea...)
   └── dtlWarrants[].neType (MSC/SIPSERVER/GPRS) 每个 NE 类型一个
3. WarrantService.getWarrantList    → 验证创建结果
4. WarrantService.deleteWarrant     → 清理
```

### ⚠️ SoapUI 5.10.0 testrunner 限制

SoapUI 5.10.0 的 `testrunner.sh` 在命令行/无头模式下存在已知问题——无法通过项目 XML 中的 `xsi:type` 属性实例化测试步骤（无论是 `WsdlTestRequestStep` 还是 `GroovyScriptStep` 均受影响）。表现为项目加载成功、测试用例运行（FINISHED），但 TestSteps=0，实际不发送任何 SOAP 请求。

**解决方案**：
- **交互式调试**: 使用 SoapUI GUI 打开项目文件，直接点 Send
- **命令行自动化**: 使用 Python mock + curl（已验证通过）
- **参考**: `references/ericsson-x1-soap-testing.md` 有完整的 curl 命令模板

### Python Mock 测试方式

```bash
python3 /tmp/ericsson-li-mock.py &        # 启动 mock（端口 19090）
curl ... -H "SOAPAction: urn:Login" ...     # 发送 SOAP 请求
curl ... -H "SOAPAction: urn:CreateWarrant" ...
kill %1                                     # 清理
```

Mock 响应：code=3 (SUCCESS), objectId=10001 (warrantID)，支持所有四个操作。

## 九、OpenLI 开源 LI 系统

OpenLI 是新西兰怀卡托大学 WAND 团队开发的 ETSI 合规开源合法监听系统，现由 SearchLight Ltd 维护。适用于 LI 系统开发评估、测试环境搭建。

### 三组件架构
- **Provisioner** — 中央设控控制器，REST API
- **Collector** — 抓包+ETSI 编码（SIP/Radius/GTP/Email）
- **Mediator** — HI2/HI3 交付，需 RabbitMQ

### 构建依赖链
```
wandio (v6.0.6) → libtrace (v7.2.4) → OpenLI (v1.1.19)
                                       ↗ libwandder (v2.4.5)
```

完整构建步骤、最小测试配置、VS Code 集成见 `references/openli-build-reference.md`。

## 十、语音处理架构

本会话中学习了以下语音处理系统，见 `knowledge/li/projects/STCMS-MSVRS/voice-processing-architecture.md` 和 `voiceprint-match.md`：

### 10.1 四系统语音处理对比

| 系统 | 转码组件 | 输入→输出 | 特点 |
|------|---------|-----------|------|
| **STCMS/MSVRS** | TPF | 格式一(私有)→格式三(PCMA/WAV) | Kafka 实时流，TPF 多模块 |
| **TMC** | RVF | X3口原始编码→PCMA(不带头) | TDM直出PCMA，IP需RVF |
| **TSPS** | VDC | 私有格式→WAV/PCMA | 类似STCMS但转码不同 |
| **SICMS** | 播放器内置 | 私有格式原始编解码 | 仅录播，无实时播放 |

### 10.2 语音文件格式

| 格式 | 状态 | 文件头 | 语音帧 |
|------|------|--------|--------|
| **格式一** | 在用 | 32B(NAP2)+帧头(9B/pt+长度+SEQ+时间戳) | 变长原始编码 |
| **格式二** | 废弃 | 256B(全0) | 160B固定PCMA, 50fps |
| **格式三** | 在用 | 44B(标准WAV RIFF头) | 160B固定PCMA, 50fps |

格式三参数已验证符合 ITU-T G.711 / RFC 3551 标准，WAV 44B 头符合 Microsoft RIFF 规范。

### 10.3 声纹匹配（Voiceprint Match）

- **实时匹配**: Flink消费csp-etl → TPF转码 → 声扬匹配 → 入GP
- **历史匹配**: Web创建任务 → Kafka topic → historyvoice_transcode转码 → historyvoice_match匹配 → 入GP
- 声扬引擎: `http://192.168.42.16:38870`，阈值60分，TOP10
- 匹配方式：1个检材→样本 / 多检材→样本匹配检材
- License限制：默认全局10个声纹库同时匹配
- Redis key: `VOICE_REALTIME_MATCH_TASKS`, `VoiceCount_{taskId}`

详见 `knowledge/li/projects/STCMS-MSVRS/voiceprint-match.md`

## 十一、关联技能

- `zte-li` — ZTLIG 网关配置、进程架构、命令参考
- `huawei-hi2` — 华为 CS/IMS LI 协议及 X1/X2/X3 接口解码
- `etsi-lawful-intercept` — ETSI LI 标准体系
- `bigdata-platform-ops` — HDP 大数据平台通用运维
- 各组件专家技能：`hdfs-expert`、`kafka-ops-expert`、`hbase-ops` 等

## 十二、常见 Pitfalls

### 设控号码选错
- MTN/ZAIN 出局必须选 ISDN，选 MSISDN 会导致设控不生效
- SU 出局和本地呼叫必须选 MSISDN

### 网元 out-of-control 后客户继续设控
- 客户在 out-of-control 网元上设控 target 后，OWLS 页面不显示，客户以为没设上
- 必须先取消 out-of-control → 手工 syn 同步 → 再通知客户

### SSH被暴力破解锁定
- 远程站点B反复输错密码后，root 会被 faillock 锁定，IP 会被临时拦截
- 必须本地登录站点B执行 `faillock --user root --reset`

### 离线任务路径问题
- 站点A与站点B的定时任务脚本路径不同
- 站点B的脚本路径为 `bin/dt/processD.sh` 而非 `bin/processD.sh`

### Gremlin Server 吊死
- JanusGraph 的 Gremlin Server 会无故僵死
- 必须 kill -9 后再启动，`gremlin-server.sh start` 中的 PID 检查可能误判

### MPP Loader UnknownHostException
- `/etc/hosts` 中缺少目标主机名映射
- 添加 `192.172.16.11 rhino01` 后重启进程

### ⚠️ 安全红线 — LI 敏感内容禁止发送到外网 LLM
本技能涉及 LI/LIG 领域，以下内容**严禁**通过在线 LLM API（如 DeepSeek、OpenAI 等外网模型）处理：

**禁止向外发送的内容类别：**
- **ZTLIG 架构分析** — 二进制符号（`nm`/`strings` 输出的函数名、变量名）、进程间拓扑、线程架构
- **配置信息** — `ztlig.cfg` 内容、现场部署配置、端口映射、网元对接参数
- **站点拓扑** — 站点 A/B 网络拓扑、IP 地址规划、Kafka/Redis/DB 集群信息
- **LI 厂商协议细节** — 解码逻辑、ASN.1 模块实现、厂商特有字段含义
- **现场源码** — `~/work-projects/ETSI-ASN1-Assistant/`、`~/work-projects/A1/` 等目录下的源码

**处理规则：**
- 仅允许本地文件操作（`read_file`/`search_files`/`patch`/`write_file`）
- 必须获得用户明确许可后才能读取这些内容
- 需要 LLM 辅助分析时，必须确认当前模型是**本地部署模型**而非外网 API
- 日常非 LI 任务可正常使用外网 API
- 详细规则见 skill: `knowledge-privacy-policy` → LEVEL 6 本地源码安全隔离

## 十二、参考文件
- `references/business-topic-field-dictionary.md` — Kafka business topic 字段字典
- `references/utimaco-rai-cli-quickref.md` — Utimaco LIMS RAI CLI 速查表
- `references/owls-gp-query-patterns.md` — OWLS GP 数据库查询模式
- `references/A1-北苏丹谛听系统运维手册.md`
- `references/ericsson-x1-soap-testing.md` — Ericsson IMS LI X1 SOAP 接口 curl 测试模板
- `references/ztlig-ssf-oms-ats-csc-analysis.md` — SSF 实例与 OMU-ATS-CSC 信令关系分析
- `references/a1-vneid-mapping.md` — A1 项目 VNEID ↔ 实际网元映射速查表
- `references/ztlig-ligcdr-extraction.md` — ZTLIG2 LigCdr 日志提取与分析参考（V1.2 工具）
- `references/li-flask-web-patterns.md` — LI Flask Web 工具开发参考（子目录部署、ASN.1 错误分类、版本管理、GFW推送）
