# HW LI 知识库索引

查看 `/home/andymao/Documents/Obsidian Vault/知识/telecom/lawful_interception/`

| 笔记 | 定位 | 涉及接口 |
|------|------|---------|
| 华为SVC_VoLTE_ETSI监听方案.md | IMS/SVC方案原理 + ICID/port negotiation | X2/X3 IMS |
| 华为SVC_IMS_X2报告抓包示例.md | 13步VoLTE呼叫IRI完整解码 + SIP消息还原 | X2 IMS |
| 华为CS_X接口说明与ZTLIG部署实战.md | CS全接口(X1/X2/X3) + BER编码 + 实战日志(SSF/RVF) | X1/X2/X3 CS |
| ZTLIG运维手册.md | 完整运维(23章+附录, ~150项配置, 8进程配置块) | 全接口 |
| TMC系统工勘指导.md | LI开局网元调查模板(2G~5G/VoLTE/VoNR/PSTN) | 全接口 |
| 爱立信1口对接调试文档.md | Ericsson LI-IMS SOAP(WSDL/XSD/Properties) + HI1结构 + SOAP操作 | X1 |
| HI2和标准.md | HI2定义 + ETSI标准体系(101671/102232/33108) + 文件命名规范 | 标准参考 |

## ASN.1 规范文件（`/home/andymao/LI/asn/`）
- `HI2Operations,ver18.asn` — ETSI TS 101 671 v18 (1035行)
- `UmtsCS-HI2Operations.asn` — 3GPP TS 33.108 R17 (255行)
- `LI-PS-PDU,ver39.asn` — ETSI TS 102 232 v39 (762行)

## Ericsson 资源（`/home/andymao/LI/ETSI/E/`）
- `爱立信1口对接调试文档.md` — SOAP对接文档
- `爱立信-HI1结构一览及其构造-详细.md` — HI1请求结构+字段详解
- `2-3-爱立信-请求响应对.py` — 完整SOAP XML模板(5种操作)
- `爱立信LI-IRI-LUD.xmind` — IRI类型脑图
