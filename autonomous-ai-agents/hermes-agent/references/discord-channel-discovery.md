# Discord Channel Discovery & Send Workflow

When the gateway is running but Discord has no home channel set, use these steps to find available channels and send messages.

## Prerequisites

- Gateway running with Discord connected (`[Discord] Connected as botname#1234` in gateway.log)
- Bot invited to the server
- Bot token available in `.env`

## Step 1: List guilds the bot is in

```bash
curl -s -x http://127.0.0.1:7897 \
  -H "Authorization: Bot $(grep DISCORD_BOT_TOKEN /home/andymao/.hermes/.env | cut -d= -f2)" \
  "https://discord.com/api/v10/users/@me/guilds"
```

Returns guild ID + name.

## Step 2: List text channels in the guild

```bash
curl -s -x http://127.0.0.1:7897 \
  -H "Authorization: Bot $(grep DISCORD_BOT_TOKEN /home/andymao/.hermes/.env | cut -d= -f2)" \
  "https://discord.com/api/v10/guilds/<GUILD_ID>/channels"
```

Filter for `type=0` (Guild Text) or `type=5` (Guild Forum).

## Step 3: Send message to a channel

Using `send_message` tool with explicit channel ID:

```
send_message(target="discord:<CHANNEL_ID>", message="...")
```

This works even when no home channel is set. The channel ID is a numeric snowflake.

## Alternative: Set home channel

Once a home channel is established (via @mention in a channel or DM), future sends can use `target="discord"` without arguments. To set it explicitly:

```bash
hermes config set DISCORD_HOME_CHANNEL <channel_id>
```
