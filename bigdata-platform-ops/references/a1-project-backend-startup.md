# A1 项目 OWLS 后台服务启动顺序 (苏丹谛听)

## SECPASS 组件启动顺序（按序）

1. GREENPLUM → 2. presto → 3. gp → 4. zookeeper → 5. hdfs → 6. yarn
7. mapreduce → 8. kafka → 9. DolphinScheduler → 10. hbase
11. hive → 12. Elasticsearch → 13. redis → 14. janusgraph → 15. nginx

## OWLS 后端 16 模块启动顺序

### rhino08 (215.152.1.18)
1. ftpfilesync: `cd /home/flink-tmc-1.0.0/bin && sh toolStart.sh ftpfilesync`
2. filesync: `cd /home/flink-tmc-1.0.0/bin && sh toolStart.sh filesync`
3. Listener-export: `cd /home/listener-export && sh startup.sh`
4. listener-es-hbase: `cd /home/listener-es-hbase-1.0.0 && sh startup.sh`

### rhino05 (215.152.1.12)
5. csp-etl (3 tasks): lis_rdt + text_mobile_sicms + flow_data
6. mpploader: `./start_mpploader.sh`
7. csp-alarm: `sh start-flink.sh`
8. Flink-tmc afterwards: `sh startup.sh afterwards`
9. Flink-tmc realtime: `sh startup.sh realtime`
10. Data-aging: `./startup.sh start`
16. voip-merge: `sh start-tool.sh voip_merge`

### rhino04 (215.152.1.11)
11. Graph2: `su - graph2 && sh startup.sh`
12. Graph1: `su - graph1 && sh startup.sh`
13. timespace: `./startAllScript.sh ds-timespace start`
14. web-server: `./startup.sh`
15. realtime player: `./voip_decoder ...`

## 实用命令

| 命令 | 用途 |
|------|------|
| `yarn application -list` | 查看 YARN 任务 |
| `yarn application -kill <id>` | 杀掉 YARN 任务 |
| `hdfs dfsadmin -rollEdits` | 触发 NameNode Checkpoint |
| `hdfs dfsadmin -safemode enter/leave` | 安全模式 |
| `hdfs fsck / -list-corruptfileblocks` | 查看缺失块 |

## 站点差异

站点 B 无 PS-LIG、SICMS、ES Head。
