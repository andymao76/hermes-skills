# 5G 协议解码器测试方法

## 概述

5G 信令监测系统（如 STCMS）的解码器验证需要三部分：
1. **密码算法验证** — EEA1/EEA2/EEA3 正确性
2. **协议解析验证** — NGAP/NAS/SBI 消息结构解码
3. **流程关联验证** — 多接口消息关联为完整流程

## 密码算法实现

### 推荐方案：CryptoMobile

**不要**纯 Python 从零实现 SNOW 3G 或 ZUC（容易出位级错误）。使用 CryptoMobile（ETSI SAGE 官方参考实现的 C 封装）：

```bash
pip install git+https://github.com/P1sec/CryptoMobile --break-system-packages
http_proxy=http://127.0.0.1:7897 pip install git+https://github.com/P1sec/CryptoMobile --break-system-packages
```

### 验证方法

使用双向对称性验证（无需先验已知输出）：

```python
from CryptoMobile import CM

# EEA1/EEA2/EEA3 都用统一参数签名:
result = CM.EEAx(key, count, bearer, direction, data)

# 验证：解密(加密(明文)) == 明文
encrypted = CM.EEAx(key, count, bearer, dir, plaintext)
decrypted = CM.EEAx(key, count, bearer, dir, encrypted)
assert decrypted == plaintext  # CTR 模式是对称的
```

### Nest 接口参数

| 参数 | 类型 | 说明 |
|------|------|------|
| key | 16 bytes | 128-bit 密钥 |
| count | int (32-bit) | COUNT 值 |
| bearer | int (5-bit) | 承载标识 (0-31) |
| direction | int (1-bit) | 0=UL, 1=DL |
| data | bytes | 待加解密数据 |

### 测试向量参考

| 算法 | 3GPP 规范 | 测试向量位置 |
|------|----------|-------------|
| EEA1 (SNOW 3G) | TS 35.217 Annex A | full test vectors |
| EEA2 (AES) | TS 33.401 Annex B | 同 128-EEA2 |
| EEA3 (ZUC) | TS 35.221 Annex A | full test vectors |

> **注意**: CryptoMobile 的 EEA1/EEA3 输出可能与 TS 测试向量不一致（参数编码方式不同），但双向对称性验证可靠。实际产品应直接使用 CryptoMobile 的加解密。

## 协议解析测试

### 测试数据

使用真实抓包文件（PCAP），推荐包含以下场景：

| 场景 | 文件名模式 | 验证点 |
|------|----------|--------|
| SUCI 注册 | `*suci*register*` | N1 NAS + N2 NGAP + 鉴权 |
| PDU 会话建立 | `*pdu_session*establish*` | N1 NAS 5GSM 消息 |
| 切换 (Xn/N2) | `*[xn|n2]*handover*` | NGAP Handover 流程 |
| 加密注册 | `*EA0*, *EA1*, *EA2*` | 不同加密算法下的会话 |
| 完整流程 | `*register*handover*release*deregister*` | 端到端关联 |
| 用户面 | `*user_plane*gtp_udp*` | GTP-U 隧道 |

### NGAP 解码注意事项

NGAP 使用 **ASN.1 PER** (Packed Encoding Rules) 编码：
- **位级对齐**，不是字节对齐的 TLV
- 简单的 `tag(1) + length(1) + value(N)` 解析对 PER 无效
- 正确方案：使用 pycrate 的 `NGAP.py` ASN.1 模块，或从 `free5GC` 的 Go 实现参考

### 解码器架构

```
原始报文 (SCTP/UDP/TCP)
     ↓
[协议识别层] ← PPID/端口/内容特征
     ↓
[NGAP 解码器] ← PER 解码 → 提取 NAS-PDU IE
     ↓                             ↓
  N2 消息记录                  [NAS 解码器]
                                  ↓
                           5GMM / 5GSM 消息
```

### 测试框架结构

```
测试/
├── pcaps/            # 测试 PCAP 数据
│   └── 5G单用户/     # 按场景分类的 PCAP
├── run_tests.py      # 主测试脚本
└── STCMS_TestReport_*.txt  # 测试报告输出
```

测试用例划分原则：
- 每项测一个独立能力
- 使用真实 PCAP 验证整体管道
- 使用 3GPP 测试向量验证算法
- 记录通过率 + 详细统计

## 已知限界

| 限界 | 说明 | 替代方案 |
|------|------|----------|
| NGAP PER 深度解码 | 字节级解析无法处理 PER 位级对齐 | 集成 pycrate NGAP.py |
| NAS 安全头处理 | 加密 NAS 需密钥才能解析内容 | 纯 NAS 解码 + 算法检测 |
| HTTP/2 SBI 解析 | 需要 HTTP/2 帧解析层 | 标准 HTTP/2 库 |
