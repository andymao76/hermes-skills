# 合法监听数据层 TLV 编码（华为/Sinovatio）

> 来源：HW SBC LI 上报 pcap + ORI 文件 + X2 IRI 日志分析
> 关联：[[pcap-volte-sip-i-li-data-layer-analysis]]

---

## 华为 LI 数据层协议头

```
aa05         — 2字节 协议魔数
LL LL        — 2字节 消息总长度（小端）
SS SS SS SS  — 4字节 会话/序列号
01 FF FF FF FF FF — 头部类型标记
```

紧接着 LI TLV 负载（BER 风格编码）。

## LI TLV TAG 速查表

| TAG | Class | Tag# | 典型字段 | 编码说明 |
|:---:|:-----:|:----:|----------|---------|
| `80` | [0] | 0 | CIN / 上下文数据 | Primitive, 多字节 |
| `81` | [1] | 1 | LIID | ASCII 字符串或 反序BCD |
| `97` | [23] | 23 | OPERID / 操作码 | Primitive, 1字节 |
| `A2` | [2] | 2 | Called Party 信息 | Constructed |
| `A3` | [3] | 3 | Timestamp | Constructed |
| `A4` | [4] | 4 | 附加上下文 | Constructed |
| `A9` | [9] | 9 | SIP 消息体 | Constructed |
| `BF` | [31] | 31 | 扩展/私有字段 | Constructed |

## LIID 编码规则

### SIP-I Calling Party Subaddress 中的 LIID

LIID 编码在 ISUP Calling Party Subaddress 字段中，使用 **反序BCD**（swapped nibbles within each byte）：

| LIID | 正常 BCD | 反序 BCD |
|:----:|:--------:|:---------:|
| 84335 | `84 33 5F` | `48 33 F5` |
| 10013 | `10 01 3F` | `01 10 F3` |

解码：
```python
liid = 84335
digits = [int(d) for d in str(liid)]
bcd = []
i = 0
while i < len(digits):
    if i + 1 < len(digits):
        bcd.append((digits[i] << 4) | digits[i+1])
        i += 2
    else:
        bcd.append((digits[i] << 4) | 0x0F)
        i += 1
reversed_bcd = [((b & 0x0F) << 4) | ((b >> 4) & 0x0F) for b in bcd]
```

### ORI 文件中的 LIID

华为 ORI 上报文件中，LIID 通常为 **ASCII 编码**（如 `38 34 33 33 35` = "84335"）。

## OPERID 编码

- ORI 文件中：**ASCII 编码**（如 `36 33 36 30 31` = "63601"）
- SBC 数据层中：TAG `97` 的 Value 可能为单字节编码

## X2 IRI 关键字段

| 字段 | 编码 | 说明 |
|:----|:----|:------|
| domainID | `{0 4 0 2 2 1 6}` | ETSI LI 域标识 |
| lawfulInterceptionIdentifier | `31'H` → "1" | LIID |
| operator-Identifier | `313233'H` → "123" | OPERID |
| network-Element-Identifier | `8413f5'H` | CIN（反序BCD） |
| generalizedTime | hex → "20140722..." | ISO 时间戳 |
| sip-uri | hex → ASCII | SIP URI |
| imsChargingID | hex → ASCII | IMS 计费ID |
| sipMessage | hex → ASCII | 完整 SIP 消息体 |

## X2 IRI 消息结构（HW ATS9900）

```
码流头 (20 bytes):
  1C EB 62 00       — 固定标识（Hi3/X2 上报）
  03 00 00 00       — 长度(3)
  PP PP PP PP       — 内存指针1
  PP PP PP PP       — 内存指针2
  PP PP PP PP       — 内存指针3

CC填充区:
  CC CC ... CC      — 0xCC 对齐填充

ASN.1 PER 编码体:
  F0 72 73 00       — PER 编码开始
  ...               — ASN.1 PER 编码的 IRI-Parameters
```

不同消息的指针值不同（标识不同消息实例），但结构相同。

## 唯一会话标识

LIID + CallID = 唯一会话标识。
