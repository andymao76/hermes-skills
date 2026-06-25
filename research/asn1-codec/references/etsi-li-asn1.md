# ETSI Lawful Interception 中的 ASN.1 应用

## HI2 PDU（信令接口 — IRI）

定义在 TS 102 232-1，使用 **ASN.1 PER Unaligned** 编码。

核心数据类型：

```asn1
HI2-PDU ::= SEQUENCE {
    lawfullInterceptionIdentifier  LawfulInterceptionIdentifier,
    timestamp                      Timestamp,
    serviceData                    ServiceData OPTIONAL,
    ...
}

LawfulInterceptionIdentifier ::= OCTET STRING (SIZE(1..128))

Timestamp ::= SEQUENCE {
    year          INTEGER (0..9999),
    month         INTEGER (1..12),
    day           INTEGER (1..31),
    hour          INTEGER (0..23),
    minute        INTEGER (0..59),
    second        INTEGER (0..59),
    ...
}

ServiceData ::= SEQUENCE {
    serviceIdentifier  ServiceIdentifier,
    serviceType        ServiceType,
    ...
}
```

## HI3 PDU（内容接口 — CC）

同样使用 **ASN.1 PER Unaligned** 编码：

```asn1
HI3-PDU ::= SEQUENCE {
    interceptedContent  InterceptedContent,
    contentType         ContentType,
    sequenceNumber      SequenceNumber OPTIONAL,
    ...
}
```

## 与 3GPP TS 33.128 的关系

5G LI 的 IRI/CC 载荷定义在 **3GPP TS 33.128** 中，使用 ASN.1 描述。ETSI TS 102 232-7 引用这些定义作为 5G 唯一的交付机制。

关键区别：
- 3GPP TS 33.128 定义**监听的内容结构**（什么数据被拦截）
- ETSI TS 102 232 定义**交付的封装格式**（如何传递给 LEA）
- ETSI 部分使用 PER Unaligned，而 3GPP RRC 使用 PER Aligned

## 使用 Wireshark 解码

当 pcap 文件中包含 HI2/HI3 PDU 时：

```bash
# 显示所有 HI2/HI3 包
tshark -r capture.pcap -Y "hi2 || hi3"

# 查看 ASN.1 解码详情
tshark -r capture.pcap -Y "hi2" -V

# 导出特定字段
tshark -r capture.pcap -Y "hi2" -T fields \
  -e hi2.lawfulinterceptionidentifier \
  -e hi2.timestamp
```

## 相关 OID（ETSI LI 特有）

```text
0.0.8.102.232.1.1    ETSI TS 102 232-1 HI2 PDU
0.0.8.102.232.1.2    ETSI TS 102 232-1 HI3 PDU
```

## PER 编码完整参考

移动通信信令 PER 编码（PER Aligned / PER Unaligned / 编码公式 / 官方标准 / 学习路线）已整理在：

- `~/knowledge/telecom/lawful_interception/per-encoding-mobile-signaling-reference.md`

