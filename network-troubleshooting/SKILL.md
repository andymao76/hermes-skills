---
name: network-troubleshooting
description: 网络排障专家 — TCP/UDP 诊断/路由追踪/防火墙规则/DNS 排查/代理连通性检测/ARP Flux 双网卡排障。
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

### ARP Flux 诊断（双网卡同网段）

当 WiFi 和有线**属于同一子网**（如都是 192.168.1.0/24）时，Linux 内核可能出现 ARP Flux：同一个 IP 在两个接口上都有 Neighbor Entry，导致回包走错接口。

**典型现象：**
- Ping/SSH 部分客户端正常、部分超时（不同客户端的 ARP/Neighbor Cache 学习时间差异）
- ARP 能学到 MAC，但 ICMP/TCP 不通
- tcpdump 发现：请求从 A 口进入，回包从 B 口发出（对端 MAC 不在 B 口 → ARP FAILED）

**排障流程：**

```
# 1. 确认双网卡同网段
ip route show table all | grep <subnet>
# 两个接口都出现 192.168.1.0/24 → 典型条件

# 2. 检查邻居表
ip neigh
# 同一 IP 在两个接口上分别有 STALE 和 FAILED → ARP Flux

# 3. tcpdump 验证回包路径
sudo tcpdump -ni any host <客户端IP>
# 检查 Request 入口和 Reply 出口是否一致

# 4. 快速验证（关闭一个接口）
sudo ip link set <接口名> down
# 如果立即恢复 → 根因确认
```

**根因：** Linux 路由查表后选择默认路由出去的接口，而非收到请求的接口。两个默认路由（via 同一网关）分布在两个接口 → 回包可能从 B 口出去，而客户端 MAC 只在 A 口的 Neighbor Entry 中。

**推荐方案（★★★★★）：不同子网隔离**
- WiFi → 192.168.1.x（办公/家庭网络）
- 有线 → 192.168.250.x（实验/管理网络）

Netplan 配置示例：
```yaml
ethernets:
  enp2s0:
    addresses: [192.168.250.53/24]  # 不同子网
wifis:
  wlp1s0:
    addresses: [192.168.1.77/24]
    routes: [{to: default, via: 192.168.1.1}]
```

**临时缓解（不推荐长期）：** arp_ignore=1 + arp_announce=2 + rp_filter=2

**排查路线图：** SSH 失败 → Ping 失败 → ARP 正常 → tcpdump 发现 Request 入口 ≠ Reply 出口 → 路由表确认双接口同网段 → 关闭一个接口立即恢复 → 根因 ARP Flux

### 默认路由优先级与 Metric

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
