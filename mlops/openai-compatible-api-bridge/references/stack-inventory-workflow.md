# System Stack Inventory — How to snapshot the full architecture

When the user asks "what's the current system state", "how is everything connected", or similar broad architecture questions, run this comprehensive inventory script.

## The inventory commands (one-shot)

```bash
# Run all at once and capture the output for reference:

(
echo "=== 1. Hermes Agent ==="
hermes --version 2>&1

echo ""
echo "=== 2. Systemd Services ==="
systemctl --user status hermes-gateway --no-pager 2>&1 | grep -E "Active:|Main PID:" | head -3
systemctl --user status hermes-bridge --no-pager 2>&1 | grep -E "Active:|Main PID:" | head -3
systemctl status docker --no-pager 2>&1 | grep "Active:" | head -1

echo ""
echo "=== 3. Open WebUI ==="
pid=$(cat ~/open-webui/webui.pid 2>/dev/null)
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
  echo "RUNNING (PID $pid)"
  curl -s -o /dev/null -w "  http://localhost:3000 -> HTTP %{http_code}\n" http://localhost:3000/
else
  echo "STOPPED"
fi

echo ""
echo "=== 4. Port Map ==="
ss -tlnp | awk 'NR>1 {split($4, a, ":"); port=a[length(a)]; split($NF, b, "\""); proc=b[2]; if(proc=="") proc=b[1]; printf "  %-6s → %s\n", port, proc}' | sort -n

echo ""
echo "=== 5. Hermes Config (key) ==="
hermes config list 2>/dev/null | grep -E "provider|model|default" | head -8

echo ""
echo "=== 6. Docker ==="
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}" 2>/dev/null

echo ""
echo "=== 7. Proxy Chain ==="
curl -s --connect-timeout 3 --max-time 5 -o /dev/null -w "  api.deepseek.com: %{http_code} (direct)\n" https://api.deepseek.com/v1
curl -s --connect-timeout 3 --max-time 5 --proxy http://127.0.0.1:7897 -o /dev/null -w "  api.siliconflow.com: %{http_code} (via proxy)\n" https://api.siliconflow.com/v1

echo ""
echo "=== 8. Bridge Health ==="
curl -s --connect-timeout 3 http://localhost:9099/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Models: {len(d.get(\"data\",[]))} available')" 2>/dev/null || echo "  Not responding"

echo ""
echo "=== 9. Knowledge & Memory ==="
ls ~/.hermes/memory_store.db 2>/dev/null && echo "  Memory DB: $(du -h ~/.hermes/memory_store.db | cut -f1)" || echo "  Memory: none"
ls ~/knowledge/ 2>/dev/null && echo "  Knowledge dir: $(du -sh ~/knowledge/ 2>/dev/null | cut -f1)" || echo "  Knowledge: none"
echo "  Skills: $(ls ~/.hermes/skills/ 2>/dev/null | wc -l) installed"

echo ""
echo "=== 10. System ==="
echo "  Host: $(hostname), $(uname -r), $(uname -m)"
mem_total=$(awk '/^MemTotal:/ {printf "%.0f", $2/1024}' /proc/meminfo)
mem_avail=$(awk '/^MemAvailable:/ {printf "%.0f", $2/1024}' /proc/meminfo)
echo "  Memory: ${mem_avail}MB / ${mem_total}MB available"
echo "  Disk: $(df -h / | tail -1 | awk '{print $3"/"$2 " (" $5 ")"}')"
) 2>&1
```

## Interpreting the output

After capturing, structure the answer as a table with these sections:
1. **Core Services** — Agent version, Gateway/Bridge/Open WebUI status
2. **Port Topology** — which port belongs to which process
3. **Provider Chain** — which model routes through which provider + proxy
4. **Data Flow** — how the user reaches each service (Telegram → Gateway → Agent; Browser → Open WebUI → Bridge → Agent)
5. **Known Quirks** — any ongoing issues (port conflicts, expired tokens, proxy routing)
