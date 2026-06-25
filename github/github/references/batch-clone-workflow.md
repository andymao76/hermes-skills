# Batch Clone + Scan + Summarize Workflow

Use this pattern when the user asks to download multiple GitHub repos and organize them into a local codebase with knowledge base summaries.

## Workflow Steps

### 1. Create Category Directories

```bash
# Group by type
mkdir -p ~/code/{learning,awesome-lists,platforms,tools,libraries}
```

### 2. Clone with Proxy (if needed)

```bash
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897

git clone --depth 1 https://github.com/owner/repo.git category/repo
```

Use `--depth 1` for all clones — they're for reference, not development.

### 3. Scan Project Structures

Use `delegate_task` with a subagent to scan all projects in parallel:

- For each project: `ls -la`, `find -maxdepth 2` for directory tree, read `package.json`/`README.md` for tech stack
- Aggregate results into a markdown report

### 4. Save to Knowledge Base

```bash
# Write report
~/knowledge/research/github-<topic>-codebase.md

# Refresh enzyme index
cd ~/knowledge && enzyme refresh
```

## Example Structure

```text
~/code/
├── learning/          # Tutorials, courses, educational content
├── awesome-lists/     # Curated lists, API directories
├── platforms/         # Full platform/application code
└── tools/             # CLI tools, utilities
```

## Summary Report Format

For each project, capture:
- Name, stars count, owner
- Description and purpose
- Tech stack (languages, frameworks, build tools)
- Top-level directory structure (1-2 levels deep)
- Size (disk usage)
- Whether it's documentation-only or actual code
