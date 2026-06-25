# Open WebUI External Connection Persistence

## The Problem

Open WebUI (0.9.6) loads external OpenAI-compatible connections (`OPENAI_API_BASE_URLS`, `OPENAI_API_KEYS`) from the application's runtime config, NOT from the SQLite database. After a restart, these configs are lost unless:

1. They were passed as environment variables at startup, OR
2. They are re-applied via API after each boot

The `config` table in `webui.db` does NOT persist the external connection URL/keys by default. The `default_models` setting CAN be persisted in the DB, but the connection itself cannot.

## The Fix

Use `~/.hermes/scripts/open-webui.sh` which:
1. Starts Open WebUI on port 3000
2. Waits for the service to become available
3. Logs in via the API
4. POSTs to `/api/v1/configs/connections` to re-apply the external connection

## DB Schema for Persisted Config

Table: `config`
| Column | Type | Content |
|--------|------|---------|
| id | INTEGER | 1 (singleton row) |
| data | JSON | `{"default_models": "siliconflow", ...}` |
| version | INTEGER | Schema version |
| created_at | DATETIME | |
| updated_at | DATETIME | |

## Other important DB tables

- `auth` — login credentials (email, bcrypt password hash)
- `user` — user profiles (id, name, email, role)
- `api_key` — API keys for programmatic access (requires `ENABLE_OPENAI_API=true` to work)
- `model` — custom model configurations (user-created, not external connection models)
- `chat` / `message` — conversation history
