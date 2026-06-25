# Telegram Home Channel & CLI Send Setup

## The Asymmetry Problem

Telegram has **two separate home-channel concepts**:

1. **Gateway home channel** — set via `/sethome` in Telegram DM. This controls where the gateway routes cron jobs and cross-platform messages when they arrive *via the gateway*.
2. **CLI `send_message` home channel** — read from `.env` or `config.yaml` at the start of the CLI session. The CLI tool does NOT dynamically read the gateway's `/sethome` value.

This means: after using `/sethome` in Telegram, `send_message(target="telegram")` from the CLI still fails with "No home channel set" until you also configure it for the CLI.

## The Fix

After running `/sethome` in Telegram (which writes `TELEGRAM_HOME_CHANNEL=<id>` to `.env`), also set it in config.yaml for the CLI tool:

```bash
hermes config set TELEGRAM_HOME_CHANNEL <your_user_id>
```

For the CLI send_message tool to pick it up, you need either:
- A new CLI session (`/reset` or restart `hermes`), OR
- Use `telegram:<user_id>` directly: `send_message(target="telegram:7090273400", message="...")`

## Quick Workaround

When home channel isn't set yet, just pass the ID explicitly:

```python
send_message(target="telegram:7090273400", message="...")
```

This always works regardless of home channel configuration.

## Verifying

```bash
grep TELEGRAM_HOME_CHANNEL ~/.hermes/.env
grep TELEGRAM_HOME_CHANNEL ~/.hermes/config.yaml
```

Both should show your Telegram user ID (not your bot's ID).
