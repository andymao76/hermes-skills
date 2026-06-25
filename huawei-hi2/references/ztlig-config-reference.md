# ZTLIG 配置参考（完整版）

> 完整运维手册见 `~/knowledge/telecom/lawful_interception/ZTLIG运维手册.md`

## 1. GLOBAL 部分

| 配置项 | 类型 | 默认值 | 含义 | 属性 |
|--------|------|--------|------|------|
| ztlig.x_ftp.usr | 字符串 | ztlig | X2/X3 FTP/SFTP 登录用户名 | C |
| ztlig.x_ftp.pwd | 字符串 | ztlig | X2/X3 FTP/SFTP 登录密码 | C |
| ztlig.dbLeaID | 整数 | 0 | 多 TMC 模式：0=不开启, >0=开启 | M |
| ztlig.kafka_operations_topic | 字符串 | metric_report | 推送进程信息的 Kafka topic | O |
| ztlig.kafka_operations_brokers | 字符串 | | 推送进程信息 Kafka IP:Port | O |

## 2. LICENSE 部分

| 配置项 | 含义 | 说明 |
|--------|------|------|
| max_target | 最大设控目标数 | License 控制 |
| max_lea | 最大监听中心个数 | License 控制 |
| max_vne | 最大虚拟网元个数 | License 控制 |
| ztlig_drs | 容灾备份功能 | 0=不支持, 1=支持 |
| zte_lis_v3 / zte_lis_v4 | ZTE LIS 接口 | 0=关闭, 1=开启 |
| zte_ne_v3 / zte_ne_v4 | ZTE NE 接口 | 0=关闭, 1=开启 |
| eric_lis_v1 / eric_lis_v2dot1 | Ericsson LI-IMS 接口 | 0=关闭, 1=开启 |
| **hw_ne** | **Huawei NE 接口** | **0=关闭, 1=开启** |
| nsn_ne / utimaco_ne / uag_ne / group2k_ne / zeel_ne | 其他厂商接口 | 0=关闭, 1=开启 |
| alu_ne | ALU NE 接口 | 0=关闭, 1=开启 |

## 3. NE-COM（物理网元配置）

NE(x) 配置块定义每个物理网元的对接参数，x 为 tneid。

| 配置项 | 类型 | 默认值 | 含义 | 需重启 | 属性 |
|--------|------|--------|------|--------|------|
| tneid | 整数 | 1 | 网元编号 [1-100] | 所有进程 | M |
| vendor | 字符串 | 空 | 厂商：zte/hw/ericsson/nsn/utimaco/uag/group2k/zeel | 所有进程 | M |
| version | 字符串 | 空 | 版本列表：zte_v3/v4/hw_cs/hw_ps/hw_epc/hw_ngn/... | 所有进程 | M |
| valid_fg | 整数 | 0 | 网元是否有效 [0-1] | 所有进程 | M |
| x1_ip | IP | 0.0.0.0 | X1 接口 IP（zte_v3 不需要）| ZTLIG1 | M |
| x1_port | 整数 | 1 | X1 接口端口 [1-65535] | ZTLIG1 | M |
| x1_user | 字符串 | 空 | X1 用户名（zte_v3/zte_v3_lis/nsn_LIPV1 不需要）| ZTLIG1 | C |
| x1_pwd | 字符串 | 空 | X1 密码（Utimaco: 8-15位含2字母+2数字）| ZTLIG1 | C |
| x1_transtype | 字符串 | | X1 传输方式：tcp/http/ssh/https | ZTLIG1 | M |
| x2_transtype | 字符串 | 空 | X2 传输方式：sftp/ftp/tcp/udp | ZTLIG2 | M |
| x2_ip | 字符串 | 空 | X2 接口 IP | ZTLIG2 | M |
| filenamerule | 字符串 | Method_B | X2 文件命名方式（ftp/sftp 需要）| ZTLIG2 | C |
| x3_transtype | 字符串 | tcp | X3 传输方式：tcp/udp/ftp | ZTLIG3 | M |
| x3_ip | 字符串 | 空 | X3 接口 IP | ZTLIG3 | M |
| trace_type | 整数 | 1 | 追踪激活方式 [0-1]（hw_cs/zte_v3/zte_v3_lis 需要）| ZTLIG1 | C |

## 4. VNE-COM（虚拟网元配置）

VNE(x) 配置块定义虚拟网元参数。

| 配置项 | 类型 | 默认值 | 含义 | 需重启 | 属性 |
|--------|------|--------|------|--------|------|
| tneid | 整数 | 1 | 所属物理网元编号 [1-100] | 所有进程 | M |
| vneid | 整数 | 1 | 虚拟网元编号 [1-1000]（不同 NE 下不重复）| 所有进程 | M |
| vne_type | 字符串 | | 网元类型：MSCs/MSCe/SGSN/GGSN/PDSN/iHLR/HLRe/HSS/MME/SGW/PGW/VOLTE/IMS/GSM/LTE | 所有进程 | M |
| operid | 字符串 | 空 | 2 口报告 opid（若 ztlig2.x.operid 有效则后者优先）| ZTLIG2 | C |
| hi2_neid | 字符串 | 空 | 2 口报告 neid（网元实际 ID）| ZTLIG2 | M |
| speechtype | 整数 | 0 | 语音处理：0=合并, 1=分离, 5=分割两话单（ZTE V4 LIS）| ZTLIG1 | M |
| incptType | 整数 | 1 | 监听类型：1=IRI, 2=CC, 3=IRI+CC（AGCF/SBC=3, IMS/GTAS=1）| ZTLIG1 | M |
| ulicver | 整数 | 1 | 3 口 ULIC 头版本 [0-1]（Ericsson/zte_v3_lis/nsn_lis 需配置）| ZTLIG3 | M |

## 5. LEA（监听中心配置）

LEA(x) 配置块定义监听中心对接参数。

| 配置项 | 含义 | 需重启 |
|--------|------|--------|
| leaid | 监听中心编号 [1-8] | 所有进程 |
| li_standard | 监听标准（kafkaowls） | 所有进程 |
| cc_addr / cc_type | CS 域 3 接口地址/类型（ISUP）| ZTLIG1 |
| redis_ipport | OWLS Redis IP | 所有进程 |
| kafka_realtime_brokers | 实时 Kafka 集群 IP | 所有进程 |
| kafka_realtime_group | 实时 Kafka 消费组 | ZTLIG1 |
| kafka_realtime_targetTopic | 设控请求 topic | ZTLIG1 |
| kafka_realtime_resultTopic | 设控响应 topic | ZTLIG1 |
| kafka_realtime_cdrTopic | 2 口报告 topic | ZTLIG2/RVF |
| kafka_offline_brokers | 离线 Kafka 集群 IP | ZTLIG2/RVF |
| kafka_offline_cdrTopic | 离线 2 口报告 topic | ZTLIG2/RVF |
| kafka_specialtarget_Topic | 码流分享特殊 target topic | ZTLIG1 |
| sftp_specialtarget_ip/port/user/pwd | 码流分享 SFTP 服务器 | ZTLIG2/SSF/RVF |
| securityredis_flag | Redis 安全认证 [0-1] | ZTLIG1 |
| redis_password | Redis 密码 | ZTLIG1 |
| hi2_sessionmange | 2 口会话管理 [0-1] | ZTLIG2 |
| sicms_recvmac | SI 侧 MAC 地址 | ZTLIG3 |
| rvf_voicepath | 语音文件落地路径 | RVF |

## 6. ZTLIG1（设控进程）

| 配置项 | 类型 | 默认值 | 含义 | 需重启 | 属性 |
|--------|------|--------|------|--------|------|
| ip | IP | 0.0.0.0 | 内部 TCP 通信 IP | 所有进程 | M |
| port | 整数 | oam分配 | 内部 TCP 通信端口 [10010-11999] | 所有进程 | M |
| x1_ip | 字符串 | 空 | X1 接口 IP（hw_ps/nsn_lipv1 需要）| ZTLIG1 | C |
| x1_port | 字符串 | 空 | X1 接口端口 | ZTLIG1 | C |
| db_ip | IP | 0.0.0.0 | 数据库 IP | ZTLIG1 | M |
| syn_night | 整数 | 1 | 夜间三方同步（bit0=hw, bit1=zte, bit2=ericdot21, bit3=nsn, bit4=utimaco, bit5=mavenir, bit6=g2k, bit7=zeel）| ZTLIG1 | M |

## 7. ZTLIG2（信令处理进程）

| 配置项 | 类型 | 默认值 | 含义 | 需重启 | 属性 |
|--------|------|--------|------|--------|------|
| ip / port | IP/整数 | oam分配 | 内部 TCP 通信 | ZTLIG2 | M |
| tneid | 字符串 | 空 | 对接 NE 序列（逗号分隔）| ZTLIG2 | M |
| leaid_port | 字符串 | 空 | LEA 端口映射（ftp/sftp 需要）| ZTLIG2 | C |
| x2_ip / x2_port | 字符串/整数 | 空 | X2 接口 IP/端口（仅 tcp 需要 x2_port）| ZTLIG2 | C |
| networkType | 整数 | 1 | 网元类型：1-CS/2-PS/3-EPC/4-IMS/5-5GC/11~14=CS_2G~5G/15~18=PS_2G~5G | ZTLIG2 | M |
| CallDuringBcd | 整数 | 0 | 通话时长 BCD 正/反序 [0-1] | ZTLIG2 | M |
| VoicePathTimeout | 整数 | 300 | 等待语音路径超时(s) | ZTLIG2 | M |
| CallSessionTimeout | 整数 | 3600 | 呼叫会话超时(s) | ZTLIG2 | M |
| SmsSessionTimeout | 整数 | 15 | 短信会话超时(s) | ZTLIG2 | M |
| operid | 字符串 | | 运营商 ID（配置后统一出值）| ZTLIG2 | M |

## 8. ZTLIG3（EPC 流量转接）

| 配置项 | 类型 | 默认值 | 含义 | 属性 |
|--------|------|--------|------|------|
| ip / port | IP/整数 | oam分配 | 内部 TCP 通信 | M |
| tneid | 字符串 | 空 | 对接 NE 序列（冒号分隔）| M |
| x3_ip / x3_port | 字符串/整数 | 空 | X3 接口 IP/端口 | C |
| x3_tunnel_port | 整数 | | ZTE 网元 X3 端口 | C |
| leaid_port | 字符串 | 空 | LEA 端口映射（ftp/sftp 需要）| C |
| sicms.sendmacpci | 字符串 | | LIG 侧 PCI 号（格式 0000:05:00.1）| O |
| sicms.proccore | 字符串 | 1,2 | DPDK 核心 | O |
| sicms.socketmem | 字符串 | 10,0 | DPDK 大页内存 | O |
| sicms.timeout | 整数 | 60 | 会话超时(s) | O |
| sicms.operid | 整数 | | SI 侧运营商 ID | O |
| hi2location_timeout | 整数 | 60 | 三码位置会话超时 [60-120] | O |

> SICMS 推送开启条件：sendmacpci + proccore + socketmem + timeout + operid **全部有效**

## 9. SSF（SIP-I 会话管理）

| 配置项 | 类型 | 默认值 | 含义 | 取值范围 |
|--------|------|--------|------|---------|
| ip / port | IP/整数 | 10.45.129.111/11300 | 内部 TCP 通信 | [10010-11999] |
| threadnum | 整数 | 2 | 处理线程数 | [2-10] |
| sessionnum | 整数 | 5000 | 每线程会话数 | [5000-20000] |
| siptimeout | 整数 | 1800 | SIP 会话超时(s) | [5-7200] |
| ztlig2seq | 字符串 | | 对接 ZTLIG2 进程序号（逗号分隔）| |
| sigip / sipUdpPort | IP/整数 | /5060 | SIP-I 信令 IP/端口 | |
| interfaceType | 整数 | 1 | 模式：1=sip_i, 2=102232-5, 3=mavenir, 4=ims_base, 5=102232-6 | [1-5] |
| isControlConnect | 整数 | 0 | 去振铃音 [0-1] | [0-1] |

## 10. 常用排障命令

```bash
# ztlig1 错误检查
cat ztlig1.{id}.txt.old | grep -i "error"

# ztlig2 Kafka 统计
show ztlig2 {id} kafka stat      # sendFailNum=0, sendSuccNum增长

# ztlig3 网卡统计
show ztlig3 {id} nic stat        # oerrors=0, obytes变动

# SSF 统计
show ssf {id} stat               # RecvNum 增长

# RVF 统计
show rvf {id} stat               # RecvTotalMsgLen增长, CurSessionNum变动

# 实时 CDR 查看
cat ztlig2.{id}.txt | grep EncodeToJson | tail

# 按 LIID 过滤
cat ztlig2.*.txt | grep EncodeToJson | grep '"LIID":"8070"'

# 确认 hi2_neid
cat ztlig2.{id}.txt | grep EncodeToJson | \
  awk -F 'Neid":"' '{print $2}' | awk -F '","CaptureTime' '{print $1}' | sort | uniq
```

## 11. 抓包命令

| 进程 | 场景 | 命令 |
|------|------|------|
| ztlig2 | TCP/UDP | `tcpdump -i {网卡} port {x2_port} -s 0 -w ztlig2_{进程号}_{时间戳}.pcap` |
| ztlig2 | FTP | `tcpdump -i {网卡} -s 0 -w ztlig2_{进程号}_{时间戳}.pcap` |
| SSF | SIP-I | `tcpdump -i any port {sipUdpPort} -s 0 -w SSF_{进程号}_{时间戳}.pcap` |
| RVF | sdpport | `tcpdump -i any port "20000 or 20002 or 20004" -s 0 -w RVF_{进程号}_{时间戳}.pcap` |
| RVF | x3port | `tcpdump -i any port {x3port} -s 0 -w RVF_{进程号}_{时间戳}.pcap` |

## 12. 配置属性说明

| 属性 | 含义 |
|------|------|
| C | 必配，配置不正确会影响功能 |
| M | 重要属性，需谨慎修改 |
| O | 可选属性 |
