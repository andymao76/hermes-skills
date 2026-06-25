---
name: tcpdump-analysis
description: tcpdump 抓包分析专家 — 流量采集/协议解析/SIP RTP 分析/PCAP 文件分析/通信信令排障。
priority: normal
category: devops
---

# tcpdump 抓包分析专家

tcpdump 抓包分析，特别是针对通信行业场景（SIP、RTP、SIP-I、AMR-WB、PCMA）。

## 基础抓包命令

```bash
# 指定接口 + 写入文件
tcpdump -i bond1 -s 0 -w capture.pcap

# 指定端口（SIP 通常 5060）
tcpdump -i bond1 port 5060 -w sip.pcap

# 指定主机
tcpdump -i bond1 host 192.168.1.100 -w host.pcap

# 环形缓冲（限制文件大小）
tcpdump -i bond1 -C 100 -W 10 -w capture.pcap
# 每个文件 100MB，最多 10 个
```

## SIP 信令分析

```bash
# 只抓 SIP 协议
tcpdump -i bond1 -s 0 port 5060 -X -vv

# 查看 SIP 信令流
tcpdump -i bond1 -s 0 -A port 5060 | grep -E "INVITE|200 OK|BYE|REGISTER"

# 分析特定 Call-ID
tcpdump -r capture.pcap -A | grep -A 5 -B 5 "Call-ID: xxxxxx"

# 使用 tshark 深度分析
tshark -r capture.pcap -Y "sip" -T fields -e sip.msg.method -e sip.call_id
tshark -r capture.pcap -Y "sip.Request-Line contains INVITE" -T fields -e sip.from.user -e sip.to.user
```

## RTP 媒体流分析

```bash
# 识别 RTP 流
tcpdump -r capture.pcap portrange 10000-20000 -X | head -50

# tshark RTP 分析
tshark -r capture.pcap -Y "rtp" -T fields -e rtp.payload_type -e rtp.ssrc -e rtp.timestamp

# RTP 负载类型
# 0 = PCMU, 3 = GSM, 8 = PCMA, 9 = G722
# 98 = AMR-WB, 102 = AMR-NB

# 查看 RTP 流统计
tshark -r capture.pcap -z rtp,streams
```

## 通信协议速查

| 协议 | 默认端口 | 用途 |
|------|----------|------|
| SIP | 5060/UDP, 5061/TLS | 会话初始协议 |
| SCTP | 2905 | SIGTRAN 信令传输 |
| RTP | 10000-20000 | 实时传输协议 |
| RTCP | RTP+1 | RTP 控制协议 |
| DNS | 53 | DNS |
| Diameter | 3868 | 认证计费 |
| GTP-C | 2123 | 3G/4G 控制面 |
| GTP-U | 2152 | 3G/4G 用户面 |

## 性能分析

```bash
# 流量统计
tcpdump -r capture.pcap -nn | awk '{print $3}' | cut -d. -f1-4 | sort | uniq -c | sort -rn | head -10

# 包大小分布
tcpdump -r capture.pcap -nn | awk '{print $NF}' | sed 's/.*length //' | awk '{if($1>1500) print ">1500"; else if($1>500) print "500-1500"; else print "<500"}' | sort | uniq -c

# 通信场景通用过滤
tcpdump -i bond1 "port 5060 or portrange 10000-20000 or port 53"
```
