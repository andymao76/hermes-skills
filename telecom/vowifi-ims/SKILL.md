---
name: vowifi-ims
description: VoWiFi(Voice over Wi-Fi)和IMS(IP Multimedia Subsystem)技术文档集合 — 架构、信令流程、标准规范参考、Troubleshooting指南。覆盖非信任域/信任域接入、ePDG/IPSec隧道、IMS注册/呼叫流程、3GPP/ETSI/GSMA标准索引。
category: telecom
tags: [vowifi, ims, epdg, sip, volte, 3gpp, etsi, wlan, ipsec, troubleshooting]
---

# VoWiFi (Voice over Wi-Fi) & IMS 技术参考

## 一、VoWiFi 概述

VoWiFi（Voice over Wi-Fi, 又称 Wi-Fi Calling）是基于 IMS 核心网的语音通信技术，允许用户通过 Wi-Fi 接入运营商的 EPC（演进分组核心网）和 IMS 系统，实现与传统蜂窝网络无缝集成的语音/视频通话。其本质是将语音数据封装为 IP 包经 Wi-Fi 传输，最终通过运营商核心网连接至目标终端。

### 核心价值
- 蜂窝网络覆盖盲区（地下室、电梯、偏远地区）的语音补充方案
- 与 VoLTE 共享同一 IMS 核心，互补部署
- 支持 VoLTE ↔ VoWiFi 无缝切换（SRVCC/ePDG continuity）
- 利用现有 Wi-Fi 基础设施降低运营商覆盖成本

### VoWiFi vs VoLTE vs VoNR

| 特性 | VoLTE | VoWiFi | VoNR |
|------|-------|--------|------|
| 接入网络 | LTE (E-UTRAN) | Wi-Fi (非3GPP) | NR (5G) |
| 安全机制 | LTE NAS/AS 安全 | IKEv2 + IPSec 隧道 | 5G NAS/AS 安全 |
| 核心网 | EPC + IMS | ePDG + EPC + IMS | 5GC + IMS |
| 标准 | 3GPP TS 23.228 | 3GPP TS 23.402, TS 33.402 | 3GPP TS 23.501 |
| QoS | EPS Bearer 机制 | Best-effort（无端到端 QoS） | 5G QoS Flow |

## 二、IMS 核心网架构

IMS（IP Multimedia Subsystem）是 3GPP 标准化的 IP 多媒体架构，采用分层设计：

```
┌──────────────────────────────┐
│   业务应用层 (Application)   │
│  TAS / MRF / IM-SSF / AS    │
├──────────────────────────────┤
│   呼叫控制层 (Control)       │
│  P-CSCF / I-CSCF / S-CSCF   │
│  HSS / SLF / BGCF            │
├──────────────────────────────┤
│   接入层 (Access / Transport)│
│  UE → ePDG → PGW → IMS      │
│  或 UE → LTE → PGW → IMS     │
└──────────────────────────────┘
```

### IMS 关键网元

| 网元 | 全称 | 功能 |
|------|------|------|
| P-CSCF | Proxy-CSCF | UE 的 IMS 接入点，SIP 代理，安全网关 |
| I-CSCF | Interrogating-CSCF | 归属网络 SIP 入口，查询 HSS 分配 S-CSCF |
| S-CSCF | Serving-CSCF | IMS 核心会话控制，注册管理，业务触发 |
| HSS | Home Subscriber Server | 用户数据库，存储签约信息、鉴权向量 |
| MRF | Media Resource Function | 媒体资源处理（会议、录音、通知音） |
| BGCF | Breakout Gateway Control Function | PSTN 出口选择 |
| IBCF | Interconnection Border Control Function | 网络互联边界控制 |

### P-CSCF / I-CSCF / S-CSCF 协作关系

- **P-CSCF = 本地代理服务器**：UE 接入 IMS 的第一个节点，负责 SIP 消息转发和安全保护
- **I-CSCF = 归属地代理服务器**：在归属网络中作为 SIP 入口，查询 HSS 找到合适的 S-CSCF，兼负载均衡
- **S-CSCF = 归属地呼叫控制服务器**：实际处理 SIP 注册/会话，与 HSS 交互获取用户签约信息，触发 SPT（Service Point Trigger）业务逻辑

## 三、VoWiFi 接入架构

### 三种接入方式

#### 1. 非信任域 WLAN 接入（Untrusted WLAN，主流方案）
- **标准**：3GPP TS 23.402（Rel-6 引入）
- **路径**：UE → Wi-Fi（公共/家庭）→ Internet → ePDG → PGW → IMS
- **安全**：IKEv2 + IPSec 隧道（UE ↔ ePDG 全程加密）
- **关键新增网元**：ePDG、3GPP AAA Server

```
[UE] -- WiFi -- Internet -- [ePDG] -- SWm -- [3GPP AAA]
                                   |-- S2b -- [PGW] -- SGi -- [IMS]
```

#### 2. 信任域 WLAN 接入（Trusted WLAN）
- **标准**：3GPP Rel-8
- **路径**：UE → 运营商自有 Wi-Fi → TWAG → PGW → IMS
- **安全**：无需 IPSec，网络可信（802.1x/EAP）
- **关键新增网元**：TWAG（Trusted Wireless Access Gateway）

#### 3. IMS 直接接入（IMS Direct Access）
- **路径**：UE（APP）→ Wi-Fi → 直接连接到 IMS（绕过 EPC）
- **场景**：无 SIM 设备、老旧终端 App 方式
- **特点**：APP 处理认证、编解码、IMS 适配

### ePDG 详解

ePDG（Evolved Packet Data Gateway）是 VoWiFi 非信任接入的核心网关节点，类似 5G 中的 N3IWF。

**主要功能**：
1. **IKEv2 隧道搭建**：与 UE 协商加密参数，建立 IPSec 隧道
   - 常见加密：AES-256 + SHA-256
   - 认证协议：EAP-AKA'（基于 SIM 卡）
2. **流量导引**：通过 S2b 接口将加密后的语音数据送往 PGW
   - 剥离外层 IP 头，保留内层 IMS 信令原始 IP
3. **安全网关**：防止非信任 Wi-Fi 网络对核心网的攻击

**ePDG 接口**：

| 接口 | 协议 | 连接对象 | 用途 |
|------|------|---------|------|
| SWu | IKEv2/IPsec | UE | IPSec 隧道建立与管理 |
| SWm | Diameter | 3GPP AAA | EAP-AKA' 认证、密钥分发 |
| S2b | GTP/PMIP | PGW | PDN 连接承载 |
| SWx | Diameter | HSS（经AAA） | 用户签约数据获取 |

## 四、VoWiFi 信令流程

### 4.1 IKEv2 认证与 IPSec 隧道建立

```
UE                          ePDG                  3GPP AAA         HSS
 |                           |                       |               |
 |--- IKE_SA_INIT ---------->|                       |               |
 |<-- IKE_SA_INIT Response---|                       |               |
 |                           |                       |               |
 |--- IKE_AUTH (EAP-AKA')--->|                       |               |
 |                           |--- Diameter EAP------>|               |
 |                           |                       |--- SWx ------->|
 |                           |                       |<-- Auth Vector-|
 |                           |<-- Diameter EAP-------|               |
 |<-- IKE_AUTH (EAP-Req)-----|                       |               |
 |                           |                       |               |
 | (UE SIM 计算 RES)         |                       |               |
 |--- IKE_AUTH (EAP-Resp)--->|                       |               |
 |                           |--- Diameter EAP------>|               |
 |                           |                       | (验证 RES)    |
 |                           |<-- Diameter EAP_OK----|               |
 |<-- IKE_AUTH (IPsec SA)----|                       |               |
 |                           |                       |               |
 |===== IPSec Tunnel Established =====|               |               |
```

**步骤说明**：
1. **IKE_SA_INIT**：UE 与 ePDG 协商 IKE 安全参数（加密算法、DH 组、PRF）
2. **IKE_AUTH Phase 1**：UE 发送 EAP-AKA' 认证请求（含 IMSI/NAI）
3. **ePDG → AAA → HSS**：ePDG 通过 SWm/Diameter 向 AAA 转发认证请求，AAA 通过 SWx 从 HSS 获取鉴权向量（AUTN, RAND, XRES, IK, CK）
4. **AAA → ePDG → UE**：将 AUTN+RAND 下发给 UE
5. **SIM 验证**：UE SIM 卡验证 AUTN（确认网络合法性），计算 RES/IK/CK
6. **UE → ePDG → AAA**：返回 RES，AAA 验证通过后通知 ePDG
7. **IPsec SA 建立**：ePDG 安装 IPsec 安全关联，UE ↔ ePDG IPSec 隧道建立

### 4.2 IMS 注册流程（VoWiFi 场景）

隧道建立后，UE 通过已建立的 IPSec 隧道进行 IMS 注册：

```
UE          ePDG          PGW        P-CSCF     I-CSCF     S-CSCF     HSS
 |            |            |           |          |          |         |
 |========== IPSec Tunnel ============|          |          |         |
 |                                    |          |          |         |
 |--- SIP REGISTER ------------------>|          |          |         |
 |                                    |--- SIP REGISTER -+->|         |
 |                                    |                   |-- Diameter UAR ->|
 |                                    |                   |<-- UAA ----------|
 |                                    |                   |-- assign S-CSCF  |
 |                                    |<-- SIP REGISTER --+---|              |
 |                                    |                              |        |
 |                                    |                              |-- Diameter MAR ->|
 |                                    |                              |<-- MAA ----------|
 |                                    |--- 401 Unauthorized ---------+->|         |
 |<-- 401 Unauthorized ---------------|          |          |         |         |
 |                                    |          |          |         |         |
 | (UE 重新生成鉴权响应 DIGEST)      |          |          |         |         |
 |                                    |          |          |         |         |
 |--- SIP REGISTER (含 Digest) ------>|          |          |         |         |
 |                                    |--- SIP REGISTER -----+--->|  |         |
 |                                    |                              |-- Diameter SAR ->|
 |                                    |                              |<-- SAA ----------|
 |                                    |--- 200 OK -------------------+->|         |
 |<-- 200 OK -------------------------|          |          |         |         |
 |                                    |          |          |         |         |
```

### 4.3 IMS 呼叫建立流程（VoWiFi → VoLTE）

```
UE(A)       ePDG/A      IMS-A       IMS-B       ePDG/B      UE(B)
 |            |           |           |            |          |
 |== IPsec ==|           |           |            |          |
 |                                    |            |          |
 |--- SIP INVITE (SDP offer) -------->|           |          |
 |            |           |-- INVITE -+->|         |          |
 |            |           |           |-- INVITE -+->|== IPsec==|
 |            |           |           |            |-- INVITE->|
 |            |           |           |            |<--180 RING|--|
 |            |           |           |            |          | 振铃
 |            |           |<-- 180 RING------------|          |
 |<-- 180 RING--------------|           |           |         |
 |            |           |           |            |<-- 200 OK---|
 |            |           |<-- 200 OK--------------|           |
 |<-- 200 OK (SDP answer)--|           |           |          |
 |            |           |           |            |          |
 |--- SIP ACK ------------------------>|           |          |
 |            |           |--- ACK ---+->|         |--- ACK ->|
 |            |           |           |            |          |
 |=============== RTP Media Flow (SRTP) ======================|
 |            |           |           |            |          |
 |--- SIP BYE ------------------------>|           |          |
 |            |           |--- BYE ---+->|         |--- BYE ->|
 |<-- 200 OK for BYE ------------------|           |          |
```

## 五、关键标准与规范参考

### 3GPP 规范

| 规范编号 | 标题 | 用途 |
|----------|------|------|
| TS 23.228 | IP Multimedia Subsystem (IMS); Stage 2 | IMS 架构总体规范 |
| TS 23.234 | 3GPP system to WLAN interworking | WLAN 互通系统描述 |
| TS 23.402 | Architecture enhancements for non-3GPP accesses | 非3GPP接入架构增强（VoWiFi核心规范） |
| TS 24.229 | IP multimedia call control based on SIP and SDP | IMS SIP/SDP 协议应用 |
| TS 33.203 | 3GPP security; IMS | IMS 安全架构 |
| TS 33.402 | Security aspects of non-3GPP accesses | 非3GPP接入安全（VoWiFi安全核心规范） |
| TS 24.302 | Access to 3GPP EPC via non-3GPP access networks | 非3GPP接入EPC流程 |
| TS 29.273 | EPC; 3GPP AAA interface | AAA 接口（SWm/SWx/S6b） |
| TS 23.502 | Procedures for 5G System (5GS) | 5G 会话管理流程（含非3GPP接入） |

### GSMA 规范

| 规范编号 | 标题 | 用途 |
|----------|------|------|
| IR.51 | IMS Profile for Voice, Video and SMS over Wi-Fi | VoWiFi UE 和网络能力最小要求集 |
| IR.61 | IMS Profile for Voice, Video and SMS over Wi-Fi for Mission Critical | 关键通信 VoWiFi 配置 |
| TS.63 | UE Wi-Fi Calling Requirements Specification | UE 端 Wi-Fi Calling 需求规范 |

### ETSI 标准

| 标准编号 | 对应 3GPP | 用途 |
|----------|-----------|------|
| ETSI TS 123 234 | TS 23.234 V11.0.0 | WLAN 互通 |
| ETSI TS 123 402 | TS 23.402 | 非3GPP接入架构 |

## 六、VoWiFi 位置信息（Location Information）

VoWiFi 场景下的位置信息比 VoLTE 更复杂，因为 Wi-Fi 接入网无法直接提供类似 3GPP 小区 ID 的精确定位。以下是 VoWiFi 位置信息的核心机制和测试要点。

### 6.1 VoWiFi 位置信息来源

VoWiFi 的位置信息主要来源于以下几个层面：

| 来源 | 机制 | 精度 | 适用场景 |
|------|------|------|---------|
| i-wlan-node-id | Wi-Fi AP MAC 地址（SIP P-Access-Network-Info 头） | AP 覆盖范围（~几十米） | 基本位置参考、紧急呼叫路由 |
| NPLI (Network Provided Location Information) | 核心网通过 PCRF/PCF 提供的网络侧位置 | 动态 | IMS 紧急呼叫、合法监听 |
| LIS (Location Information Server) | HELD 协议查询（HTTP Enabled Location Delivery） | 取决于定位源 | 固定宽带、Wi-Fi 接入 |
| SUPL (Secure User Plane Location) | A-GNSS 辅助定位 | 米级 | 高精度定位需求 |
| UE 提供位置 | 终端 GPS/Wi-Fi 扫描上报 | 米级（GPS）/ ~50m | 紧急呼叫（PIDF-LO） |

### 6.2 P-Access-Network-Info 头中的位置信息

VoWiFi 场景下，UE 在 SIP 消息中携带 `P-Access-Network-Info` 头，该头包含 Wi-Fi 接入网的标识信息。

#### WLAN 场景的 access-type
```
P-Access-Network-Info: "IEEE-802.11" / "IEEE-802.11a" / "IEEE-802.11b" / 
                       "IEEE-802.11g" / "IEEE-802.11n"
```

#### i-wlan-node-id 构造规则
- **值**：Wi-Fi AP MAC 地址的十六进制 ASCII 表示（不含分隔符）
- **示例**：AP MAC = `00-0C-F1-12-60-28` → `i-wlan-node-id = "000cf1126028"`
- **应用**：所有 WLAN 接入场景（不仅限于 I-WLAN）

#### SIP 消息中的完整示例
```
REGISTER sip:ims.mnc001.mcc310.3gppnetwork.org SIP/2.0
P-Access-Network-Info: IEEE-802.11;i-wlan-node-id="000cf1126028"
...
```

### 6.3 Non-3GPP 位置信息上报机制

VoWiFi 中位置信息的特殊挑战在于 Wi-Fi 接入网的动态性：

**ePDG 指派 IP 地址时的位置关联**
- ePDG 在 IKEv2 阶段通过 IKEv2 Configuration Payload (CP) 获取 UE 的 IP 地址
- AAA 服务器在认证过程中可能携带 AP 位置信息（从接入网获取）
- ePDG 可以通过 ALT (Access Location Type) AVP 向 PGW 传递位置信息

**SIP 层面的位置传递**
```
UE → P-CSCF:
  SIP INVITE (P-Access-Network-Info: IEEE-802.11;i-wlan-node-id="XXXXXXXXXXXX")
  
P-CSCF → E-CSCF (紧急呼叫场景):
  根据 P-Access-Network-Info 中的 access-type 判断紧急呼叫类型
  E-CSCF 触发 LRF/RDF 获取位置信息
```

**3GPP 位置上报流程（通过 PCRF/PCF）**
```
SMF → PCF: SMPolicyControl_Create (含 UE 位置)
PCF → AF (IMS): Rx RAR (3GPP-User-Location-Info AVP)
AF → P-CSCF: SIP 消息中携带位置信息
```

### 6.4 NPLI (Network Provided Location Information)

NPLI 是 3GPP 标准化的位置服务机制，用于在 IMS 呼叫中提供网络侧获取的位置信息。

| 规范 | 内容 |
|------|------|
| 3GPP TS 23.167 | IMS 紧急会话位置要求 |
| 3GPP TS 24.229 | SIP 中 P-Access-Network-Info 的使用 |
| 3GPP TS 29.214 | Rx 接口上的位置信息传递 |
| 3GPP TS 29.272 | S6b/SWx 接口的位置信息 |

**NPLI 在 VoWiFi 中的挑战**：
- Wi-Fi 接入网无法提供 3GPP 小区 ID（TAC+ECGI）
- 需要替代定位机制（ePDG 位置、AP MAC、IP 地址地理数据库）
- NPLI 响应时间直接影响紧急呼叫接通速度

### 6.5 VoWiFi 紧急呼叫位置要求

VoWiFi 紧急呼叫涉及的关键网元和位置传递：

```
UE → ePDG → PGW → P-CSCF → E-CSCF → LRF/RDF → PSAP
                         ↕           ↕
                    Emergency Registration   Location Server (GMLC)
                    
位置信息传递链：
1. UE P-Access-Network-Info: i-wlan-node-id (AP MAC)
2. P-CSCF 根据 access-type 检测为紧急呼叫
3. P-CSCF 转发给 E-CSCF（而非 S-CSCF）
4. E-CSCF 查询 LRF/RDF 获取最终位置
5. LRF 通过 SUPL/HELD 等方式获取精确定位
6. 位置信息随 SIP 信令传给 PSAP（PIDF-LO）
```

**紧急注册 vs 正常注册**：
- 已注册 UE：正常 IMS 注册状态，直接发起紧急 INVITE
- 未注册 UE：先进行**紧急注册**（emergency registration），P-Access-Network-Info 必须携带位置信息
- 无 SIM UE：允许未经认证的紧急会话建立（需各国法规支持）

### 6.6 VoWiFi 位置信息测试场景

#### 测试场景 1：P-Access-Network-Info 头验证

**目的**：验证 UE 在 VoWiFi 场景下正确填充 PANI 头

**测试步骤**：
1. UE 连接已知 MAC 地址的 Wi-Fi AP
2. UE 发起 IMS 注册（SIP REGISTER）
3. 抓取 P-CSCF 侧 SIP 消息
4. 验证 `P-Access-Network-Info` 中的 `i-wlan-node-id` 等于 AP MAC（十六进制无分隔符）

**预期结果**：
```
P-Access-Network-Info: IEEE-802.11n;i-wlan-node-id="aabbccddeeff"
```

**失败排查**：
- i-wlan-node-id 为空 → UE 未正确读取 Wi-Fi MAC，需检查 modem 驱动
- access-type 错误 → UE 802.11 协议栈分类错误
- PANI 未被填充 → VoWiFi IMS 设置中位置上报未使能

#### 测试场景 2：VoWiFi 紧急呼叫定位测试

**目的**：验证 VoWiFi 紧急呼叫时 E-CSCF/LRF 正确获取位置并路由到 PSAP

**测试步骤**：
1. UE 通过 Wi-Fi 接入，确保无蜂窝信号
2. 拨打紧急号码（如 911/112）
3. 抓取 P-CSCF → E-CSCF SIP INVITE 消息
4. 验证 E-CSCF 查询 LRF/RDF
5. 验证 PSAP 收到的位置信息正确

**SIP INVITE 紧急呼叫示例**：
```
INVITE sip:911@ims.mnc001.mcc310.3gppnetwork.org SIP/2.0
P-Access-Network-Info: IEEE-802.11;i-wlan-node-id="aabbccddeeff"
Geolocation: <cid:location1@ue>
Geolocation-Routing: yes
Content-Type: multipart/mixed; boundary="boundary1"
--boundary1
Content-Type: application/sdp
...
--boundary1
Content-Type: application/pidf+xml
Content-ID: <location1@ue>
<?xml version="1.0" encoding="UTF-8"?>
<presence xmlns="urn:ietf:params:xml:ns:pidf"
          xmlns:gp="urn:ietf:params:xml:ns:pidf:geopriv10"
          xmlns:ca="urn:ietf:params:xml:ns:pidf:geopriv10:civicAddr">
  <gp:geopriv>
    <gp:location-info>
      <ca:civicAddress>
        <ca:country>CN</ca:country>
        <ca:A1>Jiangsu</ca:A1>
        <ca:A3>Nanjing</ca:A3>
        <ca:RD>Example Road</ca:RD>
        ...
      </ca:civicAddress>
    </gp:location-info>
  </gp:geopriv>
</presence>
```

#### 测试场景 3：不同 Wi-Fi AP 间切换的位置更新

**目的**：验证 UE 在不同 Wi-Fi AP 间切换时正确更新位置信息

**测试步骤**：
1. UE 连接 AP1（MAC: AA:BB:CC:DD:EE:01），发起 VoWiFi 呼叫
2. 保持通话，切换 UE 连接到 AP2（MAC: AA:BB:CC:DD:EE:02）
3. 抓取 SIP re-INVITE 或 UPDATE 消息
4. 验证 PANI 中 i-wlan-node-id 更新为 AP2 的 MAC

**注意**：VoWiFi 切换 AP 可能导致 IPSec 隧道重建，影响通话连续性。

#### 测试场景 4：NPLI 响应时延测试

**目的**：验证网络侧 NPLI 查询时延满足紧急呼叫要求

**测试步骤**：
1. 构造 IMS 紧急呼叫请求
2. 在 P-CSCF/E-CSCF 侧计时：从 SIP INVITE 到 LRF 返回位置信息
3. 验证端到端时延 < 规范要求（通常 < 500ms）

#### 测试场景 5：位置篡改安全测试

**目的**：验证网络侧对 P-Access-Network-Info 头的完整性保护

**参考**：安全研究显示 P-CSCF 只是追加网络标识而非验证已有字段，存在被篡改风险（通过虚假 i-wlan-node-id 伪造位置）

**测试步骤**：
1. 构造 SIP 消息，修改 P-Access-Network-Info 中的 i-wlan-node-id
2. 发送到 P-CSCF
3. 验证 P-CSCF/S-CSCF 是否检测到 PANI 不一致
4. 确认 IPSec 完整性保护下 PANI 未被篡改

### 6.7 相关标准规范

| 规范 | 内容 |
|------|------|
| **3GPP TS 23.167** | IMS 紧急会话（含 I-WLAN 位置处理 Annex B） |
| **3GPP TS 24.229** | SIP P-Access-Network-Info 头的生成和使用 |
| **3GPP TS 24.302** | 非3GPP接入的位置信息上报 |
| **3GPP TS 24.008** | Location Information IE 定义 |
| **RFC 3455 / RFC 7315** | P-Header 扩展（P-Access-Network-Info 语法） |
| **RFC 7913** | P-Access-Network-Info ABNF 更新 |
| **ETSI ES 203 283** | IMS 紧急呼叫位置技术要求 |
| **GSMA NG.115** | P-Access-Network-Info 头中 i-wlan-node-id 规范 |
| **3GPP TS 23.271** | LCS 定位服务架构 |
| **OMA SUPL** | Secure User Plane Location 协议 |
| **IETF HELD (RFC 5985)** | HTTP Enabled Location Delivery |

### 6.8 测试工具与诊断

**SIP 消息抓取与 PANI 分析**：
```bash
# tcpdump 过滤 SIP 信令
tcpdump -i any -s 0 -w vowifi_sip.pcap port 5060 or port 5061

# Wireshark 显示过滤器
sip.P-Access-Network-Info
sip.P-Access-Network-Info && sip.Method == REGISTER
sip.P-Access-Network-Info && sip.Method == INVITE

# 提取 PANI 中的 i-wlan-node-id
tshark -r vowifi_sip.pcap -Y "sip.P-Access-Network-Info" -T fields \
  -e frame.number -e sip.P-Access-Network-Info
```

**UE 侧位置调试**：
```bash
# Android 获取 Wi-Fi 信息
adb shell dumpsys wifi | grep -E "SSID|BSSID"
adb shell dumpsys telephony.registry | grep -A5 "wlan"

# 获取 IMS 注册时的 PANI 值
adb logcat -b radio | grep -i "P-Access-Network-Info"
adb logcat -b radio | grep -i "i-wlan-node-id"

# iOS 现场测试
*3001#12345#* → Serving Cell Info → Wi-Fi Calling
```

**网络侧位置测试**：
```bash
# 检查 ePDG 位置相关配置
openssl s_client -connect <epdg>:443 -servername ss.epdg.epc.mnc<MNC>.mcc<MCC>.pub.3gppnetwork.org

# 验证 PCRF/PCF NPLI 响应
# 在 PCF 侧检查 Rx RAR 中的 3GPP-User-Location-Info AVP
```

## 七、Troubleshooting 指南

### 6.1 常见故障分类

| 分类 | 典型问题 | 根因方向 |
|------|---------|---------|
| 注册失败 | UE 无法注册到 IMS | IPSec 隧道未建立 / IKEv2 协商失败 / SIP 401 鉴权失败 |
| 呼叫失败 | 拨号无音/呼叫立即挂断 | SIP 路由错误 / SDP 协商不匹配 / 媒体面不通 |
| 语音质量差 | 断续/回声/单通 | Wi-Fi 网络抖动/丢包 / IPSec 开销 / 编解码不匹配 |
| 切换失败 | VoWiFi ↔ VoLTE 切换不掉 | ePDG 切换流程异常 / SRVCC 准备失败 |
| 连接断开 | 通话中突然中断 | IPSec DPD 超时 / Wi-Fi 信号弱 / ePDG 会话超时 |

### 6.2 诊断命令与工具

#### 抓包分析
```
# tcpdump 抓取 ePDG 侧的 IKEv2 和 IPSec 流量
tcpdump -i any -s 0 -w vowifi.pcap port 500 or port 4500 or udp

# Wireshark 过滤 VoWiFi 相关包
udp.port == 500    # IKEv2 SA_INIT
udp.port == 4500   # IKEv2 NAT-T
ip.proto == 50     # ESP (IPSec 加密数据)
sip                # SIP 信令
```

#### UE 侧排查
```
# Android ADB 获取 VoWiFi 状态
adb shell dumpsys telephony.registry | grep -i wifi
adb shell dumpsys ims | grep -i vowifi
adb logcat -b radio | grep -i epdg
adb logcat -b radio | grep -i ims

# iOS 现场诊断
*3001#12345#* → Wi-Fi Calling 状态
```

#### 网络侧排查
```
# ePDG 日志检查 IKEv2 协商
# 3GPP AAA 日志检查 EAP-AKA' 认证
# P-CSCF 日志检查 SIP REGISTER 状态

# 关键检查项
ping <epdg_fqdn>                    # ePDG 可达性
nslookup <epdg_fqdn>                # DNS 解析
openssl s_client -connect <epdg>:443 # 证书检查
```

### 6.3 典型故障排查

#### 故障 1：IMS 注册失败（401 持续循环）
- **现象**：UE 反复收到 401 Unauthorized，无法完成注册
- **根因**：
  - SIM 卡/鉴权向量 HSS 与 UE 不匹配
  - S-CSCF 配置的鉴权算法与 UE 不一致
  - P-CSCF 未正确转发 Authorization Header
- **排查**：
  1. 抓取 P-CSCF 侧 SIP 消息，验证 Authorization Digest 参数完整性
  2. 检查 HSS 中用户签约的 IMS 鉴权算法（AKAv1-MD5 / AKAv2）
  3. 确认 IMPI/IMPU 映射正确

#### 故障 2：VoWiFi 呼叫建立后无语音（单通/双不通）
- **现象**：SIP 200 OK 收到但 RTP 媒体流不通
- **根因**：
  - SDP 中 c= 行 IP 地址是 VoLTE PDN 地址，但媒体经 VoWiFi 路径
  - Firewall/NAT 未开放 RTP 端口范围
  - IPSec 未正确路由 RTP 流（TFC/ESP 配置错误）
- **排查**：
  1. 检查 SDP offer/answer 中的 c= 地址和端口
  2. tcpdump 确认 RTP 包是否到达 PGW/IMS
  3. 验证 ePDG 的 ESP 策略是否正确路由媒体面流量

#### 故障 3：Wi-Fi 信号正常但 VoWiFi 图标消失
- **现象**：手机 Wi-Fi 连接正常，但状态栏 VoWiFi/Wi-Fi Calling 图标消失
- **根因**：
  - ePDG FQDN DNS 解析失败
  - IKEv2 UDP 端口（500/4500）被防火墙阻断
  - 运营商侧 ePDG 许可证不足
- **排查**：
  1. 检查 ePDG FQDN 格式：`ss.epdg.epc.mnc<MNC>.mcc<MCC>.pub.3gppnetwork.org`
  2. 确认 UDP 500/4500 端口可达性
  3. UE 端 `adb logcat -b radio | grep -i ke` 查看 IKEv2 错误码

## 七、参考资源链接

### 中文资源
- [CSDN: VoWiFi技术深度解析：架构、流程与演进](https://blog.csdn.net/gou12341234/article/details/149201353)
- [CSDN: VoWiFi 核心网元与信令流程全解析](https://blog.csdn.net/weixin_42531925/article/details/160978107)
- [CSDN: 从ePDG到IMS：VoWiFi核心网元配置与抓包分析指南](https://blog.csdn.net/weixin_42563415/article/details/160972591)
- [CSDN: 理解IMS核心网架构](https://blog.csdn.net/dxpqxb/article/details/107632849)
- [CSDN: 一文读懂SIP协议](https://blog.csdn.net/yugangnj/article/details/157761885)
- [telecomtutorial: VoWiFi Architecture Overview](https://www.telecomtutorial.info/post/02-vowifi-architecture)

### 英文资源
- [GSMA: VoWiFi Networks](https://www.gsma.com/solutions-and-impact/technologies/networks/ip_services/vowifi)
- [Amarisoft: VoWiFi Tutorial (ePDG)](https://tech-academy.amarisoft.com/ePDG_VoWiFi.html)
- [Worth Doing Badly: Learning VoWiFi/VoLTE/IMS](https://worthdoingbadly.com/vowifi)
- [Huawei VoWiFi White Paper](https://carrier.huawei.com/en/technical-topics/core-network/huawei-vowifi-technical-white-paper)
- [Cisco UCC SMF VoWiFi Support](https://www.cisco.com/c/en/us/td/docs/wireless/ucc/smf/2021-01-0/SMF_Config_Admin/b_ucc-5g-smf-config-and-admin-guide_2021-01/b_SMF_chapter_0100000.html)

### 3GPP 规范下载
- https://www.3gpp.org/ftp/Specs/archive/23_series/23.402/
- https://www.3gpp.org/ftp/Specs/archive/33_series/33.402/
- https://www.3gpp.org/ftp/Specs/archive/23_series/23.234/
- https://www.3gpp.org/ftp/Specs/archive/24_series/24.302/

### GitHub 开源项目
- [SWu-IKEv2 (sysmocom)](https://github.com/sysmocom/SWu-IKEv2) - Python IKEv2/EAP-AKA' client
- [awesome-telco](https://github.com/ravens/awesome-telco) - 电信资源合集
- [5G-Repo](https://github.com/shotsan/5G-Repo) - 5G 开源测试床/软件清单
- [Open5GS](https://github.com/open5gs/open5gs) - 开源 5G/4G 核心网（含 ePDG 支持）
- [OAI (OpenAirInterface)](https://openairinterface.org/) - OAI 开源 5G NR/4G LTE 实现

## 八、参考文件

- `references/sip-options.md` — SIP OPTIONS 探测：用途（keepalive/能力探测/健康检查）、tcpdump 命令、Wireshark 过滤表达式、非标准端口识别、生产环境关闭要求
- `references/wireshark-sip-filter.md` — Wireshark SIP 信令抓包过滤表达式

### 工具
- [Wireshark](https://www.wireshark.org/) - SIP/IKEv2/DIAMETER 协议分析
- [sipp](http://sipp.sourceforge.net/) - SIP 协议测试工具
- [StrongSwan](https://www.strongswan.org/) - IKEv2/IPsec VPN 服务器（可用于 ePDG 模拟）
