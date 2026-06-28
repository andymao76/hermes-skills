---
name: hw-li
description: 华为合法监听(HW LI) — CS/PS/IMS X1/X2/X3接口、SVC VoLTE ETSI监听、ZTLIG LIG系统运维。覆盖华为CS(ISUP/M3UA/SIP-I)、IMS(SIP/VoLTE)、SVC融合核心网的合法监听全栈，以及多厂商(ZTE/NSN/ERIC/UTIMACO/G2K/ZEEL)对接配置。
category: telecom
tags: [华为, LI, 合法监听, CS, PS, IMS, SVC, VoLTE, ETSI, X1, X2, X3, ZTLIG, BER, ASN1, ztlig.cfg, 多厂商, 工勘, Ericsson, SOAP, ASN.1]
triggers:
  - user mentions: 华为监听, hw li, 合法监听, X1/X2/X3接口, ZTLIG, ztlig1/2/3, SSF, RVF, IRI报告, HI2, lawful interception, SVC监听, VoLTE监听, 爱立信监听
  - user mentions: ztlig.cfg, ztlig配置, ztlig_target, 设控, 巡检, 语音还原, TMC工勘
  - user mentions: HI2标准, ETSI标准, 101671, 102232, ASN文件, BER解码
  - user mentions: SOAP, WSDL, XSD, createWarrant, Altova XMLSpy, 爱立信SOAP
---

# HW LI — 合法监听全栈

## 概述
合法监听（Lawful Interception）涵盖华为 CS（传统电路域/M3UA/ISUP）、PS（分组域）、IMS/SVC（融合话音核心网）三种场景的 X1/X2/X3 接口对接，以及 ZTLIG LIG（合法监听网关）系统的完整运维。

同时覆盖多厂商（ZTE/NSN/Ericsson/Utimaco/Group2K/Zeel）的 X1 接口对接配置。

## 知识笔记
所有详细资料存储在 `知识/telecom/lawful_interception/` 目录下，共 7 篇笔记：

| 笔记 | 定位 | 涉及接口 |
|------|------|---------|
| 华为SVC_VoLTE_ETSI监听方案.md | IMS/SVC 方案原理、ICID、port negotiation | X2/X3 IMS |
| 华为SVC_IMS_X2报告抓包示例.md | IMS X2 接口13步VoLTE呼叫完整解码 | X2 IMS |
| 华为CS_X接口说明与ZTLIG部署实战.md | CS X1+X2+X3 全接口 + BER编码 + 实战日志 | X1/X2/X3 CS |
| ZTLIG运维手册.md | ZTLIG 系统完整运维(23章+附录、~150项配置、5厂商特有) | 全接口 |
| TMC系统工勘指导.md | LI 系统开局网元信息调查模板(2G~5G/VoLTE/VoNR) | 全接口 |
| 爱立信1口对接调试文档.md | Ericsson LI-IMS SOAP(WSDL+XSD+properties) + HI1结构 + IRI类型 | X1 |
| hw-vs-zte-cs-x1-comparison.md | HW vs ZTE CS X1 接口参数逐项对比 | X1 |
| HI2和标准.md | HI2定义、ETSI标准体系、域适配、文件命名规范 | 标准参考 |
| ZTE_CS_LI_HI1_HI2_HI3_三接口规范.md | ZTE CS 三接口详解(HI1 CLI命令+HI2 ASN.1+HI3 ISDN CC) | HI1/HI2/HI3 CS |
| Utimaco_LIMS_RAI_v16.1_协议规范.md | Utimaco LIMS RAI v16.1 远程管理二进制协议(RAI-SP/RAI-CL) | RAI |
| 5g-li-standards-evolution.md | 5G LI标准体系演进(3GPP SA3-LI + ETSI TC-LI + X1/X2/X3) | 标准参考 |

### 厂商对比参考
| 文件 | 说明 |
|------|------|
| `references/hw-vs-zte-cs-x1-comparison.md` | CS X1 接口对比: 华为 vs 中兴 (参数/配置/命令/排障) |
| `references/hw-ps-packet-decode-example.md` | HW PS X2/IRI BER报文解码示例(IMSI/MSISDN/IMEI TBCD解码) |

### ASN.1 规范文件（位于 `/home/andymao/LI/asn/`）
| 文件 | 来源标准 | 说明 |
|------|---------|------|
| HI2Operations,ver18.asn (1035行) | ETSI TS 101 671 v18 | HI2核心操作，IRI-Parameters/IRIsContent/CommunicationIdentifier |
| UmtsCS-HI2Operations.asn (255行) | 3GPP TS 33.108 R17 | CS域扩展，Cs-Event (1~13) |
| LI-PS-PDU,ver39.asn (762行) | ETSI TS 102 232 v39 | PS域PDU，含IPAccess/Email/IPMultimedia子模块 |
| hw_5gc_x2.asn (1197行) @ `/home/andymao/LI/software/000000app_v1/asnfile/` | 华为自定义 HWIriReport | **5GC X2 扁平化结构**，含 SUPI/SUCI/PEI/GPSI/GUTI 5G标识、5GC IRIEvent (50~61) |
| zte_epc.asn (643行) @ `/home/andymao/LI/software/asn/asnfile/` | EpsHI2Operations r10 ver-3 | ZTE EPC X2 字段定义，含 visitedNetworkId 等扩展 |

### 实测配置样本
| 文件 | 说明 |
|------|------|
| `references/hw-vs-zte-cs-x1-comparison.md` | 华为 vs 中兴 CS X1 接口详细对比 |
| `references/ztlig-cfg-samples-readme.md` | 实战 ztlig.cfg 样本说明 (MTN/SU/ZAIN ~200K) |
| `references/hw-5gc-field-structure.md` | 华为 5GC X2 HWIriReport 字段结构 vs ETSI 标准对比 |
| `references/ztlig-ssf-oms-ats-csc-analysis.md` | SSF实例与OMU-ATS-CSC信令关系 + VoWiFi架构分析 (含ATS Sh接口/PANI位置/Calling Flow) |

### HW LI 知识库目录结构

HW LI 文档已按产品线归类，位于 `~/knowledge/li/HW/` 下：

| 子目录 | 内容 |
|:-------|:-----|
| `SBC/` | SE2900 SBC ETSI LI 测试用例（1652个 .tcl）、ETSI 监听搭建、LICI 特通监听 |
| `IMS-VoLTE/` | VoLTE/IMS LI、X2 抓包示例、VoWiFi 架构图 |
| `CS-Core/` | MSC/MSS/SoftX3000 CS 核心网 LI 协议、维护手册、NGN X1X2 |
| `5GC-EPC/` | 5GC/EPC/GGSN LI 协议标准、X2 Tag 映射表、信令分析 |
| `HSS/` | HSS 北向接口原子命令 |
| `ME60/` | ME60 路由器日志参考 |
| `LI-Protocol/` | LI 通用协议（ReturnCode/ASN1/OID/技术文档索引）|
| `ZTLIG-Integration/` | 华为与 ZTLIG 对接、SSF 分析经验 |
| `Tools/` | Wireshark/ASN1 解码/CGP 维护工具 |
| `Archives/` | 原始 7z 压缩包备份 |

详细索引见 `SBC/HW-SE2900-SBC-ETSI-LI-testcases-index.md`

### VoWiFi 架构参考
| 文件 | 说明 |
|------|------|
| `~/knowledge/li/HW/IMS-VoLTE/HW-VOWIFI-clean.svg` | A1 Sudani VoWiFi 呼叫信令流 SVG 图（MO ATS获取位置 → MT ATS删除位置）|
| `~/knowledge/li/HW/ZTLIG-Integration/hw-li-ztlig-ssf-analysis-experience.md` | 完整经验文档含ZTLIG双通道捕获对比 |

### 配置分析方法论
| 文件 | 说明 |
|------|------|
| `references/ztlig-ssf-oms-ats-csc-analysis.md` | SSF实例数差异追踪分析 + A/B站配置对比方法论 |

### Ericsson 资源（位于 `/home/andymao/LI/ETSI/E/`）
| 文件 | 说明 |
|------|------|
| 爱立信1口对接调试文档.md | SOAP对接文档 |
| 爱立信-HI1结构一览及其构造-详细.md | HI1请求结构+字段详解 |
| 2-3-爱立信-请求响应对.py | 完整SOAP XML模板(login/createWarrant/getWarrantList/modifyWarrant/deleteWarrant) |
| 爱立信LI-IRI-LUD.xmind | IRI类型脑图(IRI-BEGIN/CONTINUE/END/REPORT) |

## 核心概念

### 接口说明
| 接口 | 功能 | 传输方式 |
|------|------|---------|
| X1 | 命令通道（设控/停控） | TCP/IP / SOAP(爱立信) |
| X2 | 信令面（IRI 报告/BER编码） | TCP/UDP/FTP/SFTP |
| X3 | 媒体面（RTP 语音/文件） | TCP/UDP/FTP |

> 华为 vs 中兴 CS X1 接口详细对比：`references/hw-vs-zte-cs-x1-comparison.md`

### ZTLIG 进程映射
| 进程 | 接口 | 功能 | 配置块 |
|------|------|------|--------|
| ztlig1 | X1 | 设控管理 | ZTLIG1(x) + NE(x) |
| ztlig2 | X2 | 信令解析/CDR | ZTLIG2(x) |
| ztlig3 | EPC | DPDK→SICMS | ZTLIG3(x) |
| ssf | SIP-I | SIP 会话管理 | SSF(x) |
| rvf | RTP | 语音还原 | RVF(x) |

### 三层 ID 映射（核心概念）
```
物理网元 (hi2_neid) — 网元实际ID
     ↓ 映射
tneid (物理网元编号) — 系统自定义
     ↓
vneid (虚拟网元编号) — 系统自定义，映射hi2_neid
     ↓
后端界面下发设控时使用 vneid
```

### 呼叫模式
| 模式 | X2 关联 | X3 实现 |
|------|---------|---------|
| CS (M3UA/ISUP) | ISUP 消息 | 主/被叫子地址关联 |
| SIP-I | Application消息(Access Transport 携带 LIID+CIN) | 四元组(IP+Port)关联 |
| IMS-base (SBC) | LIID+imsChargingID | RTP复制, TX/RX分离 |

### 关联逻辑
- **基本关联**: LIID + CIN
- **TX/RX分离**: LIID + CIN + Direction
- **Option A 多方**: 每次通话建2条CC链接，LIID+CIN
- **SIP-I 四元组**: srcIP/srcPort/dstIP/dstPort (SDP 200 OK)

### HI2 标准体系
| 标准 | 说明 |
|------|------|
| ETSI TS 101 671 | HI2 核心接口，CS/IMS IRI 格式 |
| ETSI TS 102 232-x | IP-based 监听，IMS/NGN/VoIP (x=1通用, -5 IMS, -6) |
| 3GPP TS 33.108 | 3G/UMTS 监听接口 |
| ETSI TR 102 503 | HI 接口标准导航文档 |

### 命名方式（S/FTP 模式）
- **Method A**: `<LIID>_<seq>.<ext>`（以目标为中心）
- **Method B**: `ABXYyymmddhhmmsseeeet`（以时间戳为中心，固定长度）
  - ext/t: 1=IRI, 2=CC-MO, 4=CC-MT, 6=CC-Both, 8=国家扩展

## 关键参数
- **LIID**: 拦截目标唯一 ID, 1~65535, ASCII 传输
- **CIN**: Call Identification Number, X2/X3关联标识
- **ICID**: IMS Charging Identifier, 会话内唯一
- **BER编码**: ASN.1 BER, TLV结构, 定长≥128用0x81前缀
- **networkType**: 1-CS, 2-PS, 3-EPC, 4-IMS, 5-5GC, 11~18=细粒度
- **ztlig_target字段**: 见 `references/ztlig-target-fields.md`
- **3口TLV标签**: IMSI(SUPI)=T1, MSISDN(GPSI)=T2, IMEI(PEI)=T3, 8B十进制BCD
- **ISUP信令**: IAM→ACM→ANM→REL→RLC

## ztlig.cfg 配置构架(~150项)
| 配置块 | 项数 | 说明 |
|--------|------|------|
| NE-COM 通用 | 18 | 物理网元(vendor/version/x1/x2/x3) |
| NE-HW | 5 | 华为特有(neid/alias/need_time/des_key/encrypt_mode) |
| NE-ZTE | 8 | 中兴特有(phneid/module_ip/batch/sp_fg/neno_fg等) |
| NE-NSN | 10 | 诺西特有(alive_interval/fdelay/fsize/aauser等) |
| NE-ERIC | 5 | 爱立信特有(lemfid/csmcnb/psmcnb/leaname) |
| NE-UTIMACO | 7 | Utimaco特有(mc_iri/icd/mc_data/mc_mm/mc_voice) |
| NE-GROUP2K | 5 | Group2K特有(SenderId/ReceiverId/DeliveryProfile等) |
| NE-ZEEL | 1 | Zeel特有(agency_num) |
| VNE-COM | 10 | 虚拟网元(vneid/hi2_neid/speechtype/incptType) |
| VNE-ZTE | 4 | 中兴VNE特有(vmscindex/alias/operator/password) |
| VNE-ERIC | 5 | 爱立信VNE特有(ericssonid/interceptgroupid等) |
| LEA | 22 | 监听中心(Kafka/Redis/SFTP/码流分享) |
| ZTLIG1 | 6 | 设控进程(x1/db/syn_night) |
| ZTLIG2 | 12 | 信令处理(tneid/networkType/超时/operid) |
| ZTLIG3 | 13 | EPC转接(SICMS DPDK全参数) |
| SSF | 10 | SIP-I会话(interfaceType 5种模式) |
| RVF | 12 | RTP语音还原(clientnum/sdpport/ssfSeq/openvox) |
| LICENSE | 17 | 各厂商接口开关 |
| GLOBAL | 5 | FTP/多TMC/Kafka监控 |

### 配置分析：ZTLIG 多站对比方法

当分析多个站点的 ZTLIG 配置（如 A/B 双站）时，使用以下步骤：

### 步骤
1. **进程实例数对比** — 先用 `grep -c '^\\[SSF_\\|^\\[RVF_\\|^\\[ZTLIG2_\\|^\\[NE_'` 比较各模块实例数，定位差异
2. **IP 地址归类** — 将差异分为 LIG 内部 IP、X 接口 IP、Kafka/Redis/DB IP 三组，验证是否是镜像配置
3. **非 IP 差异深追** — 过滤掉 IP 替换差异后检查剩余的结构差异（`diff | grep -vE '\\.ip|port|redis|kafka'`）
4. **SSF 差异追根** — SSF 实例数差异说明某路 SIP 信令出口在站点间有拓扑差异，追踪对应的 ZTLIG2 → NE → 网络架构
5. **结合网络拓扑验证** — 差异原因往往不是配置错误，而是站点间网络架构不同

### 典型发现模式
- **SSF 实例数 ≠ NE 数**，等于需要独立会话管理的 SIP 信令出口数
- SSF 实例数多 = 多一路需要独立会话管理的 SIP 信令出口
- 多出的 SSF → 对应 CSCF+ATS 复用 IP 的 IMS 融合网元 → 往往与 VoWiFi 信令路径相关

### 华为 SVC 设备部署模式

华为 **SVC** (Service Control) 设备集成了 OMU + ATS + CSCF 等功能，复用同一物理 IP。同一设备在不同运营商的部署模式不同：

| 场景 | 运营商 | 启用功能 | SSF 需求 |
|------|--------|----------|----------|
| VoWiFi 全量信令 | **SU** (苏丹) | OMU + ATS + CSCF | **需要**额外 SSF 处理 VoWiFi SIP 信令出口 |
| 仅补充业务 CDR | **ZAIN、MTN** | **仅 OMU** | 不需（无 SIP 信令出口） |

**部署原则：**
- 配了 OMU（华为 SVC）不一定需要 ATS-CSC。带 SIP 信令出口的才需要额外 SSF
- SSF 判断标准：OMU-ATS-CSC 是否有 SIP 信令出口（即是否承载 VoWiFi/IMS 会话）

### 参考文件
- `references/ztlig-ssf-oms-ats-csc-analysis.md`
- `~/knowledge/li/HW/hw-li-ztlig-ssf-analysis-experience.md`

### 日常巡检（6项）
| 进程 | 检查命令 | 正常指标 |
|------|---------|---------|
| ztlig1 | `show ztlig1 {id} mainframe stat` | curTarNum正常 |
| ztlig2 | `show ztlig2 {id} kafka stat` (×2) | sendFailNum=0, sendSuccNum增长 |
| ztlig3 | `show ztlig3 {id} nic stat` (×2) | oerrors=0, obytes变动 |
| ssf | `show ssf {id} stat` (×2) | RecvNum增长 |
| rvf | `show rvf {id} stat` (×2) | RecvTotalMsgLen增长 |
| OpenVox | `show rvf 1400 kafka stat` | sendsucc正常 |

### 常见错误
| # | 错误 | 原因 | 排查 |
|---|------|------|------|
| 1 | RC 9 = 无效 NEID | X1 NEID 配置错误 | 检查 `ztlig.cfg` 中 NE 配置 |
| 2 | alarm-id 504, 认证失败 | X1 用户名/密码/NEID 错误 | 检查 LIG 认证配置 |
| 3 | X2 LeaIdx invalid | 设控LEAID与实际不匹配 | 检查 LEA 配置 |
| 4 | X2 the ne is unlawful | tneid未添加到2口配置 | `show ztlig2` 确认 |
| 5 | X2 get actneID fail | vneid不存在 | 检查 VNE 配置 |
| 6 | ZTLIG3 vneid not support | hi2_neid未配置 | 确认 VNE 映射 |
| 7 | **ReturnCode 28 = invalid liid** | LIID 无效 | 见下方详细排查 |
| 8 | 语音无文件 | SSF/RVF 配置问题 | 检查 voiceCtrlType、端口、sdpport |

#### ReturnCode 28 (invalid liid) 详细排查
**含义**: NE 返回 ReturnCode=28，表示 X1SetTarget/X1ModifyTarget 消息中的 LIID 无效。
**根因可能性**:
1. **LIID 格式违规** — LIID 为 1~25 字节 ASCII 串。若 X3 使用 ISUP 子地址关联（BCD 编码），LIID **只能由 0~9 数字组成**，含字母/特殊字符则报 28
2. **LIID 超范围** — 合法范围 1~65535，0 或 >65535 的值直接拒绝
3. **LIID 超长** — 超过 25 字节被截断或拒绝
4. **VNE/TNE 未配置** — 即使 LIID 正确，若对应 VNEID 在 NE 侧不存在也报无效
5. **LIID 重复** — 同一 NE 上不同目标使用了相同 LIID

**排查步骤**:
```bash
# 1. 确认 LIID 值（纯数字字符串，无空格/不可见字符）
echo -n "8070" | od -A x -t x1z    # 应显示纯 ASCII 数字

# 2. 检查 ztlig1 日志中该 LIID 的设控过程
grep "liid.*8070" /path/to/ztlig1.log

# 3. 确认 VNE 配置正常
show ztlig <id> mainframe stat      # 检查目标数量
show ztlig <id> target table        # 查看目标列表

# 4. 更换 LIID 重试以排除 LIID 值本身问题
```

**注意**: 设控刚删除后立即重用相同 LIID，部分华为网元需要同步时间窗口，建议换一个新 LIID 值。

### HW CS 实时位置查询（X1 SubscriberStat）

**适用场景**: 查询指定 MSISDN 号码在 HW CS 网元（MSC/MSCe）上的实时位置（基站）。
**不适用 PS 域**: SGSN/GGSN/EPC 网元类型不同，不走此流程。

#### 整体流程

```
Web UI → Kafka TMC_TARGET_INFO topic → ztlig1 → HW MSC (X1 SubscriberStat)
                                                         ↓
Web UI ← Kafka TARGET_INFO_STATUS topic ← ztlig1 ← HW MSC 返回 userState + location
```

- Web 通过 Kafka 发送查询到 `TMC_TARGET_INFO`（与设控 target 同一 topic）
- ztlig1 通过 X1 向 HW MSC 发送 subscriber stat 查询
- HW MSC 返回 userState + location（基站信息）
- ztlig1 推送结果到 `TARGET_INFO_STATUS`（与网元受控返回的状态 topic 一致）
- Web 10s 超时，超时算查询失败

#### ztsh CLI 查询

```bash
# 语法
show ztlig1 {id} hwmsc {leaId} {vneId} subscriber stat MSISDN {号码}

# 示例
LIG02# show ztlig1 300 hwmsc 2 10 subscriber stat MSISDN 249914560717
send x1 subscriber stat message to ne:10 success

# 日志输出
[ztlig-1_hwne][hwmsc_x1_subscriberStatRsp]:
  hua wei msc subscriber Stat response,
  num 249914560717, userstate outOfService,
  location 6340155F252A0, tneID=10
```

**前置条件**：
```
debug ztlig1 300 web on
write ztlig1 300 logfile on
```
不需要 db debug 或 ztlig2 owlsprint。

#### Kafka 消息格式

**Web 发起查询**：
```json
{"account":"249914560717","editFlag":0,"isDel":3,"len":12,
 "officesIds":"19,20,15,16,8,9,7,10,14,11,2,1",
 "protocolType":"MSISDN","restoreType":"TMC"}
```

**LIG 返回**：
```json
{"account":"249914560717","officesIds":"...","ret":"3,3,...,0,1,1,3,3",
 "mapId":0,"isDel":3,"editFlag":0,"detail":",,,,,,,,,,,",
 "userState":"outOfService","locationType":6,"location":"6340155F252A0"}
```

#### 返回字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `userState` | 用户状态 | `outOfService`/`powerOff`/`busy`/`reachable` |
| `locationType` | 位置类型 | `4`=注册位置, `6` |
| `location` | 位置（MCC MNC CELL_ID 十六进制拼接） | `6340155F252A0` = MCC=634 + MNC=015 + CELL_ID=5F252A0 |

**location 解码示例**: `6340155F252A0` → MCC=634(Sudan) + MNC=015 + CELL_ID=5F252A0

#### 排障

| rc | 含义 |
|:--:|------|
| 0 | 成功，有位置信息 |
| 11 | 其他原因（号码不存在/网元无响应等） |

**失败示例**:
```
[ERROR][hwmsc_x1_subscriberStatRsp]: ... rc=11
```
→ 检查 leaId/vneId 匹配，更换 vneId 重试

#### 注意事项
1. **仅 HW CS 适用** — PS 域不走此流程
2. **非目标也可查询** — 不需要设控
3. **不入库** — 仅 Web 回显
4. **10s 超时**
5. **不占 license** — 不计入 max_target

详细参考 `sinovatio-ztlig` skill 第十一章。

### Wireshark 过滤
- LIID: `data.data contains <ASCII_HEX>` (如 25115→32:35:31:31:35)
- CIN: `data.data contains <ASCII_HEX>` (8字节)
- 事件标签: `0x9F21` 位于码流末尾
- CIN 过滤: `frame contains "CIN值"`

### PSM 捕包（版本 >= T3B23）
```bash
sh psm_uninstall.sh  # 配置 ztlig.psm_pcap_dir
pkill ssf rvf ztlig3 ztlig2 ztlig1 cmf
./cmf -s ztlig -d y  # 重启cmf
sh psm_install.sh     # 安装psm
write psm 10 capfile on 200  # 开启捕包
```

## 培训要点
- **语音通知文件**: 实时离线模式可不配 rvf_noticepath（后续优化）
- **语音文件名**: `Liid.cin.operatorid.neid.direction`（operid/neid优先用报告值）
- **多TMC模式**: `ztlig.dbLeaID > 0` 开启，extra fields: tmcid + mcliid
- **syn_night bit位**: bit0=hw, bit1=zte, bit2=eric, bit3=nsn, bit4=utimaco
- **Ericsson X1**: SOAP/WebService(WSDL+XSD+properties)，非TCP直连
- **Ericsson createWarrant**: warrantID=-1（系统分配）, 含requestHeader+warrantItem+dtlWarrants
- **Ericsson IRI类型**: BEGIN(呼叫开始)/CONTINUE(通信中)/END(结束)/REPORT(非通信事件)
- **3口TLV标签**: IMSI=Type1, MSISDN=Type2, IMEI=Type3, 8字节十进制BCD
- **LIID+CallID=唯一会话**: LIID 与 SIP Call-ID（或 ISUP CIC）组合确定唯一会话
- **反序BCD编码**: 华为在 SIP-I ISUP Subaddress 中使用反序BCD（swap nibbles）编码 LIID。如 LIID=84335 → BCD normal `84 33 5F` → 反序BCD `48 33 F5`

## HW LI 方案选型速查

| 场景 | 主推方案 | 核心网元 |
|------|:--------:|----------|
| VOBB（小容量AGCF） | 方案二：分布式监听IP复制 | ATS + SBC + MGCF |
| VOBB（大容量AGCF） | 方案一：集中监听IP复制 | ATS + CSC + CCTF + MRP |
| VoLTE(RCS) | 方案二：分布式监听IP复制 | ATS + SBC + MGCF |
| VOBB+VoLTE融合(FMC) | 方案三：FMC监听IP复制 | ATS + CSC + CCTF + MRP + SBC |
| 非华为SBC/MGCF | 方案一：集中监听 | ATS + CSC + CCTF + MRP |

详细选型矩阵见 `~/knowledge/li/HW/hw-li-solution-selection-guide.md`

## ISBC 特通监听

ISBC（Integrated Service Border Controller）特通监听规范测试用例：
`knowledge/li/HW/SBC/CR-02026143-SE2900 V300R001C20-SE2900 ISBC支持特通规范/`

共 36 个 `.tcl` 用例（华为 SPIDER 框架），覆盖 ISBC 本域/外域监听、TEL格式目标、协议互通、SIP/SIPI互转、呼叫保持、IMS中继呼叫等场景。

**核心流程：** INVITE → 隧道建立请求 → 上报被控目标呼叫事件 → X3隧道建立 → 媒体协商 → BYE结束

详细测试用例索引见 `HW-SE2900-SBC-ETSI-LI-testcases-index.md`

## 已知重叠技能
- `huawei-hi2`: 更窄的 HI2 接口专项，本 skill 覆盖 HW LI 全栈（含SVC/IMS/ZTLIG及多厂商）
- `ericsson-li`: Ericsson LI X1 SOAP/External API 专项，含完整的 SessionService/WarrantService CRUD 和 SoapUI 测试流程
