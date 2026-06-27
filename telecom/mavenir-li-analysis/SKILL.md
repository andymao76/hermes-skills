---
name: mavenir-li-analysis
title: Mavenir LI 接口合规验证与解码分析
description: Mavenir IMS LI 设控(X1)/信令面(X2)/媒体面(X3)的PCAP抓包与ZTLIG日志对照分析, 验证是否符合 x1.xsd / x2-Common-V.1.3.xsd / x3-uag-V.1.4.xsd API 文档定义
tags:
  - Mavenir
  - LI
  - X1
  - X2
  - X3
  - SOAP
  - ZTLIG
  - PCAP
  - compliance
---

# Mavenir LI 接口合规验证与解码分析

参考文件: `references/command-速查.md` — 全量分析命令速查

## 适用场景

分析 Mavenir IMS LI 接口的抓包（PCAP）数据, 验证是否符合 Mavenir API 文档定义（x1.xsd / x2-Common-V.1.3.xsd / x3-uag-V.1.4.xsd）, 或排查 ZTLIG 各模块（ztlig1/ztlig2/ssf/rvf）处理问题。

也可分析 Mavenir 官方 XMLSpy 项目归档包（.spp/.7z）, 提取 XSD 约束、验证 RI 报文合规性、对比现有知识库。

## 前置条件

- PCAP 文件（来自 ZTLIG 机器 em2 接口）或 XMLSpy 项目包（.7z 含 .spp 项目文件）
- ZTLIG 日志（ztlig1, ztlig2, ssf, rvf）
- Mavenir API 文档（knowledge/li/Mavenir/）
- capinfos, tcpdump, strings, grep, base64, 7z

## 分析流程

### Step 1: 确认分析类型

| 特征 | 类型 | 对应日志 |
|:----|:-----|:---------|
| X1 SOAP (addTarget/delTarget/getStatus) | 设控分析 | ztlig1 |
| X2 IRI (hi2-uag + CDATA SIP) | 信令面分析 | ztlig2 + ssf |
| X3 CC (hi3-uag + RTP) | 媒体面分析 | rvf |

### Step 2: PCAP 基本信息

```bash
capinfos file.pcap | grep -E "Number|Duration|Size|SHA"
```

### Step 3: 提取操作分布

```bash
tcpdump -r file.pcap -A | grep -oaP "Mavenir:\w+" | sort | uniq -c
tcpdump -r file.pcap -A | grep -oaP '<litid>\d+' | sort | uniq -c
tcpdump -r file.pcap -A | grep -oaP '<ReturnCode>\d+' | sort | uniq -c
tcpdump -r file.pcap -A | grep -oaP 'Call-ID: \S+' | sort -u
```

### Step 4: X1 SOAP 设控分析（参考 x1.xsd WSDL）

检查清单: 命名空间(http://mavenir.net/li/), addTarget/delTarget/getStatus 参数结构, ReturnCode 值, TargetType 枚举值。

```bash
grep "MavUagX1" ztlig1.log | grep -v "GetStatus"      # add/del处理
grep "MavUagX1GetStatus" ztlig1.log | head -5           # 健康轮询
grep "lig1_target_notify.*fail\|actneID fail" ztlig1.log # 错误
```

### Step 5: X2 IRI 信令面分析（参考 x2-Common-V.1.3.xsd）

检查 hi2-uag 全部必选字段。v1.3 新增: Mid-Call Interception, IAP-id 64字符, uid。

```bash
grep "Mavenir_LIS_MsgProc" ztlig2.log
grep "MatchUsrinfo.*liid\[" ztlig2.log | head -5
```

SSF 状态机: 161(INVITE) → 162(180) → 163(200) → 164(BYE)

### Step 6: X3 媒体面分析（参考 x3-uag-V.1.4.xsd）

v1.4 可选字段: stamp/IAP-id/PayloadType/PayloadLength。

```bash
strings file.pcap | grep -oP '<PayloadLength>\d+' | sort | uniq -c | sort -rn
strings file.pcap | grep -oP '<li-tid>\d+' | sort | uniq -c    # 双li-tid检查
```

### Step 7: RVF 日志

```bash
grep -c "getXmlStringElement" rvf.log        # 轮询次数
grep -E "rvfCreateSession|rvfFindMavenirSessionId" rvf.log
```

已知问题: voiceCtrlType=2 阶段高密度 getXmlStringElement 轮询。

### Step 8: LigCdr 解码验证

EventDetail: 10=INVITE, 14=180, 11=200接通, 13=BYE(含CallDuration), 1=REGISTER
EventDirection: 1=主叫, 2=被叫 | ReportType: 1=注册, 2=呼叫/短信

### Step 9: 时间偏差处理

Mavenir UAG stamp vs ZTLIG log vs PCAP 抓包时间三者不一致, 用 Call-ID 或 Correlation-id 做关联键。

### Step 10: 报告输出

保存到数据所在目录, 文件名 analysis-report, 纯文本格式。

## 扩展场景: XMLSpy 项目归档包分析

当获得 Mavenir 官方 XMLSpy 项目包（.7z 内含 .spp + XSD + XML 样本）时, 可进行以下分析:

### 1. 解包与项目结构分析

```bash
7z l archive.7z                                    # 列出文件
7z x archive.7z -y                                 # 解压
cat IMS-LI.spp                                     # XMLSpy 项目文件, 查看文件夹分组
```

### 2. XSD 约束提取（三份核心 Schema）

| 文件 | 覆盖接口 | 版本 |
|:----|:---------|:----|
| x1.xsd | X1 SOAP WSDL | WSDL 1.1 (document/literal) |
| x2-Common-V.1.3.xsd | X2 IRI (hi2-uag) | v1.2→v1.3 (2019-09-24) |
| x3-uag-V.1.4.xsd | X3 媒体面 (hi3-uag) | v1.4 (FRN-1861, 2019-05-13) |

XSD 关键约束速查:

| 字段 | 格式 | 来源 |
|:----|:-----|:-----|
| IMSI | 15位数字 `[0-9]+` | xsd:minLength=15 + maxLength=15 |
| IMEI | 15位数字 `[0-9]+` | 同上 |
| IMEISV | 16位数字 `[0-9]+` | minLength=16 + maxLength=16 |
| EMAIL | 正则 `[^@]+@[^\\.]+\\..+` | pattern 约束 |
| IAP-id | 固定64字符 (v1.3前为8字符) | LimitedString64 |
| PayloadType (X3) | 枚举: RTP / MSRP | x3 限定 |
| TargetType | 枚举8种 | SIP-URI/MSISDN/IMSI/IMEI/IMEISV/EMAIL/SERVICE-NUMBER/CELL-ID |

### 3. DTD 引用检查

XML 样本通过 DOCTYPE 引用外部 DTD:
```xml
<!DOCTYPE hi2-uag SYSTEM "hi2-uag.dtd">
<!DOCTYPE hi3-uag SYSTEM "hi3-uag.dtd">
```
包内通常不包含 DTD 文件, DTD 由 Mavenir UAG 设备本地管理。

### 4. XML 样本验证

对照 XSD 检查每个 XML 样例的合规性:

- **X1**: Addtarget.xml, addTargetResponse.xml, delTarget.xml, getstatus.xml (SOAP Envelope)
- **X2**: X2-base64-CDATA-.xml (Base64 SIP), X2-invite.xml (明文 SIP 200 OK), X2-RC-0.xml (Return-code 元素)
- **X3**: X3-xmludp.xml (RTP 元数据)

X2 Return-code 元素 (流内错误反馈):
```xml
<hi2-uag>
  <Return-code>0</Return-code>
</hi2-uag>
```
Return-code=0 正常, 非零值表示流内错误（不是 SOAP ReturnCode, 是 UAG 内在的流级反馈）。

### 5. Base64 SIP Payload 解码验证

Mavenir 使用 Base64 编码 SIP 原文, 解码后包含完整鉴权信息:

```bash
grep -oa '<!\[CDATA\[[A-Za-z0-9+/=]*\]\]>' file.xml | \
  sed 's/<!\[CDATA\[//;s/\]\]>//' | base64 -d
```

解码结果特征: 含 Authorization Digest (AKAv1-MD5)、+sip.instance=IMEI、P-Access-Network-Info 小区ID、User-Agent 终端型号、Contact 含 mmtel+smsip 能力标识。

### 6. 与现有知识库对比

解压后需要与 `knowledge/li/Mavenir/` 下的知识条目交叉比对:

- Mavenir_IMS_LI_接口包_X1_X2_X3.md — XSD 约束、Payload 编码、Mid-Call Interception
- Mavenir_CM_LI_ADD_DEL_返回状态码.md — 返回码含义
- Mavenir_LI_ZTLIG_PCAP_对照分析方法论.md — PCAP 对照验证

新发现需补充入库, 避免后续分析遗漏。

### 7. X2 Mid-Call Interception (v1.3 新增)

X2 EventPayload 用于通话中媒体拦截 (Offer/Answer 协商):

| 子元素 | 说明 |
|:------|:-----|
| SipMsgOffer | 初始 SIP 消息 (Offer) |
| SdpOffer | 初始 SDP (Offer) |
| SipMsgAnswer (可选) | 应答 SIP (Answer) |
| SdpAnswer (可选) | 应答 SDP (Answer) |

### 8. X3 FRN-1861 (v1.4 可选化)

v1.4 (2019-05-13) 将以下字段改为可选: stamp, IAP-Id, PayloadType, PayloadLength。PayloadType 仅支持 RTP 或 MSRP。

## 常见踩坑点

1. tshark 在 ZTLIG 环境不可用 → 用 tcpdump -A + grep
2. 大PCAP 的 tcpdump -A 超时 → 用 strings 或加 BPF
3. PCAP 无 X2 IRI → 设控期间无通话则无流量
4. ztlig2/3 NE 同步失败(port 480) → 目标不转发到信令面
5. actneID 获取失败 → TMC 侧配置问题, 不影响 SOAP 直连
6. X2 Base64 Payload 截断 → tcpdump -A 可能跨包拆分, 用 `grep -oa`（binary模式）提取
7. X2 Return-code ≠ SOAP ReturnCode → Return-code 是hi2-uag流内错误反馈（非SOAP）, 不要混淆
