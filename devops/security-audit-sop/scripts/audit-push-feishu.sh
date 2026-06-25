#!/bin/bash
# 安全审计报告 → 飞书推送
# 读取最新的审计报告，提取摘要，推送到飞书
# 位置: ~/.hermes/scripts/audit-push-feishu.sh (供cron使用) + 本skill目录

set -uo pipefail

AUDIT_DIR="$HOME/knowledge/_system/security/audit-reports"
FEISHU_CLIENT="$HOME/.hermes/venv/bin/python3 $HOME/.hermes/skills/feishu-openapi/scripts/feishu_client.py"

# 从 .env 逐行读取飞书配置（避免 source 整份文件因特殊字符崩溃）
FEISHU_HOME_CHANNEL=$(grep "^FEISHU_HOME_CHANNEL=" "$HOME/.hermes/.env" | head -1 | cut -d= -f2-)
FEISHU_APP_ID=$(grep "^FEISHU_APP_ID=" "$HOME/.hermes/.env" | head -1 | cut -d= -f2-)
FEISHU_APP_SECRET=$(grep "^FEISHU_APP_SECRET=" "$HOME/.hermes/.env" | head -1 | cut -d= -f2-)

export FEISHU_APP_ID FEISHU_APP_SECRET

# 找最新审计报告
LATEST=$(ls -t "$AUDIT_DIR"/security-audit-*.md 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then
    echo "No audit report found."
    exit 1
fi

REPORT_DATE=$(basename "$LATEST" | sed 's/security-audit-//;s/\.md$//')

# 提取关键指标
ISO_VIOLATIONS=$(grep -c "隔离违规" "$LATEST" || echo "0")
SENSITIVE_HITS=$(grep -c "敏感词" "$LATEST" || echo "0")
# 总结行在 ## 总结 之后隔一个空行，需 -A2 再 tail -1
SUMMARY_LINE=$(grep -A2 "^## 总结" "$LATEST" | tail -1 || echo "无摘要")

# 状态图标
if grep -q "❌ 异常" "$LATEST" 2>/dev/null; then
    STATUS_ICON="⚠️"
    STATUS_TEXT="发现异常"
else
    STATUS_ICON="✅"
    STATUS_TEXT="全部通过"
fi

# 构建消息
TITLE="【每日安全审计报告】${REPORT_DATE}"
MSG="${TITLE}\n"
MSG="${MSG}──────────────────\n"
MSG="${MSG}状态: ${STATUS_ICON} ${STATUS_TEXT}\n"
MSG="${MSG}隔离违规: ${ISO_VIOLATIONS} 处\n"
MSG="${MSG}敏感词命中: ${SENSITIVE_HITS} 处\n"
MSG="${MSG}──────────────────\n"
MSG="${MSG}${SUMMARY_LINE}\n"
MSG="${MSG}──────────────────\n"
MSG="${MSG}⏰ $(date '+%H:%M:%S') | Hermes Security"

# 发送到飞书
$FEISHU_CLIENT send-text "$FEISHU_HOME_CHANNEL" "$MSG" 2>/dev/null
echo "Feishu push: $REPORT_DATE"
