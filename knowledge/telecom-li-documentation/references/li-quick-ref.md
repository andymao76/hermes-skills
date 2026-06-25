# LI Interface Quick Reference

## BER Encoding (for X2 IRI reports)

```
T L [T L V ...] [00 00]
```

- Length ≤ 127: 1 byte
- Length > 127: first byte = 0x81, subsequent bytes = actual length
  - e.g. length 255 → `0x81 0xFF`

## HW X2 Report Header

```
aa 05 01 00 01 a5 01 a5 04 ff ff ff ff ff   # HW header
a4 82 01 a1                                    # IRI-End-Report, length 0x01a1
80 06 04 00 02 02 01 06                        # csdomainID
97 01 06                                        # iRIversion
81 05 33 31 34 39 30                            # lawfulInterceptionIdentifier (ASCII "1490")
a2 1f                                           # communicationIdentifier
     80 08 30 31 39 31 39 34 38 39              # cin
     a1 13
     ...
```

## AddressString Encoding (0x91)

First byte:
- bit 8: 1 (no extension)
- bits 765: Nature of Address (001=international)
- bits 4321: Numbering Plan (0001=E.164)

Common value: **0x91** = international + E.164

## Number Field Decoding

| Field | Contains 0x91? | Decoding |
|-------|---------------|----------|
| msISDN | Yes (indicator byte) | Strip indicator, TBCD decode |
| callingPartyNumber | Yes (MAP-format) | Strip indicator, TBCD decode |
| calledPartyNumber | Yes (MAP-format) | Strip indicator, TBCD decode |
| e164-Format | No (carries T/L) | Parse T/L first, then value |

## Cs-Event Enumeration (ETSI CS)

| Value | Event |
|-------|-------|
| 1 | call-establishment |
| 2 | answer |
| 3 | supplementary-Service |
| 4 | handover |
| 5 | release |
| 6 | sMS |
| 7 | location-update |
| 10 | serving-System-Report |
| 18 | ims-Gen-IRI-Report (IMS) |

## UMTSevent (Wireshark raw)

| Value | Event |
|-------|-------|
| 1 | CALL |
| 2 | ANSWER |
| 3 | SUPPLE |
| 5 | RELEASE |
| 6 | SMS |
| 7 | LOCATION |
| 9 | POWERON |
| a | POWERDOWN |
| d | ALTER |

## ZTLIG Process Mapping

| Process | Interface | Function |
|---------|-----------|----------|
| ztlig1 | HI1/X1 | Setup control |
| ztlig2 | HI1/X2 | IRI reporting |
| ztlig3 | EPC/DPDK | Traffic forwarding |
| ssf | SIP-I | SIP session management |
| rvf | RTP | Media processing |

## Voice File Naming

```
{LIID}.{CIN}.{OperID}.{Neid}.{Direction}
```

- Direction: 0=mixed, 1=uplink, 2=downlink
- `.fin` = completion marker (0 bytes)

## X2/X3 Correlation

| Mode | Correlation Key |
|------|----------------|
| Basic ETSI | LIID + CIN |
| TX/RX separated | LIID + CIN + Direction |
| CS (M3UA/SCCP) | ISUP message |
| SIP-I | LIID+CIN in ISUP Access Transport (SIP INVITE) |
| SIP-I 4-tuple | srcIP:port + dstIP:port (from SDP 200 OK) |

## EventDetail (CS)

| Code | Event |
|------|-------|
| 10 | CALL_SETUP |
| 11 | ANSWER |
| 12 | SUPPLE |
| 13 | RELEASE |
| 14 | ALERT |
| 15 | HANDOVER |
| 17 | CCSETUP |
| 18 | CCCLOSE |
| 19 | DTMF |

## Location Encoding (byte structure)

All location types share MCC+MNC at first 3 octets:

| Type | Octets | Fields |
|------|--------|--------|
| CGI | 5-7 | MCC+MNC + LAC + CI |
| LAI | 5 | MCC+MNC + LAC (14bit int) |
| SAI | 7 | MCC+MNC + LAC + SAC |
| RAI | 6 | MCC+MNC + LAC + RAC |
| TAI | 6 | MCC+MNC + TAC |
| ECGI | 8 | MCC+MNC + Spare/ECI |

## Ericsson LI-IMS SOAP Operations

| Operation | Purpose | Key Params |
|-----------|---------|------------|
| login | Authenticate, get sessionID | userName, password |
| createWarrant | Create interception warrant | warrantID=-1, targetNumber, neType, mcnbs |
| getWarrantList | List/search warrants | warrantID, targetNumber, neGroupName |
| modifyWarrant | Modify/terminate warrant | warrantID, state, dtlWarrants |
| deleteWarrant | Delete warrant | warrantID, targetNumber |

### createWarrant Structure
```
requestHeader (type + userID + sessionID)
  + warrantItem (warrantID=-1, targetTypeID, neGroupName, lea, ...)
  + dtlWarrantNeTypeItemArray[]
      - per neType: neType, HI2Lemf, isDataMonitoringOnly, mcnbs[]
```

### neType Values
MSC, OV_MSC, HLR, OV_HLR, GPRS, OV_GPRS, FIX, OV_FIX,
SIPSERVER, OV_SIPSERVER, MOWLAN, OV_MOWLAN, BBNAS, OV_BBNAS,
OV_NGN, AAASERVER, OV_AAASERVER, APPSERVER, 1357_ULIS,
HSS_GPRS, HSS_SIPSERVER, 5GCORE

### supplementaryInfo Bitmask

| Bit | Hex | Dec | Feature |
|-----|-----|-----|---------|
| 0 | 0x0001 | 1 | LIPA_ON (Location授权) |
| 1 | 0x0002 | 2 | ACCURATE_POS (事件触发) |
| 2 | 0x0004 | 4 | SIMPLE_POS |
| 3 | 0x0008 | 8 | ON_DEMAND_POS |
| 4 | 0x0010 | 16 | PERIODIC_POS |
| 5 | 0x0020 | 32 | GEO_FENCING_POS |
| 6 | 0x0040 | 64 | ALL_PHONES_POS |
| 7 | 0x0080 | 128 | LOCATION_POS |
| 8 | 0x0100 | 256 | CR_ON (位置变更) |
| 9 | 0x0200 | 512 | CELL_REPORTING |
| 10 | 0x0400 | 1024 | DOMAIN_WILDCARD |

MSC supports: bits 0-4 (1+2+4+8+16 = 31 max)
GPRS supports: bits 0-4 + 8-9 (up to 799)
SIPSERVER supports: bits 0 + 10 (1 or 1025)

## ISUP Signal Flow (OpenVox/SS7)

IAM → ACM → ANM → ... → REL → RLC

| Signal | Meaning |
|--------|---------|
| IAM | Initial Address Message (call setup) |
| ACM | Address Complete (routing done) |
| ANM | Answer (called party answered) |
| REL | Release (hangup request) |
| RLC | Release Complete (confirmed) |

## 3口 TLV Tags (SICMS)

| Tag | Type | Length | Encoding |
|-----|------|--------|----------|
| IMSI (SUPI) | 1 | 8 | decimal BCD, pad F, big-endian |
| MSISDN (GPSI) | 2 | 8 | decimal BCD, pad F |
| IMEI (PEI) | 3 | 8 | decimal BCD, pad F |

## Network Type Encoding (ztlig2)

| Value | Meaning | Value | Meaning |
|-------|---------|-------|---------|
| 1 | CS | 11~14 | CS_2G~5G |
| 2 | PS | 15~18 | PS_2G~5G |
| 3 | EPC | | |
| 4 | IMS | | |
| 5 | 5GC | | |

## SSF interfaceType Modes

| Value | Mode |
|-------|------|
| 1 | SIP-I |
| 2 | TS-102232-5 |
| 3 | Mavenir |
| 4 | IMS-base |
| 5 | TS-102232-6 |

## voiceCtrlType (SSF→RVF)

| Value | Meaning |
|-------|---------|
| 1 | Start (media copy begin) |
| 2 | Update (media param update) |
| -1 | Ringing |
| -2 | Answer |
| -4 | Stop (media copy end) |

---

## 5GC SVC LI 接口速查

### 5GC 四接口模型

| 接口 | 协议 | 方向 | 用途 |
|------|------|------|------|
| X1 | TCP + ASN.1 BER (回显除外) | ADMF→NF (LIG主动连) | LI目标设置/DF地址下发 |
| X1M | HTTP/HTTPS | NE→ADMF (NE主动连) | LI证书管理(5GC新增) |
| X2 | TCP + ASN.1 BER | NF→DF2 | IRI报告 |
| X3 | UDP 或 TCP | UPF/GGSN-U→DF3 | IDP报告/通信内容 |

### 5GC TNEType

| TNEType | 值 | 全称 | 逻辑包含 |
|---------|-----|------|---------|
| UDM | 105 | Universal Data Management | UDM, HSS |
| UNC | 162 | Universal Network Controller | AMF, SMF, SMSF, MME, SGSN, S-GW-C, P-GW-C, GGSN-C |
| UDG | 163 | Universal Distributed Gateway | UPF, S-GW-U, P-GW-U, GGSN-U |
| USN | 160 | Universal Subscriber Node | MME, SGSN, 集成 |

### 5GC FUNCType (Bit7=1)

| FUNCType | 值 | 二进制 |
|----------|------|--------|
| AMF | 0x81 | 1 0000001 |
| SMF | 0x82 | 1 0000010 |
| SMSF | 0x83 | 1 0000011 |
| UPF | 0x84 | 1 0000100 |

### 传统 FUNCType (Bit7=0, EPS)

| Bit7(MSB) | 6 | 5 | 4 | 3 | 2 | 1 | 0(LSB) |
|-----------|---|---|---|---|---|---|---|
| 0 | Reserved | Reserved | Reserved | GGSN | P-GW | S-GW | MME | SGSN |

### 安全要求（5GC）

| 接口 | 安全 |
|------|------|
| X1 (TCP) | TLS ≥ 1.1 |
| X1M (HTTP) | HTTPS |
| X2 (TCP) | TLS ≥ 1.1 |
| X3 (UDP) | DTLS ≥ 1.1 |
| X3 (TCP) | TLS ≥ 1.1 |

双向认证，推荐 X.509 PEM。

### LIOID

- 32-bit 无符号整数
- 同一NE上每个LI目标唯一
- (目标编号+编号类型)组合不同 → 分配不同LIOID（即使同一用户）
- ADMF分配最小化处理负荷的值

### LIRP 消息类型

| 类型 | Hex |
|------|-----|
| IDP通知 | 0xC0 |
| IDP通知确认 | 0xC1 |
| IRI通知 | 0xC2 |
