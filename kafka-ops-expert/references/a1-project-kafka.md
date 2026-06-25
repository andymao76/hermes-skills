# A1 项目 Kafka 运维参考 (苏丹谛听)

## 环境信息

| 项目 | 值 |
|------|-----|
| Kafka 目录 | /usr/hdp/3.1.0.0-78/kafka/bin/ |
| Bootstrap Server | 215.152.1.15:9092 |
| Kafka Manager | http://215.152.1.15:9000 |
| Kafka Manager 启动 | `nohup /home/kafka/kafka-manager-2.0.0.0/bin/kafka-manager -Dhttp.port=9000 >./start.log 2>&1 &` |

## Topic 速查

| Topic | 用途 |
|-------|------|
| TMC_TARGET_INFO | 设控/解控指令下发 |
| TTARGET_INFO_STATUS | 设控状态反馈 |
| SICMS_STREAM_IPDR | IPDR 话单流 |
| TARGET_INFO_STATUS | 目标信息状态 |

## Consumer Group 诊断

```bash
# 查看所有 group
./kafka-consumer-groups.sh --bootstrap-server 215.152.1.15:9092 --list

# 查看指定 group
./kafka-consumer-groups.sh --bootstrap-server 215.152.1.15:9092 --describe --group <groupName>

# 全量查看
./kafka-consumer-groups.sh --bootstrap-server 215.152.1.15:9092 --all-groups --describe
```

## 设控 JSON 下发

```json
{"account":"<ISDN号码>","editFlag":4,"isDel":0,"mapId":<id>,"officesIds":"<网元ID>",
 "protocol":"ISDN","protocolType":"ISDN","restoreType":"TMC","targetId":<id>}
```

isDel: 0=设控, 2=解控

## 注意

⚠️ IP、端口、Topic 名称均为 A1 项目（苏丹/北苏丹）专属，其他项目需人工确认。
