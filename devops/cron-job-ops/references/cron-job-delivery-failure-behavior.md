# Cron Job Delivery Failure Behavior

## Multi-Platform Delivery Asymmetry on Failure

When a cron job is configured with multiple delivery targets (e.g. `deliver: "telegram,discord"`) and the job **fails at the model level** (Content Exists Risk, timeout, API error), the scheduler does **not** fan out the error notification to all configured targets equally.

Instead, the scheduler delivers the error notification to **one platform only** — typically the first one in the delivery queue, or the one it can reach most quickly. The other platforms receive nothing.

This means: if a user has a cron job that should always reach both Telegram and Discord, a failure at the LLM layer will only notify them on one platform (usually Telegram). They may assume the second platform also received the notification and be unaware the job failed.

### Observed Behavior (2026-06-09)

Example job config: `deliver: "telegram,discord"` for "每日头条新闻" (LLM-based, web tools, DeepSeek model).

On failure (Content Exists Risk at "Streaming failed before delivery"):
- Telegram ✅ — error notification delivered (via live adapter, fell back to standalone)
- Discord ❌ — no delivery attempt logged anywhere (agent.log, gateway.log)

This is **not** a bug in the Discord adapter — the scheduler simply did not attempt delivery to Discord for the error path.

### Root Cause

The scheduler's error handling path (`_run_job_impl` → raises `RuntimeError`) triggers a delivery to the job's configured targets. But the implementation appears to iterate delivery targets and stop on first success or process them sequentially without guaranteeing full fan-out on failure.

The error is raised from within the agent loop, and only the error text is delivered — not via the job's normal output pipeline.

### Detection

When investigating a multi-platform cron job failure:

```
# Check for delivery on all platforms
grep "delivered to" ~/.hermes/logs/agent.log | grep <job_id>
```
This shows only the platforms that actually received the error notification.

Cross-reference with `cronjob(action='list')` → check `last_delivery_error` — if `null` but the job failed, the error was delivered to at least one platform.

## Live Adapter Fallback

When a cron job's agent runs inside a gateway-managed session and the gateway's live adapter delivery path is degraded, the scheduler falls back to **standalone adapter delivery**.

### Log Signature

```
WARNING cron.scheduler: Job '<job_id>': live adapter send to telegram:<chat_id> failed (send_path_degraded), falling back to standalone
```

### Behavior

1. The live adapter (`send_message` via the gateway's in-process adapter) fails with `send_path_degraded`
2. The scheduler falls back to **standalone send** — directly calling the platform's adapter outside the gateway's live-connection pool
3. For Telegram: routes through the proxy (if configured): `INFO tools.send_message_tool: send_message: standalone Telegram send routed through proxy http://127.0.0.1:7897`
4. The message is delivered successfully via the fallback path

### Implications

- `send_path_degraded` is **not** a permanent failure — the message still goes through
- The fallback is transparent to the end user (they receive the message as normal)
- The `delivered to telegram:` log line still appears after the fallback completes
- This is a network/connection pool issue, not a configuration problem
