# Kafka Business Topic 字段字典

## 命令模板

```bash
./kafka-console-consumer.sh --bootstrap-server <KAFKA_IP>:<PORT> \
  --topic <BUSINESS_TOPIC> \
  --from-beginning | grep <CIN值>
```

参数替换：Kafka IP:Port、业务topic名、要查的CIN( CIDNUM )。

## 输出结构

一个CIN通常返回多条记录，对应通话的不同阶段（UMTS_EVENT不同）。

### 基础标识

| 字段 | 说明 | 示例 |
|------|------|------|
| TID | 记录唯一ID | `22_2319d84358d89b79a3fe9716a73f768d_1781614404` |
| CLUE_ID | 线索/案件ID | 17746 |
| CIDNUM | 通话标识号 (CIN) | `atbpcscf01.19a.8315.20260616125313` |
| NEID | 网元ID | 2491250814467 |
| NEID_TYPE | 网元类型 | 2 |
| OPERID | 运营商ID | 2048 / 123 |

### 调用方向

| 字段 | 说明 |
|------|------|
| CALLDIR | 呼叫方向 (1=主叫) |
| CALLER_MSISDN | 主叫号码 |
| CALLED_MSISDN | 被叫号码 |
| CALLER_IMSI / CALLED_IMSI | 主叫/被叫IMSI |

### 事件与动作

| 字段 | 说明 |
|------|------|
| UMTS_EVENT | 事件类型（见下方对照表） |
| ACTION_TYPE | 动作类型 (1=振铃, 2=接通, 5=挂断) |
| SERVICE_TYPE | 业务类型 (1=语音) |
| DURATION | 通话时长(秒) |
| CAPTURETIME | 捕获时间戳 (Unix) |

### 位置信息

| 字段 | 说明 | 示例 |
|------|------|------|
| SITE_NAME | 基站名称 | KHN (喀土穆北部) |
| SITE_ID | 基站ID | 6340704523F4C |
| CITY_NAME | 城市名称 | KHN |
| LAC | 位置区码 | 1106 |
| CELLID | 小区ID | 16204 |
| LATITUDE / LONGITUDE | 纬度/经度 | 15.6087 / 32.6033 |
| CALLER_LAT_LON | 主叫经纬度组合 | 15.6087,32.6033 |
| AZIMUTH | 天线方位角(度) | 330 |
| GEOHASH | GeoHash编码 | sdz0vck |
| RAT_TYPE | 接入网类型: 12=GERAN(2G), 13=UTRAN(3G) |

### 文件路径

| 字段 | 说明 |
|------|------|
| FILE_PATH | 媒体文件路径(话后) |
| ORIGINAL_FILE_PATH | 原始文件路径(采集侧) |
| FACTORY_NAME | 厂家标识 (hw / zte) |

### 其他

SRC_INFO_TYPE=4000(监听), COUNTRYCODE=249(苏丹), SSCODE, TAG, UUID, REDIRECTIONNUMBER, TRGTNUM, TRGTIMSI, SMS_NUM, SMS_CONTENT

## UMTS_EVENT 完整对照

| 值 | 含义 |
|----|------|
| 1 | 振铃/呼叫尝试 (Alerting) |
| 2 | 接通/应答 (Connect) |
| 3 | 释放 (Release) |
| 4 | 呼叫前转 (Call Forwarding) |
| 5 | 挂机/通话结束 (Disconnect) |
| 6 | 切换 (Handover) |
| 7 | 位置更新 (Location Update) |
| 8 | 短信提交 (SMS Submit) |
| 9 | 短信投递 (SMS Delivery) |

## 分析示例

查询 CIN `atbpcscf01.19a.8315.20260616125313` 返回 3 条记录:

| 序号 | UMTS_EVENT | 含义 | 关键信息 |
|------|-----------|------|---------|
| 1 | 1 | 振铃 | 无位置, 有原始/话后文件路径 |
| 2 | 2 | 接通 | **有位置**: KHN基站, LAC=1106, CELLID=16204, 15.6087°N/32.6033°E |
| 3 | 5 | 挂断 | DURATION=10秒, OPERID变为123, RAT_TYPE=13 |

三条记录通过 TID 的 UUID 前缀关联为同一通话的不同阶段。
