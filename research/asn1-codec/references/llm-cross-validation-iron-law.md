# BER/TLV/确定性知识交叉验证铁律

> 铁律定义：任何编程、确定性知识或技能类任务必须做交叉验证，
> 不能仅靠当前 LLM 的输出来判定正确性。
>
> 来源：用户 andymao 在 2026-06-22 BER TAG 分析会话中明确声明。

---

## 适用范围

- BER/DER/PER 编解码、TAG/偏移量计算
- 任何协议解析（TLV、ASN.1、二进制格式）
- CRC/校验和计算
- 编码转换（TBCD、HEX、Base64）
- 任何"要么对要么错"的确定性知识

## 实验证据

47 byte MAP 码流交叉验证：

| 模型 | IMSI 解码 (46010000000024) | TAG 结构 | 结论 |
|------|:--------------------------:|:--------:|:----:|
| DeepSeek-V3 (siliconflow.com) | ❌ 完全错误(919644073) | ❌ 多处错误 | **不可靠** |
| Qwen3.5-397B (siliconflow.cn) | ✅ 正确 | ⚠️ 漏了 B0 21 节点 | 细节有遗漏 |
| pyasn1 0.6.3 | ✅ 正确 | ✅ 11/11 完全一致 | 标准参考 |

结论：LLM 的概率生成特性不适合做确定性协议解析的正确性验证。
标准库（pyasn1、asn1tools、Wireshark）才是正确做法。

## 标准工作流

1. **先猜** — 用 LLM 分析码流结构，作为初稿假设
2. **再验** — 用标准库工具（pyasn1/asn1tools/Wireshark）解码验证
3. **三对比** — 三种 TAG 假设（2位/4位/6位）交叉对比
4. **定结论** — 以工具输出为准，LLM 输出仅供参考

## 验证脚本

```bash
# BER 解码验证
~/.hermes/venv/bin/python ~/.hermes/scripts/asn1-codec.py decode-hex "02012a"

# 三种 TAG 假设分析
python3 /home/andymao/ber-tag-analyzer.py "30 2D 80 08 64 10 00 00 00 00 20 F4 B0 21 A1 1F"

# pyasn1 标准解码
python3 -c "
from pyasn1.codec.ber import decoder
data = bytes.fromhex('02012a')
decoded, _ = decoder.decode(data)
print(decoded)  # 验证结果
"
```

## 参考

- `ber-tag-analyzer.py`: `/home/andymao/ber-tag-analyzer.py`
- 知识库: `~/knowledge/telecom/3gpp/ber-tlv-tag-analyzer-tool-and-validation.md`
- 官方 BER 规范: `~/knowledge/telecom/3gpp/ITU-T_X.690-0207_BER.pdf`
