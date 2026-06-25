# ETSI-ASN1-Assistant V3 — HI2 IRI 解码 Web App

项目位于 `/home/andymao/work-projects/ETSI-ASN1-Assistant/`，是一款 Flask Web 应用，用于上传 PCAP 或 IRI 报告文本，解码 HI2 信令消息。

## 支持的厂商/协议

- HW_5GC_X2
- HW_SAE_X2
- NSN_CS
- ZTE_EPC
- Mavenir（XML 报告解码）

ASN.1 规范文件位于 `src/asnfile/`，包含 UMTS/CS/PS/EPS 等的 HI2Operations 定义。

## 启动方式

```bash
cd /home/andymao/work-projects/ETSI-ASN1-Assistant
source venv/bin/activate
python3 src/app_linux_v3.py
```

依赖（已装于 venv）：`flask`, `dpkt`, `asn1tools`, `pyyaml`

## 端口配置

默认监听 `0.0.0.0:5000`。可通过环境变量修改：
```bash
LI_PORT=8080 python3 src/app_linux_v3.py
```

## 访问

浏览器打开 http://127.0.0.1:5000，上传文件解码。

## 架构

- `app_linux_v3.py` — Flask 应用入口，TCP 流组装、文件上传
- `asn_decode_iri_report_v3.py` — IRI 报告/PCAP 解码入口
- `asn_decode_api_v3.py` — `decode_hi2_cs_message()` 等底层解码 API
- `asn_spec_v3.py` — ASN.1 规范编译与字段描述准备
- `templates/` — upload.html / result.html / result1.html / result2.html
