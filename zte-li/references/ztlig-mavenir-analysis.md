# Mavenir IMS LI 分析 — ZTLIG 日志 vs PCAP 交叉验证

## 背景

Mavenir 使用 XML+SOAP 架构（非 ASN.1 BER），X2 IRI 信令以 `hi2-uag` XML 格式输出，SIP 信令放在 `<Payload>` 的 CDATA 内（明文或 Base64）。ZTLIG 通过 `ztlig2` 模块的 `Mavenir_LIS_MsgProc` 子模块解码。

当 ZTLIG 配置 interfaceType=3（Mavenir 模式）时，ztlig2 走 Mavenir XML 解析路径而非 ASN.1 BER 解码。

## 关键区别：Mavenir vs ASN.1 厂商

| 特性 | 华为/中兴 (ASN.1 BER) | Mavenir (XML/SOAP) |
|------|----------------------|-------------------|
| X1 协议 | RPC/XDR / TCP 二进制 | SOAP/HTTPS (WSDL) |
| X2 编码 | ASN.1 BER TLV | XML (hi2-uag) + CDATA SIP |
| 解码工具 | ETSI-ASN1-Assistant / ber-tag-analyzer | tcpdump -A + grep |
| PCAP 分析 | tshark + asn1tools | strings + grep -oa |
| IRI 结构 | 二进制 TLV 层次 | 扁平 XML 元素 |

## X2 报文结构 (hi2-uag)

```xml
<hi2-uag>
  <li-tid>10078</li-tid>                          ← LI 目标 ID
  <target>256759809987</target>                   ← 目标 MSISDN
  <targettype>MSISDN</targettype>                 ← 目标类型
  <otheridentities>
    <msisdn>+256****9987</msisdn>
    <imsi>641010245817504</imsi>                  ← 15位数字
    <imei>358179580029390</imei>                  ← 15位数字
  </otheridentities>
  <session-id>session-id-token</session-id>        ← = SIP Call-ID
  <stamp>2024-08-01 10:53:07.453</stamp>           ← Mavenir UAG 时间
  <CallDirection>to-target/from-target</CallDirection>
  <Correlation-id>correlation-id</Correlation-id>  ← 关联ID
  <IAP-id>UAGPTN01</IAP-id>                       ← IAP 实例名
  <Payloadtype>SIP-PDU</Payloadtype>
  <Payload><![CDATA[SIP message here]]></Payload>
  <EventPayload/>                                  ← v1.3 mid-call
</hi2-uag>
```

## X3 报文结构 (hi3-uag)

```xml
<hi3-uag>
  <li-tid>10078</li-tid>
  <stamp>2024-08-01 10:53:10</stamp>               ← v1.4 可选
  <CallDirection>from-target</CallDirection>
  <Correlation-id>2200034c0-3-429566ab3ee3</Correlation-id>
  <IAP-id/>                                         ← v1.4 可选，可空
  <PayloadType>RTP</PayloadType>                    ← RTP 或 MSRP
  <PayloadLength>101</PayloadLength>                ← 字节数
</hi3-uag>
```

注意: X3 仅传媒体面元数据（方向、长度），实际 RTP 流走独立通道。

## PCAP 分析命令

### 基本信息
```bash
capinfos voltelog-X2-20240801-3.pcap
```

### 提取所有 Call-ID（按呼叫关联）
```bash
tcpdump -r voltelog-X2-20240801-3.pcap -A 2>/dev/null | grep -oa 'Call-ID: \S*' | sort -u
```

### 提取所有 li-tid，检查双 LIID 模式
```bash
tcpdump -r voltelog-X2-20240801-3.pcap -A 2>/dev/null | grep -oa '<li-tid>\d+' | sort | uniq -c
# 正常: 每个 SIP 消息只出现一次
# Mavenir: 可能每个消息出现两次（10078 + 10073 = 双监听目标）
```

### 提取 Correlation-id（与 ZTLIG log 对照）
```bash
tcpdump -r voltelog-X2-20240801-3.pcap -A 2>/dev/null | grep -oa '<Correlation-id>[^<]*' | sort -u
```

### 提取 IMSI 验证目标用户
```bash
tcpdump -r voltelog-X2-20240801-3.pcap -A 2>/dev/null | grep -oa '<imsi>[^<]*' | sort -u
```

### 提取 SIP 方法统计
```bash
tcpdump -r voltelog-X2-20240801-3.pcap -A 2>/dev/null | grep -oaE '^(MESSAGE |SIP/2\.0 [0-9]+|REGISTER |NOTIFY |SUBSCRIBE |INVITE |BYE |ACK )' | sort | uniq -c
```

### 提取 SMS 判定
```bash
tcpdump -r voltelog-X2-20240801-3.pcap -A 2>/dev/null | grep -oc 'application/vnd\.3gpp\.sms'
```

### X3 PayloadLength 统计
```bash
strings voltelog-X3-20240801-3.pcap | grep -oP '<PayloadLength>\d+' | sort | uniq -c | sort -rn
```

### 提取特定 Correlation ID 的呼叫完整流程
```bash
tcpdump -r voltelog-X2-20240801-3.pcap -A 2>/dev/null | grep -a "2200034c0-3-429566ab3ee3" | head -20
```

## ZTLIG 日志分析

### 按 Correlation ID 过滤 ztlig2 日志
```bash
grep -a "2200034c0-3-429566ab3ee3" ztlig2.430.txt
```

### 提取 LigCdr JSON
```bash
grep -a "EncodeToJson" ztlig2.430.txt | grep "LIID.*10078"
```

### SSF 状态机验证
```bash
grep -a "ssf_deal_sip_msg\|ssf_send_lig2_call_msg" ssf.1320.txt | grep "2200034c0-3-429566ab3ee3"
```

SSF state 含义:
- 161 = INVITE (呼叫发起)
- 162 = 180 Ringing (振铃)
- 163 = 200 OK (接通)
- 164 = BYE (释放)

### RVF 媒体控制分析
```bash
# 统计 voiceCtrlType 分布
grep "voiceCtrlType" rvf.1420.txt | grep -oP 'voiceCtrlType[:=]\s*\d' | sort | uniq -c

# voiceCtrlType 含义:
#   1 = 媒体开始 (180 Ringing 时)
#   2 = 媒体应答/连接 (200 OK 时)
#   4 = 媒体停止 (BYE 时)

# 检查 RVF 轮询问题
grep -c "getXmlStringElement" rvf.1420.txt
```

### EventDetail 对照表 (Mavenir IMS)

| EventDetail | SIP 消息 | 说明 |
|:-----------|:---------|:-----|
| 10 | INVITE | 呼叫发起 |
| 11 | 200 OK (INVITE) | 呼叫应答 |
| 13 | BYE | 呼叫释放 |
| 14 | 180 Ringing | 振铃 |
| 1 | REGISTER | IMS 注册 |

### ReportType 含义
- 1 = 注册/位置事件
- 2 = 呼叫/短信事件

## 分析流程 (SOP)

### Step 1: 数据源准备
- PCAP: `capinfos` 检查基本信息
- ztlig2 日志: 确认 Mavenir_LIS_MsgProc 子模块
- ssf 日志: 确认 SIP 会话状态机
- rvf 日志: 确认媒体录制

### Step 2: 提取关键关联字段
```
Call-ID (SIP) → session-id (XML) → 唯一关联键
Correlation-id (XML) → ssf/xtlig2 correlationID → 跨模块关联
li-tid (XML) → LIID (ztlig2 log) → 监听目标
```

### Step 3: Call-ID 对照
PCAP 的 Call-ID 应与 ZTLIG log 中的 callId 完全一致。逐个列出全部 Call-ID，交叉验证。

### Step 4: SIP 流程还原
按 Call-ID 分组还原 SIP 对话序列。Mavenir 的典型呼叫: INVITE → 180 → 200 OK → ACK → BYE → 200 OK

### Step 5: LigCdr 字段验证
对照 JSON CDR 字段与 SIP 原始字段:
- CallingNum 应与 INVITE From 一致
- CalledNum 应与 INVITE To 一致
- CallDuration 应为 BYE 时间 - INVITE 时间
- Location 应来自 P-Access-Network-Info

### Step 6: 双 li-tid 检测
检查 PCAP 中同一条 SIP 消息是否出现两次（不同 li-tid）。若是，说明 Mavenir UAG 将 IRI 发给了多个监听目标。

### Step 7: RVF 轮询检测
计算 getXmlStringElement 调用 / 呼叫数。若远大于 voiceCtrlType 事件数(3/呼叫)，说明存在忙等待。

## 已知风险与问题

### RVF 忙等待（busy-wait）
在 voiceCtrlType=2（媒体应答）阶段，rvf 对 getXmlStringElement 进行高密度轮询。
正常: 2~3 次/voiceCtrlType 事件
异常: ~8,000 次/呼叫

影响: CPU 空转，日志膨胀（~40K 行/呼叫）
建议: 改为事件驱动或有限次重试（带退避）。

### 双 LIID 导致数据翻倍
同一条 SIP 消息可能携带两个 li-tid，导致 PCAP 和日志中的数据量翻倍。
ZTLIG 只对主 LIID 产单，另一 LIID 不产 LigCdr，但 rvf 仍会创建多余媒体会话。

### 时间戳偏差
Mavenir UAG 的 `<stamp>` 时间、ZTLIG log 时间、PCAP 抓包时间三者可能不一致。
不要依赖时间戳直接对比，用 Call-ID / Correlation-id 关联。

### PCAP 混杂流量
ZTLIG 机器的 em2 口可能混杂 Hikvision 摄像头发现协议(ethertype 0x8033)、VRRP、ARP 等非 LI 流量。过滤方法:
```bash
tcpdump -r file.pcap -A 2>/dev/null | grep -a "<?xml" | head -5
```

## API 符合性检查清单

| 检查项 | 检查方法 | 通过条件 |
|:-------|:---------|:---------|
| X2 li-tid | PCAP 提取 | int 值, 1~65535 |
| X2 OtherIdentities | PCAP 提取 | msisdn/imsi/imei 15位数字 |
| X2 CallDirection | PCAP 提取 | from-target 或 to-target |
| X2 Payloadtype | PCAP 提取 | SIP-PDU |
| X2 IAP-id | PCAP 提取 | 64字符内 |
| X3 PayloadType | PCAP 提取 | RTP 或 MSRP |
| X3 IAP-id (可选) | PCAP 提取 | v1.4 允许空 |
| ztlig2 EventDetail | ztlig2 log | 10=INVITE, 11=200OK, 13=BYE, 14=180 Ringing |
| SSF state 序列 | ssf log | 161→162→163→164 |
| rvf voiceCtrlType | rvf log | 1→2→4 |

## LigCdr JSON 关键字段速查 (Mavenir IMS)

```json
{
  "CdrType": "LigCdr",
  "LIID": "10078",
  "CidNum": "2200034c0-3-429566ab3ee3",       // Correlation-id
  "OperID": "111",
  "NeidType": 2,                               // 2=IMS
  "Neid": "125",
  "VneID": "11",
  "CaptureTime": "20240801105307",
  "Vendor": "uag",                             // Mavenir UAG
  "NetworkType": 1,
  "ReportType": 2,                             // 2=呼叫事件
  "EventDetail": 10,                           // 10=INVITE
  "EventDirection": 2,                         // 2=被叫方向
  "IMSI": "641010245817504",
  "MSISDN": "256759809987",
  "IMEI": "358179580029390",
  "CallingNum": "256740825532",
  "CalledNum": "256759809987",
  "LocationType": 4,                           // 4=E-UTRAN CGI
  "Location": "64101005F10F",
  "CallDuration": "000013"                     // BYE时携带, 秒
}
```

## 参考案例

完整分析报告示例见:
- `~/PCAP/Mavenir-IMS-LI/call-test/analysis-report` — VoLTE 呼叫 (INVITE→BYE)
- `~/PCAP/Mavenir-IMS-LI/sms-test` — SMS (MESSAGE) 分析
- `~/PCAP/Mavenir-IMS-LI/Mavenir-IMS-LI/` — X1 WSDL + X2/X3 XSD 规范文件
