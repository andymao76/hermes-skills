# v3 版 LI ASN.1 解码器新增 4 套 ASN.1 规范

从 `~/LI/software/asn/`（原 Windows EXE 项目）中发现并移植的 4 个额外 ASN.1 规范文件，使工具从 6 种解码模式扩展到 10 种。

## 新增规范

| ASN.1 文件 | 模块名 | 行数 | 供应商 | 解码模式 | 关键类型 |
|-----------|--------|------|--------|---------|---------|
| `hw_5gc_x2.asn` | HWIriReport | 1197 | 华为 | hw-5gc | IRI-Parameters (含 correlationNumber=SMF Charging ID, FifthGS-SpecificParameters) |
| `hw_sae_x2.asn` | HWIriReport | - | 华为 | hw-sae | IRI-Parameters (含 activationDuration, ipAssignment static/dynamic/notKnown) |
| `nsn_cs.asn` | OlcmReportModule | - | 诺西 | nsn-cs | OlcmReport (含 liid, communicationIdNumber, EXTENSIBILITY IMPLIED) |
| `zte_epc.asn` | EpsHI2Operations | 798 | 中兴 | zte-epc | EpsIRIContent CHOICE {iRI-Begin,iRI-End,iRI-Continue,iRI-Report} |

## 文件位置

- 源码项目：`~/LI/software/000000app_v1/asnfile/` (24 个 .asn)
- 原始 Windows 项目：`~/LI/software/asn/asnfile/` (24 个 .asn)

## 解码架构

v3 版解码器 `decode_hi2_cs_message()` 内部按 vendor 路由：

```
vendor in ("hw_cs","hw_ims","hw_5gc_x2","hw_sae_x2") → 跳过14字节头
华为系: hi2_spec_hw / hi2_spec_hw_ims  → UmtsCS-IRIContent
华为5GC: hi2_spec_hw_5gc → HWIriReport → IRI-Parameters
华为SAE: hi2_spec_hw_sae → HWIriReport → IRI-Parameters
中兴CS: hi2_spec_zte → UmtsCS-IRIContent
中兴EPC: hi2_spec_zte_epc → EpsHI2Operations → EpsIRIContent
诺西CS: hi2_spec_nsn → OlcmReportModule → OlcmReport
G2K: hi2_spec_1023232 → LI-PS-PDU → PS-PDU
其它: hi2_spec_gl → UmtsCS-IRIContent
```

## 反编译来源

Windows EXE `app_v1_1.exe` (8.9MB, Python 3.7) 经 pyinstxtractor + uncompyle6 反编译。EXE 版使用 `decode_ps_*` 独立解码路径处理新增厂商，v3 版统一为 `decode_hi2_cs_message()` 架构。

## 运行方式

```bash
cd ~/LI/software/000000app_v1
~/.hermes/hermes-agent/venv/bin/python3 app_linux_v3.py
# 浏览器 http://127.0.0.1:5000
```
