# NAS 消息类型偏移调试

## 问题

某些 5G PCAP 数据集（如 STCS 项目测试数据）的 NAS 消息类型不在标准位置 `data[1]`，而在 `data[2]`。

## 数据集特征

| 特征 | 值 |
|------|-----|
| 消息类型偏移 | `data[2]`（非标准） |
| byte[0] EPD | 0x07（5GMM，标准） |
| byte[0] SHT | 0x0E（非标准，标准应为 0x00-0x03） |
| byte[1]=0x00 | 裸消息，消息类型在 byte[2] |
| byte[1]=0x02 | 安全封装（wrapped），内层 NAS 从 byte[7] 开始 |
| byte[1]=0x04 | 加密封装（ciphered），内层 NAS 从 byte[7] 开始 |

## 调试方法

### 1. 扫描数据集确认偏移

```python
from 源码.utils.constants import NAS_5GMM_MSG
patterns = {}
for msg in decoded_messages:
    np = msg.fields.get('nas_pdu', '')
    if np:
        raw = bytes.fromhex(np)
        b2 = raw[2]
        name = NAS_5GMM_MSG.get(b2, f'0x{b2:02X}')
        patterns[b2] = patterns.get(b2, 0) + 1
```

### 2. 检测封装格式

```python
b0_epd = data[0] >> 4   # 应为 7 (5GMM)
b1 = data[1]            # 0=裸, 2=安全封装
b2 = data[2]            # 消息类型（非标准）

if b1 == 0x02 and len(data) >= 8 and data[7] == 0x7E:
    inner = data[7:]   # 内层 NAS
    inner_msg_type = inner[2]  # 同样 byte[2] = 消息类型
```

## 验证

- 如果 byte[2] 能正确匹配 5GMM 消息类型（0x41=REGISTRATION_REQUEST, 0x43=REGISTRATION_COMPLETE, 0x45=DEREGISTRATION 等），说明此数据集使用偏移=2
- 如果 byte[1] 能匹配消息类型，则使用标准偏移=1
