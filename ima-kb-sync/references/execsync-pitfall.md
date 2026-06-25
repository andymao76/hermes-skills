# Node.js child_process.execSync stdout capture failure

## Symptom

When a Hermes agent session calls a Node.js script via `child_process.execSync()`, the child process exits with code 1 and **empty stdout + stderr** — even though the same command works perfectly when run directly from the shell.

```javascript
// This FAILS when called from within a Hermes agent session:
const result = execSync(
  `node "${IMA_API}" "${apiPath}" '${JSON.stringify(body)}'`,
  { cwd: SKILL_DIR, encoding: 'utf8', timeout: 30000 }
);
// → throws Error: Command failed — stdout: '', stderr: ''
```

```bash
# Same command, works fine in bash:
$ node /home/andymao/.hermes/skills/ima/ima_api.cjs "openapi/wiki/v1/search_knowledge_base" '{"query":"","limit":20}'
# → returns valid JSON
```

## Root Cause

The Hermes agent's terminal tool uses a managed shell environment where `child_process.execSync` (and `spawnSync`) from a **nested Node.js process** have stdout pipe capture issues. The child Node.js process writes stdout but the pipe is not readable by the parent.

This is reproducible:
- `execSync` with `shell: '/bin/bash'` → still fails
- `spawnSync` → same failure
- Direct bash invocation → works fine
- Python's `subprocess.run()` → works fine (different pipe IO model)

## Fix

**Replace Node.js scripts with Python equivalents** when they need to be called from within Hermes agent tasks or cron jobs.

```python
# This WORKS in Hermes agent context:
import subprocess, json
result = subprocess.run(['node', IMA_API, api_path, json.dumps(body)],
    cwd=SKILL_DIR, capture_output=True, text=True, timeout=60)
# → result.stdout has the output
```

## Affected Scripts

- `~/.hermes/scripts/ima_kb_sync.js` — **replaced by** `~/.hermes/scripts/ima_kb_sync.py`
- Any other Node.js script called via `execSync` from within Hermes

## Verification

```bash
# Test if execSync works in the current session:
node -e "
const { execSync } = require('child_process');
try {
  const r = execSync('echo hello', { encoding: 'utf8', timeout: 5000 });
  console.log('OK:', JSON.stringify(r));
} catch(e) {
  console.log('FAIL:', e.status, JSON.stringify(e.stdout), JSON.stringify(e.stderr));
}
"
```

If stdout is empty (`""`), the issue is present — use Python subprocess instead.
