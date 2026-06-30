---
name: a1-project-sudan-li
category: telecom
description: 北苏丹谛听(A1项目)系统日常维护、紧急流程与问题排查 — 覆盖HDP大数据集群+ZTLIG+SICMS+OWLS全栈
platform: A1 Project
severity: high
verified: true
author: Andy Mao
date: 2026-06-16
tags: [A1, Sudan, LI, ZTLIG, LIG, OWLS, SICMS, HDP, MTN, ZAIN, SU]
---

# A1项目：北苏丹谛听系统运维技能

## 系统概述

双站点架构：

| 项目 | 站点A | 站点B |
|------|-------|-------|
| **位置** | **PSD — 苏丹港 (Port Sudan)** | **ATB — 阿特巴拉 (Atbara)** |
| 角色 | 主站点 | 远程站点 |
| 网段 | 215.152.1.0/24 | 192.172.16.0/24 |
| 主机前缀 | rhino01~09 | rhino01~09 |
| LIG前缀 | LIG01~07 | - |

### 站点配置文件

ZTLIG 配置文件位于 `~/projects/A1/202606/A1-ZTLIG-CONFIG/`，按「运营商-站点-域」命名：

| 文件 | 运营商 | 站点 | 位置 | 域 | 大小 |
|------|--------|:----:|:----:|:--:|:----:|
| `SU-A-CS-ztlig.cfg` | 苏丹(SU) | A | PSD | CS | 88K |
| `SU-A-PS-ztlig.cfg` | 苏丹(SU) | A | PSD | PS | 18K |
| `SU-B-CS-ztlig.cfg` | 苏丹(SU) | B | ATB | CS | 87K |
| `ZAIN-A-CS-ztlig.cfg` | ZAIN | A | PSD | CS | 68K |
| `ZAIN-A-PS.ztlig.cfg` | ZAIN | A | PSD | PS | 22K |
| `ZAIN-B-CS-ztlig.cfg` | ZAIN | B | ATB | CS | 68K |
| `MTN-A-CS-ztlig.cfg` | MTN | A | PSD | CS | 39K |
| `MTN-B-CS-ztlig.cfg` | MTN | B | ATB | CS | 39K |

- **A** = 站点 A (PSD 苏丹港) — 部署 CS+PS 双域
- **B** = 站点 B (ATB 阿特巴拉) — 目前仅 CS 域

**配置对比发现**: A/B 站配置几乎完全镜像（仅 IP/leaid/x1_user 不同），但 A 站多一个 SSF_1310（绑定 OMU-ATS-CSC），原因是 PSD 站的华为 SVC 设备中 CSCF+ATS 复用同一 IP，VoWiFi SIP 信令也从该网元出口，需独立 SSF 处理。\
ZAIN 和 MTN 的华为 SVC 设备仅使用 OMU 功能（补充业务 CDR），不走 VoWiFi 信令，因此不需要该 SSF。\
详见 HW LI 技能 `references/ztlig-ssf-oms-ats-csc-analysis.md` 和 `~/knowledge/li/HW/hw-li-ztlig-ssf-analysis-experience.md`。
| AnyDesk | 1486642146 / security@1234 | 1725897961 / Sud$2026! |
| SECPASS | http://215.152.1.11:8080 admin/admin | http://192.172.16.11:8080 admin/admin |
| ZABBIX | http://215.152.1.26 Admin/zabbix | http://192.172.16.26/zabbix Admin/zabbix |
| Kafka Manager | http://215.152.1.15:9000/clusters/TMC-A | http://192.172.16.15:9000/clusters/SiteB |

测试账号：wangqq123 / Wang@123 或 Wang@1234（每3个月改密）

## 设控逻辑

- **MTN/ZAIN出局呼叫** → 设控号码选 **ISDN**
- **SU出局和本地呼叫** → 设控号码选 **MSISDN**
- **MTN/ZAIN/SU国漫** → 设控号码选 **ISDN**
- **VOLTE设控** → 按VOLTE协议走

## 站点访问

**Windows 永久路由（管理员CLI）：**
```cmd
route add 215.152.1.0 mask 255.255.255.0 192.168.123.254 -p
route add 192.168.2.0 mask 255.255.255.0 192.168.123.254 -p
# 删除
route delete 215.152.1.0
route delete 192.168.2.0
```

**站点B访问：** 通过站点A服务器的10.171.2.x内网IP访问（10.171.2.31对应站点B的rhino01）
**SSH被锁处理：** 输错root密码会触发faillock，清除方法：
```bash
faillock --user root --reset
# 检查 /etc/security/access.conf 和 /etc/hosts.deny
grep -i root /etc/security/access.conf
```

## 主机映射

Windows 客户端需配置 hosts：

```
215.152.1.11 rhino01  215.152.1.12 rhino02  ...  215.152.1.19 rhino09
215.152.1.20 LIG01   215.152.1.21 LIG02     ...  215.152.1.26 LIG07
```

站点B通过站点A的10.171.2.x内网IP访问。

## 大数据组件巡检速查

### HDFS
```bash
# 检查块状态
hdfs dfsadmin -report | grep -E "Blocks|Missing|Corrupt|Under replicated"

# 列出缺失块文件
hdfs fsck / -list-corruptfileblocks

# 触发副本恢复
hdfs fsck / -replicate

# 检查NameNode HA状态
hdfs haadmin -getServiceState nn1
hdfs haadmin -getServiceState nn2

# 检查Checkpoint
ls -ltr /data01/hadoop/hdfs/namenode/current/fsimage_*
grep -i checkpoint /data01/var/log/hadoop/hdfs/hadoop-hdfs-namenode-*.log | tail -20

# 快速验证配置完整性
hdfs getconf -confKey dfs.namenode.rpc-address.nameservice1.nn2

# 手动触发EditLog滚动（触发checkpoint前需要）
hdfs dfsadmin -rollEdits

# 手动强制保存命名空间
hdfs dfsadmin -safemode enter   # 进入安全模式（只读）
hdfs dfsadmin -saveNamespace    # 保存命名空间
hdfs dfsadmin -safemode leave   # 退出安全模式

# 综合分析缺失块
hdfs fsck / -files -blocks -locations -replicaDetails | grep -i 'MISSING\|CORRUPT'

# 删除损坏文件
hdfs fsck / -delete
```

### YARN
```bash
# 查看应用
yarn application -list
# 查看队列
yarn queue -status <queue_name>
# 查看NodeManager状态
yarn node -list
```

### Kafka
```bash
# 查看topic列表
kafka-topics --zookeeper localhost:2181 --list
# 查看consumer group延迟
kafka-consumer-groups --bootstrap-server localhost:9092 --group <group> --describe
```

> ⚠️ A1 项目专属：Kafka IP（215.152.1.15:9092）、Topic 名称（TMC_TARGET_INFO、SICMS_STREAM_IPDR 等）均为 A1 项目专属，不适用于 OWLS/ZTLIG 等其他项目。使用前必须人工确认。
> 详细 Kafka 操作（Manager启动/Topic管理/生产消费/Consumer Group诊断/设控JSON字段/日志解读）见知识库笔记：[[Kafka-Manager运维与CLI命令速查]]

### JanusGraph / Gremlin
```bash
# 重启Gremlin Server
ps -ef | grep gremlin | grep -v grep | awk '{print $2}' | xargs kill -9
export JANUSGRAPH_YAML=/home/websrv/janusgraph/conf/gremlin-server/socket-gremlin-server.yaml
cd /home/websrv/janusgraph/bin && ./gremlin-server.sh start
```

> 详细查询模式（connect 边/sourceno/date/tree()）见知识库笔记：[[A1项目Gremlin-JaniusGraph操作手册]]

> Gremlin Console 加载失败的修复：`wget https://repo1.maven.org/maven2/org/fusesource/jansi/jansi/1.18/jansi-1.18.jar` 并拷贝到 `/home/websrv/janusgraph/lib/`。

### Greenplum

**连接：**
```bash
psql -h 215.152.1.13 -p 5432 -U daedb -d bigdata
```

**集群启停：**
```bash
gpstart -a                 # 启动（免确认）
gpstop -a -M fast          # 快速停止（免确认）
gpstop -r -a -M immediate  # 立即重启（不回滚事务，免确认）
gpstate -s                 # 集群详细信息
gpstate -e                 # 故障/降级 Segment
```

> 详细查询（设控工作流/lims_bds_target/lims_bds_group_target/hts_clue_hit/bds_profile_statistics/psql元命令/COPY导出）见知识库笔记：[[A1项目Greenplum-psql查询手册]]

**VNEID → 实际网元查询：**
hts_lig_hi2 分区表的 `neid` 字段 = ZTLIG 定义的 VNEID（虚拟网元 ID）。通过 `rds_neid_info` 表或 ZTLIG 配置可映射到实际网元名/别名。

```sql
-- 查分区表中有哪些 VNEID
SELECT neid, count(*) AS cnt
FROM hts_lig_hi2_1_prt_part_YYYYMMDD_2_prt_cdr
GROUP BY neid ORDER BY cnt DESC;

-- 查 rds_neid_info 获取网元别名
SELECT * FROM rds_neid_info WHERE neid = <VNEID>;
-- 列结构用 \d rds_neid_info 确认

-- 两表 JOIN 统计
SELECT h.neid, r.*, count(*) AS cnt
FROM hts_lig_hi2_1_prt_part_YYYYMMDD_2_prt_cdr h
LEFT JOIN rds_neid_info r ON h.neid = r.neid
GROUP BY h.neid, r.*;
```

详见 `references/vneid-neid-gp-query.md`（含 ZTLIG 配置示例、数据源编号、注意事项）。

**内存调优（OOM时调整）：**
```bash
gpconfig -c gp_vmem_protect_limit -v 20000 -m 20000    # 30G→20G
gpconfig -s gp_vmem_protect_limit                        # 确认
gpstop -ar                                               # 重启生效
# 公式：并发数 × statement_mem <= gp_vmem_protect_limit
# 日志路径：/home/daedb/gpmaster/gpseg-1/pg_log
```

**分区管理：**
```bash
psql -U daedb -d bigdata -c "select * from base_addpart_config;"
psql -U daedb -d bigdata -c "update base_addpart_config set keep_time = 720 where lower(table_name) = 'hts_lig_hi2';"
```

**会话管理：**
```sql
-- 查看 bigdata 库的连接
SELECT * FROM pg_stat_activity WHERE datname = 'bigdata';
-- 断开指定会话（GP6: procpid, GP7: pid）
SELECT pg_terminate_backend(14063);
```

### 离线任务

crontab 在 rhino02 上：
```bash
0 1 * * * sh /home/rhino/RelationGraph/timetaskall/allmission.sh
5 */1 * * * sh /home/rhino/RelationGraph/timetaskall/allmissiontwo.sh
0 5 * * * sh /home/rhino/still-points-1.0/bin/start-still-points.sh
0 */2 * * * sh /home/rhino/RelationGraph/bin/combine-file.sh
```
离线任务结果目录：`/home/rhino/RelationGraph/bin/process/`
MPPLoader 日志：`tailf mpploader.log`

### Redis
```bash
redis-cli -h localhost -p 6379
KEYS * | INFO | DBSIZE | MEMORY STATS
```

### ES (Cerebro)
```bash
# ES 健康检查
curl -XGET 'http://localhost:9200/_cluster/health?pretty'
curl -XGET 'http://localhost:9200/_cat/indices?v'

# ES Head Web UI: http://215.152.1.17:9000 (站点A)
# 站点B 无 ES Head 部署
# 启动 Cerebro: nohup /usr/share/cerebro/bin/cerebro &
```

### MySQL (ZTLIG)
```bash
# ZTLIG1 服务器上连接 ztlig_target 库
mysql -u sa -psecurity ztlig_target

# 备份（含存储过程）
mysqldump -h <IP> -u sa -psecurity --routines ztlig_target > dump.sql

# 备份脚本路径：/home/rhino/mysql-server/bin/mysql_backup_sk.sh
```

### ZooKeeper
```bash
# 连接（ZK客户端路径: /usr/hdp/3.1.0.0-78/zookeeper/bin）
zkCli.sh -server 127.0.0.1:2181

# 常用查询（在zkCli内）
ls /                              # 查看根znode
ls /brokers/ids                   # Kafka Broker列表
ls /brokers/topics                # Kafka Topic列表
ls /hbase/rs                      # HBase RegionServer列表
ls /hadoop-ha                     # Hadoop HA选主
get /controller                   # 当前Kafka Controller
get /brokers/ids/1001             # 特定Broker信息

# 四字命令（不用进zkCli）
echo stat | nc 127.0.0.1 2181    # 服务状态
echo ruok | nc 127.0.0.1 2181    # 健康检查（返回imok）
echo cons | nc 127.0.0.1 2181    # 连接客户端
```

> ⚠️ ZK 是底层基础设施。如果 ZK 没起来，Hadoop/HBase/Kafka 都起不来。

### HBase
```bash
# 进入 HBase Shell
hbase shell

# 常用命令
list;                                                # 列出所有表
get "zxsk_tmc:20250612", "rowkey"                    # 按rowkey查
scan 'zxsk_tmc:20250612', {LIMIT => 5}               # 扫前5条
disable '表名'; drop '表名'                           # 删除表

# Web UI: http://rhino01:16010 (当前版本 HBase 2.5.1)
```

### Hive / Beeline
```bash
# Hive CLI（rhino05上）
su rhino
hive
> show databases;                          # default, information_schema, sys, zxsk_lis
> use zxsk_lis;
> show tables like 'tr*';
> show partitions owls_wide_table;
> show partitions owls_wide_table partition(`table`='trs_lig_hi2');
> desc formatted 表名;
> msck repair table owls_wide_table partition(`table`='trs_lig_hi2');  # 修复元数据

# Beeline（JDBC远程连接，推荐）
beeline -u jdbc:hive2://215.152.1.11:10000

# 日期时间转换
SELECT from_unixtime(1750567970);         # 时间戳→日期
SELECT unix_timestamp('2024-06-23 11:21:22');  # 日期→时间戳
```

> Tez 是 Hive 3.x 默认执行引擎。Hive 本身不执行任务，只生成 DAG 提交给 YARN/Tez。

### Tez (Hive执行引擎) 与 YARN 队列

#### 问题：Tez 任务失败
```bash
# 错误: "Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.tez.TezTask"
# YARN URL: http://rhino01:8088/cluster/apps/FAILED
```

**常见原因**: YARN Capacity Scheduler 中 `root` 是父队列，不能直接提交任务。

**解决**:
```sql
-- 指定叶子队列
set tez.queue.name=root.default;

-- 可用队列: root.default, root.spark-max, root.spark-middle, root.spark-min

-- 查看可用队列
yarn queue -status root
-- 或打开 http://rhino01:8088/cluster/scheduler

-- 临时切回 MR（规避 Tez 问题）
set hive.execution.engine=mr;

-- ORC/vector 兼容问题
set hive.vectorized.execution.enabled=false;
```

> 执行引擎对比：MR(稳定但慢,写磁盘多) → Tez(快,默认,数据直传内存) → Spark(内存计算)

### Zabbix API

```bash
# 登录获取 token
curl -s -X POST -H 'Content-Type: application/json-rpc' \
  -d '{"jsonrpc":"2.0","method":"user.login","params":{"username":"Admin","password":"zabbix"},"id":1}' \
  http://215.152.1.26/zabbix/api_jsonrpc.php | jq

# 获取主机列表
curl -s -X POST -H 'Content-Type: application/json-rpc' \
  -d '{"jsonrpc":"2.0","method":"host.get","params":{"output":["hostid","host","name"]},"auth":"<TOKEN>","id":2}' \
  http://215.152.1.26/zabbix/api_jsonrpc.php | jq

# 获取当前告警
curl -s -X POST -H 'Content-Type: application/json-rpc' \
  -d '{"jsonrpc":"2.0","method":"problem.get","params":{"output":"extend","sortfield":"eventid","sortorder":"DESC","recent":true},"auth":"<TOKEN>","id":4}' \
  http://215.152.1.26/zabbix/api_jsonrpc.php | jq
```

# Debug命令
debug ztlig1 300 db on
debug ztlig1 300 web on
debug ztlig1 300 huawei on
write ztlig1 300 logfile on

# 夜间同步阈值保护（Redis vs MySQL 差距过大时跳过）
syn ztlig1 300 redis 0    # 关闭阈值，强制执行三方同步

# 查看网元目标同步差异（ztsh内执行）
start ztlig1 300 hwmsc 1 23 list

# 查看版本目录
find /home -name "cmf" 2>/dev/null
# 示例: /home/20250331/bin/cmf

# 设控不同步快速诊断
# 1) grep "Lig1NightSync" ztlig1.300.txt | tail -5     ← 检查差距
# 2) grep "X_1 link authentication fail" ztlig1.300.txt  ← 检查X1失败
# 3) cat ztlig.cfg | grep "ztlig.ne.*valid_fg"          ← 检查无效网元
# 4) syn ztlig1 300 redis 0                             ← 强制同步
# 5) grep "ne syn handle succ" ztlig1.300.txt           ← 确认
```

> 详细运维（Crontab配置/DPDK PS重绑/SICM重绑/HugePages检查/日志备份/PSM捕包/MySQL连接/Night Sync阈值/X1认证失败处理/Kafka设控日志解读/快速诊断流程）见知识库笔记：[[ZTLIG运维手册]] 和 [[ZTLIG-MySQL数据库连接]]

### SICMS
```bash
# 版本目录
find /home -name "cmf" 2>/dev/null
# cmf重启 → dpdk_setup_linux.sh → keeppsmon.sh → ./cmf -d y

# PLD进程启动
pld -g 215.152.1.24 -s 463 -p 10463 -d y

# 运维命令
show running
show pld 463 dpdk_nic_stat         # 网卡丢包检查（Err_cnt，<1/50万）
show pld 463 dpi_mod stat          # PLD识别丢包检查（Fail列，<1/50万）
show pld 463 dpi recg all num      # 协议/应用识别检查
show pld 463 online_protocol       # 协议插件加载检查

# 抓包验证
tcpdump -i any -s0 -w /tmp/sicms_x2.pcap port 19001
```

> 完整运维手册见 [[ZTLIG运维手册#附录：SICMS 运维手册]]

## 系统重启流程（断电恢复）

1. **检查硬件状态** — 电源、硬盘、网络
2. **检查防火墙状态** — iptables/ufw
3. **检查NTP服务器** — `timedatectl` `ntpq -p`
4. **重启Secpass/Zabbix**:
   - Secpass Admin: http://215.152.1.11:8080
   - Zabbix: `/usr/local/zabbix/zabbix-server/sbin/zabbix_server -c /usr/local/zabbix/zabbix-server/etc/zabbix_server.conf`
5. **前台LIG系统重启** — 安装cmf → 安装PSM → 检查进程
6. **前台SICMS系统重启**
7. **后台系统(OWLS/SECPASS)** — 检查挂载(mount) → OWLS模块启动 → cron任务检查

> 💡 可视化版本：`references/restart-flowchart.html` — 含7步流程图+快速诊断命令卡片+rhino02定时任务表，可用Chrome打开。

## WEB-UI 调试 (Chrome DevTools)

当 WEB UI 页面数据异常、报错或响应慢时：

```bash
# Step 1: F12 → Network 面板
# Step 2: 筛选 Fetch/XHR 请求
# Step 3: 查看指定请求的:
#   - Payload: 请求参数（tid, mapId, sourceno）
#   - Preview/Response: 返回数据
#   - Initiator: 调用链（哪个组件/函数触发的请求）
#   - Timing: 各阶段耗时（TTFB > 3s 表示后端慢）
```

### OWLS 调用链解读

```
Promise.then
  Dr @ request.ts:107          ← Axios 发请求
  s  @ targetQuery.ts:24       ← 封装查询参数
  Pe @ middle.vue:1056         ← 中间层处理
  be @ QTable.vue:537          ← 表格组件触发
```

### 关联 WEB LOG 查数据库

```bash
# 从 WEB LOG 提取参数（TmcRequestPrint 日志）
grep "detailQuery" /home/websrv/listener-web-1.0/logs/*.log | tail -20

# 从日志中提取 tid 和 mapId，然后查 hts_lig_hi2
```

```sql
-- 数据库验证
SELECT * FROM hts_lig_hi2 WHERE tid = '<tid>' AND clue_id = <mapId>;
-- 查看字段映射
SELECT * FROM rds_source_define WHERE sourceno = '<tableName>';
```

> 详细教程见 skill:chrome-devtools-debug 和 KB笔记 [[WEB-UI跟踪与DevTools调试]]



### 1. 登录Web系统失败
检查系统组件进程是否正常。

### 2. 暂无数据 / 提前目标查询
检查HDFS分区、Hive表数据是否写入。
```sql
select * from trs_hi3_ipdr where date_partition='YYYYMMDDHH/' and msisdn!='' order by capturetime desc limit 100;
```

### 3. 设控目标不一致
检查ZTLIG前后台同步状态、MAP_ID对应关系。

### 4. 目标数量不一致
排查ZTLIG TARGET LIST的NE同步完整性。

### 5. 通话时长问题
检查媒体流 X3 接口数据。

### 6. 数据无法入库
检查Kafka Consumer → ES/HBase/Greenplum 全链路。

### 7. 语音丢失/播放慢/无法播放
检查语音文件存储服务器、ES/HBase PS数据。

### 8. PS-CDR查询为空
检查ES索引及CDR入库链路。

### 9. 离线任务空MPP
检查MPPLoader日志：
```bash
tail -f /home/rhino/RelationGraph/log/mpploader.log
```
常见错误：`UnknownHostException: Invalid host name: local host is: (unknown)` — 检查/etc/hosts。
重新执行离线任务：
```bash
sh /home/rhino/RelationGraph/timetaskall/allmissiontwo.sh
```

### 10. 关系图为空（I-Analysis）
- 检查Gremlin Server: `ps -ef|grep gremlin`
- WEB日志错误：`gremlin-groovy is not an available GremlinScriptEngine` → gremlin-server吊死
- Gremlin重启：
  ```bash
  ps -ef | grep gremlin | grep -v grep | awk '{print $2}' | xargs kill -9
  export JANUSGRAPH_YAML=/home/websrv/janusgraph/conf/gremlin-server/socket-gremlin-server.yaml
  cd /home/websrv/janusgraph/bin && ./gremlin-server.sh start
  ```
- 检查离线任务结果目录: `/home/rhino/RelationGraph/bin/process/`
- 检查MPPLoader日志: `tailf /home/rhino/mpploader-1.0/log/mpploader.log`
- MPPLoader路径问题：`UnknownHostException: local host is: (unknown)` → 补充/etc/hosts中站点B对rhino01的解析

### 11. 查询时有时无（查询慢）
检查WEB日志中GP OOM报错：
```
FATAL: Out of memory / Vmem limit reached
```
原因：Greenplum内存耗尽。`gp_vmem_protect_limit` 过大（30G），调整为20G重启生效：
```bash
gpconfig -c gp_vmem_protect_limit -v 20000 -m 20000
gpstop -ar
```

### 12. 管理员密码丢失
```sql
-- 初始化密码为明文 admin
update sys_user set password = 'UH0QX2DWWhba0jYVAalarA==' where user_name = 'admin';
```

### 13. 数据老化配置
- Greenplum: `update base_addpart_config set keep_time = 720 where lower(table_name) = 'hts_lig_hi2';`
- 语音/PS文件: `data-aging-2.0.0`工具，配置文件 `/home/rhino/data-aging-2.0.0/config/config.json`
- 需拷贝Hadoop/ES/HBase/Hive的xml配置到data-aging的config目录

### 24. 站点B路径问题（重要）
站点B的 `allmission.sh` 脚本中路径为：
```bash
# 站点B必须用 bin/processD.sh（而不是bin/dt/processD.sh）
sh bin/processD.sh call-relation-cmr.sh
sh bin/processD.sh phone-card-relation.sh
sh bin/processD.sh mult-code.sh
```
定时任务 `combine-file.sh` 也应调整为 `sh /home/rhino/RelationGraph/bin/combine-file.sh`（去掉dt/路径）。

### 25. VoWiFi 呼叫位置信息在 OWLS Web 不显示

**现象：** tcpdump 抓包中能提取到 cell-id 和 WiFi 公网 IP，但 OWLS Web 界面上位置字段为空。

**场景特征：**
- 呼叫类型：VoWiFi（SIP over ePDG → PGW → IMS）
- 被叫号码源：来自筛选文件（ZTLIG → Kafka → OWLS）
- ZTLIG X2 模块日志只截取了 From/To/P-Asserted-Identity 头，P-Access-Network-Info 不在日志明文输出中
- pcap 中 SIP 消息的 PANI 格式为 `IEEE-802.11`（WiFi 接入类型），含 `Wlan-ue-local-ip`（WiFi 公网 IP）和 `sbc-domain` 参数

**VoWiFi PANI 核心差异（与普通 VoLTE 对比）：**

| 对比项 | VoLTE (E-UTRAN) | VoWiFi (IEEE-802.11) |
|---|---|---|
| 接入类型 | `3GPP-E-UTRAN-FDD` | `IEEE-802.11` |
| 小区位置 | `utran-cell-id-3gpp=MCC.MNC.CellID` | **无标准 cell-id 参数** |
| 位置来源 | 基站侧直接提供 | SBC 附加 `last-utran-cell-id-3gpp` |
| UE 公网 IP | 无 | `Wlan-ue-local-ip=196.202.142.x` |

**关键发现：** pcap 确认 SBC（atbpcscf01）在 IEEE-802.11 PANI 末尾附加了 `"last-utran-cell-id-3gpp=6340704523F4C"` 参数，这是 ZTLIG 提取 Location 值的来源。该参数是非标准扩展（非 `utran-cell-id-3gpp`），代表 UE 最后注册的 LTE 小区。

**排查路径：**

1. 确认 Kafka OWLS_TMC 消息是否含有 `Location` 字段
2. 检查同一 CidNum 是否存在 NetworkType=13(IMS无位置) 先到、NetworkType=11(E-UTRAN有位置) 后到的时序问题
3. 检查 OWLS Web 是否只展示 LocationType=4(注册位置)，忽略 LocationType=1(呼叫实时位置)
4. 检查 Web 后端数据库(ES/GP)中该记录是否实际入库了 Location 值
5. 从 pcap 中提取原始 P-Access-Network-Info 头域，比对 ZTLIG 解析结果
6. **特殊场景：VoWiFi 的 LocationType=1 来自 `last-utran-cell-id-3gpp` 非标准参数，Web 展示逻辑可能需要适配**

**常见根因：**

| 根因 | 验证 | 修复 |
|---|---|---|
| LocationType=1 被 Web 忽略 | 检查 Web 代码 | 修复展示逻辑 |
| CidNum 去重取了无位置记录 | 按时间查看 CidNum 完整序列 | 优先取有位置的记录 |
| Location 字段入库但未渲染 | 直接查数据库 | 补全前端渲染 |
| **VoWiFi `last-utran-cell-id` 展示未适配** | 检查 Web 对 NetworkType=11 + LocationType=1 的处理 | 适配 VoWiFi 位置展示 |

**详细参考：** `references/vowifi-location-troubleshooting.md` — 含完整 PANI 参数字段表、pcap 分析命令、端到端数据链路验证、排查速查表。

## 参考文件
- `references/数据库表信息.md` — A1项目完整GP(54表)+HIVE(24表)体系
- `references/ztlig-cfg-vneid-extraction.md` — ztlig.cfg VNEID ↔ 实际网元名提取 awk 脚本 + 已知分段速查，含核心查询语句、sourceno映射、数据导出方法
- `references/vneid-neid-gp-query.md` — VNEID ↔ 实际网元 GP 查询方法：映射原理、6种查询SQL、ZTLIG配置示例、数据源编号、注意事项
- `references/ne-control-state-diagnostics.md` — 网元控制状态诊断：Redis INVALID_NET_INFO、GP SYS_OPERATION_LOG 审计、out-of-control 行为、起控后恢复流程
- `references/ztlig-release-package-analysis.md` — ZTLIG 发行包 (LISTENER V1.1.02_LIG_T11) 完整分析，含 8 进程架构、127 个厂商插件分类、ztlig2 深度函数分析、ztlig.cfg 配置段落速查
- `references/vowifi-location-troubleshooting.md` — VoWiFi 位置不显示排查指南（含 LocationType 含义、NetworkType 映射、排查步骤、常见根因对照表）
- `references/vowifi-wlan-ip-data-model-gap.md` — VoWiFi WLAN-ue-local-ip 数据模型缺口分析（含两日期对比、验证命令、协议分层图）
- `references/vowifi-dual-ne-ztlig-processing.md` — ZTLIG 双网元处理机制：SBC INVITE 分叉（两条 INVITE）、双 NE 拦截架构、CidNum 命名规律、SBC 预探测模式（Canceled Call Ahead）、Location 提取条件与失败场景、IMS 架构全貌与 ATS 位置生命周期、Pcap vs 日志对比分析、排查命令速查
- `~/projects/A1/202606/VOWIFI-architecture.svg` — 重构的暗色主题网元架构图（可打开 `VOWIFI-architecture.html` 查看）

## 关联 Skill
- `sinovatio-ztlig` — ZTLIG 网关系统（进程架构/ztlig.cfg/CLI命令/补丁分析）
- `chrome-devtools-debug` — Chrome DevTools 前端调试与 API 请求跟踪，适用 OWLS WEB-UI 前后端问题排查

## 参考文件

## 26. VoWiFi WLAN-ue-local-ip 在 OWLS 不显示 — LigCdr 数据模型局限

**现象：** tcpdump/PCAP 中 SIP P-Access-Network-Info 头域确认包含 `Wlan-ue-local-ip=196.202.142.135`，确认抓包设备为 iPhone（User-Agent: iOS/26.5 iPhone），但 OWLS/Deep Insight 的 CDR 界面完全不显示该 IP。

**与已知位置不显示问题（Section 25）的区别：**
- 位置不显示：`last-utran-cell-id-3gpp` 被 ZTLIG 正确提取为 `Location` 字段，但 OWLS Web 未渲染 → **UI/去重逻辑问题**
- WLAN IP 不显示：`Wlan-ue-local-ip` 字段在 LigCdr JSON schema 中**从未被定义** → **数据模型缺口**

### 根因：协议分层导致的数据模型缺失

```
HI2 X2 TCP 8890 port — BER 编码的 IRI 报告
  └─ iRI-Report-record (ASN.1 解码层)
       └─ sipMessage (SIP 文本)
            └─ P-Access-Network-Info header
                 └─ Wlan-ue-local-ip=196.202.142.135  ← HI2 深度 3 层

ZTLIG2 → Kafka → LigCdr JSON (23 字段 schema)
  └─ 没有 WlanUeLocalIp / WLAN-IP 字段
```

LigCdr 的 23 个字段只覆盖呼叫元数据的基本维度，`Wlan-ue-local-ip` 藏在 HI2 IRI 报告的 SIP P-Access-Network-Info 头域中，深度 3 层，ZTLIG2 在提取 LigCdr 时没有下钻到该层面。

### 为什么版本升级没有修复

OWLS 升级（Web UI / 后端入库）只影响 LigCdr JSON 的**展示和存储层**，不影响 ZTLIG2 的**数据提取层**。只要 ZTLIG2 → Kafka 的 LigCdr JSON schema 不新增 WlanUeLocalIp 字段，OWLS 无从显示。

### 修复方向

| 方案 | 修改层面 | 工作量 | 复杂度 |
|------|---------|--------|--------|
| ZTLIG2 新增字段 | 修改 LigCdr 提取逻辑，从 SIP PANI 解析 Wlan-ue-local-ip | 中 | 中 |
| SSF 模块增强 | SSF 接收 SIP 消息时提取并存储 | 中 | 中 |
| OWLS 接收新增字段 | 扩展 Kafka JSON 解析和新字段入库 | 小 | 低 |

**最可行的方案：** ZTLIG2 在 Kafka 消息中新增字段 `WlanUeLocalIp` / `WlanUeLocalPort`，从 `P-Access-Network-Info: IEEE-802.11` 头域正则提取。

### 如何验证 WLAN IP 存在

PCAP 层面（strings / tshark 均可）：
```bash
strings <pcap> | grep -o 'Wlan-ue-local-ip=[^";]*' | sort -u
strings <pcap> | grep "IEEE-802.11" | head -5
strings <pcap> | grep -oP 'icid-value="[^"]*"' | sort -u  # 与 OWLS 交叉引用
```

OWLS 层面：LigCdr JSON 无该字段。CidNum（IMS Charging ID）可用于跨源关联。

### 历史案例对比

| 日期 | WLAN IP | UE IP | P-CSCF | 端口 | 终端 | OWLS |
|:----:|:-------:|:-----:|:------:|:----:|:----:|:----:|
| 2026-06-23 | 196.202.142.135 | 10.201.24.98 | psdpcscf02 | 16567 | iPhone iOS/26.5 | ❌ |
| 2026-06-30 | 196.202.142.135 | 10.201.212.200 | atbpcscf01 | 21238 | iPhone iOS/26.5 | ❌ |

同一 WLAN IP（同一部 iPhone）两次分析均确认存在，OWLS 始终不显示，印证了数据模型缺口。

### WLAN IP 的用途

`Wlan-ue-local-ip` 是 UE 在 Wi-Fi 网络下的真实公网 IP（非 ePDG 隧道私网 IP）：
- 定位用户物理位置（城市/ISP 级）
- 确认呼叫确实走 WiFi 接入（区分 VoWiFi 与 VoLTE）
- 排除 NAT 混淆（隧道内 10.x.x.x 私网 vs 公网出口 IP）

## 补丁分析（lig-patch）

A1 项目的 ZTLIG 补丁集（ARM aarch64）位于 `/home/andymao/lig-patch/A1-LIG/`，共 18 个补丁（含 1 个重复），时间跨度 2025-09-05 ~ 2025-12-24：

| 时间段 | 补丁数 | 覆盖模块 | 核心问题 |
|:------:|:------:|----------|----------|
| 09-05 | 1 | psm/psm_ass (x86-64) | 进程管理拉起限制 |
| 10-09~10-19 | 3 | ztlig1 (libwebhi1+libetsihi1) | 内存泄漏→重构增强 |
| 10-26 | 1 | rvf (1.8MB) | 语音文件写入失败 |
| 11-01~11-05 | 4 | ztlig1 (libhwx1+ztlig1) | HWNE X1 协议库引入迭代 |
| 11-12~11-14 | 3 | ztlig3+X2+X3 (libhi3pro+libhi2pro) | recvmac+X2批量更新 |
| 12-03~12-04 | 2 | ztlig1 (libhwx1+libztsh+ztlig1.ini) | HWNE 大更新+Shell |
| 12-10~12-24 | 3 | ztlig3 (libhi3pro+libhwepcx3) | usrip→IPv6→微调 |

**分析方法**: `file`→`readelf`→`strings`→`r2` 6 步分析法。详见 `sinovatio-ztlig` skill 补丁分析章节和 SOP。

**安全规则 — 源码隔离**

本技能涉及 A1 项目 LI/LIG 系统，当需要读取或分析本地源码时：
- `~/work-projects/ETSI-ASN1-Assistant/`（HI2/X2 编解码实现）和 `~/work-projects/A1/`（ZTLIG 配置）等目录下的源码**严禁**发送到 Web 搜索引擎或在线 LLM API
- 仅允许本地文件操作（`read_file`/`search_files`/`patch`/`write_file`）和本地终端命令
- 必须先获得用户明确许可后才能读取这些源码
- 详细规则见 skill: `knowledge-privacy-policy` → LEVEL 6 本地源码安全隔离

## 知识库笔记索引

本技能涵盖以下知识库笔记（`knowledge/telecom/lawful_interception/` 和 `knowledge/telecom/a1-project/`）：

| 笔记 | 内容 | 会话 |
|------|------|------|
| [[华为LI技术文档索引]] | 华为LI 7份CHM文档索引（ETSI标准/EPC信令/VoLTE信令/CGP维护/监听手册/ETSI搭建/特通搭建） | ← 本会话 |
| [[Kafka-Manager运维与CLI命令速查]] | Kafka Manager启动、Topic管理、Consumer Group监控、设控数据生产/消费、设控JSON字段 | ← 本会话 |
| [[A1项目Gremlin-JaniusGraph操作手册]] | Gremlin查询模式（connect边/sourceno/date/tree()）、Server故障处理、jansi修复、时间戳转换、REST API | ← 本会话 |
| [[A1项目Greenplum-psql查询手册]] | GP连接、设控查询工作流（lims_bds_target→lims_bds_group_target→hts_clue_hit）、bds_profile_statistics、psql元命令、COPY导出 | ← 本会话 |
| [[ZTLIG-MySQL数据库连接]] | ZTLIG MySQL连接（sa/security/ztlig_target）、备份恢复 | ← 本会话 |
| [[ZTLIG运维手册]] | ZTLIG完整运维（配置/进程/故障/协议/Debug/PS重绑/Crontab/Night Sync阈值/SICMS附录/PSM捕包/Kafka设控日志/快速诊断/抓包命令/地址映射） | ← 本会话大幅扩展 |
| [[AI编程Skill体系参考]] | AI编程Skill vs Rule vs MCP概念、6类Skill速查、4个获取来源 | ← 本会话 |
| [[A1项目OWLS-SECPASS后台系统启动手册]] | OWLS后端16模块启动顺序、SECPASS 15组件启动、Kafka Manager/Cerebro手动检查 | ← 本会话新增 |
| [[WEB-UI跟踪与DevTools调试]] | WEB LOG关联查询、hts_lig_hi2验证、Chrome DevTools Network/Initiator/Timing分析 | ← 本会话新增 |
| [[Zabbix-API查询手册]] | Zabbix API认证、host.get/item.get/problem.get、jq格式化、A1主机列表 | ← 本会话新增 |
| [[A1项目网络配置与主机名映射]] | Windows永久路由、hosts文件（16台服务器）、服务器清单速查 | ← 本会话新增 |
| [[A1项目HDFS运维与NameNode Checkpoint]] | HDFS文件查看、块修复、NN Checkpoint、Roll Edits、安全模式 | ← 本会话新增 |
| [[A1项目ZooKeeper运维手册]] | ZK连接、19个znode说明、常用查询、四字命令 | ← 本会话新增 |
| [[A1项目HBase与Hive运维手册]] | HBase Shell/Web UI、Hive/Beeline查询、分区管理、msck repair、日期转换 | ← 本会话新增 |
| [[A1项目Hive_on_Tez执行引擎]] | Tez DAG流程、YARN队列问题、tez.queue.name指定、MR回退 | ← 本会话新增 |

## ZTLIG LigCdr 日志提取与分析

A1 项目 ZTLIG2 日志中 LigCdr 记录的提取和分析工作流，使用 `~/PCAP/20260623-A1-VOWIFI/extract_ligcdr.py` (V1.2, 已上传 GitHub ops-monitoring/ztlig-tools/)。

### 新增 V1.2 功能: 非 JSON 行匹配

设置过滤条件后，不含 JSON 结构的日志行也会按 LIID/MSISDN/CIN/EventDetail/Vendor/Neid 做文本子串匹配，输出到 `raw_matches_filtered.txt`。

### 分析工作流

```bash
# 1. 确定分布
grep -l '14029' A1-ztlig/*.txt

# 2. 去重提取（限 .txt 文件）
python3 extract_ligcdr.py ztlig2.467.txt --liid 14029 --unique -o /tmp/out

# 3. 统计分布
python3 extract_ligcdr.py A1-ztlig/ --liid 14029 --stats
```

**注意**: `.gz` 假文件会导致 gzip.open() 崩溃，指定 `.txt` 文件或建软链接目录规避。

### 分析维度

| 维度 | 方法 | 发现参考 |
|------|------|---------|
| EventDetail 序列 | 按CIN分组统计 | 典型4事件: 10→11→13→14 |
| MSISDN 聚合 | 国际/本地/国际前缀合并 | 同一用户3种格式 |
| 站点分布 | CIN前缀区分PSD/ATB | A1双站漫游常见 |
| 跨LIID关联 | 同一号码在CallingNum/CalledNum | 号码可同时是目标和对方 |
| 非JSON行 | 自动捕获调试/SIP日志 | 每JSON平均10~20行 |

### 典型结果速查

- LIID 14029: 5029去重, 1168CIN, 26天跨度, 249123634828
- MSISDN 120120415: 56条, 5LIID, 36条作为目标, 20条作为对方
- 详细模式文档: `references/ztlig-ligcdr-analysis-patterns.md`

## 快速诊断命令集

```bash
# HDFS健康
hdfs dfsadmin -report | grep -E "Blocks|Missing|Corrupt|Under replicated"

# 系统进程
ps -ef | grep -E "gremlin|kafka|zk|janus|lig|sicms" | grep -v grep

# 磁盘
df -h && echo "---" && du -sh /data01/*

# 主机名解析
hostname && cat /etc/hosts | grep $(hostname)

# ZTLIG抓包
tcpdump -i any -s0 port 19002 -w /tmp/ztlig_x2.pcap

# 数据老化配置检查
psql -U daedb -d bigdata -c "select table_name, keep_time from base_addpart_config;"
```
