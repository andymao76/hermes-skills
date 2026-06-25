# SiliconFlow Provider Notes

## Vendor-Prefixed Model Names

SiliconFlow uses vendor-prefixed model slugs in their API, following the pattern:

```
<vendor>/<model-name>
```

Examples:
- `Qwen/Qwen3.5-397B-A17B`
- `deepseek-ai/DeepSeek-V3`
- `THUDM/glm-4-9b-chat`
- `01-ai/Yi-34B-Chat`

This is the **same format** that OpenRouter uses to route to different providers. However, when using SiliconFlow directly (not via OpenRouter), this is the correct and expected format.

## Configuration

```yaml
model:
  provider: siliconflow
  default: Qwen/Qwen3.5-397B-A17B
  base_url: https://api.siliconflow.com/v1
  api_key: ${SILICONFLOW_API_KEY}
```

## Herms Doctor Warning

Running `hermes doctor` may show this warning:

```
⚠ model.default 'Qwen/Qwen3.5-397B-A17B' uses a vendor/model slug but provider is 'siliconflow' 
  (vendor-prefixed slugs belong to aggregators like openrouter)
```

**This warning is a false positive for SiliconFlow.** The heuristic was designed to catch users who mistakenly set `provider: openrouter` but forgot the vendor prefix, or set `provider: anthropic` with a `anthropic/claude-sonnet-4` style slug. It does not account for providers that legitimately use vendor-prefixed names.

### How to Verify Your Configuration Works

```bash
# Check API connectivity
curl -s -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  https://api.siliconflow.com/v1/models | jq

# Test chat completion
curl -s -X POST https://api.siliconflow.com/v1/chat/completions \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.5-397B-A17B",
    "messages": [{"role": "user", "content": "Hello"}]
  }' | jq '.choices[0].message.content'
```

If the API returns a valid response, your configuration is correct regardless of the warning.

## Image Generation

SiliconFlow also offers image generation via an OpenAI-compatible endpoint:

```bash
curl -s -X POST https://api.siliconflow.com/v1/images/generations \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "black-forest-labs/FLUX.1-schnell",
    "prompt": "a cat on a desk",
    "size": "1024x1024"
  }' | jq '.data[0].url'
```

See `scripts/siliconflow-image.py` for a Python wrapper.

## Rate Limits

As of 2026, SiliconFlow free tier:
- ~10-20 requests/minute depending on model
- No hard daily limit, but fair usage applies

Check current limits at: https://cloud.siliconflow.com/pricing

## Popular Models (2026)

### Flagship Models (Highest Performance)

| Model ID | Parameters | Context | Price (In/Out) | Best For |
|----------|------------|---------|----------------|----------|
| `Pro/deepseek-ai/DeepSeek-V4-Pro` | 1.6T/49B | 1M tokens | $1.60/$3.48 | Complex reasoning, full codebase analysis |
| `Pro/moonshotai/Kimi-K2.6` | 1T/32B | 256K tokens | $0.90/$4.00 | Long-horizon coding, AI agents, UI generation |
| `Pro/Z-ai/GLM-5.1` | 754B | Ultra-long | $0.90/$4.00 | Agent engineering, repo-level code gen |
| `Qwen/Qwen3.6-35B-A3B` | 35B/3B | 262K tokens | $0.20/$1.60 | Multimodal, best value MoE |

### Best Value (Daily Use Recommended ⭐)

| Model ID | Context | Price (In/Out) | Use Case |
|----------|---------|----------------|----------|
| `deepseek-ai/DeepSeek-V4-Flash` | 1M tokens | **$0.13/$0.28** | Daily coding assistant, chat, agents |
| `Qwen/Qwen3.6-27B` | 262K tokens | $0.30/$3.20 | Frontend dev, multi-step problem solving |
| `Qwen/Qwen3.5-397B-A17B` | 262K+ | $0.20/$1.60 | Complex reasoning, high-intensity tasks |
| `tencent/Hy3-preview` | 262K tokens | **$0.066/$0.26** | Production agents, lowest cost |

### Free Models (Testing/Learning)

| Model ID | Context | Notes |
|----------|---------|-------|
| `Qwen/Qwen1.5-7B-Chat` | 32K | Free, rate-limited |
| `internlm/internlm2_5-7b-chat` | 32K | Free, Shanghai AI Lab |
| `mistralai/Mistral-7B-Instruct-v0.2` | 32K | Free, 7B small model |
| `THUDM/glm-4-9b-chat` | 32K | Free, Zhipu AI |
| `THUDM/chatglm3-6b` | 32K | Free, ChatGLM3 |

### Llama Series

| Model ID | Parameters | Notes |
|----------|------------|-------|
| `meta-llama/Llama-3.1-405B-Instruct` | 405B | Meta's strongest instruction model |
| `meta-llama/Llama-3.3-70B-Instruct` | 70B | Lightweight, good value |

## Model Selection Guide

**By Use Case:**
- 📝 **Daily chat/coding**: `DeepSeek-V4-Flash` (best value)
- 🔍 **Complex reasoning/research**: `DeepSeek-V4-Pro` or `GLM-5.1`
- 💻 **Code development**: `Kimi-K2.6` (agent-optimized) or `Qwen3.6-27B`
- 💰 **Budget sensitive**: `Hy3-preview` (Tencent, cheapest) or `DeepSeek-V4-Flash`
- 🧪 **Testing/learning**: Free 7B models (rate-limited)

**By Budget:**
- Free: 7B-class models (rate-limited)
- Ultra-low: `Hy3-preview` ($0.066/M) or `DeepSeek-V4-Flash` ($0.13/M)
- Balanced: `Qwen3.6-35B-A3B` ($0.20/M)
- No-compromise: `DeepSeek-V4-Pro` or `GLM-5.1`

## Changing Models

Use the interactive CLI:
```bash
hermes model
```

Or edit config.yaml directly:
```yaml
model:
  default: deepseek-ai/DeepSeek-V4-Flash  # Change this line
  provider: siliconflow
  base_url: https://api.siliconflow.com/v1
```

Then start a new session (`/reset` or restart Hermes) for changes to take effect.

## Proxy Requirements

SiliconFlow **international API** (`api.siliconflow.com`) may be blocked in some regions (e.g., mainland China). If you experience connection timeouts:

1. Configure a proxy in your systemd gateway service or environment:
   ```bash
   export HTTPS_PROXY=http://127.0.0.1:7897
   ```

2. For gateway service, add to `~/.config/systemd/user/hermes-gateway.service`:
   ```ini
   Environment="HTTPS_PROXY=http://127.0.0.1:7897"
   Environment="HTTP_PROXY=http://127.0.0.1:7897"
   ```

3. Restart: `systemctl --user daemon-reload && systemctl --user restart hermes-gateway`

## Domestic Station (中国) vs International Station

SiliconFlow operates **two separate endpoints** with significant performance differences:

| Aspect | Domestic (.cn) | International (.com) |
|--------|----------------|---------------------|
| **API Endpoint** | `https://api.siliconflow.cn/v1` | `https://api.siliconflow.com/v1` |
| **Latency** | ~100ms ⚡ | ~1000ms+ 🐢 (10x slower) |
| **Network** | Direct connection (China) | Requires proxy/VPN |
| **Currency** | CNY (¥) | USD ($) |
| **Free Tier** | ¥14 (~20M tokens) | $1 USD |
| **Payment** | WeChat/Alipay/Bank transfer | Credit Card/PayPal |
| **Invoice** | VAT special invoice ✅ | Not available |
| **Models** | 93 models (incl. DeepSeek V4 Pro, Qwen3.6) | Full catalog (~60+ models) |
| **Separate Key** | Yes — independent SK from cloud.siliconflow.cn | Yes — independent SK from cloud.siliconflow.com |

### Latency实测 (2026-06-08)

```bash
# Domestic station
curl -s -o /dev/null -w "DOM: %{time_total}s\n" https://api.siliconflow.cn/v1/models
# Result: 0.09s

# International station (via proxy)
curl -s -o /dev/null -w "INTL: %{time_total}s\n" --proxy http://127.0.0.1:7897 https://api.siliconflow.com/v1/models
# Result: 1.02s
```

**Speed difference: ~11x**

### Recommendation

**Use domestic station (`.cn`) if:**
- ✅ You are located in mainland China
- ✅ You want 10x faster response times
- ✅ You need Chinese invoices for reimbursement
- ✅ You prefer CNY pricing and WeChat/Alipay payment

**Use international station (`.com`) only if:**
- You need models exclusive to international catalog
- You already have significant USD balance
- You require USD payment/international invoices

### Switching to Domestic Station

```bash
# Method 1: Override existing provider URL (requires same SK for both stations)
hermes config set providers.siliconflow.base_url https://api.siliconflow.cn/v1

# Method 2 (Recommended): Add as separate provider entry in config.yaml
# This allows switching without losing international station config:
#   providers:
#     siliconflow-cn:
#       api_key: sk-xxx
#       base_url: https://api.siliconflow.cn/v1
#       default: Qwen/Qwen3.6-35B-A3B
# Then switch model.provider to siliconflow-cn
hermes config set model.provider siliconflow-cn
hermes config set model.default Qwen/Qwen3.6-35B-A3B
hermes config set model.base_url https://api.siliconflow.cn/v1

# Verify
hermes chat -q "用中文一句话介绍你是谁" -Q
```

Get domestic API Key from: https://cloud.siliconflow.cn/

### Testing Domestic APIs from execute_code (Proxy Pitfall)

When testing `api.siliconflow.cn` from Python's `urllib` inside `execute_code`, the function **inherits the shell's proxy environment variables** (`HTTP_PROXY`/`HTTPS_PROXY`). Since the domestic endpoint is a China-local IP, routing it through an overseas proxy (127.0.0.1:7897) causes **connection timeouts** — even though `curl --noproxy '*'` works fine from a terminal.

**Fix:** Clear proxy env vars before making the request:

```python
import os
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
# Now urllib will connect directly to api.siliconflow.cn
```

**Alternative:** Use `curl` directly from `terminal()` with `--noproxy '*'` for one-shot tests, but `execute_code` is preferred for multi-step validation logic.

## Related

- OpenRouter-compatible custom providers: see `references/openai-compatible-custom-provider.md`
- OpenAI provider quirks (the `openai` alias issue): see `references/openai-provider-quirks.md`