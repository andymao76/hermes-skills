# Dubuisson ASN.1 教材 — Tagging / BER / PER 核心参考

> 来源: Olivier Dubuisson "ASN.1 – Communication between Heterogeneous Systems" (2000)
> 适用于 ZTLIG ZTE CS HI2 ASN.1/BER 编解码场景

---

## Tag 编码模式速查

| 模式 | 语法 | BER 行为 | 备注 |
|------|------|----------|------|
| EXPLICIT | `[0] EXPLICIT T` 或无关键字 | 内层 UNIVERSAL tag **一并编码**；Constructed 形式嵌套 | TLV 嵌套，自描述 |
| IMPLICIT | `[0] IMPLICIT T` | **仅编码最外层 tag**，覆盖内层所有 tag（含 UNIVERSAL） | TLV 一层，解码方需知 abstract syntax |
| AUTOMATIC TAGS | 模块头声明 | 编译器自动分配 context-specific tags (0,1,2...) | **新规范推荐**；默认 IMPLICIT |

**IMPLICIT 限制**：CHOICE type、open type（ObjectClassFieldType）、type parameter **必须用 EXPLICIT**。

---

## BER — TLV 编码结构

### T 字段 (Tag Octets)

**单字节格式 (tag ≤ 30)**：
```
bit 8-7: class (00=UNIVERSAL, 01=APPLICATION, 10=context-specific, 11=PRIVATE)
bit 6:   P/C (0=primitive, 1=constructed)
bit 5-1: tag number
```

**多字节格式 (tag ≥ 31)**：
- 首字节 bits 5-1 = 11111
- 后续字节 bit 7 = 1 表示"未完"，bit 7 = 0 表示最后字节
- 拼接 bits 6-0 得到 tag number

### L 字段 (Length Octets)

| 格式 | 条件 | 编码 |
|------|------|------|
| Short definite | length ≤ 127 | `0` + 7-bit 长度值 (1 字节) |
| Long definite | 128 ≤ length | 首字节 `1` + 后续长度字节数；后续大端长度值 |
| Indefinite | 仅 constructed | `0x80`，尾部 `00 00` (EOC) 标记结束 |

### 各类型 BER 编码要点

| 类型 | T (UNIVERSAL) | 形式 | 要点 |
|------|--------------|------|------|
| BOOLEAN | 1 | Primitive | FALSE=0x00, TRUE=任1非0字节 |
| NULL | 5 | Primitive | 无 V 字节 |
| INTEGER | 2 | Primitive | 正数二进制，负数 2's complement；首字节 0x00 防符号混淆 |
| BIT STRING | 3 | Primitive/Constructed | 首字节记录末尾未用 bit 数(0-7) |
| OCTET STRING | 4 | Primitive/Constructed | 无首字节，长度必须 8 的倍数 |
| OBJECT IDENTIFIER | 6 | Primitive | 首两弧合并为 arc1×40+arc2；后续连续编码(bit7=续段) |
| SEQUENCE/SEQUENCE OF | 16 | Constructed | 按定义顺序编码 |
| SET/SET OF | 17 | Constructed | 编码顺序由发送方自定 |
| CHOICE | — | — | 取决于所选 alternative 的编码 |

---

## PER — Packed Encoding Rules

### 核心差异
- 格式：`[P][L][V]`（Preamble + Length + Value），基于 **bit**
- **Tags 永不传输**
- 比 BER 省 40-60%
- 解码器必须引用 ASN.1 规范

### 四种变体
```
Basic Aligned      → octet 对齐，非规范
Canonical Aligned  → octet 对齐，编码唯一
Basic Unaligned    → 最紧凑，无对齐
Canonical Unaligned → 最紧凑 + 编码唯一
```

### PER 关键编码规则

| 类型 | 编码要点 |
|------|----------|
| BOOLEAN | **1 bit** (1=TRUE, 0=FALSE) |
| NULL | **0 bits**（由 preamble bitmap 指示） |
| INTEGER | 有效约束 `[bmin,bmax]` 时，值编码为 n-bmin 用 ⌈log₂d⌉ bits |
| ENUMERATED | 重新索引为 0..n-1，用 constrained whole number |
| SEQUENCE | 可扩展: 1-bit preamble；可选组件: bitmap |
| SET | **先按 canonical tag order 排序**，再按 SEQUENCE 规则编码 |
| CHOICE | 可扩展: 1-bit preamble + index (constrained whole number) |

### PER-visible 约束（压缩关键）

| 约束 | 应用于 | 效果 |
|------|--------|------|
| Single value / Value range | INTEGER | 计算 effective interval，编码差值 |
| SIZE | BIT/OCTET STRING, strings, lists | 固定长度时不传 L |
| FROM (Alphabet) | known-multiplier string | 每字符 ⌈log₂n⌉ bits |
| Type inclusion | INTEGER, strings | 传递引用中的约束 |

### 编码量估算公式
```
BOOLEAN:                                1 bit
INTEGER [bmin, bmax]:                  ⌈log₂(bmax-bmin+1)⌉ bits
ENUMERATED (n roots):                   ⌈log₂n⌉ bits
BIT STRING SIZE(n):                     n bits
Known-multiplier string SIZE(n), FROM(m chars):  n × ⌈log₂m⌉ bits
```

---

## HI2 实际应用背景

ZTE CS LI HI2 接口使用 ASN.1/BER 编码，通过 FTP 或 ROSE 传输。HI2 记录类型：
- Begin[1]A1 / End[2]A2 / Continue[3]A3 / Report[4]A4 / Alarm[16]B0
- 关键字段：LIID[1] / CID[2] / Timestamp[3] / PartyInfo[9] / Location[8]

BER 解码时注意：
1. **Tag 编码模式**：ZTE HI2 可能使用 IMPLICIT 或 EXPLICIT，影响 TLV 嵌套层数
2. **Indefinite length**：某些字段可能使用 0x80 + EOC 格式
3. **UNIVERSAL tag 16**：SEQUENCE 和 SEQUENCE OF 共享同一 tag，需区分上下文
