# Dubuisson ASN.1 教材参考

> Olivier Dubuisson 《ASN.1 — Communication between Heterogeneous Systems》
> 基于 2000 年版本（ASN.1:1994/1997 标准）
> 免费 PDF: https://www.oss.com/asn1/resources/books-whitepapers-pubs/dubuisson-asn1-book.PDF
> 本地: `~/knowledge/telecom/3gpp/dubuisson-asn1-book.PDF`（6.4MB, 590页）
> 本地勘误: `~/knowledge/telecom/3gpp/references/dubuisson-asn1-errata.PDF`（130KB）

## 章节速查

| 章节 | 页码 | 内容 | 实用度 |
|:----|:----:|------|:------:|
| Ch12 Tagging | 205-255 | Tag class、IMPLICIT/EXPLICIT、AUTOMATIC TAGS | ⭐⭐⭐⭐⭐ |
| Ch13 约束 | 257-296 | PER-visible constraints 基础 | ⭐⭐⭐⭐ |
| **Ch18 BER** | **393-415** | **TLV 结构、全部类型编码、属性** | ⭐⭐⭐⭐⭐ |
| Ch19 DER/CER | 417-423 | 确定性编码规则 | ⭐⭐⭐ |
| **Ch20 PER** | **425-451** | **[P][L][V]格式、四种变体、各类型编码** | ⭐⭐⭐⭐⭐ |
| Ch21 其他编码 | 453-459 | LWER/OER/XER 概览 | ⭐⭐ |

## 关键知识点

详见知识库：`~/knowledge/telecom/3gpp/dubuisson-asn1-book-summary.md`

### 最值得注意的要点

1. **Tagging**：IMPLICIT 递归覆盖、CHOICE 强制 EXPLICIT、AUTOMATIC TAGS 推荐配合 PER
2. **BER 偏移量**：与 `ber-tag-analyzer.py` 的三种假设分析一致，length=0 不 break
3. **PER 格式**：无 tag、无固定 length，PER Unaligned 用于 ETSI LI HI2/HI3 PDU
4. **BER INTEGER 补码**：正数高位=0 加 0x00 前导，负数高位=1 加 0xFF 前导
5. **LLM 交叉验证**：教材本身强调 PER 解码必须对照 ASN.1 规范，与用户的铁律一致

## 书中已知局限（2000 年版）

- 未覆盖 ASN.1:2002+ 的新特性（如 PER 的 canonical 变体更详细的定义）
- 编码效率数据基于当时工具，现代实现更快
- 未涉及 3GPP NR (5G) RRC 等新协议

## 姊妹篇

John Larmouth《ASN.1 Complete》(1999) 与本书互补：
- Dubuisson = 编码规则参考手册（查 BER/PER 细节用）
- Larmouth = 教程 + 编译器使用指南 + 设计哲学
- Larmouth 的编码规则部分从 BER→PER 演进叙事，便于理解设计动机
- 学习建议：Dub 用于查，Larmouth 用于学
- Larmouth 参考：`skill_view("asn1-codec", "references/larmouth-asn1-complete-reference.md")`
