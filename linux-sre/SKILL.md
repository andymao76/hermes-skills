---
name: linux-sre
description: Linux 高级运维/SRE — 系统内核调优、性能剖析、网络排障、存储管理、容器编排、高可用架构
priority: high
category: devops
---

# Linux SRE

Linux 高级运维/SRE 技能。覆盖系统内核调优、进程/CPU/内存深度管理、存储与文件系统、网络专家级排障、安全审计、性能可观测性、自动化运维、容器编排、高可用架构。面向生产环境深度运维场景。

---

## 一、系统内核与启动

### 1.1 内核核心机制

| 领域 | 核心概念 | 调试手段 |
|------|---------|---------|
| 进程调度 | CFS 完全公平调度、实时调度 (SCHED_FIFO/RR)、cgroup v2 cpu 控制器 | `/proc/sched_debug`, `/sys/kernel/debug/sched_features` |
| 内存管理 | 虚拟内存/页表/TLB、kswapd/direct reclaim、水位线 min/low/high | `/proc/zoneinfo`, `/proc/pagetypeinfo` |
| 文件系统层 | VFS、inode/dentry 缓存、page cache、回写机制 (dirty_expire/dirty_background) | `/proc/sys/vm/dirty_*`, slabtop |
| 网络栈 | sk_buff、NAPI 轮询、GRO/GSO 卸载、XDP 旁路 | ethtool -k, `/proc/net/softnet_stat` |

### 1.2 内核参数调优

```bash
# 查看当前值
sysctl -a | grep -E 'vm.swappiness|vm.dirty_ratio|net.core.somaxconn'

# 常用调优（根据场景选配）
vm.swappiness = 10                    # 尽量避免 swap
vm.dirty_ratio = 20                   # 脏页占内存比上限
vm.dirty_background_ratio = 5         # 后台写回触发点
net.core.somaxconn = 65535            # listen 队列上限
net.ipv4.tcp_tw_reuse = 1             # TIME_WAIT 复用（NAT 环境慎用）
net.ipv4.tcp_fin_timeout = 15         # FIN_WAIT2 超时
net.core.rmem_max = 16777216          # socket 接收缓冲最大
net.core.wmem_max = 16777216          # socket 发送缓冲最大

# 固化到 /etc/sysctl.d/99-custom.conf
cat > /etc/sysctl.d/99-custom.conf << 'EOF'
vm.swappiness=10
vm.dirty_ratio=20
net.core.somaxconn=65535
EOF
sysctl --system
```

**注意**：容器环境下 net.* 参数非 namespace 化（除 `net.ipv4.ip_local_port_range` 等少数），宿主机调优影响所有容器。

### 1.3 systemd 深度

```bash
# unit 依赖分析
systemctl list-dependencies sshd.service
systemctl list-dependencies --reverse sshd.service

# 定时器管理
systemctl list-timers --all
systemctl cat systemd-tmpfiles-clean.timer

# journald 存储与清理
journalctl --disk-usage
journalctl --vacuum-size=500M
journalctl --vacuum-time=30d

# 配置 /etc/systemd/journald.conf
SystemMaxUse=500M
MaxRetentionSec=30day
```

### 1.4 内核崩溃分析（kdump）

```bash
# 安装 kdump
apt install kdump-tools crash makedumpfile

# 配置 crash 内核大小（建议 64M-128M）
# /etc/default/kdump-tools: KDUMP_RESERVED_MEM=128M

# 触发 crash 测试
echo c > /proc/sysrq-trigger

# 分析 vmcore
crash /usr/lib/debug/boot/vmlinux-$(uname -r) /var/crash/*/vmcore
crash> bt                          # 查看调用栈
crash> vm                          # 进程内存
crash> log                         # 内核日志
```

---

## 二、进程、CPU 与内存深度管理

### 2.1 CPU 调度与分析

```bash
# CPU 亲和性
taskset -pc 0-3 <PID>             # 绑定到 core 0-3
# cpuset cgroup v2
echo "0-3" > /sys/fs/cgroup/<group>/cpuset.cpus

# 优先级
nice -n -5 ./process               # 启动时设 nice
renice -n -5 -p <PID>              # 运行时改 nice

# 中断平衡
systemctl status irqbalance
# 查看中断分布
cat /proc/interrupts | awk '{print $1, $2, $3, $NF}'

# CPU 时间片解读（top/pidstat 字段）
# us=用户态, sy=内核态, wa=IO等待, hi=硬中断, si=软中断, st=steal(虚拟化偷取)
pidstat -u -p <PID> 1 5
```

### 2.2 内存泄漏排查

```bash
# /proc/meminfo 解读
# Cached = page cache (文件缓存)
# Buffers = 块设备缓存
# AnonPages = 匿名页(堆/栈)
# MemAvailable ≈ MemFree + 可回收的 page cache

# smaps 分析进程内存
cat /proc/<PID>/smaps | grep -E '^(VmRSS|Pss|Private_)' | head -20
# pmap
pmap -x <PID> | sort -k3 -rn | head -20

# valgrind 内存泄漏
valgrind --leak-check=full --show-leak-kinds=all ./program

# AddressSanitizer (gcc/clang)
gcc -fsanitize=address -g -o program program.c

# 透明大页 THP — 对数据库(MySQL/MongoDB)建议关闭
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# cgroup OOM 调整
echo -500 > /proc/<PID>/oom_score_adj          # 降低被 OOM kill 概率
echo -1000 > /proc/<PID>/oom_score_adj          # 禁止 OOM kill
```

### 2.3 进程追踪与调试

```bash
# strace — 追踪系统调用
strace -c -p <PID>                # 统计系统调用频率/耗时
strace -e trace=network -p <PID>  # 只追踪网络相关调用
strace -tt -T -p <PID>            # 显示时间戳与耗时

# perf — CPU 采样与火焰图
perf record -F 99 -p <PID> -g --sleep 30
perf script > out.perf
# 使用 FlameGraph 生成火焰图
git clone https://github.com/brendangregg/FlameGraph
perl FlameGraph/stackcollapse-perf.pl out.perf > out.folded
perl FlameGraph/flamegraph.pl out.folded > flame.svg

# bpftrace — 动态追踪
bpftrace -e 'tracepoint:syscalls:sys_enter_open { printf("%s %s\n", comm, str(args->filename)); }'
# bcc 工具集
execsnoop-bpfcc                   # 实时追踪新进程
opensnoop-bpfcc                   # 实时追踪文件打开
tcptop-bpfcc                      # TCP 连接排名

# ftrace
cd /sys/kernel/debug/tracing
echo function > current_tracer
echo schedule > set_ftrace_filter  # 追踪特定函数
echo 1 > tracing_on
cat trace
```

---

## 三、存储与文件系统

### 3.1 IO 栈深度分析

Linux 存储栈：VFS → 文件系统 → Block Layer (IO调度器) → 驱动

```bash
# IO 调度器查看/设置
cat /sys/block/sda/queue/scheduler
echo mq-deadline > /sys/block/sda/queue/scheduler

# 调度器适用场景
# mq-deadline：通用场景
# kyber：延迟敏感的 SSD
# bfq：桌面/交互式，带宽公平
# none：NVMe 等高性能设备（硬件自己做调度）

# blktrace — 块层 IO 追踪
blktrace -d /dev/sda -o trace
blkparse trace.blktrace.* -o trace.txt

# iostat 深度解读
iostat -x 1
# await = IO 平均耗时(ms) — 含排队+服务时间
# svctm ≈ 不可靠(现代 SSD 已无意义)
# %util = 设备忙闲比，100% 不一定饱和(多队列设备)
# 真正看饱和：r_await/w_await 是否明显 > 基准值

# fio 压测
fio --name=test --rw=randread --bs=4k --size=1G --runtime=60 --iodepth=32 --numjobs=4
fio --name=test --rw=write --bs=1M --size=10G --runtime=120 --iodepth=16
```

### 3.2 文件系统

```bash
# ext4
tune2fs -l /dev/sda1 | grep -E 'Filesystem|Inode|Blocks'
# 检查碎片
e2fsck -fn /dev/sda1
# inode 耗尽排查
df -i /var

# xfs
xfs_info /dev/sda1
xfs_repair -n /dev/sda1            # 只检查不修复

# btrfs 快照
btrfs subvolume snapshot /data /data/snap-$(date +%Y%m%d)
btrfs send /data/snap-20260101 | btrfs receive /backup/

# 挂载优化
mount -o noatime,nodiratime,discard /dev/sda1 /data
# noatime：不更新最后访问时间（大幅减少写 IO）
# nodiratime：同上，针对目录
# discard：TRIM 对齐（SSD）

# 大目录优化
# ext4: tune2fs -O dir_index /dev/sda1  (创建索引)
# xfs: xfs_io -c 'extsize 65536' /large-dir  (扩大 extent)
```

### 3.3 高级存储

```bash
# LVM thin provisioning
lvcreate -L 100G -T vg01/thinpool
lvcreate -V 50G -T vg01/thinpool -n thinvol1
# 快照
lvcreate -s -L 10G -n snap01 vg01/lv01

# mdraid
mdadm --detail /dev/md0
mdadm --manage /dev/md0 --add /dev/sdc  # 热备加入
cat /proc/mdstat

# iSCSI
iscsiadm -m discovery -t st -p 192.168.1.100
iscsiadm -m node --login

# Ceph 基础
ceph osd perf
ceph pg stat
ceph pg dump | grep -E 'active|degraded'
```

---

## 四、网络专家级管理

### 4.1 TCP 协议栈调优

```bash
# TIME_WAIT 堆积排查
ss -tan state time-wait | wc -l
# 超过 3 万需要关注

# 拥塞控制
sysctl net.ipv4.tcp_congestion_control
# 推荐 bbr（高带宽高延迟场景）
echo net.ipv4.tcp_congestion_control=bbr >> /etc/sysctl.d/99-tcp.conf

# 网络命名空间
ip netns add ns1
ip link add veth0 type veth peer name veth1
ip link set veth1 netns ns1
ip netns exec ns1 ip addr add 10.0.0.2/24 dev veth1
ip netns exec ns1 ip link set veth1 up

# 策略路由
echo 100 custom >> /etc/iproute2/rt_tables
ip rule add from 10.0.0.0/24 table custom
ip route add default via 10.0.1.1 table custom
```

### 4.2 包过滤与防火墙

```bash
# iptables 深度
iptables -L -n -v --line-numbers
iptables -t nat -L -n -v
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m recent --name badguy --set -j DROP

# nftables 现代实践
nft list ruleset
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0 \; }
nft add rule inet filter input ct state established,related accept

# conntrack 表满排查
sysctl net.netfilter.nf_conntrack_count
sysctl net.netfilter.nf_conntrack_max
# 如果 count 达到 max 的 90%，业务可能出现丢包
# 调优
echo net.netfilter.nf_conntrack_max=1048576 >> /etc/sysctl.d/99-conntrack.conf
```

### 4.3 网络诊断

```bash
# tcpdump 高级
tcpdump -i eth0 -s 0 -w capture.pcap
tcpdump -r capture.pcap 'tcp[tcpflags] & (tcp-syn|tcp-ack) == tcp-syn'  # SYN 包
tcpdump -nn -i eth0 'host 10.0.0.1 and port 443'

# ss 深度
ss -tiepna                        # TCP 详细信息(ino,timer,mem)
ss -x -a                          # UNIX socket 诊断
# Recv-Q/Send-Q 非零但不阻塞：可能是 unix socket 缓冲区积压

# 延迟排查
mtr --report 8.8.8.8              # 路径逐跳延迟
hping3 -S -p 80 --tcp-timestamp 192.168.1.1  # TCP 时间戳测量

# 流量控制模拟（测试用）
tc qdisc add dev eth0 root netem delay 100ms 20ms
tc qdisc add dev eth0 root netem loss 10%
tc qdisc del dev eth0 root

# RSS/RPS 调优
ethtool -l eth0                   # 查看队列数
ethtool -L eth0 combined 8        # 调整队列数
# RPS（软件均衡）
echo f > /sys/class/net/eth0/queues/rx-0/rps_cpus
```

### 4.4 网卡与驱动

```bash
# 网卡信息
ethtool eth0                       # 速率/双工
ethtool -i eth0                    # 驱动版本
ethtool -S eth0 | grep error       # 错误统计
ethtool -k eth0                    # 硬件卸载能力
# GRO/GSO 开启后能大幅降低 CPU 负载
ethtool -K eth0 gro on gso on tso on

# 排查丢包（网卡/内核/应用三层）
ethtool -S eth0 | grep -i drop     # 网卡层丢包
cat /sys/class/net/eth0/statistics/rx_dropped  # 内核 socket 缓冲满丢包
nstat -az | grep TcpExt           # TCP 扩展统计
# TcpExtListenOverflows / TcpExtListenDrops → application backlog 满
```

---

## 五、安全硬化与审计

### 5.1 强制访问控制

```bash
# SELinux 排查
ausearch -m avc -ts recent        # 查询最近被拒绝的操作
audit2allow -w -a                  # 生成允许策略
audit2allow -a -M mymodule         # 生成模块
semodule -i mymodule.pp
restorecon -Rv /var/www           # 恢复文件标签

# AppArmor
aa-status                          # 查看所有 profile
aa-enforce /path/to/bin            # 强制模式
aa-complain /path/to/bin           # 只记录不拒绝
journalctl -x | grep apparmor      # 查看拒绝日志

# seccomp（容器用）
# Docker 默认 seccomp profile：放行约 300 个 syscall
# 自定义 profile
docker run --security-opt seccomp=custom.json ...
```

### 5.2 auditd 与日志

```bash
# 监控关键文件变更
auditctl -w /etc/passwd -p wa -k passwd_changes
auditctl -w /etc/shadow -p wa -k shadow_changes

# 监控系统调用
auditctl -a always,exit -S execve -k command_exec

# 查看日志
ausearch -k passwd_changes -ts today

# SUID/SGID 扫描
find / -perm -4000 -o -perm -2000 2>/dev/null | xargs -I{} stat -c "%a %n" {}
```

### 5.3 加密与证书

```bash
# OpenSSL 自建 CA
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -days 3650 -out ca.crt

# 签发证书
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

# LUKS 磁盘加密
cryptsetup luksFormat /dev/sdb1
cryptsetup open /dev/sdb1 secret
mkfs.ext4 /dev/mapper/secret
mount /dev/mapper/secret /mnt/secret
```

---

## 六、性能调优与可观测性

### 6.1 方法论

| 方法 | 全称 | 核心理念 |
|------|------|---------|
| USE | Utilization/Saturation/Errors | LL 逐个资源检查利用率、饱和度和错误 |
| RED | Rate/Errors/Duration | LL 服务粒度：请求率、错误率、响应时间 |

**60s 性能检查清单（Brendan Gregg）— 理解原理而非背命令：**
1. `uptime` — 负载均值（结合 CPU 核数看）
2. `dmesg -T | tail` — 内核错误/OOM/软锁
3. `vmstat 1` — runqueue/swap/io/system
4. `mpstat -P ALL 1` — 单核利用率不均
5. `pidstat 1` — 异常进程
6. `iostat -xz 1` — IO 等待与设备饱和
7. `free -m` — 内存水位
8. `sar -n DEV 1` — 网络吞吐与丢包
9. `sar -n TCP,ETCP 1` — TCP 重传/连接失败
10. `top` — 概览

### 6.2 火焰图与可观测性

```bash
# off-CPU 分析（进程在等什么）
perf record -e sched:sched_switch -g -a sleep 10
# 生成 off-CPU 火焰图（方法同 CPU 火焰图，但追踪的是切换事件）

# memory 火焰图
perf record -e memory:*
# 或使用 bcc 的 memleak
memleak-bpfcc -p <PID> -a
```

### 6.3 基准测试

```bash
# sysbench
sysbench cpu run
sysbench memory run
sysbench fileio --file-total-size=10G prepare
sysbench fileio --file-test-mode=rndrw run

# stress-ng
stress-ng --cpu 4 --io 2 --vm 2 --vm-bytes 1G --timeout 30s

# iperf3 网络
iperf3 -s                            # 服务端
iperf3 -c 192.168.1.100 -P 4 -t 30   # 客户端并行 4 流
```

---

## 七、自动化与配置管理

### 7.1 Ansible 高级

```yaml
# 动态 inventory：使用脚本或 AWS EC2 插件
# ansible-inventory --list  # 查看动态 inventory

# 自定义模块
# library/my_module.py
#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
def main():
    module = AnsibleModule(argument_spec=dict(name=dict(type='str', required=True)))
    module.exit_json(changed=False, result=f"Hello {module.params['name']}")
if __name__ == '__main__': main()

# Playbook 编排策略
ansible-playbook site.yml -f 10           # 10 个并行 fork
ansible-playbook --step                   # 交互式确认每步
```

### 7.2 Terraform 运维

```hcl
# 状态管理与模块化
terraform state list
terraform state mv module.old module.new
terraform import aws_instance.web i-12345678
```

### 7.3 CI/CD

- 蓝绿发布：通过负载均衡切换流量组
- 金丝雀：逐步放大新版本流量比例（Istio/nginx upstream）
- GitLab Runner 维护：`gitlab-runner register`, `/etc/gitlab-runner/config.toml`

---

## 八、容器与编排

### 8.1 容器运行时

```bash
# cgroup v2 + namespace 手动实验
# 创建新 mount namespace
unshare --mount --fork /bin/bash

# 隔离 PID
unshare --pid --fork --mount-proc /bin/bash

# Docker 底层
docker inspect <container> | jq '.[0].GraphDriver'  # 存储驱动
# overlay2 分层：/var/lib/docker/overlay2/

# containerd
ctr images pull docker.io/library/nginx:alpine
ctr run docker.io/library/nginx:alpine nginx1
```

### 8.2 Kubernetes 运维

```bash
# etcd 备份
ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /backup/etcd-$(date +%Y%m%d).db

# 证书到期检查
kubeadm certs check-expiration

# 节点 NotReady 排查
kubectl describe node <node>
journalctl -u kubelet -n 50 --no-pager
# 常见原因：CNI 未就绪、磁盘压力、kubelet 证书过期

# Pod 挂起排查
kubectl describe pod <pod>
# 常见：资源不足(Pending)、镜像拉取失败(ImagePullBackOff)、配置错误(CrashLoopBackOff)

# RBAC
kubectl create clusterrolebinding admin-binding --clusterrole=cluster-admin --user=user@example.com

# OPA 策略
# policies/ deny_privileged.rego
package kubernetes.admission
deny[msg] {
    input.request.object.spec.containers[_].securityContext.privileged
    msg = "Privileged containers not allowed"
}

# 大规模集群
# etcd 调优：使用 SSD、--quota-backend-bytes=8589934592(8G)
# kube-apiserver：--max-mutating-requests-inflight=1000
```

### 8.3 服务网格与可观测

```bash
# Istio sidecar 注入
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled

# Prometheus Recording Rules
groups:
  - name: kubernetes_compute
    rules:
      - record: node:memory_usage_bytes:ratio
        expr: |
          1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Grafana Loki + Promtail
loki:
  # docker-compose 示例
  - docker run --name=loki -p 3100:3100 grafana/loki
  - docker run --name=promtail grafana/promtail -config.file=/etc/promtail/config.yml

# OpenTelemetry + Jaeger
# agent 侧注入 SDK，发送到 Jaeger collector:4317
```

---

## 九、高可用与灾难恢复

### 9.1 负载均衡

```bash
# LVS DR 模式（直接路由）
ipvsadm -A -t 10.0.0.10:80 -s rr
ipvsadm -a -t 10.0.0.10:80 -r 192.168.1.11:80 -g
ipvsadm -a -t 10.0.0.10:80 -r 192.168.1.12:80 -g

# HAProxy 配置
# frontend 入 → backend pool → 健康检查
frontend web-in
    bind *:443 ssl crt /etc/ssl/certs/server.pem
    use_backend app_servers

backend app_servers
    balance leastconn
    server app1 10.0.0.1:8080 check inter 3s fall 2 rise 3

# Nginx 反向代理深度
upstream backend {
    least_conn;
    keepalive 32;
    server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8080 backup;
}
server {
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

### 9.2 集群与共享存储

```bash
# Pacemaker + Corosync
pcs status
pcs resource create web_vip ocf:heartbeat:IPaddr2 ip=10.0.0.100 cidr_netmask=24 --group web_group
pcs constraint colocation add web_vip with web_service INFINITY

# DRBD
drbdadm status
drbdadm primary r0 --force          # 强制升主
mount /dev/drbd0 /mnt/data
```

### 9.3 备份与恢复

```bash
# PITR (PostgreSQL 示例)
# 开启 WAL 归档
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
# 恢复
pg_ctl -D /data/pgdata stop
cp /backup/base_backup/* /data/pgdata/
touch /data/pgdata/recovery.signal
# recovery.conf: restore_command = 'cp /backup/wal/%f %p'

# 异地容灾
# RTO 恢复时间目标 / RPO 恢复点目标
# 设计原则：
# - RTO < 4h → 冷备+脚本自动恢复
# - RTO < 15min → 主备切换（同步复制）
# - RPO = 0 → 同步复制/共享存储
```

---

## 十、远程服务器维护（通过 Hermes/SSH）

### 10.1 SSH 配置规范

SSH config 是管理多台远端机器的核心入口，应集中配置：

```
# ~/.ssh/config
Host tencent
  HostName 124.222.206.209
  User andymao
  IdentityFile ~/.ssh/tencent-cloud.pem
  StrictHostKeyChecking no

Host office
  HostName 192.168.1.x
  User andymao

Host dev
  HostName dev.example.com
  User root
  IdentityFile ~/.ssh/dev-key
```

### 10.2 一键巡检（多服务器并行）

```bash
for h in tencent office dev; do
  echo "=== $h ==="
  ssh $h "
    echo 'UPTIME:'; uptime
    echo 'DISK:'; df -h / | tail -1
    echo 'MEM:'; free -h | grep Mem
    echo 'LOAD:'; ps aux --sort=-%cpu | head -3
  " 2>&1
done
```

### 10.3 Hermes 定时自动巡检

创建 cron 任务让 Hermes 每天自动检查远端服务器：

```bash
#!/bin/bash
# ~/.hermes/scripts/remote-healthcheck.sh
SERVER="tencent"
ssh $SERVER "
  echo '=== UPTIME ==='; uptime
  echo '=== DISK ==='; df -h /
  echo '=== MEMORY ==='; free -h
  echo '=== TOP CPU ==='; ps aux --sort=-%cpu | head -5
  echo '=== LISTENING ==='; ss -tlnp | grep -E ':(80|443|3000|8080|9099) '
" 2>&1
```

注册 cron 任务：
```bash
hermes cron create "每天9点远程巡检" --script remote-healthcheck.sh
```

### 10.4 远程终端 Backend（高级方案）

将 Hermes 的 `terminal` 工具默认指向远程服务器，所有命令在远端执行：

```bash
hermes config set terminal.backend ssh
hermes config set terminal.ssh_host tencent
hermes config set terminal.ssh_user andymao
```

配置后，`read_file`、`write_file`、`patch`、`terminal` 全部在远端执行。

### 10.5 常见远程运维场景

| 场景 | 命令 |
|------|------|
| 检查磁盘 | `ssh tencent "df -h"` |
| 查看日志 | `ssh tencent "tail -50 /var/log/nginx/error.log"` |
| 检查进程 | `ssh tencent "ps aux --sort=-%mem | head 10"` |
| 检查 Docker | `ssh tencent "docker ps --format 'table {{.Names}}\t{{.Status}}'"` |
| 重启服务 | `ssh tencent "sudo systemctl restart nginx"` |
| 查看网络 | `ssh tencent "ss -tlnp"` |

### 10.6 远程调用远端 Hermes Agent

当目标服务器上也运行着 Hermes，可以通过 SSH 直接调用远端 Hermes 的 CLI：

```bash
# 远端 Hermes 属于不同用户时（如 ubuntu），需要 sudo + 正确设置 HOME/HERMES_HOME
ssh tencent "sudo -u ubuntu bash -c 'cd /home/ubuntu && \
  HERMES_HOME=/home/ubuntu/.hermes HOME=/home/ubuntu \
  /home/ubuntu/.hermes/hermes-agent/venv/bin/hermes chat -q \"你好\"'"
```

**关键点：**
- `sudo -u ubuntu` — 切到目标用户（否则无权限读 config.yaml/.env）
- `bash -c '...'` — 包住多步命令
- `cd /home/ubuntu` — 工作目录也切过去，避免 `.git` 权限错误
- `HERMES_HOME=/home/ubuntu/.hermes` — 指定远端 Hermes 配置目录
- `HOME=/home/ubuntu` — 修正 HOME 环境变量（SSH 登录默认是本地用户名）

**简化方案：** 在 `~/.bashrc` 添加函数：
```bash
rh() {
  ssh tencent "sudo -u ubuntu bash -c 'cd /home/ubuntu && \
    HERMES_HOME=/home/ubuntu/.hermes HOME=/home/ubuntu \
    /home/ubuntu/.hermes/hermes-agent/venv/bin/hermes chat -q \"$*\"'"
}
```
之后只需 `rh "检查磁盘状态"`。

**使用场景：** 本地 Hermes 拿到需要操作的远端上下文后，委派远端 Hermes 执行本地不方便的操作（不同的 provider/api key、不同的网络环境、本地操作远端文件）。两端 Hermes 可以通过 SSH 互相调用，形成分布式 agent 协作。

### 10.7 Hermes Dashboard 自动启动（systemd 用户服务）

将 Dashboard 注册为 systemd 用户服务，随用户登录自动运行：

```ini
# ~/.config/systemd/user/hermes-dashboard.service
[Unit]
Description=Hermes Agent Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=%h/.hermes/hermes-agent/venv/bin/hermes dashboard --port 9119 --no-open
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable hermes-dashboard.service
systemctl --user start hermes-dashboard.service
```

访问 `http://127.0.0.1:9119`。

### 10.8 Hermes 跨实例同步（本地 ↔ 远端）

当本地和远端服务器都运行 Hermes Agent 时，需要在实例间同步三样内容：技能、API Key、记忆。

#### 第一步：发现远端 Hermes 安装位置

SSH 远端后 Hermes 可能运行在**不同用户**下，直接 SSH 的用户目录可能找不到：

```bash
# 探查远端服务器上有哪些用户可能运行了 Hermes
ssh tencent "ls /home/"
# 返回: andymao  ubuntu  lighthouse

# 逐个检查谁的 ~/.hermes/skills/ 有内容
ssh tencent "ls ~/.hermes/skills/ 2>/dev/null | wc -l"          # andymao 用户 → 可能 0
ssh tencent "sudo ls /home/ubuntu/.hermes/skills/ 2>/dev/null | wc -l"  # ubuntu 用户 → 82 个技能
```

**常见模式：** 远端 Hermes 作为 gateway 运行时可能使用独立的系统用户（如 `ubuntu`），SSH 登录用户（如 `andymao`）需要 `sudo` 才能访问。

#### 第二步：对比两端的技能差异（同步前先看清楚）

```bash
# 远端技能列表
ssh tencent "sudo ls /home/ubuntu/.hermes/skills/" | sort > /tmp/remote_skills.txt

# 本地技能列表
ls ~/.hermes/skills/ | sort > /tmp/local_skills.txt

# 远端有但本地没有 → 需要拉取的
echo "--- 远端有 本地没有 ---"
comm -23 /tmp/remote_skills.txt /tmp/local_skills.txt

# 本地有但远端没有 → 需要推送的
echo "--- 本地有 远端没有 ---"
comm -13 /tmp/remote_skills.txt /tmp/local_skills.txt
```

#### A. 同步 Skills

**方向 A1：本地 → 远端（Push）**

```bash
# 本地打包
cd ~/.hermes && tar czf /tmp/hermes-skills.tar.gz skills/

# 传到远端
scp /tmp/hermes-skills.tar.gz tencent:/tmp/

# 远端解压（注意目标用户 ownership）
ssh tencent "sudo tar xzf /tmp/hermes-skills.tar.gz -C /home/ubuntu/.hermes/ \
  && sudo chown -R ubuntu:ubuntu /home/ubuntu/.hermes/skills/"
```

**方向 A2：远端 → 本地（Pull）** — 当远端积累了本地没有的技能时

```bash
# 方式一：tar 管道直传（推荐，无需中间文件）
ssh tencent "sudo tar czf - -C /home/ubuntu/.hermes/skills/ \
  <技能名1> <技能名2> ..." | tar xzf - -C ~/.hermes/skills/

# 全量拉取（所有远端技能）
ssh tencent "sudo tar czf - -C /home/ubuntu/.hermes/skills/ \
  $(ssh tencent 'sudo ls /home/ubuntu/.hermes/skills/' | tr '\n' ' ')" \
  | tar xzf - -C ~/.hermes/skills/

# 差异拉取（仅同步远端有而本地没有的）
MISSING=$(comm -23 <(ssh tencent "sudo ls /home/ubuntu/.hermes/skills/" | sort) \
                   <(ls ~/.hermes/skills/ | sort) | tr '\n' ' ')
if [ -n "$MISSING" ]; then
  ssh tencent "sudo tar czf - -C /home/ubuntu/.hermes/skills/ $MISSING" \
    | tar xzf - -C ~/.hermes/skills/
  echo "已同步: $MISSING"
else
  echo "两边的技能一致，无需同步"
fi
```

**关键点（方向 A2）：**
- `sudo tar czf -` — 用 sudo 读取 ubuntu 用户的文件
- `-C /home/ubuntu/.hermes/skills/ <names>` — 指定源目录和技能名
- `| tar xzf - -C ~/.hermes/skills/` — 管道直接解压到本地，无需中间文件
- `$(ssh ...)` 子命令展开动态技能列表

#### B. 同步 API Key（.env）

```bash
scp ~/.hermes/.env tencent:/tmp/hermes-env
ssh tencent "sudo cp /tmp/hermes-env /home/ubuntu/.hermes/.env \
  && sudo chown ubuntu:ubuntu /home/ubuntu/.hermes/.env \
  && sudo chmod 600 /home/ubuntu/.hermes/.env"
```

**安全注意事项：**
- `.env` 包含敏感凭据，传输后立即 `chmod 600`
- `scp` 传输是加密的（SSH 通道）
- 不要在命令历史或日志中暴露 API Key

#### C. 同步 Knowledge 与 Memory

知识文件直接复制到远端：
```bash
# 创建知识目录
ssh tencent "sudo mkdir -p /home/ubuntu/.hermes/knowledge && \
  sudo chown ubuntu:ubuntu /home/ubuntu/.hermes/knowledge -R"

# 推送知识文件
scp ~/knowledge/**/*.md tencent:/tmp/
ssh tencent "sudo cp /tmp/*.md /home/ubuntu/.hermes/knowledge/ && \
  sudo chown -R ubuntu:ubuntu /home/ubuntu/.hermes/knowledge"
```

Memory 无法直接文件同步（存储在 SQLite 中），需要让远端 Hermes 通过对话学习：
```bash
# 通过远端 Hermes CLI 让它在 memory 中记住
ssh tencent "sudo -u ubuntu bash -c 'cd /home/ubuntu && \
  HERMES_HOME=/home/ubuntu/.hermes HOME=/home/ubuntu \
  /home/ubuntu/.hermes/hermes-agent/venv/bin/hermes chat -q \"请记住：...\"'"
```

#### D. 验证同步结果

```bash
# 验证本地技能数（拉取后）
echo "本地技能数：$(ls ~/.hermes/skills/ | wc -l)"

# 验证远端 Hermes 是否可用
ssh tencent "sudo -u ubuntu bash -c 'cd /home/ubuntu && \
  HERMES_HOME=/home/ubuntu/.hermes HOME=/home/ubuntu \
  /home/ubuntu/.hermes/hermes-agent/venv/bin/hermes chat -q \"你好\"'"

# 重新加载技能（在 Hermes 会话中）
# /reload-skills
```

#### Pitfalls

- **跨用户访问**：远端 Hermes 可能运行在非 SSH 用户下（如 `ubuntu`），必须用 `sudo` 读写其 `~/.hermes/` 目录
- **SSH 用户的 `~/.hermes/` 可能是空的**：不等于远端没装 Hermes，需要检查其他用户
- **技能所有权**：`sudo tar xzf` 解压后文件 owner 是 root，需 `chown` 回目标用户，否则 Hermes 无法写入（curator 等操作会报权限错误）
- **大技能包**：如果 `du -sh ~/.hermes/skills/` 超过 50MB，优先用差异同步而非全量拉取
- **同步后需要 reload**：当前 Hermes 会话中运行 `/reload-skills` 才能看到新技能，新会话自动加载

### 10.9 安全注意事项

- **SSH key 权限**：`chmod 600 ~/.ssh/*.pem`
- **避免明文密码**：始终用 key 认证，不在命令中传密码
- **sudo 需求**：涉及 `sudo` 的操作 worker 无法自动执行（无交互式密码输入），需预先写入 scripts 并用 `NOPASSWD` sudoers 配置，或通过 cron 脚本执行
- **连接保活**：SSH config 加 `ServerAliveInterval 60` 防止长任务超时断开

## 十一、脚本与运维开发

### 10.1 Shell 专家

```bash
# 严格模式
set -euo pipefail

# trap 信号处理
cleanup() { rm -f /tmp/lockfile; exit; }
trap cleanup INT TERM EXIT

# 并发控制
(
  flock -n 200 || exit 1
  # 临界区
  echo "locked" > /tmp/lockfile
) 200>/tmp/lockfile

# xargs 并行
# 小心：-P 过多导致 IO 竞争
find . -name "*.log" | xargs -P 4 -I{} gzip {}

# JSON/YAML 处理
curl -s http://example.com/api | jq '.data[] | {id, name}'
kubectl get pod -o yaml | yq eval '.spec.containers[].image'
```

### 10.2 Python 运维

```python
# psutil 系统信息
import psutil
cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
mem = psutil.virtual_memory()
disk_io = psutil.disk_io_counters()

# subprocess 安全执行
import subprocess
result = subprocess.run(['journalctl', '-u', 'nginx', '-n', '10'],
                       capture_output=True, text=True, check=True)
```

### 10.3 GitOps

```bash
# Conventional Commits
# feat: add user authentication
# fix: handle OOM on large requests
# chore(deps): bump prometheus-client to 0.17.0

# 文档即代码（Mermaid）
# ```mermaid
# graph LR
#   A[Ingress] --> B[Service]
#   B --> C[Pod]
# ```
```

---

## 十一、事故管理与流程

### 事故报告（Postmortem）模板

```
# 事故标题：XXXXXX

## 概述
- 日期: YYYY-MM-DD
- 持续时间: Xh Ym
- 影响范围: X% 用户受影响
- 严重等级: P0/P1/P2

## 时间线
- HH:MM 告警触发
- HH:MM 工程师介入
- HH:MM 定位根因
- HH:MM 恢复服务

## 根因分析
- 直接原因: ...
- 根本原因: ... (5 Whys)

## 改进项
- [ ] 监控补充
- [ ] 自动化恢复
- [ ] 文档完善
```

### 知识沉淀

- Runbook 应覆盖：告警→诊断→恢复→验证 四步
- 混沌工程入门：Chaos Monkey（随机杀实例）/ Litmus（K8s 注入）

---

## 相关技能

| 技能 | 覆盖领域 |
|------|---------|
| network-troubleshooting | 网络排障专项（代理/DNS/连通性） |
| monitoring-expert | 可观测性专项（Prometheus/Grafana/OTel） |
| linux-backup | 备份策略与 Rsync |
| linux-disk-management | 磁盘挂载与分区管理 |

## 注意事项

1. **内核调优要验证**：改完 `sysctl` 后用实际业务压测确认效果
2. **先确认再改**：调优前记录基线值（`sysctl -a > /tmp/sysctl_baseline`）
3. **不要迷信大页**：THP 对数据库有负面影响，确认场景后用 `madvise` 模式
4. **OOM 调优警告**：`oom_score_adj=-1000` 可能导致宿主机卡死（进程永不释放内存）
5. **生产慎用** `net.ipv4.tcp_tw_reuse`：NAT 环境可能导致连接复用冲突
