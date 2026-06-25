# A1 VoWiFi HI2 IRI 解码实例

> 2026-06-24 会话，A1 项目苏丹 ZAIN 网络 VoWiFi 合法监听 X2 接口分析

## 概述

- **工具**: ETSI-ASN1-Assistant V3 (hw-ims 模式)
- **PCAP**: 2 个 (34k + 52k 包), TCP 端口 8890 X2 IRI 交付
- **运营商**: ZAIN Sudan (MCC=634, MNC=007, OperatorID=2048)
- **核心网**: atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org
- **解码结果**: 123 条 IRI 报告, 15 个 LIID 会话

## 原始数据分析

### PCAP 文件

| 文件 | 包数 | 时间范围 | 解码IRI |
|------|------|---------|--------|
| a8b0f01b-2ef1-48a2-b46b-527e14da0f3d.pcap | 34,130 | 18:08:36~18:08:48 | 61 条 |
| c8381c8b-eaf1-4090-9180-4984971a3344.pcap | 52,243 | 18:04:33~18:04:51 | 62 条 |

### 端口分布

| 端口 | 类型 | 说明 |
|------|------|------|
| 8890 (TCP) | X2 IRI | aa05 协议封装 + BER 编码的 HI2 消息 |
| 20000/20002/20004 (UDP) | X3 CC | RTP 媒体流 |
| 9904/9905 (UDP) | 统计/心跳 | 非 BER 格式 |

## 关键会话

### LIID=16796 (HONOR ALT-L42)
- 主叫: +249****5503 → 0123496896
- 信令: INVITE → 200 OK → ACK
- 接入: 3GPP-UTRAN-FDD(3G) + 3GPP-E-UTRAN(LTE) 切换
- 小区: 6340704533FEF, 63407A0930044302
- UE IP: 10.201.177.169:40615
- 终端: HONOR ALT-L42 (Android 8.0)

### LIID=18041 (iPhone iOS/26.5) — 含公网IP
- 主叫: +249****0415 → 0123123638
- 信令: INVITE → 200 OK → ACK → BYE (cause=200, 约7秒)
- 接入: IEEE-802.11 (VoWiFi) + 3GPP-UTRAN-FDD(3G) 切换
- 小区(3G): 6340700210E52
- UE私网IP: 10.201.24.98:5060
- **公网IP: 196.202.142.135:16567** (Wlan-ue-local-ip)
- SBC: psdpcscf02.ims.mnc007.mcc634.3gppnetwork.org
- IMS CID: psdpcscf02.191.325e.20260623100424
- 报文: PCAP1:#9772,#9806,#10328,#10365,#26462,#27084 / PCAP2:#17890,#17960,#18456,#18497,#36941,#37414
- 终端: iPhone iOS/26.5

### LIID=17289 (HONOR ALT-L42)
- 主叫: +249****6811 → 0125406569
- 信令: INVITE → 100rel → PRACK (含100rel可靠性机制)
- 接入: 3GPP-E-UTRAN(LTE) + 3GPP-UTRAN-FDD(3G)
- 小区: 634079C610071505, 63407044EA17F

## 公网IP 发现

在 **LIID=18041** 的 VoWiFi 通话中，PANI 的 `Wlan-ue-local-ip` 字段携带公网 IP `196.202.142.135`。

### 特征
- IP 归属: AFRINIC (苏丹), 非运营商CGNAT
- 前置条件: 接入类型 = `IEEE-802.11`
- 区别于 `ue-ip` (IMS 私网 10.x.x.x)
- 用户身份: iPhone iOS/26.5
- 通话全程IP不变 → 用户位置未变化

### 报文出处
共 12 条 IRI 报告包含该 IP:
- PCAP1: #9772(ACK), #9806(ACK), #10328(200OK), #10365(200OK), #26462(BYE), #27084(BYE)
- PCAP2: #17890(ACK), #17960(ACK), #18456(200OK), #18497(200OK), #36941(BYE), #37414(BYE)

## PANI 接入类型分布

| 类型 | 次数 | 含义 |
|------|------|------|
| 3GPP-UTRAN-FDD | 42 | 3G WCDMA (主流) |
| 3GPP-E-UTRAN | 18 | 4G LTE (含VoWiFi) |
| IEEE-802.11 | 12 | WiFi (仅LIID=18041) |
| 3PTC/3POC | 5 | IMS终止/发起侧 |
| 3GPP-GERAN | 2 | 2G GSM |

## ZTLIG 日志过滤命令

```bash
# 按LIID
cat ztlig2*.* | grep "LIID\":\"18041" > liid-18041.txt

# 按CIN
cat ztlig2*.* | grep "CIN\":\"2491250814467" > cin-xxx.txt

# 按IMS ChargingID
cat ztlig2*.* | grep "psdpcscf02.191.325e" > cid-target.txt

# 打包(忽略活动文件警告)
tar czf ztlig2_$(date +%Y%m%d_%H%M%S).tar.gz ztlig2*.* --warning=no-file-changed
```

## Word 报告章节结构

完整报告(7章) 示例结构:
1. **标题页**: 项目 + 时间 + PCAP统计
2. **汇总统计**: 包数、解码条数、LIID数
3. **PANI位置信息表**: 所有LIID的接入类型、小区ID、UE IP:Port
4. **通话会话详情**: 每个LIID的信息表 + PANI明细
5. **解码方法说明**: 工具、ASN.1规范
6. **CID专项分析**: IMS ChargingID过滤 + 时序表
7. **公网IP分析**: 含报文出处明细表(7.7)

每条结论必须标注来源(PCAP文件名+报文序号)，不能含糊表述。
