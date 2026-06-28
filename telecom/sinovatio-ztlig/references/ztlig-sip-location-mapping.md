# ZTLIG SIP 小区位置信息提取映射参考

## 背景

ZTLIG 在处理华为 IMS/VoLTE SIP 信令时，从 SIP 消息的 `P-Access-Network-Info`（PANI）头域中提取小区位置信息，映射到 OWLS TMC JSON 消息的 `LocationType` + `Location` 字段。

## 原始 SIP 头域

```
P-Access-Network-Info: 3GPP-E-UTRAN-FDD; utran-cell-id-3gpp=MCC.MNC.TAC.ECI
```

- **位置：** SIP INVITE / SIP REGISTER 消息中
- **规范依据：** 3GPP TS 24.229 / RFC 7315

**注意：** ZTLIG 的 DEBUG 日志（X2 submodule `X2_HW_IMS_MsgProc`）仅打印 From/To/P-Asserted-Identity 等有限头域，**不打印原始 PANI 头域**。PANI 的解析在 ZTLIG 内部完成，结果直接写入 OWLS 消息。

## OWLS TMC JSON 映射

```json
{
  "LocationType": 1,
  "Location": "6340704523F4C"
}
```

## LocationType 取值

| LocationType | 含义 | 来源 SIP 消息 | 场景 |
|---|---|---|---|
| `1` | 通话中小区位置 (Call-related) | SIP INVITE | VoLTE/VoNR 通话建立时 |
| `4` | 注册/附着位置 (Registration/Attach) | SIP REGISTER | 用户注册/附着时 (ReportType=1, EventDetail=2) |

## Location 值编码

格式为 `MCC MNC CELL_ID_HEX` 拼接的十六进制字符串：

| 示例 | 解码 | 含义 |
|---|---|---|
| `6340704523F4C` | MCC=634(苏丹), MNC=07(ZAIN), Cell=0x4523F4C | 4G LTE ECI |
| `634070043801` | MCC=634(苏丹), MNC=07(ZAIN), Cell=0x43801 | LAC/CI 或 ECI |
| `634070066101` | MCC=634(苏丹), MNC=07(ZAIN), Cell=0x66101 | LAC/CI 或 ECI |

## 典型日志示例（ZT LIG debug + INFO）

### 通话中位置（LocationType=1）

```
[DEBUG][ztlig2:462]X2 submodule:[X2_HW_IMS_MsgProc]sendLen = 2898, liid = [17746] target[+249****0415] sip msg[INVITE ...
From: <tel:+249****0415>;tag=aseh2aeo
P-Asserted-Identity: <sip:+249****0415@ims.mnc007.mcc634.3gppnetwork.org;cpc=ordinary>,<tel:+249****0415;cpc=ordinary>

[INFO ][ztlig2:462][ZtligKafkaProduceMsgByKey] topic[OWLS_TMC_REALTIME] msg[{
  "LocationType":1,
  "Location":"6340704523F4C",
  "NetworkType":11,
  ...
}]
```

### 注册位置（LocationType=4）

```
[INFO ][ztlig2:466][ZtligKafkaProduceMsgByKey] topic[OWLS_TMC_REALTIME] msg[{
  "CdrType":"LigCdr",
  "ReportType":1,
  "EventDetail":2,
  "LocationType":4,
  "Location":"634070066101",
  ...
}]
```

## OWLS 消息字段组合速查

| 场景 | ReportType | EventDetail | LocationType | NetworkType |
|---|---|---|---|---|
| 呼叫开始(Call Start) | 2 | 10 | 1 | 11(LTE)/13(IMS) |
| 呼叫应答(Answer) | 2 | 11 | 1 | 11/13 |
| 呼叫结束(Call End) | 2 | 13 | 1 | 11/13 |
| 呼叫转移(Forward) | 2 | 12 | - | 11/13 |
| 用户注册(Registration) | 1 | 2 | 4 | 13 |

## 关联

- `zte-li` SKILL.md → 第四章 巡检命令（`grep "Location"` 可快速定位位置信息）
- `hw-li` — 华为 HI2 接口中位置信息的 ASN.1 编码
