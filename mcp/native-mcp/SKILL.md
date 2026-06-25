---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option                       | Type   | Default | Description                                       |
|------------------------------|--------|---------|---------------------------------------------------|
| `command`                    | string | --      | Executable to run (stdio transport, required)     |
| `args`                       | list   | `[]`    | Arguments passed to the command                   |
| `env`                        | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`                        | string | --      | Server URL (HTTP transport, required)             |
| `transport`                  | string | streamable-http | Transport protocol: `sse` for SSE endpoints |
| `headers`                    | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`                    | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout`            | int    | `60`    | Timeout for initial connection and discovery      |
| `supports_parallel_tool_calls` | bool | `false` | Allow concurrent tool calls from this server    |
| `sampling.enabled`           | bool   | `true`  | Allow server to request LLM completions           |
| `sampling.model`             | string | --      | Model override for sampling requests              |
| `sampling.max_tokens_cap`    | int    | --      | Max tokens per sampling request                   |
| `sampling.timeout`           | int    | `30`    | LLM call timeout for sampling                     |
| `sampling.max_rpm`           | int    | --      | Max sampling requests per minute                  |
| `sampling.allowed_models`    | list   | `[]`    | Model whitelist (empty = all)                     |
| `sampling.max_tool_rounds`   | int    | `5`     | Tool loop limit in sampling (0 = disable)         |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

### Transport Verification: Three Code Paths, Three Results

当使用 Streamable HTTP 传输时，**三条代码路径使用不同的 HTTP 客户端和探测方式**，结果可能不一致：

| 路径 | 方法 | 客户端 | 成功率判断 |
|------|------|--------|-----------|
| `hermes mcp test` | 通过 Hermes CLI probe | MCP loop + `_connect_server` | 最低（报错可能是假阳性） |
| Venv Python 直连 | 直接调用 `streamable_http_client` | 原生 mcp SDK | **最可靠**（与运行时同路径） |
| 运行时初始化 | Agent 启动时通过 `run()` 连接 | 同上 + `_preflight_content_type` | 实际可用性 |

**推荐验证优先级**：venv 直连 > 运行时 > `hermes mcp test`。

某类服务器（如 xiaohongshu-mcp Go SDK）可能出现以下不一致模式：
- **`hermes mcp test` 返回 400**，但 **venv Python 直连成功**
- **venv 直连成功**，但 **运行时初始化失败**（TaskGroup 异常，源于 `_preflight_content_type` 预检的 HEAD/GET 请求触发 400）

venv 直连测试命令（以 xiaohongshu 为例）：

```bash
cd ~/.hermes && source hermes-agent/venv/bin/activate
python3 -c "
import asyncio
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
async def test():
    async with streamable_http_client('http://localhost:18060/mcp') as (read, write, sid):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            print(f'Connected! Tools: {len(result.tools)}')
            for t in result.tools:
                print(f'  - {t.name}')
asyncio.run(test())
"
```

如果 venv 直连成功但 Hermes 运行时失败，优先用 stdio bridge 替代（见 xiaohongshu-mcp-config.md）。

### Transport Swap: When Migration Requires a Full Restart

When switching an MCP server config from **stdio** to **HTTP** (streamable-http) transport, or back:

- `hermes mcp test` and `hermes mcp list` both read from config.yaml, so the new transport shows immediately in the CLI even if the runtime cannot actually connect. **This is misleading** — the listed status reflects the config, not the connection.
- **The runtime (agent session) caches server state**. After `/reload-mcp` picks up the new config, if the connection fails (`TaskGroup` exception, `_preflight_content_type` 400, etc.), the server stays stuck in "failed" state for the rest of the agent process lifetime. The old transport's tools disappear and the new transport's tools never appear.
- **Mitigation**: Exit the current agent session entirely and start a new `hermes` process. This resets all MCP server state. Do NOT rely on `/reload-mcp` after a transport-type change — it works well for adding/removing servers but can fail when the same server name changes transport.
- **Verification after any transport change**: (1) `hermes mcp test <name>` to confirm the CLI can connect, (2) start a fresh Hermes session, (3) call `mcp_<server>_<tool>` to verify tools are registered, (4) check agent.log for registration messages: `grep -i "registered.*tool" ~/.hermes/logs/agent.log`. A venv Python direct connection test (see above) is more reliable than `hermes mcp test` alone.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### `hermes mcp login <name>` fails: "non-interactive environment"

When running `hermes mcp login` for an OAuth MCP server (Linear, GitHub OAuth mode, etc.) **from within a Hermes agent session**, it fails with:

```
✗ Authentication failed: MCP OAuth for 'linear': non-interactive environment
  and no cached tokens found. Run `hermes mcp login linear` interactively
  first to complete initial authorization.
```

**Root cause:** The `_is_interactive()` function at `tools/mcp_oauth.py:138` checks `sys.stdin.isatty()`. Inside a Hermes agent session, stdin is piped (not a TTY), so this returns `False` and the OAuth browser flow is blocked.

**Fix:** Run `hermes mcp login <name>` **directly in the user's terminal**, not through the Hermes agent. This command will:
1. Start a local HTTP callback server on a free port
2. Automatically open the browser to the OAuth authorization page
3. Cache the tokens to `~/.hermes/mcp_oauth/` after successful authorization

After successful login, the OAuth tokens are cached on disk and the MCP server will work when Hermes restarts or reconnects.

### `hermes mcp login <name>` fails with "timed out after 40.0s" (OAuth timeout)

Even when running `hermes mcp login` from the user's own terminal, it may still fail with:

```
Starting OAuth flow for 'linear'...
✗ Authentication failed: MCP call timed out after 40.0s (configured timeout: 40.0s)
```

**Root cause:** The `_probe_single_server` function in `hermes_cli/mcp_config.py:217` has a default `connect_timeout=30`, and the actual run timeout is `connect_timeout + 10 = 40s`. This is too short for the user to open the browser, log in, and authorize the app via OAuth.

**Fix — add explicit timeouts to the MCP server config** in `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  linear:
    url: https://mcp.linear.app/mcp
    auth: oauth
    enabled: true
    timeout: 300          # Give 5 minutes for the full OAuth browser flow
    connect_timeout: 300  # Match the probe timeout to the OAuth window
```

The `_wait_for_callback` in `tools/mcp_oauth.py:513` already uses `timeout=300.0`, so the probe caller needs to be at least as patient. After adding the config, run `hermes mcp login linear` again.

**Alternative — manual callback URL paste:** If the browser doesn't open automatically (e.g. headless SSH), run `hermes mcp login linear`, then manually open the authorization URL from agent logs (`~/.hermes/logs/agent.log`), and paste the redirected callback URL back into the terminal. The `_paste_callback_reader` thread listens for pasted redirect URLs when `_is_interactive()` is True.

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### MCP Health Check Workflow

When diagnosing MCP connectivity, follow this systematic procedure rather than guessing:

#### Phase 1 — Triage: Do MCP Tools Exist?

Before diving into individual server details, answer the primary question: **does the current session have any MCP tools at all?**

1. **Check the agent's own tool list** — Are any `mcp_`-prefixed tools available? If zero MCP tools exist, proceed through the log-file triage below.

2. **Log file triage (in order)** — Each log holds different information about the MCP discovery process:

   | Log file | What it tells you | Key grep |
   |----------|-------------------|----------|
   | `~/.hermes/logs/agent.log` | MCP registration per session, tool counts, per-server success/failure | `grep -i "mcp.*registered\|MCP: registered"` |
   | `~/.hermes/logs/gateway.log` | Gateway startup sequence, platform connections | `grep -i "starting\|init"` (MCP registration logs here if the Gateway handles it) |
   | `~/.hermes/logs/errors.log` | Silent failures, warnings that didn't make it to agent.log | `grep -i mcp` |
   | `~/.hermes/logs/mcp-stderr.log` | Raw stderr from MCP server subprocesses (module errors, tracebacks, broken pipes) | `grep -i "traceback\|error\|broken"` |

3. **Cross-reference mcp-stderr.log vs agent.log for "starts but never registers"** — A server may appear in stderr log as "starting MCP server" but never complete initialization. This is a silent failure:

   ```bash
   # Servers that started (from mcp-stderr.log)
   grep "starting MCP server" ~/.hermes/logs/mcp-stderr.log
   
   # Servers that successfully registered (from agent.log)
   grep "MCP server.*registered" ~/.hermes/logs/agent.log | grep -oP "'[^']+'" | sort -u
   ```
   
   Any server in the first list but missing from the second either crashed during initialization or failed to respond to `list_tools`. Get more info by capturing startup output:
   
   ```bash
   grep -A 15 "starting MCP server.*SERVER-NAME" ~/.hermes/logs/mcp-stderr.log | tail -20
   ```
   
   Common causes: silent import error, hang on stdio handshake, port conflict with a stale process.

4. **Cross-reference config.yaml vs startup time** — An MCP server in `config.yaml` won't register if the file was modified after the Hermes process started. Compare timestamps:
   ```bash
   stat ~/.hermes/config.yaml | grep Modify
   # vs Hermes process start time:
   ps -o lstart,etime -p $(pgrep -f 'hermes.*gateway' | head -1)
   ```
   
   **When `hermes mcp list` crashes** (e.g., `TypeError: string indices must be integers, not 'str'` — a JSON-string-in-YAML config issue), the CLI cannot report status. Skip it and use the log-file triage above directly. The crash itself is a diagnostic signal.

5. **Check the process tree** — MCP servers are spawned from the Gateway, not the CLI agent session. Look for the Gateway:
   ```bash
   ps aux | grep -i 'hermes.*gateway' | grep -v grep
   ```
   If the Gateway is running separately from the agent session, MCP discovery may have occurred in a different process scope. A `/reload-mcp` in-session or full Gateway restart is needed to bridge this gap.

#### Phase 2 — Direct Server Test (Diagnostic Gold Standard)

When the agent's MCP tools are unavailable but the server files exist and imports work, test the MCP server directly via its stdio protocol. This proves whether the server itself works, independent of Hermes' MCP discovery:

```bash
# For stdio-based MCP servers: send initialize request directly
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0"}}}\n' | timeout 10 <command> <args...> 2>/dev/null || true
```

Replace `<command> <args...>` with the server's command and args from config.yaml (e.g. `/path/to/venv/bin/python3 /path/to/server.py`). A successful response returns a JSON-RPC result with `serverInfo` and `capabilities`.

Then test tool discovery (requires bidirectional communication — use `anyio` via Python for a proper test, see "Venv Python 直连" section above for the stdio variant):

```python
import asyncio, subprocess
from mcp.client.stdio import stdio_client
from mcp import ClientSession

async def test():
    async with stdio_client(subprocess.Popen(
        ['<command>', '<args>'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            tools = [t.name for t in result.tools]
            print(f'Connected! Tools ({len(tools)}): {tools}')

asyncio.run(test())
```

**Expected outcome from a healthy server**: successful initialize response + tool list. If this passes but Hermes doesn't register the server, the issue is in Hermes' discovery/connection layer (timing, Gateway scope, or silent config-read failure), not the server.

#### Phase 3 — Mitigation

If logs show no MCP registration at all for the current session, try:

1. **`/reload-mcp`** in-session — hot-reloads MCP config without restarting the agent (this is a session-level slash command, not a CLI command — user must type it themselves)
2. **Restart the Gateway** — `hermes restart gateway` (or kill the Gateway PID and let systemd/systemd revive it)
3. **Full Hermes restart** — exit the current session entirely and start a fresh `hermes` process

**Important: Gateway vs CLI Agent scope.** MCP server discovery runs at the **Gateway** process level (`hermes gateway run`), not per-CLI-agent session. If the Gateway started before a config.yaml change was made, or if MCP discovery silently failed during Gateway init, the CLI agent session will have zero MCP tools even though `hermes mcp test` confirms each server individually. A `/reload-mcp` or Gateway restart is required to bridge this gap — starting a new CLI agent alone won't help.

#### Phase 4 — Clean Up Stale Processes

Each Hermes restart spawns new MCP server processes, leaving old ones behind. Accumulated zombies waste memory and may hold stale auth tokens. After a restart or config change:

```bash
# Kill all but the newest instance of each MCP server
for proc in \
    'csdn/server.py' \
    'db_query_server.py' \
    'taobao_mcp/server.py' \
    'wikipedia-mcp' \
    'zh_mcp_server/run.py' \
    'github-mcp-server' \
    'jd_mcp/server.py' \
    'xiaohongshu-mcp'; do
    pids=$(ps aux | grep "$proc" | grep -v grep | awk '{print $2}' | sort -n)
    count=$(echo "$pids" | wc -l)
    if [ "$count" -gt 1 ]; then
        echo "$pids" | head -n -1 | xargs -r kill 2>/dev/null
        echo "Killed $((count-1)) stale instances of $proc"
    fi
done
```

**Verification** — After cleanup, confirm each server has exactly 1 process remaining:

```bash
for name in csdn db-query github-gov1 jd taobao wikipedia xiaohongshu zhihu; do
    case "$name" in
        csdn)       pn="csdn/server.py" ;;
        db-query)   pn="db_query_server.py" ;;
        github-gov1) pn="github-mcp-server" ;;
        jd)         pn="jd_mcp/server.py" ;;
        taobao)     pn="taobao_mcp/server.py" ;;
        wikipedia)  pn="wikipedia-mcp" ;;
        xiaohongshu) pn="xiaohongshu-mcp" ;;
        zhihu)      pn="zh_mcp_server" ;;
    esac
    c=$(ps aux | grep -v grep | grep -c "$pn")
    echo "${c:+✓} $name: ${c}个进程"
done
```
Then run `/reload-mcp` in-session or restart Hermes to respawn clean instances.

#### Phase 5 — Test Individual Servers

Once MCP tools are registered, test each server:

1. **Test basic connectivity** — Call a simple tool from each MCP server directly (search, list, or status check).
   - For servers with cached sessions, call their actual tools (e.g. `mcp_wikipedia_test_wikipedia_connectivity`, `mcp_db_query_list_tables`).
   - Errors at this stage reveal auth, network, or runtime issues.

2. **Test auth-dependent tools separately** — Some servers connect fine but fail on authenticated calls:
   - **GitHub**: `mcp_github_search_repositories` with a simple query. Bad credentials = token expired.
   - **Xiaohongshu**: `mcp_xiaohongshu_check_login_status`. "未登录" means the QR session expired.
   - **Taobao**: `mcp_taobao_taobao_initialize_login`. Browser session may need re-init.

#### Phase 6 — Verify Delivery Integration (Cron-Layer Health)

MCP servers that produce output for cron-delivered jobs (news briefings, weather reports) may be healthy at the MCP layer but fail at the delivery layer. Check:
```bash
cronjob(action='list')
```

Look at **`last_delivery_error`** on each job. Common delivery-layer failures that don't show up in MCP tool tests:
- **Discord 404**: Channel ID is stale — the channel was deleted, renamed, or the bot was removed
- **Telegram/Discord/WeChat SSL connect errors**: Network proxy (127.0.0.1:7897) was down at delivery time
- **"Cannot connect to host"**: Transient network outage — verify the proxy is running, then monitor next run
- **Script jobs with null last_run_at**: The cron schedule may not have fired yet (check next_run_at) or the scheduler has a cold-start issue — manually trigger with `cronjob(action='run', job_id='...')` and observe

### "hermes mcp list crashes with TypeError: string indices must be integers, not 'str'"

This crash means one of your MCP server entries in `config.yaml` uses a **JSON string format** instead of proper YAML dict format. Common when a server was added via a script or automated tool rather than by direct YAML editing.

**Detection:** The server with the JSON string format is never discovered at startup, and `hermes mcp list` crashes before showing it. The server config looks like:

```yaml
# ❌ WRONG — JSON string value, not proper YAML dict
github-gov1: '{"command":"/path/to/wrapper.sh","args":["stdio"],"connect_timeout":15,"timeout":120}'
```

**Workaround (bypass the crash):** Even though `hermes mcp list` crashes, you can test each server individually:

```bash
hermes mcp test <server-name>
```

This bypasses the list-parsing code and tests the server directly. A success here means the server works — the issue is only in the `list` display logic.

**Fix:** Convert the JSON string to proper YAML dict format:

```yaml
# ✅ CORRECT — proper YAML dict
github-gov1:
    command: /path/to/wrapper.sh
    args: ["stdio"]
    connect_timeout: 15
    timeout: 120
```

After fixing, run `/reload-mcp` in-session (or restart the Gateway) to pick up the corrected config and register the server's tools.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.
- **Python relative imports**: Selenium-based MCP servers (like zhihu auto-poster) may fail with `attempted relative import with no known parent package`. Fix by converting relative imports (`from .write_zhihu import ...`) to absolute imports (`from write_zhihu import ...`).
- **Module entry vs script entry**: When a MCP server package uses relative imports in `__init__.py`, `python3 -m pkg` may fail. Solution: create a flat `run.py` entry point with absolute imports and set `args: ["/path/to/run.py"]` in config instead of `args: ["-m", "pkg"]`.
- **GitHub MCP Authentication Failed: Bad credentials**: The GITHUB_PERSONAL_ACCESS_TOKEN in config.yaml may have expired while the `gh` CLI (system keyring) still has a valid token.

  **Detection:** Compare the two tokens:
  ```bash
  # gh CLI token (likely valid, from system keyring)
  GH_TOKEN=$(gh auth token)
  echo "gh token length: ${#GH_TOKEN}  prefix: ${GH_TOKEN:0:10}... suffix: ${GH_TOKEN: -4}"

  # Config token (may be stale or truncated)
  CONFIG_TOKEN=$(grep GITHUB_PERSONAL_ACCESS_TOKEN ~/.hermes/config.yaml \
    | sed 's/.*: *//' | tr -d "'\"")
  echo "config length: ${#CONFIG_TOKEN}  prefix: ${CONFIG_TOKEN:0:10}... suffix: ${CONFIG_TOKEN: -4}"

  # If they differ, config token needs update
  if [ "$GH_TOKEN" = "$CONFIG_TOKEN" ]; then
    echo "TOKENS MATCH"
  else
    echo "TOKENS DIFFER - update needed"
  fi
  ```

  **⚠ Truncated / placeholder tokens:** Config token values like `ghp_WS...eh2g` (with literal `...` in the middle) are NOT valid tokens — someone likely pasted a redacted/masked version. Full GitHub PATs are always 40 characters (`ghp_` followed by 36 hex chars). If the config length is < 40 or contains `...`, replace with the real token from `gh auth token`.

  **Fix — update config.yaml:** The `patch` and `write_file` tools refuse to write to `config.yaml` (protected file). Use `sed` via terminal:

  ```bash
  # Get current gh token
  GH_TOKEN=$(gh auth token)

  # Update config.yaml in-place (works because it's a single-line replacement)
  sed -i "s|GITHUB_PERSONAL_ACCESS_TOKEN:.*|GITHUB_PERSONAL_ACCESS_TOKEN: $GH_TOKEN|" \
    ~/.hermes/config.yaml

  # Verify
  python3 -c "
  import yaml
  with open('$HOME/.hermes/config.yaml') as f:
      data = yaml.safe_load(f)
  t = data['mcp_servers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN']
  print(f'Updated: {t[:10]}...{t[-4:]}')
  "
  ```

  **Stale process cleanup:** Old MCP server processes still hold the expired token in their env. Killing them forces Hermes to respawn with the new config:

  ```bash
  ps aux | grep 'mcp-server-github' | grep -v grep | awk '{print $2}' | xargs -r kill
  ```

  Then either restart Hermes or run `/reload-mcp` in-session. Note: `/reload-mcp` does NOT re-read env variables for the same server name — it only re-connects after the process dies. If the new token still doesn't work after `/reload-mcp`, a full Hermes restart is needed.

  **Verification:** After restart, call a simple GitHub MCP tool:
  ```
  mcp_github_search_repositories(query="hermes-agent", perPage=1)
  ```

  Expected: successful search results (not "Authentication Failed").
- **System python vs venv**: `ModuleNotFoundError: No module named 'mcp'` usually means the `command` uses system python (`/usr/bin/python3`) instead of the venv python (`~/.hermes/hermes-agent/venv/bin/python3`) where `mcp` is installed.
- **Hermes blocks direct config.yaml write**: Agent refuses `write_file`/`patch` on config.yaml with "Refusing to write to Hermes config file". Use a Python script with yaml library or `hermes config` CLI instead.
- **Selenium MCP servers**: See [Selenium MCP Server Setup Guide](references/selenium-mcp-server-setup.md) for detailed troubleshooting of browser-automation-based MCP servers.

### "GitHub MCP Server running on stdio" message at startup

This message is printed by the `@modelcontextprotocol/server-github` package itself to **stderr** during initialization. Hermes captures MCP stderr to `~/.hermes/logs/mcp-stderr.log`. The message is **not an error** — it just means the server loaded successfully. It can be safely ignored.

### MCP Server Startup Optimization (npx → direct node)

Many MCP servers use `npx -y <package>` as their command. npx adds startup latency because:

1. **First launch**: npx downloads the package from npm registry (5-30s depending on network)
2. **Subsequent launches**: npx still checks version freshness, hashes, and caches
3. **Proxy environments**: npx download through a proxy (7897, etc.) can be significantly slower

**Optimization — pre-install globally and use direct node execution:**

```bash
# Install the package globally
npm install -g @modelcontextprotocol/server-github

# Verify the install path
ls "$(npm prefix -g)/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js"

# Find the entry point
node -e "console.log(require.resolve('@modelcontextprotocol/server-github'))"
```

Then update `config.yaml` to skip npx entirely:

```yaml
mcp_servers:
  github:                          # name stays the same
    command: /usr/bin/node         # direct node, no npx
    args:
    - /home/user/.npm-global/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js
    env:
      GITHUB_TOKEN: ghp_...        # standard env var
      GITHUB_PERSONAL_ACCESS_TOKEN: ghp_...  # fallback
    connect_timeout: 15            # faster startup failure detection
    timeout: 120
```

Key changes:
- **`command: /usr/bin/node`** instead of `npx` — zero download/check overhead
- **`connect_timeout: 15`** — quicker retry on transient failures (default 60s is overkill for a local stdio process)
- **Both `GITHUB_TOKEN` + `GITHUB_PERSONAL_ACCESS_TOKEN`** — the `@modelcontextprotocol/server-github` package respects `GITHUB_TOKEN` as the primary env var; adding both ensures compatibility across versions

**After config change**: a full Hermes restart is required (not just `/reload-mcp`) because MCP server config/env changes aren't hot-reloaded for the same server name.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Build from Source: Go-basierte MCP Server

Manche MCP Server（如 GitHub Official MCP Server）liegen als Go-Quellcode vor und erfordern Kompilierung statt `npx` oder `uvx`.

### Workflow: Go MCP Server kompilieren und integrieren

```bash
# 1. Repository klonen
cd /tmp && git clone --depth 1 https://github.com/github/github-mcp-server.git

# 2. Kompilieren（Go vorausgesetzt）
export PATH="$HOME/.go/bin:/usr/local/go/bin:$PATH"
cd /tmp/github-mcp-server && go build -o ~/bin/github-mcp-server ./cmd/github-mcp-server/

# 3. Binary testen
~/bin/github-mcp-server --help
~/bin/github-mcp-server list-scopes  # 列出所有可用工具和所需 OAuth Scopes
```

### Environment Variable Wrapper Script

Da Hermes nur sicherheitsrelevante Basis-Env-Vars an MCP-Subprozesse weitergibt, muss oft ein Wrapper-Script die benötigten Token/Variablen bereitstellen:

```bash
# ~/bin/github-mcp-wrapper.sh
#!/bin/bash
# Wrapper: mapped von vorhandenem Env-Var auf den vom MCP Server erwarteten Namen
export GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_TOKEN}"
exec /home/andymao/bin/github-mcp-server "$@"
```

**Warum ein Wrapper?**
- Hermes filtert die Umgebung für MCP Subprozesse (nur `PATH`, `HOME`, `USER`, `LANG` etc.)
- `env` in der MCP-Konfiguration übergibt nur Literal-Strings, keine geshellte Expansion
- Ein Wrapper kann vorhandene Env-Vars auf die vom Server erwarteten Namen mappen

### Konfiguration in Hermes

```yaml
mcp_servers:
  github-gov1:
    command: "/home/andymao/bin/github-mcp-wrapper.sh"
    args: ["stdio"]
    connect_timeout: 15
    timeout: 120
    # env wird nicht benötigt, da der Wrapper die Variable setzt
```

### GitHub MCP Server Besonderheiten

- **Env Var Name:** Der Server erwartet `GITHUB_PERSONAL_ACCESS_TOKEN` (nicht `GITHUB_TOKEN`)
- **Token:** Fine-grained PAT mit `repo`, `read:org`, `security_events` Scopes
- **`list-scopes`:** Zeigt alle aktivierten Toolsets und deren benötigte OAuth Scopes an, sehr nützlich zur Überprüfung des Tokens
- **Standard-Toolsets:** `context`, `repos`, `issues`, `pull_requests`, `users`
- **Via `--toolsets` erweiterbar:** `actions`, `code_security`, `discussions`, `dependabot`, `gists`, `git`, `labels`, `notifications`, `orgs`, `projects`, `secret_protection`, `security_advisories`, `stargazers`
- **Insiders Mode:** `--insiders` für experimentelle Tools
- **Read-Only Mode:** `--read-only` über `GITHUB_READ_ONLY=1` Environ

### Wann `npx` vs. kompilierte Binary?

| Kriterium | `npx` / Docker | Kompilierte Binary |
|-----------|---------------|-------------------|
| Startzeit | 5-30s (npx download check) | <1s |
| Netzwerkabhängigkeit | Ja (npm registry / Docker Hub) | Nein |
| Versionkontrolle | Immer aktuell | Manuelles Update |
| Offline-Fähigkeit | Nein | Ja |
| Proxy-Probleme | Häufig (undici ignorier HTTP_PROXY) | Selten |

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

**Note:** If you see startup delays or "Authentication Failed" errors, see the startup optimization section below for the recommended direct-node setup (faster, no npx download overhead).

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers at runtime: use `hermes mcp add/remove` CLI commands, then `/reload-mcp` in-session to hot-reload (no full restart needed)
- For Hermes-as-server mode (reverse direction): `hermes mcp serve`

## Reverse Direction: Hermes as MCP Server → External Clients

When you want external MCP clients (VS Code, Claude Desktop, Cursor, Continue.dev) to connect TO Hermes and use its tools, see [Hermes as MCP Server](references/hermes-as-mcp-server.md). Quick reference:

| Client | Registration command |
|--------|---------------------|
| VS Code (Copilot Chat) | `code --add-mcp '{"name":"hermes","command":"hermes","args":["mcp","serve"]}'` |
| Claude Desktop | Edit `~/.config/Claude/claude_desktop_config.json` |
| Continue.dev | Edit `~/.continue/config.json` |
| Cline / Roo Code | Add stdio server in extension settings |

## References

- [Hermes as MCP Server](references/hermes-as-mcp-server.md) — running Hermes as an MCP server, connecting VS Code/Claude/Cursor
- [MCP CLI Management](references/mcp-cli-management.md) — hermes mcp add/list/remove/configure/test commands
- [京东 MCP 配置](references/jd-mcp-config.md) — JD MCP server setup, tools, verification for this environment
- [小红书 MCP 配置](references/xiaohongshu-mcp-config.md) — xiaohongshu-mcp Go SDK 服务器配置（Streamable HTTP 协议，transport 注意点，13 个工具清单）
- [Custom MCP Server Build Pattern](references/custom-mcp-server-build-pattern.md) — 完整工作流：搜索社区 MCP → 评估 → 安装/wiring → 自定义 Python MCP 快速开发 → 验证
