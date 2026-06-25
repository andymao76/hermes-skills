# SBI HTTP/2 解析参考

## HTTP/2 帧结构

```
+-----------------------------------------------+
| Length (24 bits) | Type (8) | Flags (8)        |
+-----------------------------------------------+
| Stream Identifier (31 bits) | R (1)           |
+-----------------------------------------------+
| Frame Payload (Length bytes)                   |
+-----------------------------------------------+
```

## 帧类型

| 类型码 | 名称 | 用途 |
|-------|------|------|
| 0x00 | DATA | 请求/响应体 |
| 0x01 | HEADERS | HPACK 编码的头部块 |
| 0x04 | SETTINGS | 连接参数协商 |
| 0x07 | GOAWAY | 连接关闭 |
| 0x09 | CONTINUATION | HEADERS 延续 |

## HEADERS 帧标志

| 标志 | 值 | 含义 |
|------|----|------|
| END_STREAM | 0x01 | 流结束 |
| END_HEADERS | 0x04 | 头部块结束 |
| PADDED | 0x08 | 尾部填充 |
| PRIORITY | 0x20 | 带优先级 |

## HPACK 动态表限制

- 静态表索引 1-61（RFC 7541 Appendix A）
- 动态表索引 ≥ 62
- 单包 PCAP 缺少 SETTINGS/HEADERS 帧建立动态表上下文
- **错误特征**: "Invalid table index N" (N ≥ 62)

## Body 服务推断回退

当 HPACK 解码失败时，从 DATA 帧 JSON body 推断：

| Body 特征 | 服务 | 接口 |
|-----------|------|------|
| deregCallbackUri + amfInstanceId | Nudm_UECM | N8 |
| registrationTime + amfInstanceId | Nudm_UECM | N8 |
| smsfInstanceId | Nsmsf_SMService | N20 |
| accessAndMobilitySubscriptionData | Nudm_SubscriberDataManagement | N8 |
| authType + 5G_AKA/EAP_AKA | Nausf_UEAuthentication | N12 |
| pduSessionId | Nsmf_PDUSession | N11 |
| authenticationInfoResult | Nudm_UEAuthentication | N13 |

## SUPI 提取

```python
# URI 路径
import re
supi = re.search(r'/(\d{5,15})(?:/|$)', uri)

# Body 回退（HPACK 失败时）
supi = re.search(r'imsi[-]?(\d{5,15})', body_str)
```

## 5G SBI 服务路径模式

| 服务 | 路径前缀 | 接口 |
|------|---------|------|
| Nudm_UECM | /nudm-uecm/v1/ | N8/N10 |
| Nudm_SubscriberDataManagement | /nudm-sdm/v1/ | N8 |
| Nudm_UEAuthentication | /nudm-ueau/v1/ | N13 |
| Nsmf_PDUSession | /nsmf-pdusession/v1/ | N11 |
| Nausf_UEAuthentication | /nausf-auth/v1/ | N12 |
| Nsmsf_SMService | /nsmsf-sms/v1/ | N20 |

## 已知限界

- **单包 PCAP**: HPACK 动态表无法重建
- **TCP 重组**: 当前未做完整的 TCP 流重组
- **HPACK 表状态**: 跨包解码需要维护 HPACK Decoder 实例状态
- **生产建议**: 使用 tshark `-z follow,tcp,ascii` 或 pyshark 做完整流重组
