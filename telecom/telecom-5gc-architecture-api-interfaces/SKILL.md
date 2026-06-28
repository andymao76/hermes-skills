---
name: telecom-5gc-architecture-api-interfaces
description: 5GC SBA架构、网元、接口、SBA API调用、Registration/PDU Session流程、PFCP、VoNR、LI合法监听映射关系及Hermes排障规则
version: 1.0
domain: Telecom / 5G Core / IMS / Lawful Interception
---

# 5G Core Network (5GC) Architecture, API, Interfaces, Procedures & LI

## 1. 5GC 核心思想

5G Core (5GC) 采用 SBA（Service Based Architecture）。

核心变化：
- 4G EPC → 点对点接口 / Diameter / GTP-C
- 5GC → Service Based Architecture / HTTP-2 / REST API / JSON / TLS

控制面全面服务化，用户面继续使用 GTP-U 和 PFCP。

## 2. 5GC 网元

### AMF (Access and Mobility Management Function)
- 职责: Registration, Mobility Management, Paging, NAS
- 对应4G: MME
- 口诀: **AMF 管接入**

### SMF (Session Management Function)
- 职责: PDU Session, IP地址管理, QoS控制
- 对应4G: PGW-C, SGW-C
- 口诀: **SMF 管会话**

### UPF (User Plane Function)
- 职责: 用户面转发, 流量分流, NAT, DPI
- 对应4G: PGW-U, SGW-U
- 口诀: **UPF 管转发**

### UDM (Unified Data Management)
- 职责: 用户数据, Subscription
- 对应4G: HLR, HSS
- 口诀: **UDM 管用户**

### AUSF (Authentication Server Function)
- 职责: 5G AKA, EAP-AKA'
- 口诀: **AUSF 管认证**

### PCF (Policy Control Function)
- 职责: QoS, Charging Policy, Traffic Policy
- 对应4G: PCRF
- 口诀: **PCF 管策略**

### NRF (Network Repository Function)
- 职责: NF注册, NF发现
- 类似: Kubernetes Service Registry
- 口诀: **NRF 管发现**

### NSSF (Network Slice Selection Function)
- 职责: Slice Selection
- 口诀: **NSSF 管切片**

## 3. 5GC 接口

| 接口 | 连接 | 协议 | 说明 |
|------|------|------|------|
| N1 | UE ↔ AMF | NAS | 接入层信令 |
| N2 | gNB ↔ AMF | NGAP | 接入网与核心网 |
| N3 | gNB ↔ UPF | GTP-U | 用户面数据 |
| N4 | SMF ↔ UPF | PFCP | 控制用户面 |
| N6 | UPF ↔ Internet | - | 出口接口 |
| N7 | SMF ↔ PCF | - | 策略接口 |
| N8 | AMF ↔ UDM | - | 用户资料 |
| N10 | SMF ↔ UDM | - | 会话相关数据 |
| N11 | AMF ↔ SMF | - | 会话管理 |
| N12 | AMF ↔ AUSF | - | 认证 |
| N13 | AUSF ↔ UDM | - | 认证向量 |
| N15 | AMF ↔ PCF | - | 移动性策略 |

## 4. SBA API 调用

### AMF 注册 NRF
`PUT /nnrf-nfm/v1/nf-instances` → 返回: `{"nfType":"AMF", "status":"REGISTERED"}`

### NF 发现
`GET /nnrf-disc/v1/nf-instances`

### 创建 PDU Session
`POST /nsmf-pdusession/v1/sm-contexts`

### 查询用户数据
`GET /nudm-uecm/v1`

### 调用认证
`POST /nausf-auth/v1`

## 5. Registration 流程

`UE → Registration Request → gNB → N2 → AMF → N12 → AUSF → N13 → UDM` → Authentication Vector → `AMF → Registration Accept → UE`

口诀: UE → AMF → AUSF → UDM

## 6. PDU Session 流程

`UE → AMF → N11 → SMF → N7 → PCF → N4 → UPF → N6 → Internet`

步骤:
1. UE 请求 PDU Session
2. AMF 选择 SMF
3. SMF 获取策略
4. SMF 控制 UPF
5. 建立用户面

## 7. PFCP (Packet Forwarding Control Protocol)

- 作用: SMF 控制 UPF
- 典型消息: Session Establishment, Session Modification, Session Deletion

## 8. VoNR (Voice over New Radio)

架构: UE → 5GC → IMS

流程: IMS REGISTER → INVITE → 180 Ringing → 200 OK → ACK

与 VoLTE 区别: 无线侧 LTE → NR，IMS 完全相同。

## 9. 5GC 与 LI（合法监听）关系

| 网元 | LI输出 |
|------|--------|
| AMF | Registration IRI, Mobility IRI |
| SMF | PDU Session IRI |
| UPF | IPDR, User Plane |
| IMS | SIP IRI, VoNR IRI |

## 13. Hermes 排障规则

### Registration 失败
检查链路: N1 → N2 → N12 → N13

### 无法上网
检查链路: N11 → N4 → N6

### VoNR 失败
检查: IMS Registration / SIP INVITE / QoS Flow / PFCP

## 11. 5GC SBI URI 路径与正则匹配

### URI 标准模板（3GPP TS 29.501）

```
{apiRoot}/{apiName}/v{version}/{resource}/{resourceId}
```

### 13 个 NF API 路径

| NF | API 名称 | URI 路径前缀 |
|----|----------|-------------|
| NRF | Nnrf_NFManagement | `/nnrf-nfm/v1/nf-instances` |
| NRF | Nnrf_NFDiscovery | `/nnrf-disc/v1/nf-instances` |
| AMF | Namf_Communication | `/namf-comm/v1/ue-contexts` |
| AMF | Namf_EventExposure | `/namf-evts/v1/subscriptions` |
| SMF | Nsmf_PDUSession | `/nsmf-pdusession/v1/pdu-sessions` |
| SMF | Nsmf_EventExposure | `/nsmf-evts/v1/subscriptions` |
| UDM | Nudm_SDM | `/nudm-sdm/v2/{supi}` |
| UDM | Nudm_UECM | `/nudm-uecm/v1/{supi}` |
| AUSF | Nausf_UEAuthentication | `/nausf-auth/v1/ue-authentications` |
| PCF | Npcf_PolicyAuthorization | `/npcf-auth/v1/app-sessions` |
| NEF | Nnef_TrafficInfluence | `/nnef-trafficinfluence/v1/subscriptions` |
| NSSF | Nnssf_NSSelection | `/nnssf-nsselection/v1/network-slice-information` |
| SMSF | Nsmsf_SMService | `/nsmsf-sms/v1/{supi}/sms` |

### 通用正则提取服务名

```regex
^/(n[np][a-z]+-[a-z]+?)/v[0-9]+/
```
匹配结果分组 1 即 API 服务名，如 `nnrf-nfm`、`namf-comm`。

### 3GPP TS 29.571 公共数据类型校验正则

| 类型 | pattern | 说明 |
|------|---------|------|
| SUPI | `^(imsi-[0-9]{5,15}\|nai-.+\|...)$` | 用户永久标识 |
| NF Instance ID | `^[A-Fa-f0-9]{8}-[0-9]{3}-[0-9]{2,3}-(hex){1,10}$` | UUID变种 |
| GPSI | `^(msisdn-[0-9]{5,15}\|extid-[^@]+@[^@]+\|.+)$` | 用户公开标识 |
| PEI | `^(imei-[0-9]{15}\|imeisv-[0-9]{16}\|...)$` | 设备标识 |
| gNB ID | `^[A-Fa-f0-9]+$` | gNB标识 |
| AMF ID | `^[A-Fa-f0-9]{6}$` | 3字节hex |
| PLMN MCC | `^\d{3}$` | 国家码 |
| PLMN MNC | `^\d{2,3}$` | 网络码 |

完整 30+ 种正则模式见：[[5gc-regex-patterns]]

## 12. 快速记忆口诀

### 网元口诀
- AMF → 管接入
- SMF → 管会话
- UPF → 管转发
- UDM → 管用户
- AUSF → 管认证
- PCF → 管策略
- NRF → 管发现
- NSSF → 管切片

### 接口口诀
- N1 UE到AMF | N2 gNB到AMF | N3 gNB到UPF
- N4 SMF控UPF | N6 UPF出网
- N11 AMF找SMF | N12 AMF找AUSF | N13 AUSF找UDM
