# Full System Snapshot — Canonical Probe Commands

This reference captures the exact commands used to produce the 8-dimension system overview.
Use as a recipe when collecting data for a full architecture dump.

## 1. Hermes Version & Repo Info

```bash
which hermes && hermes --version
cat ~/.hermes/config.yaml   # Redact api_key lines before showing user
ls -la ~/.hermes/
```

Key files to note in ~/.hermes/:
- config.yaml — main configuration
- .env — secrets (never display raw)
- memory_store.db — holographic memory
- state.db — session DB
- knowledge_index.db — FTS5 knowledge index
- SOUL.md — system prompt override
- cron/jobs.json — scheduled jobs
- gateway.pid / gateway.lock — gateway state
- processes.json — background processes
- logs/ — agent.log, errors.log, gateway.log

## 2. System Services (systemd)

```bash
systemctl --user list-units --type=service | grep -E '(hermes|clash|xvfb)'
systemctl list-units --type=service --state=running --no-pager | head -30
```

Common Hermes services:
- hermes-gateway.service — messaging platform gateway
- hermes-bridge.service — OpenAI-compatible API bridge

## 3. Listening Ports

```bash
ss -tlnp | grep -E '(:8642|:9099|:7897|:18060|:3000|:80|:443)'
```

Port mapping:
- 8642 — Hermes Gateway (REST API + WebSocket)
- 9099 — Hermes Bridge (OpenAI-compatible API)
- 18060 — Xiaohongshu MCP HTTP server
- 7897 — Clash proxy
- 3000 — Open WebUI (if running)
- 80/443 — Dify (if running, behind nginx)

## 4. MCP Server Configuration

Extract from config.yaml under `mcp_servers:` section. For each server, note:
- command and args
- protocol (stdio via Python/node, or HTTP)
- connect_timeout / timeout
- env vars (especially proxy settings like HTTP_PROXY, HTTPS_PROXY)
- special requirements (DISPLAY=:99 for Xvfb, DISPLAY=:99, no_proxy for taobao)

Typical servers found:
- db-query — local SQLite query
- xiaohongshu — stdio bridge to Go HTTP server :18060
- zhihu — Python MCP server
- csdn — Python MCP server
- wikipedia — wikipedia-mcp Go binary, needs proxy
- taobao — Python MCP server, needs Xvfb:99
- session_reset:filesystem — npx @modelcontextprotocol/server-filesystem
- session_reset:github — npx @modelcontextprotocol/server-github

## 5. Skills Library

Use `skills_list()` tool call (no shell alternative). Count and categorize:
- Total skill count
- Category breakdown
- Notable special skills (Prism series, Chinese-platform adapters, etc.)
- Agent-created vs bundled vs hub-installed

## 6. Knowledge Base

```bash
find ~/knowledge/ -type f | wc -l
for d in ~/knowledge/*/; do echo "$(basename $d): $(find $d -type f | wc -l) files"; done
du -sh ~/.hermes/knowledge_index.db 2>/dev/null
```

Subdirectory hierarchy matters — articles_baidu/ often dominates raw file count.
Break down by subdirectory for meaningful statistics.

## 7. Memory Store

```bash
ls -la ~/.hermes/memories/
```

If holographic memory is enabled (memory.provider=holographic):
```bash
sqlite3 ~/.hermes/memory_store.db "SELECT COUNT(*) FROM facts;" 2>/dev/null
```

Read MEMORY.md and USER.md for current injected content.

## 8. Session Database

```bash
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions;" 2>/dev/null
sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM messages;" 2>/dev/null
```

Handle WAL lock gracefully — if empty, check for .db-shm and .db-wal files.

## 9. Cron Jobs

Read `~/.hermes/cron/jobs.json` for the full job list. For each job extract:
- name, schedule (cron expression), type (no_agent = script, false = AI-driven)
- delivery targets (origin, telegram, discord, weixin, local)
- last_status (null = never run, "ok" or "error")
- enabled state

## 10. Additional Context

```bash
cat ~/.hermes/SOUL.md
node --version
npm --version
python3 --version
# Check git version of hermes-agent
(cd ~/.hermes/hermes-agent && git log --oneline -3 2>/dev/null)
```
