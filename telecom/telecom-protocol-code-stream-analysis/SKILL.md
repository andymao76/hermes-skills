---
name: telecom-protocol-code-stream-analysis
title: 电信协议码流分析工作流
description: 用户分享原始 hex 码流（信令抓包/APDU/PDU）时，逐字节解析、C 结构体映射、ASN.1 TLV 解码、字段含义解读的标准化工作流。覆盖 MAP/TCAP/GTP/SIP/NAS/NGAP 等 Core Network 协议。
category: telecom
tags:
  - telecom
  - protocol-analysis
  - code-stream
  - hex-decode
  - ASN1
  - MAP
  - TCAP
  - network-signaling
---

# 电信协议码流分析工作流

## 触发条件

用户直接发送一段 hex 码流（如 `C0 00 00 07 00 00 01 01 2F 00 30 2D...`），或提及「码流」「抓包」「hex dump」「PDU」「二进制报文」等关键词，要求逐字节解析。

## 工作流程

### 第 1 步：前置分析

1. **确认码流长度** — 统计总字节数
2. **识别协议层** — 根据码流特征判断：
   - 有 C 结构体头部（WORD/BYTE 字段）+ ASN.1 内容 → **TCAP/MAP**（SS7/SIGTRAN 上层）
   - 全是 ASN.1 TLV（30/31/80/81/A0/A1...）→ **RRC/NAS/NGAP**
   - 有固定头（GTP-U Header: Flags+Message Type+Length）→ **GTP**
   - SIP 文本开头 → **SIP/IMS**
3. **小端序 vs 大端序** — SS7/SIGTRAN 协议通常大端序（network byte order）；apReq_T 等内部结构体可能小端序，根据协议规范确认

### 第 2 步：C 结构体头部解析（如适用）

如果有已知的 C 结构体定义（如 `apReq_T`），按字段逐字节分解：

| 字段 | 偏移 | 长度 | 值 | 含义 |
|------|:----:|:----:|:----:|------|
| DigId | 0-1 | WORD | 小端序 | 对话标识 |
| InvkId | 2 | BYTE | — | 事务标识（通常 0=始发） |
| OpCode | 3 | BYTE | **0x07** | **操作码 — 识别 MAP 操作** |
| LinkIdFg | 4 | BYTE | — | 联接标识标记 |
| LinkId | 5 | BYTE | — | 联接标识 |
| IndMsgSeg | 6 | BYTE | 0/1 | 指示消息携带在 TC_Continue(1) 或 TC_End(0) |
| LastMessage | 7 | BYTE | 0/1 | 是否最终成分 |
| CodeLen | 8-9 | WORD | — | ASN.1 码流长度 |

### 第 3 步：MAP OpCode 操作识别

| OpCode | 操作 | 方向 | 说明 |
|:------:|------|------|------|
| 0x00 | updateLocation | MSC/VLR → HLR | 位置更新 |
| 0x01 | cancelLocation | HLR → VLR | 取消位置 |
| 0x02 | purgeMS | VLR → HLR | 清除 MS |
| 0x03 | sendIdentification | VLR → HLR | 发送标识 |
| 0x04 | restoreData | VLR → HLR | 恢复数据 |
| 0x05 | insertSubscriberData (CS) | HLR → MSC/VLR | 插入签约数据（电路域） |
| 0x07 | insertSubscriberData (GPRS) | HLR → SGSN | 插入签约数据（分组域） |
| 0x06 | deleteSubscriberData | HLR → VLR | 删除签约数据 |
| 0x3B | sendAuthenticationInfo | HLR → AuC/HLR | 发送鉴权信息 |
| 0x4B | provideSubscriberLocation | GMLC → HLR | 定位查询 |

### 第 4 步：ASN.1 TLV/PER 内容解析

#### UE ↔ Network (RRC/NAS) — PER Aligned 编码

- 使用 `tshark -Y` 或 `wireshark` 配合 ASN.1 解码器
- NAS 消息结构：Protocol Discriminator (½ byte) + EPS Bearer ID (½ byte) + Procedure Transaction Identity + Message Type
- RRC/NAS ASN.1 定义在 TS 24.301/24.501/36.331/38.331 的 `.asn1` 附件中

#### Network ↔ Network (MAP/CAP) — BER/DER 编码

- 基本结构：**Tag + Length + Value**
- Tag 分类：
  | Tag (hex) | 含义 |
  |:---------:|------|
  | 0x02 | INTEGER |
  | 0x04 | OCTET STRING |
  | 0x05 | NULL |
  | 0x30 | SEQUENCE/SEQUENCE OF |
  | 0x80-0xBF | Context-specific [0]-[63] primitive |
  | 0xA0-0xBF | Context-specific [0]-[63] constructed |

- **Context-specific tag 命名规则**：
  - `0x80` = [0] primitive, `0xA0` = [0] constructed
  - `0x81` = [1] primitive, `0xA1` = [1] constructed
  - `0x90` = [16] primitive, `0xB0` = [16] constructed

#### 字段解码规则

- **IMSI (TBCD 编码)**：
  - 原始字节如 `64 10 00 00 00 00 20 F4`
  - 解码：每个 nibble 反转→ `64→46, 10→01, 00→00, ...`
  - → `460100000000024`
  - MCC=460(中国), MNC=01(中国移动), MSIN=0000000024
  - 如果字节数为奇数，最后一个 nibble 为 filler (F)

### 第 4 步附加：BER TAG 三种假设分析（TAG 字段试探法）

当 BER TLV 结构中 TAG 字段长度不确定时（特别是 context-specific [0]-[63] 标签），使用三种假设
同时分析，通过比对结果交叉验证编码方案：

| 假设 | 规则 | 适用场景 |
|:----:|------|----------|
| **2位假定 (短格式)** | TAG = 首字节 & 0x1F（BER 短格式低5位 = tag number） | 标准 BER 短格式标签（tag < 31） |
| **4位假定 (2字节长格式)** | 首字节低5位=11111 ? 取第2字节低7位 : 取低5位 | 2 字节长格式（1 个续字节） |
| **6位假定 (多字节长格式)** | 标准 BER 长格式多字节拼接，每字节低7位累加，最后字节 continuation=0 | 多字节长格式标签（tag ≥ 128 时常见） |

**规则详解与数学验证：**

**2位假定 = 首字节低5位（bit 5-1）：**
- `0x80` = 1000_0000 → bit 5-1 = 00000 = **TAG 0** ✓
- `0x90` = 1001_0000 → bit 5-1 = 10000 = **TAG 16** ✓
- `0xA4` = 1010_0100 → bit 5-1 = 00100 = **TAG 4** ✓
- `0xB2` = 1011_0010 → bit 5-1 = 10010 = **TAG 18** ✓
- 注意：这不是简单的 `& 0x7F`（那是 bit 7-1），而是 `& 0x1F`（bit 5-1）

**4位假定 = 第2字节低7位（仅当首字节低5位=31时触发长格式）：**
- `BF 50` = 10_1_11111 + 0_1010000 → TAG = 0x50 = **80** ✓
- 首字节 `BF`：Context-specific, Constructed, 长格式标记

**6位假定 = 多字节续码拼接（标准 BER 长格式）：**
- `9F 81 48`：
  - `9F` = 10_0_11111 (Context-specific, Primitive, 长格式标记)
  - `81` = 1_0000001 (continuation=1, value bits=1)
  - `48` = 0_1001000 (continuation=0, last, value bits=72)
  - TAG = (1 << 7) | 72 = **200** ✓

**验证示例**（取自 MAP insertSubscriberData 码流，全部 17 个 TAG 值经数学验证正确）：

```
2位假定全线测试：
0x80→TAG=0 ✓  0x81→TAG=1 ✓  0x82→TAG=2 ✓  0x83→TAG=3 ✓
0x85→TAG=5 ✓  0x89→TAG=9 ✓  0x90→TAG=16 ✓ 0x8F→TAG=15 ✓
0x8D→TAG=13 ✓ 0x8A→TAG=10 ✓ 0x8B→TAG=11 ✓ 0x8C→TAG=12 ✓
0x93→TAG=19 ✓ 0x97→TAG=23 ✓ 0xA4→TAG=4 ✓  0xAE→TAG=14 ✓
0xB2→TAG=18 ✓
```

**结构遍历输出示例：**
```
序列 | 偏移量 | 增量 | 16进制 | 10进制 | 2位TAG | 2位原值 | 4位tag | 4位原值 | 6位tag | 6位原值
--------------------------------------------------------------------------------------------------------
 215 | 4005.000 | 0.000 | 30 | 48 | 16 | 30 | 16 | 30 | 16 | 30
 216 | 4007.000 | 2.000 | 80 | 128 | 0 | 80 | 0 | 80 | 0 | 80
 217 | 4017.000 | 10.000 | B0 | 176 | 16 | B0 | 16 | B0 | 16 | B0
 218 | 4019.000 | 2.000 | A1 | 161 | 1 | A1 | 1 | A1 | 1 | A1
```

**判断方法：** 交叉对比三个假设的 TAG 值变化模式。合理的 BER 编码应呈现出：
- 短格式 TAG（0x01-0x1E）在三种假设下值一致
- 长格式 TAG（≥ 31）仅在正确字节数假设下才得到合理值
- 上下文标签 [0]-[63] 常用于 ASN.1 隐式标记（implicit tagging）
- 三种假设配合使用时，通过值的变化模式可以推断数据的 BER 编码层级

**配套工具：**
- `scripts/ber-tag-analyzer.py` — 实现以上三种假设的自动分析脚本（支持结构遍历和逐字节两种模式）
- `scripts/ber-tag-verify.py` — 数学验证脚本，对已知数据运行可验证 TAG 解码正确性

### 第 5 步：消息流程关联

按协议上下文还原端到端流程：

- **MAP**: HLR → SGSN/VLR (insertSubscriberData) 通常是位置更新流程的一部分
  ```
  VLR/MSC ──(MAP updateLocation)──→ HLR
  HLR ──(MAP insertSubscriberData)──→ VLR/SGSN  ← 当前码流
  HLR ──(MAP insertSubscriberData)──→ VLR/SGSN  ← 多个签约数据
  HLR ──(MAP updateLocationReturn)──→ VLR/MSC
  ```

- **SIP**: UE → P-CSCF → I-CSCF → S-CSCF → AS
- **NAS**: UE ↔ MME/AMF
- **GTP**: eNB/SGW/PGW/SMF/UPF

### 第 6 步：输出格式

采用表格 + 文字说明的紧凑格式，避免大段原文：

| 字段 | 值 | 含义 |
|------|:---:|------|
| 原始码流 | `C0 00 00 07 00 00 01 01 ...` | 57 bytes |
| 协议 | MAP insertSubscriberData | OpCode=0x07 |
| 方向 | HLR → SGSN | TC_Continue |
| IMSI | 460100000000024 | 中国移动(46001)用户 |

ASN.1 内部结构用缩进树状格式：

```
30 2D          — SEQUENCE, 45 bytes
+-- 80 08 ...  — [0] IMSI, 8 bytes
+-- B0 21      — [16] constructed, SubscriberData
    +-- 30 1D  — SEQUENCE, 29 bytes
        +-- 02 01 01       — INTEGER = 1
        +-- 90 02 F1 21    — [16] BearerService
        +-- 92 03 24 42 1F — [18] Teleservice
        +-- 93 00          — [19] NULL (SS-Status)
        +-- 94 02 01 2A    — [20] Ext-BearerService
        +-- 80 09 ...      — [0] ExtensionContainer
```

## 常用 OpCode 速查

### MAP OpCode（TS 29.002 §14）

| 操作 | OpCode | 方向 |
|------|:------:|------|
| updateLocation | 0x00 | MSC → HLR |
| cancelLocation | 0x01 | HLR → VLR |
| insertSubscriberData | 0x05 / 0x07 | HLR → VLR/SGSN |
| deleteSubscriberData | 0x06 | HLR → VLR |
| sendAuthenticationInfo | 0x3B | HLR → AuC |
| provideSubscriberLocation | 0x4B | GMLC → HLR |

> 注：OpCode 0x07 = insertSubscriberData 用于 GPRS（SGSN 方向）
> OpCode 0x05 = insertSubscriberData 用于 CS（MSC/VLR 方向）

### TCAP 消息类型

| 类型 | Tag | 说明 |
|:----:|:---:|------|
| TC-BEGIN | 0x62 | 开始对话 |
| TC-CONTINUE | 0x62 | 继续对话 |
| TC-END | 0x62 | 结束对话 |
| TC-ABORT | 0x67 | 异常终止 |
| TC-INVOKE | 0xA1 | 调用成分 |
| TC-RESULT | 0xA2 | 返回结果 |
| TC-RETURN-ERROR | 0xA3 | 返回错误 |
| TC-REJECT | 0xA4 | 拒绝 |

### PCAP 文件分析流程（信令抓包/ORI文件）

当码流被封存在 PCAP / ORI / LI 上报文件中时，先提取并识别封装层，再进入 BER/PER 分析。

#### 常见封装格式

| 格式 | 特征 | 典型协议 |
|------|------|---------|
| **PCAP (libpcap)** | 文件头 `D4 C3 B2 A1` 或 `A1 B2 C3 D4` | Wireshark/tcpdump 标准格式 |
| **华为 SBC LI 上报** | 数据层头部 `aa05` magic | VoLTE SIP + LI 字段 |
| **ORI 文件** | `aa05 01 00 xx xx` | LI 拦截记录（呼叫详情） |

#### PCAP 分析步骤

1. **识别链路层** — tcpdump 自动解析（EN10MB=Ethernet, Linux SLL, RAW）
2. **定位协议数据**：
   ```bash
   tcpdump -r file.pcap -X -c 1              # 查看首个包
   tcpdump -r file.pcap -X 'sip' | head -30   # 过滤 SIP 消息
   tcpdump -r file.pcap -X 'udp port 20000'   # 按端口过滤
   ```
3. **搜索特定字段**：
   ```bash
   tcpdump -r file.pcap -X | grep -i "hex_pattern"    # 搜索16进制模式
   tcpdump -r file.pcap -A | grep -i "keyword"        # 搜索 ASCII 字段
   ```

#### 华为 SBC LI 数据层格式（aa05 magic）

华为 SBC 的 LI 上报数据使用 `aa05` 魔数标记数据层起始：

```
aa05 XX XX         — HW LI Protocol magic + 长度
YY YY YY YY        — 序列号(计数器)
01 FF FF FF FF FF  — LI 头部类型
A4 82 06 D4        — 固定头(TLV式)
80 06 XX XX XX XX XX XX  — [0] 数据字段（可能含CIN）
97 01 XX           — [23] 操作码/标识
81 05 XX XX XX XX XX     — [1] LIID (ASCII)
```

**LIID 位置：** TAG=0x81 ([1], length=5), value为5位ASCII数字
**CIN 位置：** 可能在 TAG=0x80 的 value 中编码（需视具体版本）

#### ORI 文件格式（拦截记录）

ORI 文件（如 `O1LI14071612460000031`）是 LI 系统的原始拦截记录，二进制 TLV 结构：

| TAG | 含义 | 示例 |
|:---:|------|------|
| `81 05` | LIID (ASCII 5位) | `31 30 30 31 33` = "10013" |
| `97 01` | 操作码/标识 | `06` |
| `A2 0E` | 电路/会话标识组 | 含子字段 |
| `A1 0C` | 子标识组 | 含子字段 |
| `80 03` | 电路/通道ID | `30 30 31` = "001" |
| `A1 05 81 03` | OPERID (BCD 反序编码) | `84 13 F5` |
| `A3 19` | 时间戳组 | 含时间字段 |
| `80 12` | 时间戳 ASCII | `32303234313031323132343433342E353637` = "20241012124434.567" |
| `A9 1A 30 18` | 被叫号码组 | 含 `tel:+249...` |
| `89 11 74 65 6C` | 号码字符串 | `tel:+249119284261` |

#### SIP-I ISUP 中的 LI 字段定位

SIP-I（SIP with encapsulated ISUP）消息中，LI 数据嵌入在 ISUP body 的 subaddress 参数中：

**Calling Party Subaddress → LIID：**
- ISUP 参数类型：Generic Number / Called Party Number
- LIID 使用**反序BCD编码**嵌入 subaddress：
  - 原始值：84335
  - BCD normal：`84 33 5F`
  - 反序BCD（swap nibbles）：`48 33 F5`
  - 特征：以 `A8` 或其他 subaddress 类型标记开头

**Called Party Subaddress → CID + OPERID：**
- CID：009515677 → BCD normal `00 95 15 67 7F`，反序 `00 59 51 76 F7`
- OPERID：63601 → ASCII `3633363031` 或 BCD 编码
- 在 ORI 文件中 OPERID 以 ASCII 形式存储

#### LIID + CallID 唯一会话标识

合法监听系统中，唯一会话由以下组合确定：
```
LIID + CallID = 唯一会话
```
- LIID：监听授权标识符（拦截目标标识）
- CallID：SIP Call-ID 头域值（或 ISUP CIC）
- 同一 LIID 下不同 CallID 表示不同会话

#### 数据点核对验证方法

验证如 "40eb9fc → 68073980 = CIN" 等声明的标准步骤：

```python
# 1. 确认16进制→十进制转换
assert 0x40EB9FC == 68073980  # ✓

# 2. 确认 BCD/反序BCD 编解码
def bcd_reverse_encode(value: int) -> str:
    digits = [int(d) for d in str(value)]
    bcd = []
    i = 0
    while i < len(digits):
        if i + 1 < len(digits):
            bcd.append((digits[i] << 4) | digits[i+1])
        else:
            bcd.append((digits[i] << 4) | 0x0F)  # F padding
        i += 2
    rev = [((b & 0x0F) << 4) | ((b >> 4) & 0x0F) for b in bcd]
    return ' '.join(f'{b:02X}' for b in rev)

# 3. 在二进制文件中定位
with open("file.ori", "rb") as f:
    data = f.read()
pos = data.find(bytes.fromhex("4833F5"))  # LIID=84335 反序BCD
```

**CIN 字段说明：** CIN (Call Identification Number) 是 LI 系统中用于 X2/X3 关联的标识，通常在 ISUP/IAM 消息中编码。不同厂商编码方式不同——华为有时将 CIN 编码为 4 字节整数或 8 字节 ASCII 字符串，具体位置需结合 PCAP 实际数据验证。40EB9FC（小端序 4 字节）在目标 pcap 的 RTP 流中多次出现（40EB8780、40EB9CED），需确认是否实际为 RTP 媒体数据而非 CIN。
```

#### 注意事项

- **LI 数据安全等级（LEVEL 5）**：LIID/IMSI/MSISDN/IMEI/CIN 等数据禁止发送到外部 LLM
- **PCAP 文件命名即线索**：文件名常包含 LIID、IP、端口等关键信息
- **ORI 文件时间戳**：`O1LI14071612460000031` → 2024-07-16 12:46:00 + 序号 031
- **反序BCD vs 正常BCD**：不同厂商实现不同，华为常用反序BCD编码LI ID
- **华为SUDAN项目特征**：文件名含 `sudan`，号码前缀 `+249`（苏丹国家码）

### 第 7 步：PER 码流分析流程（RANAP/NGAP/NAS 等 PER 编码协议）

当码流为 PER (Packed Encoding Rules) 编码时（区别于 BER/DER 的 TLV 结构），采用以下专用流程：

#### PER vs BER 快速区分

| 特征 | BER/DER | PER (Aligned) |
|------|---------|---------------|
| Tag 编码 | 显式 TLV，Tag 占用独立字节 | 无显式 Tag，接收方需知道 ASN.1 结构 |
| 长度编码 | 短/长/不定长格式 | 根据 ASN.1 约束自动确定（固定/可变） |
| 典型应用 | MAP/CAP/SNMP/LDAP | RANAP/NGAP/NAS/RRC |
| 字节对齐 | 天然字节对齐 | 可对齐(A-PER)或非对齐(U-PER) |

#### 准备工作

1. **获取对应的 ASN.1 定义文件** — 从 3GPP TS 或厂商文档中找到 `.asn1` 或 `.txt` 格式的类型定义
2. **理解 TOP 层 CHOICE** — 大多数 PER 协议数据单元 (PDU) 以 CHOICE 开始。需要知道扩展位和 choice index 的比特位编码
3. **确定 PER 对齐模式** — Aligned PER (A-PER) 将字段对齐到字节边界；Unaligned PER (U-PER) 按位紧凑排列

#### 逐层解码步骤

1. **CHOICE 解码**：首位 = 扩展位 (0=不扩展)，后续位 = 选择索引
   ```
   ext(1bit) + choice_index(#bit) + [padding to byte boundary]
   ```

2. **SEQUENCE 解码**：首位 = 扩展位，后续位 = OPTIONAL bit map
   - ext=0: OPTIONAL bit map 覆盖 `...` 前的可选字段
   - ext=1: 无 OPTIONAL bit，后续是扩展增加字段
   ```
   ext(1bit) + optional_bits + [padding to byte boundary]
   ```

3. **字段长度规则**：
   - 固定尺寸（如 INTEGER(0..255)）→ `ceil(log2(range))` 位
   - 可变尺寸（如 SEQUENCE OF SIZE(0..65535)）→ 16 位长度前缀
   - Open type (任何类型) → 8/16 位长度前缀 + 值

4. **基本类型 PER 编码**：
   - INTEGER: 约束范围决定位数 `ceil(log2(max-min+1))`
   - ENUMERATED: `ceil(log2(N))` 位
   - OCTET STRING: 固定尺寸直接编码；可变尺寸加长度前缀
   - BIT STRING: 固定尺寸直接编码

5. **嵌套 Open Type 的长度分层**：
   ```
   ProtocolIE-Field value (open type):
     outer_length(8bit) = 内部总字节数
     └── 实际 PER 内容（如 OCTET STRING 的 PER 编码）
          内层长度(8bit) + 内容
   ```

#### pcap 实测验证模式

当系统中有 `.pcap` 文件时，通过实测数据交叉验证分析结果的正确性：

1. **提取原始码流** — 用 Python 解析 pcap 文件，找到 RANAP/SCTP 等协议数据单元
2. **定位 PER 码流起始位置** — 搜索已知的 PDU 头部模式（如 `00 13 40` 对应 RANAP initiatingMessage + procedureCode=id-InitialUE-Message）
3. **比特级逐字段核对** — 验证每个字段的 PER 编码与 ASN.1 定义一致
4. **标记分析偏差** — 发现分析文档中的错误（如 OPTIONAL bit 标反、遗漏扩展容器等），写入审核报告

#### PER 码流审核输出模板

审核报告应包含：
- **逐层解码验证表** — 每层标注原始字节、ASN.1 类型、PER 编码规则、正确/错误判定
- **分析问题清单** — 明确标注 analysis.txt 中的错误
- **正确性置信度评分** — 以百分比评估原分析的准确度
- **修正建议** — 具体到字节和 bit 位置的修改建议

### 第 8 步：BER 解码器 C 实现分析（对照 API 设计模式）

当用户分享 BER 解码器的 C 语言 API 接口规范时（区别于协议码流分析），采用以下分析框架：

#### API 分类体系

| 函数类别 | 示例 | 功能说明 |
|---------|------|---------|
| **码流控制** | `BERCheckEnd()`, `BERMovDecodePtr()` | 边界检测、指针偏移 |
| **标签解码** | `BERDecodeIdentifier()`(偏移), `BERDecodeTag()`(不偏移) | 类型域解析 |
| **长度解码** | `BERDecodeLength()` | 短/长/不定长格式统一处理 |
| **基本类型** | `BERDecodeInt()`, `BERDecodeBoolean()`, `BERDecodeNULL()`, `BERDecodeEnumBYTE()`, `BERDecodeOctetStr()`, `BERDecodeBitString()` | 各基础类型解码 |
| **复合类型** | SEQUENCE(顺序/Tag驱动), CHOICE, SEQUENCE OF(显式循环/回调) | 结构体嵌套解码 |

#### 解码设计模式

| 模式 | 适用场景 | 实现方式 |
|------|---------|---------|
| **循环检测模式** | 嵌套 SEQUENCE | `do {...} while(BERCheckEnd())` 边界安全检测 |
| **顺序解码** | 无 OPTIONAL 的 SEQUENCE | 按 ASN.1 定义顺序逐个调用基本函数 |
| **Tag 驱动循环** | 含 OPTIONAL 的 SEQUENCE | 先解 Tag，`switch(id)` 分发，未知 Tag 跳过 |
| **回调模式** | SEQUENCE OF 大量元素 | 传入解码函数指针 + 类型枚举 + 计数上限 |

#### 安全工程最佳实践

| 实践 | C 代码模式 | 作用 |
|------|-----------|------|
| 边界检测 | `BERCheckEnd(begin, end, len, contentstart)` | 防止越界读取 |
| 空长度处理 | `if(0 == dlen) return DecodeOK_M` | 空内容直接返回 |
| Tag 验证 | `if(TAG_MID != id) return DecodeError_M` | 自定义结构校验 |
| 防无限循环 | `if(seq_num > MAX_COUNT) return DecodeError_M` | SEQUENCE OF 上限 |
| 字段跳过 | `BERMovDecodePtr(begin, end, dlen)` | 不解码的 OPTIONAL 字段 |

#### 与码流分析的关联

- **相同基础规则**：解码器中的 Tag/Length 解码规则与 BER 编码理论完全一致（TLV 结构）
- **双向验证**：解码器 C 代码可反向验证码流分析的正确性，反之亦然
- **应用协议**：此类 BER 解码器规范通常对应 H.248/Megaco、MAP、CAP 等协议实现

## 注意事项

- **CodeLen vs 实际长度** — C 结构体中的 CodeLen 可能与 ASN.1 解析出的 Layer 不同，前者是 ASN.1 字节流长度（不含头部），后者是包含头部
- **TCAP 层选位** — TCAP 消息中操作码可能携带在其他字段中（如 component type 后的调用/操作标识）
- **IMSI TBCD 编码** — 每两个 nibble 反转解码；如果总字节数为奇数，最后一个字节的 high nibble = F
- **小端序陷阱** — C 结构体中的 WORD 字段（如 DigId=0x00C0）不要读反为 C000
- **BER TAG 编码陷阱 — 2位假定不是 `& 0x7F`！** 新手容易误用 `byte & 0x7F`（取低7位），但 BER 短格式的 tag number 在 **位5-1**（低5位）。`0xA4 & 0x7F = 36`（错误），正确应为 `0xA4 & 0x1F = 4`。注意 `0x30`（SEQUENCE）的低5位是 `0x30 & 0x1F = 16`（而不是 48/0x30 这个值本身）。核心规则：TAG 编码 = Class(2bit) + P/C(1bit) + TagNumber(5bit)，解析时必须只取低5位。
- **BER 结构遍历陷阱：`length == 0` 不代表结束！** 在 BER TLV 遍历中，`length=0`（如 `93 00` = SS-Status NULL）只表示 value 为空，后续仍有 TLV 结构。如果在 `length == 0` 时 `break`，会遗漏后面全部节点（如 `94 02 01 2A` Ext-BearerService 和 `80 09 ...` ExtensionContainer 等）。正确做法：`length == 0` 时不调整偏移量（buf_offset 已在下一个 TAG 位置），继续循环。详见 `scripts/ber-tag-analyzer.py` 中的实现。
- **LLM 不能作为 BER 解码的交叉验证基准** — DeepSeek-V3 和 Qwen3.5 在本轮测试中均出现 BER 解析错误（IMSI 位置错误、字段名颠倒、遗漏结构层）。正确的验证方法是使用 `pyasn1` 库（见 verification 流程）或 Wireshark 内建解码器。LLM 适合辅助解读字段含义，不适合做精确的 TLV 结构验证。
- `references/ber-x690-encoding-rules-and-verification.md` — BER TAG 编码规则 (ITU-T X.690)、2/4/6位假设数学验证、pyasn1 三方验证、已知 BUG 记录
- `references/per-encoding-reference-x691.md` — PER 编码规则 (ITU-T X.691)、A-PER/U-PER 差异、编解码步骤
- `references/map-hlr-sgsn-insertsubscriberdata-example.md` — MAP insertSubscriberData 码流实测解析（C 结构体 + ASN.1 BER 解码全流程，含 2/4/6 位 TAG 数学验证）
- `references/pycrate-5g-ngap-nas-decoding.md` — pycrate NGAP IE 值格式陷阱（`(type_name, bytes)` 元组前缀截断问题）及 5G NAS-PDU 测试设备字节布局差异（消息类型偏移 byte[2] 而非标准 byte[1]）
- `references/ndpi-deep-packet-inspection-tool.md` — nDPI 开源 DPI 工具安装与使用（协议识别、SIP/RTP 验证）

**本地 PDF 规范文件**（`~/knowledge/telecom/3gpp/`）：
- `ITU-T_X.690-202102_BER.pdf` (822K, v2021) — BER/CER/DER 现行有效
- `ITU-T_X.690-0207_BER.pdf` (513K, v2007) — BER 旧版参考
- `ITU-T_X.691-0207_PER.pdf` (638K, v2007) — PER 规范

## 验证方法

### pyasn1 作为 BER 解码 ground truth

pyasn1 是 BER 结构化解码的权威验证工具，已预装在 Hermes venv 中（v0.6.3+）。

```python
from pyasn1.codec.ber import decoder
from pyasn1.type import univ

data = bytes.fromhex("30 2D 80 08 64 10 ...")
decoded, remainder = decoder.decode(data, asn1Spec=univ.Any())
```

**验证要点：**
- pyasn1 递归解码全部嵌套，无 `length==0` 提前退出问题
- 对比脚本的输出节点数和偏移量，不一致则脚本有 bug
- pyasn1 输出每个 TAG 的 class/P/C/tag-number，可逐层验证

> **2026-06-22 实测：** pyasn1 解析 MAP insertSubscriberData 得到 11 个节点。脚本原输出 9 个（`length==0: break` 遗漏了 Ext-BearerService 和 ExtensionContainer）。修复后 11/11 完全对齐。

### 数学验证脚本

```bash
python3 scripts/ber-tag-verify.py          # 标准验证
python3 scripts/ber-tag-verify.py --verbose # 详细输出
```

### 手工验证清单

- [ ] 码流前 10 字节是否为 C 结构体头部（apReq_T）
- [ ] OpCode 是否正确映射到 MAP 操作
- [ ] IMSI TBCD 解码：64→46, 10→01, ...
- [ ] BER TAG 编码：短格式取 `& 0x1F`，不是 `& 0x7F`
- [ ] 2/4/6 位三种 TAG 假设结果是否合理
- [ ] `length==0` 的节点（如 `93 00`）后仍有后续 TLV
- [ ] 结构遍历节点数与 pyasn1 一致
