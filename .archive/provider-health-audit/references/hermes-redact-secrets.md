# Hermes `redact_secrets` Behavior

## What It Does

When `security.redact_secrets: true` in `~/.hermes/config.yaml` (default), Hermes obscures API keys and credentials when **displaying them in conversation**. This affects:
- `read_file` tool output (config.yaml, .env)
- Terminal output that matches key patterns
- `search_files` that matches credential patterns

## What It Does NOT Do

- It does NOT modify the actual file content on disk
- It does NOT prevent the credential from being used — internal providers read the real value
- The real key is still on disk; only the **display** is obscured

## How to Read Past the Obscuring

### Method 1: Python yaml.safe_load (config.yaml)

```python
import yaml
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)
key = cfg['providers']['deepseek']['api_key']
print(f"Key length: {len(key)}")  # Real length, not obscured chars
```

This works because `yaml.safe_load` reads the real file content. The key appears as-is.

### Method 2: Binary read of `.env`

```python
with open(os.path.expanduser('~/.hermes/.env'), 'rb') as f:
    data = f.read()
idx = data.find(b'GEMINI_API_KEY=*** idx >= 0:
    eol = data.find(b'\n', idx)
    val = data[idx+16:eol].decode('ascii').strip()
```

### Method 3: Shell copy + inspect

```bash
# Copy to temp file bypasses redact
cp ~/.hermes/.env /tmp/check.env
# Then read /tmp/check.env
```

## The Redact-Interferes-with-Diagnostics Trap

When you try to diagnose "why is provider X failing", `redact_secrets` can show:
- `***` for the whole key value (in .env display)
- Truncated key like `sk-6f1...7887` (in config.yaml display)
- This **looks** like the key is corrupted, but it may be intact

**The real file on disk** may contain the full key. Always verify with binary/hex inspection before concluding the key is damaged.

## When Keys Are Actually Corrupted

`redact_secrets` config.yaml obscuring is **read-only**. Key truncation in `config.yaml` (like `sk-6f1...7887` instead of `sk-6f1...7887...restofactualkey`) is NOT caused by `redact_secrets` — it's a **write-side bug** where a previous `patch` or `hermes config set` command wrote a shortened value.

.env keys are more resilient to this because they use `KEY=VALUE` format without YAML syntax issues.

## Corrupted Key Recovery

If a key in config.yaml is genuinely truncated:
1. Check ~/.hermes/.env for the same key via env var (KEY=FULL_VALUE)
2. If both are damaged, the user must re-copy from the provider dashboard
3. There is no backup/undo — Hermes doesn't version-control credential changes
