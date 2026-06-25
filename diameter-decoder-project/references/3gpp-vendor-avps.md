# 3GPP 厂商特定 AVP 字典

所属技能: diameter-decoder-project
供应商 ID: 10415 (3GPP), 193 (Ericsson), 94 (Nokia/NSN), 2011 (Huawei)
来源: 3GPP TS 29.061, TS 29.212, TS 32.299, TS 29.229, IANA SMI 注册

---

## TS 29.061 / 29.272 (GPRS / S6a/S6d 用户数据)

| Code | 名称 | 类型 | 说明 |
|------|------|------|------|
| 1 | 3GPP-IMSI | UTF8String | 用户 IMSI |
| 2 | 3GPP-Charging-Id | OctetString | 计费会话 ID |
| 3 | 3GPP-PDP-Type | Enumerated | PDP 类型 (IPv4/IPv6/PPP) |
| 4 | 3GPP-GGSN-Address | Address | GGSN 地址 |
| 5 | 3GPP-GGSN-IPv6-Address | Address | GGSN IPv6 地址 |
| 6 | 3GPP-NSAPI | OctetString | NAS 会话标识 |
| 7 | 3GPP-IMSI-MCC-MNC | UTF8String | IMSI 中的 MCC+MNC |
| 8 | 3GPP-GPRS-QoS-Profile | OctetString | QoS 档案 |
| 9 | 3GPP-MCC-MNC | UTF8String | 运营商 MCC+MNC |
| 10 | 3GPP-RAT-Type | OctetString | 无线接入类型 |
| 11 | 3GPP-User-Location-Info | OctetString | 用户位置信息 |
| 12 | 3GPP-MS-TimeZone | OctetString | 用户时区 |
| 14 | 3GPP-PDP-Address | Address | PDP 地址 (IPv4) |
| 15 | 3GPP-PDP-IPv6-Address | Address | PDP IPv6 地址 |
| 16 | 3GPP-SGSN-Address | Address | SGSN 地址 |
| 18-23 | 3GPP-CGI/SAI/RAI/TAI/ECGI/LAI | OctetString | 小区/路由/跟踪区标识 |
| 25-27 | 3GPP-MSISDN/IMEI/IMEISV | UTF8String | 用户/MS 标识 |
| 30-32 | 3GPP-APN / Charging-Characteristics / PDP-Context | OctetString/Grouped | 接入点/计费/上下文 |
| 34-36 | Secondary-RAT-Type / SIPTO / CSG-Info | OctetString | 增强特性 |

## TS 29.212 (Gx / PCC 策略和计费控制)

| Code | 名称 | 类型 | 说明 |
|------|------|------|------|
| 100 | QoS-Rule-Install | Grouped | 安装 QoS 规则 |
| 101 | QoS-Rule | Grouped | QoS 规则定义 |
| 102 | QoS-Class-Identifier | Enumerated | QCI (1-9) |
| 103-104 | QoS-Rule-Remove / Base-Name | Grouped/OctetString | 删除/基底名称 |
| 105-109 | Charging-Rule-* | Grouped/OctetString | 计费规则安装/删除/定义/名称 |
| 110 | Bearer-Usage | Enumerated | 承载用途 |
| 111-112 | Bearer-Identifier / Event-Trigger | OctetString/Enumerated | 承载标识/事件触发 |
| 113-115 | Bearer-Operation / AN-Charging-Id | Enumerated/Grouped | 承载操作 |
| 116-117 | Charging-Rule-Report / Default-EPS-QoS | Grouped/OctetString | 规则报告/默认QoS |
| 118-125 | AN-GW-Address, APN-AMBR, GBR, MBR | Address/Unsigned32 | 带宽参数(上下行) |
| 126-128 | IP-CAN-Type / QoS-Info / Default-Access | Enumerated/Grouped/OctetString | 接入类型/QoS/默认接入 |

## TS 32.299 (Charging / Gy / Gz 离线在线计费)

| Code | 名称 | 类型 | 说明 |
|------|------|------|------|
| 200-201 | Service-Id / Traffic-Data-Volumes | OctetString/Grouped | 服务标识/数据量 |
| 202-204 | Service-Identifier / Rating-Group / Quota-Time | Unsigned32 | 计费单元 |
| 206-208 | User-Equipment-Info (Type+Value) | Grouped/Enumerated/OctetString | UE 信息 |
| 209-211 | Service-Context-Id / Sponsor-Identity / ASP-Identity | OctetString/UTF8String | 业务上下文/赞助商 |
| 212-214 | Online-Charging-Flag / Reporting-Reason / Time-Quota-Type | Enumerated | 计费控制 |
| 215 | Event-Type | Grouped | 事件类型 |
| 216 | UTRAN-Positioning-Info | OctetString | 定位信息 |
| 217-225 | MME/MSC/SGSN Number/Name/Realm | OctetString/UTF8String | 网络节点信息 |

## TS 29.229 (Cx / Sh / Dh IMS)

| Code | 名称 | 类型 | 说明 |
|------|------|------|------|
| 300 | Visited-Network-Identifier | OctetString | 拜访网络 ID |
| 301 | Public-Identity | UTF8String | 公有用户标识 (SIP URI) |
| 302 | Server-Name | UTF8String | S-CSCF 名称 |
| 303-305 | Server-Capabilities (Mandatory/Optional) | Grouped/Unsigned32 | 服务器能力 |
| 306 | User-Data | OctetString | HSS 用户数据 (XML) |
| 307-312 | SIP-Auth-* | Grouped/OctetString | SIP 认证 |
| 313-317 | Charging-Information (Primary/Secondary ECF/CCF) | Grouped/OctetString | 计费功能地址 |
| 318-322 | User-Data-Available / Associated-Id / User-Identity | Enumerated/Grouped | 用户关联 |
| 321 | SCSCF-Restoration-Info | Grouped | S-CSCF 恢复 |
| 322 | Multiple-Registration-Indication | Enumerated | 多注册指示 |

## LCS (Location Services)

| Code | 名称 | 类型 | 说明 |
|------|------|------|------|
| 400 | LCS-EPS-Delivery | Enumerated | LCS 传递模式 |
| 401 | LCS-Client-Name | OctetString | LCS 客户端名 |
| 402 | LCS-APN | OctetString | LCS 接入点 |
| 405 | LCS-QoS-Class | Enumerated | LCS QoS 等级 |
| 406-407 | LCS-Privacy-Check / Supported-Methods | Enumerated/OctetString | 隐私检查/支持方法 |

## 其他厂商

| 厂商 | Vendor ID | Codes | 说明 |
|------|-----------|-------|------|
| Ericsson | 193 | 152-153 | Owner-Info, Owner-Data |
| Nokia/NSN | 94 | 20-21 | Charging-Info, Service-Data |
| Huawei | 2011 | 1-2 | Charging-ID, Service-Info |
