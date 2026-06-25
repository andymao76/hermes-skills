# ETSI LI 标准版本参考

## TS 102 232 系列（Handover Interface for IP Delivery）

| Part | 内容 | 最新版本 | 状态 |
|------|------|----------|------|
| Part 1 | 通用架构、PDU 格式、ASN.1 编码 | V3.28.1 (2023+) | ✅ Activity |
| Part 2 | 邮件服务（POP3/IMAP/SMTP） | V3.x | ✅ Active |
| Part 3 | IP 承载服务（宽带/WiFi） | V3.12.1 (2023) | ✅ Active |
| Part 4 | 二层网络服务 | V3.2.2 (2014) | ⚠️ Stale |
| Part 5 | 多媒体（SIP/RTP/IMS/VoLTE） | V3.x | ✅ Active |
| Part 6 | PSTN/ISDN 电路交换 | V3.x | ⚠️ Legacy |
| Part 7 | 移动网络（2G/3G/4G/5G） | V3.x | ✅ Active |

## 其他核心标准

| 标准 | 名称 | 说明 |
|------|------|------|
| TS 101 331 | LEA 需求规范 | LI 功能需求的顶层规范 |
| TS 101 671 | 电路交换监听接口 | ⛔ Legacy，被 TS 102 232-6 取代 |
| TS 102 657 | 数据留存接口（HI-A/HI-B） | 留存数据请求和交付 |
| TS 103 120 | 令状交换（Warrant Exchange） | HI1 行政接口标准 |
| TS 103 221 | 内部接口（X1/X2/X3） | 5G LI 核心接口 |

## TS 33.128（5G LI 载荷定义）

- 3GPP 定义 IRI/CC 载荷内容结构
- ETSI TS 102 232-7 引用作为 5G 交付机制
- 与 ETSI 标准互补：3GPP 定义拦截什么，ETSI 定义如何交付

## 版本查询方法

```bash
# 查询 ETSI 标准最新版本（需联网）
# ETSI 标准下载页面:
#   https://www.etsi.org/deliver/etsi_ts/102200_102299/10223201/
#
# 查询特定 Part:
#   https://www.etsi.org/deliver/etsi_ts/102200_102299/10223201/latest/
#   https://www.etsi.org/deliver/etsi_ts/102200_102299/10223203/latest/
```
