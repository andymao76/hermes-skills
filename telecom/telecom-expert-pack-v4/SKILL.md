---
name: telecom-expert-pack-v4
version: "4.0"
category: telecom
description: 电信专家知识库完整包 — SIP 200+场景/Diameter/GTP/PFCP/NGAP/NAS/Wireshark Filter/VoLTE/VoNR Call Flow/Huawei ZTE LI全字段/HDP大数据运维
target: telecom_network_ops
language: zh-CN
---

# Telecom Expert Pack Enterprise v4.0

## 触发条件

当用户提出以下问题时，应加载此 skill：
- SIP 协议相关问题（呼叫流程、头域、响应码）
- Diameter 协议（命令码、AVP、接口流程）
- GTPv2-C / PFCP 协议（消息类型、IE 字段）
- NGAP / NAS（5GMM/5GSM/EMM/ESM）过程
- 5G 协议解码器测试（PCAP 验证、NEA1/2/3 加解密集成）
- VoLTE / VoNR 信令流程（IMS 注册、EPS Fallback、SRVCC、CSFB）
- Wireshark 过滤器（SIP/Diameter/GTP/PFCP/NGAP/NAS/RTP）
- 华为 / ZTE LI 字段字典（X1/X2/X3、AA Header、BER/TLV）
- HDP 3.1 大数据运维（Kafka/Flink/Hive/HBase/ES）

## 文件索引

知识库位置：`知识/电信专家包v4/`

| 文件 | 行数 | 用途 |
|------|------|------|
| `sip_call_scenarios.md` | 1,735 | 40+ 完整ASCII信令流程图，15种SIP方法 |
| `diameter_message_library.md` | 1,363 | S6a/Gx/Gy/Gz/Rx/Cx/Sh 命令码+AVP |
| `gtp_pfcp_message_library.md` | 879 | GTPv1-U/GTPv2-C/PFCP 消息+Cause+IE |
| `ngap_nas_message_library.md` | 994 | NGAP+5GMM/5GSM+EMM/ESM 过程 |
| `volte_vonr_call_flow.md` | 700 | VoLTE/VoNR 完整信令图集 |
| `wireshark_filter_handbook.md` | 1,234 | Display/Capture Filter + 着色规则 |
| `huawei_zte_li_dictionary.md` | 1,113 | X1/X2/X3 字段 + ETSI↔厂商映射 |
| `bigdata_runbook.md` | 1,312 | HDP 3.1 全组件运维命令|

### 支持文件

| 文件 | 用途 |
|------|------|
| `references/chm-extraction-workflow.md` | CHM 文档 → Markdown 提取入库工作流（7z + pandoc，含批量脚本模板） |
| `references/5g-protocol-decoder-testing.md` | 5G 协议解码器测试方法 — CryptoMobile 集成、PCAP 测试、NGAP PER 编码限界 |

### 补充参考文件（中文版，知识库 `知识/telecom/`）

| 文件 | 行数 | 用途 | 差异 |
|------|------|------|------|
| `Diameter完整消息库速查手册.md` | 1,495 | S6a/Gx/Gy/Gz/Rx/Cx/Sh/St/DOIC 完整命令码+AVP+12章 | 含DOIC、SGs、附录App-ID表 |
| `GTP_PFCP完整消息库速查手册.md` | 1,289 | GTPv1-U/GTPv2-C/PFCP 消息+IE+规则+6流程图 | 更详细PFCP规则结构(PDR/FAR/URR/QER/BAR/MAR)、6流程 |

> 技能 linked files 中 `references/` 目录有对应摘要说明文件。

## 快速参考

| 现象 | 查哪个文件 | 关键章节 |
|------|-----------|---------|
| 5G 协议解码器测试 / CryptoMobile 集成 | `references/5g-protocol-decoder-testing.md` | NEA1/2/3 集成方法、NGAP PER 解码限界 |
| VoLTE 打不通 | `volte_vonr_call_flow.md` | 注册/呼叫流程 |
| LTE 附着失败 | `ngap_nas_message_library.md` | EMM Cause 字典 |
| SIP 呼叫异常 | `sip_call_scenarios.md` | 失败场景/响应码 |
| Diameter 超时 | `diameter_message_library.md` | Result-Code / 各接口流程 |
| PFCP 会话失败 | `gtp_pfcp_message_library.md` | PFCP Cause / Session流程 |
| Wireshark 抓包分析 | `wireshark_filter_handbook.md` | 综合场景 |
| LI 上报字段异常 | `huawei_zte_li_dictionary.md` | X2 IRI / ETSI↔厂商映射 |
| Kafka 消费堆积 | `bigdata_runbook.md` | Kafka 运维 |

### Wireshark 端口速查
- SIP: 5060/5061 (TCP/UDP)
- Diameter: 3868 (TCP/SCTP)
- GTPv1-U: 2152 (UDP)
- GTPv2-C: 2123 (UDP)
- PFCP: 8805 (UDP)
- S1AP/NGAP: 36412/38412 (SCTP)
- RTP: 动态端口 (10k-60k)

### 3GPP Cause 值速查
- EMM Cause #3: Illegal UE
- EMM Cause #6: Illegal ME
- 5GMM Cause #3: Illegal UE
- 5GSM Cause #8: Operator Determined Barring
- GTP-C Cause 16: Context Not Found
- PFCP Cause 3: Request Rejected
- NGAP Cause: RadioNetwork/Transport/Protocol/Misc

## 来源 3GPP 规范

TS 23.002/401/501 | TS 33.107/108/126 | TS 24.229/301/501 | TS 29.212/214/229/244/272/274/281/328 | TS 38.413 | ETSI TS 101 671 | RFC 3261/3665/5359/6733/4006

## 相关技能

- `telecom-core`: 2G→5G 核心网架构基础
- `hw-li`: 华为 LI 深度
- `zte-li`: Sinovatio ZTLIG 运维
- `li-system-ops`: LI 系统全栈运维
- `a1-project-sudan-li`: 北苏丹 A1 项目
- `wireshark-lua`: Wireshark Lua 插件开发
- `hdfs-expert` / `yarn-expert` / `kafka-ops-expert` / `flink-sre-expert` / `hive-expert` / `hbase-ops` / `elasticsearch-ops`: 大数据运维
