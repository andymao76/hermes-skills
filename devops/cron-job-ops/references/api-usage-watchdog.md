# API Usage Watchdog Cron Jobs

When a cron job relies on a third-party API (Tavily, Serper, etc.) with usage limits, set up a **no_agent watchdog** to alert before the quota runs out.

## Pattern

1. **Create a shell script** that queries the API usage endpoint and exits with codes:
   - `0` = sufficient (>=200 left)
   - `1` = warning (100-199 left)
   - `2` = critical (<100 left)

2. **Register it as a no_agent cron job** (zero token cost):
   ```python
   cronjob(action='create',
       name='Tavily Usage Watchdog',
       schedule='0 20 * * 5',      # weekly Friday 20:00
       script='tavily-watchdog.sh',
       no_agent=True,
       deliver='origin',
       repeat=3)                    # auto-destroy after 3 runs
   ```

3. **Exit code semantics for no_agent scripts:**
   - `exit 0` + empty stdout → silent (nothing delivered)
   - `exit 0` + non-empty stdout → delivered as-is
   - `exit non-zero` → error alert always delivered
   This means the watchdog naturally stays quiet when quota is fine.

## Tavily Usage Endpoint

```
GET https://api.tavily.com/usage
Authorization: Bearer tvly-...
```

Returns:
```json
{
  "key": { "usage": 707, "limit": null, "search_usage": 650, ... },
  "account": { "current_plan": "Researcher", "plan_usage": 707, "plan_limit": 1000, ... }
}
```

Key fields: `account.plan_usage` / `account.plan_limit` (monthly rolling).
