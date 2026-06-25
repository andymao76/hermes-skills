# BER TAG 编码规则 (ITU-T X.690) 与三方验证记录

> 来源: ITU-T X.690 (02/2021) §8.1.2 / ISO/IEC 8825-1
> 验证工具: pyasn1 0.6.3, tomkp/ber-tlv (GitHub), 自研数学验证
> 验证日期: 2026-06-22

## 一、BER Identifier Octet 结构 (X.690 §8.1.2)

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

### 常见 BER 首字节速查

| 字节 | 结构 | TAG | 含义 |
|:----:|------|:---:|------|
| 0x02 | 00_0_00010 | 2 | Universal Primitive INTEGER |
| 0x04 | 00_0_00100 | 4 | Universal Primitive OCTET STRING |
| 0x05 | 00_0_00101 | 5 | Universal Primitive NULL |
| 0x30 | 00_1_10000 | 16 | Universal Constructed SEQUENCE |
| 0x31 | 00_1_10001 | 17 | Universal Constructed SET |
| 0x80 | 10_0_00000 | 0 | Context-Specific Primitive [0] |
| 0xA0 | 10_1_00000 | 0 | Context-Specific Constructed [0] |
| 0xB0 | 10_1_10000 | 16 | Context-Specific Constructed [16] |
| 0x90 | 10_0_10000 | 16 | Context-Specific Primitive [16] |
| 0x9F | 10_0_11111 | ≥31 | Context-Specific Primitive 长格式标记 |

## 二、短格式 TAG (X.690 §8.1.2.4)

**规则：** Tag Number ≤ 30 时，直接编码在首字节低5位。

`TAG = first_byte & 0x1F`

**全部 17 个测试值（已验证通过）：**

| 字节 | 二进制 | 低5位 | TAG | 含义 |
|:----:|:------:|:-----:|:---:|------|
| 0x80 | 10000000 | 00000 | 0 | Context [0] primitive |
| 0x81 | 10000001 | 00001 | 1 | Context [1] primitive |
| 0x82 | 10000010 | 00010 | 2 | Context [2] primitive |
| 0x83 | 10000011 | 00011 | 3 | Context [3] primitive |
| 0x85 | 10000101 | 00101 | 5 | Context [5] primitive |
| 0x89 | 10001001 | 01001 | 9 | Context [9] primitive |
| 0x90 | 10010000 | 10000 | 16 | Context [16] primitive |
| 0x8F | 10001111 | 01111 | 15 | Context [15] primitive |
| 0x8D | 10001101 | 01101 | 13 | Context [13] primitive |
| 0x8A | 10001010 | 01010 | 10 | Context [10] primitive |
| 0x8B | 10001011 | 01011 | 11 | Context [11] primitive |
| 0x8C | 10001100 | 01100 | 12 | Context [12] primitive |
| 0x93 | 10010011 | 10011 | 19 | Context [19] primitive |
| 0x97 | 10010111 | 10111 | 23 | Context [23] primitive |
| 0xA4 | 10100100 | 00100 | 4 | Context [4] constructed |
| 0xAE | 10101110 | 01110 | 14 | Context [14] constructed |
| 0xB2 | 10110010 | 10010 | 18 | Context [18] constructed |

**⚠️ 常见错误：** 新手误用 `byte & 0x7F`（取低7位），正确应为 `byte & 0x1F`（低5位）。
- `0xA4 & 0x7F = 36` ❌
- `0xA4 & 0x1F = 4` ✓

## 三、长格式 TAG (X.690 §8.1.2.4.1)

**规则：** Tag Number ≥ 31 时，首字节低5位=11111（标记），续字节存储实际值。

续字节结构:
- bit 8 = continuation flag: 1=还有续字节, 0=最后字节
- bit 7-1 = 7-bit 值段（big-endian 拼接）

### 验证

| 编码 | 字节 | 首节分析 | 续节拼接 | TAG |
|:----:|:----:|---------|:-------:|:---:|
| 4位假设 | BF 50 | 10_1_11111 (Context Constructed) | 50 & 0x7F = 80 | **80** |
| 6位假设 | 9F 81 48 | 10_0_11111 (Context Primitive) | (1<<7)\|72=200 | **200** |
| X.690示例 | 5F 28 | 01_0_11111 (Application Primitive) | 28 & 0x7F = 40 | **40** |
| EMV | 9F 27 | 10_0_11111 (Context Primitive) | 27 & 0x7F = 39 | **39** |

## 四、pyasn1 三方验证 (ground truth)

### 验证方法

```python
from pyasn1.codec.ber import decoder
from pyasn1.type import univ

data = bytes.fromhex("30 2D 80 08 64 10 00 00 00 00 20 F4...")
decoded, remainder = decoder.decode(data, asn1Spec=univ.Any())
```

### MAP insertSubscriberData 验证结果 (11/11)

| # | 偏移 | TAG | 字段 | 脚本 | pyasn1 |
|:-:|:----:|:---:|------|:----:|:------:|
| 0 | 0 | 30(SEQUENCE) | InsertSubscriberDataArg | ✓ | ✓ |
| 1 | 2 | 80([0]) | IMSI | ✓ | ✓ |
| 2 | 12 | B0([16]) | SubscriberData | ✓ | ✓ |
| 3 | 14 | A1([1]) | 子结构入口 | ✓ | ✓ |
| 4 | 16 | 30(SEQUENCE) | 内部序列 | ✓ | ✓ |
| 5 | 18 | 02(INTEGER) | msNetworkCapability | ✓ | ✓ |
| 6 | 21 | 90([16]) | BearerService | ✓ | ✓ |
| 7 | 25 | 92([18]) | Teleservice | ✓ | ✓ |
| 8 | 30 | 93([19]) | SS-Status (NULL) | ✓ | ✓ |
| 9 | 32 | 94([20]) | Ext-BearerService | ✓ | ✓ |
| 10 | 36 | 80([0]) | ExtensionContainer | ✓ | ✓ |

### BUG 发现与修复

**问题：** 脚本在 `length == 0` 时直接 `break`，导致 `93 00`（SS-Status NULL）之后的 `94` 和 `80` 两个节点被遗漏。

**修复：** `length == 0` 时不 `break`，仅不推进 offset（已在下一个 TAG 位置）。详见 `scripts/ber-tag-analyzer.py` 中 `analyze_structure()` 的 `if length == 0: pass` 处理。

## 五、LLM 不可用于 BER 结构验证

| 模型 | IMSI解码 | TAG结构 | 结论 |
|------|:--------:|:-------:|------|
| DeepSeek-V3 | ❌ 919644073 | ❌ 多处错误 | 不可靠 |
| Qwen3.5-397B | ✅ 正确 | ⚠️ 漏B0层 | 大部分正确但有遗漏 |

**正确验证路径：** Python 脚本 → pyasn1 标准库 → Wireshark 抓包对照

## 六、完整验证命令

```bash
# 结构遍历分析
python3 scripts/ber-tag-analyzer.py "30 2D 80 08 64 10 00 00 00 00 20 F4 B0 21 A1 1F 30 1D 02 01 01 90 02 F1 21 92 03 24 42 1F 93 00 94 02 01 2A 80 09 02 91 96 40 40 73 00 00 00"

# 数学验证
python3 scripts/ber-tag-verify.py --verbose

# pyasn1 验证
python3 -c "from pyasn1.codec.ber import decoder; d=bytes.fromhex('302D800864100000000020F4B021A11F301D0201019002F121920324421F93009402012A800902919640407300000000'); print(decoder.decode(d))"
```

## 七、本地 PDF 规范文件

以下 PDF 已下载至知识库 `knowledge/telecom/3gpp/` 目录：

| 文件 | 版本 | 大小 | 说明 |
|------|:----:|:----:|------|
| `ITU-T_X.690-202102_BER.pdf` | v2021 | 822K | **现行有效**，BER/CER/DER 完整规范 |
| `ITU-T_X.690-0207_BER.pdf` | v2007 | 513K | 旧版参考 |
| `ITU-T_X.691-0207_PER.pdf` | v2007 | 638K | PER 编码规范 |

使用本技能时可直接引用这些 PDF 看原文第 X.690 §8.1.2 等章节。
