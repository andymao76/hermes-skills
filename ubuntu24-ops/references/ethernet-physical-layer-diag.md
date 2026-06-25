# 以太网物理层诊断（Ubuntu 24.04 实际输出示例）

## 背景

2026-06-23 现场诊断：用户插网线后报告不能访问外网。最终发现是有线网卡 `enp2s0` 物理层无载波（NO-CARRIER），实际通过 WiFi 上网。

## 完整诊断命令链

### 1. 接口状态

```bash
$ ip link show enp2s0
2: enp2s0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc fq_codel state DOWN
    link/ether 00:e0:4c:dc:03:be brd ff:ff:ff:ff:ff:ff
```

关键信号：`<NO-CARRIER, ..., UP>` + `state DOWN`。

### 2. 载波文件

```bash
$ cat /sys/class/net/enp2s0/carrier
cat: /sys/class/net/enp2s0/carrier: 输入/输出错误
```

当 NO-CARRIER 时，carrier 文件可能不存在或报错。

### 3. ethtool 物理层确认

```bash
$ ethtool enp2s0
Settings for enp2s0:
    Supported ports: [ TP MII ]
    Supported link modes:   10baseT/Half 10baseT/Full
                            100baseT/Half 100baseT/Full
                            1000baseT/Half 1000baseT/Full
    Auto-negotiation: on
    Speed: Unknown!
    Duplex: Unknown! (255)
    Port: Twisted Pair
    Link detected: no
```

关键字段：`Link detected: no`，`Speed: Unknown!`，`Duplex: Unknown! (255)`。

### 4. nmcli 设备状态

```bash
$ nmcli device status
DEVICE          TYPE      STATE         CONNECTION 
wlp1s0          wifi      已连接        MIFI_5B81  
enp2s0          ethernet  不可用        --         
```

`不可用` = 物理层不通。

### 5. 连接配置查看

```bash
$ nmcli connection show | grep ether
有线连接 1      3db1b453-...  ethernet  --      
有线连接 2      289a5f43-...  ethernet  --      
netplan-enp2s0  7ea6f90b-...  ethernet  --      
```

有连接配置但设备不可用，不会被激活。

### 6. 尝试重连（无效）

```bash
$ nmcli device reapply enp2s0
错误：重新应用连接到 "enp2s0" 失败：Device is not activated
```

NO-CARRIER 状态下所有软件重连都会失败。

### 7. 路由确认

```bash
$ ip route show default
default via 192.168.0.1 dev wlp1s0 proto static metric 600
```

默认路由走 WiFi，有线未参与路由。

## 代理/Crash 端口检查

Clash Verge 的 mixed-port 在配置文件中：

```bash
$ cat ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml | grep mixed-port
mixed-port: 7897
```

系统代理设置：

```bash
$ gsettings get org.gnome.system.proxy mode
'manual'
$ gsettings get org.gnome.system.proxy.http host
'127.0.0.1'
$ gsettings get org.gnome.system.proxy.http port
7897
```

Clash 内核版本：

```bash
$ curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/version
{"meta":true,"version":"v1.19.25"}
```

## 物理层故障判定速查

| 现象 | 判定 | 处理 |
|------|------|------|
| `ip link` 显示 `<NO-CARRIER,...>` | 物理无载波 | 检查网线/端口/对端供电 |
| `ethtool` 显示 `Link detected: no` | 确认物理不通 | 软件无法修复 |
| `nmcli` 显示状态 `不可用` | 设备无法激活 | 检查物理连接 |
| `nmcli device reapply` 报 `Device is not activated` | 印证物理不通 | 不要重复尝试 |
| Google 代理通（7897 HTTP 200）但 Wi-Fi 在有线插拔后短暂不通 | 网络切换间隙 | WiFi 重连即可，或有线完全替代前断开 WiFi |

## 关联阅读

- `references/netplan-static-ip-stale.md` — 物理链路 UP 但静态 IP/网关配置错误场景（本机实际诊断记录）

## 注意事项

- Ubuntu 24.04 下 `ss -tlnp` 可能被安全策略拦截
- `sudo ip link set ... down/up` 需要 sudo 密码或 NOPASSWD 配置
- 不要混淆 `state DOWN`（接口管理状态 down）与 `NO-CARRIER`（物理层无载波）
