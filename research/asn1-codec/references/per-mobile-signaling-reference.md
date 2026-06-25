# PER (Packed Encoding Rules) 编码规范与移动通信信令分析参考

> 用途：移动通信信令分析 (3GPP RRC/NAS / ETSI LI HI2/HI3)
> 数据来源：Google / GitHub 搜索结果 + 本地 skill `asn1-codec` 交叉验证
> 原文位置：`~/knowledge/telecom/lawful_interception/per-encoding-mobile-signaling-reference.md`

## 官方标准

| 标准 | 内容 | 链接 |
|------|------|------|
| ITU-T X.691 (2021) | PER 规范 | https://www.itu.int/rec/T-REC-X.691-202102-I |
| ISO/IEC 8825-2 | 等效 ISO 标准 | https://www.iso.org/obp/ui/#iso:std:iso-iec:8825:-2:en |
| TS 38.331 | NR RRC (5G PER Aligned) | — |
| TS 36.331 | LTE RRC (4G PER Aligned) | — |
| TS 102 232-1 | ETSI LI HI2/HI3 (PER Unaligned) | — |

## PER 核心规则速查

| 约束 | 编码方式 | 比特数 |
|------|----------|--------|
| INTEGER(0..1) | 1 bit | 1 |
| INTEGER(0..100) | ceil(log2(101)) = 7 bits | 7 |
| BOOLEAN | 1 bit (0=F, 1=T) | 1 |
| ENUMERATED {4种} | 2 bits | 2 |
| OCTET STRING SIZE(16) | 固定长度，无前缀 | 128 |
| OCTET STRING SIZE(1..256) | 1字节长度+值 | 可变 |
| SEQUENCE 无OPTIONAL | 按序编码，无标记 | 按字段 |
| SEQUENCE 有OPTIONAL | 1 bit presence/字段 | 按字段 |
| CHOICE {3种} | ceil(log2(3)) bits索引+值 | 按字段 |

## Aligned vs Unaligned

PER Aligned: 每字段结束后填充到字节边界 (3GPP RRC/NAS)
PER Unaligned: 字段间不填充，比特紧凑 (ETSI LI HI2/HI3)

## Python 解码

```python
import asn1tools
# PER Aligned (3GPP)
compiled = asn1tools.compile_string(spec, "per")
# PER Unaligned (ETSI LI)
compiled = asn1tools.compile_string(spec, "uper")
```

## 参考资源

- OSS PER Quick Reference: https://www.oss.com/asn1/resources/asn1-made-simple/asn1-quick-reference/packed-encoding-rules.html
- 3GPP Online Decoder: https://www.3glteinfo.com/tools/3gpp-decoder/
- OpenLI (开源LI): github.com/OpenLI-NZ/openli
- pycrate (3GPP解析): github.com/P1sec/pycrate
