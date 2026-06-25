# `.env` File Sourcing Pitfalls

## Problem

`source ~/.hermes/.env` can fail silently when any line contains unquoted special characters. This causes ALL downstream commands that depend on those env vars to fail with no obvious error message.

## Common Culprits

| Variable | Typical Malformed Value | Characters That Break `source` |
|----------|------------------------|-------------------------------|
| `WHATSAPP_ALLOWED_USERS` | `+!^)#%%&#%$^` | `!`, `)`, `#`, `^`, `%` |
| Any password/token | `abc!def#123` | `!`, `#` in unquoted context |

## Diagnosis

```bash
bash -c 'source ~/.hermes/.env 2>&1; echo "EXIT=$?"'
```

Expected (healthy): no error output, `EXIT=0`.  
Unhealthy: shows line number + "unexpected token" error, `EXIT=2`.

## Root Cause

The `.env` file is a bash script, not a key-value store. When `source` runs it, bash parses each line as shell code. Special characters like `!` (history expansion), `)`, `#` (comment start), and `%` are evaluated, not treated as literal data.

The correct fix is to quote values containing special characters:
```bash
WHATSAPP_ALLOWED_USERS='+!^)#%%&#%$^'
```

But `write_file`/`patch` may not be able to modify the `.env` file directly (Hermes credential store protection), so the workaround is to use grep.

## Workaround: `grep` Instead of `source`

Instead of sourcing the entire file, extract only the variables you need:

```bash
# Safe extraction — grep returns raw strings, no shell parsing
FEISHU_APP_ID=$(grep "^FEISHU_APP_ID=" ~/.hermes/.env | head -1 | cut -d= -f2-)
FEISHU_APP_SECRET=*** "^FEISHU_APP_SECRET=*** ~/.hermes/.env | head -1 | cut -d= -f2-)

# Export for subprocesses
export FEISHU_APP_ID FEISHU_APP_SECRET

# Now use them
python3 /tmp/my_script.py
```

### Multiple Vars in One Script (Pattern)

```bash
#!/bin/bash
# Extract only the vars this script needs
for var in FEISHU_APP_ID FEISHU_APP_SECRET FEISHU_HOME_CHANNEL; do
    val=$(grep "^${var}=" ~/.hermes/.env | head -1 | cut -d= -f2-)
    [ -n "$val" ] && export "$var=$val"
done

# Proceed with normal logic
python3 /tmp/send_message.py
```

### Python Equivalent

```python
import os, subprocess

def get_env(key):
    """Safely extract a single env var from ~/.hermes/.env"""
    result = subprocess.run(
        ["grep", f"^{key}=", os.path.expanduser("~/.hermes/.env")],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode == 0 and result.stdout:
        return result.stdout.strip().split("=", 1)[1]
    return None

os.environ["FEISHU_APP_ID"] = get_env("FEISHU_APP_ID") or ""
os.environ["FEISHU_APP_SECRET"] = get_env("FEISHU_APP_SECRET") or ""
```

## Prevention Tips

- Test `.env` syntax after any manual edit: `bash -c 'source ~/.hermes/.env' 2>&1`
- If a new variable contains user-generated content (e.g., allowed users list), wrap the value in single quotes
- For cron job scripts, prefer grep extraction over `source` — it's immune to syntax errors on unrelated lines
- The `.env` file is NOT a safe place for arbitrary strings — it's a bash source file, so values must follow bash quoting rules
