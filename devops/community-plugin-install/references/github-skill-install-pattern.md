# GitHub Skill Install Patterns

Common patterns encountered when installing community SKILL.md files into Hermes.

## Path Variants

Not every GitHub repo stores SKILL.md at the root. Common paths found in real repos:

| Repository | Path to SKILL.md | Notes |
|---|---|---|
| **lugasia/3gpp-skill** | `./SKILL.md` (root) | Simple single-skill repo |
| **anthropics/financial-services** | `plugins/agent-plugins/<agent>/skills/<name>/SKILL.md` | Multi-agent plugin structure |
| **wshobson/agents** | `plugins/<domain>/skills/<skill-name>/SKILL.md` | Multi-domain, multi-skill monorepo |
| **binance/binance-skills-hub** | `skills/binance/binance/SKILL.md` | Nested category structure |
| **an略/...** | files within `.claude-plugin/` | Claude Code plugin format |
| **mindrally/skills** | `./<skill-name>/SKILL.md` or `./skills/<skill>/SKILL.md` | Flat or nested |
| **vllm-project/vllm-skills** | `plugins/vllm-skills/skills/<name>/SKILL.md` | Plugin-wrapped skills |

## Default Branch Detection

Many repos default to `master` rather than `main`. Always verify before constructing raw URLs:

```bash
# Check default branch
curl -sL https://api.github.com/repos/<owner>/<repo> | python3 -c "
import sys, json
print(json.load(sys.stdin).get('default_branch', 'unknown'))
"
```

## Directory Listing

When SKILL.md is not at an obvious path:

```bash
# List repo root (returns array of {type: "file"|"dir", name: ...})
curl -sL https://api.github.com/repos/<owner>/<repo>/contents/

# List subdirectory
curl -sL https://api.github.com/repos/<owner>/<repo>/contents/skills

# Recursive tree listing (most powerful — returns ALL files with paths)
curl -sL https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1 | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('tree',[]):
    if 'SKILL.md' in item['path']:
        print(f\"  {item['path']}\")
"
```

## Hermes Security Scanner Quirks

- `Verdict: SAFE` → installs automatically
- `Verdict: CAUTION` → blocked by default, use `--force` to override
- `Verdict: DANGEROUS` → `--force` does NOT override
- Skills containing shell commands, file writes, or network calls are more likely to get CAUTION/DANGEROUS verdicts
- Anthropic/nvdia/binance official repos are always safe

## npx skills add vs hermes skills install

`npx skills add <owner/repo@skill>` installs into the Claude Code/Cursor ecosystem
(.claude/skills/ or .cursor/skills/). `hermes skills install <url>` installs into
`~/.hermes/skills/`. They are NOT interchangeable — npx will not make the skill
visible to Hermes. The npx tool is useful only for discovery (search, install counts);
actual installation should always use `hermes skills install` with the raw GitHub URL.

## Failed Install Recovery

When `hermes skills install` gets interrupted (timeout, ^C):

```bash
# Check if the partial install left residual files
find ~/.hermes/skills -name "SKILL.md" -mmin -5

# Retry with the raw URL. Hermes is idempotent on re-install.
hermes skills install <url> --name <name> --category <cat> --force

# If the skill name collides, Hermes may rename it. Check with find.
```
