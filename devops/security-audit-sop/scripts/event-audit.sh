#!/bin/bash
# event-audit.sh — 事件驱动安全审计
set -euo pipefail

usage() {
  echo "用法: $0 --event <事件名称> [--scope <范围>]"
  echo "示例: $0 --event '异常登录检测' --scope 'SSH,Auth'"
  exit 1
}

EVENT=""
SCOPE="全量"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --event) EVENT="$2"; shift 2 ;;
    --scope) SCOPE="$2"; shift 2 ;;
    *) usage ;;
  esac
done

if [ -z "$EVENT" ]; then
  usage
fi

AUDIT_DIR=~/knowledge/_system/security_audit
REPORT_DIR="$AUDIT_DIR/reports"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="$REPORT_DIR/event-audit-$TIMESTAMP.md"

mkdir -p "$REPORT_DIR"

echo "=== 事件驱动安全审计 ==="
echo "触发事件: $EVENT"
echo "审计范围: $SCOPE"
echo ""

# 根据事件类型执行对应审计
case "$EVENT" in
  *登录*|*auth*|*Auth*)
    echo "→ 执行 SSH Key 审计 ..."
    SSH_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-ssh-keys.sh 2>&1 || true)
    echo "→ 执行 MCP 审计 ..."
    MCP_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-mcp.sh 2>&1 || true)
    ;;
  *部署*|*deploy*|*配置*|*config*|*config*)
    echo "→ 执行服务变更审计 ..."
    SVC_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-service-changes.sh 2>&1 || true)
    echo "→ 执行权限审计 ..."
    PERM_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-permissions.sh 2>&1 || true)
    ;;
  *漏洞*|*vuln*|*cve*|*CVE*)
    echo "→ 执行完整 Secret Scanner ..."
    SECRET_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-secret-scanner.sh 2>&1 || true)
    echo "→ 执行权限审计 ..."
    PERM_RESULT=$(bash ~/skills/security-audit-sop/scripts/audit-permissions.sh 2>&1 || true)
    ;;
  *)
    echo "→ 未匹配特定事件类型，执行全量审计 ..."
    bash ~/skills/security-audit-sop/scripts/run-full-audit.sh
    exit 0
    ;;
esac

# 生成事件审计报告
cat > "$REPORT_FILE" << EOF
# 事件驱动安全审计报告 — $EVENT

| 属性 | 值 |
|------|-----|
| 触发事件 | $EVENT |
| 触发时间 | $(date '+%Y-%m-%d %H:%M:%S') |
| 审计范围 | $SCOPE |

---

## 事件描述

$EVENT 触发安全审计。

## 审计结果

\`\`\`
${SECRET_RESULT:-}(未执行)
${PERM_RESULT:-}(未执行)
${SSH_RESULT:-}(未执行)
${MCP_RESULT:-}(未执行)
${SVC_RESULT:-}(未执行)
\`\`\`

## 建议措施

根据审计结果采取相应修复措施。详情请参考安全审计 SOP。

---

*事件响应报告 — 由 Hermes Agent 安全审计 SOP 自动生成*
EOF

echo ""
echo "========================================"
echo "  事件审计完成"
echo "  事件: $EVENT"
echo "  报告: $REPORT_FILE"
echo "========================================"
