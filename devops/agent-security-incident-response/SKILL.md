---
name: 'agent-security-incident-response'
version: '1.0.0'
description: 'Agent 安全事件应急响应剧本 — 涵盖事件分级、响应流程、分类剧本、取证速查、上报模板与事后复盘'
author: 'Hermes Agent'
created: '2026-06-17'
category: 'devops/security'
depends_on:
  - 'security-governance-framework'
  - 'security-audit-sop'
tags:
  - 'security'
  - 'incident-response'
  - 'playbook'
  - 'soc'
  - 'sre'
---

# Agent 安全事件应急响应剧本

> 本剧本适用于 Hermes Agent 日常运行中可能遇到的安全事件。所有响应动作均应在 Agent 环境下可执行，优先使用内置工具链（journalctl、auditd、find、grep 等），减少对外部系统的依赖。

---

## 1. 事件分级（P0–P3）

| 级别 | 名称 | 定义 | 响应时限 | 示例 |
|------|------|------|----------|------|
| **P0** | 严重（Critical） | 导致 Agent 服务中断、敏感数据已泄露、系统被未授权控制 | ≤ 15 分钟 | API Key 明文泄漏到公共仓库；SSH Key 被新增且被外部连接；Cron 中被插入反弹 Shell |
| **P1** | 高（High） | 存在明确入侵迹象或已造成局部影响 | ≤ 30 分钟 | MCP 被异常调用执行高危操作；配置文件被篡改导致权限提升 |
| **P2** | 中（Medium） | 可疑行为但尚未确认损失，需进一步调查 | ≤ 4 小时 | Cron 中出现不明任务；关键文件被非预期删除 |
| **P3** | 低（Low） | 安全告警但无明显风险，需记录及观察 | ≤ 24 小时 | 权限审计发现异常但无实际行为；日志中有可疑扫描 |

### 升级规则

- P3 事件 24 小时内未闭环 → 自动升级为 P2
- P2 事件若发现数据泄露或横向移动 → 立即升级 P1 或 P0
- 涉及同一系统的多个 P2 事件 → 合并升级评估

---

## 2. 应急响应流程

### 流程概览

```
Triage (分类) → Contain (抑制) → Eradicate (根除) → Recover (恢复) → Postmortem (复盘)
```

### 2.1 Triage — 分类

**目标：5 分钟内确认事件类型、影响范围、紧急程度**

```bash
# 1. 取当前 Agent 状态快照
ps aux | grep -E '(hermes|agent)' --no-headers
systemctl --user status hermes-agent 2>/dev/null || systemctl status hermes-agent 2>/dev/null

# 2. 最近的活动日志
journalctl -u hermes-agent --since "5 min ago" --no-pager -n 50 2>/dev/null

# 3. 检查异常进程/连接
ss -tlnp 4 2>/dev/null  # 监听端口
ss -tunp 2>/dev/null    # 活跃连接
lsof -i -n -P 2>/dev/null | grep -E '(hermes|agent)'

# 4. 检查文件变更（最近 1 小时）
find ~/.hermes -mmin -60 -type f -ls 2>/dev/null
find ~/.ssh -mmin -60 -type f -ls 2>/dev/null

# 5. 检查 Cron 变更
crontab -l 2>/dev/null
ls -la /var/spool/cron/crontabs/ 2>/dev/null
systemctl list-timers --all --no-pager 2>/dev/null
```

**Triage 输出模板：**

```
事件 ID: IR-{YYYYMMDD}-{序号}
时间检测到: {ISO8601 时间戳}
事件级别: P0/P1/P2/P3
事件类型: {API Key 泄露 / Cron 异常 / MCP 滥用 / 文件误删 / 配置篡改 / SSH Key 新增}
影响范围: {影响的主机、用户、服务列表}
初步判定: {一句话风险摘要}
状态: Active / Mitigated / Closed
```

### 2.2 Contain — 抑制

**目标：阻止损害扩散，隔离受影响组件**

| 事件类型 | 抑制动作 |
|----------|----------|
| API Key 泄露 | 立即吊销 Key → 轮换所有使用该 Key 的服务 → 审核 Key 权限 |
| Cron 异常 | 禁用所有 user crontab → 逐一审查任务 → 恢复可信 crontab |
| MCP 被滥用 | 切断 MCP 连接 → 禁用可疑 MCP 服务器 → 审计调用历史 |
| 文件误删 | 立即 umount 相关分区（如适用）→ 停止写入 → 从备份恢复 |
| 配置篡改 | 从 Git 或备份恢复配置 → 锁定文件权限 (chmod 400 / chattr +i) |
| SSH Key 新增 | 从 authorized_keys 中删除 → 检查 ~/.ssh 目录权限 → 审核新增来源 |

**通用 Contain 命令：**

```bash
# 立即阻断外部连接
sudo iptables -A INPUT -s <可疑IP> -j DROP 2>/dev/null
sudo ufw deny from <可疑IP> 2>/dev/null

# 隔离进程
kill -STOP <PID>
sudo systemctl stop hermes-agent --now 2>/dev/null

# 快照现场（取证前必须先做）
sudo tar czf /tmp/forensics-$(date +%Y%m%d-%H%M%S).tar.gz \
  ~/.hermes \
  ~/.ssh \
  /var/log/journal/ \
  /var/log/auth.log \
  2>/dev/null
```

### 2.3 Eradicate — 根除

**目标：清除入侵痕迹、修补漏洞、移除后门**

```bash
# 移除可疑 cron 任务
crontab -r
# 或编辑后重新加载
EDITOR=nano crontab -e

# 移除可疑 SSH Key
sed -i '/<可疑Key指纹>/d' ~/.ssh/authorized_keys

# 恢复被篡改的配置
cd ~/.hermes && git checkout -- .  # 如果配置在 Git 中
chmod 600 ~/.ssh/config ~/.hermes/config.yaml 2>/dev/null

# 审计并清理未知 systemd timer/systemd service
systemctl list-units --type=service --state=active --no-pager | grep -vE '(systemd|hermes|ssh|docker)'
systemctl --user list-units --type=service --state=active --no-pager | grep -vE '(hermes)'

# 扫描可疑二进制/脚本
find /tmp /dev/shm /var/tmp -type f \( -perm -o+x -o -name '*.sh' \) -mtime -7 -ls 2>/dev/null
find ~ -name '.*' -type f -mtime -3 -ls 2>/dev/null | grep -vE '(.bash_history|.bashrc|.profile|.git)'
```

### 2.4 Recover — 恢复

**目标：安全恢复服务，确保无残留后门**

```bash
# 恢复服务
sudo systemctl start hermes-agent 2>/dev/null || echo "重启 hermes-agent 服务"
hermes --version 2>/dev/null && hermes status 2>/dev/null

# 验证完整性
cd ~/.hermes
git status 2>/dev/null    # 检查文件是否干净
diff -r . ~/.hermes.backup.$(date +%Y%m%d) 2>/dev/null || echo "建议与备份比较"

# 验证关键路径权限
ls -la ~/.ssh/authorized_keys
ls -la ~/.hermes/config.yaml 2>/dev/null
ls -la /etc/crontab 2>/dev/null

# 确认已无异常连接
ss -tunp 2>/dev/null | grep -vE '(127.0.0.1|::1|ESTAB.*localhost)'
```

**恢复验证清单：**
- [ ] Agent 服务正常运行且响应正常
- [ ] 所有 API Key 已轮换且仅服务于必要范围
- [ ] Cron 任务列表已审核且仅含授权任务
- [ ] SSH authorized_keys 仅含已知 Key
- [ ] 关键配置文件权限为 600 或更严格
- [ ] 系统日志中无持续异常

### 2.5 Postmortem — 复盘

> 详见第 6 节「事后复盘模板」

---

## 3. 各类安全事件响应剧本

### 3.1 API Key 泄露

**触发条件：** 检测到 Key 被提交到公开仓库、日志中出现 Key 被未授权使用、第三方通报

**Triage 命令：**

```bash
# 查找本地 Key 泄漏风险
grep -rn --include='*.{env,json,yaml,yml,toml,conf,ini,md,txt}' \
  -E '(sk-[a-zA-Z0-9]{20,}|api_key|api_key|OPENAI_API_KEY|ANTHROPIC_API_KEY)' \
  ~/.hermes ~/.ssh ~/projects 2>/dev/null | grep -v 'example\|sample\|\.git/'

# 检查 Key 最近使用情况
journalctl -u hermes-agent --since "24 hours ago" | grep -E '(API|token|key|auth)' | tail -30
```

**Contain：**

1. **立即吊销 Key** — 登录对应平台（OpenAI / Anthropic / 其他）吊销 Key
2. **轮换所有关联 Key** — 生成新 Key 并更新配置
3. **审计 Key 权限** — 检查 Key 绑定范围是否过大，缩减至最小必要权限

```bash
# 更新环境配置中的 Key
sed -i 's/OLD_KEY/NEW_KEY/g' ~/.hermes/config.yaml 2>/dev/null
sed -i 's/OLD_KEY/NEW_KEY/g' ~/.env 2>/dev/null
hermes reload 2>/dev/null || systemctl --user restart hermes-agent 2>/dev/null
```

**Eradicate：**

- 从 Git 历史中清除泄漏的 Key（使用 `git filter-branch` 或 `bfg`）
- 检查是否有基于该 Key 创建的后门/持久化机制
- 清理日志文件中可能残留的 Key 明文

**收尾：**

- 检查 Key 的 API 调用历史，确认被窃取后的调用量
- 评估数据泄露范围（Key 的权限能访问哪些数据）
- 通知相关方

---

### 3.2 Cron 异常

**触发条件：** 审计发现不明 cron 任务、crontab 内容变更告警、系统出现周期性异常行为

**Triage 命令：**

```bash
# 列出所有用户的 cron
for user in $(cut -f1 -d: /etc/passwd); do
  crontab -u "$user" -l 2>/dev/null && echo "--- $user ---"
done

# 检查 systemd timer
systemctl list-timers --all --no-pager 2>/dev/null
systemctl --user list-timers --all --no-pager 2>/dev/null

# 检查 anacron / cron.hourly 等
ls -la /etc/cron.hourly/ /etc/cron.daily/ /etc/cron.weekly/ /etc/cron.monthly/ 2>/dev/null
ls -la /etc/cron.d/ 2>/dev/null

# 比对上次记录的 crontab
diff <(crontab -l 2>/dev/null) ~/.hermes/snapshots/crontab.baseline 2>/dev/null
```

**Contain：**

```bash
# 立即清空当前用户 crontab 并备份
crontab -l > /tmp/crontab.backup.$(date +%Y%m%d-%H%M%S)
crontab -r

# 或者只注释可疑行
crontab -l | sed '/可疑命令/s/^/#/' | crontab -
```

**Eradicate：**

```bash
# 逐行审查 crontab 备份
cat /tmp/crontab.backup.* | while read line; do
  echo "检查: $line"
  # 检查是否为已知合法任务
done

# 如果发现恶意 payload，追踪原始文件
grep -r '可疑内容' ~/ /tmp/ /var/tmp/ 2>/dev/null | head -20
```

**Recover：**

```bash
# 恢复仅包含已知合法任务的 crontab
crontab ~/.hermes/snapshots/crontab.known-good

# 添加 crontab 监控
(crontab -l 2>/dev/null; echo "# Crontab完整性监控 - 由 agent-security-incident-response 管理") | crontab -
```

---

### 3.3 MCP 被滥用

**触发条件：** MCP Server 返回异常、MCP 工具被非预期调用、MCP 连接频率异常

**Triage 命令：**

```bash
# 查看当前 MCP 配置
cat ~/.hermes/mcp.json 2>/dev/null || cat ~/.hermes/config.yaml 2>/dev/null | grep -A 20 'mcp'

# 检查 MCP 调用日志
find ~/.hermes/logs/ -name '*.log' -exec grep -l -E '(mcp|MCP|tool_call)' {} \; 2>/dev/null
journalctl -u hermes-agent --since "1 hour ago" | grep -i mcp | tail -50

# 检查 MCP Server 状态
ss -tlnp 2>/dev/null | grep -E '(3000|4000|5000|8000|8080)'  # 常见 MCP 端口
```

**Contain：**

```bash
# 暂时禁用所有 MCP 连接
cp ~/.hermes/mcp.json ~/.hermes/mcp.json.disabled.$(date +%Y%m%d)
echo '{"mcpServers": {}}' > ~/.hermes/mcp.json

# 或只禁用可疑 MCP
# 手动编辑 ~/.hermes/mcp.json，移除或注释可疑 server

hermes reload 2>/dev/null || systemctl --user restart hermes-agent 2>/dev/null
```

**Eradicate：**

- 移除恶意/可疑 MCP Server 配置
- 检查 MCP Server 的源码或二进制文件（如果是从本地运行）
- 更新 MCP 白名单策略

**Recover：**

- 从备份恢复受信任的 MCP 配置
- 逐个启用 MCP Server 并验证行为
- 添加 MCP 调用审计日志

---

### 3.4 文件误删

**触发条件：** 关键文件丢失、Agent 功能异常、文件系统完整性检查失败

**Triage 命令：**

```bash
# 查找最近删除的文件（通过 debugfs 或 extundelete 工具）
sudo debugfs -R "ls -d /home/andymao/.hermes" /dev/sda1 2>/dev/null || echo "需要 root 权限且指定正确设备"

# 检查日志中的删除操作
journalctl -u hermes-agent | grep -E '(unlink|remove|rm |delete|trash)' | tail -30
history | grep -E 'rm |mv |trash' | tail -20

# 检查文件系统可用性
ls -la ~/.hermes/config.yaml 2>/dev/null || echo "config.yaml 不存在"
ls -la ~/.hermes/skills/ 2>/dev/null || echo "skills 目录不存在"
```

**Contain：**

```bash
# 立即卸载受影响分区（如果是独立的）
# sudo umount /dev/sdb1

# 停止写入操作
# sudo mount -o remount,ro /home/andymao/.hermes

# 如果文件系统支持，立即创建 dd 镜像
# sudo dd if=/dev/sda1 of=/tmp/fs-image.dd bs=4M status=progress
```

**Eradicate：**

```bash
# 从 Git 恢复（如果受 Git 管理）
cd ~/.hermes && git log --oneline -5
git checkout HEAD -- path/to/deleted-file

# 从备份恢复
rsync -av ~/backups/hermes/latest/ ~/.hermes/ 2>/dev/null

# 使用 extundelete（需 root）
# sudo extundelete /dev/sda1 --restore-file home/andymao/.hermes/config.yaml
```

**Recover：**

- 验证恢复的文件完整性（checksum 比对）
- 重启 Agent 确认功能正常
- 追加文件系统监控

---

### 3.5 配置篡改

**触发条件：** 配置文件的 checksum/inode 发生变化、Agent 行为异常、配置内容被非预期修改

**Triage 命令：**

```bash
# 检查关键配置文件状态
for f in ~/.hermes/config.yaml ~/.hermes/mcp.json ~/.ssh/config ~/.env; do
  echo "=== $f ==="
  stat "$f" 2>/dev/null || echo "文件不存在"
done

# 查看最近的配置变更
find ~/.hermes ~/.ssh -name '*.yaml' -o -name '*.json' -o -name '*.conf' | \
  xargs ls -la 2>/dev/null | sort -k6,7

# 检查可疑的权限变更
find ~/.hermes ~/.ssh -perm /o+w -ls 2>/dev/null  # 其他用户可写的文件
find ~/.hermes ~/.ssh ! -user "$(whoami)" -ls 2>/dev/null  # 非当前用户的文件

# 比对 Git 状态
cd ~/.hermes && git diff --name-only HEAD 2>/dev/null
```

**Contain：**

```bash
# 从 Git 强制恢复已知良好的配置
cd ~/.hermes && git checkout -- config.yaml mcp.json 2>/dev/null

# 锁定关键文件
chmod 600 ~/.hermes/config.yaml ~/.hermes/mcp.json 2>/dev/null
chattr +i ~/.hermes/config.yaml 2>/dev/null || sudo chattr +i ~/.hermes/config.yaml 2>/dev/null
```

**Eradicate：**

```bash
# 审计所有 config 文件的差异
diff -u ~/.hermes/config.yaml ~/.hermes/config.yaml.bak 2>/dev/null

# 检查是否存在隐藏的 include/import 链
grep -rn 'include\|import\|source\|load' ~/.hermes/config.yaml 2>/dev/null

# 搜索后门配置
grep -E '(hook|callback|webhook|remote|exec|command|script|shell)' ~/.hermes/config.yaml 2>/dev/null | grep -vE '(#|example)'
```

**Recover：**

- 重新应用最小权限配置
- 启用配置完整性监控（inotifywait 或 aide）
- 配置从只读源加载（如 Git 的 `post-checkout` hook）

---

### 3.6 SSH Key 新增

**触发条件：** `authorized_keys` 内容变更告警、SSH 登录审计发现未知 Key、未授权的 SSH 连接

**Triage 命令：**

```bash
# 检查 authorized_keys 状态
ls -la ~/.ssh/authorized_keys
stat ~/.ssh/authorized_keys

# 查看所有 authorized_keys 内容
cat ~/.ssh/authorized_keys

# 查看 SSH 登录日志
journalctl -u sshd --since "7 days ago" | grep -E '(Accepted|Failed|Invalid)' | tail -30
last -i | head -20
sudo cat /var/log/auth.log 2>/dev/null | grep -E '(sshd|ssh)' | tail -20

# 检查所有用户的 authorized_keys
for home in /home/*; do
  user=$(basename "$home")
  if [ -f "$home/.ssh/authorized_keys" ]; then
    echo "=== $user ==="
    cat "$home/.ssh/authorized_keys"
  fi
done
```

**Contain：**

```bash
# 立即移除未知 Key
# 手动编辑 authorized_keys，或使用以下命令清除后重新添加已知 Key
cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.backup.$(date +%Y%m%d)

# 只保留当前会话中已知的 Key（需手动确定哪些是合法的）
# 编辑 ~/.ssh/authorized_keys，只保留您确认的 Key

# 立刻禁止 root SSH 登录、禁用密码登录
sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

**Eradicate：**

```bash
# 确定新增 Key 的来源
# 1. 检查 Key 的注释（comment 字段）
ssh-keygen -lf ~/.ssh/authorized_keys.backup.$(date +%Y%m%d)

# 2. 追踪 Key 是何时、被哪个进程添加的
sudo auditctl -w ~/.ssh/authorized_keys -p wa -k ssh-key-monitor 2>/dev/null
sudo ausearch -k ssh-key-monitor --start today 2>/dev/null | tail -20

# 3. 检查是否有恶意脚本在添加 Key
grep -r 'authorized_keys' ~/ /tmp/ /var/tmp/ /opt/ 2>/dev/null | grep -v '.git/' | grep -v 'backup'
```

**Recover：**

- 重新生成 SSH Key Pair 并更新所有关联服务
- 设置 `authorized_keys` 为只读（`chmod 400` + `chattr +i`）
- 启用 SSH Key 变更告警（auditd watch）
- 审核 SSH 配置：禁用转发、禁用代理

---

## 4. 取证命令速查

### 4.1 journalctl — 系统日志

```bash
# Agent 服务日志（最近）
journalctl -u hermes-agent --since "1 hour ago" --no-pager

# SSH 登录日志
journalctl -u sshd --since "today" --no-pager

# 指定时间范围
journalctl --since "2026-06-17 00:00:00" --until "2026-06-17 23:59:59" --no-pager

# 内核日志（USB 插入、模块加载等）
journalctl -k --since "30 min ago"

# 输出 JSON 格式便于解析
journalctl -u hermes-agent --since "today" -o json-pretty
```

### 4.2 auditd — 审计子系统

```bash
# 检查 auditd 是否运行
sudo systemctl status auditd 2>/dev/null

# 添加文件变更监控
sudo auditctl -w /home/andymao/.ssh/authorized_keys -p wa -k ssh-key-audit
sudo auditctl -w /home/andymao/.hermes -p wa -k hermes-config-audit

# 查询审计日志
sudo ausearch -k ssh-key-audit --start today --format text
sudo ausearch -k hermes-config-audit --start today --format text

# 查看最近 20 条所有审计事件
sudo ausearch --start recent -ts recent | tail -20

# 找出谁在执行命令（如果配置了 execve 审计）
sudo ausearch -sc execve --start today | head -30
```

### 4.3 history — 命令历史

```bash
# 当前用户的历史命令
history | tail -100

# 带时间戳的 history（需启用 HISTTIMEFORMAT）
export HISTTIMEFORMAT='%Y-%m-%d %H:%M:%S | '
history | tail -50

# 从 .bash_history 直接读取
cat ~/.bash_history | tail -50 | nl

# 检查 history 是否被篡改（行数、时间戳连贯性）
wc -l ~/.bash_history
file ~/.bash_history

# 对比多个用户的 history（需 root）
for user in andymao root; do
  home=$(eval echo ~$user)
  if [ -f "$home/.bash_history" ]; then
    echo "=== $user ($(wc -l < $home/.bash_history) 行) ==="
    tail -10 "$home/.bash_history"
  fi
done
```

### 4.4 ls -la 时间线分析

```bash
# 按修改时间排序（最近修改的在最后）
ls -latr ~/.ssh/
ls -latr ~/.hermes/
ls -latr /tmp/

# 按文件状态变更时间排序（ctime — 权限/所有权变更）
ls -latrc ~/.ssh/
ls -latrc ~/.hermes/

# 查找特定时间范围的文件
find ~/.ssh -newer ~/.ssh/authorized_keys.backup -not -name '*.backup*' -ls
find ~/.hermes -newermt "2026-06-16" ! -newermt "2026-06-18" -ls

# stat 查看完整时间线
stat ~/.ssh/authorized_keys
stat ~/.hermes/config.yaml 2>/dev/null

# 分析文件创建/修改模式
for f in ~/.ssh/*; do
  echo "$(stat -c '%Y %y %n' "$f")"
done | sort -n

# 展示每个文件的三个时间戳
echo "文件 | 修改时间(mtime) | 状态变更(ctime) | 访问时间(atime)"
for f in ~/.hermes/*.yaml ~/.hermes/*.json 2>/dev/null; do
  printf "%-40s | %s | %s | %s\n" "$(basename $f)" \
    "$(stat -c '%y' "$f" | cut -d. -f1)" \
    "$(stat -c '%z' "$f" | cut -d. -f1)" \
    "$(stat -c '%x' "$f" | cut -d. -f1)"
done
```

### 4.5 其他取证命令

```bash
# 进程关系树
pstree -ap 2>/dev/null | grep -E '(hermes|agent|ssh|nc|bash)'

# 网络连接全览
ss -tunap 2>/dev/null

# DNS 查询缓存
resolvectl statistics 2>/dev/null || cat /etc/resolv.conf 2>/dev/null

# 最近关机/重启记录
last -x | grep -E '(reboot|shutdown)' | head -10

# 容器 / Podman 状态
podman ps -a --no-trunc 2>/dev/null || docker ps -a --no-trunc 2>/dev/null

# 挂载点检查（可疑 mount）
mount | grep -vE '(proc|sysfs|devtmpfs|devpts|cgroup|tmpfs|overlay)'

# 检测 Rootkit 常见迹象
find /dev -type f -ls 2>/dev/null          # 正常情况下 /dev 下不应有普通文件
lsmod | grep -E '(hide|kit|root)' 2>/dev/null   # 可疑内核模块
cat /proc/1/cmdline | tr '\0' ' '          # init 进程检查
```

---

## 5. 上报与通知模板

### 5.1 即时通知模板（用于 IM / Slack / 飞书）

```
🚨 [Hermes Agent 安全事件] P{级别} - {事件类型}

📋 事件 ID: IR-{YYYYMMDD}-{序号}
🕐 发现时间: {ISO8601}
📊 级别: P{0-3} ({严重/高/中/低})
📌 状态: Active
📝 摘要: {一句话描述}

🔍 初步 Triage 结果:
  - 受影响组件: {列表}
  - 可疑指标 (IOC): {IP / 文件路径 / Key 指纹}
  - 已执行动作: {动作列表}

⏱ 响应时限: {15min / 30min / 4h / 24h}
👤 处理人: @责任人
📎 详情: {链接到复盘文档}
```

### 5.2 邮件通知模板

```
主题: [安全事件] P{级别} | {事件类型} | IR-{YYYYMMDD}-{序号}

正文:

Hermes Agent 安全事件通知

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
事件信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
事件 ID:     IR-{YYYYMMDD}-{序号}
事件类型:    {API Key 泄露 / Cron 异常 / MCP 滥用 / ...}
严重级别:    P{0-3} - {严重/高/中/低}
发现时间:    {ISO8601 时间戳}
检测来源:    {审计告警 / 第三方通报 / 人工发现}
当前状态:    Active / Mitigated / Closed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
事件描述
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{详细描述，包括如何发现、影响范围、已知的损害}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
已执行动作
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. {动作 1} - {时间} - {结果}
2. {动作 2} - {时间} - {结果}
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
后续步骤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. {下一步 1}
2. {下一步 2}
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
处理人:     {姓名}
响应时限:   {截止时间}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.3 外部通报模板（当涉及第三方服务时）

```
To: {第三方安全团队 / 平台安全组}
Subject: Security Incident Notification - {API Key / Token} Compromise - IR-{ID}

We are writing to notify you of a security incident involving our Hermes Agent.
Affected credential: {Key 名称 / ID}
Time of detection: {ISO8601}
Action taken: Key has been revoked and rotated.

We will provide a full incident report within {X} business days.

Regards,
{处理人}
```

---

## 6. 事后复盘（Postmortem）模板

### 元信息

```yaml
Postmortem ID: PM-{YYYYMMDD}-{序号}
事件 ID: IR-{YYYYMMDD}-{序号}
标题: {简明标题}
日期: {YYYY-MM-DD}
作者: {复盘负责人}
参与人: {参与者列表}
状态: Draft / Review / Final
```

### 6.1 时间线

| 时间 (UTC+8) | 事件 |
|-------------|------|
| HH:MM | 事件发生（从日志推断） |
| HH:MM | 首次检测到异常 |
| HH:MM | Triage 完成，定级 P{N} |
| HH:MM | Contain 动作执行 |
| HH:MM | Eradicate 完成 |
| HH:MM | Recover 完成（服务恢复） |
| HH:MM | 复盘会议 |

### 6.2 根本原因分析 (RCA)

**5 Whys 分析：**

1. 为什么事件发生？ → {原因 1}
2. 为什么{原因 1}存在？ → {原因 2}
3. 为什么{原因 2}未被阻止？ → {原因 3}
4. 为什么{原因 3}未被检测到？ → {原因 4}
5. 为什么{原因 4}的系统性缺陷未被修复？ → {根因}

**直接原因：** {一句话}
**根本原因：** {一句话}

### 6.3 影响评估

```yaml
服务中断时长: {X 分钟}
受影响用户数: {X}
数据泄露: {是/否/不确定}
泄露数据类型: {如有}
经济损失估计: {如有}
合规影响: {如有}
```

### 6.4 做得好的

- {做了什么好的决策}
- {哪个控制手段有效}
- {响应速度方面的亮点}

### 6.5 做得不够的

- {检测延迟}
- {Contain 动作不够快}
- {沟通不畅}
- {工具支持不足}

### 6.6 整改措施 (Action Items)

| # | 整改项 | 负责人 | 截止日期 | 状态 |
|---|--------|--------|----------|------|
| 1 | {整改项描述} | @who | YYYY-MM-DD | Open/In Progress/Done |
| 2 | {整改项描述} | @who | YYYY-MM-DD | Open/In Progress/Done |
| 3 | {整改项描述} | @who | YYYY-MM-DD | Open/In Progress/Done |

### 6.7 监控与告警改进

- [ ] 新增检测规则：{规则描述}
- [ ] 缩短告警响应时间：{措施}
- [ ] 增加日志覆盖：{措施}
- [ ] Playbook 更新：{更新内容}

### 6.8 结语

> 本次事件暴露了 {根本问题}。通过 {整改措施}，我们预期将 ... 下次类似事件的 MTTD 降至 {目标}，MTTR 降至 {目标}。

---

## 附录 A: 响应速查卡

### A.1 常用命令速查

```bash
# 一键 Triage 脚本
alias ir-triage='echo "=== 进程 ===" && ps aux | grep -E "(hermes|agent|nc|ncat|socat)" && echo "=== 连接 ===" && ss -tunp 2>/dev/null | grep -v "127.0.0.1" && echo "=== Cron ===" && crontab -l 2>/dev/null && echo "=== SSH Key ===" && cat ~/.ssh/authorized_keys 2>/dev/null | head -5 && echo "=== 最近文件变更 ===" && find ~/.hermes -mmin -30 -type f -ls 2>/dev/null'

# 一键 Contain（停服务+快照）
alias ir-contain='sudo systemctl stop hermes-agent 2>/dev/null; sudo tar czf /tmp/forensics-$(date +%Y%m%d-%H%M%S).tgz ~/.hermes ~/.ssh 2>/dev/null; echo "已执行 Contain"'
```

### A.2 关键文件清单

| 文件/目录 | 作用 | 监控方式 |
|-----------|------|----------|
| ~/.hermes/config.yaml | Agent 主配置 | auditd + git diff |
| ~/.hermes/mcp.json | MCP Server 配置 | auditd |
| ~/.ssh/authorized_keys | SSH 授权 Key | auditd + stat |
| ~/.ssh/config | SSH 客户端配置 | auditd |
| ~/.env | 环境变量/API Key | 文件权限监控 |
| /etc/crontab | 系统 cron | diff 比对 |
| ~/.bash_history | 命令历史 | 完整性校验 |

### A.3 Severity Matrix（严重性矩阵）

```
                    [影响范围]
                   小     中     大
          ┌───────────────────────
    高     │  P2     P1     P0
[危害]  中  │  P2     P2     P1
    低     │  P3     P3     P2
```

---

> 本文档由 agent-security-incident-response Skill 自动管理。
> 最后更新: 2026-06-17
> 维护者: Hermes Agent Security Team

## 参考案例

| 文件 | 说明 |
|------|------|
| `references/case-backup-key-leak.md` | 实战案例：24 个备份文件发现 388 条明文 API Key 的完整处置记录 |
