# Mavenir IMS LI — X1/X2/X3 接口包快捷参考

**来源：** `/home/andymao/tempfile/Mavenir-IMS-LI.7z` → `knowledge/li/Mavenir/Mavenir_IMS_LI_接口包_X1_X2_X3.md`

## 关键架构特征

- Mavenir 不使用 ASN.1 BER，采用 **XML + SOAP/HTTPS** 架构
- X1 管理面: SOAP/HTTPS Web Service，命名空间 `http://mavenir.net/li/`
- X2 IRI 面: XML 报文，SIP 信令 Base64 编码后放入 CDATA
- X3 媒体面: 仅传元数据（方向/长度/类型），RTP/MSRP 流走独立通道

## X1 操作 (WSDL)

| 操作 | 请求类型 | 响应类型 | 说明 |
|:----|:---------|:---------|:-----|
| addTarget | TargetData | X1Response | 添加监听目标 |
| delTarget | Target | X1Response | 删除监听目标 |
| modifyTarget | TargetData | X1Response | 修改目标配置 |
| listTarget | Target | TargetListItem | 查询单个目标 |
| listAllTargets | (空) | TargetList | 查询全部目标 |
| getStatus | (空) | X1Response | 系统状态 |

## X2 hi2-uag 结构 (v1.3)

`li-tid` / `target` / `targettype` / `OtherIdentities(msisdn,imsi,imei,imeisv,email,uid)` / `session-id` / `stamp` / `CallDirection` / `Correlation-id` / `IAP-id`(64char) / `Payloadtype` / `Payload`(CDATA or Base64) / `EventPayload`(v1.3)

## TargetType 枚举（8种）

SIP-URI, MSISDN, IMSI, IMEI, IMEISV, EMAIL, SERVICE-NUMBER, CELL-ID

## 现网参考（乌干达 MTN, 2024-07）

- MCC/MNC: 641/001 (MTN Uganda)
- IMS 域: ims.mnc001.mcc641.3gppnetwork.org
- 终端: iOS/17.5.1 iPhone, LTE VoLTE
- 编码: AMR-WB/16000
- IAP 节点: UAGPTN01

## ZTLIG 对接

```c
ztlig.ssf.1300.interfaceType = 3;  // 3 = Mavenir 厂商模式
```

## 相关知识库文档

- [[Mavenir_CM_LI_ADD_DEL_返回状态码]] — SOAP 返回码 (200/400/401 等)
- [[ZTLIG运维手册]] — ZTLIG Mavenir 模式配置
- [[LI_ASN1解码工具_架构文档]] §3.4 — Mavenir XML Base64 解码说明
