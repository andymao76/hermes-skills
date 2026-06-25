# ztlig_target.txt 字段速查

## 基本字段（23个）

| # | 字段名 | 说明 |
|---|--------|------|
| 1 | leaID | LEA ID |
| 2 | liid | 合法监听标识（给网元下发的 LIID）|
| 3 | targetType | 跟踪类型: 3=IMEI, 4=TEI, 5=IMSI, 6=MSISDN, 7=E.164, 8=SIP-URL, 9=TEL-URL |
| 4 | targetID | 布控目标 ID |
| 5 | module | 模块（默认不填）|
| 6 | incptType | 监听类型: 1=IRI, 2=CC, 3=IRI+CC |
| 7 | failDeal | 失败处理 |
| 8 | speechType | 语音处理: 0=合并, 1=分离 |
| 9 | hi2A | 2口对接地址 |
| 10 | hi2Port | 2口对接端口 |
| 11 | hi2User | 2口对接用户名 |
| 12 | hi2Pass | 2口对接密码 |
| 13 | hi2link | 2口链路类型 |
| 14 | hi3A | 3口地址 |
| 15 | startDay | 布控开始日期 |
| 16 | startTime | 布控开始时间 |
| 17 | endDay | 布控结束日期 |
| 18 | endTime | 布控结束时间 |
| 19 | virneID | 虚拟网元 ID |
| 20 | neID | 物理网元 ID |
| 21 | hw_lioid | 华为特有 lioid（非华为不需要）|
| 22 | nsn_reqId | NSN PS 域请求 ID |
| 23 | mcID | 监听中心编号 |

## 多 TMC 模式额外字段（共25个）

| # | 字段名 | 说明 |
|---|--------|------|
| 24 | tmcid | 多 TMC 模式下 TMC 标识 |
| 25 | mcliid | MC 下发的真实 LIID 值 |

**多 TMC 模式配置**: `ztlig.dbLeaID > 0`
