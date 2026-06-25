---
name: openai-compatible-api-bridge
description: >-
  Expose any LLM agent/backend as an OpenAI-compatible API endpoint so
  external tools (Open WebUI, Cursor, VS Code Copilot, custom apps, IDE
  plugins) can consume it. Covers the reverse proxy / bridge pattern where
  the agent is the server, not a client — a FastAPI adapter that translates
  /v1/chat/completions requests into Hermes CLI calls.
created_by: agent
date_created: 2026-06-06
---

# OpenAI-Compatible API Bridge

Expose an LLM agent as a standard OpenAI-compatible HTTP API endpoint,
so external tools can call it without knowing the underlying provider.

## When to use this skill

- The user asks to connect Open WebUI, Cursor, VS Code Copilot, or any
  tool that supports "Custom OpenAI API endpoint"
- The user wants a browser UI for an agent that normally runs in the terminal
- A third-party tool needs an OpenAI-compatible `/v1/chat/completions` endpoint
- The user wants to share a single agent backend across multiple frontends

## How it works

A lightweight FastAPI server (`scripts/openwebui-bridge.py`) listens on a
configurable port and translates incoming OpenAI-format requests into
Hermes CLI calls via `hermes chat -q`:

```
Open WebUI (3000)  →  Bridge (9099)  →  Hermes CLI  →  LLM provider
```

## Quick start

The bridge script lives at `~/.hermes/scripts/openwebui-bridge.py`.

```bash
# Install dependencies (one-time)
~/.hermes/venv/bin/pip install fastapi uvicorn sse-starlette

# Start the bridge
~/.hermes/scripts/hermes-bridge.sh start

# Verify
curl http://localhost:9099/v1/models
curl -X POST http://localhost:9099/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hi"}]}'
```

## Configuration

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRIDGE_HOST` | `0.0.0.0` | Listen address |
| `BRIDGE_PORT` | `9099` | Listen port |
| `BRIDGE_API_KEY` | (empty) | Optional Bearer token for auth |

### Model map

Edit `MODEL_MAP` in `openwebui-bridge.py` to add/remove available models:

```python
MODEL_MAP = {
    "siliconflow": {
        "id": "siliconflow",
        "provider": "siliconflow",
        "model": "Qwen/Qwen3.6-35B-A3B",
    },
    "deepseek-chat": {
        "id": "deepseek-chat",
        "provider": "deepseek",
        "model": "deepseek-chat",
    },
}
```

Each entry maps the model ID (what Open WebUI shows) to Hermes `--provider` and `--model` flags.

### Stream support

The bridge supports both `stream: true` and `stream: false`. Streaming
works by chunking the complete Hermes response into SSE events (Hermes
CLI `chat -q` itself does not support streaming output).

## External tool integration

### Open WebUI

Open WebUI stores external OpenAI-compatible connections at runtime — they
do NOT survive a restart unless configured via API after each boot or baked
into the DB.

**Option A: Environment variables at startup (persistent)**

```bash
OPENAI_API_BASE_URLS="http://localhost:9099/v1" \
OPENAI_API_KEYS=\
EN...true \
/home/xxx/open-webui/.venv/bin/open-webui serve --port 3000
```

**Option B: API call after startup (script-friendly)**

```bash
# Get admin token first
TOKEN=*** -s -X POST http://localhost:3000/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"..."}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])"

# Configure external connection
curl -s -X POST http://localhost:3000/api/v1/configs/connections \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"ENABLE_DIRECT_CONNECTIONS":true,"ENABLE_BASE_MODELS_CACHE":true,"OPENAI_API_BASE_URLS":"http://localhost:9099/v1","OPENAI_API_KEYS":""}'
```

**Option C: Direct DB write (most durable)**

Write `default_models` key into the `config` table's `data` JSON column to
persist the default model across restarts. The external connection itself
(URL + key) is still loaded from the config at runtime — DB controls the
default model selection.

See `references/open-webui-default-model-db.md` for the exact Python
snippet and the `config` table schema.

**Full management script:** `~/.hermes/scripts/open-webui.sh` handles
start/stop/status/logs and auto-configures the external connection via
API (Option B) on every start.

```bash
~/.hermes/scripts/open-webui.sh start   # Launch + auto-configure
~/.hermes/scripts/open-webui.sh stop
~/.hermes/scripts/open-webui.sh status
```

### Cursor / VS Code / Any OpenAI client

Same pattern — point the tool's custom API endpoint at `http://<host>:9099/v1`.

## Service management

Use `scripts/hermes-bridge.sh`:

```bash
~/.hermes/scripts/hermes-bridge.sh start    # Launch (nohup + PID file)
~/.hermes/scripts/hermes-bridge.sh stop     # Kill
~/.hermes/scripts/hermes-bridge.sh restart  # Stop + start
~/.hermes/scripts/hermes-bridge.sh status   # Check running + health
~/.hermes/scripts/hermes-bridge.sh logs     # tail the log file
```

The bridge runs via nohup and uses a PID file at `~/.hermes/bridge.pid`.
Logs go to `~/.hermes/logs/bridge.log`.

## End-to-end flow: "Set up Open WebUI for my Hermes models"

When the user asks "帮我设置 Open WebUI 用 Hermes 的大模型" or similar, follow
this checklist step by step. Never stop at writing a plan — execute everything.

### Step 1: Check current state

```bash
~/.hermes/scripts/hermes-bridge.sh status  # is the bridge running?
~/.hermes/scripts/open-webui.sh status     # is Open WebUI running?
```

Also check port bindings explicitly if scripts report STOPPED:
```bash
ss -tlnp | grep -E '9099|3000'
```

### Step 2: Start what's stopped

Always start bridge BEFORE Open WebUI (bridge must be ready when Open WebUI
configures its external connection on startup):

```bash
~/.hermes/scripts/hermes-bridge.sh start
~/.hermes/scripts/open-webui.sh start      # auto-configures external connection
```

### Step 3: Verify bridge directly

Probe the bridge without Open WebUI in the path:

```bash
# List available models
curl -s http://localhost:9099/v1/models

# Test a chat completion
curl -s -X POST http://localhost:9099/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"1+1=?"}],"stream":false}'
```

This tests: bridge process → Hermes CLI → LLM provider. If this fails, the
problem is in the bridge or the provider config, not Open WebUI.

### Step 4: Verify through Open WebUI

Get an admin token, then test the full chain:

```bash
# Get token
TOKEN=*** ...
  -s -X POST http://localhost:3000/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"..."}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

# List models exposed through Open WebUI
curl -s http://localhost:3000/api/v1/models \
  -H "Authorization: Bearer $TOKEN"

# Test chat through Open WebUI
curl -s -X POST http://localhost:3000/api/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"2+2=?"}],"stream":false}'
```

Expected: the `/v1/models` list shows both `siliconflow` and `deepseek-chat`
(and any custom models added to MODEL_MAP), and the chat endpoint returns a
valid response.

### Step 5: Tell the user what they have

After verification, summarize the running stack:

- Open WebUI URL: http://localhost:3000
- Admin login: the configured email/password
- Available models: list them with a clear recommendation (e.g. "deepseek-chat
  is faster because it's China-direct; siliconflow routes through a proxy")
- Model selection: Open WebUI shows model IDs from Bridge's MODEL_MAP

If the user wants different models, explain how to edit MODEL_MAP in
`scripts/openwebui-bridge.py` and restart the bridge.

## Pitfalls

- **Hermes CLI `chat -q` is single-turn only.** The bridge does NOT run a
  full agent loop — no tool calling, no file access, no subagent delegation
  via the bridge. For full agent capabilities, use `hermes` in the terminal.
  The bridge is for chat/QA/translation/code-pattern queries only.

- **Model name must match the provider.** The `MODEL_MAP` entry needs both
  the correct `provider` (from config.yaml) AND the correct `model` name
  for that provider. The `--provider` flag does NOT auto-resolve the model.

- **System Python `externally-managed-environment`.** Ubuntu 22.04+ blocks
  `pip install` system-wide. Always install packages in Hermes's venv:
  `~/.hermes/venv/bin/pip install <pkg>`.

## Architecture / Site Inventory

When asked to describe the "current system architecture" holistically, use the
one-shot inventory at `references/stack-inventory-workflow.md` — it dumps
services, ports, Docker containers, provider chains, and memory state in a
single script, producing consistent structured output for diagnosis or
documentation.

- **systemd user service status 216/GROUP.** On some Ubuntu versions (24.04, systemd 255), user-level systemd services fail with `status=216/GROUP` ("Failed to determine supplementary groups: Operation not permitted"). This is triggered by **both** an empty `SupplementaryGroups=` field and a `User=` field in user-mode services (where it's redundant). Fix: delete both lines:
  ```bash
  sed -i '/^SupplementaryGroups=$/d' ~/.config/systemd/user/hermes-bridge.service
  sed -i '/^User=/d' ~/.config/systemd/user/hermes-bridge.service
  systemctl --user daemon-reload && systemctl --user restart hermes-bridge
  ```
  After fixing, if restart still fails with `status=1/FAILURE` and `address already in use`, there's an old manual process still holding the port — find it with `ss -tlnp | grep 9099` and kill it first. See `references/systemd-216-group-pitfall.md` for the full diagnostic flow.

- **Concurrent requests.** The bridge processes requests sequentially
  because Hermes CLI is a single-process tool. Multiple concurrent users
  will queue. For concurrent workloads, consider deploying the bridge
  behind a load balancer or using multiple bridge instances on different
  ports.

- **Timeout.** Hermes CLI has a 120-second timeout in the bridge script.
  Very long queries (large code generation, multi-turn reasoning) may
  time out. Increase the `timeout=120` in `call_hermes()` if needed.

- **Service restart kills prior nohup process if port is held.** When
  restarting the bridge, the old process may still hold the port even after
  `kill` (zombie state). Use `kill -9 <pid>` or `ss -tlnp | grep 9099` to
  identify the stubborn PID before starting a new instance. The
  `hermes-bridge.sh restart` script handles this — call it instead of
  manual `nohup`.

- **Adding a new model only needs a bridge restart, not Open WebUI restart.**
  After editing MODEL_MAP in `openwebui-bridge.py`, only restart the bridge
  (`~/.hermes/scripts/hermes-bridge.sh restart`). Open WebUI re-polls
  `/v1/models` automatically — the new model appears in the dropdown
  without restarting Open WebUI. This works because Open WebUI discovers
  models at runtime via the OpenAI-compatible `/v1/models` endpoint, not
  from a static config file.

- **Dify Web 3000 is NOT mapped to host.** Despite both Open WebUI and Dify
  Web listening on port 3000 internally, they occupy different network
  namespaces — Dify Web's 3000 is container-internal only, accessible via
  Nginx. The `docker port` command is the truth. See
  `references/dify-web-port-no-conflict.md`.

## Open WebUI Admin Credential Management

When the Open WebUI admin password is unknown (fresh install or lost),
reset it by directly writing a new bcrypt hash to the database:

```bash
python3 -c "
import bcrypt, sqlite3
pw = 'new-password'
hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()
db = sqlite3.connect('/path/to/webui.db')
db.execute('UPDATE auth SET password = ? WHERE email = ?', (hashed, 'admin@example.com'))
db.commit()
print('Password updated')
"
```

The token from `POST /api/v1/auths/signin` expires on gateway restart.
Always re-fetch before API calls.

## Gateway Telegram Authorization (common mismatch)

A common misconfiguration: the `.env` file has `TELEGRAM_ALLOWED_USERS` set
to the **Bot's user ID** (from the bot token prefix) instead of the
**human user's Telegram user ID**.

The gateway checks authorization via **environment variables** in `.env`,
NOT the `allowed_chats` field in `config.yaml`:
- `TELEGRAM_ALLOWED_USERS` — comma-separated Telegram user IDs (for DM)
- `TELEGRAM_GROUP_ALLOWED_CHATS` — comma-separated group/supergroup chat IDs
- `TELEGRAM_ALLOW_ALL_USERS=true` — blanket allow (debug only)

See `references/telegram-home-channel-cli-setup.md` for the full diagnostic and the asymmetric home-channel setup.

Find your Telegram user ID by sending a message to the bot and checking
the gateway log for `Unauthorized user: <YOUR_ID>`. Or use:
```bash
curl -s --proxy ... "https://api.telegram.org/bot<TOKEN>/getUpdates" | jq '.result[0].message.from.id'
```

## Cross-reference: dedicated Open WebUI skill

For comprehensive Open WebUI coverage — installation methods (Docker / pip), plugin system (Tools/Pipes/Filters/Actions), database operations (user management, password reset, default model config), troubleshooting, and full feature reference — load the dedicated skill:

```
/skill open-webui
```

The `open-webui` skill (under `productivity/`) supersedes the Open WebUI sections in this bridge skill. This bridge skill remains the authoritative reference for the **Hermes Bridge layer** (the FastAPI adapter itself, model mapping, bridge management scripts).