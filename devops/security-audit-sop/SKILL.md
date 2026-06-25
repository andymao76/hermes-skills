---
name: security-audit-sop
slug: security-audit-sop
version: 1.1.0
category: devops
description: "安全审计标准操作流程（SOP）。涵盖审计触发条件（每日/每周/事件驱动）、完整检查清单（Secret Scanner、权限、Cron、MCP、SSH Key、服务变更）、报告模板、修复跟踪流程及自动化脚本。适用于 Hermes Agent 环境的安全审计与合规保障。"
metadata:
  clawdbot:
    emoji: "🔐"
    requires:
      bins: [git, grep, find, stat]
    os: [linux, darwin]
tags: [security, audit, sop, compliance, devops, 安全审计, 合规]
changelog: "v1.1.0 — 新增飞书推送集成、审计全链路 no-agent cron"
---

# 安全审计标准操作流程 (Security Audit SOP)

> 适用环境：Hermes Agent / Linux / DevOps
> 审计报告目录：`~/knowledge/_system/security_audit/`
> 版本：1.0.0

---

## 目录

1. [审计触发条件](#1-审计触发条件)
2. [审计检查清单](#2-审计检查清单)
3. [审计报告模板](#3-审计报告模板)
4. [修复跟踪流程](#4-修复跟踪流程)
5. [生成命令和脚本](#5-生成命令和脚本)

---

## 1. 审计触发条件

### 1.1 每日审计 (Daily Audit)

| 条件 | 时间 | 执行方式 | 覆盖范围 |
|------|------|----------|----------|
| 定时触发 | 每日 09:00 (UTC+8) | Hermes Cron 调度 | 知识库敏感词扫描、文件权限变更检测 |
| 定时触发 | 每日 22:00 (UTC+8) | Hermes Cron 调度 | 服务变更、SSH Key 完整性检查 |

**每日审计脚本入口：**
```bash
# 手动触发每日审计
bash ~/skills/security-audit-sop/scripts/daily-audit.sh
```

### 1.2 每周审计 (Weekly Audit)

| 条件 | 时间 | 执行方式 | 覆盖范围 |
|------|------|----------|----------|
| 定时触发 | 每周一 08:00 (UTC+8) | Hermes Cron 调度 | 全量检查清单 |
| 定时触发 | 每周五 18:00 (UTC+8) | Hermes Cron 调度 | 修复进度回顾 |

**每周审计脚本入口：**
```bash
# 手动触发每周审计
bash ~/skills/security-audit-sop/scripts/weekly-audit.sh
```

### 1.3 事件驱动审计 (Event-Driven Audit)

| 触发事件 | 响应动作 | 优先级 |
|----------|----------|--------|
| 新用户/服务加入系统 | 权限审计 + SSH Key 审计 | P0 |
| 检测到异常登录行为 | 立即执行完整安全审计 | P0 |
| 服务部署/配置变更 | 服务变更审计 | P1 |
| 安全漏洞公告发布 | 针对性漏洞扫描 | P1 |
| Cron 作业异常 | Cron 审计 | P2 |
| MCP Server 配置变更 | MCP 安全审计 | P1 |

```bash
# 手动触发事件驱动审计
bash ~/skills/security-audit-sop/scripts/event-audit.sh --event "<事件名称>"
```

---

## 2. 审计检查清单

### 2.1 Secret Scanner — 密钥/密码泄露检测

```bash
#!/bin/bash
# audit-secret-scanner.sh — 扫描硬编码密钥和密码

echo "=== Secret Scanner ==="

# AWS Access Key
grep -rn 'AKIA[0-9A-Z]\{16\}' \
  --include='*.{js,ts,py,go,java,rb,env,yml,yaml,json,xml,cfg,conf,ini,toml,sh}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'node_modules\|\.git\|vendor\|__pycache__' \
  && echo "⚠️  发现 AWS Key" || echo "✅ AWS Key 扫描通过"

# 通用 API Key / Token
grep -rn -i 'api[_-]\?key\|api[_-]\?secret\|access[_-]\?token\|auth[_-]\?token\|bearer ' \
  --include='*.{js,ts,py,go,java,rb,env,yml,yaml,json,xml}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'node_modules\|\.git\|example\|test\|mock\|placeholder\|xxxx' \
  && echo "⚠️  发现 API 密钥" || echo "✅ API 密钥扫描通过"

# 私钥文件
find ~/ -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name 'id_rsa' -o -name 'id_ed25519' \
  -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null \
  | while read f; do echo "⚠️  发现私钥文件: $f"; done

# 环境变量中的硬编码密码
grep -rn -i 'password\s*[:=]\s*["'"'"'][^"'"'"']*["'"'"']' \
  --include='*.{env,yml,yaml,json,xml,cfg,conf,ini,toml}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'example\|test\|mock\|placeholder\|changeme\|xxxx' \
  && echo "⚠️  发现硬编码密码" || echo "✅ 密码扫描通过"

# OpenAI / Anthropic API Key 格式
grep -rn 'sk-[A-Za-z0-9]\{20,\}' \
  --include='*.{js,ts,py,go,java,rb,env,yml,yaml,json,xml,cfg,conf,ini,toml,sh}' \
  ~/knowledge/ ~/skills/ 2>/dev/null | grep -v 'node_modules\|\.git\|vendor' \
  && echo "⚠️  发现 LLM API Key" || echo "✅ LLM API Key 扫描通过"
```

### 2.2 权限审计 — 文件/目录权限检测

```bash
#!/bin/bash
# audit-permissions.sh — 审计关键文件权限

echo "=== 权限审计 ==="

# ~/.ssh 目录权限
SSH_DIR=~/.ssh
if [ -d "$SSH_DIR" ]; then
  SSH_PERM=$(stat -c "%a" "$SSH_DIR" 2>/dev/null || stat -f "%Lp" "$SSH_DIR" 2>/dev/null)
  [ "$SSH_PERM" = "700" ] && echo "✅ ~/.ssh 权限正确 (700)" \
    || echo "⚠️  ~/.ssh 权限异常: $SSH_PERM (应为 700)"
  
  for key in "$SSH_DIR"/id_*; do
    [ -f "$key" ] || continue
    KEY_PERM=$(stat -c "%a" "$key" 2>/dev/null || stat -f "%Lp" "$key" 2>/dev/null)
    case "$key" in
      *.pub) [ "$KEY_PERM" = "644" ] && echo "✅ $(basename $key) 权限正确 (644)" \
               || echo "⚠️  $(basename $key) 权限异常: $KEY_PERM (应为 644)" ;;
      *)     [ "$KEY_PERM" = "600" ] && echo "✅ $(basename $key) 权限正确 (600)" \
               || echo "⚠️  $(basename $key) 权限异常: $KEY_PERM (应为 600)" ;;
    esac
  done
fi

# 审计报告目录权限
AUDIT_DIR=~/knowledge/_system/security_audit
if [ -d "$AUDIT_DIR" ]; then
  AUDIT_PERM=$(stat -c "%a" "$AUDIT_DIR" 2>/dev/null || stat -f "%Lp" "$AUDIT_DIR" 2>/dev/null)
  echo "ℹ️  审计报告目录权限: $AUDIT_PERM (建议 700)"
fi

# 全局可写文件检测
echo "--- 全局可写文件检测 ---"
find ~ -type f -perm -o=w -not -path '*/.git/*' -not -path '*/node_modules/*' 2>/dev/null | head -20
```

### 2.3 Cron 审计 — 定时任务检查

```bash
#!/bin/bash
# audit-cron.sh — 审计 Hermes Cron 任务

echo "=== Cron 审计 ==="

# 列出所有活跃 Cron 任务
hermes cron list 2>/dev/null || echo "⚠️  hermes cron list 不可用，尝试查看 cron 文件"

# 系统 crontab
echo "--- 系统 crontab ---"
crontab -l 2>/dev/null && echo "✅ 系统 crontab 已配置" || echo "ℹ️  无用户 crontab"

# 检查可疑 Cron 作业
echo "--- 可疑 Cron 检查 ---"
crontab -l 2>/dev/null | grep -i 'curl\|wget\|nc\|ncat\|bash -c\|eval\|/dev/tcp' \
  && echo "⚠️  发现可疑网络请求的 Cron 作业" || echo "✅ 无可疑 Cron 作业"

# Cron 作业健康检查
echo "--- Cron 执行历史 ---"
hermes cron history 2>/dev/null | tail -10 || echo "ℹ️  历史记录不可用"
```

### 2.4 MCP 审计 — MCP Server 安全配置检查

```bash
#!/bin/bash
# audit-mcp.sh — 审计 MCP Server 配置

echo "=== MCP Server 审计 ==="

# 检查 MCP 配置文件
MCP_CONFIG=~/.hermes/mcp.json
if [ -f "$MCP_CONFIG" ]; then
  echo "✅ MCP 配置文件存在: $MCP_CONFIG"
  
  # 检查 MCP 配置中的网络端点
  grep -o '"url"[[:space:]]*:[[:space:]]*"[^"]*"' "$MCP_CONFIG" 2>/dev/null | while read url; do
    echo "ℹ️  MCP 端点: $url"
  done
  
  # 检查是否有 localhost 绑定
  grep -o '"127\.0\.0\.1\|"localhost' "$MCP_CONFIG" 2>/dev/null && echo "✅ MCP 绑定本地地址" \
    || echo "⚠️  检查 MCP 是否有外部地址绑定"
  
  # 检查认证配置
  grep -qi '"apiKey\|"token\|"auth' "$MCP_CONFIG" 2>/dev/null && echo "✅ MCP 配置含认证信息" \
    || echo "⚠️  MCP 配置未检测到显式认证"
else
  echo "ℹ️  MCP 配置文件不存在"
fi

# MCP 进程检查
echo "--- MCP 进程检查 ---"
ps aux | grep -i '[m]cp' && echo "ℹ️  MCP 相关进程运行中" || echo "ℹ️  无 MCP 进程运行"
```

### 2.5 SSH Key 审计 — SSH 密钥完整性检查

```bash
#!/bin/bash
# audit-ssh-keys.sh — 审计 SSH 密钥

echo "=== SSH Key 审计 ==="

SSH_DIR=~/.ssh

# authorized_keys 检查
if [ -f "$SSH_DIR/authorized_keys" ]; then
  KEY_COUNT=$(grep -c 'ssh-' "$SSH_DIR/authorized_keys" 2>/dev/null)
  echo "ℹ️  authorized_keys 中有 $KEY_COUNT 个公钥"
  
  # 检查 authorized_keys 权限
  AUTH_PERM=$(stat -c "%a" "$SSH_DIR/authorized_keys" 2>/dev/null || stat -f "%Lp" "$SSH_DIR/authorized_keys" 2>/dev/null)
  [ "$AUTH_PERM" = "600" ] && echo "✅ authorized_keys 权限正确 (600)" \
    || echo "⚠️  authorized_keys 权限异常: $AUTH_PERM (应为 600)"
fi

# known_hosts 检查
if [ -f "$SSH_DIR/known_hosts" ]; then
  HOST_COUNT=$(wc -l < "$SSH_DIR/known_hosts" 2>/dev/null)
  echo "ℹ️  known_hosts 中有 $HOST_COUNT 个主机记录"
fi

# SSH config 检查
if [ -f "$SSH_DIR/config" ]; then
  echo "✅ SSH config 存在"
  # 检查密钥路径引用
  grep -i 'IdentityFile' "$SSH_DIR/config" 2>/dev/null | head -5
fi

# 密钥指纹汇总
echo "--- 本地密钥指纹 ---"
for key in "$SSH_DIR"/id_*.pub; do
  [ -f "$key" ] || continue
  echo "  $(ssh-keygen -lf "$key" 2>/dev/null)"
done
```

### 2.6 服务变更审计 — 检测环境变化

```bash
#!/bin/bash
# audit-service-changes.sh — 检测服务与配置变更

echo "=== 服务变更审计 ==="

SNAPSHOT_DIR=~/knowledge/_system/security_audit/snapshots
mkdir -p "$SNAPSHOT_DIR"

# 基线快照文件名
BASELINE="$SNAPSHOT_DIR/baseline.txt"
CURRENT="$SNAPSHOT_DIR/current-$(date +%Y%m%d).txt"

# 生成当前快照
{
  echo "# 系统快照 $(date)"
  echo "--- Installed Packages (关键) ---"
  which dpkg 2>/dev/null && dpkg -l 2>/dev/null | grep -E '^(ii|hi)' | awk '{print $2, $3}' | head -50
  which rpm 2>/dev/null && rpm -qa 2>/dev/null | head -50
  
  echo "--- Listening Ports ---"
  ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null
  
  echo "--- Systemd Services ---"
  systemctl list-units --type=service --state=running 2>/dev/null || echo "N/A"
  
  echo "--- Docker Containers ---"
  docker ps 2>/dev/null || echo "N/A"
  
  echo "--- Hermes Process ---"
  ps aux | grep '[h]ermes' 2>/dev/null || echo "N/A"
} > "$CURRENT"

# 与基线比较
if [ -f "$BASELINE" ]; then
  echo "--- 与基线对比变更 ---"
  diff "$BASELINE" "$CURRENT" 2>/dev/null | head -50 \
    && echo "✅ 无变更" || echo "⚠️  检测到变更"
else
  echo "ℹ️  首次运行，创建基线快照"
  cp "$CURRENT" "$BASELINE"
fi
```

### 审计检查清单汇总表

| 检查项 | 每日 | 每周 | 事件驱动 | 检测方法 |
|--------|------|------|----------|----------|
| 🔑 Secret Scanner | ✅ | ✅ | ✅ | grep 正则匹配 / Gitleaks / TruffleHog |
| 🔒 权限审计 | — | ✅ | ✅ | stat / find 权限检测 |
| ⏰ Cron 审计 | ✅ | ✅ | ✅ | hermes cron list / crontab |
| 🌐 MCP 审计 | — | ✅ | ✅ | 配置解析 + 进程检查 |
| 🗝️ SSH Key 审计 | — | ✅ | ✅ | 权限 / 指纹 / authorized_keys |
| 🔄 服务变更 | ✅ | ✅ | ✅ | 基线快照 diff |
| 📂 知识库敏感词 | ✅ | ✅ | ✅ | regex 扫描 + 分类隔离 |
| 📊 磁盘/资源 | ✅ | — | — | df / free / uptime |

---

## 3. 审计报告模板

### 3.1 每日审计报告模板

```markdown
# 每日安全审计报告 — {{DATE}}

| 属性 | 值 |
|------|-----|
| 生成时间 | {{TIMESTAMP}} |
| 审计类型 | 每日例行 |
| 触发方式 | {{TRIGGER: cron / manual}} |

---

## 1. Secret Scanner 结果

| 扫描项 | 状态 | 发现数 |
|--------|------|--------|
| AWS Key | {{PASS/FAIL}} | {{COUNT}} |
| API Token | {{PASS/FAIL}} | {{COUNT}} |
| 私钥文件 | {{PASS/FAIL}} | {{COUNT}} |
| 硬编码密码 | {{PASS/FAIL}} | {{COUNT}} |
| LLM API Key | {{PASS/FAIL}} | {{COUNT}} |

## 2. Cron 作业状态

| 作业名称 | 状态 | 最后执行 | 备注 |
|----------|------|----------|------|
| {{NAME}} | {{active/failed}} | {{TIME}} | {{NOTE}} |

## 3. 服务变更检测

- 基线对比: {{无变更/检测到 N 项变更}}
- {{变更明细}}

## 4. 知识库敏感词扫描

| 敏感词类型 | 命中次数 | 风险等级 |
|-----------|---------|----------|
| {{TYPE}} | {{COUNT}} | 🔴/🟡/🟢 |

## 5. 总结

- ✅ 通过: {{PASS_COUNT}}
- ⚠️ 警告: {{WARN_COUNT}}
- 🚫 失败: {{FAIL_COUNT}}

**总体评级:** {{PASS / MINOR / CRITICAL}}

---

*报告由 Hermes Agent 自动生成*
```

### 3.2 每周完整审计报告模板

```markdown
# 每周安全审计报告 — {{WEEK}} ({{DATE_RANGE}})

| 属性 | 值 |
|------|-----|
| 生成时间 | {{TIMESTAMP}} |
| 审计类型 | 每周完整审计 |
| 审计范围 | 全量检查清单 |

---

## 1. 审计概要

| 检查项 | 状态 | 发现数 | 严重程度 |
|--------|------|--------|----------|
| 🔑 Secret Scanner | {{PASS/FAIL}} | {{N}} | 🔴/🟡/🟢 |
| 🔒 权限审计 | {{PASS/FAIL}} | {{N}} | 🔴/🟡/🟢 |
| ⏰ Cron 审计 | {{PASS/FAIL}} | {{N}} | 🔴/🟡/🟢 |
| 🌐 MCP 审计 | {{PASS/FAIL}} | {{N}} | 🔴/🟡/🟢 |
| 🗝️ SSH Key 审计 | {{PASS/FAIL}} | {{N}} | 🔴/🟡/🟢 |
| 🔄 服务变更 | {{PASS/FAIL}} | {{N}} | 🔴/🟡/🟢 |
| 📂 知识库敏感词 | {{PASS/FAIL}} | {{N}} | 🔴/🟡/🟢 |

## 2. 各检查项详情

### 2.1 Secret Scanner 详情
```
{{DETAILED_OUTPUT}}
```

### 2.2 权限审计详情
```
{{DETAILED_OUTPUT}}
```

### 2.3 Cron 审计详情
```
{{DETAILED_OUTPUT}}
```

### 2.4 MCP 审计详情
```
{{DETAILED_OUTPUT}}
```

### 2.5 SSH Key 审计详情
```
{{DETAILED_OUTPUT}}
```

### 2.6 服务变更详情
```
{{DETAILED_OUTPUT}}
```

## 3. 待修复项统计

| 优先级 | 未修复 | 修复中 | 已修复 | 总计 |
|--------|--------|--------|--------|------|
| P0 (紧急) | {{N}} | {{N}} | {{N}} | {{N}} |
| P1 (高) | {{N}} | {{N}} | {{N}} | {{N}} |
| P2 (中) | {{N}} | {{N}} | {{N}} | {{N}} |
| P3 (低) | {{N}} | {{N}} | {{N}} | {{N}} |

## 4. 修复跟踪

| 编号 | 发现日期 | 检查项 | 问题描述 | 优先级 | 状态 | 负责人 | 计划修复日 |
|------|----------|--------|----------|--------|------|--------|-----------|
| SEC-{{N}} | {{DATE}} | {{ITEM}} | {{DESC}} | {{P0-P3}} | {{open/in_progress/resolved}} | {{OWNER}} | {{DATE}} |

## 5. 趋势分析

- 本周问题总数: {{N}} ({{↑/↓}} 对比上周 {{N}})
- 新增问题: {{N}}
- 已解决: {{N}}

## 6. 总结与建议

{{RECOMMENDATIONS}}

---

*报告由 Hermes Agent 自动生成于 {{TIMESTAMP}}*
```

### 3.3 事件驱动审计报告模板

```markdown
# 事件驱动安全审计报告 — {{EVENT_NAME}}

| 属性 | 值 |
|------|-----|
| 触发事件 | {{EVENT_NAME}} |
| 触发时间 | {{TIMESTAMP}} |
| 审计范围 | {{SCOPE}} |
| 优先级 | {{P0/P1/P2}} |

---

## 事件描述

{{EVENT_DESCRIPTION}}

## 即时发现

{{FINDINGS}}

## 建议措施

{{ACTIONS}}

---

*事件响应报告 — 由 Hermes Agent 自动生成*
```

---

## 4. 修复跟踪流程

### 4.1 问题登记

发现安全问题后，在审计报告目录中创建修复跟踪记录：

```bash
# 创建修复跟踪记录
cat >> ~/knowledge/_system/security_audit/fix-tracker.md << 'EOF'
## SEC-{{NEXT_ID}}

| 字段 | 值 |
|------|-----|
| **发现日期** | {{DATE}} |
| **检查项** | {{ITEM}} |
| **问题描述** | {{DESC}} |
| **影响范围** | {{SCOPE}} |
| **严重级别** | {{P0/P1/P2/P3}} |
| **状态** | 🔴 待修复 |
| **发现人** | Hermes Agent |
| **修复人** | |
| **修复方案** | |
| **计划修复日** | |
| **实际修复日** | |
| **验证结果** | |
EOF
```

### 4.2 严重级别定义

| 级别 | 标签 | 描述 | 响应时限 |
|------|------|------|----------|
| P0 | 🔴 紧急 | 直接安全风险（密钥泄露、未授权访问） | 4 小时内 |
| P1 | 🟠 高 | 潜在安全风险（权限配置不当、服务异常） | 24 小时内 |
| P2 | 🟡 中 | 合规偏差（权限不规范、文档不完整） | 72 小时内 |
| P3 | 🟢 低 | 建议改进（优化建议、冗余清理） | 下周审计前 |

### 4.3 修复流程

```
发现问题 → 登记问题 → 分配修复人 → 实施修复 → 验证修复 → 更新状态 → 关闭
   🔴        🔴          🟡           🟡          🟢          🟢          ✅
```

**状态流转规则：**
- `🔴 待修复` — 问题已登记，待处理
- `🟡 修复中` — 已分配修复人，正在修复
- `🟢 已修复` — 修复完成，待下次审计验证
- `✅ 已验证` — 下次审计通过验证，问题关闭
- `⏸️ 暂缓` — 经评估后决定暂缓处理，需注明原因

### 4.4 定期回顾

```bash
# 每周回顾时，统计修复进度
echo "=== 修复进度回顾 ==="
grep -c '🔴' ~/knowledge/_system/security_audit/fix-tracker.md 2>/dev/null && echo "待修复: $(grep -c '🔴' ~/knowledge/_system/security_audit/fix-tracker.md)"
grep -c '🟡' ~/knowledge/_system/security_audit/fix-tracker.md 2>/dev/null && echo "修复中: $(grep -c '🟡' ~/knowledge/_system/security_audit/fix-tracker.md)"
grep -c '🟢' ~/knowledge/_system/security_audit/fix-tracker.md 2>/dev/null && echo "已修复(待验证): $(grep -c '🟢' ~/knowledge/_system/security_audit/fix-tracker.md)"
```

---

## 5. 生成命令和脚本

### 5.1 一键执行所有审计

```bash
#!/bin/bash
# run-full-audit.sh — 执行完整安全审计并生成报告
set -euo pipefail

AUDIT_DIR=~/knowledge/_system/security_audit
REPORT_DIR="$AUDIT_DIR/reports"
SNAPSHOT_DIR="$AUDIT_DIR/snapshots"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="$REPORT_DIR/security-audit-$TIMESTAMP.md"

mkdir -p "$REPORT_DIR" "$SNAPSHOT_DIR"

echo "========================================"
echo "  安全审计开始 — $(date)"
echo "========================================"

# 收集所有审计结果
SECRET_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-secret-scanner.sh 2>&1 || true)
PERM_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-permissions.sh 2>&1 || true)
CRON_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-cron.sh 2>&1 || true)
MCP_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-mcp.sh 2>&1 || true)
SSH_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-ssh-keys.sh 2>&1 || true)
SVC_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-service-changes.sh 2>&1 || true)

# 生成报告（使用模板）
cat > "$REPORT_FILE" << REPORTEOF
# 安全审计报告 — $(date +%Y-%m-%d)

| 属性 | 值 |
|------|-----|
| 生成时间 | $(date '+%Y-%m-%d %H:%M:%S') |
| 报告路径 | $REPORT_FILE |
| 审计类型 | 完整审计 |

---

## 1. Secret Scanner

\`\`\`
$SECRET_RESULT
\`\`\`

## 2. 权限审计

\`\`\`
$PERM_RESULT
\`\`\`

## 3. Cron 审计

\`\`\`
$CRON_RESULT
\`\`\`

## 4. MCP 审计

\`\`\`
$MCP_RESULT
\`\`\`

## 5. SSH Key 审计

\`\`\`
$SSH_RESULT
\`\`\`

## 6. 服务变更

\`\`\`
$SVC_RESULT
\`\`\`

---

*报告由 Hermes Agent 安全审计 SOP 自动生成于 $(date '+%Y-%m-%d %H:%M:%S')*
REPORTEOF

echo "========================================"
echo "  审计完成"
echo "  报告: $REPORT_FILE"
echo "========================================"
```

### 5.2 快速审计别名

将以下内容添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
# 安全审计快捷命令
alias audit-secret='bash ~/skills/security-audit-sop/scripts/audit-secret-scanner.sh'
alias audit-perm='bash ~/skills/security-audit-sop/scripts/audit-permissions.sh'
alias audit-cron='bash ~/skills/security-audit-sop/scripts/audit-cron.sh'
alias audit-mcp='bash ~/skills/security-audit-sop/scripts/audit-mcp.sh'
alias audit-ssh='bash ~/skills/security-audit-sop/scripts/audit-ssh-keys.sh'
alias audit-svc='bash ~/skills/security-audit-sop/scripts/audit-service-changes.sh'
alias audit-all='bash ~/skills/security-audit-sop/scripts/run-full-audit.sh'
```

### 5.3 Hermes Cron 注册（每日、每周审计）

```bash
# 每日审计 — 09:00
hermes cron add \
  --name "每日安全审计" \
  --schedule "0 9 * * *" \
  --script "bash ~/skills/security-audit-sop/scripts/run-full-audit.sh" \
  --mode "no-agent"

# 每周完整审计 — 周一 08:00
hermes cron add \
  --name "每周安全审计" \
  --schedule "0 8 * * 1" \
  --script "bash ~/skills/security-audit-sop/scripts/run-full-audit.sh" \
  --mode "no-agent"

# 服务变更监控 — 每 6 小时
hermes cron add \
  --name "服务变更检测" \
  --schedule "0 */6 * * *" \
  --script "bash ~/skills/security-audit-sop/scripts/audit-service-changes.sh" \
  --mode "no-agent"
```

### 5.4 审计报告目录结构

```
~/knowledge/_system/security_audit/
├── reports/                    # 审计报告
│   ├── security-audit-2026-06-17.md
│   └── ...
├── snapshots/                  # 系统快照
│   ├── baseline.txt
│   └── current-YYYYmmdd.txt
├── fix-tracker.md              # 修复跟踪
└── templates/                  # 报告模板
    ├── daily-template.md
    ├── weekly-template.md
    └── event-template.md
```

### 5.5 审计工具安装指南

```bash
# 可选增强工具（非必须，grep/find 已满足基础审计需求）

# Gitleaks — Git 仓库密钥扫描
# brew install gitleaks
# go install github.com/gitleaks/gitleaks/v8@latest

# TruffleHog — 深度密钥扫描
# pip install truffleHog

# Lynis — 系统安全审计
# apt install lynis
# lynis audit system

# ClamAV — 恶意软件扫描
# apt install clamav
# clamscan -r ~/knowledge/
```

---

## 6. 飞书通知与全链路自动化

### 6.1 架构

审计完成后自动推送到飞书，全链路使用 no-agent cron（不消耗 LLM token）：

```
Cron (每天08:30, no-agent)
  → ~/.hermes/scripts/audit-full-chain.sh
      ├── [1] python3 security-audit.py → 审计报告
      └── [2] bash audit-push-feishu.sh → 飞书推送摘要
```

### 6.2 脚本说明

| 脚本 | 位置 | 作用 |
|------|------|------|
| `audit-push-feishu.sh` | `~/.hermes/scripts/` | 读取最新审计报告，提取关键指标（隔离违规数、敏感词命中数、摘要行），发送飞书消息 |
| `audit-full-chain.sh` | `~/.hermes/scripts/` | 依次运行审计脚本 + 推送脚本，全链路封装 |

### 6.3 关键实现细节

**从 .env 读取飞书配置（避免 source 整份文件导致的特殊字符崩溃）：**
```bash
FEISHU_APP_ID=$(grep "^FEISHU_APP_ID=" ~/.hermes/.env | head -1 | cut -d= -f2-)
FEISHU_APP_SECRET=$(grep "^FEISHU_APP_SECRET=" ~/.hermes/.env | head -1 | cut -d= -f2-)
```

**审计报告摘要提取：**
```bash
ISO_VIOLATIONS=$(grep -c "隔离违规" "$LATEST" || echo "0")
SENSITIVE_HITS=$(grep -c "敏感词" "$LATEST" || echo "0")
SUMMARY_LINE=$(grep -A2 "^## 总结" "$LATEST" | tail -1 || echo "无摘要")
```

### 6.4 Cron 注册命令

```bash
# 创建全链路 cron（no-agent 模式，每日 08:30）
hermes cron add \
  --name "安全审计全链路—飞书推送" \
  --schedule "30 8 * * *" \
  --script "audit-full-chain.sh" \
  --mode "no-agent"
```

### 6.5 推送消息格式

```
【每日安全审计报告】2026-06-23
──────────────────
状态: ⚠️ 发现异常
隔离违规: 2 处
敏感词命中: 5 处
──────────────────
⚠️ **发现 1 个隔离问题 + 5 类敏感词命中**
──────────────────
⏰ 10:46:27 | Hermes Security
```

### 6.6 Script Locations

The Feishu integration scripts are registered as skill support files (visible via `skill_view`) AND symlinked/copied to `~/.hermes/scripts/` for cron resolution:

| Script | Skill path | Cron path |
|--------|-----------|-----------|
| `audit-push-feishu.sh` | `scripts/audit-push-feishu.sh` | `~/.hermes/scripts/audit-push-feishu.sh` |
| `audit-full-chain.sh` | `scripts/audit-full-chain.sh` | `~/.hermes/scripts/audit-full-chain.sh` |

### 6.7 Pitfalls

- ⚠️ 安全审计脚本发现异常时返回 exit 1（正常行为），全链路脚本需用 `set -uo pipefail` 而非 `set -euo pipefail` 避免中断
- ⚠️ `.env` 文件含特殊字符（如 WhatsApp token 的 `~`），不要 `source` 整份文件，改用逐行 `grep` 提取
- ⚠️ 审计报告 `## 总结` 和摘要行之间有一个空行，`grep -A1` 只能拿到空行，需用 `-A2` 再 `tail -1`

---

## 参考链接

- [Hermes Agent 安全审计](/knowledge/_system/security/安全审计报告.md)
- [LLM 数据治理技能](/knowledge/_system/security/llm_data_governance.skill.md)
- [现有安全审计报告](/knowledge/_system/security/audit-reports/)
- [Hermes Cron 调度系统](https://hermes-agent.nousresearch.com/docs/cron)
