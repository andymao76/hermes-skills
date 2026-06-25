---
name: domain-investigation-workflow
description: "Systematic multi-file investigation, learning, and knowledge base import for domain-specific technical documentation"
version: 1.0.0
author: agent-created
tags: [research, knowledge-base, import, learning, xmind, drawio, visio, pcap, markdown]
---

# Domain Investigation Workflow

Template for investigating, learning, and importing files from a directory into the knowledge base. Covers handling of diverse file formats encountered in technical documentation.

## Trigger Conditions

- User says "学习" (learn/study) files under a directory
- User points you at a folder of technical documents to understand
- User wants to import documents into the knowledge base
- User has a mix of file types (.md, .xmind, .drawio, .vsd, .pcap, .docx, .zip)

## Obvious Pitfalls

- **Skipping format conversion before content extraction** — Visio (.vsd) needs LibreOffice to PDF; draw.io (.drawio) needs deflate+base64+URL decode pipeline; XMind (.xmind) is a zip file with either content.xml (old) or content.json (new). Always check the actual file type first with `file` command, then pick the right parser.
- **Asking "can I proceed?"** — The user said to do it, so do it end-to-end in one turn. Don't stop mid-way to ask for confirmation.
- **Not checking modification times** — When multiple copies of the same file exist across directories, compare mtime and size to pick the latest.
- **Forgetting to refresh enzyme index after import** — Knowledge is not searchable until `enzyme refresh` runs.

## Step-by-Step Workflow

### Step 0: Understand Scope
Check if user said all files or specific files. Note: "学习" means learn AND potentially import. Ask if uncertain.

### Step 1: Discover Files
```bash
search_files(path="<directory>", pattern="*", target="files")
```
Note the count and types of files before proceeding.

### Step 2: Process Each File by Type

**Markdown (.md)**: Read directly with `read_file`. Extract key info. If already imported, note and skip.

**XMind (.xmind)**: These are zip files. Two internal formats:
- Old format: `content.xml` — XML with `urn:xmind:xmap:xmlns:content:2.0` namespace
- New format (2020+): `content.json` — JSON with `rootTopic` structure
- Parse via Python: `zipfile.ZipFile` → extract `content.json` or `content.xml` → recursively extract `title` from `rootTopic.children.attached[]`
- Documents can have multi-language warning strings at the root level — skip those, extract real content from `rootTopic`

**Draw.io (.drawio)**: Also zip/compressed XML.
- Check first bytes: `b'<mxfile'` = XML text format; binary garbage = compressed format
- XML text format: parse `value="..."` attributes from `mxCell` elements within the `<diagram>` compressed blob
- Compressed format: Extract content between `<diagram>` and `</diagram>`, then pipeline:
  ```python
  raw = base64.b64decode(compressed_text)
  xml_str = urllib.parse.unquote(zlib.decompress(raw, -zlib.MAX_WBITS).decode('utf-8'))
  ```
- Some files use binary encryption (starts with `b#eE`) — require password, cannot parse
- After extracting values, HTML-unescape and strip tags

**Visio (.vsd)**: Use LibreOffice headless conversion:
```bash
libreoffice --headless --convert-to pdf <file>.vsd --outdir /tmp/
pdftotext -layout <file>.pdf -
```

**Word (.docx)**: Use pandoc:
```bash
pandoc <file>.docx -t markdown --wrap=none -o <output>.md
```

**ZIP archives (.zip)**: First list contents, look for Chinese encoding issues:
```bash
unzip -l <file>.zip           # check file list
unzip -O gbk <file>.zip ...   # correct Chinese encoding
```

**pcap files**: Use tcpdump for overview, Python for structured decoding:
- Count packets, identify protocols, identify endpoints
- For Huawei LI packets: parse 14-byte LIRP header (AA + version + msg_type + length + LEAID), then BER decode
- Cross-reference with existing knowledge base for tag mapping

**PowerPoint (.pptx)**: Use python-pptx or LibreOffice conversion.

### Step 3: Extract and Summarize
For each file, extract key information. If multiple files form a set (e.g., OWLS system documentation), maintain cross-references between them in your summary.

### Step 4: Import to Knowledge Base
1. Create `~/knowledge/research/<topic>.md` with:
   - YAML frontmatter (tags, links to related knowledge files)
   - Structured markdown (tables for tabular data, sections for each subtopic)
   - Keep it concise but complete — capture the essence, not every word
2. For large multi-file sets, create a single comprehensive summary file plus individual files for detailed documents
3. Run `cd ~/knowledge && enzyme refresh` to update semantic index

### Step 5: Deliver Summary
Present a structured overview of what was learned in screen output. Use tables, bullet points, and clear organization. Don't just dump raw content.

## Multi-Format Document Processing

When a directory contains mixed formats (as often happens with OWLS/TMC/LIG documentation):

1. First do a `ls -la` to see all files and sizes
2. Separate into "already processed" vs "new" vs "cannot parse"
3. Process new files first, then report unparseable ones as status info
4. Create linking relationships between related documents in the knowledge base entry

## Knowledge Base Import Conventions

- Topic file path: `~/knowledge/research/<EnglishTopicDescription>.md`
- Use descriptive YAML title, not the raw file name
- Add links: `links: ["[[RelatedFile1]]", "[[RelatedFile2]]"]`
- Tag aggressively for discoverability
- For the enzyme index refresh, run from `~/knowledge/` directory
