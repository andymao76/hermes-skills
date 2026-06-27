---
name: etsi-lawful-intercept
description: "ETSI 合法监听(LI)标准体系专家。涵盖 TC LI 技术委员会、TS 102 232 交付接口(7部分)、HI1/HI2/HI3 三大接口、X1/X2/X3 内部接口、ASN.1 编码、5G LI 演进(TS 33.128)、留存数据(TS 102 657)、传统监听(TS 101 671)、以及 ETSI LI 卡片生成。当用户提及 lawful intercept、合法监听、LI、ETSI TS 102 232、HI2、HI3、IRI、CC、X1/X2/X3、LEMF、Mediation Function、CSP 监听义务、3GPP TS 33.128、5G LI、手绘信息、华为LI协议、中兴LIG、ZTLIG、OWLS、TMC、LJ平台、SOSM、LICI、CSPETL、SSF日志、RVF日志、X接口日志分析 时触发。也覆盖 Visio (.vsd) 和 XMind (.xmind) 文件中 LI 流程图的解析和知识导入。"
version: 1.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [etsi, lawful-intercept, telecom-security, 5G, standards]
    related_skills: [3gpp-expert, asn1-codec, self-learning]
    config:
      - key: etsi_li.output_dir
        description: "ETSI LI 卡片图片输出目录"
        prompt: "ETSI LI 卡片图片保存目录"
        default: "/home/andymao/"
---

# ETSI Lawful Interception (LI) 标准体系

ETSI 合法监听标准专家。熟悉 TC LI 技术委员会全系列标准，包括交付接口（HI1/HI2/HI3）、内部接口（X1/X2/X3）、ASN.1 PDU 编码、5G 监听架构演进。

---

## 一、TC LI 技术委员会

ETSI 下设 **TC LI**（Technical Committee Lawful Interception）技术委员会，负责制定合法监听及数据披露的国际标准。标准已被全球各国广泛采纳，成为事实上的行业基准。

覆盖范围：
- 交付接口（Handover Interface）
- 令状交换（Warrant Exchange）
- 内部拦截接口（Internal Interception）
- 留存数据（Retained Data）

---

## 二、核心标准三层架构

```
Step 1: TS 101 331 — LEA 需求规范
         Law Enforcement Agency 对 LI 系统的功能需求

Step 2: TS 102 232 — 交付接口规范（7部分）
         标准化的 HI2/HI3 接口，ASN.1 编码 + TLS

Step 3: TS 101 671 — 传统电路交换接口（已标记 Legacy）
```

---

## 三、三大交付接口（HI1 / HI2 / HI3）

| 接口 | 名称 | 说明 | 标准 |
|------|------|------|------|
| **HI1** | 行政接口 | 令状下发、激活、暂停、终止、审计 | TS 103 120 |
| **HI2** | 信令接口 | 拦截相关信息（IRI）— 谁、何时、何地 | TS 102 232 |
| **HI3** | 内容接口 | 通信内容（CC）— 语音、数据、消息 | TS 102 232 |

**传输机制：**
- HI2/HI3 使用 **ASN.1 PER 编码**（Packed Encoding Rules）
- 通过 **HI2 PDU** 和 **HI3 PDU** 传输
- 双向 TLS 认证保护
- 由 Mediation Function 在 CSP 网络和 LEMF 之间桥接

---

## 四、TS 102 232 系列详解（7部分）

> 每个 Part 的独立版本号和最新状态见 `skill_view("etsi-lawful-intercept", "references/versions.md")`

| 部分 | 内容 | 覆盖场景 |
|------|------|----------|
| Part 1 | 通用架构、PDU 格式、ASN.1 编码定义 | 框架性规范 |
| Part 2 | 邮件消息服务 | POP3 / IMAP / SMTP |
| Part 3 | IP 承载服务 | 固定宽带、WiFi |
| Part 4 | 二层网络服务 | L2 VPN / 以太网 |
| Part 5 | 多媒体服务 | SIP / RTP / MSRP / IMS / VoLTE |
| Part 6 | 传统 PSTN/ISDN | 电路交换监听 |
| Part 7 | 移动网络 | 2G / 3G / 4G / 5G |

**关键版本：**
- V3.x 系列为当前主流版本
- Part 1 当前版本 V3.28.1（2023+）
- 每个 Part 独立演进版本号

---

## 五、内部接口标准化（X1 / X2 / X3）

**TS 103 221** 定义了 5G 时代标准化的 X1/X2/X3 接口：

| 接口 | 方向 | 描述 | 推荐编码 |
|------|------|------|----------|
| **X1** | LIPF ↔ POI/TF/MDF | LI 系统对 Network Function 配置监听任务 | XML/SOAP 或厂商私有 |
| **X2** | POI → MDF2 | 传输拦截信令（xIRI） | TLV |
| **X3** | POI → MDF3 | 传输拦截内容（xCC），高性能优化 | TLV |

**重要：X1 是 CSP 内部的管理接口，不在 TS 33.108 范围内。** TS 33.108 定义的是 HI1/HI2/HI3（Handover Interface，CSP → LEMF 的交付接口）。TS 33.127 第 5.4.4 节定义了 **LI_X1**（LIPF↔POI/TF/MDF 四个子接口：LI_X1_1~LI_X1_4）的功能语义，但**不规定传输协议**——这是厂商之间的最大差异。

### 四家厂商 X1 实现对比

3GPP 标准只定义"激活/去激活/修改拦截任务"的功能语义，传输层完全开放：

| 维度 | 华为 (Huawei) | 中兴 (ZTE) | 爱立信 (Ericsson) | UTIMACO |
|------|--------------|------------|------------------|---------|
| **定位** | CSP 网元+LI 网关一体 | CSP 网元+IIF 模块 | CSP 网元+SOAP 服务 | 第三方 LI 中介设备 |
| **X1 传输协议** | TCP 私有二进制 | IIF + CORBA/SNMP/MML | SOAP/XML over HTTP | 标准 ETSI HI 转换 |
| **X1 本质** | LIG↔NE 独立二进制通道 | NE 内部 IIF 模块 | ADMF↔NE XML 交换 | 多厂商统一转 HI |
| **帧头** | 14字节/8字节，前导 `0xAA` | CORBA GIOP 消息头 | HTTP + SOAP Envelope | 取决于对接厂商 |
| **数据编码** | C 结构体 / ASN.1 PER | NE 内部自有格式 | XML 文档 | ASN.1 PER（标准） |
| **接口标准** | 语义符合 TS 33.108，传输私有 | 语义通过 IIF 实现 | XML 映射 ASN.1 语义 | TS 102 232 完整实现 |

### 关键澄清

- **TS 33.108 定义的是 HI（Handover Interface），不是 X1。** X1 是 CSP 内部的厂商私有接口，3GPP 标准只管从 ADMF/DF 向 LEMF 送数据的那一段。  
- **华为**：私有 TCP 二进制协议，随 NGN 时代（2003年）延续至今。详见 `~/knowledge/baidu-netdisk/parsed/LI-HW.md` 和 `HW_NGN_X1X2.md`。
  - X1 通道：TCP/IP 双向通道，网元是服务器，LIG 是客户端。X1Handshake 永久维护会话。并发≤5。非法码流丢弃。5 秒超时。
  - LIID：拦截目标唯一 ID = lawfulInterceptionIdentifier。ASCII，1~65535。子地址模式仅数字。
  - NEID 错误 → RC 9。对接核对用户名/密码/NEID。
  - 设控号码：GMSC(ISDN)→ISDN，其他→MSISDN。原因：它国号码无法在本网分析为 MSISDN。
  - SpeechOutputMode：缺省 combinedOptionB(0) = ACCESS NUMBER。
  - **X2/X3 关联**：CS(M3UA) 模式通过 ISUP 消息关联。SIP-I 模式必须在 SIP INVITE 的 ISUP 部分携带 Access Transport 传递 LIID+CIN（application 消息关联）。TX/RX 分离模式下用 LIID+CIN+Direction 确定拦截方。
  - **SIP-I LIG 处理流程**：NE 与 SSF 建链（SSF 不向网元注册SIP）→ ISUP 层带 LIID+CIN → SDP 获取 RVF IP+PORT → 发送 RTP。对接检查 MGW/SBC 连通性和防火墙端口。
  - **X3 信号传输**：TMD(传统)→ISUP；当前主流→IP + M3UA。
  - 华为 X1 错误排查：认证失败→alarm-id=504；X1 中断→alarm-id=512。过滤 X2 端口可查看 NE 错误信息。
- **中兴**：通过 **IIF（Internal Interception Function）** 模块接收 CORBA/SNMP/MML 命令，NE 内部拦截。
- **爱立信**：构建 **XML 消息**，通过 SOAP/HTTP 发送给 NE 的 LI 服务端口。与 5GC SBA 的 HTTP/REST 技术栈一致。
- **UTIMACO**：第三方 LI 中介设备，专长于将多厂商私有 X1/X2/X3 转换为标准 ETSI HI1/HI2/HI3 接口，对接 LEMF。典型应用场景：CSP 同时部署华为/ZTE/爱立信三种网元时，用 UTIMACO LI 网关统一管理。
- **5G 选择**：爱立信随 5GC SBA 全面转向 SOAP/HTTP，华为仍沿用私有 TCP 协议，UTIMACO 作为中间层适配任意厂商。

### 四家厂商对比速查表

| 场景 | 华为 | 中兴 | 爱立信 | UTIMACO |
|------|------|------|--------|---------|
| X1 管理面 | M2000（私有TCP） | NetNumen（CORBA/MML） | ENM（SOAP/HTTP） | 统一北向 HI1 转换 |
| X2 信令面 | LIG 的 X2 通道 | IIF→HI2 映射 | EIP 的 IRI 交付 | 中间件转换 |
| X3 用户面 | LIG 的 X3 通道 | IIF→HI3 映射 | EIP 的 CC 交付 | 中间件转换 |
| LI 网关产品 | LIG (Lawful Interception Gateway) | ZTLIG (Sinovatio LIG) | EIP (Ericsson Interception Platform) | Utimaco LI Platform |

### 5G 演进

- **X1/X2/X3 标准化接口** 已成为 5G LI 架构核心
- **TS 102 232-7** 是 5G 唯一的交付机制
- IRI/CC 载荷定义在 **3GPP TS 33.128**（安全架构和 LI 规范）
- 标准化接口使 NF（AMF/SMF/UPF 等）与 LI 系统可独立开发

---

## 六、留存数据（Retained Data）

| 标准 | 说明 |
|------|------|
| **TS 102 657** | 数据留存接口规范 |
| **HI-A** | LEA 向 CSP 提交数据留存请求 |
| **HI-B** | CSP 向 LEA 交付留存数据 |

---

## 七、传统监听标准

| 标准 | 说明 |
|------|------|
| **TS 101 671** | 传统电路交换监听接口（PSTN/ISDN） |
| 状态：**Legacy** | 已被 TS 102 232-6 逐步取代 |

---

## 八、5G 监听架构演进

- **X1/X2/X3 标准化接口** 已成为 5G LI 架构核心
- **TS 102 232-7** 是 5G 唯一的交付机制
- IRI/CC 载荷定义在 **3GPP TS 33.128**（安全架构和 LI 规范）
- 标准化接口使 NF（AMF/SMF/UPF 等）与 LI 系统可独立开发

**5G LI 关键变化：**
- 从 4G 的 S-GW/P-GW 集中式拦截 → 5G 支持分布式 UPF 拦截
- 网络切片（Network Slicing）带来新的 LI 挑战
- MEC（Multi-access Edge Computing）需要本地疏导场景下的监听

> 详见知识库：`~/knowledge/telecom/lawful_interception/5g-li-standards-evolution.md`
> 包含 3GPP SA3-LI 规范体系 (TS 33.126/127/128)、ETSI TC-LI 标准族、X1/X2/X3 标准化接口详解、5G LI 与 4G 的全面对比

---

## 九、参考文献引用

本 skill 附有以下支持文件：
- `references/versions.md` — 各标准最新版本号及查询方式
- `self-learning` 关联 skill：`/learn ETSI TS 102 232 latest version` 追踪标准更新

## 十、生成 ETSI LI 卡片

可用以下命令生成 ETSI 标准体系图文长图：

```bash
~/.hermes/scripts/etsi-li-card.py
```

输出文件：`/home/andymao/etsi-li-standards.png`

卡片内容包含：
- TC LI 技术委员会概述
- 核心标准三层架构
- HI1/HI2/HI3 三大交付接口
- TS 102 232 系列 7 部分详解
- X1/X2/X3 内部接口
- 留存数据与传统标准
- 5G 时代演进

## Related Skills

- **3gpp-expert** — 3GPP 全栈通信专家（2G→6G），覆盖 TS 23/24/25/36/38 系列、RAN/NAS/RRC 协议栈。对于 5G RAN/RRC/NAS 层级的问题需协作。
- **asn1-codec** — ASN.1 BER/PER 编解码工具，用于 HI2/HI3 PDU 的底层编码分析。ETSI LI 的核心编码规则是 ASN.1 PER Unaligned，详细 TLV/PER 结构见该 skill。
- **self-learning** — 自动研究新技术并生成 SKILL.md，可用于追踪 ETSI LI 标准版本更新。用法：`/learn ETSI TS 102 232 latest version updates`
- **huawei-hi2** — 华为 HI2 合法监听接口全栈 — CS X1/X2/X3 协议、IMS/SIP-I 监听方案、BER 编解码、CDR 字段定义、号码/位置 ASN.1 编码、ZTLIG 部署排障。HW 场景下联动使用。

---

---

## Common Pitfalls

1. **不要混淆 LI 和 L1** — LI = Lawful Intercept（合法监听），L1 = Level 1（如 OSI 物理层、L1 缓存等）。这是完全不同的两个缩写，不可混用。用户对"LI"写法的准确性敏感。
2. **不要混淆 HI2 和 HI3** — HI2 是信令（IRI，谁/何时/连接详情），HI3 是内容（CC，实际通信内容）
3. **HI2 PDU 和 HI3 PDU 是不同的编码结构** — 不要混用 ASN.1 类型
3. **TS 102 232 各 Part 独立版本号** — 需要单独检查每个 Part 的最新版本
4. **Internal Interception（X1/X2/X3）与 Handover Interface（HI1/HI2/HI3）不同** — 前者在 CSP 网络内部，后者是 CSP 到 LEA 的交付接口
5. **5G LI 不能套用 4G 架构** — 服务化架构（SBA）改变了监听触发点，NF 取代了传统网元
6. **华为 LI 报文解码的常见错误：**
   - LIRP 头偏移判断错误：保留字段（字节 9-13）不是 BER 起始位置，BER 从偏移 14 开始
   - 混淆 CS 版与 5GC 版：CS 版 X1 用固定 14 字节帧头+命令码，5GC 版 X2 用 LIRP 封装+BER
   - 未确认加密状态：明文长度=密文长度时才可直接读取 payload
   - X2 的 correlationNumber 用于 X3 CC 关联（基于 Charging ID），不是简单的序列号
7. **多家厂商 LIG 的 Target 格式差异** — 华为用 ASN.1/二进制结构，ZTE 用 CSV 文本（23字段），字段映射不同
8. **华为 X1 设控号码格式：** GMSC(ISDN) 必须选择 ISDN 格式，其他 MSC 选择 MSISDN。原因：它国用户号码在本网不可能分析为 MSISDN。ASN.1 PER 编码 tag：TAG_HWMSCE_SETTGT_NUMBER=0xA3，TAG_HWMSCE_NUMBER_ISDN=0x84。
9. **华为 X1 对接注意：** NEID 携带不对时返回 RC 9=无效的 NEID。X1 用户名、密码、NEID 三项需核对。认证失败告警 alarm-id=504，X1 中断告警 alarm-id=512。
10. **华为 LIID：** 取值范围 1~65535（外场可能超过），ASCII 格式传输。子地址模式下仅 0~9 数字。X1SetTarget 中 SpeechOutputMode 缺省 combinedOptionB(0)，对应设控时的 ACCESS NUMBER。
11. **ZTLIG(Sinovatio/中新赛克, Kafka) 部署注意：** 前后台传输不通时需先在前台手动创建 Kafka topic（TARGET_INFO/TARGET_INFO_STATUS/OWLS_TMC_REALTIME/OWLS_TMC_OFFLINE），否则 ZTLIG 1 进程不启动。ZK 地址需正确配置。
12. **HW X2/X3 关联模式区分：** CS(M3UA) 模式通过 ISUP 消息关联；SIP-I(IP) 模式必须在 SIP INVITE ISUP 部分用 Access Transport 带 LIID+CIN（application 消息），普通 ISUP 不行。TX/RX 分离用 LIID+CIN+Direction。
13. **HW X3 信号传输：** TMD(传统) 用 ISUP，当前主流用 IP+M3UA。SIP-I 模式下 LIG 处理流程：NE→SSF(ISUP 层带 LIID+CIN)→SDP 获取 IP+PORT→RTP。对接需确保 MGW/SBC PING 通、防火墙端口通。
14. **号码编码 0x91 处理：** msISDN/callingPartyNumber/calledPartyNumber 均含指示字节 0x91（国际+E.164），解码时忽略。e164-Format 携带 T/L，需先解析 T/L 再解析值。
15. **位置信息编码：** CGI/LAI/SAI/RAI/TAI/ECGI 六种格式，均为 MCC(3dig)+filler(1111)+MNC(2~3dig)+位置码(LAC/TAC/SAC/CI/RAC) 的结构。
8. **Visio .vsd 文件处理：** LibreOffice 可以转 PDF 和 PNG（`--convert-to pdf/png`），PDF 用 `pdftotext -layout` 提取文本。图表内容需用 vision_analyze 读取 PNG。
9. **XMind .xmind 文件处理：** 本质是 ZIP，`content.json`（新格式）或 `content.xml`（旧格式）。新格式 rootTopic 下 `children.attached` 嵌套子节点。旧格式用 namespace `urn:xmind:xmap:xmlns:content:2.0`。如果标准 zip 失败则文件损坏。批量处理时用 `search_files` 列出 → `zipfile.ZipFile` 逐个解析 → 递归遍历 → 写入知识库作为 Markdown 笔记。
10. **HW X2 BER 与 IMS X2 格式不同：** CS X2 用 ASN.1 BER 编码（TLV 嵌套），IMS X2 用 iMS-IRI-Report 封装 SIP 消息。HW 通过报文头区分。CDR 字段定义（35 个字段含 EventDetail/NetworkType/ReportType/SsCode/SsSubCode）见 `references/huawei-cs-x2-cdr-spec.md`。
11. **HI1 ASN.1 编译链：** `HI1NotificationOperations,ver7.asn` 不能独立编译，需链式包含 `UmtsHI2Operations_gl.asn` + `HI2Operations_gl.asn` + `UmtsCS-HI2Operations_gl.asn` 才能解析 `LawfulInterceptionIdentifier`/`TimeStamp`/`CommunicationIdentifier` 等导入类型。单独编译报 `cannot import type from missing module`。
12. **14字节华为头 V4 解析：** 字节2=NE类型(1=MSC,9=SBC,111=IMS等23种)，字节8=LEAID。字节2前的0xAA为固定前导码。BER 解码载荷从偏移14开始，非 0xAA 开头说明数据可能已是裸 BER 无帧头。
13. **X 接口日志解析的 LOG_HEADER_RE 尾随空格：** SSF/RVF/ZTLIG 日志的 LEVEL 字段可能有尾随空格（如 `[INFO ]` 而非 `[INFO]`），正则必须写为 `(\w+)\s*` 否则匹配失败（返回 None）。
14. **ztlig2 文件可能是 gzip 伪装：** `.txt` 后缀的文件可能实际是 gzip 压缩数据（`file` 命令检测为 `gzip compressed data`）。读取时用 `errors='replace'` 处理不可解码行，或先用 gzip 解压。
15. **VS Code 终端启动失败 — 启动目录不存在：** workspace 中引用的项目目录（如 `~/projects/STCS/`）如不存在，VS Code 终端报 "终端进程启动失败: 启动目录不存在"。创建空目录即可解决，VS Code 不要求目录是 git 仓库。
16. **VS Code 的 git 代理在 GFW 后推送失败：** `git push` 报 `gnutls_handshake() failed`。修复：`git config --global http.proxy http://127.0.0.1:7897` 并确保 `url.https://github.com/.insteadof=git@github.com:` 没设错（如果误配会导致 SSH remote 被转成 HTTPS 协议）。
17. **HW X2 PCAP 解码必须启用 TCP 重组 + 端口过滤：** 华为 X2 帧的 ASN.1 BER 内容可能 >1460B 跨多个 TCP 段。单个包解码会因 BER 长度超限返回空结果。必选：勾选「TCP 重组」或调用 `parse_pcap(path, reassemble=True)`。同时输入端口过滤（华为IMS X2口=8890），否则全量网络包（TCP握手/HTTP等）会被尝试解码，产生大量误报。检测逻辑：前50包找 ≥3 个 0xAA 帧头即提出警告。实测：7.6MB PCAP 无过滤→34,047包全部失败→57MB页面；端口8890+TCP重组→61包/60成功→432KB页面。
25. **ZTLIG1 X1 日志解析器 ZTLIG1_CMD_RE 必须覆盖运行态操作：** 初始 ZTLIG1_CMD_RE 只匹配 7 种启动阶段命令（recv start init req / add succeeded / failed to get license / set/delete/modify/query target），缺失全部运行时 X1 操作。修复：扩展到 14 种命令分类，包括 link_check/link_error/ne_no_response/kafka_add_del_target/x1_send_cmd/hi1_queue/redis_sync/etsi_liid_check/db_query/location_report/list_target_rsp 等。LIID 提取必须同时支持 `liid=XXX` 和 `liid[XXX]` 两种格式。子模块名提取需兼容 A/B/C 三种日志格式（有INFORM/无INFORM/裸body）。见 `x_interface_decoder.py` 的 ZTLIG1 处理分支。
26. **Web 日志分析页面上传大文件导致 Chrome SIGILL：** ztlig1 日志可达 521MB/473万行。`FileReader.readAsText()` 整文件读入导致 OOM → SIGILL。修复：`file.slice(0, 5MB)` 前端截断 + `content[:5MB]` 后端双重保护。见 `references/log-analysis-large-file-handling.md`。

19. **BugFix 文档工作流（用户强制要求）**：每次修复 Bug 必须按以下流程记录，缺一不可：(1) 测试报告写入 `docs/tests/` (2) 变更日志写入 `docs/changelog/` (3) 经验沉淀到知识库 `~/knowledge/知识/技能/hermes-asn1/` (4) 软件日志 (5) 本地 git commit (6) GitHub push。用户对"只改代码不写文档"的行为零容忍。
20. **单元测试强制要求**：代码修改后必须创建/更新 `src/tests/test_all.py` 中的测试用例。测试覆盖：新增功能对应 TestClass、BugFix 有回归测试（截断/边界/错误输入）。运行命令：`venv/bin/python3 -m pytest src/tests/test_all.py -v --tb=short`。
21. **经验库的 SIGILL 模式**：Web 应用上传大日志文件时，Chrome 的 `FileReader.readAsText()` 可能 OOM → SIGILL。修复：前端 `file.slice(0, 5MB)` + 后端 `content[:5MB]` 双重截断。见 `references/log-analysis-large-file-handling.md`。
22. **BER 截断处理**：`pre_decode_split_report()` 中，当 BER TLV 声明的 payload 长度超出可用数据时，传统逻辑直接 `break` 返回空结果。正确做法：取剩余全部数据，让 asn1tools 自己决定能否解码。见 `asn_decode_api_v4.py` 的 `V4.0.1 fix` 注释。
23. **X 接口日志解析的 LEVEL 空格陷阱**：SSF/RVF/ZTLIG 日志 `[INFO ]` 有尾随空格。`LOG_HEADER_RE` 必须写 `(\\w+)\\s*` 而非 `(\\w+)`，否则匹配失败返回 None。
24. **ztlig2 文件可能是 gzip**：`.txt` 后缀但实际是 gzip 压缩数据。读取时用 `errors='replace'` 或先 `file` 命令检测。\n## Verification Checklist

- [ ] 能准确区分 HI1/HI2/HI3 各自的职责和标准
- [ ] 知道 TS 102 232 各 Part 覆盖什么通信场景
- [ ] 理解 X1/X2/X3 与 HI1/HI2/HI3 的层次关系（注意：TS 33.108 定义的是 HI 不是 X1）
- [ ] 知道 `~/.hermes/scripts/etsi-li-card.py` 可生成标准体系卡片
- [ ] 能解释 5G LI 相比 4G 的架构变化
- [ ] 引用版本参考：`skill_view("etsi-lawful-intercept", "references/versions.md")`
- [ ] 理解三家厂商（华为/中兴/爱立信）的 X1 实现差异（私有TCP vs IIF命令 vs SOAP/XML）
- 知道 3GPP TS 33.108 定义的是 HI（Handover Interface）不是 X1
- 能区分 "HI1/HI2/HI3" 和 "X1/X2/X3" 分别是哪段路径上的接口
- 知道本地知识库中 LI 参考文档存放位置（~/knowledge/3gpp-ts33108/ 和 ~/knowledge/baidu-netdisk/parsed/）
- 知道 3GPP 规范下载方式：`wget "https://www.3gpp.org/ftp/Specs/archive/33_series/33.108/33108-i00.zip"`

## 十二、三家厂商 X1 接口实现对比

3GPP TS 33.127 第 5.4.4 节定义了 **LI_X1**（LIPF↔POI/TF/MDF 四个子接口），但**不规定传输协议**——这是厂商之间的最大差异。

| 维度 | 华为 (Huawei) | 中兴 (ZTE) | 爱立信 (Ericsson) |
|------|--------------|------------|------------------|
| **X1 传输协议** | **TCP 私有二进制** | **IIF（内部拦截功能）+ CORBA/SNMP/MML 命令** | **SOAP/XML over HTTP** |
| **X1 本质** | LIG↔NE 之间的独立二进制通道 | NE 内部 IIF 模块接收外部管理指令 | ADMF↔NE 之间的 XML 消息交换 |
| **帧头** | 14字节（新版）/ 8字节（NGN老版），前导 `0xAA` | 无独立帧头（CORBA GIOP 消息头） | 无独立帧头（HTTP + SOAP Envelope） |
| **NE type 编码** | 第3字节：MSC=1, HLR=2, IMS=111, … | CORBA 对象引用解析 | URL 路径或 SOAP Action 头 |
| **数据编码** | C 结构体 / ASN.1 PER | NE 内部自有格式 | XML 文档 |
| **加密** | DES/AES，ECB 模式（帧头指定） | 取决于下层传输（IPSec/TLS） | HTTPS + WS-Security |
| **命令方式** | nCmdCode 字节（0x10~0xF0）或 ASN.1 CHOICE tag | MML 命令（ACTIVATE INTERCEPTION: …） | SOAP 方法（WSDL 定义） |
| **与 ETSI 关系** | 语义符合 TS 33.108，传输私有 | 语义通过 IIF 实现，命令私有 | XML 映射 ASN.1 语义 |

**关键澄清**：
- TS 33.108 定义的是 **HI1/HI2/HI3**（Handover Interface：ADMF/DF → LEMF 的交付接口），**不是 X1**。X1 是 CSP 内部的厂商私有接口。
- TS 33.127 5.4.4 定义 **LI_X1** 的功能语义（激活/去激活/修改拦截任务），传输层开放。
- 华为私有 TCP 协议完整文档见 `~/knowledge/baidu-netdisk/parsed/`（LI-HW.md + HW_NGN_X1X2.md）。
- 中兴通过 IIF 模块接收 CORBA/SNMP/MML 命令（非独立二进制通道）。
- 爱立信用 SOAP/XML 封装，与 5GC SBA 的 HTTP/REST 趋势一致。

## 十三、本地知识库中的 LI 参考文档

### LI 工具链：ops-monitoring 项目

仓库 `github.com/andymao76/ops-monitoring` 包含三个实用工具，路径为 `~/projects/`:

| 工具 | 位置 | 说明 | 参考 |
|------|------|------|------|
| **ETSI-ASN1-Assistant** | `~/projects/ETSI-ASN1-Assistant/` | HI2/X2/X3/HI1 解码器 Web 工具, 12种模式 + X接口日志分析 (V4.0) | `references/etsi-asn1-assistant-tool.md` |
| **X 接口日志分析** | `~/projects/ETSI-ASN1-Assistant/src/x_interface_decoder.py` | SSF/RVF/ZTLIG1/ZTLIG2 日志解析器 | `references/x-interface-log-analysis.md` |
| **Diameter-decoder** | `~/projects/Diameter_decoder/` | Diameter 协议解码器 | — |
| **ztlig-tools** | (ops-monitoring 子目录) | ZTLIG 运维工具集 | — |

ETSI-ASN1-Assistant 当前版本 **V4.0.1**, 包含 7 个 V4 模块 + X 接口 ZTLIG1 解码器增强 (14种命令、LIID双格式、子模块A/B/C三种格式兼容)。版本升级时所有文档更新流程见 `references/v4-version-upgrade-checklist.md`。

### 文档索引

| 文档 | 位置 | 说明 |
|------|------|------|
| **TS 33.108 V18.0.0** (HI 接口规范) | `~/knowledge/3gpp-ts33108/` | 完整正文 + 19个 ASN.1 附件 |
| **TS 33.127 V18.0.0** (LI 架构) | `~/knowledge/3gpp-references/ts33127.md` | LI_X1/LI_X2/LI_X3 架构定义 |
| **TS 33.126 V18.0.0** (LI 需求) | `~/knowledge/3gpp-references/ts33126.md` | 系统级 LI 需求 |
| **LI-HW.md** (华为 CS ETSI) | `~/knowledge/baidu-netdisk/parsed/` | X1 帧头 / NE type / ASN.1 第12章 |
| **HW_NGN_X1X2.md** (华为 NGN) | `~/knowledge/baidu-netdisk/parsed/` | 老版 X1/X2, C帧结构 + 命令码表 |
| **NGN_XPTU.md** | `~/knowledge/baidu-netdisk/parsed/` | XPTU 架构和 HI↔X 映射 |
| **华为LI标准协议翻译**（中文） | `~/knowledge/research/华为LI标准协议翻译.md` | 华为 5GC+CS X1/X2/X3 中文协议标准 + 8个 ASN.1 文件 |
- **华为LI实现细节** | `references/huawei-li-implementation.md` | 华为 X1 帧头编码、NEID 差异（ASCII vs BCD）、FUNCType 位掩码、LIOID 分配规则等 |
- **华为帧头字节布局** | `references/hw-header-byte-layout.md` | X1/X2/X3 帧头字节级结构、NE 类型映射表(23种)、X1 命令码表、NGN 8字节头、TBCD 位置编码 |
| **华为 SVC VoLTE IMS 监听场景** | `references/huawei-svc-volte-ims-monitoring.md` | IMS 监听架构(X1/X2/X3)、iMS-IRI-Report 参数结构、ICID、多号码拦截、CS vs IMS 模式选择 |
| **华为 IMS X2 抓包示例** | 知识库: 知识/telecom/lawful_interception/华为SVC_IMS_X2报告抓包示例.md | 真实 13 步 VoLTE 呼叫 IRI 解码、SIP 消息 + SDP、ICID 关联验证 |
| **华为 CS X 接口与 ZTLIG 部署** | 知识库: 知识/telecom/lawful_interception/华为CS_X接口说明与ZTLIG部署实战.md | X1 TCP 细节、LIID、NEID RC 9、设控号码格式 ASN.1 PER、乌干达 Kafka 部署 |
| **华为 CS X2 CDR 字段规范** | `references/huawei-cs-x2-cdr-spec.md` | BER 编码规则、35 个 CDR 字段定义表（含 NetworkType/ReportType/EventDetail 编码）、EventDetail 编码（CS 10-19 / PS 40-70 共 31 种）、补充业务码表（SsCode 0x11~0x99 + SsSubCode）、HW X2 排查命令（Wireshark + tcpdump + Kafka） |
| **华为LI PCAP 解码** | `references/huawei-li-pcap-decode.md` | 华为 X1/X2 接口 pcap 报文结构分析、LIRP 封装头、BER IE 解码、X1 链路保活/X2 IRI 上报识别 |
| **Sinovatio LIG (ZTLIG) 实战** | `references/zte-lig-ztlig-notes.md` | Sinovatio LIG Target 字段定义、多 TMC 模式、与华为 LIG 对比 |
| **SOSM 监听流程** | `references/sosm-li-flow.md` | SOSM 系统主叫触发监听及 X3 通道建立流程 |
| **OWLS 平台架构** | `references/owls-platform-architecture.md` | OWLS 系统 LJ 平台三大数据源、TMC/CSPETL/OTT通联/CBS阻断/SNS虚实关联 |
| **OWLS 详细知识库** | `~/knowledge/research/OWLS_系统架构与业务流程.md` | 基于 17 个 xmind 文件的完整知识库（TMC 设控、SICMS2.0 协议、OT T 关联、专题分析等） |
| **5G LI 标准演进** | `~/knowledge/telecom/lawful_interception/5g-li-standards-evolution.md` | 5G SA3-LI新规范(TS 33.126/127/128)、ETSI标准体系、X1/X2/X3标准化 |
| **ZTE CS LI 三接口规范** | `~/knowledge/hi2/厂商对接/ZTE_CS_LI_HI1_HI2_HI3_三接口规范.md` | ZTE CS HI1 CLI命令(65xx)+HI2 ASN.1+HI3 ISDN CC交付 |
| **Utimaco LIMS RAI v16.1** | `~/knowledge/hi2/厂商对接/Utimaco_LIMS_RAI_v16.1_协议规范.md` | Utimaco LIMS RAI二进制协议(RAI-SP/RAI-CL)、86种Target Type、Flags体系 |
| **5G 定位技术** | `~/knowledge/research/5G_定位技术_R16_R17.md` | 5G R16/R17 定位精度需求与 6 种定位方案 |
| **SOSM 详细知识库** | `~/knowledge/research/SOSM_主叫触发监听_X3通道建立流程.md` | SOSM 系统完整信令时序图 |
| **LI 技术资料库总索引** | `~/knowledge/research/li-tech-library-index.md` | 百度网盘备份的 LI 技术资料总索引（含 v2.1 知识图谱） |
| **LI 知识图谱 v2.1** | `~/knowledge/research/li-knowledge-graph.svg` + `li-knowledge-graph.html` | 6层15节点可视化图谱，含 HW/ZTE/Ericsson/NSN/UTIMACO/OWLS/2G3G |
| **5GC 核心网技术资料** | `~/knowledge/research/5gc-core-network.md` | 注册/去注册/PDU会话/Service Request 流程详解 + SUCI 标识 |
| **EPC 核心网技术资料** | `~/knowledge/research/epc-core-network.md` | 4G/5G NSA EPC、MME 全系列手册(M01-M17)、LTE-TDD、抓包数据 |
| **2G/3G 核心网技术资料** | `~/knowledge/research/2g-3g-core-network.md` | GSM/UMTS 核心网、HLR/HSS、MSC/MGW、IMS |
| **7750 SR 技术手册** | `~/knowledge/research/nokia-7750-sr-technical-manual.md` | 诺基亚 7750 SR MG/GW/MME 配置指南、培训 PPT、KPI 计数器 |
| **5620 SAM 运维管理** | `~/knowledge/research/5620-sam-management.md` | 诺基亚 5620 SAM 安装/管理/排障/用户指南全系列 |
| **ASN.1 与 3GPP 规范解析** | `~/knowledge/research/asn1-3gpp-spec-analysis.md` | 正则表达式在3GPP 5G规范中的应用（PDF+视频）、VoLTE、5G 大话 |
| **EVE-NG 实验环境** | `~/knowledge/research/eve-ng-lab-environment.md` | EVE-NG 工具包、Lab 拓扑合集、ISO 镜像、COOK-BOOK |
| **华为 LI 技术体系** | `~/knowledge/research/huawei-li-system.md` | 华为 CS（UMG8900/MSOFTX3000）和 PS（USN9810/SAE-GW）LI 技术 |
| **ZTE LI 技术体系** | `~/knowledge/research/zte-li-system.md` | 中兴 ZXWN GPRS / ZTELIG LI 接口规范 |
| **爱立信 LI 技术体系** | `~/knowledge/research/ericsson-li-system.md` | 爱立信 MSC/EIP/ENM LI 技术 + 实战案例 |
| **NSN LI 技术体系** | `~/knowledge/research/nsn-li-system.md` | 诺基亚西门子 FlexiNG / HLRI（待补充） |
| **UTIMACO LI 技术体系** | `~/knowledge/research/utimaco-li-system.md` | UTIMACO LI 网关/HSM/安全管理平台 |
| **LI 标准与规范** | `~/knowledge/research/li-standards-specifications.md` | ETSI/3GPP 标准、HI1/HI2/HI3、X1/X2/X3、CORBA |
| **ETSI-ASN1-Assistant UI & 报告生成模式** | `references/etsi-asn1-assistant-ui-report-patterns.md` | V4.0.1 页面架构/报告模式/导出/常见Bug |
| **ZTLIG1 X1日志分析经验** | `~/knowledge/telecom/lawful_interception/ztlig1-x1-log-analysis.md` | ZTLIG1 日志三种格式(A/B/C)、14种命令分类、LIID双格式提取、子模块5种、常见故障模式 | ZTLIG1 日志三种格式(A/B/C)、14种命令分类、LIID双格式提取、子模块5种、常见故障模式 |
| **ETSI-ASN1-Assistant 使用经验与排障** | `~/knowledge/telecom/lawful_interception/etsi-asn1-assistant-usage-guide.md` | TCP重组原理/实测对比、PCAP/IRI/X日志正确使用方法、端口过滤脚本、关联LI文档索引 |

## 十四、Visio / XMind 文件转换流程

处理 Visio (.vsd) 和 XMind (.xmind) 文件的标准流程：

### Visio (.vsd)
```bash
# 步骤1: LibreOffice 转 PDF
libreoffice --headless --convert-to pdf input.vsd --outdir /tmp/output/

# 步骤2: 从 PDF 提取文本
pdftotext -layout input.pdf output.txt

# 步骤3: 如果 PDF 包含图表，可同时转 PNG
libreoffice --headless --convert-to png input.vsd --outdir /tmp/output/
```

### XMind (.xmind)
`.xmind` 文件本质是 ZIP 包，内含 `content.json` (XMind 2020+, 新格式) 或 `content.xml` (XMind 8, 旧格式)。

```python
import zipfile, json, xml.etree.ElementTree as ET

with zipfile.ZipFile('file.xmind') as z:
    if 'content.json' in z.namelist():
        content = json.loads(z.read('content.json'))
        # XMind 2020+ 格式: sheet[0]['rootTopic']['children']['attached']
        for sheet in content:
            rt = sheet['rootTopic']
            # 递归遍历 rt['children']['attached']
    elif 'content.xml' in z.namelist():
        root = ET.fromstring(z.read('content.xml'))
        # XMind 8 格式: namespace urn:xmind:xmap:xmlns:content:2.0
        ns = {'x': 'urn:xmind:xmap:xmlns:content:2.0'}
        for topic in root.findall('.//x:topic', ns):
            title = topic.find('x:title', ns).text
```

**要点**：
- XMind 2020+ 格式的 `rootTopic` 有 `children.attached` 子节点，嵌套递归
- 旧格式用 XML namespace `urn:xmind:xmap:xmlns:content:2.0`
**注意**：如果标准 zip 解压报错（文件头损坏），尝试 `python3 -c "import zipfile; zipfile.ZipFile(fname)"` 诊断

#### 批量处理工作流

将目录下所有 .xmind 文件解析为结构化 Markdown 存入知识库：

1. 用 `search_files(pattern='*.xmind', path=DIR)` 列出文件
2. 用 `zipfile.ZipFile` 解压，读 `content.json`（XMind 2020+）或 `content.xml`（XMind 8）
3. 递归遍历 `rootTopic['children']['attached']` 生成层级缩进 Markdown
4. 写入知识库（如 `知识/工作/项目/XXX/`），附加 frontmatter（title/source/tags/creator）
5. 前端发 MEDIA 消息或 CLI 输出文件路径
注意：content.json 格式的 title 在 sheet 级为画布名，rootTopic.title 为根主题；content.xml 用 namespace `urn:xmind:xmap:xmlns:content:2.0` 解析 topic/title。

### Draw.io (.drawio)

OWLS 系统目录中的 `.drawio` 文件包含流程图和架构图信息。解析方法：

```python
import re, base64, zlib
from urllib.parse import unquote

with open('file.drawio', 'r') as f:
    content = f.read()

m = re.search(r'<diagram[^>]*>(.*?)</diagram>', content, re.DOTALL)
compressed = m.group(1)

if compressed.startswith('<'):  # 未压缩
    xml_str = compressed
else:  # base64 + deflate(no header) + URL encode
    raw = base64.b64decode(compressed)
    dec = zlib.decompress(raw, -zlib.MAX_WBITS)
    xml_str = unquote(dec.decode('utf-8'))

# 提取所有 mxCell 的 value 属性
import html as html_mod
values = re.findall(r'value="([^"]*?)"', xml_str)
for v in values:
    text = html_mod.unescape(v).replace('&#xa;', '\\n')
    text = re.sub(r'<[^>]+>', '', text).strip()
    if text:
        print(text)
```

**二进制加密格式**：以字节 `0x62`（'b'）开头，标识 `b#eE`（draw.io 加密保存），无密码不可读。用 `xxd -p -l1` 检测。无法解析时直接删除。
- 3 个文件（OTT通联、OWLS数据源、SICMS2.0数据接入）是 XMind 2020+ content.json 格式

## 十五、OWLS 系统（LJ 平台）

OWLS 是一个完整的合法监听数据平台，详见参考文件 `references/owls-platform-architecture.md`。关键信息：

- **三大数据源**: A口(MSIS/电围) + LIG/TMC(合法监听) + MIMC(移动互联网)
- **TMC**: 处理 ZTLIG 上报的 CS 域 HI2/HI3 数据，OWLS 中的主动式设控模块
- **CSPETL**: 22 步通用处理流程（协议映射→三码校验→白名单→国家码→基站补全）
- **sourceno 体系**: 30+ 种协议号（DST_017xxx 系列）
- **OTT 通联**: VOIP 应用关联方案（通用 SSRC 关联 + Telegram CRC 碰撞）
- **CBS 阻断**: 6 种策略类型（IP/DOMAIN/URL/APP/PROTOCOL/IP+APP）
- **SNS 虚实关联**: Facebook/Twitter/YouTube/Instagram 碰撞（时间窗口+权重公式）

当用户提及 OWLS、TMC、LJ平台、CSPETL、SICMS、DFX、ZTLIG 时触发。

## 十六、SOSM 系统

SOSM 是 LI 系统中的信令调度模块，处理主叫用户触发监听及 X3 通道建立流程，详见 `references/sosm-li-flow.md`。

涉及实体: CCB/MGRA/LICI/SOSM/IGW/CDBI/BCLIB
核心流程: 主叫UE→SETUP(带监听标志)→CCB→LICI→SOSM→IGW X3通道建立→SEND ONLY→激活

## 十七、华为 LI X 接口错误码

两套错误码体系用于 pcap 报文解码和协议排错：

- **LIG Return Code（操作级）**：27 种（0~26 + 255），包括连接故障、认证、号码状态、LEAID 状态等
- **EPC Cause（内层协议级）**：26 种（128~221），包括成功、系统错误、参数错误、资源限制等

完整映射见 `references/huawei-li-error-codes.md`。

在 pcap 解码时可能同时遇到这两套码值：
- X1 连接响应中 EPC Cause=128 表示成功
- 设控操作失败时 LIG Return Code=20 表示 userNumberNotExist

## 十八、多厂商 LI 错误码参考

三家中兴/爱立信的错误码见 `references/vendor-error-codes.md`：
- **中兴 ZTE V3/V4 LIS**：17 种返回码，含目标状态（已存在/不存在/LIID重复）、参数校验（SD/ST/ED/ET/TT格式）、MC 不存在、无权限
- **爱立信 Ericsson LI-IMS 登录**：12 种登录返回码，含账户锁定、密码策略（首次改密/过期/强度/历史）、许可证控制
- **三家对比表**：同一场景（成功/认证/参数/权限/资源）在各厂商的码值差异

## 十九、Draw.io (.drawio) 文件解析

OWLS 系统目录中的 `.drawio` 文件包含流程图和架构图信息。解析方法：

```python
import re, base64, zlib
from urllib.parse import unquote

with open('file.drawio', 'r') as f:
    content = f.read()

# 提取 diagram 标签间的压缩内容
m = re.search(r'<diagram[^>]*>(.*?)</diagram>', content, re.DOTALL)
compressed = m.group(1)

if compressed.startswith('<'):  # 未压缩
    xml_str = compressed
else:  # base64 + deflate(no header) + URL encode
    raw = base64.b64decode(compressed)
    dec = zlib.decompress(raw, -zlib.MAX_WBITS)
    xml_str = unquote(dec.decode('utf-8'))

# 提取所有 mxCell 的 value 属性
import html as html_mod
values = re.findall(r'<mxCell[^>]*?value="([^"]*?)"[^>]*?(?:/>|</mxCell>)', xml_str)
for v in values:
    text = html_mod.unescape(v).replace('&#xa;', '\n')
    text = re.sub(r'<[^>]+>', '', text).strip()
    if text:
        print(text)
```

**二进制加密格式**：以字节 `0x62`（字符 'b'）开头，标识 `b#eE`（draw.io 加密保存），无密码不可读。需用 `xxd -p -l1` 检测文件头确认。无法解析时直接删除或告知用户。

## 二十、快速下载 3GPP LI 规范

## 二十一、OpenLI 开源 ETSI LI 系统

OpenLI 是一个完整的开源 ETSI 合规合法监听系统（C, GPL-3.0），含 Collector/Mediator/Provisioner 三组件。

- **编译指南**: `references/openli-build-guide.md` — 完整编译流程（libwandder → libwandio → libtrace → OpenLI）
- **本地克隆**: `~/projects/openli/` (v1.1.19)
- **官方仓库**: https://github.com/OpenLI-NZ/openli

```bash
curl -LO "https://www.3gpp.org/ftp/Specs/archive/33_series/33.108/33108-i00.zip"  # R19
curl -LO "https://www.3gpp.org/ftp/Specs/archive/33_series/33.127/33127-i00.zip"
curl -LO "https://www.3gpp.org/ftp/Specs/archive/33_series/33.126/33126-i00.zip"

unzip 33xxx-i00.zip
# .doc格式需先转.docx: libreoffice --headless --convert-to docx xxx.doc
markitdown 33xxx-i00.docx > 33xxx.md
```

版本标记：`i`=R19, `h`=R18, `g`=R17。不要从 ETSI 网站直接下载 PDF（常返回重定向页）。
