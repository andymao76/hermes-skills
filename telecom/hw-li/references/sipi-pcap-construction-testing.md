# SIP-I PCAP 构造与解码测试方法论

## 概述

SIP-I (SIP with Encapsulated ISUP, ITU-T Q.1912.5) 是 VoIP 网络中 ISUP 信令通过 SIP 承载的协议。ISUP 消息（IAM, ACM, ANM, REL, RLC 等）封装在 SIP body 的 multipart/mixed 中，MIME type 为 `application/isup; version=itu-t94+`。

本参考文档描述使用 **scapy**（无需 tshark/pyshark）构造 SIP-I PCAP 测试数据并进行解码验证的完整工作流。

## 适用场景

- 为 LI 系统开发 SIP-I 解码模块时编写单元测试
- 验证 ZTLIG SSF 的 SIP-I 会话管理行为
- 复现生产环境中的 SIP-I 解码问题
- 无需 tshark 安装权限的 PCAP 测试环境

## 架构

SIP-I 消息结构：
```
SIP 消息体 (multipart/mixed)
  ├── MIME part 1: application/sdp (SDP 媒体协商)
  └── MIME part 2: application/isup (ISUP 二进制负载, base64 编码)
                        │
                        ▼
               ISUP IAM 二进制结构 (Q.763)
  ├── 路由标签 (4 bytes): DPC(2) + OPC(2)  → 网络指示语(1)
  ├── CIC (2 bytes): 电路识别码
  ├── 消息类型 (1 byte): IAM=0x01, ACM=0x06, ANM=0x09, REL=0x0C, RLC=0x10
  ├── 必选固定参数 (可变):
  │   ├── Nature of Connection Indicators (1 byte)
  │   └── Forward Call Indicators (2 bytes)
  ├── 必选可变参数:
  │   ├── Called Party Number (TLV: Tag=0x04)
  │   └── Calling Party Number (TLV: Tag=0x0A)
  └── 可选参数 (TLV 序列)
```

## 关键实现细节

### 1. ISUP IAM 二进制构造

IAM 消息二进制布局（参考 Q.763/Q.764）：

```
偏移  字节数  字段
0-3     4     路由标签 (DPC OPC SLS)
4-5     2     CIC
6       1     消息类型 (0x01 = IAM)
7       1     Nature of Connection Indicators
8-9     2     Forward Call Indicators
10+     TLV   Called Party Number (Tag=0x04, Len, DataBCD)
...     TLV   Calling Party Number (Tag=0x0A, Len, DataBCD)
```

**Called Party Number 编码规则 (Q.763 §3.10)**：
- Tag: 0x04 (必选可变参数)
- Length: 1 byte (不含 Tag 和 Length)
- Byte 0: Nature of Address Indicator (0x80=国内, 0x40=国际)
- 后续字节: BCD 编码（反序 nibble），奇数位补 F
- 例: `8613800138000` → BCD 字节: `86 13 80 01 38 00 0F`

### 2. MIME Multipart 解析要点

边界检测关键区分：
- `--boundary001`（开始）→ `startswith("--")` AND NOT `endswith("--")`
- `--boundary001--`（结束）→ `startswith("--")` AND `endswith("--")`

base64 body 收集：只有 MIME header 后的空行之后的文本才是 base64 内容，
Content-Disposition 等 headers 不能混入缓冲区。

### 3. 验证管道

```
构造 ISUP IAM 二进制 (build_isup_iam_binary)
    ↓
构造 SIP 消息文本 (build_sipi_packet)
    ↓
scapy wrpcap → PCAP 文件
    ↓
scapy rdpcap → Raw.load → SIP 文本
    ↓
解析 multipart body → base64 decode → ISUP 二进制
    ↓
逐字段解码 (decode_isup_iam)
    ↓
pytest 断言验证
```

## 常见陷阱

| 陷阱 | 症状 | 修复 |
|------|------|------|
| 边界行检测错误 | ISUP data = None | `--boundary001--` 检测需 `startswith("--") AND endswith("--")` |
| MIME headers 混入 base64 | base64 decode 失败 | 跳过 `Content-Disposition` 行，等空行后再收集 |
| CIC 字节序错误 | CIC 值不匹配 | 使用 `struct.pack(">H", cic)` 大端序 |
| Content-Length 不精确 | 不影响 scapy 解析 | scapy 仅将 SIP 文本作为 Raw load，不校验 Content-Length |

## 参考

- 完整测试模板：`templates/test_sipi_decode.py`
- Q.763 (ITU-T ISUP 格式规范)
- Q.764 (ITU-T ISUP 信令流程)
- RFC 3372 (SIP-T 框架)
- 华为 SIP-I LI 数据分析：`references/pcap-li-analysis.md`
