# GitHub Token + Hermes MCP Integration Notes

## Reproduction: Fine-Grained Token → Classic Token Migration

**Symptom:** `gh auth status` shows logged in, `gh api user --jq '.login'` returns correct username, but `gh api user/repos --jq '.[].full_name'` returns empty.

**Root cause:** Token starts with `github_pat_` (fine-grained) and only authorizes specific repos selected during creation. The agent cannot list any repos, create repos, or work with repos not explicitly in the token's scope.

**Fix:**

```bash
# 1. User creates classic token at https://github.com/settings/tokens
#    - Type: "Classic"
#    - Scopes: repo, workflow, read:org
#    - Copy the ghp_* token

# 2. Log in with new token
echo '<ghp_..._token>' | gh auth login --with-token

# 3. Verify
gh auth status
gh repo list --limit 5    # Should now show repos
```

## MCP Config Corruption Pattern: Wrong YAML Nesting

**Symptom:** `hermes mcp test github` never invoked (no output) or "MCP server not found". The github entry exists in config.yaml but is nested under `session_reset:` instead of `mcp_servers:`.

**How it happens:** A manual YAML edit or a prior agent placed `filesystem:` and `github:` inside `session_reset:` block, usually with a placeholder token like `github...MVsR`. Hermes ignores unrecognized keys in `session_reset:` silently.

**Fixed config structure:**

```yaml
mcp_servers:
  # ... other MCP servers ...
  github:
    args:
    - -y
    - '@modelcontextprotocol/server-github'
    command: npx
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: ghp_********************
    timeout: 60

session_reset:
  at_hour: 4
  idle_minutes: 1440
  mode: none
  # NO filesystem: or github: here
```

**Python fix script fragment** (to move github from session_reset to mcp_servers):
```python
import os, re
cfg = os.path.expanduser('~/.hermes/config.yaml')
with open(cfg) as f:
    content = f.read()

# Remove ghost github/filesystem from session_reset
old_block = '''  github:
    args:
    - -y
    - '@modelcontextprotocol/server-github'
    command: npx
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: github...MVsR'''
content = content.replace(old_block, '')

# Ensure clean session_reset
# Add proper github entry under mcp_servers
# ... (logic depends on current structure)

with open(cfg, 'w') as f:
    f.write(content)
```

## MCP GitHub Server Verification

```bash
# Should show 26 tools
hermes mcp test github

# Expected tools include:
#   create_or_update_file, create_repository, create_issue,
#   create_pull_request, push_files, search_repositories, search_code,
#   fork_repository, merge_pull_request, get_file_contents, etc.

# Verify in mcp list
hermes mcp list
# Expected: github | npx -y @modelcontextprotocol/server-github | all | ✓ enabled
```
