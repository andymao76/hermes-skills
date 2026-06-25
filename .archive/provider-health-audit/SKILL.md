---
name: provider-health-audit
description: Audit all configured LLM API providers — test keys, measure latency, diagnose failures, detect credential corruption.
category: devops
tags: [api-key, provider, latency, health-check, credential, troubleshooting]
---

# Provider Health Audit

## Trigger Conditions

Load this when the user asks to:
- Check all API keys / provider status / which keys work
- Test latency of providers
- Diagnose why a provider is failing (401, 429, 503, timeout)
- "Audit my API keys", "check keys", "why is X not working"
- Investigate credential corruption or key truncation

## When to Run

- User reports a provider suddenly failing
- After config changes that touched `providers:` section
- After Hermes upgrades that might affect credential handling
- Periodic maintenance (the `redact_secrets` feature can obscure key display)

## Key Length Reference Table

Use these to detect truncated/corrupted keys:

| Provider | Expected Length | Provider Prefix |
|----------|----------------|-----------------|
| DeepSeek | 28-50 chars | `sk-` |
| OpenRouter | 40-70 chars | `sk-or-v1-` |
| SiliconFlow (国际/国内) | 40-55 chars | `sk-` |
| 阿里百炼 (Bailian/DashScope) | 30-40 chars | `sk-` |
| Gemini | 35-42 chars | `AIzaSy` |

A key significantly shorter than the expected range is **truncated** — the user must re-paste from the provider dashboard. The truncation is irreversible (it was written to disk as-is).

## Audit Approach

### 1. Discover Configured Providers

Read all providers from `~/.hermes/config.yaml`:

```python
import yaml
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    cfg = yaml.safe_load(f)
providers = cfg.get('providers', {})
```

Key fields: `api_key` (or `api_key_env` for env-var-sourced), `base_url`, `model`.

### 2. Test Each Provider

For each provider, POST to `{base_url}/chat/completions`:

```python
payload = {
    "model": model_name,
    "messages": [{"role": "user", "content": "回复一个字：好"}],
    "max_tokens": 10,
    "temperature": 0.1,
}
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
resp = requests.post(url, json=payload, headers=headers, timeout=30, proxies=proxy_if_needed)
```

### 3. Common Error Patterns

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 200 | OK | Record latency |
| 401 | **API key invalid** | Key may be corrupted/truncated in config |
| 402 | Payment required | Account balance depleted |
| 429 | Rate limit / quota exceeded | Check plan or wait |
| 503 | Service overloaded | Retry with different model |
| Timeout | Network blocked (no proxy) | Add proxy or use domestic endpoint |
| ConnectionError | Firewall/DNS | Check proxy or try alternative endpoint |

### 4. Detect Credential Corruption (Critical Step)

**Hermes `redact_secrets: true`** can obscure key display. The actual file content may be fine even when diagnostics show `***` or truncated keys.

**How config.yaml keys get corrupted**: The `api_key` field in config.yaml can be truncated (e.g., `sk-6f1...7887` showing only 13 chars when real key is 30+). This happens when a previous tool write or `patch` operation truncated the value.

**Audit procedure for corruption**:
1. Read key from config.yaml via Python `yaml.safe_load` — note the actual length
2. Check `~/.hermes/.env` for the same key via environment variable — these are often preserved
3. Compare `api_key` in config.yaml vs the env-var-sourced key (if `api_key_env` is set)
4. A normal API key length: DeepSeek/OpenRouter keys are ~30-60 chars. SiliconFlow keys ~51 chars. Bailian keys ~35 chars. If the config key is significantly shorter, it's corrupted.

**To fix a corrupted key**: The user must manually re-copy the full key from the provider's website into `~/.hermes/config.yaml`. There is no way to recover a truncated key from the system.

### 5. Test Proxy Sensitivity

For providers behind the Great Firewall (Gemini, OpenRouter, SiliconFlow international), test **both** with and without proxy:
- Proxy: `HTTPS_PROXY=http://127.0.0.1:7897`
- Direct: no proxy

Results matrix: some providers work **only** with proxy (Gemini), some work both ways but faster direct (SiliconFlow domestic), some need proxy for acceptable latency.

### 6. Reporting Format

Present results in a table:

| Provider | Status | Latency | Notes |
|----------|--------|---------|-------|
| DeepSeek | ❌ 401 | N/A | Key truncated in config (13/?? chars) |
| SiliconFlow 国际 | ✅ OK | 2659ms | Needs proxy |
| SiliconFlow 国内 | ✅ OK | 515ms | Direct, faster |
| 阿里百炼 | ✅ OK | 541ms | 212 models available |
| Gemini 2.5-flash | ✅ OK | 1299ms | Needs proxy, direct blocked |
| OpenRouter | ❌ 401 | N/A | Key corrupted |

## Key Configuration Schema Check

Before running health checks, verify each provider has a **working key resolution path**:

```python
for name, info in providers.items():
    has_direct_key = bool(info.get('api_key', ''))
    has_env_key = bool(info.get('api_key_env', ''))
    has_env_var = os.environ.get(info.get('api_key_env', '')) if has_env_key else False
    key_is_placeholder = 'PLACEHOLDER' in (info.get('api_key', '') or '')
    
    if key_is_placeholder and not has_env_var:
        print(f"❌ {name}: key is placeholder text, no env key available")
    elif not has_direct_key and has_env_key and has_env_var:
        print(f"✅ {name}: using env:{info['api_key_env']}")
    elif has_direct_key and not key_is_placeholder:
        print(f"✅ {name}: using config key")
    else:
        print(f"⚠️  {name}: check manually")
```

Common config schema bugs:
- **Placeholder key without api_key_env**: `api_key: PLACEHOLDER_OPENROUTER_KEY` but no `api_key_env` — provider appears configured but always returns 401
- **Empty key with api_key_env**: `api_key: ''` + `api_key_env: OPENROUTER_API_KEY` works correctly, but the empty string can interfere with some implementations
- **api_key_env set but env var missing**: The env var may not be exported to the shell. See "How to load .env" below.

## How to Load .env Keys in Scripts

`~/.hermes/.env` is **NOT** a shell source file — it's a simple key-value store. `os.environ.get('GEMINI_API_KEY')` returns empty unless you explicitly load it:

```python
# Parse .env in Python (reliable)
env_path = os.path.expanduser('~/.hermes/.env')
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")
```

## Pitfalls

- **Do NOT trust the `***` display** — Hermes `redact_secrets: true` makes all keys look obscured. Always check raw file content with Python `yaml.safe_load` or binary read to get actual values.
- **Environment variables from `.env` are NOT exported to shell** — `os.environ.get("GEMINI_API_KEY")` returns empty in a plain terminal. See "How to Load .env Keys in Scripts" above.
- **Gemini OpenAI 兼容模式 max_tokens 陷阱** — 设 `max_tokens ≤ 10` 会返回 HTTP 200 但 `content` 为空 (`completion_tokens: 0`)。测试时至少设 `max_tokens: 50`。
- **Gemini free tier (2.0-flash) quotas deplete fast** — 2.5-flash often works after 2.0-flash hits 429.
- **SiliconFlow domestic (api.siliconflow.cn) has separate API key from international** — they are not interchangeable.
- **OpenRouter config key 可能是占位符** — 检查 `api_key` 值是否含 `PLACEHOLDER`。如果是且没有 `api_key_env`，需添加或设置真实 key。
- **切换 model/provider 前必须测试代理环境** — 修改 model.provider 或 model.model 前，先模拟 gateway 的 NO_PROXY 环境变量测试代理路由：国内站点走直连，国外站点走代理 127.0.0.1:7897。测试未通过不能切换。这是用户强制的约束条件。
- **config.yaml 被 agent 安全锁保护** — `patch` 工具直接编辑 config.yaml 会被拒绝。必须用 `hermes config set <key> <value>` 命令修改。
- **并发测试 Gemini 容易触发 429** — free tier 频率限制严格，并发 6 路测试时 Gemini 常返回 429。对策：单测或加延时重试。
- **empty string api_key 会干扰 env 回退** — `api_key: ''` 在某些实现中被视为"有 key"（非 None），导致 env 回退不生效。留空字符串比删除字段更安全。

## References

- `references/hermes-redact-secrets.md` — How `redact_secrets` works and how to read past it
- `references/provider-proxy-matrix.md` — Which providers need proxy and typical latency, plus NO_PROXY configuration guide for systemd proxy.conf
- `references/key-corruption-detection-recipe.md` — Step-by-step recipe for detecting and diagnosing truncated/corrupted keys (used in production 2026-06-08 session)
- `references/gemini-openai-compat-quirks.md` — Gemini OpenAI 兼容模式的特殊行为：max_tokens 限制、/v1/models 不可用、空回复问题

## Reusable Scripts

### scripts/provider-audit.py

Full automated provider audit — tests all keys, measures latency, detects corruption:

```bash
python3 ~/.hermes/skills/devops/provider-health-audit/scripts/provider-audit.py
```

### scripts/daily-startup-healthcheck.sh

Daily startup health check script — run after Hermes gateway starts:

```bash
bash ~/.hermes/scripts/daily-startup-healthcheck.sh
```

Checks two things:
1. **Clash Verge proxy**: GUI process ✅, Mihomo kernel ✅, port 7897 ✅, actual proxy functionality (Google + OpenRouter) ✅, NO_PROXY env var verification ✅
2. **All 6 provider models**: Concurrent API calls to deepseek/siliconflow/siliconflow-cn/bailian/gemini/openrouter. Classifies failures as FATAL (401/402 → needs human) vs TEMP (429/502/503 → auto-recoverable)

The script is no_agent (pure shell+Python, zero token cost). Deploy as cron job at system startup + 2min.

## Daily Startup Health Check Workflow

When the user wants a daily health check or after system reboot:

### Step 1: Check Clash Verge Proxy

```bash
# GUI process
pgrep -f "clash-verge" > /dev/null && echo "GUI 运行中" || echo "GUI 未运行"

# Mihomo kernel
pgrep -f "verge-mihomo" > /dev/null && echo "内核运行中" || echo "内核未运行"

# Port listening
ss -tln 2>/dev/null | grep -q ":7897 " && echo "端口正常" || echo "端口未监听"

# Functional test
curl -s -o /dev/null -w "%{http_code}" --max-time 5 -x "http://127.0.0.1:7897" "https://www.google.com/generate_204"

# NO_PROXY verification
GATEWAY_PID=$(pgrep -f "hermes_cli.main gateway" | head -1)
cat "/proc/$GATEWAY_PID/environ" 2>/dev/null | tr '\0' '\n' | grep "^NO_PROXY="
```

Expected NO_PROXY: `localhost,127.0.0.1,::1,.local,.aliyuncs.com,.siliconflow.cn,.deepseek.com,.weixin.qq.com,.wechat.com,.xiaohongshu.com,.zhihu.com,.taobao.com,.tmall.com,.csdn.net,.baidu.com,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`

### Step 2: Health Check All Providers

Use `concurrent.futures.ThreadPoolExecutor(max_workers=6)` to test all providers in parallel. For each, POST to `{base_url}/chat/completions` with `max_tokens=50` (Gemini requires ≥50 — see gemini-openai-compat-quirks.md).

Status classification:
- **OK** (200) → normal
- **FATAL** (401/402) → key invalid or quota exhausted, human intervention needed
- **TEMP** (429/502/503/timeout) → temporary, auto-recoverable

Exit codes:
- `0` → all healthy
- `1` → warnings only (temporary issues)
- `2` → failures (needs human attention)

### Step 3: Report Format

```
============================================================
1. Clash Verge 代理检查
────────────────────────────────────────────────────────────
  [✅] Clash Verge GUI 进程运行中
  [✅] Mihomo 内核进程运行中
  [✅] 代理端口 7897 正常监听
  [✅] 代理功能测试通过（Google 返回 204）
  [✅] NO_PROXY 配置正确（含国内域名）

2. 大模型健康检查
────────────────────────────────────────────────────────────
  ✅ deepseek     deepseek-chat           OK
  ✅ siliconflow  Qwen/Qwen3.6-35B-A3B   
  ⚠️  gemini     gemini-2.5-flash        HTTP 429 (临时问题)

3. 检查汇总
────────────────────────────────────────────────────────────
  ✅ 全部项目通过 — 系统健康，所有大模型可用

