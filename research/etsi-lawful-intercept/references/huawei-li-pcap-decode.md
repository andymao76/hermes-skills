# 华为 LI X 接口 PCAP 报文解码指南

> 基于 `/home/andymao/LI/ETSI/HW/port6666-hw.pcap` 和 `port8888-hw.pcap` 的反向工程分析
> 参考知识库：`~/knowledge/research/华为LI标准协议翻译.md`

## 知识库中的华为 LI 文档索引

| 文档 | 路径 |
|------|------|
| 华为 5GC/CS LI 协议标准（中文翻译） | `~/knowledge/research/华为LI标准协议翻译.md` |
| 华为 5GC LI 协议标准（详细） | `~/knowledge/research/华为LI标准协议翻译/华为5GC_LI协议标准.md` |
| 华为 CS LI 协议标准（详细） | `~/knowledge/research/华为LI标准协议翻译/华为CS_LI协议标准.md` |
| 华为 5GC X2 Tag 映射表（725项） | `~/knowledge/research/华为LI标准协议翻译/华为5GC_X2_Tag映射表.md` |
| ASN.1 源代码（8个） | `~/knowledge/research/华为LI标准协议翻译/asn/` |
| 中兴 LIG Target 字段定义 | `~/knowledge/research/ZTLIG_Target字段详解.md` |
| ETSI 标准总览 | `~/knowledge/research/ETSI_3GPP_Lawful_Intercept_Standards.md` |
| AGCF/IMS 彩铃笔记 | `~/knowledge/research/AGCF_IMS_CAT_Notes.md` |

## 报文结构概览

华为 LI X 接口报文使用 **LIRP 封装头** + **ASN.1 BER IE 列表** 的两层结构。

### LIRP 封装头（14 字节）

```
字节 0:   0xAA        同步字节（固定）
字节 1:   0x05        版本号（当前版本 5）
字节 2-3: 消息类型（大端序）
          0x0100 = IRI 报告
          0x00C0 = CC 数据
字节 4-5: 明文载荷长度（大端序）
字节 6-7: 密文载荷长度（大端序，等于明文=未加密）
字节 8:   LEAID     监听管理中心编号
字节 9-13: 保留字段（5字节，全 FF）
```

**注意**：CS 版（旧版）X1 使用固定 14 字节帧头+命令码，5GC 版使用 ASN.1 BER。但 X2 口无论在 CS 还是 5GC 场景都使用 LIRP 封装 + BER。

### BER IE 列表结构（从偏移 14 开始）

基于 `hw_5gc_x2.asn` 的 IRI-Parameters 定义：

```
IRI-Parameters ::= SEQUENCE {
    sessionID          [1] OCTET STRING (SIZE(4)) OPTIONAL,
    timeStamp          [2] TimeStamp,
    iRIEvent           [3] IRIEvent,
    partyInformation   [4] SET SIZE (1..10) OF PartyInformation OPTIONAL,
    initiator          [5] Initiator OPTIONAL,
    correlationNumber  [6] OCTET STRING (SIZE(1..20)) OPTIONAL,
    networkIdentifier  [7] Network-Identifier OPTIONAL,
    gPRS-specific      [8] GPRS-SpecificParameters OPTIONAL,
    ePS-GTPV2-specific [9] EPS-GTPV2-SpecificParameters OPTIONAL,
    ePS-PMIP-specific  [10] EPS-PMIP-SpecificParameters OPTIONAL,
    ePS-DSMIP-specific [11] EPS-DSMIP-SpecificParameters OPTIONAL,
    ePS-MIP-specific   [12] EPS-MIP-SpecificParameters OPTIONAL,
    fifthGS-specific   [13] FifthGS-SpecificParameters OPTIONAL
}
```

## X1 接口（port6666-hw.pcap）

### 特征
- TCP 短会话，约每分钟一次（链路保活）
- 源：LIG/ADMF (10.40.35.8:6666) → 目标 NE (129.0.31.102)
- 每个会话：NE 先发 48 字节 Echo 应答，ADMF 回 44 字节 Echo 请求

### 典型交互流程
```
1. Client → Server: SYN
2. Server → Client: SYN-ACK
3. Server → Client: PSH (48字节 — Echo Response，含 NEID + ztlig 认证)
4. Client → Server: ACK
5. Client → Server: PSH (44字节 — Echo Request)
6. Client → Server: FIN
7. Server → Client: FIN-ACK
```

### 可识别字段
- NEID 标识（ASCII 格式的识别字符串）
- "ztlig" 字符串（认证标识）
- Echo 请求/响应的序列号

## X2 接口（port8888-hw.pcap）

### 特征
- 大量 IRI 上报流量（11662 包）
- 目标：DF2 服务器 (10.204.115.5:8888)
- 源：多个 NE（10.251.173.x, 10.203.x.x, 10.202.x.x 等网段）
- 未加密传输（明文长度 = 密文长度）
- LEAID 通常为 4

### 消息结构详解

```
[LIRP 封装头 14 字节]
  AA 05 01 00 LL HH LL HH 04 FF FF FF FF
  ↑  ↑  ↑     ↑     ↑     ↑
  sync ver msg  plain cipher LEAID

[ASN.1 BER IE 列表]
  Context[0xA3/0xA4/0xA2] — 根 Sequence
    ├── OID (0x06) — hi2DomainID (04 00 02 02 01 06)
    ├── IRI Event (0x97) — 事件类型标识
    ├── PartyInformation
    │   ├── MSISDN (0x81 + 5 字节 ASCII 号码)
    │   ├── IMSI/ID (0x80 + 8 字节 ASCII 标识)
    │   └── 其他标识
    ├── TimeStamp
    │   └── GeneralizedTime (0x80 + 0x0E = "YYYYMMDDHHMMSS")
    ├── CorrelationNumber
    │   └── Charging ID (4 字节) + IP 地址
    └── 位置信息
        ├── AMF/gNB 区域码
        └── 小区标识
```

### 关键字段 Tag 映射

**用户标识（Context-specific class, tag 0xAB~0xAE）：**

| Tag | 字段 | 说明 |
|-----|------|------|
| 0xAA | SUPI | 5G 用户永久标识 |
| 0xAB | SUCI | 5G 用户隐藏标识 |
| 0xAC | PEI | 5G 永久设备标识 |
| 0xAD | GPSI | 5G 用户公共标识 |
| 0xAE | 5G-GUTI | 5G 临时用户标识 |

**IRI 事件中的常用 Tag：**

| Tag | 语义 | 说明 |
|-----|------|------|
| 0x97 | IRI Event Type | 事件类型码（如 Start of Interception） |
| 0x81 | MSISDN (5字节) | 移动用户号码（ASCII） |
| 0x80 | IMSI/ID (8字节) | 用户身份标识（ASCII） |
| 0xA2 | TimeStamp | 时间戳容器 |
| 0xA3 | iRIEvent | 事件详情容器 |
| 0xA4 | partyInformation | 参与方信息容器 |
| 0xA6 | correlationNumber | X2/X3 关联编号 |
| 0x80+0x0E | GeneralizedTime | 格式 "YYYYMMDDHHMMSS" |
| 0x83+8 | AMF/gNB 标识 | 控制面节点标识 |
| 0x86+7 | 位置信息 | 路由区/位置区 |

## 报文解码 Python 脚本模板

```python
import struct

def parse_lirp_header(data):
    """解析华为 LIRP 封装头（14字节）"""
    assert data[0] == 0xAA, "Not a Huawei LIRP packet"
    return {
        'sync': data[0],
        'version': data[1],
        'msg_type': data[2]<<8|data[3],
        'plain_len': data[4]<<8|data[5],
        'cipher_len': data[6]<<8|data[7],
        'leaid': data[8],
        'reserved': data[9:14].hex(),
    }

def extract_ber_fields(payload, offset=14):
    """从 BER payload 中提取关键字段"""
    data = payload[offset:]
    results = {}
    for i in range(len(data)):
        # GeneralizedTime: tag 0x80 + len 0x0E (14 chars)
        if data[i] == 0x80 and data[i+1] == 0x0E:
            results['timestamp'] = data[i+2:i+16].decode('ascii')
        # MSISDN: tag 0x81 + len 5
        if data[i] == 0x81 and data[i+1] == 5:
            results['msisdn'] = data[i+2:i+7].decode('ascii')
        # IMSI/ID: tag 0x80 + len 8
        if data[i] == 0x80 and data[i+1] == 8:
            results['imsi'] = data[i+2:i+10].decode('ascii')
    return results

# 使用 tcpdump 提取 payload
# tcpdump -r file.pcap -X | grep -A999 'length N$' | xxd -r -p > payload.bin
```

## 注意事项

1. **偏移确认**：LIRP 头 14 字节后才是 BER 内容。误将保留字段（9-13）当成 BER Tag 会导致解码完全错位
2. **加密判断**：对比明文长度和密文长度字段，相等则未加密
3. **TNEType 判断**：5GC 六种类型——UNC(AMF/SMF/MME/SGSN)、UDG(UPF)、UDM/HSS、USN(MME/SGSN)、UGW(S-GW/P-GW)
4. **X3 关联**：X2 中的 correlationNumber 对应 Charging ID，用于与 X3 口 CC 数据做关联
5. **CS vs 5GC 差异**：CS 版 X1 有 0xAA 同步字节+命令码结构，5GC 版用 LIRP 封装+BER
6. **ASN.1 解码工具**：可安装 dumpasn1 (`apt install dumpasn1`) 或使用 pyasn1 进行精确解码
