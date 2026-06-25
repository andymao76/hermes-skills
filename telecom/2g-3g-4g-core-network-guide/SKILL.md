---
name: 2g-3g-4g-core-network-guide
category: telecom
description: 2G GSM / 2.5G GPRS / 3G UMTS / 4G LTE EPC / 5G Core 核心网全栈架构、网元职责、接口命名规律、CS/PS/IMS语音业务、故障排查、LI/CDR关联知识
tags: [2G, 3G, 4G, 5G, GSM, GPRS, UMTS, LTE, EPC, 5GC, IMS, VoLTE, VoWiFi, VoNR, CSFB, SRVCC, MSC, MME, SGSN, GGSN, AMF, SMF, UPF, HLR, HSS, UDM, LI, Core Network, SBA]
related_skills: [hw-li, li-system-ops, a1-project-sudan-li]
---

# HERMES SKILL: 2G/3G/4G/5G Core Network Architecture, Interfaces, Evolution & Voice/Data Services

## 核心认知

移动核心网的演进，本质是从"电路交换语音"走向"全 IP 数据与服务化核心网"。

```
2G GSM           → 以 CS 语音为主
2.5G GPRS        → 在 2G 上增加 PS 数据域
3G UMTS          → CS + PS 双域并存
4G LTE / EPC     → 取消 CS 域，核心网全 IP，语音通过 IMS 实现 VoLTE
5G / 5GC         → 服务化架构 SBA，控制面云原生化，语音通过 IMS 实现 VoNR
```

一句话记忆：
```
2G = 打电话
2.5G = 手机上网开始
3G = CS + PS 双域
4G = EPC 全 IP + IMS 语音
5G = 5GC 服务化 + IMS 语音
```

---

# 1. 2G GSM 核心网

## 1.1 架构

```
MS
 │ Um
BTS
 │ Abis
BSC
 │ A
MSC/VLR
 ├── HLR
 ├── AuC
 └── EIR
```

## 1.2 网元

| 网元 | 全称 | 作用 |
|:----:|------|------|
| MS | Mobile Station | 手机/终端 |
| BTS | Base Transceiver Station | 无线收发基站 |
| BSC | Base Station Controller | 控制多个 BTS |
| MSC | Mobile Switching Center | 语音交换、呼叫控制、位置更新 |
| VLR | Visitor Location Register | 当前拜访位置数据 |
| HLR | Home Location Register | 用户永久数据 |
| AuC | Authentication Center | 鉴权中心 |
| EIR | Equipment Identity Register | IMEI 设备库 |

## 1.3 接口

| 接口 | 两端 | 用途 |
|:----:|:----:|------|
| Um | MS ↔ BTS | 空口 |
| Abis | BTS ↔ BSC | 基站内部控制与承载 |
| A | BSC ↔ MSC | 语音呼叫控制与承载 |
| MAP | MSC/VLR/HLR/AuC | 移动性、鉴权、位置更新 |

## 1.4 记忆口诀

```
MSC 管电话
HLR 管档案
VLR 管位置
AuC 管认证
EIR 管设备
```

---

# 2. 2.5G GPRS 核心网

GPRS 是 2G 网络上的分组数据增强。

## 2.1 架构

```
MS
 │
BTS
 │
BSC
 │ Gb
SGSN
 │ Gn
GGSN
 │ Gi
Internet / Intranet
```

## 2.2 新增网元

| 网元 | 全称 | 作用 |
|:----:|------|------|
| SGSN | Serving GPRS Support Node | 分组域移动性管理、Attach、PDP Context |
| GGSN | Gateway GPRS Support Node | 数据出口网关、连接 Internet/APN |

## 2.3 关键接口

| 接口 | 两端 | 用途 |
|:----:|:----:|------|
| Gb | BSC ↔ SGSN | GPRS 接入 |
| Gn | SGSN ↔ GGSN | GTP 隧道 |
| Gi | GGSN ↔ 外部网络 | Internet/APN 出口 |
| Gr | SGSN ↔ HLR | 用户数据查询 |
| Gc | GGSN ↔ HLR | 可选，位置/用户信息 |
| Gf | SGSN ↔ EIR | 设备校验 |

## 2.4 记忆

```
SGSN = 数据域的"人在哪里"
GGSN = 数据域的"从哪里上网"
```

---

# 3. 3G UMTS 核心网

3G 同时保留 CS 域和 PS 域。

## 3.1 架构

```
UE
 │ Uu
NodeB
 │ Iub
RNC
 ├── Iu-CS → MSC Server / MGW → PSTN
 └── Iu-PS → SGSN → GGSN → Internet
```

## 3.2 网元

| 网元 | 全称 | 作用 |
|:----:|------|------|
| NodeB | 3G Base Station | 3G 基站 |
| RNC | Radio Network Controller | 无线资源控制 |
| MSC Server | MSC 控制面 | CS 呼叫控制 |
| MGW | Media Gateway | CS 语音媒体承载 |
| SGSN | Serving GPRS Support Node | PS 移动性与会话 |
| GGSN | Gateway GPRS Support Node | PS 出口网关 |
| HLR | Home Location Register | 用户数据 |

## 3.3 接口

| 接口 | 两端 | 用途 |
|:----:|:----:|------|
| Uu | UE ↔ NodeB | 3G 空口 |
| Iub | NodeB ↔ RNC | 基站到控制器 |
| Iur | RNC ↔ RNC | RNC 间移动性 |
| Iu-CS | RNC ↔ MSC Server/MGW | 电路域 |
| Iu-PS | RNC ↔ SGSN | 分组域 |
| Mc | MSC Server ↔ MGW | 媒体网关控制 |
| Nb | MGW ↔ MGW | CS 承载 |
| Gn | SGSN ↔ GGSN | GTP |
| Gi | GGSN ↔ Internet/APN | 数据出口 |
| Gr | SGSN ↔ HLR | 用户数据 |

## 3.4 Iu 命名

```
Iu = Interface UMTS
Iu-CS = UMTS 到 CS Core
Iu-PS = UMTS 到 PS Core
```

---

# 4. CS 与 PS 的区别

## 4.1 CS: Circuit Switched

CS 是电路交换域，主要用于传统语音与短信。
- 呼叫建立时分配专用电路/资源
- 适合实时语音
- 典型网元：MSC、MGW、HLR、VLR
- 典型业务：2G/3G 普通电话、CS SMS、传真、CSFB 回落语音

## 4.2 PS: Packet Switched

PS 是分组交换域，主要用于数据业务。
- 数据按 IP 包传输
- 适合互联网业务
- 典型网元：SGSN、GGSN、MME、SGW、PGW、UPF
- 典型业务：GPRS/3G 数据、LTE 数据、5G 数据、VoLTE/VoNR 媒体承载、IPDR/CDR

## 4.3 记忆

```
CS = Call Switching = 传统电话
PS = Packet Switching = 上网数据
```

---

# 5. 4G LTE EPC

4G EPC 是全 IP 核心网，不再有 CS 域。

## 5.1 架构

```
UE
 │ LTE-Uu
eNodeB
 ├── S1-MME → MME → S6a → HSS
 └── S1-U   → SGW → S5/S8 → PGW → SGi → Internet/IMS
                         │
                         Gx
                         │
                        PCRF
```

## 5.2 网元

| 网元 | 全称 | 作用 |
|:----:|------|------|
| eNodeB | Evolved NodeB | LTE 基站 |
| MME | Mobility Management Entity | 控制面，Attach、TAU、NAS、鉴权 |
| SGW | Serving Gateway | 用户面锚点，转发 GTP-U |
| PGW | PDN Gateway | APN 出口，IP 分配，计费策略执行 |
| HSS | Home Subscriber Server | HLR 升级版 |
| PCRF | Policy and Charging Rules Function | 策略与计费规则 |
| OCS | Online Charging System | 在线计费 |
| OFCS | Offline Charging System | 离线计费 |

## 5.3 EPC 接口

| 接口 | 两端 | 协议/用途 |
|:----:|:----:|:---------:|
| LTE-Uu | UE ↔ eNB | LTE 空口 |
| S1-MME | eNB ↔ MME | S1AP/SCTP，控制面 |
| S1-U | eNB ↔ SGW | GTP-U，用户面 |
| S11 | MME ↔ SGW | GTP-C，承载控制 |
| S5 | SGW ↔ PGW | 同网内 SGW-PGW |
| S8 | SGW ↔ PGW | 漫游场景 |
| S6a | MME ↔ HSS | Diameter，鉴权与用户数据 |
| S10 | MME ↔ MME | MME 间移动性 |
| S3 | SGSN ↔ MME | 2G/3G 与 LTE 移动性 |
| S4 | SGSN ↔ SGW | 2G/3G 与 EPC 用户面 |
| SGi | PGW ↔ Internet/IMS | 外部 IP 网络 |
| Gx | PCRF ↔ PGW | PCC 策略 |
| Gy | PGW ↔ OCS | 在线计费 |
| Gz | PGW ↔ OFCS | 离线计费 |

## 5.4 S 接口命名

```
S = SAE (System Architecture Evolution)
S1 = eNB 到 EPC 的第一入口
S11 = MME 找 SGW 建承载
S5/S8 = SGW 到 PGW
S6a = MME 找 HSS 鉴权
SGi = PGW 出 Internet
Gx/Gy/Gz = 策略/在线计费/离线计费
```

## 5.5 4G Attach + 默认承载流程

```
UE
 ↓ Attach Request
eNB
 ↓ S1-MME
MME
 ↓ S6a
HSS 鉴权/用户数据
 ↓
MME
 ↓ S11 Create Session
SGW
 ↓ S5 Create Session
PGW
 ↓ 分配 IP / 建默认承载
SGW/PGW 回应
 ↓
MME
 ↓ Initial Context Setup
eNB
 ↓
UE Attach Accept
```

记忆：MME 找 HSS 鉴权 → MME 找 SGW → SGW 找 PGW → PGW 分 IP → 默认承载建立

---

# 6. 5G Core / 5GC

5G Core 采用 SBA（Service Based Architecture，服务化架构）。

## 6.1 架构

```
UE
 │ N1
gNB
 │ N2
AMF
 │
 ├── Namf / Nudm / Nausf / Nnrf / Npcf
 │
SMF
 │ N4
UPF
 │ N6
Data Network / Internet / IMS
```

## 6.2 5G 核心网函数 (NF)

| 网元/NF | 全称 | 作用 | 4G 对应 |
|:-------:|------|------|:-------:|
| AMF | Access and Mobility Management Function | 注册、移动性、接入控制 | MME 部分功能 |
| SMF | Session Management Function | PDU Session、UPF 控制、IP 分配 | PGW-C/SGW-C |
| UPF | User Plane Function | 用户面转发、分流、锚点 | SGW-U/PGW-U |
| UDM | Unified Data Management | 用户数据管理 | HSS/HLR |
| AUSF | Authentication Server Function | 鉴权 | HSS/AuC 部分 |
| PCF | Policy Control Function | 策略控制 | PCRF |
| NRF | Network Repository Function | NF 注册发现 | 新增 |
| NSSF | Network Slice Selection Function | 切片选择 | 新增 |
| NEF | Network Exposure Function | 能力开放 | 新增 |
| CHF | Charging Function | 计费 | OCS/OFCS 演进 |
| BSF | Binding Support Function | 绑定支持 | 新增 |
| AF | Application Function | 应用功能，如 IMS AF | 应用侧 |

## 6.3 5G 接口

| 接口 | 两端 | 用途 |
|:----:|:----:|------|
| N1 | UE ↔ AMF | NAS 信令 |
| N2 | gNB ↔ AMF | NGAP 控制面 |
| N3 | gNB ↔ UPF | GTP-U 用户面 |
| N4 | SMF ↔ UPF | PFCP 控制用户面 |
| N6 | UPF ↔ DN | 数据网络出口 |
| N8 | AMF ↔ UDM | 用户数据 |
| N10 | SMF ↔ UDM | 会话相关用户数据 |
| N11 | AMF ↔ SMF | 会话管理 |
| N12 | AMF ↔ AUSF | 鉴权 |
| N13 | AUSF ↔ UDM | 鉴权数据 |
| N15 | AMF ↔ PCF | 接入移动性策略 |
| N7 | SMF ↔ PCF | 会话策略 |
| N22 | AMF ↔ NSSF | 切片选择 |
| Nnrf | NF ↔ NRF | 服务注册与发现 |

## 6.4 5G 命名记忆

```
N = 5G Network Interface
N1 = UE 到 AMF
N2 = gNB 到 AMF
N3 = gNB 到 UPF
N4 = SMF 控制 UPF
N6 = UPF 出数据网
N11 = AMF 找 SMF 建会话
```

一句话：
```
AMF 管接入
SMF 管会话
UPF 管转发
UDM 管用户
AUSF 管认证
PCF 管策略
NRF 管发现
NSSF 管切片
```

## 6.5 5G Registration + PDU Session 流程

**注册流程：**
UE → gNB → AMF → AUSF/UDM 鉴权 → UDM 注册 → Registration Accept

**PDU Session 流程：**
UE → AMF → SMF → PCF 获取策略 → UPF 建立转发规则 → gNB/UPF 建用户面 → Data Network

**记忆：** AMF 负责注册，SMF 负责会话，UPF 负责转发，PCF 负责策略，UDM/AUSF 负责用户和鉴权

---

# 7. IMS 核心网

IMS 是 4G/5G 语音、多媒体业务的核心。

## 7.1 IMS 架构

```
UE
 │ SIP
P-CSCF
 │
I-CSCF
 │
S-CSCF
 │
 ├── HSS/UDM
 ├── TAS
 ├── MGCF/MGW
 └── SBC/IBCF
```

## 7.2 IMS 网元

| 网元 | 全称 | 作用 |
|:----:|------|------|
| P-CSCF | Proxy CSCF | UE 接入 IMS 的第一跳 |
| I-CSCF | Interrogating CSCF | 入口查询与路由 |
| S-CSCF | Serving CSCF | 注册、会话控制、业务触发 |
| HSS/UDM | Subscriber Database | IMS 用户数据 |
| TAS | Telephony Application Server | 补充业务、彩铃、呼转等 |
| SBC | Session Border Controller | 边界安全、媒体锚定 |
| IBCF | Interconnection Border Control Function | IMS 互联边界 |
| MGCF | Media Gateway Control Function | IMS 与 PSTN 互通 |
| IMS-MGW | IMS Media Gateway | 媒体转换 |

## 7.3 IMS 接口

| 接口 | 两端 | 用途 |
|:----:|:----:|------|
| Gm | UE ↔ P-CSCF | SIP 注册/呼叫 |
| Mw | CSCF ↔ CSCF | SIP 路由 |
| Cx | I/S-CSCF ↔ HSS | Diameter 用户数据 |
| Sh | AS ↔ HSS | 业务服务器查询用户数据 |
| ISC | S-CSCF ↔ TAS | 业务触发 |
| Mi | S-CSCF ↔ BGCF | 呼叫路由 |
| Mg | MGCF ↔ CSCF | PSTN 互通控制 |
| Mr | CSCF ↔ MRFC | 媒体资源控制 |
| Rx | P-CSCF/AF ↔ PCRF/PCF | QoS 策略请求 |

## 7.4 IMS 记忆

```
P-CSCF = Proxy，离用户最近
I-CSCF = Interrogating，负责查询入口
S-CSCF = Serving，真正服务用户
TAS = 电话业务服务器
HSS/UDM = 用户资料库
```

---

# 8. CS Call 流程

## 8.1 2G/3G 主叫 CS Call 简化流程

MS/UE → CM Service Request → BSC/RNC → MSC/VLR → HLR/AuC (鉴权) → Setup → 被叫侧 MSC → Paging → 被叫 MS/UE → Alerting → Connect → 通话建立

## 8.2 关键点

CS Call 依赖：MSC 做呼叫控制，HLR/VLR 做用户与位置，AuC 做鉴权，BSC/RNC 做无线接入，MGW 做媒体承载

## 8.3 常见信令

| 协议 | 用途 |
|:----:|------|
| BSSAP | BSC-MSC |
| RANAP | RNC-MSC/SGSN |
| MAP | MSC/HLR/VLR |
| ISUP | PSTN/局间呼叫 |
| CAP/CAMEL | 智能网业务 |

## 8.4 记忆

```
找用户 → 鉴权 → 寻呼 → 振铃 → 接通
```

---

# 9. VoLTE

VoLTE = Voice over LTE。4G 没有 CS 域，所以语音通过 IMS 在 LTE PS 承载上传输。

## 9.1 架构

UE → LTE → eNB → EPC (MME/SGW/PGW) → SGi → IMS (P-CSCF → I-CSCF → S-CSCF → TAS)

## 9.2 VoLTE 前提

- UE 支持 VoLTE
- SIM/用户开通 IMS
- LTE 网络支持 QCI/ARP 等 QoS
- EPC 能建立 IMS APN 默认承载
- IMS 注册成功
- P-CSCF 可发现
- 语音媒体通常使用专用承载

## 9.3 VoLTE 注册流程

UE Attach 到 LTE → 建立 Internet/IMS APN 承载 → 发现 P-CSCF → SIP REGISTER → P-CSCF → I-CSCF → S-CSCF → HSS 查询用户数据 → IMS 注册成功

## 9.4 VoLTE 呼叫流程

主叫 UE → SIP INVITE → P-CSCF → S-CSCF → 被叫侧 IMS → 被叫 UE → 180 Ringing → 200 OK → 主叫 UE → ACK → RTP 语音媒体建立

## 9.5 VoLTE QoS

| 承载 | 用途 |
|:----:|------|
| IMS 默认承载 | SIP 信令 |
| 语音专用承载 | RTP 语音 |
| 视频专用承载 | ViLTE 视频 |

QCI 1 = Conversational Voice | QCI 5 = IMS Signaling

## 9.6 记忆

```
VoLTE = LTE 承载 + IMS 控制 + RTP 媒体
```

---

# 10. CSFB

CSFB = Circuit Switched Fallback。当 LTE 不支持 VoLTE 或用户未开通 VoLTE 时，语音回落到 2G/3G CS 域。

## 10.1 架构

UE on LTE → MME → SGs → MSC → 2G/3G CS

## 10.2 流程

UE 在 LTE 待机 → 发起/收到语音呼叫 → MME 通过 SGs 与 MSC 交互 → UE 回落到 2G/3G → MSC 建立 CS Call

## 10.3 记忆

```
CSFB = 4G 不打电话，回 2G/3G 打
```

---

# 11. SRVCC

SRVCC = Single Radio Voice Call Continuity。用于 VoLTE 通话中从 LTE 切换到 2G/3G CS，保持语音不中断。

## 11.1 场景

VoLTE 通话中 → LTE 覆盖变差 → 切换到 2G/3G CS → 语音不中断

## 11.2 关键网元

MME, MSC Server, IMS, ATCF/ATGW, eNB, BSC/RNC

## 11.3 记忆

```
CSFB = 呼叫前回落
SRVCC = 通话中回落
```

---

# 12. VoWiFi

VoWiFi = Voice over Wi-Fi，也称 Wi-Fi Calling。语音仍然走 IMS，但接入不是 LTE，而是 Wi-Fi + 非 3GPP 接入。

## 12.1 架构

UE → Wi-Fi → WLAN → ePDG → PGW/UPF → IMS

## 12.2 网元

| 网元 | 全称 | 作用 |
|:----:|------|------|
| ePDG | evolved Packet Data Gateway | Wi-Fi 到运营商核心网的安全网关 |
| AAA | Authentication Authorization Accounting | 非 3GPP 接入认证 |
| PGW/UPF | Data Gateway | 数据出口与 IMS 连接 |
| IMS | IP Multimedia Subsystem | 语音控制 |

## 12.3 接口

| 接口 | 两端 | 用途 |
|:----:|:----:|------|
| SWu | UE ↔ ePDG | IPSec 隧道 |
| SWm | ePDG ↔ AAA | 鉴权 |
| S2b | ePDG ↔ PGW | EPC 接入 |
| N3IWF相关 | UE ↔ 5GC | 5G 非 3GPP 接入 |
| Gm | UE ↔ P-CSCF | SIP |

## 12.4 流程

UE 接入 Wi-Fi → 与 ePDG 建 IPSec → AAA 鉴权 → 连接 PGW/UPF → IMS 注册 → SIP 呼叫

## 12.5 记忆

```
VoWiFi = Wi-Fi 接入 + 安全隧道 + IMS 语音
```

---

# 13. VoNR

VoNR = Voice over New Radio。5G SA 下的语音业务，仍然基于 IMS。

## 13.1 架构

UE → NR → gNB → 5GC (AMF/SMF/UPF) → N6 → IMS (P-CSCF → I-CSCF → S-CSCF → TAS)

## 13.2 前提

- 5G SA 网络
- UE 支持 VoNR
- 用户开通 IMS
- 5GC 支持 IMS PDU Session
- IMS 注册成功
- QoS Flow 正确建立

## 13.3 流程

UE 注册 5G → 建立 IMS PDU Session → 发现 P-CSCF → IMS SIP REGISTER → VoNR 呼叫 SIP INVITE → 建立 QoS Flow → RTP/RTCP 语音媒体

## 13.4 5QI

5QI 1 = Conversational Voice | 5QI 5 = IMS Signaling

## 13.5 EPS Fallback

在 5G SA 覆盖或 VoNR 能力不足时，语音可能回落到 LTE VoLTE。

5G SA → 语音触发 → EPS Fallback 到 LTE → VoLTE 呼叫

## 13.6 记忆

```
VoNR = 5G NR + 5GC + IMS
EPS Fallback = 5G 回 4G 用 VoLTE
```

---

# 14. 业务场景对比

| 场景 | 接入 | 核心网 | 语音控制 | 媒体 | 备注 |
|:----:|:----:|:------:|:--------:|:----:|:----:|
| 2G CS Call | GSM | MSC | MSC/ISUP | TDM/TRAU | 传统电话 |
| 3G CS Call | UMTS | MSC Server/MGW | MSC Server | MGW | CS 语音 |
| GPRS Data | GERAN | SGSN/GGSN | PDP Context | GTP | 2.5G 数据 |
| 3G PS Data | UTRAN | SGSN/GGSN | PDP Context | GTP | 3G 数据 |
| LTE Data | LTE | EPC | MME/PGW | SGW/PGW | 全 IP 数据 |
| VoLTE | LTE | EPC + IMS | SIP/IMS | RTP | 4G 语音 |
| CSFB | LTE→2G/3G | EPC+MSC | MSC | CS | 回落语音 |
| SRVCC | LTE→2G/3G | EPC+MSC+IMS | IMS/MSC | RTP→CS | 通话中切换 |
| VoWiFi | Wi-Fi | EPC/5GC + IMS | SIP/IMS | RTP over IPSec | Wi-Fi Calling |
| VoNR | NR | 5GC + IMS | SIP/IMS | RTP/QoS Flow | 5G SA 语音 |
| EPS Fallback | NR→LTE | 5GC→EPC | IMS | VoLTE | 5G 回落 4G |

---

# 15. 接口快速记忆总表

## 15.1 2G/3G

| 接口 | 记忆 |
|:----:|:----:|
| Um | Mobile 空口 |
| Abis | BTS 到 BSC |
| A | BSC 到 MSC |
| Gb | BSC 到 SGSN |
| Gn | SGSN 到 GGSN |
| Gi | GGSN 出 Internet |
| Iu-CS | RNC 到 CS Core |
| Iu-PS | RNC 到 PS Core |
| Gr | SGSN 到 HLR |
| MAP | 移动核心网数据库信令 |

## 15.2 4G

| 接口 | 记忆 |
|:----:|:----:|
| S1-MME | eNB 到 MME 控制面 |
| S1-U | eNB 到 SGW 用户面 |
| S11 | MME 到 SGW |
| S5/S8 | SGW 到 PGW |
| S6a | MME 到 HSS |
| SGi | PGW 出口 |
| Gx | 策略 |
| Gy | 在线计费 |
| Gz | 离线计费 |
| SGs | MME 到 MSC，CSFB |

## 15.3 5G

| 接口 | 记忆 |
|:----:|:----:|
| N1 | UE 到 AMF |
| N2 | gNB 到 AMF |
| N3 | gNB 到 UPF |
| N4 | SMF 控 UPF |
| N6 | UPF 出口 |
| N7 | SMF 到 PCF |
| N8 | AMF 到 UDM |
| N10 | SMF 到 UDM |
| N11 | AMF 到 SMF |
| N12 | AMF 到 AUSF |
| N13 | AUSF 到 UDM |
| N15 | AMF 到 PCF |
| N22 | AMF 到 NSSF |

## 15.4 IMS

| 接口 | 记忆 |
|:----:|:----:|
| Gm | UE 到 P-CSCF |
| Mw | CSCF 之间 |
| Cx | CSCF 到 HSS |
| Sh | AS 到 HSS |
| ISC | S-CSCF 到 TAS |
| Rx | IMS 到 PCRF/PCF 策略 |

---

# 16. 演进映射

| 2G/3G | 4G EPC | 5G Core | 说明 |
|:-----:|:------:|:-------:|:----:|
| HLR | HSS | UDM | 用户数据 |
| AuC | HSS/AuC | AUSF/UDM | 鉴权 |
| SGSN | MME | AMF | 移动性控制 |
| GGSN | PGW | SMF/UPF | 数据出口演进 |
| MSC | IMS | IMS | 语音控制从 CS 转 SIP |
| BSC/RNC | eNB | gNB | 无线接入 |
| PCRF | PCRF | PCF | 策略控制 |
| GTP-U | GTP-U | GTP-U | 用户面仍大量使用 GTP-U |
| GTP-C | GTP-C | PFCP/N11 等 | 控制面服务化 |

---

# 17. LI / CDR / IPDR 关联

## 17.1 典型产生点

| 网络 | 网元 | 可能输出 |
|:----:|:----:|:--------:|
| 2G CS | MSC | CS-IRI, CC, CDR |
| 3G CS | MSC Server/MGW | CS-IRI, CC, CDR |
| 2G/3G PS | SGSN/GGSN | PS-IRI, IPDR, GTP CDR |
| 4G EPC | MME | EPS-IRI, Attach/TAU/Detach |
| 4G EPC | SGW/PGW | IPDR, Bearer, Flow, CDR |
| IMS | CSCF/TAS/SBC | SIP-IRI, VoLTE Call IRI |
| 5G Core | AMF | Registration/Mobility IRI |
| 5G Core | SMF | PDU Session IRI |
| 5G Core | UPF | User-plane/IPDR |
| VoWiFi | ePDG/IMS | Wi-Fi Calling IRI |
| VoNR | IMS/AMF/SMF/UPF | SIP + 5GC Session IRI |

## 17.2 关键字段联想

```
LIID → 监听目标标识
CIN → Communication Identity Number
CC-Link-Identifier → 通话内容关联
CommunicationIdentifier → ETSI LI 通信标识
EventType / EventDetail → 事件类型
IRI-Begin / Continue / End / Report → HI2 事件阶段
IPDR → 多来自 GGSN/PGW/UPF/数据平台
SIP INVITE / 180 / 200 / BYE → IMS/VoLTE/VoNR
GTP-C Create Session → EPC PS 承载
PFCP Session Establishment → 5GC UPF 控制
```

---

# 18. 常见故障定位思路

## 18.1 CS Call 不通

优先检查：无线接入 (BTS/BSC/RNC) → MSC/VLR 位置 → HLR 用户数据 → MAP 鉴权 → 被叫寻呼 → ISUP 局间路由 → MGW 媒体

## 18.2 LTE 数据不通

优先检查：Attach 是否成功 → S6a 鉴权 → S11 Create Session → S5/S8 到 PGW → APN 配置 → PGW 分配 IP → SGi 出口 → DNS → 策略/计费 Gx/Gy

## 18.3 VoLTE 不通

优先检查：LTE Attach → IMS APN → P-CSCF 发现 → SIP REGISTER → HSS IMS 签约 → SIP INVITE/180/200/ACK → 专用承载/QCI → RTP 单通/不通 → SBC/IMS 路由

## 18.4 VoWiFi 不通

优先检查：Wi-Fi 互联网可达 → ePDG 可达 → IPSec 隧道 → AAA 鉴权 → S2b/N3IWF 接入 → IMS 注册 → SIP 呼叫

## 18.5 VoNR 不通

优先检查：5G SA 注册 → IMS PDU Session → P-CSCF 发现 → SIP REGISTER → 5QI/QoS Flow → UPF 转发 → EPS Fallback 配置 → IMS 路由

---

# 19. 快速学习口诀

## 19.1 代际口诀
```
2G MSC 打电话
2.5G SGSN/GGSN 上网
3G CS/PS 两条路
4G EPC 全 IP
5G SBA 服务化
```

## 19.2 网元口诀
```
MSC 管电话, HLR 管档案, VLR 管位置, AuC 管认证
SGSN 管移动数据的人, GGSN 管数据出口
MME 管控制, SGW 管转发, PGW 管出口, HSS 管用户, PCRF 管策略
AMF 管接入, SMF 管会话, UPF 管转发, UDM 管用户, AUSF 管认证, PCF 管策略, NRF 管发现, NSSF 管切片
P-CSCF 是入口, I-CSCF 是查询, S-CSCF 是服务, TAS 是电话业务
```

## 19.3 语音业务口诀
```
CS Call = MSC 传统电话
VoLTE = LTE + EPC + IMS
VoWiFi = Wi-Fi + ePDG + IMS
VoNR = NR + 5GC + IMS
CSFB = 呼叫前回落
SRVCC = 通话中回落
EPS Fallback = 5G 回 4G 打 VoLTE
```

---

# 20. Hermes Agent 使用规则

当用户提出核心网、LI、CDR、IPDR、VoLTE、VoNR、VoWiFi、IMS、GTP、Diameter、PFCP、SIP 等问题时，按以下方式分析：

1. **判断网络代际**：2G / 3G / 4G / 5G / IMS
2. **判断业务域**：CS / PS / IMS / Wi-Fi Calling / LI/CDR/IPDR
3. **定位关键网元**：
   - CS: MSC/HLR/VLR/MGW
   - PS: SGSN/GGSN/MME/SGW/PGW/AMF/SMF/UPF
   - IMS: P-CSCF/I-CSCF/S-CSCF/TAS/SBC
   - LI: ADMF/MDF/DF/HI2/HI3/IRI/CC
4. **按接口追踪**：
   - 2G/3G: A/Iu/Gb/Gn/Gi/MAP
   - 4G: S1/S11/S5/S6a/SGi/Gx/Gy
   - 5G: N1/N2/N3/N4/N6/N11/N7/N8
   - IMS: Gm/Mw/Cx/Sh/ISC/Rx
5. **输出**：架构图 + 流程图 + 关键网元 + 接口 + 协议 + 故障定位步骤 + LI/CDR/IPDR 关系

---

# 21. Final Summary

```
2G/3G 的核心是 CS + PS。
4G 的核心是 EPC 全 IP。
5G 的核心是 SBA 服务化。
VoLTE、VoWiFi、VoNR 的共同核心都是 IMS。
传统电话看 MSC。
移动数据看 SGSN/GGSN/MME/SGW/PGW/AMF/SMF/UPF。
语音 IP 化看 IMS。
LI/CDR/IPDR 要按网元产生点和接口流程定位。
```

---

# 22. References

- 3GPP TS 23.501: System Architecture for the 5G System
- 3GPP TS 23.401: GPRS enhancements for E-UTRAN access
- 3GPP TS 23.002: Network Architecture
- GSMA IR.92: IMS Profile for Voice and SMS
- GSMA IR.51 / IR.94 / NG.114: IMS/VoLTE/VoWiFi/Video/Voice related profiles
- ETSI / 3GPP Lawful Interception: TS 101 671, TS 102 232, TS 33.108, TS 33.107, TS 33.126
- 源文档: `/home/andymao/HERMES_SKILL_Telecom_Core_2G_3G_4G_5G_IMS_VoLTE_VoWiFi_VoNR.md`
