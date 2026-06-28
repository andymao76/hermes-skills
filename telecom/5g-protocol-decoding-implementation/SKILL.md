---
name: 5g-protocol-decoding-implementation
title: 5G 协议解码实现
description: 实现 5G 信令监测系统的协议解码器 —— NGAP PER (pycrate ASN.1)、SBI HTTP/2 (HPACK)、NAS 5GMM/5GSM。覆盖 pycrate 集成、NGAP IE 映射、会话关联、HTTP/2 帧解析。
tags: [5g, ngap, sbi, http2, hpack, asn1, per, pycrate, stcms]
---

# 5G 协议解码实现

## 概述

5G 信令监测系统的核心协议栈：

```
N2 (SCTP/NGAP) ─→ NGAP PER 解码 ─→ 提取 NAS-PDU → NAS 5GMM/5GSM 解码
                                        ↓
N8/N10/... (TCP/HTTP/2) ─→ SBI HTTP/2 解码 → JSON body 解析
                                        ↓
N26 (UDP/GTPv2-C) ─→ GTPv2-C 解码
```

## Scapy NGAP PCAP 快速扫描（PG 级分析）

在投入 full pycrate 解码前，先用 scapy 对 PCAP 做快速扫描。这个工作流回答：
- 包里有什么协议？（SCTP vs UDP vs TCP）
- 谁是 AMF？有多少 gNB？（IP 对频率）
- NGAP 消息 PDU 类型分布？ProcedureCode 分布？
- 是否有异常模式？

**关键观察项（来自 Tunisie Telecom 现网实测）**：
- InitialContextSetupResponse 占 >60% = 大量 UE 注册潮
- HandoverPreparation + HandoverSuccess 合占 ~20% = 用户高速移动场景
- CellTrafficTrace 频繁 = 网络优化监测开启
- NGSetup 出现 97 次 = 多家 gNB 频繁重建（或 AMF 侧重置）

完整脚本见 `references/scapy-ngap-pcap-profiling.md`。

## SCTP 包解析（NGAP 传输层）

NGAP 消息通过 SCTP 传输（PPID=60 或 1024）。从 PCAP 提取 NGAP 数据时需要正确解析 SCTP 块结构。

### SCTP chunk 结构

```
SCTP Common Header (12B) → 跳过
DATA chunk:
  bytes 0-3:  Type(1) | Flags(1) | Length(2)
  bytes 4-7:  TSN
  bytes 8-11: Stream ID(2) | Stream Seq(2)
  bytes 12-15: PPID ← 偏移 12，不是 20！
  bytes 16+:   Payload ← 偏移 16，不是 28！
```

### 关键陷阱

- **PPID 和 payload 偏移**: 新手常误以为 DATA chunk header 有 28 字节（实际只有 16 字节）
- **非 DATA chunk 必须过滤**: SACK(0x03)、HEARTBEAT(0x04) 等控制块占 PCAP 中 SCTP 包的多数
- **错误后果**: 把 SACK 数据当 NGAP 喂给 pycrate → PDU 头解码"成功"但 IEs=0

### 正确做法

```python
off = 12  # 跳过 common header
while off + 8 <= len(sctp_bytes):
    ctype = sctp_bytes[off]
    clen = int.from_bytes(sctp_bytes[off+2:off+4], 'big')
    if clen < 4: break
    if ctype == 0x00:  # 仅 DATA chunk
        ppid = int.from_bytes(sctp_bytes[off+12:off+16], 'big')
        payload = sctp_bytes[off+16:off+clen]
    off += clen  # 非 DATA 同样前进
```

详见 [sctp-chunk-parsing.md](references/sctp-chunk-parsing.md)。

### pycrate ASN.1 模块位置
- 预编译模块: `~/.local/lib/python3.12/site-packages/pycrate_asn1dir/NGAP.py` (52,797 行)
- 运行时: `pycrate_asn1rt` (已随 pycrate 安装)

### 初始化步骤
```python
import NGAP as ngap_mod
from pycrate_asn1rt.init import init_modules

init_modules(
    ngap_mod.NGAP_CommonDataTypes,
    ngap_mod.NGAP_Constants,
    ngap_mod.NGAP_Containers,
    ngap_mod.NGAP_IEs,
    ngap_mod.NGAP_PDU_Contents,
    ngap_mod.NGAP_PDU_Descriptions,
)

NGAP_PDU = ngap_mod.NGAP_PDU_Descriptions.NGAP_PDU
```

### 解码 API
```python
NGAP_PDU.from_aper(ngap_data)
pdu_type, fields = NGAP_PDU._val  # (str, dict)
# pdu_type: 'initiatingMessage' | 'successfulOutcome' | 'unsuccessfulOutcome'
# fields: {'procedureCode': int, 'criticality': str,
#          'value': (procedure_name, {'protocolIEs': [...]})}
```

### 关键映射表
- **过程码 0-80**: `references/pycrate-ngap-per-decoding.md` 中完整列出
- **IE ID 0-443**: 同上
- **重要 IE**: id=10 (AMF-UE-NGAP-ID), id=85 (RAN-UE-NGAP-ID), id=38 (NAS-PDU)

### 注意事项
- `from_aper()` 返回 `None`，解码结果存在 `._val` 中
- 每次解码前不需要 clone，直接调用即可
- 解码失败时抛出异常，需捕获
- 建议先用 `decode_ngap_pdu_header()` 快速扫描（只解过程码和 PDU 类型）

## SBI HTTP/2 解析

### 协议栈
```
TCP → HTTP/2 Frame → HEADERS (HPACK) → :method, :path, :authority
                    → DATA → JSON body
```

### 组件
1. **`Http2FrameParser`** — 将 TCP 数据解析为 HTTP/2 帧
   - 支持连接前导码 ("PRI * HTTP/2.0...") 检测
   - 帧类型: HEADERS(1), DATA(0), SETTINGS(4), CONTINUATION(9), GOAWAY(7)

2. **`Http2StreamAssembler`** — 流重组 + HPACK 解码
   - 依赖 `hpack` 库 (pip install hpack)
   - HEADERS + CONTINUATION 帧重组
   - HPACK 头部解压缩

3. **`SbiHttp2Parser`** — 统一解析器，输出结构化 SBI 消息

### HPACK 动态表限制
- 单包 PCAP 缺少完整 TCP 流上下文时，HPACK 动态表引用（index > 61）会失败
- **回退方案**: 从 DATA 帧的 JSON body 推断服务类型
  - `deregCallbackUri` + `amfInstanceId` → Nudm_UECM (N8)
  - `pduSessionId` + `sNssai` → Nsmf_PDUSession (N11)
  - `authType` + `5G_AKA` → Nausf_UEAuthentication (N12)
  - 详见 `_identify_from_body()` 方法
- 生产环境需要完整 TCP 流重组

### SUPI 提取
- URI 路径: `/(\d{5,15})(?:/|$)`
- Body 回退: `imsi[-]?(\d{5,15})`

## NAS 安全上下文管理

NAS 安全上下文跟踪 Security Mode Command（SMC, 0x5E）→ Security Mode Complete（SMCpl, 0x5F）流程。

### 安全上下文结构

```python
class NasSecurityContext:
    ngksi: int                     # NAS key set identifier
    selected_enc_alg: int          # 加密算法 (0=null, 1=SNOW, 2=AES, 3=ZUC)
    selected_int_alg: int          # 完整性算法
    k_amf: bytes | None            # 根密钥（从外部注入）
    k_nas_enc: bytes | None        # K_NASenc = KDF(K_AMF, 0x69, 0x01, alg_id)
    k_nas_int: bytes | None        # K_NASint = KDF(K_AMF, 0x68, 0x02, alg_id)
    keys_available: bool
    ul_count: int / dl_count: int  # NAS COUNT（32-bit 每方向）
    activated: bool                # SMCpl 接收后置 True
```

### Security Mode Command IE 解析

| IEI | 标准含义 | 格式 |
|-----|----------|------|
| 0x10 | NAS key set identifier | TV: ngKSI(3b) |
| 0x36 | Selected NAS security algorithms | TLV: enc_alg(4b) + int_alg(4b) |
| 0x1E | UE security capability | TLV: 算法支持位图 |
| 0x52 | ABBA | TLV: 认证参数 |

**非标准数据集注意**: 某些 PCAP 数据集使用 IEI 0x77 代替标准 0x10+0x36，格式为 TLV，value[0] 的 bit 7-4=enc_alg, bit 3-0=int_alg。

### 解密尝试

```python
if ctx.keys_available and ctx.activated:
    count = ctx.get_count(direction)
    if ctx.selected_enc_alg == 2:  # AES
        from decoder.nea2 import Nea2
        plaintext = Nea2.decrypt(k_nas_enc, count, bearer=1, direction, data)
```

### COUNT 管理

- UL/DL 各 32-bit，每加密/解密一条消息递增
- 从 SMCpl 确认激活后从 0 开始（实际应从 stored NAS COUNT 恢复）
- 方向: 0=UL, 1=DL

### NAS 5GMM 消息结构
```
Byte 0: EPD(4) + SHT(4)
Byte 1: Message Type
Byte 2+: Information Elements (TLV/TV/LVE)
```

### IE 解析格式
- **TV**: IEI(1) + Value(固定), 如 ngKSI(0x10), 5GS Registration Type(0x15)
- **TLV**: IEI(1) + Length(1) + Value, 如 Mobile Identity(0x18), UE Security Capability(0x1E)
- **LVE**: IEI(1) + Length(2) + Value

### ⚠️ NAS 消息类型偏移（测试设备差异）
标准 TS 24.501 格式：消息类型在 `data[1]`。但某些测试设备（如本项目 PCAP 数据集）使用**非标准偏移**，详见 [nas-offset-debug.md](references/nas-offset-debug.md)。
```
Byte 0: EPD(4) + SHT(4)     — 0x7E=5GMM（SHT 可能为 0x0E 而非标准 0x00-0x03）
Byte 1: 封装标识             — 0x00=裸, 0x02=安全封装
Byte 2: 消息类型             — 如 0x41=REGISTRATION_REQUEST（非标准偏移）
Byte 3+: Information Elements
```
**安全封装(byte[1]=0x02 或 0x04)**：内层 NAS 从 byte[7] 开始，同样 byte[7+2]=消息类型。
- byte[1]=0x02: wrapped（完整保护）
- byte[1]=0x04: ciphered（加密）
- 两种格式统一处理：`if data[1] in (0x02, 0x04) and data[7]==0x7E: inner = data[7:]`

**处理策略**：解码器先用 byte[1] 检测封装类型，再取 byte[2] 作为消息类型。内层用 `_decode_plain_nas()` 递归解析。

### 5GS Mobile Identity 解析
```
Byte 0: type_of_id(3) | odd_even(1) | spare(4)
  type=0: SUCI, type=1: 5G-GUTI, type=2: IMEI,
  type=3: 5G-S-TMSI, type=4: IMSI
```

### 5GSM IE 结构（PDU Session）

5GSM 消息（PD=0x2E）用于 PDU Session Establishment/Modification/Release。关键 IE：

| IEI | 名称 | 格式 | 解码 |
|-----|------|------|------|
| 0x22 | PDU session type | TV | IPv4/IPv6/IPv4v6/Ethernet/Unstructured |
| 0x25 | S-NSSAI | TLV | SST(1) + SD(3,opt) + Mapped SST+SD(opt) |
| 0x27 | QoS rules | TLV-E | 流程级 QoS 规则列表 |
| 0x28 | DNN | LVE | ASCII 字符串（Data Network Name） |
| 0x29 | SSC mode | LVE | SSC mode 1/2/3 |
| 0x2B | QoS flow descriptions | LVE | QFI + Operation + 参数(5QI/GFBR/MFBR) |
| 0x2C | Session-AMBR | LVE | DL/UL 各(Unit(1)+Value(4)) |
| 0x34/0x7B | Protocol config options | LVE/TLV-E | 扩展配置 |
| 0x37 | 5GSM cause | TLV | 原因码 → 文本 |
| 0x59 | Always-on PDU session | TV | bool |
| 0x5A | GPRS timer | TV | Unit(3) + Value(5) |
| 0x5B | Reactivation result | TV | result code |
| 0x5C | Reactivation error cause | TV | error code |
| 0x79 | QoS flow params | TLV-E | 流级 QoS 参数 |

#### DNN/S-NSSAI/AMBR 解码示例

```python
# S-NSSAI (IEI 0x25)
sst = value[0]
sd = value[1:4].hex() if len(value) >= 4 else ""

# DNN (IEI 0x28) — LVE 格式
dnn = value.decode("ascii", errors="replace").rstrip("\x00")

# Session-AMBR (IEI 0x2C)
unit_dl = value[0]; dl_ambr = int.from_bytes(value[1:5], 'big')
# unit: 0=bps, 1=Kbps, 2=Mbps, 3=Gbps

# QoS Flow (IEI 0x2B)
qfi = value[0] & 0x3F
op_code = value[1] & 0x0F  # 0=noop, 1=create, 2=modify, 3=delete
```

**注意**: 某些数据集的 5GSM 消息内嵌在 UL NAS TRANSPORT（0x67）的 Payload Container IE 中。
```

## 会话关联（多接口消息关联）

### 关联策略
从不同接口（N1/N2/N8/N10/N11/N12/N13/N26）的消息关联到同一 UE 会话：

1. **SUPI 关联**（N8/N10/N11/N12/N13）— 最可靠
2. **NGAP ID 关联**（N2）— SUPI 不可用时用作临时会话键
3. **SUCI → SUPI**（N12/N13 鉴权后）— 隐藏身份到永久身份
4. **5G-GUTI 关联** — 临时身份到 SUPI
5. **PDU Session ID** — PDU 会话建立/修改/释放

### NGAP ID 作为临时会话键
当 NAS 加密导致无法提取 SUPI 时，用 NGAP NGAP ID 创建临时会话：
```
TMP-{ran_ue_ngap_id} 或 TMP-{amf_ue_ngap_id}
```
- 使用 `_ngap_id_map` 缓存 NGAP 键→SUPI 的映射
- 后续消息通过 RAN/AMF UE NGAP ID 匹配到同一临时会话
- 真实 SUPI 出现时（如从 SBI 解码中获得），替换临时键

### 陷阱
- **NGAP ID 含前缀**: `_format_ie_value()` 输出 `"RAN-UE-NGAP-ID=0"`，需用 `_extract_pure_id()` 取纯数值 `"0"`
- **NAS 加密**: 初始注册后 NAS 载荷加密，无法从中提取 SUPI/SUCI

| 算法 | 标准 | 实现方式 | 验证 |
|------|------|---------|------|
| NEA1 | TS 35.215 (SNOW 3G) | CryptoMobile | ✅ 对称性验证 |
| NEA2 | AES CTR | pycryptodome | ⚠️ API 兼容性 |
| NEA3 | TS 35.221 (ZUC) | CryptoMobile | ✅ 对称性验证 |
| NIA1-3 | 完整性算法 | 各模块封装 | ✅ 加载正常 |

## 项目结构（以 STCS 为例）

```
STCS/
├── 源码/
│   ├── engine.py              # 主引擎，协调所有解码器
│   ├── core/
│   │   ├── decoder_base.py    # DecodeResult / SbiResult 基类
│   │   ├── session.py         # 会话关联器
│   │   └── config.py
│   ├── protocols/
│   │   ├── ngap.py            # NGAP 解码器（pycrate 集成）
│   │   ├── pycrate_ngap.py    # pycrate NGAP PER 解码器
│   │   ├── http2_parser.py    # HTTP/2 + HPACK 解析
│   │   ├── sbi.py             # SBI HTTP/2 解码器
│   │   ├── nas_5gmm.py        # NAS 5GMM 解码器
│   │   ├── nas_5gsm.py        # NAS 5GSM 解码器
│   │   └── gtpv2c.py          # GTPv2-C 解码器
│   ├── decoder/
│   │   ├── nas_security.py      # NAS 安全上下文管理（SMC→K_NASenc/K_NASint→解密）
│   │   ├── nea1.py            # NEA1 (SNOW 3G)
│   │   ├── nea2.py            # NEA2 (AES CTR)
│   │   ├── nea3.py            # NEA3 (ZUC)
│   │   ├── suci.py            # SUCI 解码
│   │   ├── guti_mapper.py     # 5G-GUTI ↔ GUTI 映射
│   │   └── kdf.py             # 密钥推导
│   └── services/              # SBI 服务层解码器 (N8-N26)
└── 测试/
    └── pcaps/5G单用户/         # 17个测试 PCAP 文件
```

## 陷阱与注意事项

1. **pycrate import 路径**: 需要将 `pycrate_asn1dir` 加入 `sys.path`
2. **HPACK 单包限制**: 测试 PCAP 可能只包含部分 TCP 段，导致动态表不完整
3. **NGAP PER 对齐**: NGAP 使用 Aligned PER (APER)，非 Unaligned PER (UPER)。用 `from_aper()` 不是 `from_uper()`
4. **SCTP 分片**: SCTP DATA chunk 可能分片，需要重组。当前实现假设每个 DATA chunk 包含完整的 NGAP PDU
5. **HTTP/2 连接前导码**: 新连接先发送 24 字节前导码 + SETTINGS 帧。PCAP 可能已跳过
6. **pycrate IE 值含类型前缀**: `_format_ie_value()` 对整型 IE 返回 `"RAN-UE-NGAP-ID=0"` 格式，不能直接作为会话 ID。**必须用独立方法提取纯数值**：
   ```python
   def _extract_pure_id(self, ie_value) -> str:
       if isinstance(ie_value, tuple) and len(ie_value) == 2:
           _, actual = ie_value
           if isinstance(actual, int): return str(actual)
           if isinstance(actual, bytes): return str(int.from_bytes(actual, 'big'))
       return str(ie_value)
   ```
7. **NAS 消息类型偏移不确定**: 某些测试设备将消息类型放在 `data[2]` 而非标准 `data[1]`。解码器应检测 `data[1]` 的值来判断封装类型，再取消息类型
8. **SCTP 非 DATA chunk 过滤**: SACK(0x03)、HEARTBEAT(0x04) 等控制块必须过滤，否则 pycrate 解码会产生 IEs=0 假象。PPID 在 chunk 偏移 12，payload 在偏移 16
9. **encap=0x04 支持**: 某些数据集使用 byte[1]=0x04 而非 0x02 表示加密封装，内层 NAS 同样从 byte[7] 开始
10. **Security Mode Command 非标准 IEI**: 某些数据集使用 IEI 0x77（而非标准 0x10+0x36）编码 ngKSI 和算法选择
11. **5GSM 消息在 UL NAS TRANSPORT 内**: PDU Session 消息可能嵌在 5GMM UL NAS TRANSPORT (0x67) 的 Payload Container IE 中
