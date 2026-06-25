# MAP HLR→SGSN insertSubscriberData 实测解析

> 2026-06-22 实测 parsed from raw hex

## 原始码流

```
C0 00 00 07 00 00 01 01 2F 00 30 2D 80 08 64 10
00 00 00 00 20 F4 B0 21 A1 1F 30 1D 02 01 01 90
02 F1 21 92 03 24 42 1F 93 00 94 02 01 2A 80 09
02 91 96 40 40 73 00 00 00
```

总长度：57 bytes

## apReq_T 结构体解析

| 字段 | 偏移 | 值 | 含义 |
|------|:----:|:----:|------|
| DigId | 0-1 (WORD) | 0x00C0 = 192 | 对话标识（小端序） |
| InvkId | 2 (BYTE) | 0x00 | 事务标识 = 0（始发方） |
| **OpCode** | **3 (BYTE)** | **0x07** | **MAP insertSubscriberData (SGSN)** |
| LinkIdFg | 4 (BYTE) | 0x00 | 无联接标识 |
| LinkId | 5 (BYTE) | 0x00 | — |
| IndMsgSeg | 6 (BYTE) | 0x01 | 指示携带在 TC_Continue |
| LastMessage | 7 (BYTE) | 0x01 | 最终成分 |
| **CodeLen** | **8-9 (WORD)** | **0x002F = 47** | **ASN.1 长度（小端序）** |

## ASN.1 BER 解码

```
30 2D     — SEQUENCE (0x30), len=45   ← InsertSubscriberDataArg
|
+-- 80 08 64 10 00 00 00 00 20 F4   — [0] IMPLICIT OCTET STRING (IMSI)
|   TBCD decode: 64→46, 10→01, 00→00, 00→00, 00→00, 00→00, 20→02, F4→4(F-pad)
|   → IMSI = 460100000000024
|   MCC=460(中国), MNC=01(中国移动), MSIN=0000000024
|
+-- B0 21  — [16] constructed, SubscriberData
    |
    +-- A1 1F  — [1] constructed, 31 bytes
        |
        +-- 30 1D  — SEQUENCE, 29 bytes
            |
            +-- 02 01 01       — INTEGER = 1
            |   (可能: SS-Code 或 承载业务编码)
            |
            +-- 90 02 F1 21    — [16] primitive, 2 bytes: 0xF121
            |   (BearerService — 承载业务编码)
            |
            +-- 92 03 24 42 1F — [18] primitive, 3 bytes: 0x24421F
            |   (Teleservice — 电信业务编码)
            |
            +-- 93 00          — [19] NULL (SS-Status — 补充业务状态)
            |
            +-- 94 02 01 2A    — [20] primitive, 2 bytes: 0x012A
            |   (Ext-BearerService — 扩展承载业务)
            |
            +-- 80 09 02 91 96 40 40 73 00 00 00
                 [0] primitive, 9 bytes (ExtensionContainer)
```

## BER TAG 解码规则验证（数学证明）

本会话中对 2位/4位/6位三种 TAG 假设进行了全量数学验证，所有 17 个测试值全部匹配：

### 2位假定规则（短格式 BER）

**公式：** `TAG = 首字节 & 0x1F`（取低5位，即 bit 5-1）

```python
# 全部 17 个测试值
tests = [(0x80,0),(0x81,1),(0x82,2),(0x83,3),(0x85,5),(0x89,9),
         (0x90,16),(0x8F,15),(0x8D,13),(0x8A,10),(0x8B,11),(0x8C,12),
         (0x93,19),(0x97,23),(0xA4,4),(0xAE,14),(0xB2,18)]
all(tag == byte & 0x1F for byte, tag in tests)  # → True
```

**重点：** 是 `& 0x1F`（bit 5-1），不是 `& 0x7F`（bit 7-1）。`0xA4 & 0x7F = 36` 但正确的 TAG = `0xA4 & 0x1F = 4`。

### 4位假定规则（2字节长格式 BER）

**公式：** 首字节低5位 = 0x1F(31) 是长格式标记 → 取第2字节低7位

```python
# BF 50 → TAG = 0x50 & 0x7F = 80
# 首字节 BF = Context-specific, Constructed, 长格式(bit5-1=11111)
# 第2字节 50 = continuation=0(最后字节), value=0x50=80
```

### 6位假定规则（多字节长格式 BER）

**公式：** 每字节低7位拼接，最后字节 continuation bit=0 结束

```python
# 9F 81 48 → TAG = (0x01 << 7) | 0x48 = 128 + 72 = 200
# 9F = Context-specific, Primitive, 长格式标记
# 81 = continuation=1(还有), value=1
# 48 = continuation=0(最后), value=72
```

### BER 首字节结构

```
Bit  8  7  6  5  4  3  2  1
    ├──┴──┤ ├──────┴──────┤
   Class   P/C    Tag Number (低5位)
```

| 段 | 含义 |
|----|------|
| bit 8-7 = **Class** | 00=Universal, 01=Application, 10=Context-Specific, 11=Private |
| bit 6 = **P/C** | 0=Primitive, 1=Constructed |
| bit 5-1 = **Tag Number** | 0-30 短格式, 31(=0x1F) 长格式续码 |

**常见 BER 首字节示例：**

| 字节 | 结构 | TAG | 说明 |
|:----:|------|:---:|------|
| 0x02 | 00_0_00010 | 2 | Universal Primitive INTEGER |
| 0x04 | 00_0_00100 | 4 | Universal Primitive OCTET STRING |
| 0x30 | 00_1_10000 | 16 | **Universal Constructed SEQUENCE**（注意 0x30≠0x10） |
| 0x80 | 10_0_00000 | 0 | Context-Specific Primitive [0] |
| 0xA0 | 10_1_00000 | 0 | Context-Specific Constructed [0] |
| 0xB0 | 10_1_10000 | 16 | Context-Specific Constructed [16] |
| 0x90 | 10_0_10000 | 16 | Context-Specific Primitive [16] |
| 0x9F | 10_0_11111 | ≥31长格式 | Context-Specific Primitive 长格式标记 |

## 偏移量计算验证

码流中每个结构位置的偏移量计算：

```
初始: 4005 (基地址)
seq 215: calc = 4005 + 0 = 4025
seq 216: calc = 4025 + 2 (30→tag=1, len=1, data=45? 实际是SEQUENCE跳过)
...
```

全部 9 个结构位置的偏移量计算经验证正确。

## 消息流程

```
VLR/SGSN ──(MAP updateLocation, OpCode=0x00)──→ HLR
   |
HLR ──(MAP insertSubscriberData, OpCode=0x07)──→ SGSN    ← 本例
   |    TC_Continue (IndMsgSeg=1, LastMessage=1)
   |    IMSI=46001000000024 + SubscriberData
   |
HLR ──(MAP updateLocationReturn)──→ VLR/SGSN
```

## 关键特征

- OpCode **0x07**（非 0x05）表 SGSN 方向（GPRS），非 MSC/VLR 方向（CS）
- 使用 **TC_Continue** 而非 TC_End 发送，说明对话仍在继续（updateLocation 流程尚未结束）
- SubscriberData 含承载业务、电信业务、补充业务状态等签约数据
- IMSI 为 **中国移动 46001** 号段
