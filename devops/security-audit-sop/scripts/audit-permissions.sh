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
