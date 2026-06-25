# ETSI LI X2 (HI2 PDU) HEX 数据规范性验证

适用场景：华为/中兴/爱立信 CS 域的 X2 接口 IRI 数据，编码为 ASN.1 PER Unaligned。

## 验证流程

```
输入 HEX
   │
   ├── [关卡1] 基础格式
   │     HEX 有效？ 长度 > 10 bytes？
   │     首字节不是 0x30/0x31 (BER Tag)？
   │
   ├── [关卡2] PER 解码
   │     asn1tools 编译 HI2-PDU ASN.1 定义
   │     decode("HI2-PDU", raw_bytes) 成功？
   │
   ├── [关卡3] 字段约束
   │     LIID: OCTET STRING (1..128)
   │     Timestamp: year(0..9999), month(1..12), day(1..31)
   │               hour(0..23), minute(0..59), second(0..59)
   │     ServiceType: csCall(0), sms(1), mms(2), lcs(3), pS(4), ...
   │
   └── [关卡4] 厂商特有问题
         HW: 偶有额外封装头、尾部 0x00 填充
         中兴: ...
         爱立信: ...
```

## 工具

`scripts/verify-x2-hex.py` — 全自动验证脚本，输出 PASS/WARN/FAIL 判定 + 解码详情。

```bash
~/.hermes/venv/bin/python scripts/verify-x2-hex.py '83010203041fa950e780221a99818188'
```

## 厂商 X2 行为对比

| 检查点 | 华为 (HW) | 合规？ |
|--------|-----------|--------|
| LIID 编码 | 有时用纯 ASCII 字符串（如 "861234567890"） | ✅ 符合 OCTET STRING 定义 |
| Timestamp 精度 | second 可能始终为 0（只精确到分） | ⚠ 合法但欠妥 |
| 扩展字段 | 可能在 `...` 扩展区插入厂商私有信息 | ✅ 标准允许，接收方需能跳过 |
| ServiceType | CS 域固定为 csCall(0) | ✅ 正确 |
| PDU 首字节 | 某些版本在 PER 载荷前加 4 字节厂商头（长度 + 版本） | ❌ 非标，需剥离后再解码 |
| PDU 尾填充 | 偶发补 0x00 到偶数/4 字节对齐 | ⚠ 标准 PER 不要求填充 |

## Wireshark 验证（无脚本时）

```bash
# 直接把 HEX 转 pcap 看
text2pcap -l 147 -u 20000,20001 /tmp/x2_hex.txt /tmp/x2.pcap
tshark -r /tmp/x2.pcap -V | grep -A 30 "HI2"

# 提取关键字段
tshark -r /tmp/x2.pcap -Y "hi2" -T fields \
  -e hi2.lawfulinterceptionidentifier \
  -e hi2.timestamp.year \
  -e hi2.service_data.servicetype
```

## PER 解码失败常见原因

| Wireshark 错误 | 根因 |
|----------------|------|
| [Malformed Packet] | PER 编码损坏，字节错位或长度不对 |
| 字段乱码 | 位偏移计算错误（扩展字段标记位设反） |
| 字段越界（month=13） | HW 编码器 bug |
| 末尾多字节 | PDU 长度声明小于实际传输长度 |
