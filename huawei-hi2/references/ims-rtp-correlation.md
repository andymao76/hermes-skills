# HW IMS 监听 RTP 流与 IRI 关联机制

## 关联架构

```
X2 (IRI)                             X3 (CC/RTP)
┌────────────────────┐               ┌────────────────────┐
│ LIID               │───目标级关联──→│ LIID               │
│ communicationId    │───会话级关联──→│ Correlation Number │
│   ├─ callId        │               │ ( = Charging ID    │
│   └─ imsChargingID │               │   或 session ID )  │
│ SIP/SDP 信息       │               │ RTP payload        │
└────────────────────┘               └────────────────────┘
```

## 各关联层面

| 关联层面 | 使用的标识符 | 出现在哪 |
|---------|-------------|---------|
| 目标匹配 | **LIID** | X2 + X3 |
| 会话匹配 | **Correlation Number (= Charging ID)** | X3 头 |
| IRI 间关联 | **imsChargingID** | X2 IRI 内 |
| 媒体流解码 | SIP SDP（IP/端口/编解码） | X2 IRI 内 |

## 详细说明

### ① 目标级关联 — LIID
- X2 IRI 和 X3 CC 都携带 `lawfulInterceptionIdentifier (LIID)`
- LEMF 用 LIID 把同一个目标的所有 IRI 和 CC 归到一起

### ② 会话级关联 — communicationIdentifier ↔ Correlation Number
- X2 IRI 中 `communicationIdentifier` 携带 `imsChargingID`
- X3 IP 分组数据模式的消息头中携带 **Correlation Number**
- HW 文档定义：Correlation Number 为 P-GW/GGSN 分配的 **Charging ID**
- LEMF 用 Correlation Number 把 X3 RTP 流匹配到具体的 X2 IRI 会话

### ③ SIP 会话内关联 — imsChargingID
- `imsChargingID` 来自 SIP 的 `P-Charging-Vector` 头
- 一个 IMS 会话内所有网元（P-CSCF/S-CSCF/AS）生成的 charging ID 相同
- 用于在 X2 侧把同一会话的多个 IRI 报告（如 INVITE、183、200 OK）关联起来
- 不直接出现在 X3 头中

## 完整关联链路（LEMF 侧）

1. LIID 筛选目标
2. X3 头的 Correlation Number（= Charging ID）匹配 X2 IRI 中的 `imsChargingID`
3. X2 IRI 中的 SDP 信息（IP:端口、编解码）对应到具体的 RTP 流

## 参考标准

- 3GPP TS 33.108 Annex — IMS IRI 与 GSN CC 关联指南
- 华为 CS_LI 协议标准 §3.2.47 imsChargingID
- X3 14字节固定头格式（0xAA 同步字节 + 版本 + 长度 + 保留）

## LI ASN.1 解码工具

本地 `~/LI/software/000000app_v1/` 有一个 ASN.1 BER 解码 Web 工具（Flask + dpkt + asn1tools）：
- 支持华为 CS/IMS、中兴 CS、Mavenir、G2K 等厂商协议解码
- 20 个 HI2/X2 ASN.1 规范文件
- 分析笔记：`knowledge/telecom/lawful_interception/LI_ASN1解码工具_000000app_v1分析.md`
