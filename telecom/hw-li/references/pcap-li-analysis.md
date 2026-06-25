# PCAP/LI 数据分析参考

## Siemens SBC LI 上报（hw-sbc-imsbase）
- 目录：`PCAP/hw-sbc-imsbase/hw-SBC-imsbase/`
- LIID=10013（文件名和pcap数据层中确认）
- 数据层头：`aa05` magic + TLV 结构

## SIP-I ISUP 接口（hw-sip-i）
- 目录：`PCAP/hw-sip-i/`
- ISUP IAM (ssf-1-bussy-call-transfor.pcap)
- Calling Party Subaddress 含 LIID 反序BCD
- ORI 文件：二进制 TLV 含 LIID/OPERID/CID

## 验证数据
- LIID=84335 → 反序BCD `48 33 F5` ✓
- OPERID=63601 → ASCII ✓
- CID=009515677 → BCD `00 95 15 67 7F` ✓
- CIN 0x40EB9FC = 68073980 ✓

详细笔记：`knowledge/telecom/lawful_interception/pcap-volte-sip-i-li-data-layer-analysis.md`
