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
