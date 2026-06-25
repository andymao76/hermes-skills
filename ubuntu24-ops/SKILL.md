---
name: ubuntu24-ops
description: Ubuntu 24.04 运维 — 接口诊断、网络排障（物理层+Netplan/Cloud-Init 静态IP）、PCIe AER 修复、桌面环境、Clash Verge、输入法、系统维护
category: devops
---

# Ubuntu24 Ops

Ubuntu 24.04 运维 — 涵盖物理层网络诊断、PCIe AER 修复、桌面环境、Clash Verge、输入法、系统维护。

## 网络接口故障排查（物理层到应用层）

### 适用场景

用户报告"插上网线后无法上网"或"有线网络不通"时使用。

### 一、快速链路检测

首先确认接口是否有物理载波：

```bash
# 查看接口状态
ip link show <iface>

# 结果中 <NO-CARRIER,... state DOWN> 表示物理层不通
# 结果中 <state UP> 且无 NO-CARRIER 表示链路正常

# Carrier 文件读取（更精确）
cat /sys/class/net/<iface>/carrier 2>/dev/null
# 1 = 物理链路正常, 0 = 无载波
```

### 二、ethtool 物理层诊断

```bash
ethtool <iface>
```

关键输出字段：

| 字段 | 正常值 | 异常值（链路不通） |
|------|--------|-------------------|
| `Link detected` | `yes` | `no` |
| `Speed` | `1000Mb/s` / `100Mb/s` | `Unknown!` |
| `Duplex` | `Full` / `Half` | `Unknown! (255)` |
| `Auto-negotiation` | `on` | `on`（即使不通也可能是 on） |

### 三、nmcli 设备状态查看

```bash
nmcli device status
```

状态含义：

| 状态 | 含义 |
|------|------|
| `已连接` | 链路正常且有 IP |
| `不可用` | **物理层无载波（NO-CARRIER）** — 软件无法修复 |
| `断开` | 有载波但未获取 IP 或手动 down |

查看已有连接配置：

```bash
nmcli connection show | grep ether
```

尝试激活有线连接（仅在链路已通时有效）：

```bash
nmcli device reapply <iface>
# 链路不通时会报：Device is not activated
```

### 四、路由验证

```bash
# 查看默认网关
ip route show default

# 从哪张网卡出去
ip route get 8.8.8.8
```

### 五、区分物理层 vs 代理层故障

同时测试代理和直连的外网连通性：

```bash
# 代理方式
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" -x http://127.0.0.1:<port> --max-time 10 https://www.google.com

# 直连方式
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" --noproxy '*' --max-time 10 https://www.baidu.com
```

### 六、Clash 端口确认

Clash Verge 的混合端口可能在配置文件中指定，不一定使用标准 7890：

```bash
cat ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml | grep mixed-port
```

常见端口值：`7897`（当前环境），其他可能见下方速查表。

系统代理设置查看：

```bash
gsettings get org.gnome.system.proxy mode
gsettings get org.gnome.system.proxy.http host
gsettings get org.gnome.system.proxy.http port
```

### 七、NO-CARRIER 处理

`NO-CARRIER` 是物理层问题，软件无法修复。检查项按优先级排列：

1. **网线两端是否插紧** — 电脑端和对端交换机/路由器
2. **对端设备端口指示灯** — 是否亮/闪烁
3. **对端设备是否供电正常** — 确认通电
4. **换根网线** — 网线内部断芯不可见
5. **换端口插** — 对端交换机的不同端口
6. **检查接口协商** — 如果对端强制 100M/full，本机也应协商一致

不推荐的修复尝试：
- ❌ `sudo ip link set <iface> down && sudo ip link set <iface> up` — 对 NO-CARRIER 无效
- ❌ 多次 nmcli device reapply — 无载波时永远失败
- ❌ NetworkManager 重启 — 物理层不通，重启服务无意义

### 八、完整诊断流程举例

```bash
# 1. 接口状态
ip link show enp2s0
# 输出：<NO-CARRIER,BROADCAST,MULTICAST,UP> ... state DOWN

# 2. 物理层确认
ethtool enp2s0
# 输出：Link detected: no / Speed: Unknown!

# 3. nmcli 确认
nmcli device status
# 输出：enp2s0  ethernet  不可用

# 4. 默认路由（确认当前在用哪个接口上网）
ip route show default

# 5. DNS 是否正常
resolvectl status

# 6. 代理是否正常
curl -s -o /dev/null -w "%{http_code}" -x http://127.0.0.1:7897 --max-time 5 https://www.google.com
```

## 场景二：物理链路 UP 但无外网（静态 IP 配置错误）

### 适用场景

用户报告"插上网线了，但上不了网"或"有线不通"。诊断发现接口已 UP 且有 LOWER_UP，但外网不通。

### 一、确认链路状态

```bash
ip link show <iface>
# 期望：<BROADCAST,MULTICAST,UP,LOWER_UP> ... state UP
cat /sys/class/net/<iface>/carrier    # 应为 1
ethtool <iface>                        # Link detected: yes
```

如果链路不通（NO-CARRIER），先处理物理层问题，再回来看这里。

### 二、检查 IP 配置方式

```bash
nmcli -f ipv4.method,ipv4.gateway,ipv4.addresses connection show <profile>
```

关键信号：

| 字段 | 正常值（DHCP） | 异常值（静态配置问题） |
|------|---------------|----------------------|
| `ipv4.method` | `auto` | `manual` |
| `ipv4.gateway` | DHCP 分配的网关 | 固定 IP（可能是错的） |
| `ipv4.addresses` | 自动获取 | 静态绑定的 IP/CIDR |

### 三、识别 netplan/cloud-init 遗留配置

Ubuntu 24 cloud 镜像常见特征：NetworkManager 连接配置名为 `netplan-<iface>`，由 cloud-init 的 `50-cloud-init.yaml` 自动生成。

```bash
# 查看 ethernet 连接配置
nmcli connection show | grep ether

# 认出 netplan 遗留配置：
# netplan-enp2s0  <uuid>  ethernet  --     ← 这就是静态配置
# 有线连接 1     <uuid>  ethernet  --     ← 可能是 DHCP 配置
```

如果发现 `netplan-<iface>` 且 `ipv4.method=manual`，说明这个配置来自初始化阶段的 netplan，绑定的是当时网络的静态 IP。

### 四、验证网关可达性

```bash
# ARP 表查看
arp -n | grep <iface>

# 结果解读
# <gateway>  (incomplete)  ← ❌ 网关不存在
# <gateway>  xx:xx:xx  C   ← ✅ 网关有响应

# ping 测试
ping -c 2 -W 2 <gateway>
```

### 五、检查路由 metric 异常

```bash
ip route show default
```

正常值：
- 有线：metric 100-600（应低于 WiFi）
- WiFi：metric 600-1000（应高于有线）

**异常信号**：有线的 metric 异常高（如 `20100`），同时 WiFi metric 更低（如 `600`）。这通常是 NM 自动提高了无法到达网关的路由的 metric，实际流量仍走 WiFi。

### 六、修复方案

#### 方案 A：改为 DHCP（推荐，家庭/办公路由环境）

```bash
# 需要 sudo 修改 netplan 配置
sudo sed -i 's/dhcp4: no/dhcp4: true/' /etc/netplan/50-cloud-init.yaml
sudo sed -i '/addresses:/,/gateway4:/d' /etc/netplan/50-cloud-init.yaml
sudo netplan apply
```

或更简单：直接删除 stale netplan 配置，让 NM 自动生成 DHCP 连接：

```bash
# 1. 删除 stale netplan 文件（需要 sudo）
sudo rm /etc/netplan/90-NM-<uuid>.yaml
# 2. 切换为 DHCP
nmcli connection delete netplan-enp2s0
nmcli device disconnect <iface>
nmcli device connect <iface>   # 自动 DHCP
```

#### 方案 B：修正静态配置（如果确实需要固定 IP）

```bash
# 修改 netplan
sudo vim /etc/netplan/50-cloud-init.yaml
# 确保 addresses、routes、nameservers 正确

# 或通过 nmcli 更新
nmcli connection modify netplan-enp2s0 ipv4.gateway <正确网关>
nmcli connection up netplan-enp2s0
```

#### 方案 C：保持现状（有线只跑局域网，外网走 WiFi + Clash）

如果用户有线只接局域网设备（NAS、另一台服务器等），不需要有线出互联网，则可以接受当前配置。外网流量通过 WiFi + Clash 代理正常。

### 七、完整诊断示例

```bash
# 1. 接口状态（确认物理链路）
ip link show enp2s0
# <BROADCAST,MULTICAST,UP,LOWER_UP> ... state UP ✅ 链路正常

# 2. 载波确认
cat /sys/class/net/enp2s0/carrier
# 1 ✅

# 3. nmcli 连接详情（确认配置类型）
nmcli -f ipv4.method,ipv4.gateway,ipv4.addresses connection show netplan-enp2s0
# ipv4.method: manual       ← 静态配置（cloud-init 遗留）
# ipv4.gateway: 192.168.1.1 ← 可能不存在的网关

# 4. 网关可达性
arp -n | grep enp2s0
# 192.168.1.1  (incomplete) ← ❌ 网关不存在
# 192.168.1.99 xx:xx:xx C   ← 局域网内其他设备在线

# 5. 路由 metric
ip route show default
# default via 192.168.0.1 dev wlp1s0 metric 600      ← WiFi 优先
# default via 192.168.1.1 dev enp2s0 metric 20100    ← 有线被降级

# 6. 代理测试（确认外网能力）
curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)" -x http://127.0.0.1:7897 --max-time 5 https://www.google.com
# HTTP 200 (0.43s) ✅ 代理正常
```

### 八、故障判定表

| 现象 | 原因 | 处理 |
|------|------|------|
| `link UP` 但 `ping <gateway>` 超时 | 网关不存在 | 改为 DHCP 或修正网关 |
| ARP 显示 `(incomplete)` | 无人响应 ARP 请求的 IP | 确认网络拓扑/网关 IP |
| 有线 metric `20100`（异常高） | NM 自动降级不可达路由 | 修复网关配置后自动恢复 |
| 连接配置名 `netplan-<iface>` + `method=manual` | cloud-init 遗留静态 IP | 删掉 netplan 配置或用 DHCP |
| nmcli 显示两个有线配置（`netplan-*` + `有线连接 *`） | netplan 和 NM 各自创建了配置 | 清理冗余，保留正确的 |

## 系统死机/冻结排查（鼠标键盘SSH均无响应）

### 适用场景

用户报告 Ubuntu 24 系统完全冻结——鼠标无法移动、键盘无响应、SSH 连不上（或三者皆有）。

### 排查步骤

#### 1. 检查是否为 PCIe AER 风暴

```bash
journalctl -k -b -1 --no-pager 2>/dev/null | grep -c "pcieport.*AER"
# > 1000 即为 AER 风暴
```

如果确认是 AER 风暴，参考独立 skill `ubuntu24-pcie-aer-iwlwifi-freeze-fix`，添加 `pcie_aspm=off pci=noaer` 内核参数。

#### 2. 检查 systemd 服务重启风暴（最常见的非AER死机关机）

**核心排查命令：**

```bash
# 查看哪些服务重启次数异常高
journalctl -b -1 --no-pager 2>/dev/null | grep "restart counter is at" | sort | uniq -c | sort -rn
```

输出示例（异常信号）：
```
  19120 6月 25 feishu-hermes.service: Scheduled restart job, restart counter is at 19120
  11970 6月 25 feishu-hermes-tunnel.service: Scheduled restart job, restart counter is at 11970
```

**定位有问题的服务：**

```bash
systemctl list-units --state=failed
systemctl status <可疑服务名>
systemctl cat <服务名>.service | grep -i restart
```

**判断指标：**
- 重启计数器 > 1000 = 明显异常
- journald 反复报告 "Under memory pressure, flushing caches" → 日志洪水耗尽内存
- libinput 报告 "event processing lagging behind by Nms, your system is too slow" → 输入处理滞后

**常见根因：** 服务的可执行文件/目录已被删除或移动，但 systemd 配置为 `Restart=always` 且无 `StartLimitIntervalSec`/`StartLimitBurst` 限制，导致无限重试 ≈ 自残式 DoS。

**修复方法：**

```bash
# 1. 停止失效服务
sudo systemctl stop <服务名>.service

# 2. 添加重启限制 override
sudo mkdir -p /etc/systemd/system/<服务名>.service.d/
sudo tee /etc/systemd/system/<服务名>.service.d/override.conf << 'EOF'
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
EOF
sudo systemctl daemon-reload

# 3. 或直接禁用
sudo systemctl disable --now <服务名>.service
```

#### 3. 检查 journald 内存压力

```bash
journalctl -b -1 --no-pager 2>/dev/null | grep "Under memory pressure, flushing caches"
# 多次出现 = 日志洪水正在耗尽系统内存
```

#### 4. 检查 libinput 输入滞后

```bash
journalctl -b -1 --no-pager 2>/dev/null | grep -i "libinput.*lagging behind\|libinput.*too slow"
# "event3 - SEM USB Keyboard: client bug: event processing lagging behind by 4791ms"
# 滞后 > 1 秒 = 系统严重过载
```

#### 5. 检查 OOM / 内存 thrashing

```bash
# OOM kill 记录
journalctl -b -1 --no-pager 2>/dev/null | grep -i "oom-killer\|Out of memory\|killed process"

# 当前内存
free -h

# D 状态进程数（> 5 个 D 状态需要关注）
ps aux | awk '$8 ~ /D/' | wc -l
ps aux | awk '$8 ~ /D/'
```

### 防止再次死机的加固措施

```bash
# 1. 内核 panic 自动重启
sudo tee /etc/sysctl.d/99-panic.conf << 'EOF'
kernel.softlockup_panic=1
kernel.hung_task_panic=1
kernel.panic=30
kernel.sysrq=1
EOF
sudo sysctl -p /etc/sysctl.d/99-panic.conf

# 2. 增加 swap（预防内存 thrashing）
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 3. 内存压力监控（每10分钟检测）
# 参考 references/memory-watchdog-setup.md

### 案例参考

- `references/system-freeze-service-restorm-case.md` — feishu-hermes 服务重启风暴导致整机冻结的完整排查过程

## PCIe AER 修复

参见独立 skill `ubuntu24-pcie-aer-iwlwifi-freeze-fix`，或在上述"系统死机排查"第一步中查看是否属于 AER 风暴。

## Clash Verge 管理

（内容从原 skill 保持或后续补充）

## 参考

- `references/ethernet-physical-layer-diag.md` — 有线网物理层详细诊断步骤和输出示例
- `network-proxy-diagnostics` — 代理层网络诊断（配合使用）
- `network-doctor` — 全栈网络排障（含 DNS/延迟对比/自动修复）
