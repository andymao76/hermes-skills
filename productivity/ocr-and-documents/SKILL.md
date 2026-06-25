---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF, Document & Screenshot Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
For **screenshots / images containing text**: use `vision_analyze` (Hermes-native, zero-install, model sees the image directly — best for OCR on screenshots, handwritten notes, diagrams with labels).
This skill covers **PDFs and scanned documents** (file-based extraction).
**Do NOT use these PDF tools for screenshots or image files** — vision_analyze is faster, more accurate, and requires no dependencies.

## Step 0: Archive Extraction (RAR / ZIP / 7z)

Before extracting document content, you may need to unpack archives.

### RAR archives (`.rar`)

`unrar` is NOT pre-installed on most Ubuntu systems. If `unrar` or `7z` is missing:

```bash
# Quick check
which unrar 7z 7za

# Workaround: install unrar without sudo via apt download + dpkg-deb
cd /tmp
apt download unrar
mkdir -p unrar_extract
dpkg-deb -x unrar_*_amd64.deb unrar_extract/
cp unrar_extract/usr/bin/unrar-nonfree ~/.local/bin/unrar
chmod +x ~/.local/bin/unrar

# Verify
~/.local/bin/unrar 2>&1 | head -3

# Extract
export PATH="$HOME/.local/bin:$PATH"
unrar x -o+ archive.rar output_dir/
```

**Pitfalls**:
- `pip install rarfile` alone is NOT sufficient — it's a Python wrapper that still requires the `unrar` binary
- `pip install unrar` may compile from source and fail without the right build deps
- `apt download` only works when the package is in enabled repos (needs `multiverse` for `unrar`)
- The binary inside the .deb is named `unrar-nonfree`, not `unrar` — rename it when copying
- RAR archives from Windows sources may have GBK-encoded filenames; `unrar x` handles this automatically (unlike `unzip` which needs `-O gbk`)

### ZIP archives (`.zip`)

Standard `unzip` is usually installed. For Chinese filenames from Windows sources:

```bash
unzip -O gbk file.zip -d output_dir
```

### Python fallback for RAR listing (no extraction)

```python
import rarfile
rf = rarfile.RarFile('archive.rar')
for f in rf.infolist():
    print(f.filename, f.file_size)
```

Full extraction still requires the `unrar` binary.

---

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor
## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | markitdown (light) | marker-pdf (~3-5GB) |
|---------|-----------------|-------------------|---------------------|
| **Text-based PDF** | ✅ | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (good) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ❌ | ✅ |
| **Code blocks** | ❌ | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ❌ | ✅ |
| **Reading order detection** | ❌ | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ | ✅ (with context) |
| **Markdown output** | ✅ (pymupdf4llm) | ✅ (native) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~2MB (无GPU) | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~0.3s/page | ~1-14s/page (CPU) |
| **ASN.1 / technical tables** | ❌ | ✅ | ✅ |

**Decision tree:**
- **Screenshot / image with text → vision_analyze** (Hermes-native, no deps, model sees the image)
- Text-only PDF → **pymupdf** (instant, no deps)
- Complex technical docs (ASN.1, ISUP tables, protocol specs) → **markitdown** (lightweight, preserves structure)
- Scanned/OCR needed → **marker-pdf** (heavy, needs ~5GB)

### ⚙️ Vision Analyzer Configuration (vision_analyze)

Hermes 的 `vision_analyze` 工具由 `auxiliary.vision` 配置段控制，**默认 `provider: auto` 会回退到主模型提供商**。DeepSeek 的视觉模型在中国大陆返回 403（区域限制），因此必须显式指定视觉提供商。

**修复命令**（2026-06-09 验证通过）：

```bash
hermes config set auxiliary.vision.provider siliconflow
hermes config set auxiliary.vision.model "Qwen/Qwen3-VL-30B-A3B-Instruct"
```

**已验证的模型**：`Qwen/Qwen3-VL-30B-A3B-Instruct`（SiliconFlow 平台）
- ✅ 中文标题 + 表格（4列×10行）全部正确提取
- ✅ 结论和注释完整保留
- ⚠️ 特殊 Unicode 符号（如 ★ 星级）可能被视觉编码器误读为数字
- 速度：~30s（含首次冷启动）

**⚠️ 配置路径陷阱**：

```bash
# ❌ 错误 — 会在 config.yaml 根级追加重复 key（不生效）
hermes config set vision.provider siliconflow

# ✅ 正确 — 必须带 auxiliary 前缀
hermes config set auxiliary.vision.provider siliconflow
```

可用视觉模型清单（SiliconFlow 2026-06）：
- `Qwen/Qwen3-VL-32B-Instruct`（最大，精度最高）
- `Qwen/Qwen3-VL-30B-A3B-Instruct`（推荐，速度/精度平衡）
- `Qwen/Qwen3-VL-8B-Instruct`（最快）
- `Qwen/Qwen3-VL-32B-Thinking` / `Qwen/Qwen3-VL-30B-A3B-Thinking`（推理增强）

**markitdown installed**: `markitdown[pdf]` at `~/.local/bin/markitdown`. For `.docx`: `markitdown[docx]` adds mammoth+lxml support. Tested on Chinese-language 259-page LI spec and 3GPP docs (translated tables fine, code blocks as text, ASN.1 PER syntax extracted correctly).

**3GPP spec download + convert workflow**:

## markitdown (Microsoft) — lightweight for complex PDFs

```bash
pip install markitdown[pdf]           # ~10MB, no GPU needed
markitdown document.pdf > output.md   # CLI usage
```

**Best for**: Technical protocol documents (ASN.1 PER definitions, ISUP parameter tables, 3GPP specs, LI interface manuals). Preserves table structures and ASCII-formatted specs better than pymupdf's get_text(). Tested on 259-page Huawei LI-HW specification — full ASN.1 Chapter 12 extraction worked correctly.

**3GPP spec download + convert workflow** (validated in session 20260608):
1. Find the latest ZIP on 3GPP dynamic report page: `https://www.3gpp.org/dynareport/<spec_number>.htm`
2. Download ZIP from 3GPP FTP: `https://www.3gpp.org/ftp/Specs/archive/33_series/<spec_number>/<file>.zip`
   - Release suffix: `-i00`=R19, `-h00`=R18, `-g00`=R17, version letter ascends with Release number
3. Unzip → `.docx` (main doc, in newer releases) or `.doc` (older releases) + `attachments.zip` (ASN.1 `.asn` files)
4. If older `.doc` format: `libreoffice --headless --convert-to docx input.doc` first
5. Convert docx: `markitdown spec.docx > spec.md` (install `markitdown[docx]` for docx support first: `pip install markitdown[docx]`)
6. Extract ASN.1 attachments: `unzip attachments.zip -d asn1/`
7. Store: `~/knowledge/3gpp-<spec>/` + README.md with summary table and OID tree
8. Prefer 3GPP FTP over ETSI direct links — ETSI returns 35KB redirect pages, not real PDFs

**Examples**: TS 33.108 V18.0.0 → 787KB md + 19 ASN.1 files. TS 33.127 V18.0.0 → 349KB md. TS 33.126 V18.0.0 → 51KB md.

**Limitations**: No OCR, no equation/LaTeX support, no layout analysis.

**⚠️ Known caveats:**
- `.doc` (OLE2/Word 97-2003 format) is NOT natively supported. Use `libreoffice --headless --convert-to docx input.doc` first, then `markitdown input.docx`. LibreOffice is pre-installed in most Ubuntu desktops.
- `markitdown` fails on 3GPP-style `.doc` files with OLE2 Composite Document File V2 format. Solution: install libreoffice (`libreoffice-core`), convert before piped to markitdown.
- Tables in docx markitdown output are rendered as markdown tables but may lose multi-row/merged-cell structure. For complex tables, verify output and consider `pandoc` as alternative.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
