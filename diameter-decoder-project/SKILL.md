---
name: diameter-decoder-project
description: 从 AAADimDecoder (Python 2.7/PyQt4 EXE) 重构为 Python 3 Diameter 协议解码器，V2 已整合 jdiameter 1.5.3.1 知识
---

# Diameter Decoder 项目

## 项目位置
`~/projects/Diameter_decoder/` | git (main branch), V2.0.0

## 项目结构（V2.0.0）
```
diameter_decoder/           # 核心库
├── __init__.py            # 包初始化 (__version__ = "2.0.0")
├── __main__.py            # python -m diameter_decoder 入口
├── core.py                # DiameterHeader, AVP, DiameterMessage (+新AVP类型 13-15)
├── dictionary.py          # IANA 修正字典 + CCA/Gy 应用支持
├── decoder.py             # 解码编排器 (hex/binary/stream)
├── cli.py                 # 命令行接口 (5种输入源, 3种输出格式)
└── pcap.py                # PCAP 读取 (SCTP修复, TCP/SCTP/UDP)
tests/
├── test_diameter_decoder.py
└── test_legacy.py
.github/workflows/
└── test.yml
pyproject.toml
setup.py
README.md
LICENSE
```

## 使用方式
```bash
python -m diameter_decoder.cli --hex "0100..."
python -m diameter_decoder.cli --file msg.bin
python -m diameter_decoder.cli --pcap capture.pcap
python -m diameter_decoder.cli --hex "0100..." --json --summary
python -m diameter_decoder.cli --hex "0100..." --dict ~/PCAP/AAADimDecoder/config/cfg.ini
```

## V2.0.0 更新内容（源自 jdiameter 1.5.3.1 SSL 包）

### 1. SCTP PCAP 读取修复
- **问题**: `sctp.chunks` 为空列表，SCTP 分支永远不执行
- **根因**: scapy 中 SCTPChunkData 通过 `.payload` 链式连接，非 `chunks` 集合
- **修复**: 递归遍历 `.payload` 链，从每个 SCTPChunkData 的 `.data` 字段提取 Diameter 载荷
- **验证**: 3-27-test_diameter.pcap(2.2MB)→3,778消息; 1-25-2_diameter.pcap(54MB)→82,948消息

### 2. IANA 标准 AVP 字典修正
修正了源自 AAADimDecoder cfg.ini 的错误 AVP 映射：
- AVP 553-555: `S-VID-Start/S-VID-End/C-VID-Start` → `Subscription-Id/Subscription-Id-Data/Subscription-Id-Type`
- AVP 603-609: 各种 NAT/Duplicate 名 → `Unit-Value/Cost-Information/Requested-Service-Unit/Service-Parameter-Info/Service-Parameter-Type/Service-Parameter-Value`
- AVP 611-617: `Admission-Priority/SIP-Resource-Priority` → `CC-Time/CC-Money/Requested-Action/CC-Unit-Value`

### 3. 新增 AVP 类型（来自 jdiameter API）
- `DiameterURI` (type 13): `aaa://host:port;transport=tcp` 格式
- `IPFilterRule` (type 14): `permit in ip from any to any` 格式 (RFC 6733 §4.3)
- `QoSFilterRule` (type 15): 类似 IPFilterRule 的 QoS 规则 (RFC 6733 §4.3)

### 4. CCA/Gy (RFC 4006) 应用层支持
- `CCA_AVP_ALIASES`: 13 个 Gy 特有 AVP 别名（与 Rx 共享码点的 AVP）
- `CCA_MANDATORY_AVPS`: 8 个 Gy 强制 AVP（263/264/296/415/416/480/483/485）

### 5. JDiameter 知识沉淀
| 组件 | jdiameter 对应 |
|------|----------------|
| jdiameter-api.jar | 接口层 (Avp/AvpSet/Message/Stack/Session) |
| jdiameter-impl.jar | 实现层 (CCA/Cx/Sh 应用, 注解式 AVP 定义) |
| TLSClientConnection.java | SSL over TCP 客户端实现 |
| TLSServerConnection.java | SSL over TCP 服务器实现 |
| XMLConfiguration.java | 配置解析 (含 Security 节点) |
| CCAServer/MultiCCAClient.java | Gy/CCA 计费示例应用 |

## AVP 类型支持 (16种)
OctetString, Unsigned32, Integer32/64, Unsigned64, Float32/64, Address, Time, Grouped, UTF8String, DiameterIdentity, Enumerated, **DiameterURI**, **IPFilterRule**, **QoSFilterRule**

## 字典覆盖
- AVP_DICT: 444 RFC/IANA AVP (修正后)
- VENDOR_AVP_DICT: 130+ 厂商特定 AVP
- APP_ID_DICT: 112 个应用 ID (含 Diameter Credit Control/Gy app_id=4)
- RESULT_CODE_DICT: 32 个结果码
- CCA_AVP_ALIASES: 13 个 Gy 别名
- load_ini_dictionary(): AAADimDecoder cfg.ini 格式
- merge_dictionary(): 合并自定义字典

## PCAP SCTP 注意事项

### scapy SCTP 块遍历陷阱
scapy 的 `SCTP` 层**没有** `chunks` 列表属性。
SCTPChunkData 通过 `.payload` 链式连接：
```
SCTP → SCTPChunkData (chunk1) → SCTPChunkData (chunk2) → NoPayload
```
Diameter 载荷在 SCTPChunkData 的 `.data` 字段。
已修复于 pcap.py（2026-06-25）。

### CMCC Diameter PCAP
路径: `~/PCAP/Diameter/diameter/` (18个文件, 429MB)
- 全部 SCTP 承载 (PPID 0x2e=46, 端口 3868)
- 接口覆盖: S6a/S6d/Cx/Sh/Zh
- 真实中国移动 4G LTE 网元间信令

## 从 AAADimDecoder EXE 重构要点
- 原始 EXE = PyInstaller 2.0 / Python 2.7 / PyQt4
- 核心解码在 `dimpro` 模块 (PYZ 内嵌, Python 2.7 marshal)
- 字典来自 cfg.ini (603行, 1600条目)
- 本重构增强了: CLI、PCAP、JSON、SCTP、SSL/TLS 预备

## jdiameter 配置参考
```xml
<Security>
  <SecurityData name="myse" protocol="TLS"
    use_client_mode="false" enable_session_creation="true"
    need_client_auth="true">
    <KeyData store="JKS" manager="SunX509"
      file="/sslkeystore/kserver.jks" pwd="123123"/>
    <TrustData store="JKS" manager="SunX509"
      file="/sslkeystore/tserver.jks" pwd="123123"/>
  </SecurityData>
</Security>
```
当前 Python 解码器仅解析，不支持 SSL/TLS 传输。若需 SSL 解码需先解密 TLS 流。

## 相关参考

- `references/ocs-gy-filtering.md` — Gy 口 OCS 实时计费 Wireshark 过滤方法（按 MSISDN/IMSI/Session-ID 过滤 CCR/CCA）
- `references/scapy-sctp-chunks.md` — scapy SCTP 块遍历陷阱详解
- `references/3gpp-vendor-avps.md` — 3GPP 厂商特定 AVP 码映射
