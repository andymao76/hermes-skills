# Telegram Unauthorized User Debugging

## Symptom

Gateway log shows:
```
WARNING gateway.run: Unauthorized user: 7090273400 (Andy M) on telegram
```

User sends messages to the bot but gets no response. The bot is connected
(polling mode) and `/sethome` and other commands have no effect.

## Root Cause

The gateway authorizes Telegram DMs via **environment variables**, NOT via
`config.yaml` fields. The relevant env vars are:

| Env var | Purpose | Where set |
|---------|---------|-----------|
| `TELEGRAM_ALLOWED_USERS` | Telegram user IDs allowed to DM the bot | `.env` |
| `TELEGRAM_GROUP_ALLOWED_CHATS` | Group/supergroup chat IDs where bot responds | `.env` |
| `TELEGRAM_ALLOW_ALL_USERS` | If `true`, skip all authorization | `.env` (debug only) |

The `allowed_chats` field in `config.yaml` only controls **group** responses,
not DM authorization. DMs are authorized solely by `TELEGRAM_ALLOWED_USERS`.

## Common Mistake

Setting `TELEGRAM_ALLOWED_USERS=8819964718` — this is the **Bot's own user
ID** (from the bot token prefix before the colon), not the **human user's
Telegram user ID**.

## How to Find the Correct User ID

### Method 1: Read it from gateway logs

Send a message to the bot, then check:
```bash
tail -20 ~/.hermes/logs/gateway.log | grep "Unauthorized user"
```
Output: `Unauthorized user: 7090273400 (Andy M) on telegram`
→ Your user ID is `7090273400`.

### Method 2: getUpdates API

```bash
curl -s --proxy http://127.0.0.1:7897 \
  "https://api.telegram.org/bot<TOKEN>/getUpdates" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['message']['from']['id'])"
```

### Method 3: Use @userinfobot

Open Telegram, search for @userinfobot, start it, it will reply with your user ID.

## Fix

```bash
sed -i 's/TELEGRAM_ALLOWED_USERS=.*/TELEGRAM_ALLOWED_USERS=7090273400/' ~/.hermes/.env
systemctl --user restart hermes-gateway
```

## Verify

After restart, check the gateway log for no more `Unauthorized` lines:
```bash
tail -10 ~/.hermes/logs/gateway.log | grep -i "telegram"
```
Expected: `[Telegram] Connected to Telegram (polling mode)` without subsequent
`Unauthorized` warnings.

## Setting Home Channel

After authorization works, send `/sethome` in the Telegram DM with the bot.
This sets `TELEGRAM_HOME_CHANNEL` in `.env` so `send_message(target="telegram")`
works from any Hermes context (CLI, cron, subagent).
