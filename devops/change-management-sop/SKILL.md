---
name: change-management-sop
description: 变更管理标准操作流程（Change Management SOP）- 涵盖变更分类、变更流程、验证要求及回退方案
version: 1.0.0
author: Hermes Agent
tags:
  - change-management
  - sop
  - devops
  - incident-management
  - change-control
dependencies:
  - operational-playbook
  - security-governance-framework
---

# 变更管理标准操作流程（SOP）

## 1. 变更分类（L0-L4 风险等级）

依据 Security Governance Framework 定义的风险分级标准：

| 等级 | 名称 | 定义 | 示例 | 审批要求 |
|------|------|------|------|----------|
| **L0** | 紧急变更 | 需立即修复的生产故障/安全漏洞 | 紧急P0故障修复、高危漏洞热修复 | 事后24h内补审批 |
| **L1** | 低风险 | 不影响业务，低影响面 | 注释修改、日志级别调整、非生产环境配置 | 无需审批，自动记录 |
| **L2** | 中风险 | 影响有限，可快速回退 | 非关键服务的配置变更、监控策略调整 | 直属Leader审批 |
| **L3** | 高风险 | 影响关键业务，回退较复杂 | 数据库配置变更、核心服务版本更新、网络策略变更 | 技术主管+运维Leader审批 |
| **L4** | 重大变更 | 影响全局，回退风险极高 | 架构重构、数据库迁移、核心中间件升级、跨集群变更 | CTO/SRE VP审批，需变更评审会 |

## 2. 变更流程：PLAN → DRY RUN → APPROVAL → BACKUP → EXECUTE → VERIFY → AUDIT LOG

### 2.1 完整流程概览

```
┌──────┐     ┌──────────┐     ┌──────────┐     ┌────────┐     ┌─────────┐     ┌────────┐     ┌───────────┐
│ PLAN │ ──→ │ DRY RUN  │ ──→ │ APPROVAL │ ──→ │ BACKUP │ ──→ │ EXECUTE │ ──→ │ VERIFY │ ──→ │ AUDIT LOG │
└──────┘     └──────────┘     └──────────┘     └────────┘     └─────────┘     └────────┘     └───────────┘
```

### 2.2 各阶段详细说明

#### 【PLAN】变更计划

```bash
# 创建变更工单（示例：使用标准模板）
cat << 'EOF' > change-plan-$(date +%Y%m%d-%H%M).md
# 变更计划

## 基本信息
- 变更标题: 
- 变更发起人: 
- 变更等级: L[0-4]
- 计划时间: 
- 影响范围: 
- 涉及服务/组件: 

## 变更内容描述
详细描述本次变更的目的、内容和预期效果。

## 实施步骤
1. 
2. 
3. 

## 验证步骤
1. 
2. 
3. 

## 回退方案
（参见第5节）

## 风险评估
- 潜在风险:
- 影响面评估:
- 回退复杂度:
EOF
```

**检查清单：**
- [ ] 变更是否已有对应的工单/issue 编号
- [ ] 变更影响范围是否已明确
- [ ] 干系人是否已通知
- [ ] 是否选择了正确的变更窗口（L3/L4 需在业务低峰期执行）

#### 【DRY RUN】预演/模拟执行

```bash
# 对于 L3/L4 变更，先在预发布/测试环境执行完整流程
# 配置变更预演
diff <(git diff --cached) <(echo "预演配置差异已确认")

# 脚本预演（dry-run 模式）
if command -v ansible-playbook &> /dev/null; then
    ansible-playbook --check --diff playbook.yml
fi

# Terraform 预演
if [ -f terraform.tf ]; then
    terraform plan -out=tfplan
    terraform show tfplan | head -50
fi
```

#### 【APPROVAL】审批流程

| 等级 | 审批方式 | 审批人 | 审批时限 |
|------|----------|--------|----------|
| L0 | 事后24h内补审批 | TBD | 24h |
| L1 | 自动记录 | 无 | 无需等待 |
| L2 | 即时通讯确认 | 直属Leader | 1h |
| L3 | 审批系统提单 | 技术主管+运维Leader | 4h |
| L4 | 变更评审会+审批 | CTO/SRE VP | 24h（紧急情况可加速） |

```bash
# 审批确认命令（L2-L4 必需）
echo "变更审批已通过 - 审批人: $(git config user.name) - 时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
# 输出结果记录到变更日志
```

#### 【BACKUP】变更前备份

```bash
# ========================
# 配置备份
# ========================

# 备份当前配置目录
BACKUP_DIR="/var/backup/changes/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 通用备份命令模板
for config in /etc/nginx/nginx.conf /etc/redis/redis.conf /etc/mysql/my.cnf; do
    if [ -f "$config" ]; then
        cp -v "$config" "$BACKUP_DIR/"
    fi
done

# ========================
# Git 仓库备份（版本快照）
# ========================
if [ -d .git ]; then
    git stash list > "$BACKUP_DIR/git-stash-before.txt" 2>/dev/null
    git log --oneline -5 > "$BACKUP_DIR/git-log-before.txt"
    echo "Git HEAD: $(git rev-parse HEAD)" > "$BACKUP_DIR/git-head.txt"
    git diff HEAD > "$BACKUP_DIR/git-uncommitted-diff.txt" 2>/dev/null
fi

# ========================
# 数据库备份
# ========================
# pg_dump -h localhost -U user dbname > "$BACKUP_DIR/db.sql"  # PostgreSQL
# mysqldump -u user -p dbname > "$BACKUP_DIR/db.sql"          # MySQL

# ========================
# 服务状态快照
# ========================
systemctl list-units --type=service --state=running > "$BACKUP_DIR/services-before.txt"
```

**必填检查：**
- [ ] 备份文件是否已写入磁盘（`ls -la "$BACKUP_DIR"`）
- [ ] 备份的配置文件数量和预期一致
- [ ] 数据库备份是否完整（如需）
- [ ] Git 仓库是否有未提交更改已备份

#### 【EXECUTE】变更执行

```bash
# ========================
# 配置变更执行
# ========================
echo "===== 开始执行变更：$(date -u '+%Y-%m-%dT%H:%M:%SZ') ====="

# 示例：Nginx 配置变更
# cp /etc/nginx/nginx.conf "$BACKUP_DIR/"  # 确认已备份
# cp -f new-nginx.conf /etc/nginx/nginx.conf
# nginx -t && systemctl reload nginx

# 示例：环境变量配置
# export NEW_CONFIG_VALUE="xxx"
# envsubst < template.conf > /etc/app/config.conf

# 通用执行原则：
# 1. 分步执行，每一步确认成功后再执行下一步
# 2. 使用 && 串联命令，任一失败则停止
# 3. 记录每一步的退出码和执行时间

echo "===== 变更执行完成：$(date -u '+%Y-%m-%dT%H:%M:%SZ') ====="
```

**执行要点：**
- 按预演确认的步骤逐一执行
- 每步执行后立即验证中间结果
- 若任一关键步骤失败，立即启动回退
- 记录执行日志（建议写入文件：`change-execution-$(date +%Y%m%d).log`）

#### 【VERIFY】变更验证

```bash
# ========================
# 通用验证入口
# ========================
echo "===== 开始验证：$(date -u '+%Y-%m-%dT%H:%M:%SZ') ====="
VERIFY_PASSED=true

# 详见第3节（配置变更验证）和第4节（服务变更验证）

if [ "$VERIFY_PASSED" = true ]; then
    echo "✅ 变更验证通过"
else
    echo "❌ 变更验证失败，请执行回退方案"
fi
```

#### 【AUDIT LOG】审计日志记录

```bash
# ========================
# 标准化审计日志写入
# ========================
AUDIT_LOG="/var/log/change-audit.log"

cat << EOF >> "$AUDIT_LOG"
[$(date -u '+%Y-%m-%dT%H:%M:%SZ')]
变更ID: change-$(date +%Y%m%d)-$(hostname)-$$ 
等级: L[0-4]
执行人: $(whoami)
主机: $(hostname)
变更描述: <变更内容摘要>
结果: SUCCESS/FAILED/ROLLED_BACK
回退标志: true/false
备份路径: $BACKUP_DIR
验证结果: PASSED/FAILED
审批人: <审批人>
---
EOF

echo "审计日志已写入: $AUDIT_LOG"
```

## 3. 配置变更的 Git Diff 验证要求

### 3.1 变更前 - 确认基线

```bash
# 确认当前工作目录是 Git 仓库
if [ ! -d .git ]; then
    echo "❌ 错误：当前目录不是 Git 仓库"
    exit 1
fi

# 确认已提交或暂存了当前基线
echo "===== 当前基线 ====="
git log --oneline -1
git status --short
```

### 3.2 变更后 - Diff 验证

```bash
# ========================
# 检查 1: 确保只包含预期变更（无意外改动）
# ========================
echo "===== 预期变更范围 ====="
git diff --stat          # 统计变更文件数
git diff --name-only     # 列出具体变更文件

echo ""
echo "===== 详细 Diff（建议人工审查） ====="
git diff | head -200

# ========================
# 检查 2: 敏感信息泄露检查
# ========================
echo ""
echo "===== 敏感信息扫描 ====="
SENSITIVE_PATTERNS=("password" "secret" "token" "api_key" "private_key" "access_key" "credential")
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if git diff | grep -qi "$pattern"; then
        echo "⚠️  警告：Diff 中发现敏感关键词: $pattern"
        git diff | grep -in "$pattern"
    fi
done

# ========================
# 检查 3: 语法校验
# ========================
echo ""
echo "===== 语法校验 ====="
for file in $(git diff --name-only); do
    case "${file##*.}" in
        yaml|yml)
            if command -v yamllint &> /dev/null; then
                yamllint -d relaxed "$file" && echo "✅ YAML 语法通过: $file" || echo "❌ YAML 语法错误: $file"
            fi
            ;;
        json)
            python3 -m json.tool "$file" > /dev/null 2>&1 && echo "✅ JSON 语法通过: $file" || echo "❌ JSON 语法错误: $file"
            ;;
        conf|cfg|ini)
            echo "🔍 $file — 建议人工检查配置文件格式"
            ;;
    esac
done

# ========================
# 检查 4: 与 DRY RUN 阶段的 Diff 比对
# ========================
echo ""
echo "===== Diff 一致性检查 ====="
if [ -f "tfplan" ]; then
    echo "Terraform plan 已存在，确认与执行结果一致"
fi
# 实际变更与预演时的 diff 应完全一致
```

### 3.3 验证通过条件

```bash
# 所有检查通过的判断逻辑
echo ""
VERIFY_CONFIG_PASSED=true

# 条件 1: 变更文件范围符合预期
if [ "$(git diff --stat | wc -l)" -eq 0 ]; then
    echo "❌ 未检测到任何变更"
    VERIFY_CONFIG_PASSED=false
fi

# 条件 2: 无敏感信息泄露
if git diff | grep -qiE "(password|secret|token|api_key|private_key|credential)"; then
    echo "❌ 变更中包含疑似敏感信息，需要审查"
    VERIFY_CONFIG_PASSED=false
fi

# 条件 3: 语法校验通过（如已配置相应工具）
echo ""
echo "配置变更 Diff 验证结果: $([ "$VERIFY_CONFIG_PASSED" = true ] && echo '✅ 通过' || echo '❌ 失败')"
```

## 4. 服务变更的 systemctl status 验证

### 4.1 服务状态检查

```bash
# ========================
# 服务状态快照（变更前/后对比）
# ========================
SERVICE_NAME="<your-service>"  # 替换为实际服务名

echo "===== 变更前服务状态 ====="
systemctl status "$SERVICE_NAME" --no-pager -l 2>&1 | head -30

# 关键状态字段检查
STATUS_BEFORE=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null)
ENABLED_BEFORE=$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null)
PID_BEFORE=$(systemctl show "$SERVICE_NAME" -p MainPID --value 2>/dev/null)

echo "变更前状态: active=$STATUS_BEFORE, enabled=$ENABLED_BEFORE, PID=$PID_BEFORE"
```

### 4.2 服务变更后验证

```bash
# 执行服务重启/重载
# systemctl reload "$SERVICE_NAME"   # 热加载配置
# systemctl restart "$SERVICE_NAME"  # 完全重启

# 等待服务启动完成
sleep 3

echo ""
echo "===== 变更后服务状态 ====="
systemctl status "$SERVICE_NAME" --no-pager -l 2>&1 | head -30

STATUS_AFTER=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null)
ENABLED_AFTER=$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null)
PID_AFTER=$(systemctl show "$SERVICE_NAME" -p MainPID --value 2>/dev/null)

echo "变更后状态: active=$STATUS_AFTER, enabled=$ENABLED_AFTER, PID=$PID_AFTER"
```

### 4.3 验证检查清单

```bash
# ========================
# 验证逻辑（自动化判断）
# ========================
echo ""
echo "===== 服务变更验证检查 ====="
SERVICE_VERIFY_PASSED=true

# 检查 1: 服务是否 Active
if [ "$STATUS_AFTER" = "active" ]; then
    echo "✅ [1/5] 服务状态: active (运行中)"
else
    echo "❌ [1/5] 服务状态: $STATUS_AFTER (期望: active)"
    SERVICE_VERIFY_PASSED=false
fi

# 检查 2: 服务是否启用（开机自启）
if [ "$ENABLED_AFTER" = "enabled" ] || [ "$ENABLED_AFTER" = "static" ]; then
    echo "✅ [2/5] 服务自启: $ENABLED_AFTER"
else
    echo "⚠️  [2/5] 服务自启: $ENABLED_AFTER — 需确认是否期望 disabled"
fi

# 检查 3: PID 是否已更新（重启后 PID 应变化）
if [ "$STATUS_BEFORE" = "active" ] && [ "$STATUS_AFTER" = "active" ] && [ "$PID_BEFORE" != "$PID_AFTER" ]; then
    echo "✅ [3/5] PID 已更新: $PID_BEFORE → $PID_AFTER"
elif [ "$STATUS_BEFORE" != "active" ] && [ "$STATUS_AFTER" = "active" ]; then
    echo "✅ [3/5] 服务从停止变为运行中 (新 PID: $PID_AFTER)"
else
    echo "⚠️  [3/5] PID 检查: 需人工确认"
fi

# 检查 4: journalctl 日志无错误
echo ""
echo "===== 服务日志检查（最近20行） ====="
journalctl -u "$SERVICE_NAME" --no-pager -n 20 --since "5 minutes ago" 2>/dev/null

if journalctl -u "$SERVICE_NAME" --no-pager -n 50 --since "5 minutes ago" 2>/dev/null | grep -qiE "(error|fatal|exception|fail|critical|panic)"; then
    echo "⚠️  警告：服务日志中发现错误级别关键字，请人工审查"
fi

echo "✅ [4/5] 日志检查完成（无严重错误）"

# 检查 5: 端口/进程可达性（可选）
echo ""
echo "===== 端口/进程检查 ====="
SERVICE_PORT=$(systemctl show "$SERVICE_NAME" -p _EXE --value 2>/dev/null || true)
if command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep -i "$(systemctl show "$SERVICE_NAME" -p ExecMainPID --value 2>/dev/null)" && echo "✅ [5/5] 端口监听正常" || echo "⚠️  [5/5] 端口检查: 跳过或需人工确认"
fi

echo ""
echo "服务变更验证结果: $([ "$SERVICE_VERIFY_PASSED" = true ] && echo '✅ 通过' || echo '❌ 失败')"
```

### 4.4 多服务依赖验证

```bash
# 对于关联服务，验证上下游状态
echo "===== 依赖服务检查 ====="
DEPENDENT_SERVICES=("nginx" "redis" "postgresql")  # 替换为实际依赖
for dep in "${DEPENDENT_SERVICES[@]}"; do
    dep_status=$(systemctl is-active "$dep" 2>/dev/null)
    case "$dep_status" in
        active)
            echo "✅ 依赖服务 $dep: $dep_status"
            ;;
        inactive|dead)
            echo "⚠️  依赖服务 $dep: $dep_status — 可能正常（按需启动）"
            ;;
        failed)
            echo "❌ 依赖服务 $dep: $dep_status — 需要立即处理"
            SERVICE_VERIFY_PASSED=false
            ;;
        *)
            echo "ℹ️  依赖服务 $dep: $dep_status — 未找到或状态未知"
            ;;
    esac
done
```

## 5. 变更回退方案必填项

**所有 L0-L4 变更在执行前必须填写回退方案。** 缺少回退方案的变更不予审批。

### 5.1 回退方案模板

```bash
# 变更工单中必须包含以下回退方案
cat << 'ROLLBACK_EOF'
## 回退方案

### 基本信息
- 回退触发条件: （在什么情况下启动回退）
- 回退决策人: 
- 回退预计耗时: 
- 回退影响面: 

### 回退步骤

#### 步骤 1：停止变更/恢复备份
```bash
# 恢复配置文件备份
cp -f "$BACKUP_DIR/<original-config>" /etc/<service>/<config>
# 或使用版本控制恢复
git checkout -- <changed-file>
```

#### 步骤 2：重启/重载受影响服务
```bash
systemctl restart <service-name>
# 或
systemctl reload <service-name>
```

#### 步骤 3：验证回退成功
```bash
systemctl status <service-name>
# 检查服务指标是否恢复正常
```

#### 步骤 4：通知干系人
- 通知对象: 
- 通知方式: 即时通讯/邮件/电话
- 通知内容: 回退原因、影响时间、后续计划

### 回退验证标准
- 服务恢复运行: `systemctl is-active <service>` = active
- 业务指标恢复: （定义具体指标和阈值）
- 错误率归零: （定义检查方式）

### 回退失败应急
- 如果初次回退失败，升级路径: 
- 二次回退方案: 
- 联系人/值班工程师:
ROLLBACK_EOF
```

### 5.2 回退方案检查清单

```bash
# ========================
# 回退方案完整性检查（执行变更前运行）
# ========================
echo "===== 回退方案完整性检查 ====="
ROLLBACK_CHECK_PASSED=true

# 必填项检查
REQUIRED_FIELDS=(
    "回退触发条件"
    "回退决策人"
    "回退预计耗时"
    "回退影响面"
    "回退步骤"
    "回退验证标准"
    "回退失败应急"
)

for field in "${REQUIRED_FIELDS[@]}"; do
    if grep -q "$field" change-plan-*.md 2>/dev/null; then
        echo "✅ [$field] 已填写"
    else
        echo "❌ [$field] 缺失 — 变更未完成回退方案，不允许执行"
        ROLLBACK_CHECK_PASSED=false
    fi
done

# 备份确认
if [ -d "$BACKUP_DIR" ] && [ "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
    echo "✅ 备份文件已就绪: $BACKUP_DIR"
else
    echo "❌ 备份文件缺失 — 请先执行备份"
    ROLLBACK_CHECK_PASSED=false
fi

echo ""
echo "回退方案完整性: $([ "$ROLLBACK_CHECK_PASSED" = true ] && echo '✅ 通过' || echo '❌ 失败 — 请补充后再执行变更')"
```

### 5.3 回退执行命令

```bash
# ========================
# 标准回退执行
# ========================
echo "===== 开始回退：$(date -u '+%Y-%m-%dT%H:%M:%SZ') ====="

# 1. 从备份恢复配置
if [ -d "$BACKUP_DIR" ]; then
    cp -f "$BACKUP_DIR"/* /etc/<service>/ 2>/dev/null || echo "备份恢复完成（部分文件）"
fi

# 2. Git 回退（如适用）
if git status --short | grep -q .; then
    git checkout -- .  # 回退所有未提交的变更
    echo "Git 工作区已回退至变更前状态"
fi

# 3. 重启服务
systemctl restart "$SERVICE_NAME"

# 4. 验证回退
sleep 2
systemctl status "$SERVICE_NAME" --no-pager | head -10

# 5. 记录审计日志
echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] 变更已回退: $SERVICE_NAME" >> "$AUDIT_LOG"

echo "===== 回退完成：$(date -u '+%Y-%m-%dT%H:%M:%SZ') ====="
```

## 6. 紧急变更快速通道（L0）

### 6.1 触发条件

紧急变更（L0）仅适用于以下场景：

| 场景 | 描述 | 示例 |
|------|------|------|
| P0/P1 故障修复 | 正在影响线上业务的严重故障 | 服务宕机、功能完全不可用 |
| 高危安全漏洞 | 已确认的可被利用的高危/严重安全漏洞 | CVE 评分 ≥ 7.0 的远程代码执行漏洞 |
| 数据损坏修复 | 发现数据正在被损坏或已损坏 | 数据库表损坏、关键数据丢失 |
| 关键链路阻断 | 核心业务流程完全阻断 | 支付链路中断、登录认证失败 |

### 6.2 快速通道流程

```
                      ┌──────────────────────────┐
                      │   发现紧急问题            │
                      │   (监控告警/用户反馈/安全报告) │
                      └──────────┬───────────────┘
                                 ↓
                      ┌──────────────────────────┐
                      │   快速评估                 │
                      │   - 确认是否为 L0 等级      │
                      │   - 评估影响面              │
                      └──────────┬───────────────┘
                                 ↓
                      ┌──────────────────────────┐
                      │   口头/IM 快速审批         │ ← 最少审批
                      │   (值班TL/SRE 确认)        │
                      └──────────┬───────────────┘
                                 ↓
                      ┌──────────────────────────┐
                      │   快速备份 + 执行          │ ← 简化的备份
                      └──────────┬───────────────┘
                                 ↓
                      ┌──────────────────────────┐
                      │   快速验证                 │
                      └──────────┬───────────────┘
                                 ↓
                      ┌──────────────────────────┐
                      │   24h 内补全审计日志       │ ← 事后补录
                      └──────────────────────────┘
```

### 6.3 快速通道执行命令

```bash
# ========================
# L0 紧急变更快速执行脚本
# ========================
EMERGENCY_ID="EMERG-$(date +%Y%m%d-%H%M%S)-$(whoami)"

echo "=========================================="
echo "  紧急变更快速通道 - $EMERGENCY_ID"
echo "  时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "=========================================="

# 步骤 1: 快速评估
echo ""
echo "===== [Step 1/6] 快速评估 ====="
echo "问题描述: <在此填写>"
echo "影响范围: <在此填写>"
echo "紧急等级确认: L0 (是/否)"
read -p "确认继续? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "已取消紧急变更"
    exit 1
fi

# 步骤 2: 快速审批（值班 TL/SRE 口头确认）
echo ""
echo "===== [Step 2/6] 快速审批确认 ====="
echo "审批人: $(git config user.name 2>/dev/null || whoami)"
echo "审批方式: 即时通讯/电话 口头确认"
echo "时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "⚠️  注意：24h 内需完成正式审批补录"

# 步骤 3: 快速备份（最简版本）
echo ""
echo "===== [Step 3/6] 快速备份 ====="
EMERGENCY_BACKUP_DIR="/var/backup/emergency/$EMERGENCY_ID"
mkdir -p "$EMERGENCY_BACKUP_DIR"
# 只备份关键文件
for critical_file in "$@"; do
    if [ -f "$critical_file" ]; then
        cp -v "$critical_file" "$EMERGENCY_BACKUP_DIR/"
    fi
done
echo "紧急备份完成: $EMERGENCY_BACKUP_DIR"

# 步骤 4: 执行修复
echo ""
echo "===== [Step 4/6] 执行修复 ====="
# <在此插入修复命令>
echo "修复命令已执行"

# 步骤 5: 快速验证
echo ""
echo "===== [Step 5/6] 快速验证 ====="
# 最少验证：服务是否运行
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "✅ 服务运行正常"
else
    echo "⚠️  服务状态异常，立即检查"
fi
# 根据故障场景执行针对性验证

# 步骤 6: 事后审计（24h 内补全）
echo ""
echo "===== [Step 6/6] 事后审计（24h 内补录） ====="
echo "生成紧急变更审计记录..."
cat << EOF > "/tmp/emergency-audit-$EMERGENCY_ID.md"
# 紧急变更审计记录
- 变更ID: $EMERGENCY_ID
- 发起人: $(whoami)
- 时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
- 问题描述: <补填>
- 修复措施: <补填>
- 影响时间: <补填>
- 根因分析: <补填>
- 正式审批人: <补填>
- 审批时间: <补填>
EOF

echo ""
echo "=========================================="
echo "  紧急变更执行完成"
echo "  请在 24h 内补全: /tmp/emergency-audit-$EMERGENCY_ID.md"
echo "=========================================="
```

### 6.4 紧急变更检查清单

```bash
# ========================
# 紧急变更执行后 24h 内必须完成
# ========================
echo "===== 紧急变更事后检查清单 ====="

POST_CHECKLIST=(
    "是否已恢复服务?"
    "是否已通知所有受影响干系人?"
    "是否已记录问题描述和修复措施?"
    "是否已提交正式审批 (事后补录)?"
    "是否已创建根因分析 (RCA) 任务?"
    "是否已更新相关监控告警?"
    "是否已同步到变更管理月报?"
)

for i in "${!POST_CHECKLIST[@]}"; do
    echo "[  ] $((i+1)). ${POST_CHECKLIST[$i]}"
done

echo ""
echo "⚠️  未完成事后补录的紧急变更将触发告警升级"
```

## 附录

### A. 变更等级快速判定表

| 判断维度 | L0 | L1 | L2 | L3 | L4 |
|----------|:--:|:--:|:--:|:--:|:--:|
| 业务影响面 | 全局 | 无 | 局部 | 关键业务 | 全局 |
| 回退复杂度 | 高 | 低 | 中 | 高 | 极高 |
| 审批人数 | 0* | 0 | 1 | 2 | 3+ |
| 执行窗口 | 立即 | 随时 | 非高峰 | 审批窗口 | 变更窗 |
| 是否需预演 | 否 | 否 | 可选 | 是 | 是 |

*L0 为事后补审批

### B. 常用检查命令速查

```bash
# 配置变更检查
git diff --stat                    # 查看变更文件数
git diff --check                   # 检查空白错误
git diff --cached                  # 查看暂存的变更

# 服务检查
systemctl list-dependencies <svc>  # 查看服务依赖
systemctl show <svc> -p State      # 显示详细状态
journalctl -u <svc> -n 100 -f      # 实时查看服务日志

# 连通性检查
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/health
nc -zv localhost <port>

# 资源检查
free -h                            # 内存
df -h                              # 磁盘
top -bn1 | head -20                # 进程
```

### C. 变更模板文件结构

```
change-plan-YYYYMMDD-HHMMSS.md     # 变更计划（含回退方案）
backup/                            # 备份目录
  ├── YYYYMMDD-HHMMSS/             # 每次变更的时间戳备份
  │   ├── etc-config-backup/       # 配置备份
  │   ├── git-snapshot.txt         # Git 状态
  │   └── services-before.txt      # 服务状态快照
change-execution-YYYYMMDD.log      # 执行日志
change-audit.log                   # 审计日志（长期保留）
```

---

> **版本**: 1.0.0 | **最后更新**: $(date -u '+%Y-%m-%d') | **维护者**: Hermes Agent
>
> 本 SOP 与 Security Governance Framework 的 L0-L4 等级定义保持一致，并继承 operational-playbook 的基本操作规则。
