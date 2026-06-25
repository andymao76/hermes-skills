---
name: ber-tlv-analysis
title: BER-TLV 码流分析工作流
description: 分析 ASN.1 BER 码流的标准化流程 — 本地脚本结构遍历 + pyasn1 三方验证 + X.690 规则校验
tags: [asn1, ber, tlv, protocol-analysis]
---

# BER-TLV 码流分析工作流

## 触发条件

当用户要求分析 16 进制 BER 码流（如 MAP/CAP/TCAP 信令），或询问 BER TAG 编解码是否正确时触发。

## 参考知识

- 知识库 `telecom/3gpp/` 下有完整的 BER 参考体系
- BER 规范 PDF：`ITU-T_X.690-202102_BER.pdf`（822K, v2021）
- 分析脚本：`/home/andymao/ber-tag-analyzer.py`
- **ETSI-ASN1-Assistant V3** (Web GUI 解码器)：`~/work-projects/ETSI-ASN1-Assistant/`
  - Flask Web 应用，支持多家厂商 HI2 解码（hw-cs/hw-ims/zte-cs/hw-5gc/hw-sae/nsn-cs/zte-epc）
  - 上传 PCAP 或 IRI 文本文件，自动 BER 解码 + SIP 消息提取
  - 启动方式：`cd ~/work-projects/ETSI-ASN1-Assistant && source venv/bin/activate && python3 src/app_linux_v3.py`
  - 访问地址：`http://127.0.0.1:5000`
  - 支持 TCP 重组、端口/IP/CI N/LIID 过滤
  - 解码结果含 PANI 位置信息自动解析

## BER TAG 编解码规则（ITU-T X.690 §8.1.2）

### 短格式（tag ≤ 30）

```
TAG = byte & 0x1F（低 5 位）
bit7-6: Class (00=U, 01=A, 10=C, 11=P)
bit5:   Form  (0=Primitive, 1=Constructed)
```

### 长格式（tag ≥ 31）

```
首字节 low5 = 11111
续字节 bit7=1=more/0=last, 低7位拼接(big-endian)
```

### Length 编码（§8.1.3）

| 格式 | 规则 |
|------|------|
| 短格式(0-127) | 单字节, bit7=0 |
| 长格式(128+) | 首字节 bit7=1, 低7位=续字节数 |
| 不定长 | `0x80` + ... + `00 00` EOC |

## 分析流程

### 第一步：结构遍历

```bash
python3 /home/andymao/ber-tag-analyzer.py "16进制码流"
```

- 按 BER TLV 结构自动跳转，输出 2位/4位/6位 TAG 假设值
- length==0 时不 break（如 SS-Status NULL），继续解析下一 TAG

### 第二步：pyasn1 三方验证

```python
from pyasn1.codec.ber import decoder
data = bytes.fromhex("16进制码流")
decoded, remainder = decoder.decode(data)
```

- pyasn1 是标准库实现，结果视为 Ground Truth
- 对比脚本输出，偏移量和 TAG 值应完全一致

### 第三步：结构手动校验

对照 X.690 规则逐层验证：
1. TAG 字节：Class + Form + Tag# 是否正确
2. Length：短/长/不定长格式是否正确
3. Value：Primitive 跳过 / Constructed 递归进入

## 常见陷阱

| 陷阱 | 正确做法 |
|------|---------|
| `length == 0` 时 break | 应该 pass，继续解析下一 TAG |
| 用 LLM 验证 BER 码流 | **不推荐** — Qwen/DeepSeek 概率生成有结构化错误 |
| apReq_T 等非 BER 头部 | 跳过前 N 字节，仅分析 ASN.1 内容部分 |
| TBCD IMSI 解码手算 | 易手误，用工具计算 |
| LI 数据层 TLV 混合在码流中 | 先用 `aa05` 魔数定位 LI 协议头，跳过协议头再解析 BER TLV |
| 报告结论不标注来源 | 每条结论必须标注 PCAP 文件名 + 报文序号。用户要求明确的数据出处，不能说"查到了"或"从解码结果中提取"这种含糊表述 |
| 忽略 `Wlan-ue-local-ip` 字段 | VoWiFi PANI 的 `Wlan-ue-local-ip` 是用户真实的公网IP，区别于 `ue-ip`（IMS私网IP）。必须区分提取和标注 |

## 扩展：合法监听数据层编码

LI 数据层（华为/Sinovatio `aa05` 协议）基于 BER 风格 TLV，但 TAG 与 3GPP MAP 不同。参考文件 `references/li-data-layer-tlv-encoding.md` 包含：

- LI 协议头格式 (`aa05` + 长度 + 序列号)
- LI TLV TAG 速查表 (`80`=CIN, `81`=LIID, `97`=OPERID, `A2`=CalledParty等)
- LIID 反序BCD 编解码规则
- X2 IRI 消息结构（HW ATS9900 码流头格式）
- OPERID / 时间戳等字段的编码方式

## 分析输出：生成 Word 报告

解码后通过 python-docx 生成结构化报告，保存到 PCAP 所在目录。

### 报告结构规范

报告应按以下章节组织，每个章节必须包含**数据来源标注**：

| 章节 | 内容 | 来源标注要求 |
|------|------|-------------|
| 标题页 | 项目名、时间、统计 | 标注PCAP文件名、解码工具版本 |
| 汇总统计 | 包数、解码条数、LIID数 | 标注每项统计对应的PCAP文件和报文范围 |
| PANI位置表 | 每个LIID的接入类型、小区ID、UE IP:Port | 每条记录标注报文序号 |
| 会话详情 | 每个LIID的信息表+ PANI明细 | 每个字段标注来源(PCAP序号) |
| 专项分析 | 公网IP、CID过滤等 | 标注具体报文序号清单 |
| 附录 | 解码方法 | 工具路径、ASN.1规范文件 |

### 来源标注规范

**每条关键结论必须标注出处**，格式：
- PCAP文件名（简写: PCAP1/PCAP2）
- 报文序号（#number）
- 如跨多个报文，提供完整清单或统计："共12条(PCAP1: 6条 #9772~#27084, PCAP2: 6条 #17890~#37414)"

### 完整报告示例结构

1. **标题页**: 项目名 + 时间 + PCAP统计
2. **汇总统计表**: 包数、解码条数、LIID数
3. **PANI 位置信息表**: 所有LIID的接入类型、小区ID、UE IP:Port
4. **各LIID会话详情**: 信令流程、终端、PANI明细
5. **专项分析**: 公网IP/CID过滤的分析 + 报文出处清单表
6. **数据出处说明**: 各章节来源表、解码工具说明
7. **附录**: 解码方法、完整解码HTML路径

### 关键字段提取模板

```python
def extract_key_info(data):
    """从HI2 IRI报告提取关键字段"""
    KW = {'lawfulInterceptionIdentifier', 'imsChargingID', 'generalizedTime',
          'sipMessage', 'sipMessageDirection', 'intercepted-Call-Direct',
          'partyIdentity', 'umts-Cs-Event', 'globalCellID', 'eCGI', 'imei',
          'imsi', 'msISDN'}
    M = {'lawfulInterceptionIdentifier': 'LIID',
         'communication-Identity-Number': 'CIN',
         'generalizedTime': 'TimeStamp'}
    # ... 递归遍历extract
```

### 常用脚本模式

```bash
python3 scripts/gen_hi2_report.py decoded_a.html [decoded_b.html ...] -o report.docx
```

参考 `references/a1-vowifi-hi2-iri-decode-example.md` 的 PANI 提取方法和来源标注示例。

## 关联工具：ETSI-ASN1-Assistant V3

位于 `/home/andymao/work-projects/ETSI-ASN1-Assistant/` 的 Flask Web 解码工具，用 asn1tools 按厂商 ASN.1 规范解码 HI2 IRI 报告。

### 支持的解码类型

| 参数值 | 对应厂商/场景 |
|--------|-------------|
| `hw-ims` | 华为 IMS (VoLTE/VoWiFi) |
| `hw-cs` | 华为 CS |
| `hw-5gc` | 华为 5GC X2 |
| `hw-sae` | 华为 SAE/LTE X2 |
| `zte-cs` | 中兴 CS |
| `zte-epc` | 中兴 EPC |
| `nsn-cs` | 诺西 CS |
| `g2k` | G2K (含 Utimaco VoLTE) |
| `mavenir` | Mavenir XML 报告 |

### 启动

```bash
cd /home/andymao/work-projects/ETSI-ASN1-Assistant
source venv/bin/activate
python3 src/app_linux_v3.py
# 访问 http://127.0.0.1:5000
```

## 解码命令

```bash
curl -s -X POST \
  -F "pcap_file=@a8b0f01b-2ef1-48a2-b46b-527e14da0f3d.pcap" \
  -F "decode_type=hw-ims" \
  -F "port_filter=8890" \
  -F "tcp_fragment=tcp_fragment" \
  http://127.0.0.1:5000/ -o decoded_a8b0.html
```

## PANI (P-Access-Network-Info) 提取方法

PANI 头域位于解码后 SIP 消息 (`sipMessage` 字段) 的 `P-Access-Network-Info:` 行，包含用户接入位置信息。

### 字段结构

```
P-Access-Network-Info: 3GPP-E-UTRAN;utran-cell-id-3gpp=63407A0930044302;
"sbc-domain=atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org";
"ue-ip=10.201.177.169";"ue-port=40615";network-provided
```

| 子字段 | 说明 | 示例 |
|--------|------|------|
| 接入类型 | 接入网类型 | `3GPP-E-UTRAN` (LTE), `3GPP-UTRAN-FDD` (3G), `IEEE-802.11` (WiFi) |
| `utran-cell-id-3gpp` | 小区标识(hex) | `63407A0930044302` — 含MCC+MNC+LAC+CI |
| `ue-ip` | 用户私网IP | `10.201.177.169` |
| `ue-port` | 用户端口 | `40615` |
| `sbc-domain` | SBC/CSCF域名 | `atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org` |
| `network-provided` | 网络提供 | 表示该信息由网络侧提供 |

### Python 解析

```python
import re

def parse_pani(sip_msg):
    panis = []
    for m in re.finditer(r'P-Access-Network-Info:\s*([^\r\n]+)', sip_msg):
        raw = m.group(1).strip()
        info = {'raw': raw}
        at = re.search(r'^(\S+)', raw)
        if at: info['access_type'] = at.group(1)
        ci = re.search(r'utran-cell-id-3gpp=([0-9A-Fa-f]+)', raw)
        if ci: info['cell_id'] = ci.group(1)
        ue_ip = re.search(r'ue-ip=([0-9.]+)', raw)
        if ue_ip: info['ue_ip'] = ue_ip.group(1)
        ue_port = re.search(r'ue-port=(\d+)', raw)
        if ue_port: info['ue_port'] = ue_port.group(1)
        sbc = re.search(r'sbc-domain=([^;"]+)', raw.replace('"', ''))
        if sbc: info['sbc_domain'] = sbc.group(1).strip()
        # VoWiFi: Wlan-ue-local-ip = WiFi用户的真实公网IP
        wlan_ip = re.search(r'Wlan-ue-local-ip=([0-9.]+)', raw)
        if wlan_ip: info['wlan_public_ip'] = wlan_ip.group(1)
        wlan_port = re.search(r'Wlan-ue-local-port=(\d+)', raw)
        if wlan_port: info['wlan_public_port'] = wlan_port.group(1)
        panis.append(info)
    return panis
```

### 小区ID 解读（utran-cell-id-3gpp）

3GPP 小区 ID 编码规则（hex 字符串，总长度可变）：
- **前3位**: MCC (移动国家码，如 `634`=苏丹)
- **续2~3位**: MNC (移动网码，如 `07`=ZAIN)
- **续4位**: LAC (位置区码, 4 hex)
- **剩余**: CI (小区标识, 4~5 hex)

示例：`63407A0930044302` → MCC=634, MNC=07, LAC=A093, CI=0044302

### VoWiFi 特殊字段

当接入类型为 `IEEE-802.11` (VoWiFi) 时，PANI 携带额外字段：

| 字段 | 示例 | 说明 |
|------|------|------|
| `Wlan-ue-local-ip` | `196.202.142.135` | **WiFi用户的公网IP**（路由器NAT前地址，非运营商级NAT） |
| `Wlan-ue-local-port` | `16567` | WiFi用户的本地端口 |

**重要**: `Wlan-ue-local-ip` 是该用户在 WiFi 网络上的实际公网 IP，可用于精确定位用户所在 WiFi 网络的互联网出口。该 IP 归属 AFRINIC (非洲地区) 即表示用户所在国家。

### PANI 不包含的信息

3GPP IMS PANI 头域 **不传递** 以下信息（需要从 X3 媒体流 PDCP 层提取）：
- WiFi SSID 或网络名称
- "FREE WIFI"、hotspot、public 等标识
- AP MAC 地址
- 地理位置坐标

### 接入类型速查

| PANI 接入类型 | 含义 |
|--------------|------|
| `3GPP-UTRAN-FDD` | 3G WCDMA (UMTS) |
| `3GPP-E-UTRAN` | 4G LTE (含 VoWiFi) |
| `IEEE-802.11` | WiFi (VoWiFi) |
| `3GPP-GERAN` | 2G GSM |
| `3PTC` | IMS终止侧 (Terminating) |
| `3POC` | IMS发起侧 (Originating) |

### PANI 分析要点

- **接入切换**: 同一通话中出现 `3GPP-UTRAN-FDD` 和 `3GPP-E-UTRAN` 表示 VoWiFi ↔ 蜂窝网切换
- **LTE vs 3G**: E-UTRAN = LTE/VoWiFi, UTRAN-FDD = 3G
- **时间戳关联**: 每条 PANI 携带对应 SIP 消息的 `generalizedTime`，可重建用户移动轨迹
- **公网IP提取**: WiFi 接入时 `Wlan-ue-local-ip` 是该用户的真实出口公网 IP
- **私网IP vs 公网IP**: `ue-ip` 是 IMS 核心网分配的私网IP(10.x.x.x)，`Wlan-ue-local-ip` 才是真正的公网地址
- **免过滤区分**: 同一 PCAP 中端口 8890 的 TCP 流是 IRI，端口 9904/9905 的 UDP 是统计数据

## Word 报告自动化

解码后可通过 python-docx 生成结构化 Word 报告，包含：

1. **标题页**: 项目名 + 时间 + 统计信息
2. **统计表**: PCAP 概况、解码条数、LIID 数
3. **PANI 位置表**: 全部 LIID 的接入类型、小区ID、UE IP:Port
4. **会话详情**: 每个 LIID 的信息表(信令流程、主被叫、终端) + PANI 明细
5. **附录**: 解码方法说明

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cn_font(run, cn_font='微软雅黑', en_font='Arial',
                size=None, bold=None, color=None):
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), cn_font)
    rFonts.set(qn('w:ascii'), en_font)
    rFonts.set(qn('w:hAnsi'), en_font)
    if size: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if color: run.font.color.rgb = color

def set_cell_shading(cell, color):
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)
```

表格样式建议：深蓝表头 (`1F4E79`) + 白色文字，数据行交替浅蓝 (`E8F0FE`) 底色。

### 常见工作流：VoWiFi/IMS 抓包分析

1. 端口 8890 TCP = X2 IRI 交付（`aa05` 协议头 + BER）
2. 端口 20000/20002/20004 UDP = X3 CC 媒体流
3. 用 `hw-ims` 解码 + `port_filter=8890` + `tcp_fragment` 过滤
4. 端口 9904/9905 UDP = 统计/心跳数据（非 BER 格式）
5. 注意：端口 8890 是 TCP 流，必须启用 `tcp_fragment` 才能重组

### 路径陷阱

ASN 规范文件在 `src/asnfile/`，但 `asn_spec_v3.py` 的 `ASN()` lambda 使用 `os.path.join(current_path, "asnfile", f)` 拼接路径。启动时需确保 `current_path` 指向 `src/` 目录（不含 `asnfile`），否则路径会变成 `src/asnfile/asnfile/` 导致加载失败。

修复方式：在 `app_linux_v3.py` 中设置：
```python
asn_spec_mod.current_path = BASE_DIR  # 而不是 os.path.join(BASE_DIR, "asnfile")
```
同时遍历修正已初始化的 `.asn` 路径变量。

## 关联知识库

- `telecom/3gpp/ber-tlv-tag-analyzer-tool-and-validation.md`
- `telecom/3gpp/ber-encoding-reference-library.md`
- `telecom/3gpp/asn1-basic-syntax-and-ber-encoding-detailed.md`
- `telecom/3gpp/map-insertsubscriberdata-codec-analysis.md`
- `telecom/lawful_interception/pcap-volte-sip-i-li-data-layer-analysis.md`
