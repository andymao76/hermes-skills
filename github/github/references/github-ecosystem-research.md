# GitHub Ecosystem Research Workflow

Systematic approach to discovering, extracting, and structuring knowledge from GitHub projects.

## 1. Search Discovery

```bash
# Basic search — gets fullName, description, stargazersCount, language, url, updatedAt
gh search repos "<topic>" --limit 20 \
  --json fullName,description,owner,language,stargazersCount,forksCount,updatedAt,url

# Dual-query strategy for broad ecosystem coverage:
# Query 1: exact name match
gh search repos "<product-name>" --limit 20 --sort stars --json name,owner,stargazersCount,description,url 2>&1
# Query 2: natural language match (catches repos that mention it in description only)
gh search repos "<product-name> agent" --limit 20 --sort stars --json name,owner,stargazersCount,description,url 2>&1
# Combine and deduplicate results by URL/fullName

# With gh api for more complex queries
gh api "/search/repositories?q=<topic>&sort=stars&per_page=20&order=desc" \
  --jq '.items[] | {full_name, description, stargazers_count, language, html_url, updated_at}'
```

**Available JSON fields for `gh search repos`:** `createdAt`, `defaultBranch`, `description`, `forksCount`, `fullName`, `hasDownloads`, `hasIssues`, `hasPages`, `hasProjects`, `hasWiki`, `homepage`, `id`, `isArchived`, `isDisabled`, `isFork`, `isPrivate`, `language`, `license`, `name`, `openIssuesCount`, `owner`, `pushedAt`, `size`, `stargazersCount`, `updatedAt`, `url`, `visibility`, `watchersCount`

## 2. README Extraction

### Method A: gh API + base64 (full content, no truncation)
```bash
# Get the complete README (49KB+ files work fine)
gh api repos/<owner>/<repo>/contents/README.md --jq '.content' | \
  base64 -d > /tmp/full_readme.md

# Get file size first
gh api repos/<owner>/<repo>/contents/README.md --jq '.size'
# returns size in bytes — if > 5000, you NEED this method
```

### Method B: web_extract (simple, truncates at ~5000 chars)
```python
from hermes_tools import web_extract
result = web_extract(urls=["https://github.com/owner/repo"])
# For raw markdown: https://raw.githubusercontent.com/owner/repo/main/README.md
```

**Why web_extract may not suffice:** `web_extract` summarizes pages over ~5000 chars via LLM, losing details. The GitHub API returns the raw base64-encoded content without truncation.

## 3. Resource Download

```bash
# Download release assets
gh release download -R <owner>/<repo> -p "*.pdf" -D /target/dir

# Download specific files from repo root
curl -sL -o /target/file.pdf \
  "https://github.com/<owner>/<repo>/raw/main/path/to/file.pdf"

# Download via gh (no redirect issues)
gh api repos/<owner>/<repo>/contents/path/to/file.pdf --jq '.download_url' | \
  xargs curl -sL -o /target/file.pdf
```

## 4. Knowledge Base Structuring

For each project, capture:
- **Repository** — fullName, stars, language, license
- **Description** — what it does, key differentiator
- **Setup** — installation steps, dependencies, config
- **Usage patterns** — CLI commands, code examples
- **Pitfalls** — known issues, missing deps, anti-patterns

**Organize by category** (core/web-ui/learning/ecosystem-tools) rather than listing flat.

## 5. Cron Job Pattern for Periodic Updates

```python
cronjob(
    action="create",
    name="GitHub <topic> ecosystem search",
    prompt="Search GitHub for '<topic>' repos... (self-contained research task)",
    schedule="0 10 */3 * *",  # every 3 days at 10:00
    skills=["github-pr-workflow"],
    deliver="origin",
)
```

## 6. Fallback Chain: When GitHub MCP Returns 401

MCP GitHub 使用独立配置的 token，可能因过期/权限不足返回 401。**此时 `gh CLI` 可能仍能正常工作**（因为使用不同的凭证/scope）。推荐的降级链：

### Level 1: gh CLI（最佳替代）

```bash
# gh auth 通常使用 keyring 或不同 scope 的 token
gh auth status
# 如果正常，直接使用 gh search repos 替代 MCP
gh search repos "<query>" --limit 20 --sort stars --json name,owner,stargazersCount,forksCount,description,url,updatedAt
```

**优势：** 返回精确结构化的 JSON 数据，可按 stars 排序，与 MCP 搜索结果几乎一致。

### Level 2: web_extract + web_search_plus（最后手段）

当 `gh` 也返回 401 时（极少见），使用 web 搜索获取近似值：

```python
from hermes_tools import web_search_plus, web_extract, read_file, write_file

# 1. 搜索获取仓库列表
results = web_search_plus(query="site:github.com \"hermes-agent\" stars 2025")
# 2. web_extract 逐个抓取页面获得详细信息
data = web_extract(urls=["https://github.com/NousResearch/hermes-agent"])
# 3. 与知识库比对、更新
# 4. 写报告
```

**关键差异：**
- web_search_plus 返回的是文本搜索结果，非结构化 JSON
- web_extract Stars 是近似值（如 `194k`），非精确整数
- 无法按 stars 排序，需手动提取后比较

完整示例见 `references/github-api-401-fallback.md`。

| Operation | Command |
|-----------|---------|
| Search repos | `gh search repos "<query>" --limit N --json fullName,stargazersCount,forksCount,description,language,updatedAt,url` |
| Get full README | `gh api repos/o/r/contents/README.md --jq '.content' \| base64 -d` |
| Check file size | `gh api repos/o/r/contents/README.md --jq '.size'` |
| List releases | `gh release list -R o/r` |
| Download asset | `gh release download -R o/r -p "*.pdf"` |
| Raw file | `curl -sL "https://github.com/o/r/raw/main/path"` |
| Repo metadata | `gh repo view o/r --json description,language,stargazersCount` |
