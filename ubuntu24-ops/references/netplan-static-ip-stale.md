# Netplan/Cloud-Init 遗留静态 IP 诊断（Ubuntu 24.04 实际输出示例）

## 背景

2026-06-23 现场诊断：用户插好网线后，`enp2s0` 链路 UP（LOWER_UP），但无法访问外网。
最终发现是 cloud-init 遗留的 `netplan-enp2s0` 静态 IP 配置指定了不存在的网关。

## 完整诊断命令链

### 1. 接口状态（链路正常）

```bash
$ ip link show enp2s0
2: enp2s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    link/ether 00:e0:4c:dc:03:be brd ff:ff:ff:ff:ff:ff
```

关键信号：`UP,LOWER_UP` + `state UP` — 物理链路正常。

### 2. 载波确认

```bash
$ cat /sys/class/net/enp2s0/carrier
1
```

### 3. ethtool 确认

```bash
$ ethtool enp2s0
...
    Speed: Unknown!          ← 但 link detected 实际是 yes
    Duplex: Unknown! (255)   ← 可能因 auto-negotiate 关闭
    Link detected: yes
```

注意：本场景中 `auto-negotiate: 否`（配置为关闭），但 `Link detected: yes`。

### 4. nmcli 设备状态

```bash
$ nmcli device status
DEVICE          TYPE      STATE         CONNECTION
enp2s0          ethernet  已连接        netplan-enp2s0
```

`已连接` + 配置名以 `netplan-` 开头 = **cloud-init 遗留配置**的强烈信号。

### 5. 连接配置详情

```bash
$ nmcli -f ipv4.method,ipv4.gateway,ipv4.addresses connection show netplan-enp2s0
ipv4.method:       manual
ipv4.gateway:      192.168.1.1
ipv4.addresses:    192.168.1.53/24
```

关键发现：`method=manual`（静态），网关 `192.168.1.1`。

### 6. 网关可达性

```bash
$ arp -n | grep enp2s0
192.168.1.1                      (incomplete)                              enp2s0
192.168.1.99             ether   00:e0:4c:68:07:82   C                     enp2s0

$ ping -c 2 -W 2 192.168.1.1
PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.
From 192.168.1.53 icmp_seq=1 Destination Host Unreachable
From 192.168.1.53 icmp_seq=2 Destination Host Unreachable
```

- `192.168.1.1` → ARP `(incomplete)` + ping `Destination Host Unreachable` — **网关不存在**
- `192.168.1.99` → 同网段其他设备（MAC 00:e0:4c:68:07:82）互通（0.24ms）

### 7. 路由 metric 异常

```bash
$ ip route show default
default via 192.168.0.1 dev wlp1s0 proto static metric 600
default via 192.168.1.1 dev enp2s0 proto static metric 20100
```

有线 metric = 20100 🔴 远超正常值的 100-600。这是 NetworkManager 自动对不可达路由降级的结果。WiFi metric 600 成为实际默认路由。

### 8. 代理/外网验证（确认外网能力）

```bash
# 通过 Clash 代理 → 正常
$ curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" -x http://127.0.0.1:7897 --max-time 5 https://www.google.com
HTTP 200 (0.43s)

# 直连百度 → 正常（走 WiFi）
$ curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" --connect-timeout 5 https://www.baidu.com
HTTP 200 (0.86s)

# 直连 Google → 不通（走有线，网关不存在）... 实际上也被代理拦截了
```

## Netplan 配置文件分布

本机发现的 netplan 文件（`/etc/netplan/`）：

```
50-cloud-init.yaml                       # cloud-init 主配置
90-NM-255dd5d0-...                       # NM 自动生成的单个连接配置
90-NM-289a5f43-...
90-NM-7ea6f90b-...                       # = netplan-enp2s0 (UUID: 7ea6f90b...)
...
```

每个 NM 连接配置对应一个 `90-NM-<uuid>.yaml`。`netplan-enp2s0` 的 UUID 是 `7ea6f90b-...`。

## 局域网设备

扫描发现 `192.168.1.99` 在线，MAC `00:e0:4c:68:07:82`（同厂商——与本机 `00:e0:4c:dc:03:be` 同一 OUI），TTL 200（可能是 NAS 或另一台 Linux 服务器）。

## 判断要点汇总

| 信号 | 含义 |
|------|------|
| 配置名 `netplan-<iface>` | cloud-init 遗留的 netplan/NM 混合配置 |
| `ipv4.method=manual` | 静态 IP（非 DHCP） |
| `arp -n` 显示 `(incomplete)` | 网关 IP 在本网段无人响应 ARP |
| `metric 20100` | NM 自动降级不可达的网关路由 |
| 同 OUI 的局域网设备 (00:e0:4c:xx:xx:xx) | Realtek 网卡，可能是同交换机下另一设备 |

## 参考

- 主 SKILL.md "场景二" — 修复方案和通用诊断流程
- `references/ethernet-physical-layer-diag.md` — 物理层 NO-CARRIER 场景
