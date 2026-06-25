# ETSI / 3GPP 合法监听标准体系总览

来源：`~/knowledge/research/ETSI_3GPP_Lawful_Intercept_Standards.md`
整理日期：2025-06-02，导入知识库：2026-06-09

## 核心标准映射

### 3GPP SA3-LI

| 标准 | 内容 | 备注 |
|------|------|------|
| TS 33.126 | LI 需求 (Requirements) | 5G 新一代 |
| TS 33.127 | LI 架构与功能 (Architecture & Functions) | 5G 新一代 |
| TS 33.128 | LI 协议与流程 (Protocols & Procedures, Stage 3) | **5G HI2/HI3 委托 ETSI TS 102 232-7** |
| TS 33.129-1/-2 | LI 功能安全保障 | Active |
| TS 33.106 | 旧版 LI 需求 | 2G/3G/4G |
| TS 33.107 | 旧版 LI 架构 | 2G/3G/4G |
| TS 33.108 | 旧版 HI 接口 | 2G/3G/4G |

### ETSI TC LI

| 标准 | 内容 |
|------|------|
| TS 102 232-1 | 通用部分：LI 架构、PDU 格式、ASN.1 编码（V3.33.1 2025-04） |
| TS 102 232-2 | 消息服务（Email） |
| TS 102 232-3 | IP 服务（固定宽带、WiFi） |
| TS 102 232-4 | 二层网络服务 |
| TS 102 232-5 | 多媒体服务（SIP/RTP, VoLTE, VoWiFi, RCS, IMS） |
| TS 102 232-6 | PSTN/ISDN 电路域 |
| TS 102 232-7 | **移动网络：2G/3G/4G/5G，5G 唯一交付机制** |
| TS 103 221 | 内部 X 接口（X1/X2/X3） |
| TS 101 671 | 旧版电路交换 HI（已被 102 232-6 包裹） |

### X 接口定义

| 接口 | 说明 |
|------|------|
| X1 | LIPF ↔ POI/TF 管理/配置 |
| X2 | POI ↔ MDF2 IRI 传输 |
| X3 | POI ↔ MDF3 CC（通信内容）传输 |

5G 之前 X2/X3 为厂家私有实现，5G 引入标准化。

## 架构实体

| 实体 | 作用 |
|------|------|
| LEA | 执法机构 |
| LEMF | 执法监控设施 |
| MDF2 | 中介和交付功能 (IRI) |
| MDF3 | 中介和交付功能 (CC) |
| POI | 拦截点 |
| TF | 触发功能 |
| ADMF | 管理功能 |
| LIPF | LI 配置功能 |
| SIRF | 系统信息检索功能 |

## 用户关注点

- 对三家厂商（HW/中兴/爱立信）X1 接口实现差异感兴趣
- 要求准确到字节级，偏好表格 + HEX 码流 + ASN.1 PER 编码分析
- 厌恶行业常识错误和模糊概括
- 百度网盘中有 85 份 LI 相关文档（含 HW/ZTE 的 ETSI 接口实现 PDF）
