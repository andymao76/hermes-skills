# 学习入库参考案例（2026-06-28）

本文件记录一次完整的「源材料→分析→KB入库→worklog→日报」工作链。
作为同类任务的格式参考。

---

## 案例1：PCAP学习入库

**源材料**：`/home/andymao/PCAP/5G/js-tel-NGAP.pcap`（2.56MB/14,574包）
**+** `JS-dianxin_use.pcap`（419MB/1,643,579包）

**分析输出**：
- 网络拓扑：AMF 41.163.244.1 + 15个gNB → 突尼斯 Tunisie Telecom
- 协议分布：SCTP 44,716 / 47种 NGAP ProcedureCode
- 主导信令：InitialContextSetupResponse（11,437条，>60%）
- 时间跨度：232秒

**入库路径**：`knowledge/telecom/pcap-analysis/tunisie-telecom-5g-ngap-n2-pcap-analysis.md`

**关联笔记**：[[NGAP信令编码格式]]、[[STCS V2.0 HTTP2 子模块详细设计]]

---

## 案例2：协议规范学习入库

**源材料**：S1AP ASN.1 (3GPP TS 36.413) — 直接从ASN.1源码学习

**分析输出**：
- 14大类IE（Cause/标识符/E-RAB/切换/安全/SON/PWS等）
- CauseRadioNetwork 38种枚举值
- 与NGAP的对比

**入库路径**：`knowledge/telecom/pcap-analysis/s1ap-asn1-ie-definitions.md`

**关联笔记**：[[tunisie-telecom-5g-ngap-n2-pcap-analysis]]

---

## 案例3：工具手册学习入库

**源材料**：tshark man page

**分析输出**：
- 10大模块总结（基础用法/输入输出/抓包控制/过滤器/字段提取/解码重定向/Glossary/统计/输出格式/高级调试）
- 常用命令场景速查表

**入库路径**：`knowledge/telecom/pcap-analysis/tshark-command-reference.md`

**关联笔记**：（可被后续PCAP分析笔记引用）

---

## 案例4：CHM文档学习入库

**源材料**：deelx_zh.zip → deelx_zh.chm（DEELX正则库中文文档）

**处理方式**：`7z x deelx_zh.chm -o/tmp/deelx_zh`

**分析输出**：
- Perl兼容正则引擎、单头文件、模板实现
- 6种匹配模式、无长度限制后顾断言、RIGHTTOLEFT独有模式
- 与5G STCS HTTP2 Path匹配的关联

**入库路径**：`knowledge/telecom/pcap-analysis/deelx-regex-library.md`

**关联笔记**：[[STCS V2.0 HTTP2 子模块详细设计]]

---

## 案例5：设计文档学习入库

**源材料**：STCS V2.0 HTTP2子模块详细设计文档

**分析输出**：
- 架构定位、核心数据结构、二级跨包状态机
- 关键设计决策（不支持动态HPACK字典等）
- 老化策略、帧异常处理

**入库路径**：`knowledge/01_PROJECTS/STCS/stcs-v2-http2-submodule-design.md`

**关联笔记**：[[tunisie-telecom-5g-ngap-n2-pcap-analysis]]

---

## 案例6：在线搜索+OpenAPI研究入库

**源材料**：GitHub(free5gc) + Google搜索 5GC正则表达式

**搜索方法**：
- `web_search_plus` 搜索 3GPP TS 29.571 OpenAPI 规范
- `web_extract_plus` 提取 TS29571_CommonData.yaml 全部 pattern 字段
- `web_search_plus` 搜索 free5gc NRF 源码路径匹配逻辑
- 下载源码文件保存到 `projects/STCS/references/`

**分析输出**：
- 30+ 种 3GPP ID 正则校验模式（SUPI/GPSI/PEI/NF-ID/SUCI 等）
- 13 个 NF API URI 路径模板
- 5GC 正则综合速查表
- free5gc 源码中的 UUID.Parse/Scope 校验等实际代码

**源文件保存**：
```
projects/STCS/references/
├── 3gpp-openapi/
│   └── TS29571_CommonData.yaml   (205KB)
└── free5gc/
    ├── access_token.go           (8KB)
    ├── nf_management.go          (21KB)
    ├── nf_discovery.go           (55KB)
    ├── processor.go              (344B)
    ├── nrf_api/                  (12个 API 客户端文件)
    │   ├── nrf_NFManagement_client.go
    │   ├── nrf_NFManagement_api_nf_instances_store.go
    │   ├── nrf_NFDiscovery_api_nf_instances_store.go  (64KB, 最大)
    │   ├── nrf_AccessToken_api_access_token_request.go
    │   └── ...
    └── models/                   (12个 NRF 模型定义文件)
        ├── model_nrf_nf_management_nf_profile.go  (14KB)
        ├── model_nrf_nf_discovery_nf_profile.go    (12KB)
        ├── model_nrf_access_token_access_token_req.go
        └── ...
```

**GitHub 文件发现技巧**：
- 浏览器访问 `https://github.com/free5gc/nrf/tree/main/internal/sbi/processor` 查看实际文件名
- 用 File Finder (`github.com/.../find/main`) 搜索 nrf 相关文件路径
- openapi 仓库的 models/ 目录是扁平结构（1000+文件），NRF 相关模型以 `model_nrf_*` 命名
- 文件存在但 raw URL 返回 14B(404) → 路径可能已变更，用 browser 确认正确路径

**报告发送**：
- 学习完成后整理 TXT 报告发送飞书
- 使用 Python urllib 直接调用 Feishu API（不依赖 feishu-hermes 桥服务）
- Token 获取+消息发送约 1 秒完成
- 用户 open_id: `ou_a74c0eb0ff0f216d5036c2300a213d22`

**入库路径**：`knowledge/telecom/pcap-analysis/5gc-regex-patterns.md`

**关联笔记**：[[deelx-regex-library]]、[[STCS V2.0 HTTP2 子模块详细设计]]

---

## 案例7：5GC正则全流程详卷入库

**源材料**：本会话前6个案例积累 + 5GC SBI URI 路径分析 + STCS HTTP2 子模块代码 + free5gc 源码

**关键信号**：用户要求"结合流程输出详细的说明文档和使用实例，系统有5G的报文"

**分析输出**：
- 9章34KB 完整文档，从 PCAP 原始字节到正则匹配的完整链路
- 5GC SBI 消息处理流水线（PCAP→TCP重组→HTTP2解析→SBI路由→NF识别→业务处理）
- 正则在6个关键作用点的位置和作用
- 4个真实5G SBI请求示例（NRF注册/发现、AMF上下文、UDM查询）
- STCS `h2_header_parse_path()` 完整 C 代码 + 逐行注释
- free5gc 5 段实际 Go 代码（NF Instance ID校验/SUPI校验/NF类型匹配/NF Profile校验/IP校验）
- 15 个 NF 完整 API 路径→服务名映射表
- 3 个常见信令流程（UE注册/N2切换/PDU会话建立）中的正则应用步骤
- 所有 5GC 标识符正则校验详解（SUPI/SUCI/NF-ID/gNB-ID/PLMN/TAC/SD 等）
- STCS 项目实战：从 PCAP 原始字节到 metadata_req_t 的完整链路
- 4 条 tshark 验证命令

**文档结构**：
```
5gc-regex-flow-guide.md (34KB)
├── 第一章：整体流程概览
├── 第二章：从 PCAP 看正则应用
├── 第三章：STCS HTTP2子模块中的正则匹配
├── 第四章：free5gc 中的正则验证实战
├── 第五章：5GC SBI 正则匹配全场景表
├── 第六章：常见5GC信令流程中的正则应用
├── 第七章：正则表达式在5G数据校验中的详细示例
├── 第八章：STCS项目实战 — 从PCAP到协议解码
└── 第九章：正则在5GC各NF间的流转总结
```

**入库路径**：`knowledge/telecom/pcap-analysis/5gc-regex-flow-guide.md`

**关联笔记**：[[5gc-regex-patterns]]、[[deelx-regex-library]]、[[STCS V2.0 HTTP2 子模块详细设计]]、[[tunisie-telecom-5g-ngap-n2-pcap-analysis]]
