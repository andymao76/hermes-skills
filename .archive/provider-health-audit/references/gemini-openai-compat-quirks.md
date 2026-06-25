# Gemini OpenAI Compat Mode Quirks

Date: 2026-06-08
Environment: Hermes Agent, Gemini 2.5-flash via `generativelanguage.googleapis.com/v1beta/openai`

## Key Findings

### 1. max_tokens Must Be ≥ 50

Setting `max_tokens: 10` or lower causes Gemini to return HTTP 200 with **empty content**:

```json
{
  "choices": [{
    "finish_reason": "length",
    "message": { "role": "assistant" }   // NO "content" field!
  }],
  "usage": { "completion_tokens": 0, "prompt_tokens": 3, "total_tokens": 9 }
}
```

With `max_tokens: 50` it works normally:
```json
{
  "choices": [{
    "finish_reason": "stop",
    "message": { "role": "assistant", "content": "OK" }
  }],
  "usage": { "completion_tokens": 1, "prompt_tokens": 3, "total_tokens": 20 }
}
```

**Rule**: Always set `max_tokens >= 50` when testing Gemini via OpenAI compatible endpoint.

### 2. /v1/models Endpoint Returns 404

The OpenAI-compatible models list endpoint does NOT work:
```
GET /v1beta/openai/models → HTTP 404
```

But the native API endpoint works:
```
GET /v1beta/models?key=API_KEY → Returns model list with supportedGenerationMethods
```

The /v1/models endpoint is not part of the Gemini OpenAI compatibility layer — you must use the native API for model discovery.

### 3. Model ID Must Match Exactly

Accepted model names tested:
- `gemini-2.5-flash` ✅
- `gemini-2.5-pro` ✅ (if quota available)

Rejected:
- `gemini-2.5-flash-001` ❌ (404)
- `models/gemini-2.5-flash` ❌ (works but also returns empty content)
- `gemini-2.5-flash-exp` ❌ (404, experimental models not supported via compat endpoint)

### 4. Native API Works Out of Box

The native `generateContent` endpoint works reliably:
```
POST /v1beta/models/gemini-2.5-flash:generateContent?key=API_KEY
{
  "contents": [{"parts": [{"text": "say OK"}]}]
}
```
→ Always returns valid content, no max_tokens threshold issue.

## Practical Advice for Hermes

1. The current config `base_url: https://generativelanguage.googleapis.com/v1beta/openai` with OpenAI compat mode is fine — but don't let Hermes set `max_tokens` too low.
2. If Gemini returns empty responses in production, check if `max_tokens` is being set below 50 by the caller (e.g., gateway default settings or model config).
3. Native API mode via `google-generativeai` SDK is an alternative if OpenAI compat mode continues to be unreliable.
