---
name: telecom-core
version: "1.0"
category: telecom
description: 2G/3G/4G/5G 核心网架构、接口演进与语音/数据业务 — 覆盖 GSM/GPRS/UMTS/EPC/5GC/IMS/VoLTE/VoWiFi/VoNR
target: telecom_network_ops
language: zh-CN
---

# Telecom Core Network: 2G/3G/4G/5G/IMS/VoLTE/VoWiFi/VoNR

## Trigger Conditions

当用户提出以下问题时，应加载此 skill：
- 核心网架构相关问题（2G/3G/4G/5G）
- 接口命名与作用（A/Gb/Gn/Gi/Iu/S1/N 等）
- 语音业务（CS Call/VoLTE/VoWiFi/VoNR/CSFB/SRVCC/EPS Fallback）
- CS 域与 PS 域的区别
- IMS 相关（P/I/S-CSCF、TAS、SBC）
- LI/CDR/IPDR 的产生点
- 代际演进映射
- 故障定位（CS Call 不通/LTE 数据不通/VoLTE 不通等）

## 核心认知

移动核心网的演进：电路交换语音 → 全 IP 数据与服务化核心网

```
2G GSM      = CS 语音为主
2.5G GPRS   = 增加 PS 数据域
3G UMTS     = CS + PS 双域并存
4G LTE/EPC  = 取消 CS 域，全 IP，语音靠 IMS VoLTE
5G 5GC      = SBA 服务化架构，语音靠 IMS VoNR
```

## 网元速查

### 2G/3G
| 网元 | 作用 |
|------|------|
| MSC | 语音交换、呼叫控制、位置更新 |
| VLR | 当前拜访位置数据 |
| HLR | 用户永久数据 |
| AuC | 鉴权中心 |
| EIR | IMEI 设备库 |
| SGSN | 分组域移动性管理、Attach、PDP Context |
| GGSN | 数据出口网关，连接 Internet/APN |
| RNC | 无线资源控制（3G） |
| MSC Server | CS 呼叫控制面（3G） |
| MGW | CS 语音媒体承载（3G） |

### 4G EPC
| 网元 | 作用 |
|------|------|
| MME | 控制面：Attach、TAU、NAS、鉴权 |
| SGW | 用户面锚点，转发 GTP-U |
| PGW | APN 出口，IP 分配，计费策略执行 |
| HSS | HLR 升级版 |
| PCRF | 策略与计费规则 |

### 5G Core
| NF | 作用 | 4G 对应 |
|----|------|---------|
| AMF | 注册、移动性、接入控制 | MME 部分 |
| SMF | PDU Session、UPF 控制、IP 分配 | PGW-C/SGW-C |
| UPF | 用户面转发、分流、锚点 | SGW-U/PGW-U |
| UDM | 用户数据管理 | HSS/HLR |
| AUSF | 鉴权 | HSS/AuC |
| PCF | 策略控制 | PCRF |
| NRF | NF 注册发现 | 新增 |
| NSSF | 切片选择 | 新增 |

### IMS
| 网元 | 作用 |
|------|------|
| P-CSCF | UE 接入 IMS 的第一跳 |
| I-CSCF | 入口查询与路由 |
| S-CSCF | 注册、会话控制、业务触发 |
| TAS | 补充业务、彩铃、呼转 |
| SBC | 边界安全、媒体锚定 |
| MGCF | IMS 与 PSTN 互通 |

## 接口速查

### 2G/3G 接口
| 接口 | 用途 |
|------|------|
| Um | MS ↔ BTS 空口 |
| Abis | BTS ↔ BSC |
| A | BSC ↔ MSC |
| Gb | BSC ↔ SGSN |
| Gn | SGSN ↔ GGSN (GTP) |
| Gi | GGSN ↔ Internet |
| Iu-CS | RNC ↔ CS Core |
| Iu-PS | RNC ↔ PS Core |

### 4G EPC 接口
| 接口 | 用途 |
|------|------|
| S1-MME | eNB ↔ MME 控制面 |
| S1-U | eNB ↔ SGW 用户面 |
| S11 | MME ↔ SGW |
| S5/S8 | SGW ↔ PGW |
| S6a | MME ↔ HSS |
| SGi | PGW 出口 |
| Gx | 策略 (PCRF ↔ PGW) |
| Gy | 在线计费 |
| Gz | 离线计费 |
| SGs | MME ↔ MSC (CSFB) |

### 5G 接口
| 接口 | 用途 |
|------|------|
| N1 | UE ↔ AMF (NAS) |
| N2 | gNB ↔ AMF (NGAP) |
| N3 | gNB ↔ UPF (GTP-U) |
| N4 | SMF ↔ UPF (PFCP) |
| N6 | UPF ↔ DN |
| N11 | AMF ↔ SMF |
| N7 | SMF ↔ PCF |
| N8 | AMF ↔ UDM |
| N12 | AMF ↔ AUSF |

### IMS 接口
| 接口 | 用途 |
|------|------|
| Gm | UE ↔ P-CSCF (SIP) |
| Mw | CSCF ↔ CSCF |
| Cx | CSCF ↔ HSS (Diameter) |
| Sh | AS ↔ HSS |
| ISC | S-CSCF ↔ TAS |
| Rx | IMS ↔ PCRF/PCF 策略 |

## 语音业务对比

| 场景 | 接入 | 核心网 | 语音控制 | 媒体 |
|------|------|--------|---------|------|
| 2G CS Call | GSM | MSC | MSC/ISUP | TDM/TRAU |
| 3G CS Call | UMTS | MSC Server/MGW | MSC Server | MGW |
| VoLTE | LTE | EPC + IMS | SIP/IMS | RTP |
| CSFB | LTE→2G/3G | EPC+MSC | MSC | CS |
| SRVCC | LTE→2G/3G | EPC+MSC+IMS | IMS/MSC | RTP→CS |
| VoWiFi | Wi-Fi | EPC/5GC + IMS | SIP/IMS | RTP over IPSec |
| VoNR | NR | 5GC + IMS | SIP/IMS | RTP/QoS Flow |
| EPS Fallback | NR→LTE | 5GC→EPC | IMS | VoLTE |

## 故障定位思路

### CS Call 不通
无线接入 → MSC/VLR 位置 → HLR 用户数据 → MAP 鉴权 → 被叫寻呼 → ISUP 路由 → MGW 媒体

### LTE 数据不通
Attach → S6a 鉴权 → S11 Create Session → S5/S8 到 PGW → APN → PGW 分 IP → SGi 出口 → DNS → Gx/Gy

### VoLTE 不通
LTE Attach → IMS APN → P-CSCF 发现 → SIP REGISTER → HSS IMS 签约 → SIP INVITE/180/200 → 专用承载/QCI → RTP → SBC/IMS 路由

### VoNR 不通
5G SA 注册 → IMS PDU Session → P-CSCF 发现 → SIP REGISTER → 5QI/QoS Flow → UPF 转发 → EPS Fallback 配置

## 运维口诀

```
2G MSC 打电话       | AMF 管接入
2.5G SGSN/GGSN 上网 | SMF 管会话
3G CS/PS 两条路     | UPF 管转发
4G EPC 全 IP        | UDM 管用户
5G SBA 服务化       | AUSF 管认证

MSC 管电话          | P-CSCF 是入口
HLR 管档案          | I-CSCF 是查询
VLR 管位置          | S-CSCF 是服务
AuC 管认证          | TAS 是电话业务

CSFB = 呼叫前回落
SRVCC = 通话中回落
EPS Fallback = 5G 回 4G 打 VoLTE
```

## 演进映射

| 2G/3G | 4G EPC | 5G Core |
|-------|--------|---------|
| HLR | HSS | UDM |
| AuC | HSS/AuC | AUSF/UDM |
| SGSN | MME | AMF |
| GGSN | PGW | SMF+UPF |
| MSC | IMS | IMS |
| PCRF | PCRF | PCF |

## LI/CDR/IPDR 关联

| 网络 | 网元 | 输出 |
|------|------|------|
| 2G CS | MSC | CS-IRI, CC, CDR |
| 3G CS | MSC Server/MGW | CS-IRI, CC, CDR |
| 2G/3G PS | SGSN/GGSN | PS-IRI, IPDR, GTP CDR |
| 4G EPC | MME/SGW/PGW | EPS-IRI, IPDR, Bearer, Flow |
| IMS | CSCF/TAS/SBC | SIP-IRI, VoLTE Call IRI |
| 5G Core | AMF/SMF/UPF | Registration/PDU Session IRI, IPDR |
| VoWiFi | ePDG/IMS | Wi-Fi Calling IRI |

## 参考标准

- 3GPP TS 23.501: 5G System Architecture
- 3GPP TS 23.401: GPRS enhancements for E-UTRAN
- 3GPP TS 23.002: Network Architecture
- GSMA IR.92: IMS Profile for Voice and SMS
- ETSI TS 101 671 / TS 102 232 / TS 33.108: Lawful Interception
