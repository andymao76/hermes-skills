# ZTLIG 调试流程与问题排查方法论

> 基于二进制符号分析 + 配置文件分析 + 现场部署经验总结

## 一、问题分类

| 类别 | 现象 | 涉及进程 |
|------|------|----------|
| **设控失败** | Kafka 下发后目标未生效 | ZTLIG-1, NE, Redis |
| **无数据上报** | OWLS 收不到拦截 CDR | ZTLIG-2, X2 通道, Kafka |
| **语音文件问题** | 无语音/无声/单声道 | RVF, SSF, RTP |
| **Kafka 异常** | 消息丢失/拓扑变化 | ZTLIG-1/2/3, Kafka brokers |
| **进程崩溃** | 进程退出/core dump | 任意进程 |

## 二、调试工具矩阵

| 工具 | 用途 | 示例 |
|------|------|------|
| **ztsh CLI** | 进程内统计/调试开关 | `show ztlig2 460 stat` |
| **进程日志** | 错误定位 | `tail -f ztlig2.460.txt \| grep error` |
| **Kafka 消费** | 检查消息流 | `kafka-console-consumer.sh --topic TMC_TARGET_INFO` |
| **tcpdump** | 网络抓包 | `tcpdump -i any port 8460` |
| **Wireshark** | 协议分析 | ASN.1/BER/SIP 解码 |
| **GDB** | Core dump 分析 | `gdb ztlig2 core.xxx` |
| **ss** | 端口连通性 | `ss -tlnp \| grep 10300` |
| **/proc** | 进程资源 | `cat /proc/<pid>/status` |

> 注意: ZTLIG 二进制含 `debug_info, not stripped`，可直接 GDB 断点调试

## 三、标准 5 步排查流程

```
Step 1: 进程状态          ps aux | grep ztlig
Step 2: 配置检查          检查 ztlig.cfg 各段落
Step 3: 端口连通性        ss -tlnp | grep <port>
Step 4: 日志分析          grep -i error ztlig*.txt
Step 5: 抓包分析          tcpdump/Wireshark
```

### Step 1: 进程状态

```bash
ps aux | grep -E 'ztlig|cmf|ssf|rvf|psm'
# 检查所有 8 个进程是否都在运行
# 重点: ztlig1 (设控入口), ztlig2 (信令处理), ztlig3 (X3)
```

### Step 2: 配置检查

```bash
# 检查各段落是否完整
grep '^\[' ztlig.cfg

# 检查 ZTLIG2 实例数与 NE ID 映射
grep -A2 'ztlig.ztlig2' ztlig.cfg | grep 'tneid'

# 检查 LEA Kafka 配置
grep 'kafka.*broker' ztlig.cfg
```

### Step 3: 端口连通性

```bash
# 检查内部 TCP 端口
ss -tlnp | grep -E '10300|1046[0-9]|10480|1130[0-9]|1140[0-9]'

# 检查 X1/X2/X3 对外端口
ss -tlnp | grep -E '50000|8460|888[0-9]|8480|990[0-9]'
```

### Step 4: 日志分析

```bash
# 抓取错误日志
grep -i 'error\|fail\|alarm' ztlig1.300.txt | tail -50

# 追踪特定 LIID
grep 'LIID\":\"12345' ztlig2.460.txt

# 检查 Kafka 发送统计
grep 'sendSucc\|sendFail' ztlig2.460.txt
```

### Step 5: 抓包分析

```bash
# X2 TCP 抓包
tcpdump -i any port 8460 -w x2.pcap

# X3 SIP 抓包
tcpdump -i any port 9900 -w sip.pcap

# RTP 语音抓包
tcpdump -i any portrange 20000-20010 -w rtp.pcap
```

## 四、分场景排查

### 4.1 设控失败

```
① Kafka TMC_TARGET_INFO topic 是否有消息？
   → kafka-console-consumer --bootstrap-server ... --topic TMC_TARGET_INFO --from-beginning

② ZTLIG-1 日志是否收到？
   → grep 'AddTarget\|DelTarget' ztlig1.300.txt

③ X1 端口连通性
   → telnet <NE_IP> <x1_port>

④ 网元侧账号/密码
   → 核对 ztlig.cfg 中 x1_user/x1_pwd

⑤ License 检查
   → 确认 ztlig_lic.key 中有 eric_lis_v2dot1=1 (爱立信)

⑥ Redis 同步状态
   → redis-cli -h <redis_ip> keys 'target:*'
```

### 4.2 无数据上报

```
① ZTLIG-2 进程是否运行？
   → ps aux | grep ztlig2

② X2 端口 (TCP/UDP/FTP) 连通性
   → ss -tlnp | grep <x2_port>

③ 厂商解码插件是否正确加载？
   → ldd ztlig2 | grep <vendor>   # 应该显示已加载

④ Kafka OWLS_TMC topic 消费端状态
   → kafka-consumer-groups --bootstrap-server ... --group ... --describe

⑤ 会话超时参数
   → 检查 CallSessionTimeout/SmsSessionTimeout/VoicePathTimeout
```

### 4.3 语音文件问题

```
① SSF 是否收到 SIP 信令？
   → tcpdump -i any port <sipUdpPort>

② RVF 是否收到 RTP？
   → tcpdump -i any portrange <voicesdpport>

③ 语音文件是否生成？
   → ls /data01/voice/<operator>/
   → 检查 .fin 文件存在

④ 编解码问题
   → ffprobe <voice_file>    # 确认编码格式
```

### 4.4 Kafka 异常

```bash
# 检查 Kafka brokers 连通性
echo "test" | kafka-console-producer --broker-list ... --topic test

# 检查 topic 是否存在
kafka-topics --bootstrap-server ... --list

# 检查消费者组延迟
kafka-consumer-groups --bootstrap-server ... --group ... --describe
```

### 4.5 进程崩溃

```bash
# 检查 core dump
ls -lh /var/core/ /corefile/

# 设置 core dump
ulimit -c unlimited
echo '/var/core/core.%p.%e' > /proc/sys/kernel/core_pattern

# GDB 分析
gdb /usr/local/bin/ztlig2 /var/core/core.12345
# (gdb) bt full
# (gdb) info registers
# (gdb) thread apply all bt

# 检查系统日志
dmesg | tail -20 | grep -i 'oom\|kill\|segfault'
```

## 五、常见错误速查

| 错误 | 原因 | 处理 |
|------|------|------|
| `LeaIdx invalid` | 1口 LEAID 与实际不符 | 检查 ztlig_target.txt 和 cfg |
| `the ne is unlawful` | tneid 未加到 2口配置 | 配置 ztlig.ztlig2.{id}.tneid |
| `get actneID fail` | vneid 不存在 | 检查 vne/ne 配置 |
| `vneid[0] not support` | hi2_neid 未配置 | 确认 hi2_neid |
| alarm-id=504 | X1 认证失败 | 核对用户名/密码/NEID |
| alarm-id=512 | X1 通道中断 | 检查网络/防火墙 |
| ReturnCode 28 | LIID 无效 | LIID 只能 0~9 数字（子地址模式）|
| connect refused | X1 端口不通 | 防火墙/NE 侧服务 |
| session invalid | 爱立信 SOAP session 过期 | 重新 Login (5min 超时) |
| GGSNMonitoring=1 | PS 网元不支持 | 改配 GGSNMonitoring=0 |

## 六、ztsh CLI 常用命令

```bash
# 统计信息
show ztlig2 {id} mainframe stat
show ztlig2 {id} hi2 stat
show ztlig2 {id} x2 stat
show ztlig2 {id} kafka stat
show ztlig3 {id} hi3 stat
show ztlig3 {id} nic stat

# 调试开关
debug ztlig2 {id} ftp (on|off)
debug ztlig2 {id} hw x2 (on|off)
debug ztlig1 {id} ericlis21 (on|off)

# 抓包
capture ztlig2 {id} msg on <file_count> <file_size_MB>
capture ztlig2 {id} msg off

# 目标管理
write ztlig2 {id} target file
syn ztlig1 {id} hwmsc <leaid> <vneid>
start ztlig1 {id} ztev4lis <leaid> <vneid> list

# 重置统计
clear ztlig2 {id} stat
```
