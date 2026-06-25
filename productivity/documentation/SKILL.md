---
name: documentation
description: Write and maintain technical documentation. Trigger with "write docs for", "document this", "create a README", "write a runbook", "onboarding guide", or when the user needs help with any form of technical writing — API docs, architecture docs, or operational runbooks.
---

# Technical Documentation

Write clear, maintainable technical documentation for different audiences and purposes.

## Document Types

### README
- What this is and why it exists
- Quick start (< 5 minutes to first success)
- Configuration and usage
- Contributing guide

### API Documentation
- Endpoint reference with request/response examples
- Authentication and error codes
- Rate limits and pagination
- SDK examples

### Runbook
- When to use this runbook
- Prerequisites and access needed
- Step-by-step procedure
- Rollback steps
- Escalation path

### Architecture Doc
- Context and goals
- High-level design with diagrams
- Key decisions and trade-offs
- Data flow and integration points

### Onboarding Guide
- Environment setup
- Key systems and how they connect
- Common tasks with walkthroughs
- Who to ask for what

## Principles

1. **Write for the reader** — Who is reading this and what do they need?
2. **Start with the most useful information** — Don't bury the lede
3. **Show, don't tell** — Code examples, commands, screenshots
4. **Keep it current** — Outdated docs are worse than no docs
5. **Link, don't duplicate** — Reference other docs instead of copying

## Markdown → PDF Rendering

Two pipelines depending on document complexity:

**Pipeline A (markdown → pandoc → PDF):** For plain-text documents with headings/code/tables.
Use the three-step process below (pandoc to HTML, inject CSS, chromium to PDF).

**Pipeline B (HTML-first → PDF):** For documents with inline SVG diagrams, complex multi-page
layouts, color-coded architecture sections, or structured reports. Design the document directly
in HTML with CSS `@page` rules and `page-break-after: always` for per-topic pagination.
Then use `--print-to-pdf` from headless Chrome. The HTML is the editable source; the PDF is
the deliverable. Chinese fonts (Noto Sans CJK SC) embed natively. See
`references/md-to-pdf-rendering.md` for the full CSS, color theme mapping, and verification steps.

Pipeline A (common case):

```bash
# Step 1: Pandoc to HTML (handles markdown→structure)
pandoc input.md -f markdown -t html5 -o /tmp/output.html

# Step 2: Inject CSS for Chinese readability, page layout, code blocks
# Critical CSS properties: font-family for CJK, pre/table styling, page width

# Step 3: Chromium headless → PDF (snap chromium needs file:// URI)
chromium --headless --disable-gpu --no-sandbox \
  --print-to-pdf=/home/andymao/Documents/output.pdf \
  "file:///tmp/output.html"
# Note: --print-to-pdf path must be writable (output file in ~/Documents/ works)

# PDF verification: pdfinfo <file.pdf> | grep -E "Pages|Page size"
```

**Known pitfalls**:
- Snap chromium sandbox blocks writing to `/tmp/` — use `~/Documents/` as output target
- Markitdown CSS auto-injection: read pandoc output, replace `</head>` with `<style>...</style></head>`
- Chinese fonts: include `'Noto Sans SC', 'Microsoft YaHei', 'PingFang SC'` in font-family stack
- Code blocks: add `border-left: 3px solid #2c5f8a` for visual distinction, `white-space: pre-wrap` for overflow
- Tables: `th { background: #2c5f8a; color: #fff; }` for header styling
- Page size: Chromium defaults to Letter (612x792 pt) — use CSS `@page { size: A4; }` if needed
