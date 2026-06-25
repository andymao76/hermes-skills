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
