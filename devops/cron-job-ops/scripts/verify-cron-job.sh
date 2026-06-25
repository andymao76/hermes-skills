#!/usr/bin/env bash
# verify-cron-job.sh — Check a cron job's last run result from agent.log
# Usage: verify-cron-job.sh <job_id> [grep_time_window]
# Example: verify-cron-job.sh 69bc4fafe666 "2026-06-08 07:4[0-9]"
set -euo pipefail

JOB_ID="${1:-}"
TIME_FILTER="${2:-}"

if [[ -z "$JOB_ID" ]]; then
  echo "Usage: $0 <job_id> [grep_time_filter]" >&2
  echo "Example: $0 69bc4fafe666" >&2
  echo "Example: $0 69bc4fafe666 '2026-06-08 07:4[0-9]'" >&2
  exit 1
fi

AGENT_LOG="$HOME/.hermes/logs/agent.log"

echo "=== Cron Job $JOB_ID — Last Run Status ==="

# Get last_run info from cron list
echo ""
echo "--- From cron list ---"
hermes cron list 2>/dev/null | grep -A3 "$JOB_ID" || cronjob action=list 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for j in data.get('jobs', []):
  if j.get('job_id') == '$JOB_ID':
    print(f\"  Name:       {j.get('name', '-')}\")
    print(f\"  Status:     {j.get('last_status', '-')}\")
    print(f\"  Last run:   {j.get('last_run_at', '-')}\")
    print(f\"  Deliver:    {j.get('deliver', '-')}\")
    print(f\"  Model:      {j.get('model', '-')}\")
    print(f\"  Provider:   {j.get('provider', '-')}\")
"

echo ""
echo "--- From agent.log (truth) ---"
if [[ -n "$TIME_FILTER" ]]; then
  grep -a "$JOB_ID" "$AGENT_LOG" | grep "$TIME_FILTER" | grep -E "completed successfully|failed|delivered|error|Content Exists" | tail -5
else
  grep -a "$JOB_ID" "$AGENT_LOG" | grep -E "completed successfully|failed|delivered|error|Content Exists" | tail -5
fi

echo ""
echo "--- From gateway.log (delivery) ---"
if [[ -n "$TIME_FILTER" ]]; then
  grep -a "$JOB_ID\|delivered" "$HOME/.hermes/logs/gateway.log" 2>/dev/null | grep "$TIME_FILTER" | tail -3
else
  grep -a "$JOB_ID\|delivered" "$HOME/.hermes/logs/gateway.log" 2>/dev/null | tail -3
fi
