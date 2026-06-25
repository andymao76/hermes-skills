# PCAP/LI 数据分析 — 会话记录

日期：2026-06-22
来源：hw-sbc-imsbase (苏丹SBC LI上报) + hw-sip-i (SIP-I接口) PCAP + HW-IMS-X2-CSCF.md 分析

## 文件结构

```
PCAP/
├── hw-SBC-imsbase.zip
│   └── hw-SBC-imsbase/
│       ├── sudan-SBC_report_with_sip-LIID_10013-call-rtp.pcap
│       ├── sudan-SBC_report_with_sip-LIID_10013-call-xinling.pcap
│       ├── sudan-SBC_report_with_sip-LIID_10013-call-xinling-nobye.pcap
│       └── sudan-SBC_report_with_sip-LIID_10013-call-xinling-bye.pcap
├── hw-sip-i/
│   ├── ssf-1-bussy-call-transfor.pcap  (ISUP IAM with LIID)
│   └── target_A-putong-rvf-10.204.249.75-2008_10.204.115.12-20000.pcap (RTP)
│   └── ori/
│       ├── O1LI14071612460000031 (181 bytes)
│       ├── O1LI14071612460000131 (131 bytes)
│       ├── O1LI14071612460000231 (131 bytes)
│       ├── O1LI14071612460000331 (178 bytes)
│       ├── O1LI14071612460000431 (182 bytes)
│       └── O1LI14071612460000531 (159 bytes)
```

## 数据点验证

| 数据点 | 编码结果 | 文件位置 |
|--------|---------|----------|
| CIN 0x40EB9FC = 68073980 | ✓ 数学验证通过 | 需确认在 pcap 中的具体字段 |
| LIID=84335 → 反序BCD `48 33 F5` | ✓ | SIP-I ISUP body offset 0x24 |
| LIID=10013 → ASCII | ✓ | SBC pcap offset 0x46 |
| CID=009515677 → BCD `00 95 15 67 7F` | ✓ | ORI 文件 |
| OPERID=63601 → ASCII `3633363031` | ✓ | ORI 文件 offset 0x33 |

## 华为 SBC LI 数据层头部结构

```
aa05 XX XX   — magic(2) + 长度(2)
YY YY YY YY  — 序号(4)
01 FF FF FF FF FF  — LI 头(6)
A4 82 06 D4  — 固定头(4)
80 06 XX...  — [0] 数据字段
97 01 XX     — [23] 标识
81 05 XX...  — [1] LIID
```

## ORI 文件结构

ORI 文件（O1LI1407161246000031 格式）：
- 文件名编码：`O1LI` + 日期(YYMMDDHHMMSS) + 序号
- 二进制 TLV 结构，使用 aa05 magic 头部
- 包含 LIID（ASCII 5位）、OPERID（ASCII/BCD）、时间戳、呼叫号码

## X2 IRI 日志分析（HW ATS9900）

来源：`PCAP/HW-IMS-X2-CSCF.md`（264KB, 2816行）
测试用例：TC_VoLTE2.0_监听_05_0102 — VoLTE用户被叫被监听，AMRWB编码

### 呼叫参数

| 字段 | 值 |
|------|------|
| LIID | 1 |
| OPERID | 123 |
| CIN | 8413f5（反序BCD） |
| 主叫 | +861****2132 |
| 被叫 | sip:+861****2131@ims.mnc020.mcc460.3gppnetwork.org |
| CallID | nlwkwbimlh7m4e4n77hnufpphfm4mgg4@192.6.170.222 |
| IMS Charging ID | pcscf06.198.bb.20140722005245 |
| Codec | AMR-WB (16000Hz), AMR, G729, PCMA, PCMU |
| 网元 | A-SBC(192.6.170.222) + I-SBC(192.6.170.221) |

### 完整呼叫流程（14条X2消息，双节点上报）

```
A-SBC(222)                  I-SBC(221)                  被叫
   |                           |                          |
①--INVITE(MF=66)--------------|                          |
   |                          ②--INVITE(MF=65)----------->|
   |                           |<--183(补充业务'17)--------|
③--PRACK----------------------|                          |
   |                           |--PRACK------------------>|
   |                          ④<--200/PRACK-------------|
⑤--UPDATE(precondition)-------|                          |
   |                           |--UPDATE----------------->|
   |                          ⑥<--200/UPDATE-------------|
   |                          ⑦<--180--------------------|
   |                          ⑧<--200/INVITE-------------|
⑨--ACK------------------------|                          |
   |                          ⑩--ACK-------------------->|
   |                        通话(AMR-WB, ~12秒)          |
⑪--BYE(CSeq=5)---------------|                          |
   |                          ⑫--BYE-------------------->|
   |                          ⑬<--200/BYE---------------|
   |<--200/BYE-------------------------------------------|
```

事件时间: 08:44:37 → 08:44:58

### X2 IRI 消息结构

华为 ATS9900 的 X2 IRI 上报格式：
- 码流头: `1C EB 62 00` + 长度 + 3个内存指针
- ASN.1 PER 编码体: `F0 72 73 00...`
- 关键字段: reportReason (00=INVITE, 03=reINVITE, 08=补充业务), sipMessageDirection (01=MO→MT, 00=MT→MO)

## 关键结论

- LIID + CallID = 唯一会话标识
- 华为使用反序BCD编码 LIID（而非标准 BCD）
- SIP-I ISUP 的 Subaddress 参数承载 LI 字段
- X2 IRI 双节点上报（A-SBC + I-SBC），MF 递减确认转发路径
- nDPI 可识别 SIP/RTP 协议，但无法穿透 `aa05` LI 封装
