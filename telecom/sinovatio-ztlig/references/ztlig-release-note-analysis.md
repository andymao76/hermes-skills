# ZTLIG 版本发放说明对比分析 — 案例：WLAN IP 缺失问题 vs T23

## 背景

2026-06-25，Sinovatio 发布了 `LISTENER V1.1.02_TMC_T23` 版本，声称修复了已知问题。现场反馈："根据反馈，已经修改软件版本"。需要验证该版本是否修复了 OWLS 不显示 WLAN UE 本地 IP 的问题。

## 已知问题根因

VoWiFi 通话的 P-Access-Network-Info SIP 头中包含 `Wlan-ue-local-ip=196.202.142.135`，但 OWLS 页面不显示该字段。

**数据链路：**
```
P-CSCF (SIP) → ZTLIG2/SSF (解析) → Kafka (LigCdr JSON) → flink → OWLS (展示)
                                                                ↑
                                          字段在此环节缺失——LigCdr JSON schema
                                          未定义 Wlan-ue-local-ip
```

**根因：** 不是软件版本 bug，而是数据模型缺陷 — LigCdr JSON schema 缺少 WlanUeLocalIp 字段，HI2 X2 IRI 中的深层 SIP 头部未被 ZTLIG2/SSF 提取到 Kafka 消息中。

## 版本发放说明分析

### 文件信息
- 文件名：`LISTENER V1.1.02_TMC_T23版本发放说明.md`
- 拟制日期：2026.06.25
- 版本路径：`V1.1.0.2_T22 → V1.1.0.2_T23`
- 升级模块：flink-tmc-1.0.0.tar
- 包名：`DIA_V1.0.0_L_ISTENER_DataIngestionAnalysis_T1_B28_20260625114300_high.tar.gz`

### 6 步对比结果

| # | 维度 | 发现 | 结论 |
|:-:|------|------|:----:|
| 1 | **新增功能** (§3.1) | 唯一修复："事件无位置信息时导致位置回填失败事件5丢失问题修复" | ❌ 描述不匹配 — 我们的问题是字段缺失，不是事件丢失 |
| 2 | **涉及模块** (§7) | 升级 flink-tmc（位置回填模块） | ❌ 模块不匹配 — 根因在 ZTLIG2/SSF 采集层 |
| 3 | **故障清单** (§4) | 表格为空，无故障编号 | ❌ 无针对现场报告的专项修复 |
| 4 | **根因层级** | flink 后端无法补回采集层丢弃的字段 | ❌ 数据管道断层问题 |
| 5 | **升级范围** | 仅 flink-tmc 配置覆盖 + 进程重启 | ❌ ZTLIG2/SSF 未涉及 |
| 6 | **交叉验证** | 20260630 PCAP 仍无 WLAN IP 在 OWLS 中 | ❌ 确认未修复 |

### 结论

**LISTENER V1.1.02_TMC_T23 未修复 WLAN IP 缺失问题。**

该版本仅修复了 flink-tmc 的"事件无位置信息时导致位置回填失败事件5丢失"问题，这是一个不相关的故障。WLAN IP 缺失问题的根因在 ZTLIG2 或 SSF 的 Kafka 消息生成层，需要修改数据管道在输出 CDR 时增加 WlanUeLocalIp 字段。

## 修复该问题需要的方案

| 方案 | 涉及模块 | 复杂度 | 说明 |
|------|---------|:------:|------|
| **方案一（推荐）** | ZTLIG2 或 SSF | 中 | 修改解析逻辑，从 SIP PANI 头提取 Wlan-ue-local-ip 到 Kafka CDR |
| 方案二（治标） | OWLS 层 | 低 | 从原始 X2 消息回捞——但需保留原始消息流 |
| 方案三（治本） | flink-tmc→OWLS | 高 | 全链路增加字段定义，涉及 Kafka schema 升级 |

## 下次版本复审重点

当收到新版本时，检查：
1. 升级模块是否包含 **ztlig2** 或 **ssf** 二进制更新
2. 发放说明的故障清单是否有关于 **VoWiFi** / **WLAN** / **P-Access-Network-Info** / **WlanUeLocalIp** 的条目
3. §3.1 新增功能中是否有与 **SIP PANI 头解析**或 **Kafka CDR 字段扩展**相关的描述
