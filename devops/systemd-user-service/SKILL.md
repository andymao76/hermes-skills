---
name: systemd-user-service
category: devops
description: Best practices and troubleshooting for deploying systemd user-level services (e.g., Node.js bridges, local scripts).
---

# Systemd User Service Deployment

This skill provides proven patterns for deploying background services using `systemd --user`. Use this when the user asks to make a local script, Node.js app, or bridge run persistently in the background, survive reboots, or auto-restart on failure.

## Standard Template

For a user-level service (e.g., `~/.config/systemd/user/my-service.service`), use the following minimal, robust structure:

```ini
[Unit]
Description=My Hermes Background Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/absolute/path/to/app
ExecStart=/usr/bin/node main.js
Restart=on-failure
RestartSec=5
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="HOME=/home/andymao"

[Install]
WantedBy=default.target
```

## Hermes Dashboard Service (Concrete Example)

This pattern was used in a real session to make Hermes Dashboard auto-start on login:

```ini
[Unit]
Description=Hermes Agent Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/andymao/.hermes/hermes-agent/venv/bin/hermes dashboard --port 9119 --no-open
Restart=on-failure
RestartSec=5
Environment=HERMES_HOME=/home/andymao/.hermes
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=default.target
```

Key differences from a generic service:
- `After=network-online.target` + `Wants=network-online.target` — ensures network is fully ready before starting (dashboard needs to check for stale processes on port 9119)
- `--no-open` flag — prevents the dashboard from trying to open a browser (headless server)
- `Environment=HERMES_HOME` — required so the dashboard finds the correct config path regardless of session context
- The `ExecStart` must use the **venv Python** absolute path, not just `hermes` — systemd user services may not have `~/.local/bin` in PATH

## Critical Pitfalls & Troubleshooting

### 1. ⚠️ Restart=always Must Have StartLimitBurst (Prevent Restart Storm)

**Symptom:** System becomes unresponsive — mouse, keyboard, SSH all freeze. After forced reboot, `journalctl` shows:
- `"Under memory pressure, flushing caches"` repeated many times
- Service restart counter in the thousands or tens of thousands
- `libinput: event processing lagging behind by Nms, your system is too slow`

**Root cause:** The service's executable file (or the entire working directory) was deleted or moved, but the service config uses `Restart=always` without `StartLimitBurst`. Systemd retries endlessly every `RestartSec` seconds, flooding journald with log entries until memory is exhausted and the system thrashes.

**Real case (feishu-hermes, 2026-06-25):**
- `/home/andymao/feishu-hermes/` directory deleted
- `Restart=always` (no burst limit) → **31,195** failed restart attempts in 28 hours
- Journald under memory pressure → libinput keyboard delay **4,791ms** → total freeze

**Fix — never use bare `Restart=always`:**

```ini
# BARE Restart=always — DANGEROUS (no limit on retries)
Restart=always
# → can cause restart storm if the executable is missing

# SAFE — with burst limit:
[Unit]
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Restart=on-failure
RestartSec=10
```

**Best-practice pattern for user services:**
```ini
[Unit]
Description=My Service
After=network.target
StartLimitIntervalSec=600
StartLimitBurst=3

[Service]
Type=simple
ExecStart=/usr/bin/node /path/to/app.js
Restart=on-failure
RestartSec=10
```

**Detection command:**
```bash
# Find services with abnormally high restart counts
journalctl --user --no-pager 2>/dev/null | grep "Scheduled restart job" | sed 's/.*service//' | sort | uniq -c | sort -rn | head -5
```

**Emergency stop:**
```bash
systemctl --user stop <service>
systemctl --user disable <service>
```

### 2. Avoid `User=` and `Group=` in User Services
**Symptom:** `Failed to determine supplementary groups: Operation not permitted` and `status=216/GROUP`.
**Fix:** When using `systemctl --user`, the service *already* runs as the invoking user. Do **not** include `User=...` or `Group=...` directives in the `[Service]` section. They will cause permission/group resolution failures in standard user-session configurations.

### 2. Port Conflicts Mask as Service Failures
**Symptom:** Service exits immediately with `code=exited, status=1/FAILURE`. Node.js logs might be truncated or show `EADDRINUSE`.
**Diagnosis:** The port is likely held by a leftover interactive test process.
**Fix:** 
1. Check the service log: `journalctl --user -u <service-name> --no-pager -n 20`
2. Find the conflicting process: `lsof -ti :<PORT>` or `ss -tlnp | grep <PORT>`
3. Kill the stale process: `kill -9 <PID>`
4. Reset failed state and restart: `systemctl --user reset-failed <service-name> && systemctl --user restart <service-name>`

### 3. Absolute Paths & Environment Variables
**Symptom:** "Command not found" or modules fail to load relative to the wrong directory.
**Fix:** 
- Always use absolute paths in `WorkingDirectory` and `ExecStart` (e.g., `/usr/bin/node` instead of `node`, verify with `which node`).
- Explicitly set `Environment="HOME=/home/andymao"` and `Environment="PATH=..."` because user services may not inherit the full interactive shell environment (especially for tools like Baileys that rely on `~/.hermes/` paths).

## Management Commands

- **Reload daemon after editing:** `systemctl --user daemon-reload`
- **Clear failed state:** `systemctl --user reset-failed <service-name>`
- **Enable autostart:** `systemctl --user enable <service-name>`
- **Check status:** `systemctl --user status <service-name>`
- **View live logs:** `journalctl --user -u <service-name> -f`