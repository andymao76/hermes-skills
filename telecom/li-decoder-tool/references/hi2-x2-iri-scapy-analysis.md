# HI2 X2 IRI Scapy 分析参考案例：VoWiFi WLAN IP 缺失根因

## 场景

A1 Sudan (ZAIN) VoWiFi 呼叫，OWLS 不显示 WLAN UE 本地 IP。
PCAP 文件：`88776738-7cb4-422a-8ded-5d7b9139bc09.pcap`（57,768 frames）
关键帧：Frame 7345
站点：ATB (阿特巴拉)
运营商：ZAIN Sudan (MCC=634, MNC=007)
时间：2026-06-29

## 问题描述

OWLS 监控界面不显示 VoWiFi 呼叫的 WLAN UE 本地 IP。
T23 版本（flink-tmc-1.0.0，仍处于开发中）修复了"事件无位置信息时导致位置回填失败事件5丢失"——这是一个 **CS 域位置回填修复**，与 VoWiFi WLAN IP 问题无关。

**根因：ZTLIG2 的 HI2 X2 IRI 解码器未实现 PANI 头部的 WLAN 扩展参数解析。**
**修复路径：自底向上三层架构——ZTLIG2 解码层 → GP 库字段扩展层 → OWLS UI 呈现层。**

## 分析流程

### 1. 发现关键帧

```python
from scapy.all import *

packets = rdpcap("capture.pcap")
total = len(packets)
print(f"Total frames: {total}")

# 扫描含 WLAN IP 的帧
targets = []
for i, pkt in enumerate(packets):
    if pkt.haslayer(TCP):
        payload = bytes(pkt[TCP].payload)
        if b'Wlan-ue-local-ip' in payload:
            targets.append({
                'frame': i + 1,
                'sport': pkt[TCP].sport,
                'dport': pkt[TCP].dport,
                'src': pkt[IP].src,
                'dst': pkt[IP].dst,
                'len': len(payload)
            })

# 结果：9 frames with WLAN IP
# Frame 7345: 10.171.103.92:54141 → 10.55.2.11:8892 (1411 bytes)
```

### 2. 确认帧 7345 属性

| 属性 | 值 |
|------|-----|
| 帧编号 | 7345 |
| 时间戳 | 2026-06-29 14:57:11.988 |
| 源→目的 | 10.171.103.92 (P-CSCF) → 10.55.2.11 (ZTLIG2) |
| 协议 | TCP:8892（华为 IMS X2 口，P-CSCF→ZTLIG2 方向） |
| 负载长度 | 1,411 bytes |
| 内容 | HI2 X2 IRI 报告（BER 编码 SIP ACK） |

### 3. BER TLV 解码

TCP payload 的 BER 结构（scapy 分析）：

| 偏移 | Tag | 长度 | 内容 |
|:----|:----|:-----|:-----|
| 0x000 | 0x0C (U/P/12) | 78 | UTF8String — HI2 协议控制字段 |
| 0x04E | 0x39 (U/C/25) | 49 | 时间戳 + tel:+249XXXX0415 |
| 0x085 | 0x22 (U/C/2) | 97 | HI2 X2 报告头（含 icid-value） |
| 0x0E8 | 0x88 (C/P/8) | 1 | 标志位 |
| **0x0ED** | **0x89 (C/P/9)** | **1,174** | **SIP ACK 消息体（PANI 在其中）** |

**关键点：** Tag 0x89 是 SIP 消息体的唯一容器，P-Access-Network-Info 头部嵌入在此。

### 4. PANI 提取

SIP ACK 中的 P-Access-Network-Info 头部：

```
P-Access-Network-Info: IEEE-802.11;
"sbc-domain=atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org";
"ue-ip=10.201.212.200";
"ue-port=5060";
"Wlan-ue-local-ip=196.202.142.135";
"Wlan-ue-local-port=21238"
```

全部 9 个含 WLAN IP 的帧均使用 **同一 IP**（196.202.142.135），端口 21238/16567。

### 5. 知识库交叉验证

引用 `VoWiFi_UMTS_Event5_PANI_Knowledge.md`：

- **UMTS Event 5** = CS Location Update（MAP/BSSAP 协议）
  - 字段：LIID, IMSI, MSISDN, **LAI, Cell ID**
  - **不含：** PANI, Wlan-ue-local-ip, access-type
  - 数据表：DTS_014031（OWLS 数据仓库）
  - 产生场景：MSC 收到 UE 的 CS Location Update → 通过 HI2 X2 IRI 上报
- **IMS PANI** = SIP P-Access-Network-Info（SIP 协议）
  - 字段：**Access Type, sbc-domain, ue-ip, Wlan-ue-local-ip**
  - **不含：** LAI, Cell ID（但可能有 ECGI）
  - 数据来源：P-CSCF 转发 SIP 消息时附加的接入网络信息
  - 产生场景：UE 通过 WLAN 注册到 IMS → P-CSCF 在 SIP 消息中插入 PANI

**结论：两者属于完全不同的协议栈（CS MAP vs IMS SIP），数据源不可互换。**

### 6. T23 版本对比分析

T23 版本修复（`flink-tmc-1.0.0`，**仍在开发中，尚未发布上线**）：
- 功能名：**"事件无位置信息时导致位置回填失败事件5丢失"**
- 图中：OWLS Flink 处理日志含 `UMTS EVENT=5, SOURCENO=DTS_014031`
- 逻辑：当 CS 域事件无 LAI/Cell ID 时，从 DTS_014031（Event 5 表）查询回填位置

**T23 不涉及 VoWiFi WLAN IP：**
- T23 涉及的域：CS (Circuit Switched)，通过 MSC/VLR 获取 Event 5
- T23 回填的数据类型：LAI (MCC/MNC/LAC) 和 Cell ID
- T23 不处理的数据：PANI、WLAN IP、IMS 接入信息
- T23 不涉及的场景：VoWiFi IMS 接入（UE 通过 WLAN 注册到 IMS 域）

**关键理解：T23 是独立于 VoWiFi WLAN IP 问题的 CS 域并行修复。VoWiFi 问题需要单独的修复路径，详见下文。**

### 7. 根因定位（V2.2 最终结论）

**根因：** ZTLIG2 的 HI2 X2 IRI 解码器未实现 P-Access-Network-Info 头部的 WLAN 扩展参数解析。

数据链路断裂分析：

| 层级 | 环节 | 状态 |
|:----|:-----|:-----|
| ① | 原始数据（PCAP 帧 7345）含 PANI/WLAN IP | ✅ 存在，P-CSCF 正确传递 |
| ② | ZTLIG2 解码 HI2 X2 IRI → LigCdr JSON | **✗ 断裂：ZTLIG2 未解析 PANI** |
| ③ | GP 库存储 LigCdr 字段 | ✗ 因上层无数据，GP 表中无 WLAN IP |
| ④ | OWLS UI 呈现 | ✗ 因底层缺数据，UI 不显示 VoWiFi 位置 |

解码流程中各环节状态：

| 解码环节 | 当前状态 |
|:---------|:---------|
| HI2 X2 帧接收 (TCP:8892) | 正常。ZTLIG2 正确接收 P-CSCF 发送的 SIP 消息 |
| BER TLV 解码 (X2 负载) | 正常。协议头（TAG 80~A3 等）正确解码为结构化字段 |
| SIP 消息体提取 | 正常。SIP Method/URI/Header 层提取 |
| **P-Access-Network-Info 头部解析** | **✗ 缺失。未实现 PANI WLAN 扩展参数解码** |
| Wlan-ue-local-ip → LigCdr JSON | ✗ 缺失。因上一步缺失，无数据写入 LigCdr |

## 关键教训

1. **PCAP 直接分析不可替代** — OWLS 不显示的字段，原始 HI2 数据可能包含
2. **知识库是协议分界的权威依据** — Event 5 (CS MAP) 和 PANI (IMS SIP) 属于不同协议栈
3. **版本升级需交叉验证** — T23 fix 的逻辑在 CS 域正确，但完全不适用于 IMS/VoWiFi
4. **BER 结构需要层次解码** — 不进行 TCP 重组+BER 递归解析会丢失深层字段（Tag 0x89 内的 SIP 头域）
5. **分布式系统问题排查需沿数据链路从底向上** — 数据在 PCAP 中存在 → ZTLIG2 解码 → GP 存储 → UI 呈现，逐层排查断裂点
6. **修复路径必须自底向上** — 先解 ZTLIG2 解码层，再扩展 GP 库，最后 UI 呈现；不可跳过中间层

## 推荐修复路径（三层架构，顺序不可颠倒）

### 第一层：ZTLIG2 解码层（底层，必须先做）

1. 在 ZTLIG2 的 HI2 X2 IRI 解码器中增加 PANI 头部解析模块
2. 解析 P-Access-Network-Info 中的 access-type 字段，识别 IEEE-802.11 (WLAN) 接入类型
3. 提取 Wlan-ue-local-ip (UE WLAN 本地 IP 地址) 和 Wlan-ue-local-port
4. 提取 i-wlan-node-id 或 utran-cell-id-3gpp 作为辅助位置信息
5. 将上述字段写入 LigCdr JSON 输出，增加 `wlan_ue_local_ip`、`wlan_ue_local_port`、`wlan_access_type` 等键

### 第二层：GP 库字段扩展层

1. 在 GP (Greenplum) 数据库 LigCdr 表中增加 WLAN 接入信息字段
2. 新增字段：`wlan_ue_local_ip` (VARCHAR 或 INET 类型)
3. 新增字段：`wlan_ue_local_port` (INTEGER 类型)
4. 新增字段：`wlan_access_type` (VARCHAR，如 "IEEE-802.11")
5. 可选：`i_wlan_node_id` (VARCHAR) 存储 WLAN 节点标识
6. 确保新增字段索引策略与现有查询模式兼容

### 第三层：OWLS UI 呈现层

1. 在 OWLS 事件详情页增加 "VoWiFi 接入信息" 区域
2. 当 `wlan_ue_local_ip` 非空时，展示 WLAN IP 和端口
3. 在位置信息区域增加 WLAN 接入类型标识（区分 3G/4G/WLAN）
4. 更新 Flink TMC 的 VoWiFi 事件处理逻辑，优先使用 PANI 字段
5. flink-tmc 在处理 VoWiFi 事件时，不应仅依赖 Event 5 回填

**实施顺序至关重要：ZTLIG2 → GP → UI。T23 作为独立项目并行推进，不应与 VoWiFi 修复耦合。**

## 引用

- 报告 V1.0: `A1_VoWiFi_WLAN_IP_Analysis_Report_V1.0.docx`（198KB，首轮分析）
- 报告 V2.1: `A1_VoWiFi_WLAN_IP_Analysis_Report_V2.1.docx`（43KB，HI2 重分析验证）
- 报告 V2.2: `A1_VoWiFi_WLAN_IP_Analysis_Report_V2.2.docx`（45KB，**最终版**，用户验证确认）
- 知识库: `VoWiFi_UMTS_Event5_PANI_Knowledge.md`
- 版本说明: `LISTENER V1.1.02_TMC_T23版本发放说明.md` — T23 仍在开发中
- 分析日期: 2026-06-30
- 工作目录: `/home/andymao/PCAP/20260630-A1-VOWIFI/`

## 端口识别速查（VoWiFi 特别相关）

| 端口 | 厂商 | 接口 | 说明（VoWiFi 相关） |
|:----|:-----|:-----|:-----|
| 8890 | 华为/中兴 | X2 (IMS/EPC) | 最常见的 HI2 IRI 端口 |
| **8892** | **华为** | **X2 (IMS)** | **P-CSCF → ZTLIG2 方向，VoWiFi SIP 信令** |
| 9904 | 华为 | X2 (CS) | CS 域 IRI |
| 9905 | 华为 | X2 (CS) | CS 域 IRI |
