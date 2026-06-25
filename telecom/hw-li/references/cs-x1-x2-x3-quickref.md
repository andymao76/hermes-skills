# HW CS X1/X2/X3 接口速查

## X1 接口 — 设控
| 特性 | 值 |
|------|-----|
| 传输 | TCP/IP, NE=Server, LIG=Client |
| 并发 | ≤5 连接 |
| 超时 | 5s 无响应即失败 |
| 用户名密码 | 华为无限制, Utimaco 有 |
| NEID错误 | RC 9 |

**号码格式**: GMSC→ISDN, 其他MSC→MSISDN

## X2 接口 — 信令
- **BER编码**: TLV结构, ≥128用0x81前缀
- **HW头**: `aa 05 01 00 01 a5 01 a5 04 ff ff ff ff ff`
- **Cs-Event枚举**: 1=establishment, 2=answer, 5=release, 18=ims-Gen-IRI-Report
- **CDR必查字段**: LIID, CIN, EventDetail, EventDirection, CallingNum, CalledNum

## X3 接口 — 媒体
- CS: ISUP/PRA/SIP 复制 → ISUP关联
- SIP-I: Application消息(Access Transport携LIID+CIN) → 四元组关联
- IMS: RTP复制 → LIID+imsChargingID关联

## Wireshark 过滤
- LIID: `data.data contains <ASCII_HEX>` (如 25115→32:35:31:31:35)
- CIN: `data.data contains <ASCII_HEX>` (8字节)
- 事件标签: `0x9F21` 位于码流末尾
- CIN 过滤: `frame contains "CIN值"`
