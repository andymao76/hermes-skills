# Key Corruption Detection — Step-by-Step Recipe

This is the exact procedure used in a real session (2026-06-08) to detect and diagnose API key corruption in Hermes config.

## The Problem

User asked "check all API keys". Standard read showed:
- DeepSeek key: `sk-6f1...7887` (13 chars) 
- OpenRouter key: `***...e8a5` (20 chars, starts with `***`)
- .env values showed as `***`

## Investigation Steps

### Step 1: Read config with Python and check key length

```python
import yaml
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)

for name in ['deepseek', 'openrouter', 'siliconflow', 'bailian']:
    key = cfg['providers'][name].get('api_key', '')
    print(f"{name}: len={len(key)}")
```

**Signal**: DeepSeek showed 13 chars — way too short (expected 28-50).

### Step 2: Distinguish `redact_secrets` display vs actual truncation

The `***` in .env files is Hermes `redact_secrets: true` display-only masking. The real file may be fine:

```python
with open(os.path.expanduser('~/.hermes/.env'), 'rb') as f:
    data = f.read()

# Find all occurrences of a key
target = b'GEMINI_API_KEY=*** = data.find(target)
eol = data.find(b'\n', idx)
val = data[idx+len(target):eol].decode('ascii', errors='replace').strip()
print(f"Actual length: {len(val)}")  # If this is < expected, key is truly truncated
```

### Step 3: Binary hex verification

When in doubt check the raw bytes:

```bash
python3 -c "
with open('~/.hermes/.env', 'rb') as f:
    data = f.read()
idx = data.find(b'DASHSCOPE_API_KEY=*** = data.find(b'DASHSCOPE_API_KEY=*** idx + 1)
# idx is the SECOND occurrence
eol = data.find(b'\n', idx)
line = data[idx:eol]
key = line.split(b'=')[1]
print(f'hex: {key.hex()}')
print(f'ascii: {key.decode()}')
print(f'len: {len(key)}')
"
```

**Key insight from real debugging**: Even with `redact_secrets: true`, `.env` files preserved the full key while `config.yaml` had truncated ones. This is because `hermes config set` operations can overwrite `config.yaml` values with display-obscured strings during a bad write.

### Step 4: Check if config.yaml key vs env variable key differ

```python
# Check config.yaml key
cfg_key = cfg['providers']['bailian'].get('api_key', '')

# Check .env key 
env_file = os.path.expanduser('~/.hermes/.env')
with open(env_file, 'rb') as f:
    data = f.read()
idx = data.find(b'DASHSCOPE_API_KEY=*** idx >= 0:
    eol = data.find(b'\n', idx)
    env_key = data[idx+18:eol].decode().strip()

print(f"Config key length: {len(cfg_key)}")
print(f"Env key length: {len(env_key)}")
print(f"Same: {cfg_key == env_key}")
```

## Root Cause Identification

If the key in `.env` is full length but `config.yaml` has the truncated version:
- **Cause**: A previous `hermes config set providers.xxx.api_key "truncated_value"` or `patch` overwrote config.yaml
- **Fix**: Use `hermes config set providers.xxx.api_key "FULL_KEY_HERE"` with the full key

If **both** are truncated (extremely rare):
- **Cause**: The key was never fully stored or was explicitly overwritten
- **Fix**: User must re-copy from provider dashboard

## Repair Procedure

```bash
# For DeepSeek:
hermes config set providers.deepseek.api_key "sk-actual_full_key_here"

# For OpenRouter:
hermes config set providers.openrouter.api_key "sk-or-v1-actual_full_key_here"
```

After repair, verify by running the audit script:
```bash
python3 ~/.hermes/skills/devops/provider-health-audit/scripts/provider-audit.py
```

## What Was Learned

- **Gemini 2.5-flash** returns 200 OK but sometimes with empty `content` field. This is normal behavior—not a failure.
- **Gemini direct connect** (no proxy) gets ConnectionError (blocked by GFW). Always test with proxy.
- **SiliconFlow 国内站** (515ms) is faster than international (2659ms) because it avoids proxy routing.
- **阿里百炼 (Bailian)** has 212 models available and all tested models (qwen-plus, qwen-turbo, qwen-max) work.
- **Aliyun DashScope international endpoint** (`dashscope-intl.aliyuncs.com`) returns 401 with Bailian API key — only the domestic endpoint works with domestic keys.
