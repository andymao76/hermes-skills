# SkillsMP — Alternative Skill Registry

SkillsMP (skillsmp.com) is the largest agent skill aggregator with **1.5M+ skills** indexed from public GitHub repos. Each entry is from a repo with at least 2 stars.

## Search via Web

Since SkillsMP is JS-heavy and cannot be browsed via `web_extract` or curl reliably, use these approaches:

### Approach 1: Search engine (recommended)
```bash
web_search("site:skillsmp.com <keyword> skill")
```

### Approach 2: SkillsMP API (if available)
```bash
GET https://skillsmp.com/api/v1/skills?sort=popular&limit=20&q=<keyword>
```
Note: API stability is not guaranteed — it's an independent community project.

## Raw URL Detection from SkillsMP Results

SkillsMP shows `author` + `name` mapping. To install via Hermes:
1. Search for the skill on GitHub directly
2. Find the raw SKILL.md URL
3. Use `hermes skills install <raw-url> --name <name> --force`

## Known Featured Skills (from skillsmp.com homepage)

| Skill | Author | Installs | Status | 
|---|---|---|---|
| frontend-design | anthropics/claude-code | 139.6K | Built-in |
| skill-creator | anthropics/skills | 139.6K | Installed |
| brainstorming | obra/superpowers | 203.9K | Built-in |
| ppt-generation | bytedance/deer-flow | 69.3K | Not installed — needs deer-flow workspace |
| browser-use | browser-use | 95.2K | Not installed — Python lib, use via script |
| docx | anthropics/skills | 139.6K | python-docx skill already installed |
| code-reviewer | Shubhamsaboo | 111.3K | Overlaps with github-code-review |

## Mass Install from Skills.sh — Timeout Handling

When `npx skills search` or `hermes skills install` times out repeatedly:

### Symptom
- Command exits with code 124 after 30-60s
- `hermes skills list` shows no new entries
- `find ~/.hermes/skills -name "SKILL.md" -mmin -5` returns nothing

### Causes
- Large repos with git clone + pip dependency install
- Network latency to GitHub raw URLs through proxy
- `npx` installing npm package + fetching catalog simultaneously

### Fix Options

1. **Split into small batches** — Install 1-2 at a time, not 8-10
2. **Timeout increase** — Use `hermes skills install` which has a longer default timeout than `npx`
3. **Fallback: Manual install** — Create SKILL.md directly with `write_file`:
   ```bash
   write_file(path="~/.hermes/skills/<category>/<name>/SKILL.md", content="...")
   ```
   Extract content via `web_extract` from the raw GitHub URL, or author from knowledge.
4. **Skip pip-autoinstall** — Hermes skills install tries to `pip install` dependencies from SKILL.md frontmatter. If this hangs, install the SKILL.md manually.
5. **Verify silently** — After a timeout, always check `hermes skills list | grep <name>` — the install may have succeeded before the timeout fired.
