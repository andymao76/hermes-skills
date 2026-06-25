# scapy SCTP 数据块遍历

## 背景

电信 Diameter 消息通常通过 SCTP 传输（PPID 0x2e = 46）。scapy 可以解析 SCTP，
但对 SCTPChunkData 的访问方式与直觉不同。

## 版本信息

- scapy 版本：未固定（测试时使用 Ubuntu 24.04 自带或 pip 最新版）
- SCTPChunkData 层的继承结构：`Packet > SCTPChunkData`
- SCTP 层的 payload：直接指向第一个 SCTPChunkData（而非 chunks 列表）

## 关键发现

### 1. `sctp.chunks` 永远是空列表

无论 PCAP 中有多少个 SCTP DATA chunk，`getattr(sctp, "chunks", [])` 都返回 `[]`。
这个属性不存在或未被填充。

### 2. 数据块是链式结构

scapy 将多个 SCTP 数据块组织为链式 Packet 层：

```
SCTP（第1层）
  └─ payload → SCTPChunkData #1
                ├─ data: b'\x01\x00\x01\xc4...'  ← Diameter 消息
                └─ payload → SCTPChunkData #2
                              ├─ data: b'\x01\x00\x01\xc0...'  ← 另一个 Diameter 消息
                              └─ payload → NoPayload
```

### 3. Diameter 载荷在 `.data` 而非 `.payload`

SCTPChunkData 的字段包括：
- type, reserved, delay_sack, unordered, beginning, ending
- len, tsn, stream_id, stream_seq, proto_id
- **data** — 实际的 Diameter 消息载荷（bytes）

`bytes(chunk.payload)` 返回的是 SCTP 块头部（type/flags/length）而非 Diameter 载荷。

### 4. 对偶性验证

tcpdump 输出：
```
sctp (1) [DATA] (B)(E) [TSN: 607882506] [SID: 1] [SSEQ 60182] [PPID 0x2e],
(2) [DATA] (B)(E) [TSN: 607882507] [SID: 1] [SSEQ 60183] [PPID 0x2e]
```

对应 scapy 中两个链式 SCTPChunkData 对象。

## 正确的遍历代码

```python
import scapy.all as scapy

pkts = scapy.rdpcap("capture.pcap")
results = []

for pkt_num, pkt in enumerate(pkts, 1):
    if not pkt.haslayer("SCTP"):
        continue

    chunk = pkt["SCTP"].payload  # → 第一个 SCTPChunkData

    while chunk is not None and hasattr(chunk, "data"):
        payload_data = chunk.data  # 这里是 Diameter 载荷

        if payload_data and len(payload_data) >= 20 and payload_data[0] == 1:
            # 首字节 0x01 = Diameter version 1
            results.append((pkt_num, payload_data))

        # 跳转到下一个数据块（或 NoPayload）
        chunk = chunk.payload
        if not hasattr(chunk, "data"):
            break
```

## 注意事项

- `pkt.haslayer("SCTP")` 直接可用 — 无需先检查 `hasattr(scapy, "SCTP")`
- 如果 PCAP 是多块 DATA，链式遍历确保不会遗漏
- 此行为在 scapy 2.5+ 中得到验证，更低版本可能需要其他适配
