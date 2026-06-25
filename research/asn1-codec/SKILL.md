---
name: asn1-codec
description: "ASN.1 编解码专家。涵盖 BER (Basic Encoding Rules)、PER (Packed Encoding Rules)、DER (Distinguished Encoding Rules)、CER (Canonical Encoding Rules) 等编码规则。支持 ASN.1 语法定义、TLV 结构分析、3GPP/ETSI/电信标准中 ASN.1 类型定义解读(HI2 PDU/HI3 PDU/3GPP TS 33.128)、X.509/PKCS 证书 ASN.1 结构。提供 pyasn1 编解码工具。当用户提及 ASN.1、BER、PER、DER、TLV、OID、Abstract Syntax Notation、HI2 PDU、pyasn1、dumpasn1 时触发。"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [asn1, ber, per, der, encoding, telecom, security, cryptography]
    related_skills: [etsi-lawful-intercept, 3gpp-expert, wireshark-analysis]
---

# ASN.1 编解码专家

ASN.1（Abstract Syntax Notation One）是电信和网络安全领域的正式描述语言，定义跨平台/跨语言的数据结构。广泛用于 3GPP、ETSI、PKI/X.509、LDAP、SNMP、Kerberos 等标准。

---

## 🔴 首要原则：交叉验证铁律

**任何编程、确定性知识或技能类任务必须做交叉验证，不能仅靠当前 LLM 的输出来判定正确性。**

本条铁律适用于本 skill 调用涉及的所有任务：
- BER/DER/PER TAG 值和偏移量计算 → 用 pyasn1 / asn1tools / Wireshark 验证
- 协议码流解析 → 标准库解码输出为准，LLM 分析仅作初稿假设
- ASN.1 语法校验 → 用 ASN.1 编译器或在线 playground 验证
- CRC/校验和计算 → 用确定算法实现验证

**工作流：**
1. **先猜** — LLM 分析结构作为初步方向
2. **再验** — 标准库工具（pyasn1/asn1tools/Wireshark/dumpasn1）解码验证
3. **三对比** — 多种工具/假设交叉对比（如三种 TAG 假设分析法）
4. **定结论** — 以工具输出为准，LLM 输出仅供参考

实验证明：DeepSeek-V3 在 IMSI 解码上完全错误，Qwen3.5-397B 也会遗漏节点。标准库（pyasn1）11/11 完全一致。

详细参考：`skill_view("asn1-codec", "references/llm-cross-validation-iron-law.md")`

---

## 一、编码规则

### BER (Basic Encoding Rules) — 基础编码规则

BER 使用 **TLV（Type-Length-Value）** 三元组结构：

```
+--------+--------+-----------+
|  Type  | Length |   Value   |
| (Tag)  |  (Len) |           |
+--------+--------+-----------+
```

**Tag（标识符）字节结构：**

```
Bit  8  7  6  5  4  3  2  1
    ├──┴──┤ ├──────┴──────┤
   Class   P/C    Tag Number
```

| 字段 | 描述 |
|------|------|
| **Class** (bit 8-7) | Universal(00) / Application(01) / Context-Specific(10) / Private(11) |
| **P/C** (bit 6) | Primitive(0) / Constructed(1) |
| **Tag Number** (bit 5-1) | 0-30（直接编码），≥31（使用后续字节） |

**Universal Tag 对照表：**

BER 首字节 = `TagNumber + Class(bit8-7) + P/C(bit6)`。Primitive 类型 P/C=0，Constructed 类型 P/C=1。
SEQUENCE/SET 总是 Constructed，因此在 BER 中首字节与 Tag 编号不同。

| Tag 编号 | BER 首字节 | 类型 | 编码形式 |
|----------|-----------|------|----------|
| 0x01 | 0x01 | BOOLEAN | Primitive |
| 0x02 | 0x02 | INTEGER | Primitive |
| 0x03 | 0x03 | BIT STRING | Primitive (或 Constructed) |
| 0x04 | 0x04 | OCTET STRING | Primitive (或 Constructed) |
| 0x05 | 0x05 | NULL | Primitive |
| 0x06 | 0x06 | OBJECT IDENTIFIER | Primitive |
| 0x0A | 0x0A | ENUMERATED | Primitive |
| 0x0C | 0x0C | UTF8String | Primitive (或 Constructed) |
| 0x10 | **0x30** | **SEQUENCE** | **必为 Constructed** |
| 0x11 | **0x31** | **SET** | **必为 Constructed** |
| 0x12 | 0x12 | PrintableString | Primitive (或 Constructed) |
| 0x13 | 0x13 | T61String | Primitive (或 Constructed) |
| 0x16 | 0x16 | IA5String | Primitive (或 Constructed) |
| 0x17 | 0x17 | UTCTime | Primitive |
| 0x18 | 0x18 | GeneralizedTime | Primitive |

> **为什么 SEQUENCE 的 BER 首字节是 0x30 而不是 0x10？**
> SEQUENCE 的 Universal Tag 编号是 16 = 0x10。BER 编码时，首字节 = Class(00) + P/C(1) + Tag(10000) = `0011 0000` = 0x30。同理 SET 编号 17 = 0x11，首字节 = `0011 0001` = 0x31。表中 0x10/0x11 是 Tag 编号，0x30/0x31 是实际 BER 首字节，初学者容易混淆，特此说明。

### DER (Distinguished Encoding Rules) — BER 的子集

- 确定性编码：每种值只有一种合法 BER 编码
- 用于 PKI/X.509 证书、CMS、数字签名
- 核心要求：**Definite Length（确定长度）**、最短编码

### PER (Packed Encoding Rules) — 压缩编码规则

- **ALIGNED** 与 **UNALIGNED** 变体
- 移除 BER 的 TLV 开销，按字段定义逐比特编码
- 广泛用于 **3GPP**（RRC/NAS）和 **ETSI LI**（HI2/HI3 PDU）
- 编码依赖 ASN.1 模块中的约束条件（SIZE、EXTENSIBILITY 等）
- 比 BER 节省 70-90% 空间

### CER (Canonical Encoding Rules) — DER 的流式变体

- 用于大数据量的确定性编码
- 使用 Constructed 编码处理长数据（DER 可能用 Primitive 长格式）

### XER — XML Encoding Rules

- ASN.1 值的 XML 表示
- 可读性高，但编码尺寸大

---

## 二、ASN.1 语法快速参考

### 基本类型定义

```asn1
-- 基本类型
MyInteger    ::= INTEGER (0..255)
MyBool       ::= BOOLEAN
MyString     ::= OCTET STRING (SIZE(1..64))
MyOID        ::= OBJECT IDENTIFIER

-- 构造类型
MySequence   ::= SEQUENCE {
    field1    INTEGER,
    field2    PrintableString,
    field3    BOOLEAN OPTIONAL,          -- 可选字段
    field4    INTEGER DEFAULT 0,         -- 默认值
    ...                                  -- 扩展标记
}

MyChoice     ::= CHOICE {
    a         INTEGER,
    b         BOOLEAN,
    c         OCTET STRING
}

MySet        ::= SET {
    name      PrintableString,
    age       INTEGER
}

-- 枚举
StatusCode   ::= ENUMERATED {
    success  (0),
    error    (1),
    timeout  (2),
    ...      -- 可扩展枚举
}
```

### 约束示例

```asn1
LimitedInt       ::= INTEGER (0..255)         -- 值范围
FixedString      ::= OCTET STRING (SIZE(16))  -- 固定长度
VariableString   ::= OCTET STRING (SIZE(1..256, ...))  -- 可变长度+扩展
SizeLimit        ::= SEQUENCE (SIZE(1..100)) OF INTEGER
PatternStr       ::= PrintableString (FROM ("A".."Z"))
```

---

## 三、3GPP / ETSI 中的 ASN.1

### 3GPP RRC/NAS

- **NR RRC (TS 38.331)**：ASN.1 PER Aligned 编码
- **LTE RRC (TS 36.331)**：ASN.1 PER Aligned 编码
- **NAS (TS 24.301 / 24.501)**：部分使用 ASN.1
- 信令消息以 PER Aligned 编码传输，比 BER 紧凑 10 倍

### ETSI LI HI2/HI3 PDU

- **TS 102 232-1** 定义 HI2 PDU（信令）和 HI3 PDU（内容）
- 使用 **ASN.1 PER Unaligned** 编码
- HI2 PDU 包含：LawfulInterceptionIdentifier、TimeStamp、ServiceData 等
- HI3 PDU 包含：InterceptedContent、ContentType、SequenceNumber 等
- 详细 ASN.1 类型定义见 `skill_view("asn1-codec", "references/etsi-li-asn1.md")`

### 常见 OID

```
1.2.840.113549.1.1.1    rsaEncryption (PKCS#1)
1.2.840.113549.1.1.5    sha1WithRSAEncryption
1.2.840.113549.1.1.11   sha256WithRSAEncryption
2.5.29.14               subjectKeyIdentifier
2.5.29.15               keyUsage
2.5.29.17               subjectAltName
2.5.29.19               basicConstraints
2.16.840.1.101.3.4.2.1  sha-256 (NIST)
```

---

## 四、ASN.1 编解码工具使用

### pyasn1 — BER/DER 编解码（系统已预装）

系统已安装 `pyasn1` (v0.6.3) 和 `pyasn1-modules` (v0.4.2)。

```bash
# 快速参考
skill_view("asn1-codec", "scripts/use-asn1-codec.sh")

# BER 解码十六进制
~/.hermes/venv/bin/python ~/.hermes/scripts/asn1-codec.py decode-hex 02012a

# BER 解码 Base64
~/.hermes/venv/bin/python ~/.hermes/scripts/asn1-codec.py decode-b64 <b64_string>

# BER 编码整数
~/.hermes/venv/bin/python ~/.hermes/scripts/asn1-codec.py encode-int 42

# BER 编码布尔
~/.hermes/venv/bin/python ~/.hermes/scripts/asn1-codec.py encode-bool True

# 查看工具信息
~/.hermes/venv/bin/python ~/.hermes/scripts/asn1-codec.py info
```

**重要限制：pyasn1 不支持 PER 解码。** PER（Packed Encoding Rules）不能直接用 BER 解码器解码，因为 PER 不保留 TLV 结构，必须按 ASN.1 模块定义逐比特解码。PER 解码需要使用 `asn1tools`（见下节）。

### asn1tools — PER 编解码（按需安装）

`asn1tools` 是 Python 生态中支持 PER（Aligned 和 Unaligned）解码的库。安装：

```bash
# 必须在 Hermes venv 中安装（系统 pip 被 PEP 668 保护）
~/.hermes/venv/bin/pip3 install asn1tools
```

**PER 解码示例（ETSI HI2 PDU）：**

```python
import asn1tools

# 编译 ASN.1 模块，指定 'uper' (Unaligned PER)
asn1_spec = """
HI2-PDU DEFINITIONS AUTOMATIC TAGS ::= BEGIN
LawfulInterceptionIdentifier ::= OCTET STRING (SIZE(1..128))
Timestamp ::= SEQUENCE {
    year    INTEGER (0..9999),
    month   INTEGER (1..12),
    day     INTEGER (1..31),
    hour    INTEGER (0..23),
    minute  INTEGER (0..59),
    second  INTEGER (0..59)
}
HI2-PDU ::= SEQUENCE {
    lawfulInterceptionIdentifier  LawfulInterceptionIdentifier,
    timestamp                      Timestamp
}
END
"""
compiled = asn1tools.compile_string(asn1_spec, "uper")

# 编码
encoded = compiled.encode("HI2-PDU", {
    "lawfulInterceptionIdentifier": b"\x01\x02\x03\x04",
    "timestamp": {"year": 2026, "month": 6, "day": 9,
                  "hour": 14, "minute": 30, "second": 0}
})

# 解码
decoded = compiled.decode("HI2-PDU", encoded)
```

**编码规则参数对照：**

| 参数 | 编码规则 | 适用场景 |
|------|----------|----------|
| `"uper"` | PER Unaligned | ETSI LI HI2/HI3 PDU (TS 102 232) |
| `"per"` | PER Aligned | 3GPP RRC (TS 38.331, TS 36.331) |
| `"ber"` | BER | 通用 TLV 编码 |
| `"der"` | DER | X.509 证书，PKCS 标准 |

**已知 pitfall：** asn1tools 的解析器不支持 ASN.1 的 `...` 扩展标记。如果 ASN.1 定义中包含 `...`，需要在编译前移除或简化。移除扩展标记不影响对标准字段的解码验证。

### 编解码示例（pyasn1 — BER）

```python
from pyasn1.codec.ber import encoder, decoder
from pyasn1.type import univ, tag, namedtype

# 编码 INTEGER
i = univ.Integer(42)
encoded = encoder.encode(i)    # → 02012a (BER)

# 解码
decoded, rest = decoder.decode(encoded)
print(decoded)                  # → 42

# 定义 SEQUENCE
class MyPDU(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('id', univ.Integer()),
        namedtype.NamedType('name', univ.PrintableString()),
    )

pdu = MyPDU()
pdu['id'] = 1
pdu['name'] = 'test'
data = encoder.encode(pdu)     # BER 编码
```

---

## 七、在线调试工具与学习资源

当需要深入分析 ASN.1 结构时，推荐以下在线资源：

- **ASN.1 Playground** — https://asn1.io/asn1playground/
- **OSS ASN.1 Tools** — https://www.oss.com/asn1/resources/asn1-playground.html
- **dumpasn1** CLI（未安装）— `apt install dumpasn1`
- **Wireshark** 内建 ASN.1 / PER 解码器

## 八、移动通信 PER 编码参考

PER (Packed Encoding Rules) 是 3GPP 和 ETSI LI 中的核心编码规则，详细参考见：
`~/knowledge/telecom/lawful_interception/per-encoding-mobile-signaling-reference.md`

### PER Aligned vs Unaligned

| 类型 | 填充规则 | 用于 |
|------|----------|------|
| **PER Aligned** | 字段间填充到字节边界 | **3GPP RRC/NAS** (TS 38.331/36.331) |
| **PER Unaligned** | 字段间不填充，比特紧凑 | **ETSI LI HI2/HI3 PDU** (TS 102 232-1) |

### 整数编码公式

```
INTEGER(a..b) → ceil(log2(b-a+1)) 比特
INTEGER(0..1)    → 1 bit
INTEGER(0..255)  → 8 bits
INTEGER(0..65535) → 16 bits
INTEGER 无约束    → 8/16 bits 长度前缀 + 值
```
  - 知识库参考：`~/knowledge/telecom/3gpp/ber-encoding-reference-library.md`
  - 官方规范 PDF：`~/knowledge/telecom/3gpp/ITU-T_X.690-0207_BER.pdf` (513K)
  - PER 规范 PDF：`~/knowledge/telecom/3gpp/ITU-T_X.691-0207_PER.pdf` (638K)
- **Wireshark** 内建 ASN.1 / PER 解码器

**移动通信信令 PER 解码参考（3GPP + ETSI LI）：** `skill_view("asn1-codec", "references/per-mobile-signaling-reference.md")`
- **PER Quick Reference** — https://www.oss.com/asn1/resources/asn1-made-simple/asn1-quick-reference/packed-encoding-rules.html
- **3GPP Online Decoder** — https://www.3glteinfo.com/tools/3gpp-decoder/（在线解 RRC/NAS/NGAP）
- **3GPP ASN.1 OID** — https://www.3gpp.org/specifications-technologies/specifications-by-series/asn-1-object-identifiers

### 开源项目

- **OpenLI** — github.com/OpenLI-NZ/openli — 开源 ETSI 合规合法监听系统（C, GPL-3.0），含 PER 解码器。本地知识库: `li/OpenLI/openli-intro.md`，源码: `~/projects/openli/`
- **pycrate** — github.com/P1sec/pycrate — Python 3GPP 消息集解析（RRC/NAS/NGAP）
- **ASN1SCC** — github.com/esa/asn1scc — ESA 开源嵌入式 ASN.1 编译器

### 教材参考

- **Dubuisson ASN.1 教材** — `skill_view("asn1-codec", "references/dubuisson-asn1-book-reference.md")`
  - ASN.1 领域最权威的教材（590页，免费 PDF）
  - Ch18 BER / Ch20 PER / Ch12 Tagging 为重点章节
  - 知识库摘要：`~/knowledge/telecom/3gpp/dubuisson-asn1-book-summary.md`
- **Larmouth ASN.1 Complete** — `skill_view("asn1-codec", "references/larmouth-asn1-complete-reference.md")`
  - 教程 + 编译器使用指南 + 设计哲学，与 Dubuisson 互补
  - Section III 编码规则从 BER→PER 演进叙事，便于理解设计动机
  - 知识库摘要：`~/knowledge/telecom/3gpp/larmouth-asn1-complete-summary.md`

### 本地知识库参考

PER 编码规范与移动通信信令分析完整参考（含官方标准链接、GitHub 工具、编码规则速查表）：
`~/knowledge/telecom/lawful_interception/per-encoding-mobile-signaling-reference.md`

---

## 九、数据类型对照（BER TLV 示例）

| 类型 | 值 | BER 编码 | 说明 |
|------|----|----------|------|
| BOOLEAN | TRUE | `01 01 FF` | Tag=0x01, Len=1, Value=0xFF |
| BOOLEAN | FALSE | `01 01 00` | |
| INTEGER | 42 | `02 01 2A` | Tag=0x02, Len=1, Value=0x2A |
| INTEGER | 256 | `02 02 01 00` | 多字节，高位优先 |
| NULL | — | `05 00` | |
| OCTET STRING | "ABC" | `04 03 41 42 43` | |
| OID | 1.2.840.113549 | `06 06 2A 86 48 86 F7 0D` | 前两字节合并编码 |
| SEQUENCE | {} | `30 00` | Constructed |

---

## Common Pitfalls

1. **BER 和 DER 不完全互换** — DER 是 BER 的子集，但 DER 要求唯一编码。X.509 证书必须用 DER
2. **PER 不能直接用 BER 解码器解码** — PER 不保留 TLV 结构，必须按 ASN.1 模块定义解码
3. **PER Aligned vs Unaligned** — Aligned 在字段边界填充到字节；Unaligned 逐比特紧凑排列不填充。3GPP RRC 用 Aligned，ETSI LI HI2 PDU 用 Unaligned
4. **Tag Number ≥ 31 用多字节编码** — 不能直接写入 bit 5-1，用后续字节指示
5. **INTEGER 有符号编码** — 0x00 前缀表示正数高位为 0，0xFF 前缀表示负数
6. **SEQUENCE 和 SET 的区别** — SEQUENCE 按定义顺序编码（有序），SET 按 tag 升序编码（无序）
7. **pyasn1 不支持 PER 解码** — 需要安装 `asn1tools` 并在 Hermes venv 中运行（系统 pip 受 PEP 668 保护）
8. **asn1tools 不支持 `...` 扩展标记** — ASN.1 定义中的 `...` 会导致解析器报错 `Expected '}'`，需要在编译前移除扩展标记
9. **HW X2 数据的前导厂商头** — 某些 HW 版本的 X2 IRI PDU 在 PER 载荷前加了 4 字节厂商封装头，需剥离后才能正确解码
10. **X2 HEX 首字节为 0x30 时是 BER 而非 PER** — ETSI TS 102 232-1 规定 PER Unaligned，首字节不应是 Standard SEQUENCE Tag
11. **BER `length == 0` 不代表 TLV 结束** — `93 00`（SS-Status NULL）的 length=0 仅表示 value 为空，后面可能还有后续 TLV。解析时遇到 length=0 应继续读取下一个 TAG，不能 break
12. **三种 TAG 假设分析法** — 不确定 TAG 编码长度时可用三种假设对比：短格式(TAG=byte&0x1F)、2字节长格式(取第2字节低7位)、标准长格式(续字节低7位拼接)。参考 `references/ber-tag-assumption-analysis.md`

## Verification Checklist

- [ ] 能手动解释 BER TLV 结构中 Tag/Length/Value 每个字节的含义
- [ ] 能区分 PER Aligned 和 PER Unaligned 的适用场景
- [ ] 知道 3GPP RRC 使用哪种 ASN.1 编码规则
- [ ] 知道 ETSI LI HI2/HI3 PDU 使用哪种 ASN.1 编码规则
- [ ] 能用 `~/.hermes/scripts/asn1-codec.py` 解码 BER 数据
- [ ] 能用 `asn1tools` 解码/编码 PER 数据（`compile_string(spec, "uper")`）
- [ ] 能读出 OID 的整数序列（如 1.2.840... 对应 0x2A 0x86...）
- [ ] Python 中能用 `pyasn1` 定义和编码自定义 SEQUENCE
- [ ] 引用辅助脚本：`skill_view("asn1-codec", "scripts/use-asn1-codec.sh")`
- [ ] ETSI LI 场景参考：`skill_view("asn1-codec", "references/etsi-li-asn1.md")`
- [ ] X2 HEX 验证方法：`skill_view("asn1-codec", "references/x2-hex-validation.md")`
- [ ] X2 验证脚本：`skill_view("asn1-codec", "scripts/verify-x2-hex.py")`
- [ ] 三种 TAG 假设分析法：`skill_view("asn1-codec", "references/ber-tag-assumption-analysis.md")`
- [ ] BER 官方规范 PDF 本地：`~/knowledge/telecom/3gpp/ITU-T_X.690-0207_BER.pdf`
- [ ] PER 移动通信参考：`skill_view("asn1-codec", "references/per-mobile-signaling-reference.md")`
- [ ] ETSI-ASN1-Assistant V3（HI2 IRI 解码 Flask App）：`skill_view("asn1-codec", "references/etsi-asn1-assistant-app.md")`
- [ ] Dubuisson 教材参考：`skill_view("asn1-codec", "references/dubuisson-asn1-book-reference.md")`
- [ ] Larmouth ASN.1 Complete 参考：`skill_view("asn1-codec", "references/larmouth-asn1-complete-reference.md")`
