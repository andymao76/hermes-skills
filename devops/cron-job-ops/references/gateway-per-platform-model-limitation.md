# Gateway Per-Platform Config Bridge Analysis

## What Config Keys Are Actually Bridged

The gateway's `load_gateway_config()` (`gateway/config.py`) reads top-level config blocks like `weixin:`, `telegram:`, `discord:` from config.yaml and bridges specific keys into the `PlatformConfig.extra` dict. **Only these keys are bridged:**

```python
# From the shared-key bridge loop in load_gateway_config():
_APPROVED_BRIDGE_KEYS = [
    "unauthorized_dm_behavior",
    "notice_delivery",
    "reply_prefix",
    "reply_in_thread",
    "require_mention",
    "free_response_channels",
    "mention_patterns",
    "exclusive_bot_mentions",
    "dm_policy",
    "allow_from",
    "allow_admin_from",
    "user_allowed_commands",
    "group_policy",
    "group_allow_from",
    "group_allow_admin_from",
    "group_user_allowed_commands",
    "channel_prompts",
    "gateway_restart_notification",
]
# Plus platform-specific keys:
# - TELEGRAM: allowed_chats, group_allowed_chats, allowed_topics
# - DISCORD/SLACK: channel_skill_bindings
```

**`model` and `provider` are NOT in this list.** The `PlatformConfig` dataclass itself has no `model` or `provider` fields.

## How Agent Creation Actually Works

The gateway creates AIAgent instances using the **global model config** from `model.default` and `model.provider` in config.yaml. There is no per-platform dispatch logic that reads platform-specific model settings.

```python
# In gateway/run.py, agent creation:
agent = AIAgent(
    provider=cfg_get("model.provider"),   # always the global value
    model=cfg_get("model.default"),       # always the global value
    ...
)
```

## Why `hermes config set weixin.provider` Writes But Does Nothing

`hermes config set weixin.provider siliconflow` writes to config.yaml:
```yaml
weixin:
  provider: siliconflow
```

But `load_gateway_config()` reads `yaml_cfg.get("weixin")`, sees `provider` is not in the approved bridge key list, and **skips it entirely**. The key/value sits in config.yaml but is never loaded by any code path.

## If the Gateway Code Were to Support This

A future implementation would need:
1. `PlatformConfig` dataclass to gain `model: str = ""` and `provider: str = ""`
2. `load_gateway_config()` bridge loop to include `model` and `provider`
3. Gateway agent creation to read `config.platforms[platform].model` before falling back to global default

This is a feature request, not a bug fix.
