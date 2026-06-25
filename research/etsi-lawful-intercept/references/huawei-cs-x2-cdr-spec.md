# 华为 CS X2 CDR 字段规范

## BER 编码规则

X2 口报告采用 **ASN.1 BER 编码**，TLV 嵌套结构：

```
T  L  T  L  V ....
```

- 定长：长度 ≤ 127 用 1 字节；> 127 用 `0x81 + len`
- HW 头：`aa 05 01 00 01 a5 01 a5 04 ff ff ff ff ff`

### HW 标准 2 口报告示例

```
aa 05 01 00 01 a5 01 a5 04 ff ff ff ff ff    # HW 头
a4 82 01 a1                                     # IRI-End-Report (0x01a1)
80 06 04 00 02 02 01 06                         # csdomainID
97 01 06                                        # iRIversion
81 05 33 31 34 39 30                            # LIID "1490"
a2 1f                                           # communicationIdentifier
     80 08 30 31 39 31 39 34 38 39              # cin "01919489"
     ...
```

### Cs-Event ASN.1

```asn1
Cs-Event ::= ENUMERATED {
    call-establishment (1), answer (2), supplementary-Service (3),
    handover (4), release (5), sMS (6), location-update (7),
    subscriber-Controlled-Input (8), called-Subscriber-Access (9),
    serving-System-Report (10), object-Information-Modified-Notification (11),
    power-On (12), power-Off (13), dTMF (14), x3-Channel-State (15),
    object-Deleted-Notification (16), media-Supplementary-Information (17),
    ims-Gen-IRI-Report (18)
}
```

## 完整 CDR 字段定义表

| 字段名 | 含义 | 取值说明 | 类型 |
|--------|------|---------|------|
| CdrType | 详单类型 | LigCdr | string |
| LIID | 设控目标 ID | | string |
| CidNum | CIN，区分是否同一个通话 | | string |
| OperID | 运营商 ID | | string |
| NeidType | 网元类型 | | int |
| Neid | 网元 ID | | string |
| Vneid | 虚拟网元 ID | | string |
| CaptureTime | 捕获时间 | 时间戳 | string |
| Vendor | 厂家名称 | zte/hw/ericsson/nsn/alu/utimaco | string |
| NetworkType | 网络类型 | 1-CS, 2-PS, 3-EPC, 4-IMS, 5-5GC | int |
| ReportType | 报告类型 | 1-MM, 2-CALL, 3-SMS, 4-VIDEO, 5-FAXES, 6-OTHER | int |
| EventDetail | 事件详情 | 见 EventDetail 表 | int |
| EventDirection | 事件方向 | CALL: 1-主叫/2-被叫；SMS: 1-发送/2-接收 | int |
| IMSI | IMSI 号码 | | string |
| MSISDN | 手机号码 | | string |
| IMEI | 终端设备号 | | string |
| LocationType | 位置类型 | 1-CGI,2-LAI,3-SAI,4-ECGI,5-TAI,6-CI,7-MSCID,8-TECGI,9-AREANUMBER,10-SBCDOMAIN,11-TNCGI | int |
| Location | 位置信息 | | string |
| CcLid | 通话链路信息 | | string |
| CallDuration | 呼叫时长 | HHMMSS | string |
| CallingNum | 主叫号码 | | string |
| CalledNum | 被叫号码 | | string |
| SMSContent | 短信内容 | | string |
| GprsCorNum | PS 报告关联号 | | string |
| SsCode | 补充业务类型 | 见补充业务码表 | int |
| SsSubCode | 具体补充业务类型 | 见补充业务子码表 | int |
| RedirectingNumber | 前转号码 | | string |
| RedirectionNumber | 转移号码 | | string |
| APN | Access Point Name | | string |
| PDNAddressAllocation | 分配给 UE 的 IP | | string |
| RATType | Radio Access Type | | string |
| UELocalIPAddress | s2b untrusted wlan UE 侧 IP | | string |
| UEUdpPort | s2b untrusted wlan UE 侧 UDP 端口 | | string |
| TWANIdentifier | UE 位置(TWAN) | | string |
| SicmsOperID | SI 侧运营商 ID | | int |

## EventDetail 编码

### 公用 (1-9)
| 编码 | 事件 |
|------|------|
| 1 | ATTACH |
| 2 | DETACH |
| 3 | LOCATION UPDATE |
| 4 | SMS |

### CS (11-39)
| 编码 | 事件 |
|------|------|
| 10 | CALL_SETUP |
| 11 | ANSWER |
| 12 | SUPPLE |
| 13 | RELEASE |
| 14 | ALERT |
| 15 | HANDOVER |
| 16 | SUBSCRIBER |
| 17 | CCSETUP |
| 18 | CCCLOSE |
| 19 | DTMF |

### PS/GPRS (40-89)
| 编码 | 事件 |
|------|------|
| 40 | PDPACT |
| 41 | START_PDPACT |
| 42 | PDPCONTACTUNSUCC |
| 43 | PDPDEACT |
| 44 | PDPMOD |
| 45 | SERVSYSTEM |
| 46 | START_ATTACH |
| 47 | BEARERACT |
| 48 | STACTBEARER |
| 49 | BEARERMOD |
| 50 | BEARERDEACT |
| 51 | UEREQBEARERMOD |
| 52 | UEREQPDNCON |
| 53 | UEREQPDNDISCON |
| 54 | SERVINGEPS |
| 55-70 | PMIP/MIP/DSMIP 隧道操作 |

## 补充业务码表 (SsCode)

| 编码 | 业务 |
|------|------|
| 0x21 | Call Forwarding Unconditional |
| 0x29 | CF on Mobile Subscriber Busy |
| 0x2a | CF on No Reply |
| 0x2b | CF on Mobile Subscriber Not Reachable |
| 0x41 | Call Waiting |
| 0x50 | All Multi-Party SS |
| 0x51 | Multi-PTY |
| 0x24 | Call Deflection |
| 0x31 | Explicit Call Transfer |
| 0x11 | CLIP |
| 0x12 | CLIR |
| 0x42 | Call Hold |
| 0x61 | Closed User Group |
| 0x99 | Barring of Incoming Calls |
| 0x92 | Barring All Outgoing Calls |
| 0x93 | Barring Outgoing International Calls |
| 0x94 | Barring Outgoing Intl Except HPLMN |
| 0x71 | Advice of Charge (Information) |
| 0x72 | Advice of Charge (Charging) |
| 0-8 | SIMPLE_CALLWAIT/ADDCONF/CALLONHOLD/RETRIEVE/SUSPEND/RESUME/ANSWER/ETC/UNKNOWN |

## 排查命令

```bash
# Wireshark 过滤
frame contains "95100002"

# ZTLIG 日志按 LIID 过滤
tail -f ztlig2.*.txt | grep EncodeToJson | grep '\"LIID\":\"8070\"'

# tcpdump 抓包
tcpdump -i any host <NE_IP> and port <X2_PORT> -vvv -nn -s 0 -X
tcpdump -i any tcp port 6666 -s 0 -w x1_dump.pcap
```
