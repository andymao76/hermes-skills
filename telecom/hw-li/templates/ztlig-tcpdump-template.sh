#!/bin/bash
# ZTLIG tcpdump 抓包模板
# 使用方法: 按需取消注释对应场景

# === ztlig2 X2 口抓包 ===
# TCP/UDP 模式指定端口
# tcpdump -i {网卡} port {x2_port} -s 0 -w "ztlig2_{进程号}_$(date +'%Y%m%d_%H%M%S').pcap"

# === SSF SIP-I 信令抓包 ===
# tcpdump -i any port {sipUdpPort} -s 0 -w "SSF_{进程号}_$(date +'%Y%m%d_%H%M%S').pcap"

# === RVF RTP 抓包 (SIP-I模式, sdpport范围) ===
# tcpdump -i any port "{port1} or {port2} or {port3}" -s 0 \
#   -w "RVF_{进程号}_$(date +'%Y%m%d_%H%M%S').pcap"

# === RVF RTP 抓包 (TS-102232/Mavenir模式, x3port固定) ===
# tcpdump -i any port {x3port} -s 0 -w "RVF_{进程号}_$(date +'%Y%m%d_%H%M%S').pcap"
