# pycrate 5G NGAP/NAS 解码实战记录

## SCTP DATA Chunk 解析（IEs=0 的根因之一）

### 问题描述

NGAP 消息在 SCTP 上传输时，发动机错误地将所有 SCTP chunk（包含 SACK、HEARTBEAT 等控制 chunk）当作 DATA chunk 喂给 pycrate。pycrate 从垃圾数据中"解码"出 PDU 头和过程码，返回空的 IEs（IEs=0）。

### DATA Chunk 结构（RFC 4960 §3.3.1）

每个 SCTP chunk 从 **偏移 12**（SCTP 公共头之后）开始。DATA chunk 头部 = 16 字节：

```
Offset from chunk start:
  +0: Chunk Type (1B)          — DATA=0x00
  +1: Chunk Flags (1B)         — U B E bits
  +2: Chunk Length (2B)        — 含 chunk 头部自身的总长度
  +4: TSN (4B)                 — Transmission Sequence Number
  +8: Stream Identifier (2B)
  +10: Stream Sequence Number (2B)
  +12: Payload Protocol Identifier (4B)  ← PPID
  +16: Payload data           ← NGAP PER 数据从这里开始
```

### 正确解析代码

```python
off = 12  # SCTP common header size
while off + 8 <= len(sctp_bytes):
    chunk_type = sctp_bytes[off]
    chunk_len = int.from_bytes(sctp_bytes[off + 2:off + 4], 'big')
    if chunk_len < 4:
        break
    if chunk_type == 0x00 and off + 16 <= len(sctp_bytes):
        # PPID at off+12, payload at off+16
        ppid = int.from_bytes(sctp_bytes[off + 12:off + 16], 'big')
        payload = sctp_bytes[off + 16:off + chunk_len]
    # SACK(3), HEARTBEAT(4), etc. — skip silently
    off += chunk_len
```

### 常见错误

| 错误 | 表现 | 后果 |
|------|------|------|
| `off + 20` 取 PPID | 读到了 SI/SSN 之后的位置 | PPID=60(NGAP) 永远不匹配 |
| `off + 28` 取 payload | 超出 DATA chunk 头部 | 切片到下一个 chunk 或垃圾 |
| 不检查 chunk_type | SACK/HEARTBEAT 被当作 NGAP | pycrate 空 IEs 解码 |

## pycrate ASN.1 空 IEs 回退策略

### 问题

pycrate `from_aper()` 可能成功解码 PDU 头部（PDU type + procedure code），但 IEs 列表为空。原因：
1. SCTP 垃圾数据（见上节）
2. ASN.1 PER 嵌套太深，`_val` 结构中的 protocolIEs 位于子字典中
3. 未知的 procedure code 变体

### 修复方案：两层回退

```python
if not ies_raw:
    # 第一层：深度搜索 ASN.1 值树
    ies_raw = _deep_search_ies(value[1])
    
    # 第二层：启发式字节级回退
    if not ies_raw:
        ies = _heuristic_fallback_ies(data, proc_code)
```

**深度搜索** — 递归遍历 ASN.1 值字典，寻找 `protocolIEs` 键：

```python
def _deep_search_ies(self, d: dict) -> list:
    pis = d.get("protocolIEs", [])
    if pis:
        return pis
    for v in d.values():
        if isinstance(v, dict):
            result = self._deep_search_ies(v)
            if result:
                return result
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    result = self._deep_search_ies(item)
                    if result:
                        return result
    return []
```

**启发式回退** — 从 `data[4:]` 开始按 NGAP 线性 IE 格式解析（IE_ID(1) + Criticality(1) + Length(2) + Value）：
- 提取 AMF-UE-NGAP-ID 和 RAN-UE-NGAP-ID 用于会话关联
- 提取 NAS-PDU 原始 hex 用于下游 NAS 解码
- 设置 10000 字节的 IE 长度上限防止异常数据

## 非标准 NAS 封装类型（encap=0x04）

### 背景

测试设备 PCAP 数据集使用两种安全封装标识：
- `byte[1] = 0x02` — 安全封装（标准格式）
- `byte[1] = 0x04` — 另一种安全封装（非标准，但结构相同）

两种格式都在 byte[7] 开始存放内层 NAS 消息。

### 内层 NAS 提取

```python
# inner_data = data[7:] 适用于 encap=0x02 和 encap=0x04
if len(data) >= 8 and data[1] in (0x02, 0x04) and data[7] == 0x7E:
    inner_data = data[7:]
```

注意：`data[1]=0x04` 时 SHT（byte[0] 低 4 位）可能为 14（0x0E），不是标准 SHT 值（0-3）。

## 非标准 Security Mode Command IE 编码

### 问题

此 PCAP 数据集中的 Security Mode Command 不使用标准 3GPP IEIs（0x10=ngKSI, 0x36=Selected NAS security algorithms），而是用一个聚合的 IEI 0x77 以 **LVE 格式** 编码所有安全参数。

### 编码格式

```
77 00 09 [sec_byte] 00 00 00 00 00 00 [tail_byte]
```

- `77` — IEI（非标准，本数据集私有）
- `00 09` — 2 字节长度（LVE 格式！不是 TLV 的 1 字节长度）
- `[sec_byte]` — 算法字节
  - 高 4 位 = 加密算法 ID
  - 低 4 位 = 完整性算法 ID  
- `00 00 00 00 00 00` — 填充/保留
- `[tail_byte]` — 未知（可能是后一个 IE 的起始）

### LVE vs TLV 陷阱

| 格式 | 长度字段 | IEI 0x77 的正确解析 |
|------|---------|-------------------|
| TLV | 1 字节长度（`data[off+1]`） | 错误！`length=data[4]=0x00` → 跳过 |
| LVE | 2 字节长度（`data[off+1:off+3]`） | 正确！`length=0x0009=9` → 读取 9 字节 value |

**教训：** 非标准 IEI 不能默认用 TLV 解析。在实现 `process_security_mode_command` 时，0x77 需要单独处理为 LVE。

### 算法值不可靠

此数据集提取的 `enc_alg=8, int_alg=5` 不在标准 TS 33.501 算法 ID 范围（0-3）内，说明编码方式与标准不同。标准 3GPP IEIs（0x10, 0x36）已预留，收到标准格式消息时能正确解码。

## 5GSM 增强 IE 解码（TS 24.501 §9.11.4）

### 解码的 IE

| IEI | 名称 | 格式 | 解码输出 |
|-----|------|------|---------|
| 0x22 | PDU Session Type | TV | IPv4/IPv6/IPv4v6/Ethernet/Unstructured |
| 0x25 | S-NSSAI | TLV | SST + SD + Mapped SST + Mapped SD |
| 0x27 | QoS Rules | TLV-E | QFI + Operation + Parameters |
| 0x28 | DNN (Data Network Name) | LVE | ASCII 字符串 |
| 0x29 | SSC Mode | LVE | SSC mode 1/2/3 |
| 0x2B | QoS Flow Descriptions | LVE | QFI + 5QI + GFBR/MFBR |
| 0x2C | Session-AMBR | LVE | DL/UL value + unit |
| 0x34 | Extended Protocol Config Options | TLV-E | Raw hex |
| 0x37 | 5GSM Cause | TLV | Cause code + human name |
| 0x59 | Always-on PDU Session | TV | Boolean |
| 0x5A | GPRS Timer | TV | Timer unit + value |
| 0x5B | PDU Session Reactivation Result | TV | Result code |
| 0x5C | Reactivation Result Error Cause | TV | Error code |

### Session-AMBR（TS 24.501 §9.11.4.2）格式

标准 10 字节格式：
```
Unit-DL(1B) + DL-AMBR(4B, big-endian) + Unit-UL(1B) + UL-AMBR(4B, big-endian)
```
- Unit 编码：0=bps, 1=Kbps, 2=Mbps, 3=Gbps, 4=Tbps

### QoS Flow Descriptions（TS 24.501 §9.11.4.8）格式

每个 QoS flow：
```
QFI(1B) — bits 0-5=QFI, bit 6=DQR
[Operation Code](1B) — bits 0-3=op, bit 4=E, bits 5-7=num_params
[Parameters]:
  Param_ID(4b) + Param_Length(4b) + Param_Value
  - 0: 5QI (1B)
  - 1: GFBR (5-7B: direction + unit + value)
  - 2: MFBR (5-7B: direction + unit + value)
```

## NAS 安全上下文跟踪

### 核心实体

```
NasSecurityManager (引擎级)
  └── NasSecurityContext (每 UE 会话)
       ├── ngKSI - NAS key set identifier
       ├── selected_enc_alg / selected_int_alg - 算法 ID
       ├── ul_count / dl_count - NAS COUNT (32-bit)
       ├── activated - SECURITY_MODE_COMPLETE 后设为 True
       ├── k_amf, k_nas_enc, k_nas_int - 密钥（需 KDF 推导）
       └── keys_available - 密钥是否已推导
```

### 工作流

```
SECURITY_MODE_COMMAND (0x5E)
  → process_security_mode_command(data, session_key)
  → 提取 ngKSI + 算法 → 设置 ctx.set_security_algorithms()

SECURITY_MODE_COMPLETE (0x5F)
  → process_security_mode_complete(data, session_key)
  → ctx.activate() → COUNT 归零

后续加密消息 (SHT=2 或 encap=0x02/0x04)
  → is_message_encrypted(data) → True
  → try_decrypt_nas(data, session_key, direction)
  → NEA1/2/3 解密 → increment_count()
```

### KDF 推导（TS 33.501 §A.8）

```python
K_NASenc = HMAC-SHA-256(K_AMF, FC=0x69 || P0=0x01(N-NAS-enc-alg) || P1=alg_id)[-16:]
K_NASint = HMAC-SHA-256(K_AMF, FC=0x68 || P0=0x02(N-NAS-int-alg) || P1=alg_id)[-16:]
```

### 内层消息提取的封装检测

引擎 `_process_nas_security` 中，SECURITY_MODE_COMMAND 的内层数据提取与 NAS 5GMM 解码器一致，不能假设 `nas_result.fields["inner"]` 与原始数据有相同的字段路径：

```python
# 正确：inner 是 inner_result.fields，直接包含 message_type
inner = nas_result.fields.get("inner", {})
if inner:
    mt_hex = inner.get("message_type", "")
```

### 数据集安全参数编码总结

| 方面 | 本数据集 | 3GPP 标准 |
|------|---------|----------|
| NAS 消息类型偏移 | byte[2] | byte[1] |
| 封装类型值 | 0x00, 0x02, 0x04 | 0x00, 0x01, 0x02 |
| SMC IEI | 0x77 (LVE) | 0x10, 0x36, 0x1E |
| 算法编码 | 高4位=enc, 低4位=int | 标准 EA0-3 映射 |

## pycrate IE 值格式陷阱

### 问题描述

pycrate 解码 NGAP PDU 后，IE 值以 `(type_name, actual_value)` 元组形式返回。
使用 `_format_ie_value()` 格式化时，对 bytes 类型会添加前缀 + 截断：

```python
def _format_ie_value(self, ie_value) -> str:
    if isinstance(ie_value, tuple) and len(ie_value) == 2:
        type_name, actual = ie_value
        if isinstance(actual, bytes):
            if len(actual) <= 16:
                return f"{type_name}: {actual.hex()}"
            else:
                return f"{type_name}: {actual[:16].hex()}...({len(actual)}B)"
```

结果示例：`"NAS-PDU: 7e004179003a0122...68B"` — 下游 `bytes.fromhex()` 直接崩溃。

### 修复方案

对需要保留完整二进制值的 IE（NAS-PDU、SecurityKey 等），**在 decode() 循环中特殊处理**，
不经过 `_format_ie_value()`，直接提取原始 bytes：

```python
if ie_id == 38:  # NAS-PDU (OCTET STRING)
    _, raw_bytes = ie_value          # ie_value is (type_name, bytes)
    nas_pdu_hex = raw_bytes.hex()    # 完整 hex，无前缀、无截断
    ie_value_str = raw_bytes.hex()   # 同时用于 IE list 展示
```

### 哪些 IE 需特殊处理

| IE ID | IE 名称 | 原因 |
|-------|---------|------|
| 38 | NAS-PDU | 下游需 `bytes.fromhex()` 进一步解析 NAS |
| 94 | SecurityKey | 密钥完整二进制 |
| 119 | UESecurityCapabilities | 二进制位掩码 |
| 其他 OCTET STRING 类型 | — | 长度 > 16 字节时会被截断 |

### 注意

pycrate 的 bytes IE 值可能不带长度前缀或带长度前缀，取决于 ASN.1 定义：
- `OCTET STRING (SIZE(..))` — 直接返回裸 bytes
- `OCTET STRING` 作为 open type 时 — 可能需要外层长度字段

## 5G NAS 消息格式（测试设备 PCAP）

### 字节布局（与 TS 24.501 有差异）

测试设备产生的 5G NAS-PDU 格式：

```
Byte 0:  Extended Protocol Discriminator (4b) + Security Header Type (4b)
Byte 1:  Spare / 安全头部附加字段
Byte 2:  Message Type  ← 注意：不是标准规范的 byte[1]！
Byte 3+: Information Elements
```

这与 3GPP TS 24.501 标准（消息类型在 byte[1]）不一致。

### 示例（initial registration）

```
NAS hex: 7e004179003a0122f6402143020102af...
         ↑↑ ↑
         ││ └── REGISTRATION_REQUEST (0x41)
         │└──── Spare (0x00)
         └───── EPD=7(5GMM) SHT=14(非标准)
```

### 安全封装格式

当 Security Header Type 指示有安全头部时，格式为：

```
Byte 0:    EPD + SHT (0x7E)
Bytes 1-6: Message Authentication Code (MAC, 6 bytes)
Byte 7:    Sequence Number
Bytes 8+:  内层明文 NAS 消息
```

内层明文 NAS 消息结构相同（消息类型仍在 byte[2]）。

### 解码器实现建议

```python
def _get_msg_type_offset(data: bytes) -> int:
    """确定 NAS 消息类型偏移。标准为 1，但测试设备为 2。"""
    # 试探法：检查 byte[2] 是否是有效 5GMM 消息类型
    if len(data) > 2:
        test_msg = data[2]
        if test_msg in {0x41, 0x42, 0x43, 0x44, 0x45, 0x46,  # Registration
                        0x52, 0x53, 0x54, 0x55, 0x56,        # Authentication
                        0x5C, 0x5D,                           # Identity
                        0x5E, 0x5F, 0x60,                    # Security Mode
                        0x4C, 0x4D, 0x4E,                    # Service
                        }:
            return 2
    return 1  # 标准 byte[1]
```

