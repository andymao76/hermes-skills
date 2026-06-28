# ZTLIG 三级联动分析体系

> ETSI-ASN1-Assistant(协议层) + r2(代码层) + 完整tmp_so/(系统层)

## 三级定位

| 层次 | 工具 | 能回答的问题 |
|:----:|:----:|-------------|
| **协议层** | ETSI-ASN1-Assistant | PCAP里有哪些BER字段？字段名叫什么？值是什么？ |
| **代码层** | r2 (agc/agf/pdc) | 函数怎么解析这些字段？调用了谁？控制流怎么走？ |
| **系统层** | 完整tmp_so/ (121个.so) | 哪个.so负责哪个厂商的解码？动态库依赖链是什么？ |

## 典型联动流程 (以X1 SubscriberStat为例)

```
Level 1: PCAP (TCP 6666) → ETSI解码
  发现: account=249119284261, locationType=2, location hex

Level 2: r2 分析 libhwx1.so
  agc 揭示完整调用链:
  shell_hwmsc_x1_subscriber_stat (1972B, CLI入口)
    → hwmsc_x1_encode_subscriberStatReq (612B)
      → hwmsc_x1_subscriberStatReq (492B)
        → hwmsc_x1_subscriberStatRsp (344B)
          → hwmsc_x1_decode_X1SubscriberStatRsp (688B)
            → BERDecodeTag → BERDecodeLength → BERDecodeInt

Level 3: tmp_so/ 交叉引用
  libhwx1.so → libber.so(BER) + libcJSON.so(JSON)
             → libztsh.so(CLI) + librdkafka.so(Kafka)
```

## 端到端数据流

PCAP(X1 TCP) ←→ libhwx1.so ←→ libber.so → ztlig1 → Kafka

## 适用场景

1. **Wlan-ue-local-ip 遗漏排查**: ETSI解码PCAP→发现PANI有Wlan-ue-local-ip→r2搜索对应decoder.so
2. **CDR字段缺失定位**: ETSI解码X2 PCAP→r2分析ztlig2的FillHI2_MsgProc
3. **新厂商对接**: ETSI解码新厂商X2数据→r2分析对应decoder.so
