#!/bin/bash
# check_iwlwifi.sh — Monitor iwlwifi interrupt activity for AER storm detection
# Usage: check_iwlwifi.sh
# Run when suspecting system freeze to capture iwlwifi interrupt growth rate

echo "==== $(date) ===="
uptime
free -h | head -2
echo "--- iwlwifi interrupts ---"
grep iwl /proc/interrupts
echo
