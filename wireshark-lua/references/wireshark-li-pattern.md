# Wireshark LI (合法监听) 数据包分析参考

## 适用场景

当分析 PCAP 中包含 LI 相关 X 接口流量（X1/X2/X3）时，补充 wireshark-lua 技能中的通用解码逻辑。

## 常见 LI 协议

| 接口 | 协议 | 传输层 | 目的 |
|------|------|--------|------|
| X1 | BER (ASN.1) | TCP/SCTP | 设控命令 |
| X2 | PER (ASN.1) | TCP/SCTP | IRI 信令 |
| X3 | Raw IP / GTP | IP/UDP | 媒体内容 |
| HI2/HI3 | BER (ASN.1) | TCP | 华为 ZTLIG 内部接口 |

## Wireshark 分析要点

1. **X2 接口** — 通常使用 PER 编码，需要专用的 ASN.1 解码表
2. **X3 媒体流** — 通常是 RTP 包，使用 Wireshark 的 `telephony → RTP → Show All Streams`
3. **BER TLV 追踪** — 使用 `wireshark-lua` 技能中的 BER dissector 模板，配合已知 TAG 值解码
4. **TCP 重组** — X1/X2 常需要在 Wireshark 中启用 TCP 流重组（Edit → Preferences → Protocols → TCP → "Allow subdissectors to reassemble TCP streams"）

## 第三方解码器

对于非标准厂商接口（华为 ZTLIG、中兴 LIS、Ericsson MSS），需配合 ETSI-ASN1-Assistant 或厂商提供的 ASN.1 定义文件解码。纯 Wireshark 无法解码私有 X2 PER 编码流。
