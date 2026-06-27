# 华为 X2 PCAP 解码常见问题

## TCP 重组问题

### 现象
上传 PCAP 文件后解码失败，错误信息 `DECODE_ERR_NOT_LI` — "报文不符合所选解码库格式"。

### 根因
华为 X2 接口使用 TCP 传输，单个 0xAA 帧的 ASN.1 BER 内容可能超过单个 TCP 段大小（MSS ~1460B）。例如 iRI-Report-record [4] 的内容长度为 1802B，被拆到多个 TCP 段中。

如果不启用 TCP 重组，`parse_pcap()` 提取的是单个 TCP 段的负载，BER 解码器只能读到不完整的数据。

### 诊断方法
```python
# 检查 PCAP 中 0xAA 帧的分布
grep -c "aa" packet_hex  # 检测是否含 0xAA 帧头
```

在 Web UI 中，检测逻辑自动扫描前 50 个包，若发现 ≥3 个 0xAA 帧头且 TCP 重组未开启，会在结果页显示红色警告。

### 解决方案
1. **Web UI**: 勾选「TCP 重组」复选框后重新上传
2. **命令行**: 调用 `parse_pcap(pcap_path, reassemble=True)`

### 相关代码
- `app_linux_v4.py`: `has_aa_no_reassemble` 检测逻辑
- `asn_decode_api_v4.py`: `pre_decode_split_report` — BER 长度越界处理

## BER 长度声明超出可用数据

### 现象
解码报错: `Expected at least N contents byte(s), but got M (M < N)`

### 根因
BER TLV 编码中，内容长度字段声明的长度（如 `82 07 0a` = 1802 字节）可能超出实际可用数据。这在部分 TCP 段或截断的日志文件中常见。

### 修复
`pre_decode_split_report()` 中，当 `offset + header_len + single_len > total_len` 时，不再直接 `break` 跳过整帧，而是取剩余全部数据作为一条记录，让 asn1tools 尝试部分解码。

### 代码位置
`asn_decode_api_v3.py` / `asn_decode_api_v4.py` → `pre_decode_split_report()`
