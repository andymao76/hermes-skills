---
name: model-selection
category: research
tags: [model-selection, testing, switching, siliconflow, multimodal, vision, provider-comparison, bailian, aliyun, latency-testing]
trigger: user asks to switch model/provider, evaluate a new model, compare providers, or find a model good at a specific capability (vision, coding, etc.)
description: Systematic workflow for researching, testing, and switching AI models on SiliconFlow and other Hermes providers, including multi-provider comparison and latency benchmarking
---

# Model Selection & Switching

Systematic process for evaluating and switching between AI models in Hermes Agent, with emphasis on multimodal/vision-capable models on SiliconFlow and multi-provider comparison workflows.

## Provider Comparison Workflow

When user asks to compare providers or choose the best option, follow this systematic approach:

### Step 1: Latency Test (Ping)

Test each provider's API endpoint directly:

```bash
curl -w "@curl-format.txt" -o /dev/null -s "https://api.siliconflow.com/v1" -x 127.0.0.1:7897
curl -w "@curl-format.txt" -o /dev/null -s "https://api.siliconflow.cn/v1"
curl -w "@curl-format.txt" -o /dev/null -s "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

**Expected baselines:**
- SiliconFlow 国内站：~100ms (直连)
- SiliconFlow 国际站：~1000ms (经代理)
- 阿里云百炼：~100-200ms (直连)

### Step 2: Response Time Test

Use `hermes chat -q` with identical prompts:

```bash
hermes chat -q "用 30 字左右介绍你自己，并说出现在的日期和时间" --provider siliconflow --model "Qwen/Qwen3.5-397B-A17B" -Q
hermes chat -q "用 30 字左右介绍你自己，并说出现在的日期和时间" --provider siliconflow-cn --model "Qwen/Qwen3.5-397B-A17B" -Q
hermes chat -q "用 30 字左右介绍你自己，并说出现在的日期和时间" --provider bailian --model "qwen-plus" -Q
```

Measure total response time (typically 8-15 seconds for simple queries).

### Step 3: Compare Across Dimensions

Create a comparison table covering:
- **Latency**: API ping time (ms)
- **Response time**: End-to-end query time (seconds)
- **Context window**: Must meet ≥64K for Hermes
- **Pricing**: Input/output tokens per million
- **Free tier**: Available credits, expiry
- **Requirements**: Proxy (Y/N), registration

### Step 4: Present Trade-offs, Let User Decide

Frame recommendations as:
- "For X use case → choose Y (reason)"
- "If you prioritize A → pick B; if B → pick C"

## When to Use

- User asks "switch to a model strong at X" (vision, coding, reasoning, etc.)
- User wants to test a new model before committing
- User asks "what model is good for X task"
- User wants to compare models on the same provider

## Workflow

### Step 1: Research available models

When user requests a model switch, first understand the landscape:

1. **For SiliconFlow**: Search `site:siliconflow.cn/models` or `site:siliconflow.com/articles` plus the capability keyword (e.g., "多模态", "视觉", "vision", "multimodal")
2. **Model naming convention**: SiliconFlow uses `Vendor/ModelName` format (e.g., `Qwen/Qwen3.6-35B-A3B`, `deepseek-ai/DeepSeek-V4-Flash`)
3. **Check if model supports**: text-only, image+text (multimodal), video, tool calling, thinking mode

### Step 2: Test model connectivity before switching

Use `hermes chat` (NOT `hermes ask` — that command does not exist):

```
hermes chat -q "简短连通性测试消息" --provider PROVIDER --model "Model/Name" -Q
```

**Flags explained:**
- `-q` / `--query QUERY`: Non-interactive mode (single query, no session)
- `-Q` / `--quiet`: Suppress banner, spinner, tool previews — only final response
- `--provider PROVIDER`: Which provider (e.g., `siliconflow`, `deepseek`)
- `--model MODEL`: Full model ID string

**Pitfall**: `hermes ask` does NOT exist. Always use `hermes chat -q` for one-off queries.

### Step 3: Switch model in config

Use `hermes config set` (NOT direct file editing — the agent file tools are blocked):

```
hermes config set model PROVIDER/ModelName
```

Also update the provider's own default and model fields for consistency:

```
hermes config set providers.PROVIDER.default "ModelName"
hermes config set providers.PROVIDER.model "ModelName"
```

**Config keys changed:**
- `model` (top-level) — set to `provider/ModelName` e.g. `siliconflow/Qwen/Qwen3.6-35B-A3B`
- `providers.<name>.default` — just the model name e.g. `Qwen/Qwen3.6-35B-A3B`
- `providers.<name>.model` — just the model name e.g. `Qwen/Qwen3.6-35B-A3B`

### Step 4: Verify

Read `/home/andymao/.hermes/config.yaml` to confirm:
- Line 1: `model: provider/ModelName`
- Provider section: `default: ModelName`, `model: ModelName`

## SiliconFlow Multimodal (Vision) Models Reference

See `references/siliconflow-vision-models.md` for a curated list of tested multimodal models on SiliconFlow.

## Pitfalls

- **`hermes ask` does not exist** — use `hermes chat -q` instead
- **Cannot edit config.yaml directly** via agent file tools (patch/write_file) — use `hermes config set`
- **Provider prefix matters**: top-level `model` uses `provider/ModelName` format; provider-specific `default`/`model` fields use just `ModelName`
- **Proxy requirement**: SiliconFlow international API (`api.siliconflow.com`) requires proxy `127.0.0.1:7897` — model testing via `hermes chat` handles this automatically
- **Sessions persist old model**: model change applies to NEW sessions (`/new` or `/reset`), not the current running one
- **Provider switching**: `--provider` alone does NOT auto-switch model name — you must also specify `--model`
- **Reasoning model max_tokens trap**: DeepSeek V4 Pro 等推理模型在 `max_tokens` 过小（≤20）时，全部 token 被 `reasoning_content` 消耗，`content` 字段为空 → 被误判为"异常"。测试时 `max_tokens` 需 ≥100，且需同时检查 `content` 和 `reasoning_content`。详见 `references/multi-provider-latency-test.md`
- **API key 注入破坏源码**: 在 execute_code 或 heredoc 中嵌入含特殊字符的 API key（如 Gemini `AIzaSy...`）会破坏字符串语法。解决方案：运行时从 `.env`/`config.yaml` 读取 key，不要硬编码或内联到源码中。详见 `references/multi-provider-latency-test.md`
- **Gemini API 不可达**: 从当前网络环境 `generativelanguage.googleapis.com` 完全超时（HTTP 000），无论是否挂代理。测试脚本中 Gemini 条目预期返回不可达状态

## Provider Configurations Reference

See dedicated reference documents for detailed configuration:

- `references/multi-provider-latency-test.md` — 多 Provider 直测方案：curl 表格化测试、推理模型 max_tokens 陷阱、shell 转义方案、API key 注入问题
- `references/siliconflow-domestic-vs-international.md` — SiliconFlow 国内站 vs 国际站完整对比 (延迟、计费、切换步骤)
- `references/aliyun-bailian-provider.md` — 阿里云百炼配置、API Key 获取、模型对比、与 SiliconFlow 对比
- `references/nous-research-provider.md` — Nous Research (inference-api) provider 配置：端点、认证、免费/付费模型、低余额错误处理、连通性测试
- `references/vision-analysis-fallback.md` — OpenRouter + Gemini 2.5 Flash 视觉分析备选方案（当 SiliconFlow VL 模型不可用时）

**一键测试脚本**: `scripts/multi-provider-latency-table.sh` — 自动读取所有 provider API keys，表格化输出连通性和时延

**Key benchmarks (2026-06-08):**
- SiliconFlow 国内站延迟：**0.09s** (直连)
- SiliconFlow 国际站延迟：**1.02s** (经代理) — **11 倍差距**
- 阿里云百炼响应时间：**8 秒** (qwen-plus)
- SiliconFlow 国际站响应时间：**13 秒** (Qwen3.5-397B)

**Hermes context requirement:** Minimum 64K tokens
- ❌ `qwen-max` (32K) — too small, will fail initialization
- ✅ `qwen-plus` (128K), `qwen3.5-plus` (256K), `qwen3-max` (256K)
