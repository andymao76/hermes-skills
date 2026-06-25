# GitHub Repo Deletion — Scope & Proxy Workaround

## The Problem

Deleting a GitHub repo requires the `delete_repo` OAuth scope, which is **not** included in the standard `repo` scope.

### Error when scope missing

```
HTTP 403: Must have admin rights to Repository.
This API operation needs the "delete_repo" scope.
```

OR (via curl):

```json
{"message": "Must have admin rights to Repository.", "status": "403"}
```

## Check Current Scopes

```bash
gh auth status 2>&1 | grep -o "Token scopes: '.*'"
# Example output: Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

## Fix: Add delete_repo Scope

### Method 1 — gh auth refresh (browser OAuth)

```bash
gh auth refresh -h github.com -s delete_repo
```
This prints a one-time code and URL (https://github.com/login/device). The user must open the URL in a browser, enter the code, and authorize.

**PTY limitation**: In Hermes PTY mode, this command times out after 300s waiting for browser input. It cannot complete in an automated tool context. The user must run it in their own terminal.

### Method 2 — New Classic PAT

1. Go to https://github.com/settings/tokens
2. Generate new classic token (not fine-grained)
3. Select `delete_repo` scope
4. Use the new token:
```bash
echo "<NEW_TOKEN>" | gh auth login --with-token
```

**Note**: `delete_repo` is NOT available on fine-grained PATs (prefix `github_pat_*`). Only classic PATs (`ghp_*`) support it.

### Method 3 — Web UI (no token needed)

Navigate to `https://github.com/<owner>/<repo>/settings`, scroll to "Danger Zone", click "Delete this repository".

## Network Interactions (China + GFW)

- `api.github.com` vs `github.com` may have different accessibility behind GFW
- Through Clash proxy (127.0.0.1:7897): proxy exit cloud IPs (13.x.x.x) hit API rate limits on unauthenticated requests
- OAuth flow (`gh auth refresh`) reaches `github.com` for device code → may time out through proxy with EOF
- Proxy-less direct connection to GitHub in China: inconsistent — some IPs reachable, most blocked
