# pycrate NGAP PER 解码参考

## 过程码映射（来自 NGAP-PDU-Descriptions）

| 码 | 过程名 | 码 | 过程名 |
|---|--------|---|--------|
| 0 | AMFConfigurationUpdate | 1 | AMFStatusIndication |
| 2 | CellTrafficTrace | 3 | DeactivateTrace |
| 4 | DownlinkNASTransport | 5 | DownlinkNonUEAssociatedNRPPaTransport |
| 6 | DownlinkRANConfigurationTransfer | 7 | DownlinkRANStatusTransfer |
| 8 | DownlinkUEAssociatedNRPPaTransport | 9 | ErrorIndication |
| 10 | HandoverCancel | 11 | HandoverNotification |
| 12 | HandoverPreparation | 13 | HandoverResourceAllocation |
| 14 | InitialContextSetup | 15 | InitialUEMessage |
| 16 | LocationReportingControl | 17 | LocationReportingFailureIndication |
| 18 | LocationReport | 19 | NASNonDeliveryIndication |
| 20 | NGReset | 21 | NGSetup |
| 22 | OverloadStart | 23 | OverloadStop |
| 24 | Paging | 25 | PathSwitchRequest |
| 26 | PDUSessionResourceModify | 27 | PDUSessionResourceModifyIndication |
| 28 | PDUSessionResourceRelease | 29 | PDUSessionResourceSetup |
| 30 | PDUSessionResourceNotify | 31 | PrivateMessage |
| 32 | PWSCancel | 33 | PWSFailureIndication |
| 34 | PWSRestartIndication | 35 | RANConfigurationUpdate |
| 36 | RerouteNASRequest | 37 | RRCInactiveTransitionReport |
| 38 | TraceFailureIndication | 39 | TraceStart |
| 40 | UEContextModification | 41 | UEContextRelease |
| 42 | UEContextReleaseRequest | 43 | UERadioCapabilityCheck |
| 44 | UERadioCapabilityInfoIndication | 45 | UETNLABindingRelease |
| 46 | UplinkNASTransport | 47 | UplinkNonUEAssociatedNRPPaTransport |
| 48 | UplinkRANConfigurationTransfer | 49 | UplinkRANStatusTransfer |
| 50 | UplinkUEAssociatedNRPPaTransport | 51 | WriteReplaceWarning |
| 52-80 | (SecondaryRATDataUsageReport 等) | | |

完整映射见 `pycrate_ngap.py` 中的 `PROCEDURE_CODES` 字典（0-80，共81个）。

## 关键 IE ID

| ID | 名称 | 说明 |
|----|------|------|
| 10 | AMF-UE-NGAP-ID | 会话关联（AMF侧） |
| 26 | FiveG-S-TMSI | UE 临时标识 |
| 28 | GUAMI | 全局唯一 AMF ID |
| 38 | NAS-PDU | N1 消息载体（内嵌 NAS） |
| 45 | NR-CGI | NR 小区全球标识 |
| 85 | RAN-UE-NGAP-ID | 会话关联（RAN侧） |
| 110 | UEAggregateMaximumBitRate | UE 聚合最大比特率 |
| 119 | UESecurityCapabilities | UE 安全能力 |
| 121 | UserLocationInformation | 用户位置信息 |
| 148 | S-NSSAI | 网络切片标识 |

完整 0-443 IE ID 见 `pycrate_ngap.py` 中的 `IE_NAMES` 字典。

## pycrate 集成模式

```python
import sys
sys.path.insert(0, '~/.local/lib/python3.12/site-packages/pycrate_asn1dir')
import NGAP as ngap_mod
from pycrate_asn1rt.init import init_modules

init_modules(
    ngap_mod.NGAP_CommonDataTypes,
    ngap_mod.NGAP_Constants,
    ngap_mod.NGAP_Containers,
    ngap_mod.NGAP_IEs,
    ngap_mod.NGAP_PDU_Contents,
    ngap_mod.NGAP_PDU_Descriptions,
)
NGAP_PDU = ngap_mod.NGAP_PDU_Descriptions.NGAP_PDU

# 解码
NGAP_PDU.from_aper(ngap_data)
pdu_type, fields = NGAP_PDU._val
proc_code = fields['procedureCode']
ies = fields['value'][1].get('protocolIEs', [])
```

## 性能优化

- 使用 `decode_ngap_pdu_header()` 做快速扫描（只解过程码和 PDU 类型，不解 IEs）
- 需要完整 IEs 时才调用 `decode()`
- 批量场景可复用同一个 `PycrateNgapDecoder` 实例
