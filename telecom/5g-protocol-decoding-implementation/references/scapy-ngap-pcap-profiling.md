# Scapy 5G NGAP PCAP 快速分析工作流

## 概述

在投入 full pycrate 解码之前，先用 scapy 对 PCAP 做**快速扫描**（PG 级分析），回答以下问题：
- 包里有什么协议？SCTP 占比多少？
- 网络拓扑是怎样的？谁是 AMF？有多少个 gNB？
- NGAP 消息的 PDU 类型分布？ProcedureCode 分布？
- 是否有异常（非 DATA chunk 误入、PPID 异常、时间漂移等）？

## 基础分析脚本

### 1. 协议分布 + 拓扑重建

```python
from scapy.all import rdpcap, IP
from collections import Counter

pkts = rdpcap("capture.pcap")

# 协议分布（IP proto）
proto_counter = Counter()
for p in pkts:
    if IP in p:
        proto_counter[p[IP].proto] += 1

proto_map = {6: 'TCP', 17: 'UDP', 132: 'SCTP', 1: 'ICMP'}
for pnum, cnt in proto_counter.most_common():
    print(f"  {proto_map.get(pnum, f'proto-{pnum}')}: {cnt}")

# IP 对频率（识别核心网元）
ip_pairs = Counter()
for p in pkts:
    if IP in p:
        ip_pairs[(p[IP].src, p[IP].dst)] += 1

print("\nIP对 Top 20:")
for (src, dst), cnt in ip_pairs.most_common(20):
    print(f"  {src:20s} -> {dst:20s}  [{cnt:5d}]")
# 频率最高的 IP = AMF/核心网元
# 多个 src → 同一 dst = gNB → AMF 拓扑
```

**特征判定**：
- 最高频 IP = AMF（5G核心网）
- 多个 src 连接到同一 dst = 多个 gNB 通过 N2 连接到 AMF
- 第 2 高频 IP = 可能另一个 AMF 或 SMF
- SCTP port 38412 = 标准 NGAP N2 端口

### 2. SCTP DATA chunk + NGAP 消息提取

```python
import struct

sctp_payloads = []
for p in pkts:
    if IP not in p or p[IP].proto != 132:
        continue
    raw = bytes(p[IP].payload)
    if len(raw) < 12:
        continue

    sport = (raw[0] << 8) | raw[1]
    dport = (raw[2] << 8) | raw[3]

    offset = 12  # 跳过 SCTP common header
    while offset + 8 <= len(raw):
        chunk_type = raw[offset]
        chunk_flags = raw[offset+1]
        chunk_len = ((raw[offset+2] << 8) | raw[offset+3])
        if chunk_len < 4 or offset + chunk_len > len(raw):
            break

        if chunk_type == 0x00:  # DATA chunk
            ppid = struct.unpack('>I', raw[offset+12:offset+16])[0]
            data_start = offset + 16
            data_len = chunk_len - 16
            if data_start + data_len <= len(raw) and data_len > 0:
                sctp_payloads.append({
                    'ppid': ppid,
                    'sport': sport, 'dport': dport,
                    'data': raw[data_start:data_start+data_len],
                    'src': p[IP].src, 'dst': p[IP].dst
                })

        offset += chunk_len

# NGAP = PPID=60 (0x003C)
ngap_msgs = [m for m in sctp_payloads if m['ppid'] == 60]
print(f"NGAP消息: {len(ngap_msgs)} / SCTP总DATA: {len(sctp_payloads)}")
```

### 3. NGAP PDU 类型 + ProcedureCode 快速扫描

无需 pycrate，直接从 PER 编码的 PDU 头部提取关键字段：

```python
# NGAP-PDU ::= CHOICE {
#   initiatingMessage         [0] SEQUENCE {...},
#   successfulOutcome         [1] SEQUENCE {...},
#   unsuccessfulOutcome       [2] SEQUENCE {...}
# }
# PER Aligned 编码：
#   ext(1bit) = 0
#   choice_index(2bits): 0=init, 1=success, 2=fail
#   padding to byte boundary
#   procedureCode (INTEGER 0..255, 8bit)

ngap_procs = {
    0: "AMFConfigurationUpdate",    1: "AMFConfigurationUpdateAcknowledge",
    2: "AMFConfigurationUpdateFailure", 3: "AMFStatusIndication",
    4: "CellTrafficTrace",          5: "DeactivateTrace",
    6: "DownlinkNASTransport",      11: "ErrorIndication",
    12: "HandoverCancel",           13: "HandoverCancelAcknowledge",
    14: "HandoverPreparation",      15: "HandoverPreparationAcknowledge",
    16: "HandoverPreparationFailure", 17: "HandoverRequest",
    18: "HandoverRequestAcknowledge", 19: "HandoverFailure",
    20: "HandoverNotification",     21: "HandoverSuccess",
    22: "UEContextReleaseRequest",  23: "InitialContextSetupRequest",
    24: "InitialContextSetupResponse", 25: "InitialContextSetupFailure",
    26: "InitialUEMessage",         27: "NGReset",
    28: "NGResetAcknowledge",       29: "NGSetup",
    30: "NGSetupAcknowledge",       31: "NGSetupFailure",
    34: "Paging",                   35: "PathSwitchRequest",
    36: "PathSwitchRequestAcknowledge", 37: "PathSwitchRequestFailure",
    38: "PDUSessionResourceModifyRequest", 39: "PDUSessionResourceModifyResponse",
    40: "PDUSessionResourceModifyIndication", 41: "PDUSessionResourceModifyConfirm",
    42: "PDUSessionResourceReleaseCommand", 43: "PDUSessionResourceReleaseResponse",
    44: "PDUSessionResourceSetupRequest", 45: "PDUSessionResourceSetupResponse",
    46: "PDUSessionResourceNotify", 54: "RerouteNASRequest",
    61: "UEContextReleaseCommand",  62: "UEContextReleaseComplete",
    67: "UplinkNASTransport",
}

pdu_types = Counter()
proc_codes = Counter()

for msg in ngap_msgs:
    payload = msg['data']
    if len(payload) < 2:
        continue
    first = payload[0]
    pdu_choice = first >> 6  # top 2 bits
    pdu_types[pdu_choice] += 1
    if len(payload) > 1:
        pc = payload[1]
        pname = ngap_procs.get(pc, f'proc_{pc}')
        proc_codes[pname] += 1

print("PDU类型: 0=initMsg, 1=successOutcome, 2=failOutcome")
for t, cnt in pdu_types.most_common():
    print(f"  choice_{t}: {cnt}")

print("\nProcedureCode分布(Top 20):")
for pc, cnt in proc_codes.most_common(20):
    print(f"  {pc}: {cnt}")
print(f"  共 {len(proc_codes)} 种")
```

### 4. 时间范围分析

```python
import datetime
first = float(pkts[0].time)
last = float(pkts[-1].time)
print(f"时间范围: {datetime.datetime.fromtimestamp(first)} ~ {datetime.datetime.fromtimestamp(last)}")
print(f"持续时间: {last-first:.2f}秒")
```

## 常见信号模式解读

### 初始注册潮（InitialContextSetupResponse 占优）

InitialContextSetupResponse 占 >60% 表示：
- 大量 UE 同时发起注册（网络刚启动 / TAU 周期到达）
- gNB 密集上报 UE 上下文建立结果
- 正常高话务场景

### 切换频繁（HandoverPreparation + HandoverSuccess 占 20%+）

- 用户处于移动状态（高铁/高速场景）
- 信号覆盖边缘（gNB 间频繁切换）
- 需关注切换成功率（successfulOutcome vs unsuccessfulOutcome 比例）

### CellTrafficTrace 大量出现

- 网络在做主动优化/监测
- 运营商开启 Trace 功能收集小区级统计

### NGSetup 多次出现

- gNB 频繁重启/重连（异常）
- 或 AMF 侧周期性重置
- 正常值：每个 gNB 首次上线只出现 1 次

## 网络拓扑判定特征

| 特征 | 解读 |
|------|------|
| 同一 IP 包量远超其他（如 9237 vs 538） | 该 IP = AMF（中心节点） |
| 多个不同 src IP 指向同一 dst IP | 多个 gNB 通过 N2 连接到同一 AMF |
| SCTP port 38412 双向通信 | 标准 NGAP N2 接口 |
| 出现 38422 / 36422 等端口 | 可能涉及 SMF 或其他 NFs |
| 出现 N26 接口（MME ⇄ AMF） | 4G/5G 互操作场景 |
| 出现 183.9.x.x 段 | 核心网内部节点（非 gNB） |

## 适用场景

- **快速定界**：拿到一个大型 PCAP（如 419MB/160万包），先快速扫描再决定深入解码方向
- **异常检测**：对比正常基线，发现异常的 ProcedureCode 或 PDU 类型比例
- **拓扑验证**：验证配置中的网元拓扑是否与抓包一致
- **数据筛选**：确定哪些 IP 对/端口对应哪个 NF，选择性提取

## 限制

- 此方法只提取 PDU 头部 2 字节（pdu_choice + procedureCode），无法解码 IE 内容
- 如需完整 NGAP IE 解码，仍需使用 pycrate `from_aper()` + 6 模块初始化
- PER 编码的 pdu_choice 推断基于标准 NGAP-PDU CHOICE 编码假设（ext=0），对 ext=1 的数据可能不准确
- 无法区分 intra-gNB handover 和 inter-gNB handover（需完整 IE 解码）
