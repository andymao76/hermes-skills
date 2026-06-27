# 华为 X1/X2/X3 帧头字节布局参考

## NE 类型映射

第3字节（X2/X3 14字节头中的 byte 2）标识网元类型：

| 值 | NE 类型 | 说明 |
|----|--------|------|
| 1 | MSC | 移动交换中心 |
| 2 | HLR | 归属位置寄存器 |
| 3 | VLR | 拜访位置寄存器 |
| 4 | GMSC | 关口 MSC |
| 5 | SGSN | 服务 GPRS 支持节点 |
| 6 | GGSN | 网关 GPRS 支持节点 |
| 7 | MSC-S | MSC 服务器 |
| 8 | MGW | 媒体网关 |
| 9 | SBC | 会话边界控制器 |
| 10 | P-CSCF | 代理 CSCF |
| 11 | I-CSCF | 查询 CSCF |
| 12 | S-CSCF | 服务 CSCF |
| 13 | AS | 应用服务器 |
| 14 | MRF | 媒体资源功能 |
| 15 | HSS | 归属用户服务器 |
| 16 | E-CSCF | 紧急 CSCF |
| 17 | BGCF | 出口网关控制功能 |
| 18 | IM-MGW | IP 多媒体 MGW |
| 19 | MME | 移动性管理实体 |
| 20 | S-GW | 服务网关 |
| 21 | P-GW | PDN 网关 |
| 22 | eNodeB | 基站 |
| 23 | AMF | 接入与移动性管理功能 (5GC) |
| 24 | SMF | 会话管理功能 (5GC) |
| 25 | UPF | 用户面功能 (5GC) |
| 111 | IMS | IP 多媒体子系统 (通用) |

## X2 14 字节帧头布局

```
Byte  [0]  [1]  [2]  [3]  [4]  [5]  [6]  [7]  [8]  [9]  [10] [11] [12] [13]
Hex   AA   V    NE   ---------预留--------- LEAID ---------预留---------
      0xAA 01   09   00   00   00   00   08   03   00   00   00   00   00
      ↑         ↑                             ↑
      固定前导    NE=SBC(9)                    LEA=3
```

- [0]: 固定前导码 0xAA
- [1]: 版本/标志
- [2]: NE 类型 (见上表)
- [3-7]: 预留 (5 bytes)
- [8]: LEAID (执法机构 ID)
- [9-13]: 预留 (5 bytes)

BER 编码载荷从偏移 14 开始。非 0xAA 开头说明数据可能已是裸 BER 无帧头。

## X1 命令码表

### CS 版 14 字节 (byte 3 = 命令码)

| 码值 | 命令 | 说明 |
|------|------|------|
| 0x10 | X1Handshake | 建链 |
| 0x11 | X1HandshakeAck | 建链应答 |
| 0x20 | X1SetTarget | 设控/NEW |
| 0x21 | X1SetTargetAck | 设控应答 |
| 0x22 | X1SetTargetCancel | 取消设控 |
| 0x23 | X1SetTargetCancelAck | 取消设控应答 |
| 0x30 | X1ModifyTarget | 修改设控 |
| 0x31 | X1ModifyTargetAck | 修改设控应答 |
| 0x40 | X1QueryTarget | 查询设控 |
| 0x41 | X1QueryTargetAck | 查询设控应答 |
| 0x50 | X1HeartBeat | 心跳 |
| 0x51 | X1HeartBeatAck | 心跳应答 |
| 0xF0 | X1Disconnect | 断开 |

### NGN 老版 8 字节 (byte 1 = 命令码)

| 码值 | 命令 | 说明 |
|------|------|------|
| 0x00 | C-Reset | 复位 |
| 0x01 | C-ResetAck | 复位应答 |
| 0x10 | C-SetTarget | 设控 |
| 0x11 | C-SetTargetAck | 设控应答 |
| 0x20 | C-ReleaseTarget | 释放目标 |
| 0x21 | C-ReleaseTargetAck | 释放应答 |
| 0x30 | C-Query | 查询 |
| 0x31 | C-QueryAck | 查询应答 |
| 0x40 | C-HeartBeat | 心跳 |
| 0x41 | C-HeartBeatAck | 心跳应答 |

## X3 14 字节帧头

结构同 X2 14 字节头，但 [3-7] 字段用途不同：
- X2: 预留
- X3: 可能携带 Correlation ID（用于 X2-X3 关联，基于 Charging ID）

## 华为帧头检测逻辑

```python
if len(data) >= 14 and data[0] == 0xAA:
    # 14 字节头
    ne_type = data[2]       # → NE_TYPE_MAP
    leaid = data[8]         # LEA ID
    payload = data[14:]     # BER 编码
elif len(data) >= 8 and data[0] == 0xAA:
    # 8 字节 NGN 老版头
    cmd = data[1]           # → X1_CMD_8B_MAP
    ne_type = data[2]
    payload = data[8:]
else:
    # 可能是裸 BER/PER 数据
    payload = data
```
