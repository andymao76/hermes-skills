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
  grep -i 'IdentityFile' "$SSH_DIR/config" 2>/dev/null | head -5
fi

# 密钥指纹汇总
echo "--- 本地密钥指纹 ---"
for key in "$SSH_DIR"/id_*.pub; do
  [ -f "$key" ] || continue
  echo "  $(ssh-keygen -lf "$key" 2>/dev/null)"
done
