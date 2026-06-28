# ZTE EPC HI2 Field Mapping (EpsHI2Operations)

**ASN.1 模块**: `EpsHI2Operations` (r10 version-3)
**文件路径**: `/home/andymao/LI/software/asn/asnfile/zte_epc.asn` (643行)

## IRI-Parameters 字段映射 (R10 version-3 vs ETSI R16)

| ZTE Tag | 字段名 | ETSI R16 Tag | 差异说明 |
|---------|-------|-------------|---------|
| [0] | `hi2epsDomainId` (OID) | [0] `domainID` | ZTE 命名不同但语义同 |
| [1] | `lawfulInterceptionIdentifier` | [1] | 完全一致 (LIID) |
| [3] | `timeStamp` | [3] | 完全一致 |
| [4] | `initiator` (ENUM) | [4] `intercepted-Call-Direct` | 语义同 (0=NA, 1=MO, 2=MT) |
| [8] | `locationOfTheTarget` | [8] | 完全一致 |
| [9] | `partyInformation` (SET 1..10) | [9] | 完全一致 |
| [13] | `serviceCenterAddress` | [13] | 完全一致 |
| [14] | `sMS` | [14] | 完全一致 |
| [16] | `national-Parameters` | [16] | 完全一致 |
| [18] | `ePSCorrelationNumber` | [18] | **替代** `gPRSCorrelationNumber` |
| [20] | `ePSevent` (ENUM) | [20] `gPRSevent` | **替代** GPRSevent |
| [21] | `sgsnAddress` | [21] | 完全一致 |
| [22] | `gPRSOperationErrorCode` | [22] | 完全一致 |
| [24] | `ggsnAddress` | [24] | 完全一致 |
| [25] | `qOS` | [25] | 完全一致 |
| [26] | `networkIdentifier` | [26] | 完全一致 |
| [27] | `sMSOriginatingAddress` | [27] | 完全一致 |
| [28] | `sMSTerminatingAddress` | [28] | 完全一致 |
| [29] | `iMSevent` | [29] | 完全一致 |
| [30] | `sIPMessage` | [30] | 完全一致 |
| [31] | `servingSGSN-number` | [31] | 完全一致 |
| [32] | `servingSGSN-address` | [32] | 完全一致 |
| [34] | `ldiEvent` | [34] | 完全一致 |
| [35] | `correlation` | [35] | 完全一致 |
| [36] | `ePS-GTPV2-specificParameters` | [36] | 完全一致 (见下) |
| [37] | `ePS-PMIP-specificParameters` | [37] | 完全一致 |
| [38] | `ePS-DSMIP-SpecificParameters` | [38] | 完全一致 |
| [39] | `ePS-MIP-SpecificParameters` | [39] | 完全一致 |
| [40] | `servingNodeAddress` (OCTET) | — | ZTE特有，向后兼容，不推荐使用 |
| [41] | `visitedNetworkId` (UTF8String) | [41] | 非3GPP接入拜访网络ID |
| [43] | `servingS4-SGSN-address` (OCTET) | [43] | Diameter Origin-Host;Origin-Realm |
| [255] | `national-HI2-ASN1parameters` | [255] | 完全一致 |

## ZTE 与华为 EPC 关键差异

| 差异点 | ZTE | 华为 |
|--------|-----|------|
| ASN.1 版本 | r10 version-3 | R16 version-1 |
| OID 域 | EpsHI2Operations r10 | EpsHI2Operations r16 |
| CIN (CommunicationIdentifier) | 不包含在 IRI-Parameters，上层封装 | 同 |
| ePSevent | 完整支持 | 完整支持 |
| visitedNetworkId | 支持 | 支持 |
| servingS4-SGSN-address | 支持 | 支持 |

## ZTE LIS 版本特征

| 版本 | 特征 |
|------|------|
| ZTE LIS V3 | 基础 CS/PS 监听，ASN.1 r10 version-3 |
| ZTE LIS V4 | 增强版，支持 speechType=5 (分割两个话单) |

## 参考文件

- ASN.1: `/home/andymao/LI/software/asn/asnfile/zte_epc.asn`
- 知识库: `知识/telecom/lawful_interception/`
- 全字段字典: `/home/andymao/telecom-pack/huawei_zte_li_dictionary.md` (第 8 章)
