---
name: linux-hardening-checklist
description: Linux 安全加固检查清单 — 针对 Ubuntu 24.04 的可执行安全检查与加固命令
version: "1.0"
author: Hermes Agent
tags:
  - security
  - hardening
  - linux
  - ubuntu
  - devops
---

# Linux 安全加固检查清单

> 适用系统：Ubuntu 24.04 LTS
> 每个项目包含「检查命令」（用于审计现有状态）和「加固命令」（用于实施修复）。
> ⚠ 部分加固命令需要 root 权限，请使用 `sudo` 执行。

---

## 1. 系统更新与补丁

### 检查命令

```bash
# 查看可用的安全更新（不安装）
apt list --upgradable 2>/dev/null | grep -i security

# 查看已安装的安全更新历史
grep -i "security" /var/log/apt/history.log | tail -20

# 检查无人值守安全更新是否启用
dpkg -l | grep unattended-upgrades
systemctl is-active unattended-upgrades
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null
```

### 加固命令

```bash
# 更新软件包列表并安装所有安全更新
sudo apt update && sudo apt upgrade -y

# 安装无人值守安全更新
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades

# 配置自动安全更新
cat << 'EOF' | sudo tee /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

# 配置仅安全更新
cat << 'EOF' | sudo tee /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
```

---

## 2. SSH 安全配置

### 检查命令

```bash
# 检查是否禁止密码登录
sudo sshd -T 2>/dev/null | grep -i "passwordauthentication"

# 检查是否仅允许密钥登录
sudo sshd -T 2>/dev/null | grep -i "pubkeyauthentication"

# 检查当前 SSH 端口
sudo sshd -T 2>/dev/null | grep -i "^port "

# 检查 PermitRootLogin 设置
sudo sshd -T 2>/dev/null | grep -i "permitrootlogin"

# 检查 AllowUsers 配置
sudo sshd -T 2>/dev/null | grep -i "allowusers"

# 检查配置文件中的实际设定
sudo grep -E "^(PasswordAuthentication|PubkeyAuthentication|Port|PermitRootLogin|AllowUsers|Protocol)" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null
```

### 加固命令

```bash
# 备份原始配置
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d)

# 写入安全配置（端口改为 2222，请根据实际环境修改）
sudo tee /etc/ssh/sshd_config.d/99-hardening.conf << 'EOF'
# SSH 安全加固配置
Port 2222
Protocol 2
PermitRootLogin prohibit-password
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 10
AllowUsers andymao  # ← 修改为实际用户名
EOF

# 重启 SSH 服务前务必在另一个终端保持连接测试
sudo systemctl restart sshd

# 防火墙放行新端口（如果在防火墙生效时操作）
sudo ufw allow 2222/tcp comment 'SSH hardened port'
```

---

## 3. 防火墙设置

### 检查命令

```bash
# 检查 ufw 状态
sudo ufw status verbose

# 检查 ufw 是否启用
sudo ufw status | grep -i active

# 检查 iptables 规则
sudo iptables -L -n -v
sudo ip6tables -L -n -v

# 检查默认策略
sudo iptables -L | grep -E "^Chain.*(INPUT|FORWARD|OUTPUT)" -A 1

# 检查 nftables（Ubuntu 24.04 默认）
sudo nft list ruleset 2>/dev/null
```

### 加固命令

```bash
# ---- ufw 方案 ----
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 放行 SSH（根据实际端口修改）
sudo ufw allow 2222/tcp comment 'SSH'
# 放行 HTTP/HTTPS（如需）
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
# 放行 DNS（如需）
sudo ufw allow 53 comment 'DNS'

# 启用 ufw
sudo ufw enable

# 查看规则编号，删除特定规则
sudo ufw status numbered

# ---- iptables 方案（如果 ufw 不适用） ----
# 设置默认策略
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# 允许回环接口
sudo iptables -A INPUT -i lo -j ACCEPT

# 允许已建立连接
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 放行 SSH
sudo iptables -A INPUT -p tcp --dport 2222 -j ACCEPT

# 放行 HTTP/HTTPS（如需）
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 保存规则
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

---

## 4. 文件权限加固

### 检查命令

```bash
# 检查关键系统文件权限
ls -la /etc/shadow
ls -la /etc/gshadow
ls -la /etc/passwd
ls -la /etc/group
ls -la /etc/sudoers
ls -la /etc/ssh/sshd_config
ls -la /etc/crontab
ls -la /etc/cron*
ls -la /root 2>/dev/null

# 查找权限异常的世界可写文件
find / -type f -perm -o+w -not -path "/proc/*" -not -path "/sys/*" -not -path "/dev/*" 2>/dev/null | head -20

# 查找无主的文件
find / -nouser -o -nogroup -not -path "/proc/*" -not -path "/sys/*" -not -path "/dev/*" 2>/dev/null | head -20

# 检查 SUID/SGID 文件
find / -perm -4000 -type f -not -path "/proc/*" -not -path "/sys/*" 2>/dev/null
```

### 加固命令

```bash
# 设置正确的文件权限
sudo chmod 600 /etc/shadow
sudo chmod 600 /etc/gshadow
sudo chmod 644 /etc/passwd
sudo chmod 644 /etc/group
sudo chmod 440 /etc/sudoers
sudo chmod 440 /etc/sudoers.d/*
sudo chmod 600 /etc/ssh/sshd_config
sudo chmod 600 /etc/ssh/ssh_host_*_key
sudo chmod 644 /etc/ssh/ssh_host_*_key.pub
sudo chmod 600 /etc/crontab

# 设置正确的所有者
sudo chown root:root /etc/shadow
sudo chown root:root /etc/passwd
sudo chown root:root /etc/group
sudo chown root:root /etc/gshadow
sudo chown root:root /etc/sudoers

# 查找并修复权限异常文件（危险 SUID）
# 列出后手动评估哪些需要移除 suid
sudo find / -perm -4000 -type f -not -path "/proc/*" 2>/dev/null

# 移除不需要的 SUID（示例）
sudo chmod u-s /usr/bin/newgrp
sudo chmod u-s /usr/bin/chsh
sudo chmod u-s /usr/bin/chfn

# 修复 umask 设置（建议 027 或 077）
echo "umask 027" | sudo tee -a /etc/profile.d/umask.sh
```

---

## 5. 审计与日志

### 检查命令

```bash
# 检查 auditd 状态
sudo systemctl status auditd
sudo auditctl -s

# 查看已加载的审计规则
sudo auditctl -l

# 检查 rsyslog 状态
sudo systemctl status rsyslog

# 检查日志轮转配置
cat /etc/logrotate.conf
ls /etc/logrotate.d/

# 查看日志空间使用
du -sh /var/log/
```

### 加固命令

```bash
# 安装 auditd
sudo apt install -y auditd audispd-plugins

# 配置审计规则
sudo tee /etc/audit/rules.d/99-hardening.rules << 'EOF'
# 清除默认规则
-D
-b 8192

# 监控系统时间变更
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change

# 监控用户/组管理
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k identity

# 监控网络环境变更
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/network -p wa -k system-locale

# 监控 SELinux/AppArmor 变更
-w /etc/apparmor -p wa -k MAC-policy
-w /etc/apparmor.d -p wa -k MAC-policy

# 监控登录相关文件
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/run/faillock -p wa -k logins

# 监控内核模块加载
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# 监控 SSH 配置
-w /etc/ssh/sshd_config -p wa -k sshd

# 监控关键系统二进制文件
-w /usr/bin/passwd -p x -k privileged-passwd
-w /usr/bin/sudo -p x -k privileged-sudo
-w /usr/bin/su -p x -k privileged-su

# 设置日志文件权限
-e 2
EOF

# 重启 auditd
sudo systemctl restart auditd
sudo systemctl enable auditd

# 配置日志轮转
cat /etc/logrotate.d/auditd 2>/dev/null || echo "/var/log/audit/audit.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
}" | sudo tee /etc/logrotate.d/auditd

# 增强 rsyslog 配置
echo "auth,authpriv.*                 /var/log/auth.log
*.*;auth,authpriv.none              /var/log/syslog
kern.*                              /var/log/kern.log
*.emerg                             :omusrmsg:*" | sudo tee /etc/rsyslog.d/50-hardening.conf

sudo systemctl restart rsyslog
```

---

## 6. 内核参数加固 (sysctl)

### 检查命令

```bash
# 查看当前所有 sysctl 参数
sudo sysctl -a 2>/dev/null | grep -E "(ip_forward|rp_filter|tcp_syncookies|icmp_echo_ignore_broadcasts|accept_source_route|accept_redirects|send_redirects|log_martians)" | sort

# 检查内核参数配置文件
cat /etc/sysctl.conf
cat /etc/sysctl.d/*.conf 2>/dev/null

# 检查当前 IP 转发状态
cat /proc/sys/net/ipv4/ip_forward
```

### 加固命令

```bash
sudo tee /etc/sysctl.d/99-hardening.conf << 'EOF'
# ========================
# 网络层安全加固
# ========================

# 禁止 IP 转发（除非是路由器）
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# 禁止源路由
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# 禁止 ICMP 重定向
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# 启用反向路径过滤（防 IP 欺骗）
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# 启用 TCP SYN Cookie（防 SYN Flood）
net.ipv4.tcp_syncookies = 1

# 忽略 ICMP 广播请求
net.ipv4.icmp_echo_ignore_broadcasts = 1

# 忽略 ICMP 请求（可选，影响 ping）
# net.ipv4.icmp_echo_ignore_all = 1

# 记录不可达地址和拒绝连接（用于审计）
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# ========================
# TCP 协议栈加固
# ========================

# 禁用 TCP 时间戳（减少信息泄露）
net.ipv4.tcp_timestamps = 0

# 增加 TCP SYN 队列长度
net.ipv4.tcp_max_syn_backlog = 2048

# 减少 SYN-ACK 重试次数
net.ipv4.tcp_synack_retries = 2

# 减少 SYN 重试次数
net.ipv4.tcp_syn_retries = 5

# 启用 TCP FIN 超时优化
net.ipv4.tcp_fin_timeout = 15

# 启用 TCP 窗口缩放
net.ipv4.tcp_window_scaling = 1

# ========================
# 安全相关的内核参数
# ========================

# 禁止 core dump（禁用核心转储）
fs.suid_dumpable = 0
kernel.core_uses_pid = 1

# 限制对内核日志的访问
kernel.dmesg_restrict = 1

# 限制 ptrace 范围
kernel.yama.ptrace_scope = 1

# 限制 perf 事件暴露
kernel.perf_event_paranoid = 3

# 启用 ASLR（地址空间布局随机化）
kernel.randomize_va_space = 2

# 禁用 Kexec（防止内核热替换）
kernel.kexec_load_disabled = 1

# 禁止通过 SysRq 进行系统请求（如 Alt+SysRq+B 重启）
kernel.sysrq = 0

# 限制 BPF JIT（防止 JIT spray 攻击）
net.core.bpf_jit_enable = 0
EOF

# 立即生效
sudo sysctl --system

# 验证
sudo sysctl -a 2>/dev/null | grep -E "(ip_forward|rp_filter|tcp_syncookies|rp_filter|dmesg_restrict|randomize_va_space)" | sort
```

---

## 7. 服务最小化

### 检查命令

```bash
# 列出所有正在运行的服务
systemctl list-units --type=service --state=running

# 列出所有已启用的服务
systemctl list-unit-files --type=service --state=enabled

# 检查监听中的端口及对应服务
sudo ss -tlnp
sudo ss -ulnp

# 检查开机自启服务
systemctl list-unit-files --type=service --state=enabled | grep -E "^[^@]"

# 检查 Snap 服务
snap list 2>/dev/null
```

### 加固命令

```bash
# 停止并禁用不必要的服务（按需调整）
unnecessary_services=(
    "cups"           # 打印服务
    "avahi-daemon"   # mDNS/ZeroConf
    "bluetooth"      # 蓝牙
    "whoopsie"       # Ubuntu 错误报告
    "ModemManager"   # 调制解调器管理
    "speech-dispatcher" # 语音合成
    "thunderbird-autostart" 2>/dev/null
)

for svc in "${unnecessary_services[@]}"; do
    if systemctl is-enabled "$svc" 2>/dev/null | grep -q enabled; then
        echo "禁用多余服务: $svc"
        sudo systemctl stop "$svc" 2>/dev/null
        sudo systemctl disable "$svc" 2>/dev/null
    fi
done

# 移除不必要的软件包
sudo apt purge -y \
    cups* \
    avahi-daemon \
    bluetooth \
    bluez \
    whoopsie \
    modemmanager \
    speech-dispatcher \
    ubuntu-report \
    popularity-contest

# 自动清理
sudo apt autoremove --purge -y
sudo apt autoclean

# 屏蔽不必要的网络服务监听
# 检查哪些端口对公网开放
ss -tlnp | grep -E "^LISTEN.*0\.0\.0\.0:|^LISTEN.*\[::\]:" | grep -v "127.0.0.1" | grep -v "::1"
```

---

## 8. Fail2Ban / 入侵检测

### 检查命令

```bash
# 检查 Fail2Ban 是否安装
dpkg -l | grep fail2ban

# 检查 Fail2Ban 运行状态
sudo systemctl status fail2ban

# 查看 Fail2Ban 监狱状态
sudo fail2ban-client status

# 查看 SSH 监狱详细状态
sudo fail2ban-client status sshd

# 检查已封禁 IP
sudo fail2ban-client banned

# 检查系统的登录失败记录
sudo lastb | head -20
sudo journalctl -u sshd -n 50 --no-pager | grep "Failed password"
```

### 加固命令

```bash
# 安装 Fail2Ban
sudo apt install -y fail2ban

# 创建本地覆盖配置
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# 封禁时间（秒）
bantime = 3600
# 封禁时间增长因子
bantime.increment = true
bantime.factor = 2
bantime.maxtime = 604800

# 检测窗口（秒）
findtime = 600
# 最大失败次数
maxretry = 5

# 忽略的 IP（白名单）
ignoreip = 127.0.0.1/8 ::1

# 动作
action = %(action_mwl)s

# 日志编码
logencoding = utf-8

[sshd]
enabled = true
port = 2222  # 修改为实际 SSH 端口
logpath = %(sshd_log)s
backend = %(sshd_backend)s

[sshd-ddos]
enabled = true
port = 2222  # 修改为实际 SSH 端口
logpath = %(sshd_log)s

# 其他常用监狱
[apache-auth]
enabled = false

[nginx-http-auth]
enabled = false

[postfix]
enabled = false
EOF

# 重启并启用
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

# 可选：安装 RKHunter（rootkit 检测）
sudo apt install -y rkhunter
sudo rkhunter --propupd
# 扫描
sudo rkhunter --check --skip-keypress

# 可选：安装 chkrootkit
sudo apt install -y chkrootkit
sudo chkrootkit
```

---

## 9. 文件完整性检查 (AIDE)

### 检查命令

```bash
# 检查 AIDE 是否安装
dpkg -l | grep aide

# 检查是否已有 AIDE 数据库
ls -la /var/lib/aide/aide.db* 2>/dev/null

# 执行快速完整性检查（如果数据库已存在）
sudo aide.wrapper --check 2>/dev/null | head -30

# 检查 Tripwire（替代方案）
dpkg -l | grep tripwire 2>/dev/null
```

### 加固命令

```bash
# 安装 AIDE
sudo apt install -y aide aide-common

# 备份默认配置
sudo cp /etc/aide/aide.conf /etc/aide/aide.conf.bak

# 配置 AIDE（监视关键系统文件）
sudo tee /etc/aide/aide.conf << 'AIDE_EOF'
# AIDE 配置 — Ubuntu 安全加固

# 数据库位置
database=file:/var/lib/aide/aide.db
database_out=file:/var/lib/aide/aide.db.new
verbose=5
report_url=file:/var/log/aide/aide.log

# 定义规则
OwnerMode= p+u+g+ftype+acl+xattrs
All= p+u+g+ftype+acl+xattrs+sha256+rmd160
Log= p+u+g+n+ftype+acl+xattrs
Content= sha256+rmd160
DirOnly= p+u+g+ftype

# ========================
# 系统二进制文件
# ========================
/bin All
/sbin All
/usr/bin All
/usr/sbin All
/usr/local/bin All
/usr/local/sbin All

# ========================
# 配置文件
# ========================
/etc OwnerMode
# 但以下文件需要内容校验
/etc/passwd Content
/etc/shadow Content
/etc/group Content
/etc/gshadow Content
/etc/sudoers Content
/etc/ssh/sshd_config Content
/etc/hosts Content
/etc/hostname Content
/etc/resolv.conf Content
/etc/fstab Content
/etc/crontab Content
/etc/cron.d Content
/etc/cron.daily Content
/etc/cron.hourly Content
/etc/cron.weekly Content
/etc/cron.monthly Content

# ========================
# 内核和引导
# ========================
/boot All
/vmlinuz Content
/initrd.img Content

# ========================
# 库文件
# ========================
/lib All
/lib64 All
/usr/lib All

# ========================
# 日志（仅检查存在性）
# ========================
/var/log Log
/var/log/auth.log Log
/var/log/syslog Log
/var/log/kern.log Log

# ========================
# 排除目录
# ========================
!/proc
!/sys
!/dev
!/run
!/var/lib/docker
!/var/lib/lxc
!/var/lib/snapd
!/var/cache
!/var/tmp
!/tmp
!/root/.cache
!/home/.*/\.cache
!/home/.*/\.thumbnails
AIDE_EOF

# 初始化 AIDE 数据库（首次运行）
sudo aideinit
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# 设置每日定时检查
sudo tee /etc/cron.daily/aide-check << 'CRON_EOF'
#!/bin/bash
# AIDE 每日完整性检查
/usr/bin/aide.wrapper --check
CRON_EOF

sudo chmod +x /etc/cron.daily/aide-check

# 手动运行检查
sudo aide.wrapper --check

# 更新数据库（确认无误后）
sudo aide.wrapper --update
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

---

## 10. 定期安全扫描命令

### 快速安全审计脚本

```bash
#!/bin/bash
# quick-security-audit.sh — 快速安全审计脚本
# 保存为 /usr/local/bin/quick-security-audit.sh 并 chmod +x

echo "========================================"
echo "  Linux 安全快速审计报告"
echo "  运行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

echo ""
echo "--- 1. 系统更新 ---"
apt list --upgradable 2>/dev/null | grep -c upgradable | xargs echo "待更新软件包数:"

echo ""
echo "--- 2. SSH 安全 ---"
sudo sshd -T 2>/dev/null | grep -E "passwordauthentication|permitrootlogin" | \
  sed 's/^/  /'

echo ""
echo "--- 3. 防火墙 ---"
sudo ufw status verbose 2>/dev/null | head -5 | sed 's/^/  /'

echo ""
echo "--- 4. 关键文件权限 ---"
for f in /etc/shadow /etc/sudoers /etc/passwd; do
  perms=$(stat -c "%a %U:%G" "$f" 2>/dev/null)
  echo "  $f: $perms"
done

echo ""
echo "--- 5. 审计服务 ---"
for s in auditd rsyslog fail2ban; do
  status=$(systemctl is-active "$s" 2>/dev/null)
  echo "  $s: $status"
done

echo ""
echo "--- 6. 开放端口 ---"
ss -tlnp 2>/dev/null | sed 's/^/  /'

echo ""
echo "--- 7. 最近的登录失败 ---"
sudo lastb 2>/dev/null | head -5 | sed 's/^/  /'

echo ""
echo "--- 8. 监听中的服务 ---"
systemctl list-units --type=service --state=running --no-legend 2>/dev/null | \
  awk '{print "  " $1}' | head -20

echo ""
echo "========================================"
echo "  审计完成"
echo "========================================"
```

### 其他安全扫描工具命令

```bash
# === 端口扫描（对外暴露的服务） ===
# 从外部扫描本机（需替换目标 IP）
# nmap -sS -sV -O <目标IP>

# === Lynis 系统审计（推荐） ===
sudo apt install -y lynis
sudo lynis audit system --quick

# === ClamAV 防病毒扫描 ===
sudo apt install -y clamav clamav-daemon
sudo freshclam  # 更新病毒库
sudo clamscan -r /home --exclude-dir="^/sys|^/proc|^/dev" -i

# === Rootkit 扫描 ===
sudo rkhunter --check --skip-keypress --rwo 2>/dev/null

# === 检查被攻破的密码 ===
# 下载 Have I Been Pwned 密码列表（约 40GB，谨慎）
# 或使用本地密码审计
sudo apt install -y john
# sudo john --show /etc/shadow  # 检查弱密码

# === 检查 Docker 容器安全（如果使用 Docker） ===
# docker run --network host --pid host --userns host --cap-add audit_control \
#   -v /var/lib:/var/lib:ro \
#   -v /var/run/docker.sock:/var/run/docker.sock:ro \
#   aquasec/trivy:latest image --severity CRITICAL <镜像名>

# === Trivy 漏洞扫描 ===
# sudo snap install trivy
# trivy fs --severity CRITICAL,HIGH /  # 扫描文件系统

# === 检查 OpenSCAP 合规性（CIS Benchmarks） ===
# sudo apt install -y libopenscap8 scap-security-guide
# sudo oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis \
#   --results-arf /tmp/arf.xml --report /tmp/report.html \
#   /usr/share/xml/scap/ssg/content/ssg-ubuntu2404-ds.xml
```

---

## 📋 总体检查摘要模板

| 项目 | 状态 | 备注 |
|------|------|------|
| 1. 系统更新 | ⬜ | |
| 2. SSH 加固 | ⬜ | |
| 3. 防火墙 | ⬜ | |
| 4. 文件权限 | ⬜ | |
| 5. 审计与日志 | ⬜ | |
| 6. 内核参数 | ⬜ | |
| 7. 服务最小化 | ⬜ | |
| 8. Fail2Ban | ⬜ | |
| 9. 文件完整性 | ⬜ | |
| 10. 定期扫描 | ⬜ | |

> ✅ = 已加固 | ⚠ = 需注意 | ❌ = 待处理

---

## 参考资料

- [CIS Ubuntu Linux 24.04 LTS Benchmark](https://www.cisecurity.org/benchmark/ubuntu_linux/)
- [Ubuntu Security documentation](https://ubuntu.com/security)
- [AIDE 官方文档](https://aide.github.io/)
- [Fail2Ban 官方 Wiki](https://www.fail2ban.org/wiki/index.php/Main_Page)
- [CIS Controls](https://www.cisecurity.org/controls/)
