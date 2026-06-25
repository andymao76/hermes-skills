# SIP OPTIONS 探测 — 用途、抓包与 Wireshark 过滤

## 本质

单向问答：发 OPTIONS → 收 200 OK。不建立会话，不产生 SDP 媒体协商，轻量级探测。

## 三大用途

1. **SIP keepalive** — 心跳探测，确认对端在线
2. **能力探测** — 看对方支持哪些编解码、扩展
3. **SBC / 负载均衡健康检查** — 轻量级探测（比对端发起 INVITE 省资源）

## 报文结构

```
OPTIONS sip:user@domain SIP/2.0
Via: SIP/2.0/UDP 10.55.2.11:5060
From: <sip:probe@domain>;tag=xxx
To: <sip:user@domain>
Call-ID: xxx@10.55.2.11
CSeq: 1 OPTIONS
Contact: <sip:probe@10.55.2.11>
Max-Forwards: 70
Content-Length: 0

← 200 OK (正常)
← 超时 / 503 (对端故障)
```

## 关键特点

| 特性 | 说明 |
|------|------|
| 不建立会话 | 不会产生 SDP 媒体协商，除非显式携带 SDP（一般不推荐） |
| 状态探测 | 对端挂掉会超时或返回 503 Service Unavailable |
| 轻量级 | 非常适合健康检查，资源消耗低 |
| 明文字符串 | SIP 是文本协议，OPTIONS 以明文在 UDP/TCP 5060～5133 上传输 |

## tcpdump 抓取命令

```
# 实时抓取 OPTIONS 消息
tcpdump -i bond1 -s 0 -A -nn portrange 5060-5132 | grep "OPTIONS"

# 参数说明
# -i bond1    → 指定网卡
# -s 0        → 抓完整包（不截断）
# -A          → ASCII 输出（可读）
# -nn         → 不解析域名和服务名
# portrange   → 只抓该端口范围内的 SIP 流量
```

## 实际运维操作

### 对接阶段
- 对接时开启 OPTIONS 探测，验证 SBC / P-CSCF / S-CSCF 之间的连通性
- 确认对端返回 200 OK 即表示 SIP 信令链路正常

### 对接完成后必须关闭
- OPTIONS 是一问一答的周期性消息，**如果允许它一直运行，会持续占用网络带宽和对端处理资源**
- 停用方法：停止相关的 OPTIONS 发送脚本或定时任务
- 检查是否有残留：`tcpdump -i bond1 -A -nn portrange 5060-5132 | grep OPTIONS`

### 后台持续抓包
```
# 启动后台抓包脚本
nohup /root/sip_options_roll.sh > /dev/null 2>&1 &

# 实时查看抓包内容
tail -f /root/sip_options.log

# 停止抓包
pkill -f sip_options_roll.sh
```

## Wireshark 过滤

| 场景 | 过滤表达式 |
|------|-----------|
| 仅 OPTIONS 消息 | `sip.Method == "OPTIONS"` |
| 特定端口范围 | `sip.Method == "OPTIONS" && udp.port >= 5060 && udp.port <= 5132` |
| 特定 IP | `sip.Method == "OPTIONS" && ip.addr == 10.55.2.11` |
| 只看请求 | `sip.Method == "OPTIONS" && sip.Request-Line` |
| 只看响应（200 OK） | `sip.Method == "OPTIONS" && sip.Status-Code == 200` |

### 非标准端口（5133 等）的 Wireshark 识别

SIP 默认端口是 5060，如果 SIP 运行在非标准端口（如 5133），Wireshark 不会自动解析为 SIP 协议，需要手动设置：

1. **菜单 → Analyze → Decode As…**
2. **Transport** 选 UDP
3. **端口号** 填 5133
4. **协议** 选 SIP
5. **确认**

设置后即可看到 INVITE、REGISTER、BYE、OPTIONS 等所有 SIP 消息。
