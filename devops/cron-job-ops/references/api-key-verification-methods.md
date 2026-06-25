# API Key Verification Methods

When verifying API keys from shell or Python, the naive `curl` + shell approach has pitfalls with keys containing special characters.

## Method 1: Direct curl with env var (works for most keys)

```bash
curl -s --connect-timeout 10 \
  -X POST "https://api.deepseek.com/v1/chat/completions" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
```

**Pitfall:** If the key contains hex characters, `$`, `!`, or other shell-special chars, this may fail silently.

## Method 2: Python `subprocess.run()` with command list (preferred)

Avoids shell escaping entirely by passing arguments as a list:

```python
import subprocess, json

# For services behind proxy:
proxy = ["-x", "http://127.0.0.1:7897"]

cmd = ["curl", "-s", "--connect-timeout", "10"] + proxy + [
    "-X", "POST",
    "https://api.siliconflow.com/v1/chat/completions",
    "-H", "Authorization: Bearer " + api_key,
    "-H", "Content-Type: application/json",
    "-d", '{"model":"Qwen/Qwen3.6-35B-A3B","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
]

r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
d = json.loads(r.stdout)

if "choices" in d:
    print(f"✅ Valid: {d['choices'][0]['message']['content'][:100]}")
elif "error" in d:
    print(f"❌ {d['error'].get('message','?')}")
```

## Method 3: `execute_code` with hermes_tools (Hermes environment)

```python
from hermes_tools import terminal
import json

r = terminal(
    command=f'curl -s --connect-timeout 10 -X POST "https://api.deepseek.com/v1/chat/completions" -H "Authorization: Bearer YOUR_KEY" -H "Content-Type: application/json" -d \'{{"model":"deepseek-chat","messages":[{{"role":"user","content":"ping"}}],"max_tokens":5}}\'',
    timeout=15
)
```

**Known issue:** The `execute_code` tool passes the command string through multiple shell layers. Python curly braces `{}` must be doubled (`{{}}`). For keys with special characters, subprocess.run() inside the tool may still fail.

## Method 4: Python with urllib (no subprocess)

Use `urllib.request` for maximum control:

```python
import json, urllib.request

data = json.dumps({
    "model": "Qwen/Qwen3.6-35B-A3B",
    "messages": [{"role": "user", "content": "ping"}],
    "max_tokens": 50
}).encode()

proxy_handler = urllib.request.ProxyHandler({
    "https": "http://127.0.0.1:7897",
    "http": "http://127.0.0.1:7897"
})
opener = urllib.request.build_opener(proxy_handler)
req = urllib.request.Request(
    "https://api.siliconflow.com/v1/chat/completions",
    data=data,
    headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    },
    method="POST"
)
resp = opener.open(req, timeout=15)
result = json.loads(resp.read())
```

This avoids ALL shell escaping issues. The trade-off: cannot be used inside `execute_code` (which has its own limitations); must run via `terminal()` with `python3 << 'PYEOF'` heredoc.

## Which Method When

| Method | Best For | Avoid When |
|--------|----------|------------|
| Direct curl (Method 1) | Quick ad-hoc test, key has no special chars | Key has `$`, `!`, hex chars, or in `execute_code` |
| subprocess.run (Method 2) | Most reliable overall | Cannot use in `execute_code` (no subprocess) |
| execute_code (Method 3) | Testing within Hermes session | Keys with special chars, complex JSON payloads |
| Python urllib (Method 4) | Programmatic, needs proxy, key has special chars | Requires heredoc wrapper in terminal() |

## Verifying `config.yaml` vs Runtime Keys

config.yaml may contain:
- **Full API keys**: `sk-ybh...etvn` (where `...` is literally in the key — length 51+)
- **Truncated placeholders**: `sk-6f1...7887` (length 13 — clearly truncated)

Hermes credential pool stores keys from multiple sources:
- `env:DEEPSEEK_API_KEY` — from `.env` file
- `config:siliconflow` — from `providers.siliconflow.api_key` in config.yaml
- `config:deepseek` — from `providers.deepseek.api_key` in config.yaml

The credential pool entries are loaded lazily at runtime — `auth.json` shows the metadata but not the actual keys.
