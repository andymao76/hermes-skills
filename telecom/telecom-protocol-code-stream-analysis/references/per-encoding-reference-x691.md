# PER 编码参考 (ITU-T X.691 / ISO/IEC 8825-2)

> 来源: ITU-T X.691 (02/2021) / ISO/IEC 8825-2 — Packed Encoding Rules
> 本地 PDF: `~/knowledge/telecom/3gpp/ITU-T_X.691-0207_PER.pdf` (638K)
> 关联: [[ber-x690-encoding-rules-and-verification]]

---

## 一、PER 与 BER 核心差异

| 特征 | BER/DER | PER (Aligned) |
|------|---------|---------------|
| Tag 编码 | 显式 TLV，Tag 占用独立字节 | **无显式 Tag**，接收方需知 ASN.1 结构 |
| 长度编码 | 短/长/不定长格式 | 根据 ASN.1 约束自动确定 |
| 对齐 | 字节对齐 | 可对齐(A-PER) 或 非对齐(U-PER) |
| 效率 | 低（TLV 开销大） | 高（紧凑位级） |
| 典型应用 | MAP/CAP/SNMP/LDAP | RANAP/NGAP/NAS/RRC |

## 二、PER 基本编码规则

### SEQUENCE 开头

```
ext(1bit) + optional_bitmap + fields
```

- ext=0 表示不扩展，后面跟 OPTIONAL 字段的 bitmap
- ext=1 表示有扩展，跳过 OPTIONAL bitmap，直接进入扩展字段

### CHOICE 开头

```
ext(1bit) + choice_index(#bit) + value
```

- ext=0: choice_index 按 `ceil(log2(N))` 位编码（N 为 choice 选项数）
- ext=1: choice_index 按 `ceil(log2(N+1))` 位编码

### 长度编码

| 约束 | 长度编码方式 |
|------|-------------|
| 固定尺寸（如 INTEGER(0..255)） | 直接按 `ceil(log2(range))` 位编码，无长度前缀 |
| 可变尺寸（如 OCTET STRING SIZE(1..16)） | 如果有上界，按 `ceil(log2(max-min+1))` 位编码长度前缀 |
| 无上界 | 用 8 位（PER Aligned 的 normal）或 16 位编码长度 |

### 基本类型编码

| 类型 | PER 编码 |
|------|----------|
| INTEGER (有约束) | `ceil(log2(max-min+1))` 位，无符号二进制 |
| INTEGER (无约束) | 8/16 位长度前缀 + 2's complement |
| ENUMERATED | `ceil(log2(N))` 位，0-based 索引 |
| BOOLEAN | 1 位（0=FALSE, 1=TRUE） |
| NULL | 0 位 |
| OCTET STRING (固定) | 直接编码，字节数固定 |
| OCTET STRING (可变) | 长度前缀 + 内容 |
| BIT STRING (固定) | 直接编码，位数固定 |
| BIT STRING (可变) | 长度前缀 + 位串 |

### Open Type (任何类型)

```
length_prefix + value
```

- PER Aligned: 16 位长度前缀
- PER Unaligned: 8 位或 16 位（按范围选择）

## 三、Aligned PER vs Unaligned PER

| 特性 | Aligned PER (A-PER) | Unaligned PER (U-PER) |
|:----:|:-------------------:|:---------------------:|
| 字节对齐 | 必要时填充到字节边界 | 无填充，位级紧凑 |
| 效率 | 较高 | 最高 |
| 使用场景 | 3GPP RANAP/NGAP | 某些 IoT 协议 |

A-PER 的对齐规则：
- SEQUENCE 开头后，**所有固定类型字段**对齐到字节边界
- CHOICE 的 index 后对齐到字节边界
- Open Type 的 length 对齐到字节边界

## 四、PER 码流分析步骤

1. **获取 ASN.1 定义** — 从 3GPP TS 中找到 `.asn1` 文件（TS 24.501/38.331 等）
2. **确定 PER 对齐模式** — 通常 3GPP 使用 Aligned PER
3. **从 CHOICE 开始解码** — ext bit + choice index
4. **进入 SEQUENCE** — ext bit + optional bitmap + 字段逐个解码
5. **处理 Open Type** — 外层的 16 位长度 + 内层 PER 内容

## 五、参考

- ITU-T X.691 PDF: `~/knowledge/telecom/3gpp/ITU-T_X.691-0207_PER.pdf`
- 3GPP TS 24.501 (5G NAS) — PER Aligned 编码
- 3GPP TS 38.331 (NR RRC) — PER Aligned 编码
