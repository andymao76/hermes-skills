# SCTP chunk 解析参考（PCAP 解码场景）

## SCTP 包结构

```
+-- SCTP Common Header (12 bytes) --+
| Source Port (2) | Dest Port (2)   |
| Verification Tag (4)              |
| Checksum (4)                      |
+-----------------------------------+
| Chunk 1: DATA / SACK / HEARTBEAT  |
| Chunk 2: ...                      |
+-----------------------------------+
```

## DATA chunk 结构

```
Bytes  Offset  Field
0      0       Chunk Type = 0x00 (DATA)
1      1       Chunk Flags (U=0x01, B=0x02, E=0x04)
2-3    2       Chunk Length (big-endian)
4-7    4       TSN (Transmission Sequence Number)
8-9    8       Stream Identifier
10-11  10      Stream Sequence Number
12-15  12      Payload Protocol Identifier (PPID)
16+    16      Payload Data
```

**关键偏移**:
- PPID: chunk 起始偏移 + 12（不是 +20！常见错误）
- Payload: chunk 起始偏移 + 16（不是 +28！常见错误）

## PPID 取值

| PPID | 协议 |
|------|------|
| 60 (0x003C) | NGAP (N2) |
| 1024 (0x0400) | NGAP (N2, 某些实现) |
| 63 (0x003F) | N1 NAS / S1AP |

## 非 DATA chunk 类型

| Type | 名称 | 说明 |
|------|------|------|
| 0x00 | DATA | 数据块（需处理） |
| 0x01 | INIT | 关联初始化 |
| 0x02 | INIT ACK | 初始化确认 |
| 0x03 | SACK | 选择性确认（最常见噪音） |
| 0x04 | HEARTBEAT | 心跳 |
| 0x05 | HEARTBEAT ACK | 心跳确认 |
| 0x06 | ABORT | 终止 |
| 0x07 | SHUTDOWN | 关闭 |
| 0x08 | SHUTDOWN ACK | 关闭确认 |
| 0x09 | ERROR | 错误 |
| 0x0C | RE_CONFIG | 重配置 |

**陷阱**: SACK 块在 PCAP 中通常占大多数。错误地将其当作 DATA 块解析，会将 SACK 数据喂给 NGAP/NAS 解码器，产生 IEs=0 的假象。

## 正确解析代码

```python
sctp_bytes = bytes(sctp_packet)
off = 12  # 跳过 SCTP common header
payload = None
ppid = -1

while off + 8 <= len(sctp_bytes):
    chunk_type = sctp_bytes[off]
    chunk_len = int.from_bytes(sctp_bytes[off+2:off+4], 'big')
    
    if chunk_len < 4:
        break
    
    if chunk_type == 0x00:  # DATA chunk
        if off + 16 <= len(sctp_bytes):
            # PPID 在 chunk 内偏移 12
            ppid = int.from_bytes(sctp_bytes[off+12:off+16], 'big')
            # Payload 从 chunk 内偏移 16 开始
            start = off + 16
            end = min(off + chunk_len, len(sctp_bytes))
            if end > start:
                payload = sctp_bytes[start:end]
    # 非 DATA chunk 直接跳过
    
    off += chunk_len
```

## scapy 备选方案

```python
# scapy 内置 SCTP 解析（不如手动可靠，因为 scapy 对 chunk 边界处理有坑）
if pkt.haslayer('SCTP'):
    sctp = pkt['SCTP']
    if hasattr(sctp, 'payload') and hasattr(sctp.payload, 'ppid'):
        ppid = getattr(sctp.payload, 'ppid', -1)
        payload = bytes(sctp.payload)
```

**注意**: scapy 的 `sctp.payload` 只返回第一个 chunk 的 payload，对多 chunk 包需要手动遍历。

## SCTP 包 vs NGAP 消息关系

- 一个 SCTP 包可能包含 1 个或多个 DATA chunk
- 一个 DATA chunk 包含完整的 1 个 NGAP PDU（PER 编码）
- 一个 NGAP PDU 包含 1 个 NAS-PDU IE（内嵌 NAS 消息）
- 大消息可能跨多个 DATA chunk 分片（分段），需要 TSN 连续性检测
