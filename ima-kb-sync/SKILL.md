---
name: IMA KB Sync
version: 1.3.0
category: productivity
description: Bulk sync IMA knowledge bases to local, download PDFs, extract text, categorize content.
tags: [ima, knowledge-base, sync, pdf, extraction, 5g, telecom]
---

# IMA KB Sync

Bulk operations for IMA (腾讯IMA) knowledge bases: sync metadata to local, download PDFs with proper auth headers, extract text content, and organize into structured documents.

This skill complements the `ima-skill` (which handles individual API operations). This skill covers **bulk workflows** that span multiple KBs and items.

## Prerequisites

- IMA credentials at `~/.config/ima/client_id` and `~/.config/ima/api_key`
- `node` ≥ 18 (for `ima_api.cjs`)
- `poppler-utils` installed (`sudo apt-get install poppler-utils`) for `pdftotext`
- Python packages: `python-docx`, `python-pptx`, `openpyxl` (for DOCX/PPTX/XLSX extraction in Step 2)
- The ima-skill installed at `~/.hermes/skills/ima/`
- Write access to `~/knowledge/` (the Obsidian vault)

## 🔑 Credential Management

### API Key Expiry (`200002 skill auth failed`)

IMA API keys can expire. Symptom: `{"code":200002,"msg":"skill auth failed"}`.

**Fix (multi-machine):** If you have the same IMA account configured on another machine (e.g. Tencent Cloud), pull the working key:
```bash
ssh tencent "sudo cat /home/ubuntu/.config/ima/api_key" > ~/.config/ima/api_key
chmod 600 ~/.config/ima/api_key
```

**Fix (standalone):** Regenerate credentials from https://ima.qq.com/agent-interface and save to `~/.config/ima/`.

The `client_id` stays the same across machines for the same IMA account — only the `api_key` changes on expiry.

## Critical API Pitfalls

### 1. Finding ALL Knowledge Bases

| API | What it returns |
|-----|----------------|
| `get_addable_knowledge_base_list` | ONLY KBs you can ADD content to (excludes shared/subscribed) |
| `search_knowledge_base` with `query: ""` | ALL KBs the user has access to (personal + shared + subscribed) |

**Always use `search_knowledge_base` with empty query to enumerate all KBs.**

### 2. PDF Download Requires Headers

IMA PDF URLs are signed and require ALL headers from `url_info.headers`:
- `X-IMA-Create-URL-Time`
- `X-IMA-Platform`
- `X-IMA-Resource-Category`
- `X-IMA-Sign`
- `X-IMA-Trace-ID`
- `X-IMA-UID-SHA256`

Without these headers, curl returns empty/403. Always pass them with `-H` flags.

### 3. No Delete API

IMA OpenAPI has **no endpoint** to delete knowledge base items. Users must delete manually via the IMA web/app UI.

### 5. Node.js execSync stdout capture failure in Hermes agent context

When running inside a Hermes agent task or cron job, `child_process.execSync()` from a nested Node.js process may return empty stdout/stderr even on success (exit code 0). This is a known pipe IO issue.

**Fix:** Use the Python scripts instead. See `references/execsync-pitfall.md` for detailed reproduction and verification steps.

The Python equivalents are located at `~/.hermes/scripts/ima_kb_sync.py` and `~/.hermes/scripts/ima_kb_extract.py`.

The script at `~/.hermes/skills/ima/ima_api.cjs` automatically reads credentials from `~/.config/ima/`. No need to pass `options` JSON with clientId/apiKey — just call:

```bash
node ~/.hermes/skills/ima/ima_api.cjs "openapi/wiki/v1/search_knowledge_base" '{"query":"","limit":20}'
```

## 🚨 Mandatory Rule: Sync Must Include Content Download

**IMA knowledge base sync is NOT complete with metadata alone.** `.meta.json` files are intermediate artifacts — the actual syncing process is:
1. Fetch metadata → 2. **Download original files** → 3. **Extract text → 4. Generate Markdown notes in the Obsidian vault**

The pipeline is `ima_kb_sync.py` (metadata) → `ima_kb_extract.py` (download + convert). Both steps are required.

## Workflow: Full Sync Pipeline

### Single command

The recommended way is to run the cron job prompt directly (see [Cron Job](#cron-job) section below), or execute the two scripts in sequence:

```bash
# Step 1: Fetch latest metadata from IMA
python3 ~/.hermes/scripts/ima_kb_sync.py

# Step 2: Download files + extract text + generate markdown notes
python3 ~/.hermes/scripts/ima_kb_extract.py
```

> ⚠️ **Python scripts are preferred** over Node.js in Hermes agent contexts. The Node.js versions (`ima_kb_sync.js`) may fail due to `child_process.execSync` stdout capture issues (see `references/execsync-pitfall.md`). Python's `subprocess.run` does not have this issue.

### Step 1 — Metadata sync (`ima_kb_sync.py`)

```bash
python3 ~/.hermes/scripts/ima_kb_sync.py
```

Does:
- Enumerate all KBs via `search_knowledge_base`
- List content of each KB via `get_knowledge_list`
- Get media details via `get_media_info`
- Save `.meta.json` and `.url.txt` files locally (incremental — skips already-synced items via `.sync_state.json`)

Intermediate output: `~/knowledge/ima-sync/<KB-name>/<title>.meta.json`

### Step 2 — Content download & Obsidian conversion (`ima_kb_extract.py`)

```bash
python3 ~/.hermes/scripts/ima_kb_extract.py
```

Does:
1. Reads all `.meta.json` files from `~/knowledge/ima-sync/`
2. For each unsynced item, calls `get_media_info` API to get signed download URL
3. Downloads the file with proper auth headers (X-IMA-Sign, X-IMA-Create-URL-Time, etc.)
4. Extracts text based on file type
5. Generates structured Markdown notes with YAML frontmatter
6. Saves notes into categorized directories in the Obsidian vault
7. Tracks progress in `.download_state.json` (incremental — resumes on interruption)

### File type handling

| Type | media_type | Tool | Notes |
|------|-----------|------|-------|
| PDF | 1 | `pdftotext` (poppler-utils) | Good for text-based PDFs; limited for scanned/image-heavy |
| DOC/DOCX | 3 | `python-docx` | ⚠️ `.docx` only; legacy `.doc` fails silently |
| PPT/PPTX | 4 | `python-pptx` | Extracts slide text |
| XLSX | 7 | `openpyxl` | Tabular text with sheet headers |
| TXT | 8 | Direct read | Auto-detects UTF-8/GBK/GB2312/Big5 encoding |

### Output directory structure (in Obsidian vault)

```
~/knowledge/telecom/ima-articles/    ← Telecom/5G/IMS articles (53+ notes)
~/knowledge/ima-sync/notes/          ← General technical notes (18+ notes)
~/knowledge/ima-sync/downloads/      ← Raw downloaded files (PDF/DOCX/PPTX)
~/knowledge/ima-sync/                ← Metadata (.meta.json, .url.txt)
```

Topic categorization (keyword matching on title):
- **telecom** → `telecom/ima-articles/`: 5GC, SMF/AMF/UPF, IMS, VoLTE, SIP, SBC, LI/合法监听, LTE
- **general** → `ima-sync/notes/`: everything else

### Idempotency & resuming

Both scripts are idempotent — they track state in `.sync_state.json` and `.download_state.json`. Interrupted runs resume on re-execution. To force re-download:
```bash
rm -f ~/knowledge/ima-sync/.download_state.json
python3 ~/.hermes/scripts/ima_kb_extract.py
```

## File Locations

| File | Purpose |
|------|---------|
| `~/.hermes/scripts/ima_kb_sync.js` | Bulk metadata sync script (Node.js) |
| `~/.hermes/scripts/ima_kb_sync.py` | Bulk metadata sync script (Python — preferred in Hermes agent context) |
| `~/.hermes/scripts/ima_kb_extract.py` | Content download + text extraction + Obsidian markdown generation (Python) |
| `~/.hermes/scripts/ima_qa_extract.py` | QA extraction + categorization |
| `~/knowledge/ima-sync/` | Synced KB metadata (`.meta.json`) |
| `~/knowledge/ima-sync/downloads/` | Raw downloaded files |
| `~/knowledge/ima-sync/notes/` | General markdown notes from extraction |
| `~/knowledge/telecom/ima-articles/` | Telecom/5G/IMS categorised markdown notes (in Obsidian vault) |
| `~/.hermes/skills/ima/ima_api.cjs` | IMA API wrapper (auto-loads credentials) |

## Support Files

- `references/api-pitfalls.md` — IMA API quirks, media_type table, endpoint reference
- `scripts/ima_kb_sync.js` — Bulk metadata sync script (Node.js — use Python version in Hermes agent context)
- `scripts/ima_kb_sync.py` — Bulk metadata sync script (Python — preferred in Hermes agent context)
- `scripts/ima_kb_extract.py` — Content download + text extraction + Obsidian markdown (Python)
- `scripts/ima_qa_extract.py` — QA PDF extraction + categorization (Python)

## Multi-Instance Sync Safety

When the same IMA account is configured on multiple Hermes instances (e.g. local + Tencent Cloud):

- **IM direction**: Remote → Local only (pull from Tencent Cloud to local). Never push skills or knowledge from local to remote.
- **Restricted content (LI/OWLS)**: The following local-only content must NEVER be synced to the remote:
  - `knowledge/hi2/` — Huawei LI protocol docs (14 files)
  - `knowledge/telecom/lawful_interception/` — LI operation docs, ZTLIG config
  - `knowledge/research/OWLS_*` — OWLS system architecture
  - Skills: `huawei-hi2`, `zte-li`, `playwright-cli-openclaw`
- **Config**: Each instance maintains its own `config.yaml` independently. Do not merge configs across instances unless explicitly instructed.

## Cron Job

Cron job is the default operational mode for IMA sync. It ensures the full pipeline (metadata → download → convert) runs twice daily without manual intervention.

**Local (Hermes cron):**
```bash
hermes cron create \
  --name "IMA知识库同步" \
  --schedule "0 8,20 * * *" \
  --prompt '运行 IMA 知识库同步并提取内容到本地。

1. 先运行同步脚本拉取最新元数据：
```bash
python3 ~/.hermes/scripts/ima_kb_sync.py
```

2. 再运行提取脚本下载原文并转为 Markdown 笔记：
```bash
python3 ~/.hermes/scripts/ima_kb_extract.py
```

笔记会存到：
- ~/knowledge/telecom/ima-articles/ （电信技术文章）
- ~/knowledge/ima-sync/notes/ （通用技术笔记）

报告新增了多少笔记和下载的文件数。如果无新增则简要汇报即可。' \
  --toolsets terminal,file
```

The cron job uses the Python script by default to avoid Node.js execSync issues. Job output is delivered to the origin platform.
