# HW LI X1 NE type 编码表

Table 2-2 from LI-HW.pdf (Huawei CS ETSI 规范).

## 完整编码表

值 `0` 和 `255` 保留。网元收到不匹配自身 NE type 的 X1 消息直接丢弃。

| DEC | HEX | 网元 | 所属域 | 中文说明 |
|:---:|:---:|---|:---:|---|
| 0 | `0x00` | **保留** | - | 无效/未知网元 |
| **1** | **`0x01`** | **MSCserver / MSC** | WCDMA/GSM | 移动交换中心服务器/移动交换中心 |
| **2** | **`0x02`** | **HLR** | WCDMA/GSM | 归属位置寄存器 |
| **3** | **`0x03`** | **SMSC** | WCDMA/GSM | 短消息中心 |
| **4** | **`0x04`** | **SGSN** | WCDMA/GSM | 服务GPRS支持节点 |
| **5** | **`0x05`** | **GGSN** | WCDMA/GSM | 网关GPRS支持节点 |
| **6** | **`0x06`** | **GMLC** | WCDMA/GSM | 网关移动定位中心 |
| 31 | `0x1F` | cMSC | CDMA | CDMA MSC |
| 32 | `0x20` | cHLR | CDMA | CDMA HLR |
| 33 | `0x21` | cSMC | CDMA | CDMA 短消息中心 |
| 34 | `0x22` | PDSN | CDMA | 分组数据服务节点 |
| 37 | `0x25` | AAA | CDMA | 认证授权计费服务器 |
| 81 | `0x51` | MSE | WCDMA/GSM | 多媒体子系统增强 |
| 91 | `0x5B` | NGN | 固网 | 下一代网络 |
| 101 | `0x65` | P-CSCF | IMS | 代理CSCF |
| 102 | `0x66` | I-CSCF | IMS | 查询CSCF |
| 103 | `0x67` | S-CSCF | IMS | 服务CSCF |
| 104 | `0x68` | HSS | IMS | 归属用户服务器 |
| 105 | `0x69` | CCTF | IMS | 呼叫连续触发功能 |
| 106 | `0x6A` | MGCF | IMS | 媒体网关控制功能 |
| **111** | **`0x6F`** | **IMS** | IMS | IMS核心网（整体标识） |
| 121 | `0x79` | TAS | IMS | 电信应用服务器 |
| 123 | `0x7B` | AGCF | IMS | 接入网关控制功能 |
| 151 | `0x97` | SBC | IMS | 会话边界控制器 |
| 255 | `0xFF` | **保留** | - | - |
