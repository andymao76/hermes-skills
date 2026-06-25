#!/bin/bash
# 全链路：安全审计 → 报告 → 飞书推送
# no-agent 模式，纯脚本运行，不消耗 LLM token
# 位置: ~/.hermes/scripts/audit-full-chain.sh (供cron使用) + 本skill目录

set -uo pipefail

AUDIT_SCRIPT="$HOME/.hermes/scripts/security-audit.py"
PUSH_SCRIPT="$HOME/.hermes/scripts/audit-push-feishu.sh"
AUDIT_DIR="$HOME/knowledge/_system/security/audit-reports"

echo "=== Hermes 安全审计全链路 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Step 1: 运行审计（允许exit 1=发现安全问题，属于正常行为）
echo ">>> [1/2] 运行安全审计..."
python3 "$AUDIT_SCRIPT" 2>&1
AUDIT_EXIT=$?
echo "(审计退出码: $AUDIT_EXIT)"

# 验证报告已生成
sleep 1
LATEST=$(ls -t "$AUDIT_DIR"/security-audit-*.md 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then
    echo "❌ 未生成审计报告"
    exit 1
fi
echo "✅ 报告: $(basename "$LATEST")"

# Step 2: 推送到飞书
echo ">>> [2/2] 推送审计摘要到飞书..."
bash "$PUSH_SCRIPT"
PUSH_EXIT=$?
if [ $PUSH_EXIT -eq 0 ]; then
    echo "✅ 飞书推送成功"
else
    echo "❌ 飞书推送失败 (exit=$PUSH_EXIT)"
fi

echo "=== 全链路完成 ==="
