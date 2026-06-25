#!/bin/bash
# check_iwlwifi.sh - 监控 iwlwifi 中断增长情况
# 用途：在系统卡顿/冻结前后执行，追踪 WiFi 网卡中断是否异常暴增
# 用法：
#   bash <skill-path>/scripts/check_iwlwifi.sh          # 直接运行
#   sudo cp <skill-path>/scripts/check_iwlwifi.sh /usr/local/bin/ && sudo chmod +x /usr/local/bin/check_iwlwifi.sh  # 安装到系统

echo "==== $(date) ===="
uptime
free -h | head -2
echo "--- iwlwifi interrupts ---"
grep iwl /proc/interrupts
echo "=========================="
