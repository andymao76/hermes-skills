# BER TAG 三种假设分析法

## 适用场景
不确定接收到的码流中 TAG 字段的编码长度时，用三种假设遍历对比。

## 假设规则

| 假设 | 规则 | 含义 |
|:----:|------|------|
| **2位** | `TAG = 首字节 & 0x1F` | 假定 TAG 是 BER 短格式单字节（tag ≤ 30） |
| **4位** | 首字节低5位=11111? 取第2字节低7位 : 取低5位 | 假定 TAG 是2字节长格式 |
| **6位** | 标准 BER 长格式多字节拼接（continuation bytes） | 假定 TAG 是3+字节长格式 |

## 验证示例

原始码流:
```
30 2D 80 08 64 10 00 00 00 00 20 F4 B0 21 A1 1F
30 1D 02 01 01 90 02 F1 21 92 03 24 42 1F 93 00
94 02 01 2A 80 09 02 91 96 40 40 73 00 00 00
```

全部11个TAG节点三种假设均一致，证明均为短格式。

## 工具

`/home/andymao/ber-tag-analyzer.py` — Python 脚本，支持结构遍历和逐字节模式。

```bash
# 结构模式（自动按 BER TLV 跳转）
python3 /home/andymao/ber-tag-analyzer.py "30 2D 80 08..."

# 逐字节模式（固定步进）
python3 /home/andymao/ber-tag-analyzer.py "9F 1F 81..." --mode bytewise --step 20

# 交互模式
python3 /home/andymao/ber-tag-analyzer.py --interactive
```

## 知识库参考

- `~/knowledge/telecom/3gpp/ber-encoding-reference-library.md` — BER 规范参考库
- `~/knowledge/telecom/3gpp/ber-tlv-tag-analyzer-tool-and-validation.md` — 工具说明与验证记录
- `~/knowledge/telecom/3gpp/ITU-T_X.690-0207_BER.pdf` — 官方规范 PDF (513K)
- `~/knowledge/telecom/3gpp/ITU-T_X.691-0207_PER.pdf` — PER 规范 PDF (638K)
