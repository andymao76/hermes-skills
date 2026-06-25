---
name: scheduled-content-jobs
description: Create and manage scheduled content delivery cron jobs (daily digests, trend reports, news briefings). Covers both script-based and AI-driven patterns with multi-platform delivery.
category: productivity
---

# Scheduled Content Jobs

Create cron jobs that auto-generate and deliver content to messaging platforms.

## Trigger

User asks to create a recurring content job: news briefings, trend reports, daily digests, monitoring alerts.

## Two Patterns

### Pattern A: Script-Based (no_agent=true)

Use when the data source is fixed and formatting is programmatic — e.g., scraping GitHub Trending, fetching RSS feeds, API polling.

- Set `script` to the script path (resolved under `~/.hermes/scripts/`)
- Set `no_agent=true` — zero token cost, script output is delivered verbatim
- Set `enabled_toolsets` is unnecessary (no LLM involved)

Example:
```
cronjob(action='create', name='GitHub Trending 日报', schedule='0 9 * * *',
        script='github-trending.py', no_agent=true, deliver='telegram,discord')
```

### Pattern B: AI-Driven (no_agent=false, default)

Use when the task requires reasoning: searching, extracting, curating, formatting, summarization.

- Provide a self-contained `prompt` with clear steps
- Use `enabled_toolsets` to restrict to only needed tools (e.g., `["web"]` for search+extract) — this cuts token overhead significantly
- Do NOT include toolsets the prompt doesn't need

Example:
```
cronjob(action='create', name='每日头条新闻', schedule='30 9 * * *',
        prompt='...', deliver='telegram,discord', enabled_toolsets=['web'])
```

## Multi-Platform Delivery

Comma-separate platform names in `deliver`:
- `telegram` — home channel
- `discord` — home channel (must specify channel if not default)
- `weixin` — WeChat (beware rate limits: `rate limited` errors are common)
- Combine: `telegram,discord`

To list available targets: `send_message(action='list')`

## Pitfalls

- **Weixin rate limits**: The WeChat/iLink backend frequently returns `rate limited`. For recurring jobs, prefer Telegram and Discord which are more reliable.
- **Cron runs in fresh session**: The prompt must be fully self-contained — no reliance on conversation context.
- **Script mode delivery**: Empty stdout = silent (no message sent). Non-zero exit = error alert sent. Design scripts to be quiet when there's nothing to report.
- **Time zones**: Cron schedules use the server's local timezone (UTC+8 for this user).

## Prompt Template for News Briefings
See `references/news-briefing-prompt.md` for the reusable Chinese news aggregation prompt template.
See `references/weekly-skills-inventory-prompt.md` for the reusable weekly skills inventory cron prompt template.

**Time window pattern**: When the user specifies a custom time range (e.g. "from yesterday 00:00 to today 09:30"), embed it literally in the prompt instead of saying "last 24 hours". This ensures the cron agent gets the exact intended window regardless of when it fires. The prompt template already uses this pattern — replicate it when adapting.

## Updating Jobs (Remove + Recreate)

When changing delivery targets or other fundamental config, use remove + create (cron does not support in-place edits of `deliver`):

```
# Step 1: List to find job_id
cronjob(action='list')

# Step 2: Remove old
cronjob(action='remove', job_id='<id>')

# Step 3: Create new with updated config
cronjob(action='create', name='...', schedule='...', prompt='...',
        deliver='telegram,discord', ...)
```

## Verification

After creating a job, test it:
```bash
cronjob(action='run', job_id='<id>')
```
Check the target platforms to confirm delivery.

## Pattern C: Periodic Inventory — System Snapshot

Use for recurring inventory/audit of operating state (deployed tools, installed skills, running services, config snapshots).

Template:
```yaml
# AI-driven, writes results to knowledge base, then feeds enzyme refresh
prompt: >
  1. Call <relevant_listing_API>() to get full inventory
  2. Group by category, generate structured Markdown with statistics + per-item listings
  3. Save to ~/knowledge/<topic>/<weekly-file>.md (overwrite)
  4. Run `cd ~/knowledge && enzyme refresh` to update semantic index
  5. Report: total items, category count, file path
schedule: "0 23 * * 0"   # Sunday 23:00
deliver: origin          # back to the creating conversation
```

Cron prompt MUST be self-contained — no assumptions about past context. Include exact steps for categorization, file path, and enzyme refresh.

