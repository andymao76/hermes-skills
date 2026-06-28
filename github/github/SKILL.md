---
name: github
description: GitHub 全生命周期操作 — 认证配置、仓库管理、PR 工作流、CI 监控、Releases。Use when working with GitHub repos, PRs, branches, CI, or releases.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Authentication, Pull-Requests, Repositories, CI/CD, Git, gh-cli, Releases]
---

# GitHub 全生命周期操作

Umbrella skill covering all GitHub operations: authentication, repository management, and PR workflows. Each section is self-contained with both `gh` CLI and `git`+`curl` fallbacks.

## Quick Auth Detection

Every GitHub operation starts with this check:

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      export GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
```

Extract owner/repo from remote:
```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## Section 1: Authentication (was github-auth)

Full details: `references/hermes-mcp-github-setup.md`, `references/github-ecosystem-research.md`, `scripts/gh-env.sh`

### Method 1: HTTPS with Personal Access Token (no gh, no sudo)
```bash
git config --global credential.helper store
# Then do an operation that triggers auth; use token as password
git ls-remote https://github.com/<user>/<repo>.git
```

### Method 2: gh CLI install (no root)
```bash
cd /tmp && curl -sL "https://github.com/cli/cli/releases/download/v2.67.0/gh_2.67.0_linux_amd64.tar.gz" -o gh.tar.gz
tar xzf gh.tar.gz && mkdir -p ~/.local/bin
cp gh_*/bin/gh ~/.local/bin/ && chmod +x ~/.local/bin/gh
```

### Method 3: Token-based gh auth (most reliable for automation)
```bash
echo "<TOKEN>" | gh auth login --with-token
gh auth setup-git
```

### Token Diagnostic (fine-grained vs classic)
- `github_pat_*...` = fine-grained (limited repos) — `gh repo list` returns empty
- `ghp_*...` = classic (full scope) — recommended

### MCP GitHub Server (26 tools)
```yaml
mcp_servers:
  github:
    command: npx
    args: [-y, '@modelcontextprotocol/server-github']
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: ghp_...
    timeout: 60
```
Verify: `hermes mcp test github`

### Proxy for China/firewalled networks
```bash
export HTTPS_PROXY=http://127.0.0.1:7897
git clone --depth 1 https://github.com/owner/repo.git
```

**Network nuances (China + proxy):**
- `api.github.com` and `github.com` may be blocked differently — one might respond direct while the other requires proxy
- Proxy exit IPs (e.g. 13.x.x.x cloud IPs) hit GitHub API rate limits quickly with unauthenticated requests
- `gh auth refresh` OAuth flow requires reaching `github.com` (not just `api.github.com`) — behind GFW, this must go through proxy, and the OAuth redirect may fail with EOF if proxy is unstable
- **Workaround for scope refresh failure**: have the user run `gh auth refresh -h github.com -s <scope>` in their own terminal where the browser OAuth flow can complete, OR create a new classic PAT at https://github.com/settings/tokens with the required scopes

---

## Section 2: Repository Management (was github-repo-management)

Full details: `references/batch-clone-workflow.md`, `references/github-api-cheatsheet.md`

### Clone
```bash
gh repo clone owner/repo
git clone --depth 1 https://github.com/owner/repo.git  # shallow
HTTPS_PROXY=http://127.0.0.1:7897 git clone ...  # behind GFW
```

### Create
```bash
gh repo create my-project --public --clone
gh repo create my-project --private --description "desc" --license MIT --clone
```

### Fork & Sync
```bash
gh repo fork owner/repo --clone
# Add upstream and sync:
git remote add upstream https://github.com/owner/repo.git
git fetch upstream && git checkout main && git merge upstream/main && git push origin main
```

### Top N search by stars
```bash
gh search repos "stars:>1" --sort stars --limit 10 --json name,owner,stargazersCount,description
```

### Releases
```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release download v1.0.0 --dir ./downloads
```

### Delete Repository
```bash
# REQUIREMENT: Token must have 'delete_repo' OAuth scope
# Check current scopes:
gh auth status 2>&1 | grep -o "Token scopes: '.*'"

# If 'delete_repo' missing, add it (requires browser OAuth flow):
gh auth refresh -h github.com -s delete_repo

# Then delete:
gh repo delete owner/repo --yes

# curl fallback (still requires delete_repo scope):
curl -X DELETE -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/owner/repo
```

**Common pitfalls:**
- `repo` scope alone is NOT sufficient for deletion — `delete_repo` is a separate required scope
- `gh auth refresh` opens a browser for OAuth — **cannot complete in PTY** (times out). The user must run this in their own terminal where they can open the browser link
- Token scopes: classic PAT (ghp_*) covers all; `delete_repo` is NOT available on fine-grained PATs

### Secrets & CI
```bash
gh secret set API_KEY --body "value"
gh workflow list
gh run list --limit 10
gh run rerun <ID> --failed
```

---

## Section 3: PR Workflow (was github-pr-workflow)

Full details: `references/ci-troubleshooting.md`, `references/conventional-commits.md`, `templates/pr-body-feature.md`, `templates/pr-body-bugfix.md`

### Branch
```bash
git checkout main && git pull origin main
git checkout -b feat/description
# Conventions: feat/, fix/, refactor/, docs/, ci/
```

### Commit
```bash
git add <files>
git commit -m "feat: short description

- Bullet points for details"
```

### Push & Create PR
```bash
git push -u origin HEAD
gh pr create --title "feat: ..." --body "## Summary\n..." --draft
# curl fallback:
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d '{"title":"...","body":"...","head":"<branch>","base":"main"}'
```

### Monitor CI
```bash
gh pr checks --watch
# curl fallback: poll commit status every 30s
```

### Merge
```bash
gh pr merge --squash --delete-branch
gh pr merge --auto --squash --delete-branch  # auto-merge when green
```

### Quick Reference
| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl .../pulls?state=open` |
| View diff | `gh pr diff` | `git diff main...HEAD` |
| Add comment | `gh pr comment N --body "..."` | `curl POST .../issues/N/comments` |
| Request review | `gh pr edit N --add-reviewer user` | `curl POST .../requested_reviewers` |
| Check out PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N` |

---

## Pitfalls

- **Fine-grained token lists 0 repos**: Token prefix `github_pat_` → use classic `ghp_` token instead
- **Proxy needed in China**: Set `HTTPS_PROXY` before git/gh commands
- **MCP server config nesting**: `github:` must be direct child of `mcp_servers:`, not nested under `session_reset:`
- **Upstream clone local scripts**: Move custom scripts to `~/scripts/<project>/` to avoid git status noise
- **Batch clone**: Use `--depth 1` + category subdirectories (`~/code/learning/`, etc.)
- **MCP GitHub API 401 降级链**：当 `mcp_github_gov1_*` 返回 401 时，降级链为: (1) 先尝试 `gh CLI`（`gh search repos`，见 `references/github-ecosystem-research.md` §6）— 返回精确 JSON，与 MCP 等价；(2) 如果 gh 也失败，再使用 `web_extract` 抓取 GitHub 页面（近似值）。注意：web_extract 返回的是 LLM 总结值，非精确 API 值。详细方案见 `references/github-api-401-fallback.md`。
- **`gh repo view` 与 `gh search repos` 字段命名不一致**：两者对同一字段使用的 JSON 名不同：
  - `gh search repos --json stargazersCount` — `stargazersCount`（带 's'）
  - `gh repo view owner/repo --json stargazerCount` — `stargazerCount`（不带 's'）
  - 同理：`gh search repos --json forksCount`（带 's'）vs `gh repo view --json forkCount`（不带 's'）
  - 使用错误的字段名会报 `Unknown JSON field` 错误。这是因为 `gh search repos` 走的是 Search API（返回 `stargazers_count`/`forks_count`），而 `gh repo view` 走的是 GraphQL Repository 对象（返回 `stargazerCount`/`forkCount`），gh CLI 做了不同的 JSON 字段映射。
- **`gh search repos --topic` 用于生态研究**：搜索 GitHub topic 相关的仓库是最精准的生态盘点方式。例如 `gh search repos --topic hermes-agent --sort stars --limit 30 --json name,fullName,stargazersCount,description,language,updatedAt,url`。结合 `gh repo view owner/repo --json stargazerCount,forkCount,description,primaryLanguage,pushedAt,licenseInfo,createdAt,nameWithOwner` 获取单个仓库的详细信息。这两个命令组合可以完全替代 MCP GitHub 搜索工具。

## Verification

- [ ] `gh auth status` shows logged in (or git credential helper works)
- [ ] `hermes mcp test github` shows 26 tools (if MCP configured)
- [ ] `git ls-remote origin` works without password prompt
