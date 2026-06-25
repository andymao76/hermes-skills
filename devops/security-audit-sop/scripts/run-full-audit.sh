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
