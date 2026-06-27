---
name: huawei-hi2
description: 华为 HI2 合法监听接口全栈 — CS X1/X2/X3 协议、IMS/SIP-I 监听方案、BER 编解码、CDR 字段定义、ASN.1 号码/位置编码、ZTLIG 部署排障
category: telecom
---

# 华为 HI2 合法监听接口

华为合法监听（Lawful Interception）接口全栈技能。涵盖 CS X1/X2/X3 协议、IMS 场景下的 SIP-I/IMSBASE 监听、ASN.1 BER 编码、CDR 字段解码、部署调试等。

---

## 一、触发条件

当用户提及以下关键词时触发：
- 华为 LI、LIG、HI2、HI3、X1/X2/X3
- hw_imsbase、SIP-I、SVC VoLTE 监听
- ZTLIG 华为侧对接、设控、LIID、CIN
- BER 编解码、AddressString、TBCD-STRING、CGI/LAI/TAI/ECGI
- 乌干达/海外 ZTLIG 部署、Kafka topic 设控

## 二、X1 管理接口

### 传输特征
- **协议**：TCP/IP 双向通道（网元=server, LIG=client）
- **帧头**：14字节（新）/8字节（NGN老版），前导 `0xAA`
- **并发**：不超过 5 个连接
- **超时**：5 秒无响应视为失败
- **会话维护**：X1Handshake 永久保活
- **认证**：华为用户名/密码无限制；Utimaco 有限制

### LIID
| 属性 | 值 |
|------|-----|
| 范围 | 1~65535（ASCII，外场可超） |
| 分配 | MC 分配或 LIG 生成 |
| 子地址模式 | 仅 0~9 数字 |
| X2/X3 映射 | 等于 lawfulInterceptionIdentifier |

### X1SetTarget 主要参数
| 参数 | 说明 |
|------|------|
| TraceMode | 跟踪模式 |
| OutputNum | X3 通道地址 |
| SpeechOutputMode | 缺省 combinedOptionB(0)=Combined Rx and Tx B（ACCESS NUMBER） |
| NEID | 错误时返回 RC 9 = 无效 NEID |

### 设控号码格式
| 网元类型 | 号码格式 | 原因 |
|---------|---------|------|
| GMSC (ISDN) | **ISDN** | 它国号码在本网不可能分析为 MSISDN |
| 其他 MSC | **MSISDN** | — |

ASN.1 PER Tag：
- TAG_HWMSCE_SETTGT_NUMBER = 0xA3
- TAG_HWMSCE_NUMBER_ISDN = 0x84

### X1Handshake / X1SetTarget 排障
- NEID 错误 → RC 9 → 检查 X1 用户名/密码/NEID
- 认证失败 → alarm-id=504 (LIG Authentication Failed)
- X1 通道中断 → alarm-id=512 (X1 channel Communication Interrupted)
- 过滤 X2 端口排查：NE 向 X2 端口吐错信息

## 三、X2 信令接口

### BER 编码规则

```
T  L  T  L  V ....    [00 00]
```

- **定长编码**：长度 ≤ 127 用 1 字节；> 127 用 `0x81 + len`（如 255 → 0x81 0xFF）
- **嵌套结构**：一份 HI2 报告是多个 TLV 互相嵌套
- **HW 头**：`aa 05 01 00 01 a5 01 a5 04 ff ff ff ff ff`

### HW 标准 2 口报告 HEX 示例
```
aa 05 01 00 01 a5 01 a5 04 ff ff ff ff ff    # HW 头
a4 82 01 a1                                     # IRI-End-Report
80 06 04 00 02 02 01 06                         # csdomainID
97 01 06                                        # iRIversion
81 05 33 31 34 39 30                            # LIID "1490"
a2 1f                                           # communicationIdentifier
     80 08 30 31 39 31 39 34 38 39              # cin "01919489"
     ...
```

### Cs-Event 枚举
```asn1
Cs-Event ::= ENUMERATED {
    call-establishment (1), answer (2), supplementary-Service (3),
    handover (4), release (5), sMS (6), location-update (7),
    subscriber-Controlled-Input (8), called-Subscriber-Access (9),
    serving-System-Report (10), object-Information-Modified-Notification (11),
    power-On (12), power-Off (13), dTMF (14), x3-Channel-State (15),
    object-Deleted-Notification (16), media-Supplementary-Information (17),
    ims-Gen-IRI-Report (18)
}
```

### CDR 字段速查

核心字段（共 35 个，完整定义见 `references/huawei-cs-x2-cdr-definitions.md`）：

| 字段 | 说明 |
|------|------|
| LIID | 设控目标 ID |
| CidNum | CIN（通话关联标识） |
| EventDetail | CS: 10(CALL_SETUP)/11(ANSWER)/12(SUPPLE)/13(RELEASE)/14(ALERT)/15(HANDOVER)/17(CCSETUP)/18(CCCLOSE) |
| NetworkType | 1-CS, 2-PS, 3-EPC, 4-IMS, 5-5GC |
| EventDirection | CALL: 1-主叫, 2-被叫 |
| SsCode | 补充业务码（0x21~0x99 + 补充业务码表） |
| CallingNum / CalledNum | 主/被叫号码（TBCD-STRING 编码，含 0x91 指示字节） |
| Location | CGI/LAI/SAI/RAI/TAI/ECGI 六种格式 |

### 排查命令
```bash
# Wireshark 过滤 CIN
frame contains "95100002"

# ZTLIG 日志过滤
tail -f ztlig2.*.txt | grep EncodeToJson | grep '\"LIID\":\"8070\"'

# tcpdump (X2)
tcpdump -i any host 172.28.3.180 and port 8900 -vvv -nn -s 0 -X
```

## 四、X3 媒体接口

### 信令传输方式
- **TMD（传统）**：基于 ISUP
- **当前主流**：基于 IP 的 M3UA（MTP3 User Adaptation）

### X2/X3 关联

| 模式 | 关联方式 | 说明 |
|------|---------|------|
| 基本关联 | **LIID + CIN** | 通过主叫号码、主/被叫子地址关联 |
| CS (M3UA/SCCP) | ISUP 消息 | 传统的 TDM/M3UA 关联 |
| SIP-I (IP) | **Application 消息** | SIP INVITE → ISUP → Access Transport 携带 LIID+CIN |
| TX/RX 分离 | LIID + CIN + Direction | 确定拦截哪一方通话 |
| 多方通话 | Option A | 每次通话建 2 条 CC 链接（主/被叫），LIID+CIN 关联 |
| 四元组 | srcIP:port → dstIP:port | SIP-I 模式下 200 OK 的 SDP 信息 |

### SIP-I 处理流程
```
NE ──ISUP(LIID+CIN)──→ SSF ──SDP(RVF IP+PORT)──→ RVF ──RTP──→ LIG
```
1. NE 与 SSF 建链（SSF 初始化后不需向网元侧注册 SIP）
2. LIID+CIN 通过 **ISUP 层** 带给 SSF
3. 通过 **SDP 协议** 获取 RVF 的 IP+PORT
4. 发送 RTP 流
5. 对接检查：MGW/SBC 能 PING 通，防火墙端口不阻塞

### 关联参数传递
X3 关联参数可放在主叫号码、被叫子地址、主叫子地址中，通过 ISUP/SIP/PRA 发送给 MC。

## 五、号码编码

### IMSI / MSISDN / CallingPartyNumber / CalledPartyNumber

| 字段 | 指示字节 | 解码方法 |
|------|---------|---------|
| msISDN | 含 **0x91** | 忽略指示字节 |
| callingPartyNumber | MAP-Format，含 **0x91** | 忽略指示字节 |
| calledPartyNumber | MAP-Format，含 **0x91** | 忽略指示字节 |
| e164-Format | 携带 T/L | 解析 T/L 再解析值 |

> **0x91** = bit8=1(no extension) + bits765=001(国际) + bits4321=0001(E.164)

### AddressString (TBCD-STRING)
```
第1字节: bit8=1(no ext) | bits765=Nature of Address | bits4321=Numbering Plan
后续字节: TBCD-String 编码的数字
```

### IMSI 结构
- OCTET STRING (SIZE (3..8))
- 前 3 字节 = PLMN ID (MCC + MNC, E.212)

## 六、位置信息编码

### CGI (globalCellID [2])
```
a:   MCC digit 2 | MCC digit 1
a+1: MNC digit 3 | MCC digit 3
a+2: MNC digit 2 | MNC digit 1
a+3~a+4: LAC
a+5~a+6: CI
```

### LAI / SAI / RAI / TAI / ECGI
各位置格式的字节结构详见知识库笔记或 ASN.1 标准文档（umts-cs_hi2operations.asn）。

## 七、ZTLIG 部署实战

### 乌干达 Kafka 临时方案
前后台物理不通时，在前台部署 Kafka 并预创建 topic，否则 ZTLIG 1 进程不启动：

```bash
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic TARGET_INFO
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic TARGET_INFO_STATUS
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic OWLS_TMC_REALTIME
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic OWLS_TMC_OFFLINE
```

### tcpdump 抓包参考
```bash
# X1 对接
tcpdump -i any tcp port 6666 -s 0 -w "x1_$(date +%Y%m%d_%H%M%S).pcap"

# X2 实时
tcpdump -i any host <lig_ip> and port <x2_port> -vvv -nn -s 0 -X

# 详细输出
tcpdump -ni bond1 host <ne_ip> and host <lig_ip1 or lig_ip2> -vvv -nn -s 0 -w file.pcap
```

### tneid / vneid / hi2_neid 三层映射

```
物理网元 (hi2_neid) → tneid (系统自定义物理网元ID) → vneid (系统自定义虚拟网元ID)
```

后端界面下发设控时使用 **vneid（officesIds 字段）**。配置映射示例：
```ini
# NE 定义
ztlig.ne.683.tneid=26;  ztlig.ne.683.vendor=zte;  ztlig.ne.683.version=zte_v4_lis;
# VNE 定义——hi2_neid → vneid
ztlig.vne.791.tneid=26;  ztlig.vne.791.vneid=40;  ztlig.vne.791.hi2_neid=251971200361;
ztlig.vne.792.tneid=26;  ztlig.vne.792.vneid=41;  ztlig.vne.792.hi2_neid=251971200360;
```

### ZTLIG 进程命令参考

| 进程 | 命令 | 说明 |
|------|------|------|
| ztlig1 | `write ztlig1 {id} target file` | 布控数据写本地（生成 ztlig_target.txt）|
| | `show ztlig1 {id} mainframe stat` | 查看 curTarNum/ic/oc |
| | `syn ztlig1 {id} redis` | 三方同步 |
| ztlig2 | `show ztlig2 {id} kafka stat` | sendFailNum=0, sendSuccNum增长 |
| | `show ztlig2 {id} x2 stat` | X2 口统计 |
| ssf | `show ssf {id} stat` | 关注 RecvNum |
| rvf | `show rvf {id} stat` | 关注 RecvTotalMsgLen/CurSessionNum |
| | `show rvf {id} kafka stat` | OpenVox 推送统计 |
| ztlig3 | `show ztlig3 {id} nic stat` | oerrors=0, obytes变动 |

### 语音通知文件说明

当前版本（实时离线模式）可支持不配置 `rvf_noticepath`，但配置暂时不能直接去掉。

LIIMS 语音文件名格式：`Liid.cin.operatorid.neid.direction`
- operid：报告中若携带则用报告值，未携带则用配置值
- neid：即 hi2_neid，优先用报告值

项目组正准备在 ztlig2 上增加**运营商名称**配置，统一修改 operid。

## 八、对接检查清单

- [ ] X1 用户名/密码/NEID 三件套核对
- [ ] MGW/SBC 能 PING 通
- [ ] 防火墙端口不阻塞
- [ ] X3 端口配置（固定 x3port，无需协商）
- [ ] IMS 模式确认（hw_imsbase / mavenir / 102232-5）
- [ ] Kafka topic 预创建（ZTLIG 场景）
- [ ] 设控号码格式（GMSC→ISDN，其他→MSISDN）
- [ ] SpeechOutputMode（缺省 combinedOptionB）

## 九、参考资料

- `知识/telecom/lawful_interception/华为CS_X接口说明与ZTLIG部署实战.md`
- `知识/telecom/lawful_interception/华为SVC_VoLTE_ETSI监听方案.md`
- `知识/telecom/lawful_interception/华为SVC_IMS_X2报告抓包示例.md`
- `knowledge/telecom/lawful_interception/LI_ASN1解码工具_000000app_v1分析.md` — 本地 ASN.1 IRI 解码 Web 工具（源码架构与功能分析）
- `knowledge/hi2/华为LI协议/LI_ASN1解码工具_架构文档.md` — 工具五层架构、与华为标准/ZTLIG 的对比分析、7 项改进建议、数据流全景图
- `knowledge/hi2/华为LI协议/LI_ASN1解码工具_架构文档.md` — v3 版本新增 4 套 ASN.1 规范（hw_5gc_x2/hw_sae_x2/nsn_cs/zte_epc），10 种解码模式，EXE 反编译对比
- `~/LI/software/000000app_v1/` — v3 版 LI ASN.1 解码器源码（Ubuntu 24.04 原生运行，Flask Web 界面，10 种解码模式）
  - `app_linux_v3.py` — 主入口（10种解码模式）
  - `asn_spec_v3.py` — 9套 ASN.1 规范并行加载
  - `asn_decode_api_v3.py` — BER 解码引擎（含手动 TLV 分包）
  - `asn_decode_iri_report_v3.py` — 后处理（9种 BCD/APN/e164 转换）
  - `asnfile/` — 24个 ASN.1 规范文件（原20 + 新增4）
- `~/LI/software/v3_architecture.html` — v3 架构图（5层结构，10种解码模式，可交互 HTML）
- `~/LI/software/v3_architecture_a4.pdf` — A4 横版 300dpi 架构图 PDF
- `~/BACKUP/LI_ETSI_ASN1_ASSISTANT_V3/` — 完整项目备份（含 VS Code 配置、架构图、系统设计文档）
- `~/BACKUP/LI_ETSI_ASN1_ASSISTANT_V3/ETSI_ASN1_Assistant_V3_系统设计文档.md` — 9 章系统设计文档（含数据流全景、接口规范、ASN.1 索引、已知限制）
- `~/LI/software/asn/` — 原始 Windows EXE 项目含 4 个额外 ASN.1 规范文件（hw_5gc_x2/hw_sae_x2/nsn_cs/zte_epc），已反编译提取
- `etsi-lawful-intercept` skill — ETSI 标准体系总览
- `asn1-codec` skill — BER/PER 编解码工具
- `references/ims-rtp-correlation.md` — HW IMS RTP 流与 IRI 关联机制（LIID+imschargingid+Correlation Number）
- `references/v3-tool-asn1-specs.md` — v3 版 ASN.1 解码器新增 4 套规范详情（hw_5gc_x2/hw_sae_x2/nsn_cs/zte_epc 的解码模式、模块名、关键类型）
- `etsi-lawful-intercept` skill → `references/hw-header-byte-layout.md` — X1/X2/X3 帧头字节级布局、NE 类型映射、TBCD 位置编码

## 十、Common Pitfalls
