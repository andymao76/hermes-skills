---
name: sinovatio-ztlig
description: 中新赛克(Sinovatio) ZTLIG 合法监听网关系统 — 进程架构、ztlig.cfg 全量配置(NE/VNE/GLOBAL/LICENSE)、巡检排障、升级部署、补丁分析。注意与 ZTE LI(IIF/中兴合法监听系统)严格区分。
category: telecom
---

# ZTLIG 合法监听网关系统 (Sinovatio/中新赛克)

> **厂商**: 南京中新赛克软件有限责任公司 (Sinovatio)
> **与 ZTE LI (IIF) 严格区分**: ZTLIG 是合法监听**网关**，对接多厂商网元；ZTE LI (IIF) 是中兴**网元内置**的合法监听功能（ZXUN LIG V4 / LIS）。

ZTLIG 是标准合法监听网关系统，对接华为/中兴/爱立信/NSN/UTIMACO 等厂商网元，完成 X1/X2/X3 接口的设控管理、信令处理、媒体还原。

当用户提及 ZTLIG、ztlig1、ztlig2、ztlig3、ssf、rvf、LIG 部署、合法监听网关、LI 网关运维时触发。

---

## 一、与其他 LI 系统的关系

| 系统 | 类型 | 厂商 | 功能 |
|------|------|:----:|------|
| **ZTLIG** | **网关** (本 skill) | **Sinovatio/中新赛克** | 统一网关，对接多厂商 NE 的 X1/X2/X3 |
| HW LI | 网元内置 | 华为 | 华为 MSC/IMS/EPC 的 LI 功能 (SVC/HWLI) |
| ZTE LIS (IIF) | 网元内置 | 中兴 | ZTE MSC/MGW 的 LI 功能 (ZXUN LIG V4) |
| Ericsson LI | 网元内置 | 爱立信 | Ericsson MSS SGSN 的 LI (COD/LIMS) |
| NSN LI | 网元内置 | 诺基亚 | NSN MSC 的 LI |
| Utimaco LIMS | 独立系统 | Utimaco | 第三方 LI 管理系统 (RAI 协议) |
| Mavenir | 网元内置 | Mavenir | Mavenir IMS 的 LI (XML/SOAP) |

## 二、系统架构

### 进程说明

| 进程 | 接口 | 功能 |
|------|------|------|
| **cmf** | 内部 | 配置管理框架 |
| **ztlig1** | HI1 / X1 | 设控管理 — Kafka 设控消息 → 网元指令 → 响应推送 |
| **ztlig2** | HI1 / X2 | 信令面 — NE 的 IRI 报告（TLV 编码）→ JSON CDR → Kafka |
| **ztlig3** | EPC / DPDK | EPC 流量转接 → 剥离头 + 三码/位置 → DPDK → SICMS |
| **ssf** | SIP-I | SIP-I 会话管理：SIP 解析 → 三码/SDP/位置提取 |
| **rvf** | RTP | 媒体面：RTP 流量 → 语音文件 (.0 + .fin) |
| psm | TCP | 抓包管理 (**x86-64**) |
| psm_ass | TCP | 抓包辅助（FFmpeg 解码）(**x86-64**) |

### 数据流
```
cmf（配置中心）→ ztlig1 → NE (X1 设控)
                NE X2 → ztlig2 → JSON CDR → Kafka
                NE SIP-I → ssf → rvf → 语音文件
```

## 三、ztlig.cfg 配置参考

NE-COM: vendor/version、x1_ip/port/user/pwd、x2_transtype/x2_ip、x3_transtype/x3_ip、trace_type
VNE-COM: vne_type/speechtype/incptType/ulicver
GLOBAL: ztlig.x_ftp.usr/pwd / dbLeaID(多TMC) / kafka_operations_topic
LICENSE: 17项(max_target/厂商开关等)

## 四、巡检与排障

关键命令: `show ztlig1 {id} mainframe stat` / `show ztlig2 {id} kafka stat` / `show ztlig3 {id} nic stat`

JSON CDR 字段: LIID/CidNum/OperID/NeidType/Neid/VneID/Vendor/NetworkType/EventDetail(10=呼叫/17=注册)/MSISDN/CallingNum/CalledNum/CcLid/CallDuration/IMSI

## 五、ztlig1 CLI 命令速查（76 条）

ID范围 31001~31804。按厂商分类(cat /home/andymao/lig-patch/A1-LIG/1203-PATCH/ztlig1-cli-commands.md)。

**常用排障组合**:
```
debug ztlig1 300 web on           # Kafka 设控消息追踪
debug ztlig1 300 huawei on        # 华为 NE X1 通信
debug ztlig1 300 db on            # 数据库查询
write ztlig1 300 logfile on       # 日志文件输出
show ztlig1 300 kafka stat        # Kafka 生产统计
syn ztlig1 300 redis              # Redis→MySQL 同步
```

## 六、Kafka 设控消息格式 (TMC_TARGET_INFO)

ZTLIG1 通过 Kafka Topic `TMC_TARGET_INFO` 接收设控/解控/位置查询指令，处理后响应到 `TARGET_INFO_STATUS`。

### 字段表

| 字段 | 类型 | 说明 |
|------|------|------|
| account | String | 拦截目标号码 (MSISDN/ISDN 带国家码) |
| editFlag | int | 操作标志 (4=设控, 0=查询) |
| **isDel** | **int** | **操作类型: 0=设控, 2=解控, 3=实时位置查询** |
| targetId | int | 目标 ID (= LIID) |
| mapId | int | 映射 ID |
| officesIds | String | 网元/LEA ID 列表 (逗号分隔) |
| len | int | 网元个数 |
| protocol | String | 号码协议类型: ISDN / MSISDN / IMEI |
| protocolType | String | 同 protocol |
| restoreType | String | 还原类型 (TMC) |
| fD | String | 特征数据 |
| iT | String | Intercept Type |
| hI2A/hI2P/hI2PORT | String | HI2 接口地址/端口 |
| hI3A | String | HI3 接口地址 |

### 典型操作示例

**设控 (添加拦截)** — `isDel:0`
```json
{"account":"249914959206","editFlag":4,"isDel":0,"targetId":8072,
 "officesIds":"24","protocol":"ISDN","restoreType":"TMC","mapId":18478}
```

**解控 (删除拦截)** — `isDel:2`
```json
{"account":"249914959206","editFlag":4,"isDel":2,"targetId":8072,
 "officesIds":"24","protocol":"ISDN","restoreType":"TMC","mapId":18478}
```

**实时位置查询 (非设控)** — `isDel:3` + `editFlag:0`
```json
{"account":"249914560717","editFlag":0,"isDel":3,"officesIds":"19,20,15,16",
 "protocolType":"MSISDN","restoreType":"TMC"}
```

### 操作排查

下发 Kafka 消息后，ZTLIG1 处理链:
```
kafka_msg_consume → ztlig_license_add (License校验)
→ ztlig_db_add (DB插入)
→ hwmsc_x1_addTargetRsp/encode_kafka_rsp (X1下发+响应)
```

```bash
# 追踪设控流程
debug ztlig1 300 web on
debug ztlig1 300 db on
write ztlig1 300 logfile on

# 检查 Kafka 生产统计
show ztlig1 300 kafka stat
```

> 详细 Kafka 运维 (Consumer Group 诊断/偏移量重置/Manger 启动/生产消费) 见 `kafka-ops-expert` skill 和参考文件 `references/a1-project-kafka.md`。

## 七、HW CS 实时位置查询 (SubscriberStat)

仅适用 HW CS 网元(MSC/MSCe)。流程: Web→Kafka(TMC_TARGET_INFO)→ztlig1→HW MSC X1→返回(TARGET_INFO_STATUS)。

CLI: `show ztlig1 {id} hwmsc {lea} {vne} subscriber stat MSISDN {num}`

返回格式: userState(outOfService/powerOff/busy/reachable), location(MCC+MNC+CELL_ID_HEX)

## 八、已知问题

Wlan-ue-local-ip 遗漏 — SSF 解析 SIP PANI 头时未提取 WiFi 公网 IP 到 Kafka CDR。

## 九、补丁分析工作流（核心）

对 ZTLIG 二进制补丁进行逆向分析的方法论。核心原则：**agc(调用图) > pdc(伪C) > afl|wc -l(函数计数)**。

### 6 步分析法
1. 目录摸底 → 2. file 架构识别 → 3. BuildID 追踪 → 4. strings 指纹 → 5. 跨版本 diff → 6. r2 逆向

### r2 程序流分析（7 层级）

| 层级 | 命令 | 能看到的 |
|:----:|:-----|----------|
| 1 | `afl|wc -l` | 函数总数 |
| 2 | `afl~cJSON` | 特定库存在 |
| 3 | `afl~func` (第三列) | **函数体积暴涨=功能增强** |
| 4 | `s func; agc` | **调用图 (核心)** |
| 5 | `s func; agf` | **控制流图** |
| 6 | `s func; pdc` | **伪C源码** |
| 7 | `/ str; axt` | **交叉引用** |

### 实战对照

**libhi3pro.so usrip 修复**: 11-14(59函数) → 12-10(66函数, +6cJSON)。agc揭示: memset→cJSON_CreateObject→...→KafkaProduce。pdc揭示: cJSON_AddItemToObject(root,"UsrIP",...)。不是简单改编码，是消息格式从二进制TLV重构为JSON。

**libwebhi1.so 10-19重构**: decode_kafka_addmsg 260B→2,240B(8.6倍)。新增modmsg(2,140B)。新增5个Redis函数。agc显示参数校验全部展开。

### 三级联动分析

结合 ETSI-ASN1-Assistant(协议层) + r2(代码层) + 完整tmp_so/(系统层):

| 层次 | 工具 | 作用 |
|:----:|:----:|------|
| 协议层 | ETSI-ASN1-Assistant | 解码HI2/X2 PCAP, 识别BER字段 |
| 代码层 | r2(agc/agf/pdc) | 反编译decoder.so和主程序 |
| 系统层 | 完整tmp_so/(121个) | 交叉引用厂商插件和基础设施 |

详见 references/ztlig-3-level-analysis.md。

## 十、参考资料
- `references/ztlig-binary-structure-analysis.md` — 二进制结构分析 + 发行包分析
- `references/ztlig-debug-flow.md` — 调试流程与问题排查
- `references/ztlig-patch-analysis-sop.md` — 完整补丁分析 SOP（6步法 + r2命令 + 批量扫描）
- `references/ztlig-patch-analysis-case.md` — A1 lig-patch 完整分析案例（18个补丁）
- `references/ztlig-3-level-analysis.md` — ETSI-ASN1-Assistant + r2 + 完整包三级联动
- `references/ztlig-cdr-pcap-cross-validation.md` — PCAP↔CDR 交叉验证
- `references/ztlig-sip-location-mapping.md` — SIP PANI 位置字段映射
