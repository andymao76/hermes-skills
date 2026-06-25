# HW PS IRI Packet Decode Example

Example of a real Huawei PS domain X2/IRI BER packet captured during learning session (2026-06-18).

## Raw Packet

```
0000  4f c2 00 7f 00 00 01 06  a0 02 00 00 00 04 ff ff   O······ ········
0010  30 7d a3 19 a0 17 80 12  32 30 32 35 30 34 30 32   0}······ 20250402
0020  31 33 34 32 30 38 2e 30  30 31 81 01 00 a9 24 30   134208.0 01····$0
0030  22 80 01 03 a1 1d 81 08  53 18 97 85 30 86 53 f0   "······· S···0·S·
0040  83 08 36 06 01 30 83 18  99 f4 86 07 91 52 91 58   ··6··0·· ·····R·X
0050  95 87 88 94 01 18 ba 12  80 03 69 73 70 a1 0b 80   ········ ··isp···
0060  01 00 a1 06 81 04 0a c8  05 6b bf 24 22 8d 01 07   ········ ·k·$"···
0070  b7 1d 81 0d 18 36 f6 10  2b cc 36 f6 10 00 04 fa   ·····6·· +·6·····
0080  02 86 0c 0b 41 36 f6 10  2b cc 36 f6 10 2b cd      ····A6·· +·6··+·c
```

## Key Identifiers Decoded

| Field | Value |
|-------|-------|
| TNE Type | a0 = USN (SGSN/MME) |
| Event Type | 03 = PS attach / PDN connection request |
| Timestamp | 2025-04-02 13:42:08.001 UTC |
| **IMSI** (TBCD) | `53 18 97 85 30 86 53 f0` → **35817958036835** |
| **MSISDN** (TBCD) | `36 06 01 30 83 18 99 f4` → **636010033881994** |
| **IMEI** (TBCD) | `91 52 91 58 95 87 88` → **19251985597888** |
| APN | "isp" (ASCII) |
| SGSN IP | 10.200.5.107 |
| GGSN/PGW IP | 65.54.246.16 |

## TBCD Decoding Pattern

TBCD (Telephony Binary Coded Decimal) swaps nibbles within each byte:

```
Raw byte:   0x53 → nibbles 5,3 → swap → digits 3,5
Full byte:  0x53 0x18 → nibbles [5,3][1,8] → swap → [3,5][8,1]
```

If the last nibble is 0xF, it's padding (14-digit IMSI or IMEI).

## Header Structure (HW PS)

| Offset | Size | Field |
|--------|------|-------|
| 0x00 | 1 | Message type (0x4f = PS) |
| 0x01 | 1 | Control flags (0xc2) |
| 0x02 | 2 | Total length (0x007f = 127 bytes after header) |
| 0x04 | 2 | Reserved / sequence |
| 0x06 | 2 | Version / subtype |
| 0x08 | 2 | TNE tag+len (0xa0 0x02) |
| 0x0A | 2 | TNE subtype |
| 0x0C | 2 | IE count indicator |

See also: `~/knowledge/hi2/华为LI协议/` for additional HW ASN.1 definitions.
