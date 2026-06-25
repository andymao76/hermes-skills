# 爱立信 Ericsson IMS LI External API (HI1) WebServices

**来源**：CXC1373777_16_R6A.0_External_API_WebServices.tar
**本地路径**：`/home/andymao/tempfile/Ericsson/CXC1373777_R6A/`
**知识库路径**：`~/knowledge/telecom/lawful_interception/Ericsson_IMS_LI_External_API_WebServices_R6A.md`
**文件总量**：672 个文件（WSDL + XSD + properties）

## 文档特点

- 基于 SOAP document/literal 风格，通过 HTTP 传输
- 与 Utimaco RAI（TCP 二进制 PDU）和 ZTE CS LI（CLI 命令 + ASN.1 BER）完全不同
- 需要组合 WSDL + XSD + properties 三文件构建请求

## 接口架构

22 种 WebService，核心为：
- **SessionService** — `login`/`logout`：入口认证
- **WarrantService** — 13 种操作，Warrant CRUD
- **NeService** — 10 种操作，NE 查询/配置

## 请求构建三步法

1. **WSDL**：从 `<binding>` 找操作，从 `<portType>` 找结构
2. **XSD**：逐层追溯类型定义，注意命名空间（tns→主XSD，nrq→request_schema.xsd）
3. **Properties**：`resources/` 目录下的常量文件定义枚举值

### createWarrant 结构树

```
createWarrant → warrantCreateRequest
  ├── header → requestHeader (type, userID, sessionID)
  ├── item → warrantItem
  └── dtlWarrants → dtlWarrantNeTypeItemArray
        └── item[] → dtlWarrantNeTypeItem
```

## DtlWarrantNeTypeItem 核心字段

| 字段 | 类型 | 关键值 |
|------|------|--------|
| warrantID | int | 创建时 = -1 |
| neType | string | MSC/GPRS/SIPSERVER/MOWLAN/5GCORE 等 19 种 |
| isDataMonitoringOnly | short | 枚举常量 |
| mcnbs | int[] | CC 转发的 MCNB ID 列表 |
| supplementaryInfo | short | 位掩码（定位授权）|
| hosts | string[] | VoLTE Host 列表 |
| targetTypeID | string | IMSI/IMEI/E.164/SIP-URI 等 |

### supplementaryInfo 位定义

| 位 | 十进制 | 说明 | 适用 |
|----|:------:|------|------|
| LIPA_ON | 1 | 位置授权 | 通用 |
| ACCURATE_POS | 2 | 事件触发定位 | MSC/GPRS |
| SIMPLE_POS | 4 | 简单定位 | MSC/GPRS |
| ON_DEMAND_POS | 8 | 按需定位 | MSC/GPRS |
| PERIODIC_POS | 16 | 周期性定位 | MSC/GPRS |
| CR_ON | 256 | 改变用户位置 | GPRS |
| CELL_REPORTING | 512 | 小区报告 | GPRS |
| DOMAIN_WILDCARD | 1024 | SIP URI 通配符 | SIPSERVER |

### 跨 NE 类型一致性规则

GPRS 与 MOWLAN 的 `isDataMonitoringOnly` 和 `mcnbList` 必须完全一致。

## 分页查询 ListInformation

| 字段 | 请求值 | 说明 |
|------|:------:|------|
| recordsOnThisPage | 0 | 请求时固定 |
| maxRecordsPerPage | 正整数 | 建议 100 |
| pageNumber | ≥ 1 | 从 1 开始 |
| totalPages | -1 | 请求时固定 |

## 关联文档

- `~/knowledge/telecom/lawful_interception/Ericsson_IMS_LI_External_API_WebServices_R6A.md` — 完整文档
- `~/knowledge/telecom/lawful_interception/wsdl-xsd-basics.md` — WSDL+XSD 基础知识
- `~/knowledge/hi2/厂商状态码/Ericsson_LI-IMS_登录返回状态码.md`
