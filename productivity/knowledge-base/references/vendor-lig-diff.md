# 厂商 LIG 差异速查

## Sinovatio ZTLIG Target 字段格式（CSV，23字段）

多 TMC 模式共 25 个字段（追加 mcliid + imsi）。

| # | 字段 | 说明 |
|---|------|------|
| 1 | leaID | LEA 编号 |
| 2 | liid | lawfulInterceptionIdentifier |
| 3 | targetType | 0=UserNumber, 1=TrunkGroup, 2=Prefix, 3=IMEI, 4=TEI, 5=IMSI, 6=MSISDN, 7=E.164, 8=SIP-URL, 9=Tel-URL, 10=IDSN |
| 4 | targetID | 布控目标 ID |
| 5 | module | 模块（Kafka 下发默认空） |
| 6 | incptType | 1=IRI, 2=CC, 3=IRI+CC |
| 7 | failDeal | 失败处理 |
| 8 | speechType | 0=语音合并, 1=语音分离 |
| 9 | hi2A | HI2 地址 |
| 10 | hi2Port | HI2 端口 |
| 11 | hi2User | HI2 用户名 |
| 12 | hi2Pass | HI2 密码 |
| 13 | hi2link | HI2 链路类型（主动/被动） |
| 14 | hi3A | HI3 地址 |
| 15-18 | startDay/startTime/endDay/endTime | 布控起止时间 |
| 19 | virneID | 虚拟网元 ID |
| 20 | neID | 物理网元 ID |
| 21 | hw_lioid | 华为 LIOID（非华为不用） |
| 22 | nsn_reqId | NSN PS 域请求 ID |
| 23 | mcID | 监听中心编号 |
| 24 | mcliid | 多 TMC 模式：MC 下发真实 LIID |
| 25 | imsi | 多 TMC 模式：NSN 1IPV1 网元关联的 IMSI |

多 TMC 模式配置：`ztlig.dbLeaID > 0`，用于一套 PS 对接两套后端。

## 华为 LIG Target 字段对比

华为使用 LIOID（32-bit unsigned integer）替代 liid 的概念：
- LIOID 在 NE 上唯一标识一个 LI 目标
- 同一个用户的不同 SUPI/GPSI 组合视为不同目标，分配不同 LIOID
- 华为 X1 接口 Target 操作：SetTarget/DeleteTarget/ModifyTarget/ListTarget/QueryTargetAttribute
- 消息头含 TNEType（设备类型）和 FUNCType（功能类型），共享 X2/X3 接口

## NSN / E/// 待补充
