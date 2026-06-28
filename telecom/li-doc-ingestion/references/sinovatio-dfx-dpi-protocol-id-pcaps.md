# Sinovatio DFX DPI 协议识别 PCAP 分析参考

创建：2026-06-28
来源：/home/andymao/PCAP/DPI/
关联：li/Sinovatio/DFX/dfx-bypass-training.md（培训文档）, li/Sinovatio/DFX/dfx-bypass-pcaps.md（PCAP 分析）

## 目录结构

```
/home/andymao/PCAP/DPI/
├── 五元组ip.pcap     — WhatsApp (69.171.250.52:443)
├── http-host.pcap     — TikTok (xlog-va.musical.ly)
├── https-sni.pcap     — Instagram (i.instagram.com)
├── quic-sni.pcapng    — YouTube (redirector.googlevideo.com)
├── 协议插件.pcap      — 微信 WeChat (16 f1 03 00)
└── 组合条件.pcap      — FacebookMessage (SNI + CN)
```

## 各 PCAP 快速定位

### 五元组ip.pcap — WhatsApp
- 特征：`ip.addr == 69.171.250.52`
- 时间：2019-08-06 14:31:40
- 流：192.168.23.4:48835 → 69.171.250.52:443
- 验证：与培训文档描述完全吻合 ✓
- 注意：需区分 whatsapp（普通）和 whatsapp_call（语音）的流量特征

### http-host.pcap — TikTok
- 特征：`http.host == "xlog-va.musical.ly"`
- 时间：2019-08-05 14:11:29
- 流：192.168.23.14:45476 → 47.252.92.254:80
- HTTP Request：GET /v2/s?os=0&... → Host: xlog-va.musical.ly
- UA：com.zhiliaoapp.musically/2019080210 (Android 8.1.0)
- 私有头：X-Gorgon, X-Khronos, X-Tt-Trace-Id
- 验证：完全吻合 ✓

### https-sni.pcap — Instagram
- 特征：`tls.handshake.extensions_server_name == "i.instagram.com"`
- 时间：2019-08-06 09:30:29
- 流：192.168.23.3:47332 → 157.240.24.63:443
- SNI 偏移 0x00d0：`692e 696e 7374 6167 7261 6d2e 636f 6d` → `i.instagram.com`
- TLS 1.3, ALPN: h2, h2-fb, http/1.1
- 验证：完全吻合 ✓

### quic-sni.pcapng — YouTube
- 特征：`gquic.tag.sni == "redirector.googlevideo.com"`
- 时间：2019-08-06 16:16:38
- 流：192.168.100.167:20830 → 31.13.69.86:443 (UDP)
- QUIC CHLO 包，SNI 偏移 0x0388：`...redirector.googlevideo.com`
- UA：Cronet/82.0.4057.2 (Android YouTube)
- 注意：tcpdump 不解析 QUIC 协议层，需手动看 hex 中的 SNI tag
- 验证：完全吻合 ✓

### 协议插件.pcap — 微信 WeChat
- 特征：TCP payload 前4字节固定 `16 f1 03 00`
- 时间：2019-08-06 15:12:25
- 流：172.27.35.9:34418 → 14.215.158.119:80
- 第5字节 `a1` = 161 = TCP payload 长度(166) - 5
- 注意：走 80 端口但非 HTTP，需协议插件识别
- 验证：完全吻合 ✓

### 组合条件.pcap — FacebookMessage
- 特征：HTTPS SNI + Common Name 组合
- 时间：2019-08-06 13:50:48
- 流：192.168.23.2:43471 → 3.121.98.171:443
- 条件1 SNI：`ec2-3-121-98-171.eu-central-1.compute.amazonaws.com`
- 条件2 Cert CN：`*.internet.org`（Internet.org 是 Facebook 旗下）
- 注意：单靠 SNI（AWS 通用主机名）无法唯一识别，必须组合 CN
- 验证：完全吻合 ✓

## 常用 tcpdump 命令

```bash
# 查看报文概览（自动解析 HTTP/TLS）
tcpdump -nr <file> -v

# 查看 hex dump（定位精确偏移）
tcpdump -nr <file> -X

# 只看前 N 个包
tcpdump -nr <file> -c 5 -v

# 过滤特定 IP 或端口
tcpdump -nr <file> host 69.171.250.52
tcpdump -nr <file> port 80
```

## HEX 中寻找 SNI/特征码的技巧

- **HTTPS SNI**：在 TLS Client Hello 中搜索域名 ASCII 码（如 `i.instagram.com` → `69 2e 69 6e ...`）
- **QUIC SNI**：在 CHLO 包中搜索 `SNI` 标签（4字节 ASCII），随后 2 字节为长度，再后为域名
- **HTTP Host**：tcpdump `-v` 自动解析 HTTP 协议，直接显示 Host 字段
- **协议插件魔数**：TCP 三次握手后的第一个 PUSH 包负载的前几个字节
