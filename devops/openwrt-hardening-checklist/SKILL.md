---
name: 'openwrt-hardening-checklist'
description: 'OpenWrt 安全加固检查清单，涵盖固件更新、SSH、LuCI、防火墙、服务最小化、DNS、用户管理、日志、WiFi 及备份等关键领域的可执行加固命令'
author: 'Hermes Agent'
tags: [openwrt, security, hardening, checklist, firewall, ssh, luci, dns, backup, wifi]
---

# OpenWrt 安全加固检查清单

> 适用于运行 OpenWrt 的路由器/单板计算机（如 Raspberry Pi 5）。
> 所有命令均通过 SSH 或 LuCI 终端执行。使用前请逐项评估是否适配你的网络环境。

---

## 1. 固件更新与安全补丁

**目标：** 保持系统内核与软件包为最新，修复已知漏洞。

```bash
# 更新软件包列表
opkg update

# 列出可升级的包
opkg list-upgradable

# 升级所有可升级的包
opkg upgrade $(opkg list-upgradable | awk '{print $1}')

# 检查当前固件版本
cat /etc/openwrt_release

# 推荐：开启自动检查更新（通过 cron）
echo "0 3 * * * opkg update && opkg upgrade -y" >> /etc/crontabs/root
/etc/init.d/cron restart
```

---

## 2. SSH 安全（Dropbear）

**目标：** 禁用密码登录、仅允许密钥认证、修改非默认端口。

```bash
# 修改 SSH 端口为非默认（例如 2222）
uci set dropbear.@dropbear[0].Port='2222'

# 禁用密码认证（仅密钥登录）
uci set dropbear.@dropbear[0].PasswordAuth='off'
uci set dropbear.@dropbear[0].RootPasswordAuth='off'

# 启用密钥认证（默认已是 'on'）
uci set dropbear.@dropbear[0].RootLogin='1'

# 仅监听特定接口（例如 lan），不暴露到 WAN
uci set dropbear.@dropbear[0].Interface='lan'

# 应用配置
uci commit dropbear
/etc/init.d/dropbear restart

# 将本地公钥添加到 authorized_keys
mkdir -p /root/.ssh
chmod 700 /root/.ssh
echo "ssh-ed25519 AAAAC3... your-key-comment" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
```

---

## 3. LuCI Web 界面保护

**目标：** 强制 HTTPS、修改默认端口、设置 IP 白名单。

```bash
# 启用 HTTPS（需要安装 uhttpd 并配置证书）
opkg install uhttpd luci-ssl-openssl

# 强制 HTTPS 重定向
uci set uhttpd.main.redirect_https='1'

# 修改 LuCI 监听端口（例如 8443）
uci set uhttpd.main.listen_https='8443'

# 限制仅内网访问（仅监听 lan）
uci set uhttpd.main.listen_interface='lan'

# 设置 IP 白名单（仅允许指定 IP 访问 LuCI）
# 方法一：通过 uhttpd 的 cgi 路径限制（单 IP）
uci set uhttpd.main.allowed_ips='192.168.1.100 192.168.1.200'

# 方法二：通过防火墙规则限制
uci add firewall rule
uci set firewall.@rule[-1].name='LuCI-Allow-LAN'
uci set firewall.@rule[-1].src='lan'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].dest_port='8443'
uci set firewall.@rule[-1].target='ACCEPT'
uci set firewall.@rule[-1].family='ipv4'

# 禁用 HTTP（不监听 80 端口）
uci set uhttpd.main.listen_http='0.0.0.0:0'
uci set uhttpd.main.listen_http='[::]:0'

# 应用配置
uci commit uhttpd
/etc/init.d/uhttpd restart
```

---

## 4. 防火墙规则

**目标：** 仅开放必要端口、配置 DMZ、默认丢弃入站流量。

```bash
# 查看当前防火墙规则
uci show firewall

# 禁止 WAN 入站（默认规则）
uci set firewall.@zone[1].input='DROP'   # 通常 zone[1] 是 wan
uci set firewall.@zone[1].forward='DROP'

# 允许已建立的连接返回
uci set firewall.@zone[1].masq='1'

# 仅开放需要的端口（逐个添加规则）
# 例：开放 SSH（非默认端口 2222）从 WAN
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-SSH-WAN'
uci set firewall.@rule[-1].src='wan'
uci set firewall.@rule[-1].dest='lan'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].dest_port='2222'
uci set firewall.@rule[-1].target='ACCEPT'
uci set firewall.@rule[-1].family='ipv4'

# 禁止 WAN ping（隐藏）
uci add firewall rule
uci set firewall.@rule[-1].name='Deny-Ping-WAN'
uci set firewall.@rule[-1].src='wan'
uci set firewall.@rule[-1].proto='icmp'
uci set firewall.@rule[-1].icmp_type='echo-request'
uci set firewall.@rule[-1].target='DROP'
uci set firewall.@rule[-1].family='ipv4'

# DMZ 配置（将特定主机暴露到 WAN）
uci add firewall redirect
uci set firewall.@redirect[-1].name='DMZ-Host'
uci set firewall.@redirect[-1].src='wan'
uci set firewall.@redirect[-1].proto='tcpudp'
uci set firewall.@redirect[-1].src_dport='1-65535'
uci set firewall.@redirect[-1].dest_ip='192.168.1.50'
uci set firewall.@redirect[-1].target='DNAT'

# 应用配置
uci commit firewall
/etc/init.d/firewall reload
```

---

## 5. 服务最小化

**目标：** 关闭不必要的服务，减少攻击面。

```bash
# 列出所有正在运行的服务
/etc/init.d/ | grep enabled

# 停用并禁用不需要的服务（示例）
/etc/init.d/dnsmasq disable    # 如果使用第三方 DNS 方案
/etc/init.d/odhcpd disable     # 如果使用静态 IPv6 配置
/etc/init.d/mdns disable       # 如果不需要 mDNS
/etc/init.d/samba4 disable     # 如果不需要文件共享
/etc/init.d/vsftpd disable     # 如果不需要 FTP

# 移除不需要的软件包
opkg remove --autoremove luci-app-statistics luci-app-vnstat luci-theme-*

# 查看所有已安装包，逐项审核
opkg list-installed | less
```

---

## 6. DNS 安全

**目标：** DNS over TLS 加密查询、防止 DNS 劫持/污染。

```bash
# 安装 Stubby（DNS over TLS 客户端）
opkg install stubby

# 配置 Stubby 上游为支持 DoT 的 DNS 服务器
uci set stubby.global.resolution_type='GETDNS_RESOLUTION_STUB'
uci set stubby.@resolver[0].address='1.1.1.1@853#cloudflare-dns.com'
uci set stubby.@resolver[0].tls_authentication='GETDNS_AUTHENTICATION_REQUIRED'
uci set stubby.@resolver[1].address='9.9.9.9@853#dns.quad9.net'
uci set stubby.@resolver[1].tls_authentication='GETDNS_AUTHENTICATION_REQUIRED'

uci commit stubby
/etc/init.d/stubby enable
/etc/init.d/stubby restart

# 配置 dnsmasq 将本地 DNS 转发到 Stubby（127.0.0.1#5053）
uci set dhcp.@dnsmasq[0].noresolv='1'
uci set dhcp.@dnsmasq[0].list_server='127.0.0.1#5053'
uci commit dhcp
/etc/init.d/dnsmasq restart

# 可选：安装 DNSSEC 验证
opkg install dnsmasq-full
uci set dhcp.@dnsmasq[0].dnssec='1'
uci set dhcp.@dnsmasq[0].dnssec_check_unsigned='1'
uci commit dhcp
/etc/init.d/dnsmasq restart
```

**China-specific防污染建议：**

```bash
# 针对国内环境的 DNS 防污染方案（视需求选一）：
# 方案 A：使用 ChinaDNS-NG + 可信上游
opkg install chinadns-ng
# 方案 B：使用 https-dns-proxy（DoH）
opkg install https-dns-proxy
# 方案 C：搭配 smartdns 防污染
opkg install smartdns
```

---

## 7. 系统密码与用户管理

**目标：** 强密码策略、定期更换、限制 root 登录。

```bash
# 修改 root 密码（强制使用强密码：至少 16 位，含大小写+数字+符号）
passwd root

# 创建非 root 管理用户（减少直接 root 使用）
opkg install shadow-useradd
useradd -m -s /bin/ash admin
passwd admin

# 授予 sudo 权限（需安装 sudo）
opkg install sudo
echo "admin ALL=(ALL) ALL" >> /etc/sudoers

# 要求 SSH 使用非 root 用户登录
uci set dropbear.@dropbear[0].RootLogin='0'
uci commit dropbear
/etc/init.d/dropbear restart

# 锁定不必要的系统账号
passwd -l daemon
passwd -l nobody
passwd -l www-data

# 检查所有用户
cat /etc/passwd
```

---

## 8. 日志审核

**目标：** 启用详细日志、集中管理、定期轮转。

```bash
# 启用系统日志并设置日志级别
uci set system.@system[0].log_size='64'      # 日志大小 64KB
uci set system.@system[0].log_ip=''           # 留空为本地日志
uci set system.@system[0].conloglevel='7'     # 控制台日志级别（7=debug）
uci set system.@system[0].cronloglevel='7'    # cron 日志级别
uci commit system
/etc/init.d/log restart

# 查看关键日志
logread -e "sshd\|dropbear"          # SSH 登录日志
logread -e "firewall"                 # 防火墙事件
logread -e "auth"                     # 认证失败日志
logread -e "luci\|uhttpd"            # LuCI 访问日志

# 安装 logrotate 进行日志轮转
opkg install logrotate
cat > /etc/logrotate.conf << 'EOF'
/var/log/*.log {
    rotate 7
    weekly
    compress
    missingok
    notifempty
}
EOF

# 设置 cron 定时检查日志
echo "0 6 * * * logread -e 'Failed password' | grep -c 'Failed' >> /tmp/auth_failures.log" >> /etc/crontabs/root
/etc/init.d/cron restart
```

---

## 9. WiFi 安全

**目标：** WPA3 加密、隐藏 SSID、MAC 过滤、禁用 WPS。

```bash
# 查看当前 WiFi 配置
uci show wireless

# 加密方式设为 WPA3-SAE（最安全）
uci set wireless.@wifi-iface[0].encryption='sae'
uci set wireless.@wifi-iface[0].key='YourVeryStrongP@ssw0rd!2024'

# 2.4GHz 和 5GHz 分开配置（假设 radio0=2.4G, radio1=5G）
# 2.4G
uci set wireless.@wifi-iface[0].encryption='sae'
uci set wireless.@wifi-iface[0].key='YourStrongKey24G!'

# 5G
uci set wireless.@wifi-iface[1].encryption='sae'
uci set wireless.@wifi-iface[1].key='YourStrongKey5G!'

# 禁用 WPS
uci set wireless.@wifi-iface[0].wps_pushbutton='0'
uci set wireless.@wifi-iface[1].wps_pushbutton='0'

# 隐藏 SSID（不广播）
uci set wireless.@wifi-iface[0].hidden='1'
uci set wireless.@wifi-iface[1].hidden='1'

# MAC 地址过滤（白名单模式）
uci set wireless.@wifi-iface[0].macfilter='allow'
uci add_list wireless.@wifi-iface[0].maclist='AA:BB:CC:DD:EE:FF'
uci add_list wireless.@wifi-iface[0].maclist='11:22:33:44:55:66'

# 禁用 WiFi 客户端隔离（防止同一 WiFi 下设备互访）
uci set wireless.@wifi-iface[0].isolate='1'
uci set wireless.@wifi-iface[1].isolate='1'

# 启用 802.11w 管理帧保护（PMF）
uci set wireless.@wifi-iface[0].ieee80211w='2'   # 2=强制
uci set wireless.@wifi-iface[1].ieee80211w='2'

# 应用配置
uci commit wireless
wifi reload

# 关闭不用的无线频段（如 2.4G 不需要可禁用）
# uci set wireless.@wifi-device[0].disabled='1'
# uci commit wireless && wifi reload
```

---

## 10. 定期备份配置

**目标：** 定期备份路由器配置，防止配置丢失。

```bash
# 手动备份完整配置
sysupgrade -b /tmp/openwrt-backup-$(date +%Y%m%d).tar.gz

# 备份到远程服务器（SCP）
sysupgrade -b /tmp/backup.tar.gz
scp /tmp/backup.tar.gz root@192.168.1.200:/backups/openwrt/

# 配置 cron 自动每周备份
cat > /etc/backup_script.sh << 'SCRIPT'
#!/bin/sh
BACKUP_DIR="/tmp"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/openwrt-config-${TIMESTAMP}.tar.gz"
sysupgrade -b "${BACKUP_FILE}"
# 可选：备份到远程 NAS/SMB
# scp "${BACKUP_FILE}" user@backup-server:/path/to/backups/
# 保留最近 4 周备份
ls -t ${BACKUP_DIR}/openwrt-config-*.tar.gz 2>/dev/null | tail -n +5 | xargs rm -f
SCRIPT
chmod +x /etc/backup_script.sh

# 每周日凌晨 3:00 执行备份
echo "0 3 * * 0 /etc/backup_script.sh" >> /etc/crontabs/root
/etc/init.d/cron restart

# 恢复备份命令（备忘）
# sysupgrade -r /tmp/openwrt-backup-20240101.tar.gz
```

---

## 附：完整加固检查清单

执行以下命令快速生成加固状态报告：

```bash
cat << 'REPORT'
========== OpenWrt 安全加固检查报告 ==========

[1] 固件版本:        $(cat /etc/openwrt_release | grep DISTRIB_RELEASE)
[2] SSH 配置:        
    - 端口:          $(uci get dropbear.@dropbear[0].Port 2>/dev/null || echo "22 (默认)")
    - 密码认证:      $(uci get dropbear.@dropbear[0].PasswordAuth 2>/dev/null || echo "on")
    - Root 登录:     $(uci get dropbear.@dropbear[0].RootLogin 2>/dev/null || echo "允许")
[3] LuCI HTTPS:      $(uci get uhttpd.main.redirect_https 2>/dev/null || echo "未启用")
[4] 防火墙 WAN 输入: $(uci get firewall.@zone[1].input 2>/dev/null || echo "未知")
[5] DNS DoT:         $(ls /etc/init.d/stubby 2>/dev/null && echo "已安装" || echo "未安装")
[6] WiFi 加密:       $(uci get wireless.@wifi-iface[0].encryption 2>/dev/null || echo "未知")
[7] 定时备份:        $(crontab -l 2>/dev/null | grep -c backup)
================================================
REPORT
```

> ⚠️ **免责声明：** 以上命令部分会立即改变网络配置，建议逐项执行并在每一次更改后验证网络连通性。建议先在测试环境验证，再应用到生产路由器。修改 SSH 端口前请确保新端口已在防火墙放行，避免被锁在路由器外。
