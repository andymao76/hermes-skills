---
name: network-troubleshooting
description: 网络排障专家 — TCP/UDP 诊断/路由追踪/防火墙规则/DNS 排查/代理连通性检测。
priority: normal
category: devops
---

# 网络排障专家

Linux 网络排障标准流程。覆盖 TCP、UDP、防火墙、路由、DNS、代理六大场景。

## 诊断第一步：区分故障域

用户说"连不上网"时，先区分是**完全断网**还是**仅外网不通**：

```bash
# 国内网站
curl -s -o /dev/null -w "HTTP %{http_code} - %{time_total}s\n" --connect-timeout 5 https://www.baidu.com

# 国外网站（走代理）
curl -s -o /dev/null -w "HTTP %{http_code} - %{time_total}s\n" -x http://127.0.0.1:7897 --connect-timeout 5 https://www.google.com
```

**判定表：**

| Baidu | Google (走代理) | 结论 |
|-------|-----------------|------|
| ✅ 200 | ✅ 200 | 整体正常，问题在应用层 |
| ✅ 200 | ❌ 超时 | **代理问题** → 检查 Clash 节点/端口 |
| ❌ 超时 | ❌ 超时 | **基础网络问题** → 从物理层开始排查 |

---

## 物理层诊断（排障起点）

在排查路由/DNS/防火墙之前，**先确认网线/网卡物理层是否正常**：

```bash
# 1. 接口状态 — 检查 LOWER_UP 和 NO-CARRIER
ip link show <interface>

# 关键标识：
#   <NO-CARRIER,... state DOWN>  → 物理链路断开（网线/交换机问题）
#   <...LOWER_UP,... state UP>    → 物理链路正常

# 2. ethtool 确认链路
ethtool <interface> | grep -E "Link detected|Speed|Duplex"

# 正常:  Link detected: yes,  Speed: 1000Mb/s,  Duplex: Full
# 异常:  Link detected: no,   Speed: Unknown!,  Duplex: Unknown! (255)

# 3. carrier 文件
cat /sys/class/net/<interface>/carrier
# 1 = 有载波, 0 = 无载波

# 4. 查看所有接口
nmcli device status
```

**`NO-CARRIER` 的常见原因：**
- 网线没插紧或损坏
- 对端交换机/路由器端口 down 或未供电
- 网线类型不匹配（直连 vs 交叉，现代设备一般自适应）

---

## 双网卡/多路由诊断

当机器同时有 WiFi 和有线时，默认路由优先级是关键：

```bash
# 查看所有默认路由（按 metric 排序）
ip route show default

# 输出示例：
#   default via 192.168.0.1 dev wlp1s0  metric 600      ← WiFi 优先
#   default via 192.168.1.1 dev enp2s0  metric 20100    ← 有线优先级低
```

**Metric 值越小优先级越高**。正常情况有线（ethernet）的 metric 应小于 WiFi（100 vs 600）。如果有线 metric 异常高（如 20100），说明：

1. 静态 IP 配置的网关不可达 → NM 自动抬高 metric
2. 或 netplan/NetworkManager 配置异常

```bash
# 验证网关是否可达
arp -n | grep <gateway_ip>
# (incomplete) = 网关不存在，无人响应 ARP

# 检查 NM 连接配置
nmcli -f ipv4.method,ipv4.gateway,ipv4.addresses,ipv4.route-metric connection show <profile>
```

### "有线只通局域网 + WiFi 通外网" 的拆分模式

当有线配置了静态 IP 但网关不存在时，系统自动用 WiFi 的默认路由上网。这是一种可用的**拆分网络拓扑**：

```
🌐 外网 → Clash 代理 (127.0.0.1:7897) → WiFi (metric 600)  ✅
🖥️ 局域网 → 有线 enp2s0 直连 (192.168.1.53)           ✅
```

不需要修复只要满足：
- 有线只用于局域网通信（同网段设备互通）
- WiFi + Clash 提供外网访问
- 两条默认路由互不干扰（metric 不同）

---

## netplan 静态 IP 排查

Ubuntu 24 上 cloud-init/netplan 可能留下过时的静态 IP 配置：

```bash
# 查看 netplan 配置
ls /etc/netplan/*.yaml

# NM 连接详情（无需 root）
nmcli -s connection show <profile>

# 检查是否为手动 IP
# ipv4.method: manual  → 静态配置
# ipv4.method: auto    → DHCP
```

常见问题：`netplan-enp2s0` 这种 profile 来自 cloud-init 初始部署，IP/网关是当时环境的值，换到不同网络后就失效了。

---

## 标准诊断命令

```bash
# 连接监听
ss -lntp      # TCP 监听端口（推荐代替 netstat）
ss -lnup      # UDP 监听端口
ss -antp      # 所有 TCP 连接（含进程）
ss -s         # 连接统计（Established/TimeWait/CloseWait）

# 路由
ip route show                  # 路由表
ip route get <target_ip>       # 特定目标路由
traceroute -n <target_ip>      # 路径追踪
mtr -r -c 10 <target_ip>       # 持续路径追踪

# 防火墙
iptables -L -n -v              # iptables 规则
iptables -t nat -L -n -v       # NAT 规则
nft list ruleset               # nftables 规则

# DNS
nslookup <domain>              # DNS 解析
dig <domain>                    # DNS 详细查询
dig +short <domain>             # 仅 IP
host <domain>                   # 主机查询

# 代理连通性
curl -v --proxy http://proxy:port https://www.google.com
curl -x socks5://proxy:port https://www.google.com
```

## 常见问题诊断流程

### TCP 连接超时
```bash
# 1. 检查目标是否可达
ping -c 3 <target>

# 2. 检查目标端口是否开放
nc -zv -w 3 <target> <port>
timeout 3 bash -c "echo > /dev/tcp/<target>/<port>" && echo "open" || echo "closed"

# 3. 检查中间防火墙
traceroute -T -p <port> <target>
```

### DNS 解析失败
```bash
# 1. 确认 DNS 配置
cat /etc/resolv.conf

# 2. 测试不同 DNS
dig @114.114.114.114 <domain>
dig @8.8.8.8 <domain>

# 3. 检查 hosts 文件
grep <domain> /etc/hosts
```

### 代理不生效
```bash
# 1. 确认代理环境变量
echo "$http_proxy $https_proxy $no_proxy"
env | grep -i proxy

# 2. 测试代理连通性
curl -v --proxy http://127.0.0.1:7897 https://www.google.com

# 3. 检查 Clash Verge
ss -lntp | grep clash
```
