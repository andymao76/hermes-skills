# Second Brain V5 Architecture Blueprint

Source: 2026-06-11 user strategic analysis

## Current State (V4.0)

Hermes Agent is already a **personal AI operating system prototype**, not a chatbot:

| Layer | Description |
|-------|-------------|
| L1 | Messaging Channels: Telegram / Discord / WeChat / Feishu / CLI |
| L2 | Gateway & Scheduler: Gateway + MCP Manager + Cron x12 |
| L3 | AI Core Engine: 6 Providers (DeepSeek/SiliconFlow/Bailian/Gemini/Nous/OpenAI) |
| L4 | MCP Tools: 7 MCP servers + 4 built-in tools |
| L5 | Storage & Knowledge: kb-search (608 files, 72K segments, 100% embedded) |

## Five Capability Gaps for V5.0

### Gap 1: Proxy/Messaging is a Single Point of Failure

- Relies on local Clash Verge (127.0.0.1:7897)
- Proxy down = Provider / WebSearch / MCP all unstable
- **Solution**: network-doctor skill (health check + auto-fallback + CN/overseas mode switching)

### Gap 2: Missing Memory Layering

- Current kb-search is a document warehouse, not a second brain
- **Solution**: 5-layer memory (transient / project / long-term / preferences / action)

### Gap 3: Multi-channel lacks unified strategy

- **Solution**:
  - Telegram → Personal command console
  - Feishu → Work input / enterprise collaboration
  - WeChat → Lightweight alerts
  - CLI → Deep technical operations
  - Discord → Archive push / backup channel
  - Obsidian → Knowledge base master storage
  - Apple Notes → Mobile viewing layer

### Gap 4: Missing Task Closure Cycle

- Current Crons are push-oriented, not feedback-loop-oriented
- **Solution**: Input → Understand → Archive → Remind → Execute → Review → Summarize
  - daily_inbox.md / project_status.yaml / todo_queue.sqlite / decision_log.md / weekly_review.md

### Gap 5: Knowledge management hygiene

- Need periodic re-embed, failed-file retry, duplicate detection, mojibake detection, stale document cleanup, index integrity reports

## Network Model Strategy

| Mode | Preferred Provider | Fallback |
|------|-------------------|----------|
| China | DeepSeek / SiliconFlow / Bailian | Gemini |
| Overseas | Gemini / OpenAI / OpenRouter | Nous |
| Proxy failed | Auto-fallback to China providers | — |
| Deep analysis | deepseek-v4-pro / Gemini 2.5 Pro | — |
| Daily fast | deepseek-v4-flash / qwen-plus | — |

## 10 Skills Priority (from user analysis)

| Prio | Skill | Rationale |
|:----:|-------|-----------|
| P0 | network-doctor | Fix proxy single point of failure |
| P0 | provider-switch | Network-aware model selection |
| P0 | second-brain-inbox | PARA unified inbox |
| P1 | project-status | Centralized project status management |
| P1 | daily-review | Auto daily report + push |
| P2 | apple-notes-mcp | Mobile viewing layer |
| P2 | obsidian-sync | Bi-directional sync enhancement |
| P3 | backup-restore-drill | Encrypted backup + recovery drill |
| P3 | document-cleaner | Stale doc detection + cleanup |
| P3 | travel-mode | Auto network mode switching |

## PARA Directory Structure

```
~/knowledge/
├── 00_INBOX/              ← Unified entry for all inputs
├── 01_PROJECTS/           ← Projects with clear goals
├── 02_AREAS/              ← Ongoing areas of responsibility
├── 03_RESOURCES/          ← Reference materials
├── 04_ARCHIVE/            ← Completed/stale
└── _system/               ← System files (project_status.yaml, decision_log.md)
```

## Key Principle

Stop stacking features. Move from feature-centric to system-centric construction.
