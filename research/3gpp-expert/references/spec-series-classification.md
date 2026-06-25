# 3GPP SPEC 系列分类体系与 SVC/IMS/VoLTE/VoNR 优先级

> 来源：telecom/3gpp/spec-series-classification-and-svc-learning-roadmap.md

## 系列速查表

| 系列 | 用途 | 对 SVC 重要性 | 典型 SPEC |
|------|------|:--:|-----------|
| 21 | 总体框架 / 术语 / Release 定义 | ⭐ | 21.101, 21.900 |
| 22 | 业务需求（Stage 1） | ⭐⭐ | 22.101 VoNR, 22.228 |
| 23 | **系统架构（Stage 2）— IMS/5GC** | ⭐⭐⭐⭐⭐ | 23.501, 23.502, 23.228, 23.292, 23.203 |
| 24 | **协议细节（Stage 3）— SIP/NAS** | ⭐⭐⭐⭐⭐ | 24.229, 24.501, 24.008 |
| 25 | 3G UTRAN（基本冻结） | ⭐ | — |
| 26 | **编解码（AMR/EVS）** | ⭐⭐⭐⭐ | 26.114, 26.445 (EVS) |
| 27 | 数据 / SIM / AT 命令 | ⭐⭐ | 27.007, 27.010 |
| 28 | OAM / 网管 | ⭐ | — |
| 29 | **核心网接口（Diameter/SBI/HTTP2）** | ⭐⭐⭐⭐ | 29.500–29.502, 29.228, 29.229 |
| 31 | SIM/UICC 安全与文件结构 | ⭐ | — |
| 32 | 计费 / 统计 / OAM | ⭐⭐ | CDR 格式、KPIs |
| 33 | 安全（IMS/5G AKA） | ⭐⭐⭐ | 33.203, 33.501 |
| 34 | UE 射频一致性测试 | ⭐ | — |
| 35 | 加密算法（MILENAGE/SNOW/ZUC） | ⭐ | — |
| 36 | LTE RAN (E-UTRA/EPC) | ⭐⭐ | 36.331 RRC, 36.300 |
| 37 | 多无线共存 / 定位 | ⭐ | — |
| 38 | 5G NR RAN | ⭐⭐ | 38.331 RRC, 38.300 |
| 41 | eV2X / 车联网 | — | — |
| 42 | 服务能力 / 网络切片 | ⭐ | — |
| 43 | WLAN 互通 | ⭐ | — |
| 44+ | GERAN / 终端测试 / BSS / IoT / NB-IoT | — | — |

> 关键规律：SVC 的核心在 **23 系列（架构）+ 24 系列（协议）+ 29 系列（接口）+ 26 系列（编解码）**

## SVC 核心 SPEC 优先级

### Tier 1 — 必须掌握

| SPEC | 内容 | 说明 |
|------|------|------|
| **23.228** | IMS 总体架构 | SVC 的核心架构文档，P/I/S-CSCF、HSS/UDM、AS、BGCF、MGCF |
| **24.229** | IMS SIP 协议 + SDP | 圣经级文档 — REGISTER、INVITE、PRACK、UPDATE、BYE 所有流程 |
| **23.501** | 5GC 总体架构 | AMF/SMF/UPF/PCF，VoNR 基础 |
| **23.502** | 5GC 程序流程 | Registration、PDU Session、EPS-FB / RAT-FB |
| **23.292 / 24.292** | SVC/ICS 业务集中 | SCC AS 逻辑、单端/双端漫游、T-ADS |
| **23.203** | PCC（QoS/策略控制） | IMS 话音带宽保障，QCI/GBR/IMS APN |

### Tier 2 — 工程常用

| SPEC | 内容 |
|------|------|
| **24.501** | 5G NAS（EPS Fallback 关键） |
| **26.114** | IMS 语音终端要求（VoLTE/VoNR） |
| **26.445** | EVS 编解码（VoLTE/VoNR 主编码） |
| **29.500 / 29.502** | 5GC SBA HTTP2/JSON 接口基础 |
| **29.228 / 29.229** | Cx/Dx（IMS-HSS/UDM）、Sh（UDR/IMS） |
| **23.218** | 业务路由、iFC 初始过滤规则 |
| **33.203** | IMS 安全（AKA/SIP Digest） |
| **33.501** | 5G 核心安全 |

### Tier 3 — 参考级

| SPEC | 内容 |
|------|------|
| **23.401** | EPC 架构（VoLTE 前提） |
| **24.301** | LTE NAS（Attach/TAU/ESM） |
| **29.212 / 29.213 / 29.214** | PCRF/PCEF/SPR |
| **23.216** | SRVCC（VoLTE/VoNR → CS 回落） |
| **36.331 / 38.331** | LTE/NR RRC（SRVCC/Fallback 关键） |

## 5 阶段学习路线图

1. **阶段 1 — 基础架构**：23.228 (IMS) + 23.401/23.501 (EPC/5GC) + 23.218 (iFC)
2. **阶段 2 — SIP 协议**：24.229（REGISTER/INVITE/UPDATE/PRACK/BYE + SDP）
3. **阶段 3 — VoLTE 流程**：23.203 (PCC/QoS) + 24.301 (NAS) + SRVCC
4. **阶段 4 — SVC/ICS**：23.292 + 24.292（SCC AS/T-ADS/漫游保持）
5. **阶段 5 — VoNR**：23.502 + 24.501 + EPS Fallback

## VoLTE/VoNR 学习流程清单

- IMS Registration（最重要）
- P-CSCF 分配流程
- MO/MT VoLTE SIP INVITE 流程
- PRACK / UPDATE（非对称 SDP）
- SDP negotiate（AMR/EVS 编解码）
- RTP 建立与 One-way 音问题
- Dedicated Bearer activation (IMS 专用 QoS)
- SRVCC (23.216)
- 5G Registration + PDU Session + IMS over 5G
- VoNR MO/MT 呼叫流程
- VoNR → VoLTE fallback (EPS FB / RAT FB)
