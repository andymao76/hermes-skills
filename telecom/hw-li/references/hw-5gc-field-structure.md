# Huawei 5GC X2 IRI Field Structure (HWIriReport)

**ASN.1 模块**: `HWIriReport` (华为自定义，非标准 ETSI)
**文件路径**: `/home/andymao/LI/software/000000app_v1/asnfile/hw_5gc_x2.asn` (1197行)

## 结构特征

华为 5GC X2 的 ASN.1 采用**扁平化结构**，与 ETSI HI2Operations 的分层嵌套结构显著不同：

- 模块名 `HWIriReport`，无标准 OID 引用
- 省略 `IRIContent`/`IRISequence` 外层，直接使用 `IRI-Parameters`
- `CommunicationIdentifier` (CIN) 不作为独立 SEQUENCE，而是通过 `correlationNumber` [6] 承载
- 使用 `iRIEvent` [3] 而非 `cs-Event`/`ePSevent` 等

## IRI-Parameters 字段

| Tag | 字段名 | 类型 | 长度 | 说明 |
|-----|-------|------|------|------|
| [1] | `sessionID` | OCTET STRING | 4 | 会话ID (Activate LiTarget请求复制) |
| [2] | `timeStamp` | TimeStamp | 变长 | 事件时间戳 |
| [3] | `iRIEvent` | IRIEvent (ENUMERATED) | 1~61 | IRI 事件类型 |
| [4] | `partyInformation` | SET SIZE (1..10) | 变长 | 参与方 (含5GS标识) |
| [5] | `initiator` | Initiator | 枚举 | 发起方方向 |
| [6] | `correlationNumber` | OCTET STRING | 1~20 | 关联号 (Charging ID + IP地址) |
| [7] | `networkIdentifier` | Network-Identifier | 变长 | 网络标识 |
| [8] | `gPRS-specificParameters` | SEQUENCE | 变长 | GPRS 参数 |
| [9] | `ePS-GTPV2-specificParameters` | SEQUENCE | 变长 | EPS GTPv2 参数 |
| [10] | `ePS-PMIP-specificParameters` | SEQUENCE | 变长 | EPS PMIP 参数 |
| [11] | `ePS-DSMIP-SpecificParameters` | SEQUENCE | 变长 | EPS DSMIP 参数 |
| [12] | `ePS-MIP-SpecificParameters` | SEQUENCE | 变长 | EPS MIP 参数 |
| [13] | `fifthGS-specificParameters` | SEQUENCE | 变长 | **5GC 特定参数** |

## 5GC PartyInformation 扩展标识

| Tag | 字段 | 类型 | 对应标准名 | 说明 |
|-----|------|------|-----------|------|
| [10] | `sUPI` | SUPI | 3GPP TS 23.501 | 用户永久标识 (IMSI格式) |
| [11] | `sUCI` | SUCI | 3GPP TS 23.501 | 用户隐藏标识 (加密SUPI) |
| [12] | `pEI` | PEI | 3GPP TS 23.501 | 永久设备标识 (IMEI格式) |
| [13] | `gPSI` | GPSI | 3GPP TS 23.501 | 通用公共用户标识 (MSISDN格式) |
| [14] | `gUTI` | FiveGGUTI | 3GPP TS 23.501 | 5G 全局临时标识 |

## 5GC IRIEvent 枚举 (标签 50+)

| 值 | 事件 | 对应网元 | 说明 |
|----|------|---------|------|
| 50 | aMFRegistration | AMF | AMF 注册 |
| 51 | aMFDeregistration | AMF | AMF 注销 |
| 52 | aMFLocationUpdate | AMF | AMF 位置更新 |
| 53 | aMFStartOfInterceptionWithRegisteredUE | AMF | 已注册 UE 开始拦截 |
| 54 | aMFUnsuccessfulProcedure | AMF | AMF 流程失败 |
| 55 | sMFPDUSessionEstablishment | SMF | PDU 会话建立 |
| 56 | sMFPDUSessionModification | SMF | PDU 会话修改 |
| 57 | sMFPDUSessionRelease | SMF | PDU 会话释放 |
| 58 | sMFStartOfInterceptionWithEstablishedPDUSession | SMF | 已建立 PDU 会话开始拦截 |
| 59 | sMFUnsuccessfulProcedure | SMF | SMF 流程失败 |
| 60 | servingSystemMessage | — | 服务系统消息 |
| 61 | sMSMessage | SMF | SMF SM SMS |

## ETSI 标准 vs 华为 5GC 结构对比

| 维度 | ETSI HI2Operations | 华为 5GC HWIriReport |
|------|-------------------|---------------------|
| 外层 | IRIContent (CHOICE Begin/End/Continue/Report) | 扁平化，无外层嵌套 |
| IRI版本 | domainID [0] + iRIversion [23] | 无版本字段 |
| CIN | CommunicationIdentifier SEQUENCE (CIN+NetworkID) | correlationNumber [6] 替代 |
| 呼叫方向 | intercepted-Call-Direct [4] | initiator [5] |
| 呼叫状态 | intercepted-Call-State [5] | 无 |
| 时长 (振铃/通话) | ringingDuration [6] + conversationDuration [7] | 无 |
| 释放原因 | release-Reason [11] Q.850 | 无 |
| 呼叫性质 | nature-Of-The-intercepted-call [12] | 无 |
| SMS | sMS [14] + serverCenterAddress [13] | 无 (SMS通过SMF事件) |
| 位置 | locationOfTheTarget [8] | 无 (通过partyInformation?) |
| CC链路 | callContentLinkInformation [10] | 无 |
| 5G标识 | 无 | SUPI/SUCI/PEI/GPSI/GUTI |
| 5G特定参数 | 无 | fifthGS-specificParameters [13] |
| GPRS/EPS/PMIP/MIP/DSMIP | 有 | 有 |

## 参考文件

- ASN.1: `/home/andymao/LI/software/000000app_v1/asnfile/hw_5gc_x2.asn`
- 知识库: `知识/telecom/lawful_interception/华为CS_X接口说明与ZTLIG部署实战.md`
- 全字段字典: `/home/andymao/telecom-pack/huawei_zte_li_dictionary.md` (第 3.5 节)
