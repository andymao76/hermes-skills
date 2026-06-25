---
name: python-docx
description: "Generate professionally formatted Word (.docx) documents using python-docx — tables, headings, Chinese fonts, multi-column layouts, and structured content from research/analysis."
version: 1.1.0
author: assistant
license: MIT
tags: [Documents, Word, python-docx, Report-Generation, Chinese-Documents]
---

# python-docx — Professional Word Document Generation

Generate `.docx` documents with professional formatting using the `python-docx` library. Use this skill when the user asks for a Word document (.docx), a formatted report, or a deliverable document.

## Prerequisites

```bash
pip install python-docx
# or: uv pip install python-docx
```

## Core Pattern

Always create a standalone Python script that:
1. Creates a `Document()` object
2. Configures global styles and page margins
3. Builds content programmatically
4. Saves to the user's home directory (`~/`)

Execute the script via `terminal()` and verify the output file exists.

## Template Script

Always use the per-run font helper pattern, NOT just style-level font setting:

```python
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

doc = Document()

# ── Style-level (cosmetic only, NOT sufficient for Chinese font) ──
style = doc.styles['Normal']
style.font.name = 'Arial'
style.font.size = Pt(11)

# ── Per-run font helper (REQUIRED for Chinese to render) ──
def set_cn_font(run, cn_font='SimSun', en_font='Arial'):
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), cn_font)
    rFonts.set(qn('w:ascii'), en_font)
    rFonts.set(qn('w:hAnsi'), en_font)
    rFonts.set(qn('w:cs'), en_font)

def add_run(p, text, bold=False, size=None, color=None, cn_font='SimSun', en_font='Arial'):
    run = p.add_run(text)
    run.bold = bold
    if size: run.font.size = Pt(size)
    if color: run.font.color.rgb = color
    set_cn_font(run, cn_font, en_font)
    return run

def add_heading_safe(doc, text, level=1):
    try:
        h = doc.add_heading(text, level=level)
        for run in h.runs:
            set_cn_font(run, 'SimHei', 'Arial')
        return h
    except KeyError:
        p = doc.add_paragraph()
        add_run(p, text, bold=True, size=16 if level==1 else 14)
        return p

# Page margins (default 2.54cm → custom)
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# === USE add_run() FOR ALL TEXT ===
add_heading_safe(doc, '文档标题', 1)
p = doc.add_paragraph()
add_run(p, '中文正文内容', size=11)
```

## Chinese Document Best Practices

### Critical: Per-Run Font Setting (NOT just style-level)

**Style-level font setting is insufficient.** Setting `style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')` on the Document style does NOT reliably render Chinese — the output opens garbled. The font must be set on EVERY run via XML.

Use this helper and call it for EVERY `add_run()`:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cn_font(run, cn_font='SimSun', en_font='Arial'):
    """Set Chinese font on a run via XML (style-level is NOT enough)."""
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), cn_font)
    rFonts.set(qn('w:ascii'), en_font)
    rFonts.set(qn('w:hAnsi'), en_font)
    rFonts.set(qn('w:cs'), en_font)

def add_run(p, text, bold=False, size=None, color=None, cn_font='SimSun', en_font='Arial'):
    """Add a run with proper Chinese font. USE THIS for ALL text."""
    run = p.add_run(text)
    run.bold = bold
    if size: run.font.size = Pt(size)
    if color: run.font.color.rgb = color
    set_cn_font(run, cn_font, en_font)
    return run
```

### Heading Helper

Headings also need per-run font fixing:

```python
def add_heading_safe(doc, text, level=1):
    try:
        h = doc.add_heading(text, level=level)
        for run in h.runs:
            set_cn_font(run, 'SimHei', 'Arial')
        return h
    except KeyError:
        p = doc.add_paragraph()
        add_run(p, text, bold=True, size=16 if level==1 else 14)
        return p
```

### Table Cell Text

Tables also need explicit font on each cell's paragraph run:

```python
cell = table.rows[0].cells[0]
cell.text = ''
p = cell.paragraphs[0]
add_run(p, '表头', bold=True, size=10, cn_font='SimHei')
```

### Font Recommendations

| Usage | cn_font | en_font | Notes |
|-------|---------|---------|-------|
| Body text | SimSun (宋体) | Arial | Best for long-form Chinese |
| Headings | SimHei (黑体) | Arial Bold | Bold sans-serif for titles |
| Code/inline | SimSun | Consolas | Monospace CJK limited |

### Page Breaks
```python
doc.add_page_break()
```

## Common Building Blocks

### 1. Headings
```python
def add_heading(doc, level, text, color=RGBColor(0x1A, 0x1A, 0x2E)):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = color
    return h
```

### 2. Paragraphs with Mixed Formatting
```python
def para(text, bold=False, color=None, size=None, align=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    run = p.add_run(text)
    run.bold = bold
    if color: run.font.color.rgb = color
    if size: run.font.size = Pt(size)
    return p
```

### 3. Bullet Lists
```python
def bullet(text, level=0):
    p = doc.add_paragraph(text, style='List Bullet')
    if level > 0:
        p.paragraph_format.left_indent = Cm(1.5 * level)
    return p
```
### 4. Styled Tables

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, color_hex):
    """Set cell background color (e.g. '1E3A5F' for navy blue)"""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color_hex)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)

def create_table(doc, headers, rows, header_color='1E3A5F', alt_row_color='EDF2F7'):
    table = doc.add_table(rows=1+len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Header row
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(10)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_shading(cell, header_color)
    # Data rows with alternating background
    for ri, row_data in enumerate(rows):
        row = table.add_row()
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            cell.text = ''
            run = cell.paragraphs[0].add_run(str(val))
            run.font.size = Pt(9.5)
            if ri % 2 == 1:
                set_cell_shading(cell, alt_row_color)
    return table
```

### 6. Cover / Title Page

For professional documents, create a centered title page with version info.
**Important:** Use the `add_run()` helper (not bare `run = p.add_run()`) for Chinese text:

```python
# Add blank lines for vertical centering
for _ in range(6):
    doc.add_paragraph()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(title, '文档标题', bold=True, size=28, color=RGBColor(0x1E, 0x3A, 0x5F))

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(sub, 'V4.0 · 2026-06-11', size=16, color=RGBColor(0x47, 0x56, 0x69))

info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(info, '副标题行', size=12, color=RGBColor(0x64, 0x74, 0x8B))

doc.add_page_break()
```

### 7. Version History Table

For documents with revision tracking:

```python
doc.add_heading('版本变更记录', level=2)
add_table(
    ['版本', '日期', '变更内容'],
    [
        ['V1.0', '2026-06-05', '初始版本'],
        ['V2.0', '2026-06-10', '新增 XX 模块'],
        ['V3.0', '2026-06-11', '架构重构'],
    ]
)
```

## Full Script Template

```python
#!/usr/bin/env python3
"""Generate Word document with proper Chinese font rendering"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

doc = Document()

# ── Style-level (cosmetic only) ──
style = doc.styles['Normal']
style.font.name = 'Arial'
style.font.size = Pt(11)

# ── Per-run Chinese font (REQUIRED) ──
def set_cn_font(run, cn_font='SimSun', en_font='Arial'):
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), cn_font)
    rFonts.set(qn('w:ascii'), en_font)
    rFonts.set(qn('w:hAnsi'), en_font)
    rFonts.set(qn('w:cs'), en_font)

def add_run(p, text, bold=False, size=None, color=None):
    run = p.add_run(text)
    run.bold = bold
    if size: run.font.size = Pt(size)
    if color: run.font.color.rgb = color
    set_cn_font(run)
    return run

def add_heading_safe(doc, text, level=1):
    try:
        h = doc.add_heading(text, level=level)
        for run in h.runs:
            set_cn_font(run, 'SimHei', 'Arial')
        return h
    except KeyError:
        p = doc.add_paragraph()
        add_run(p, text, bold=True, size=16 if level==1 else 14)
        return p

def set_cell_shading(cell, color_hex):
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color_hex)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)

def add_table(doc, headers, rows, header_color='1E3A5F', alt_color='EDF2F7'):
    """Safe table builder. Headers count MUST match each row's length."""
    ncols = len(headers)
    table = doc.add_table(rows=1+len(rows), cols=ncols)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]; cell.text = ''
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_run(p, h, bold=True, size=10, color=RGBColor(0xFF,0xFF,0xFF))
        set_cell_shading(cell, header_color)
    for ri, row_data in enumerate(rows):
        row = table.add_row()
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]; cell.text = ''
            add_run(cell.paragraphs[0], str(val), size=9.5)
            if ri % 2 == 1: set_cell_shading(cell, alt_color)
    return table

# Page margins
for section in doc.sections:
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
```

```python
# === CONTENT: add your headings, paragraphs, tables here ===
# (use the building blocks above)

# === SAVE ===
output_path = os.path.expanduser('~/文档名称.docx')
doc.save(output_path)
print(f'Saved: {output_path} ({os.path.getsize(output_path)} bytes)')
```

该用户的 Smartbrain 系统文档约定：
1. **封面 + 版本历史** 在最前
2. **系统架构图（含图1）** 作为第一章
3. **业务处理流程图（含图2 + 架构说明）** 作为第二章
4. 文字内容章节从第三章开始
5. 新版本号递增（V1.0 → V1.1 → V2.0）

当生成系统架构文档时，始终将可视化图表放在文字内容之前。

## 跨 Skill 协作：HTML 图表 → DOCX

当需要生成系统架构图/流程图并嵌入 DOCX 时的工作流：

1. 用 `architecture-diagram` skill 生成纯 SVG HTML 文件
2. 独立创建两个 HTML（架构图 + 流程图），各自有独立的 viewBox 尺寸
3. 用 `google-chrome-stable --headless --no-sandbox --disable-gpu --screenshot=file.png --window-size=W,H file:///path.html` 将 HTML 渲染为 PNG
4. 用 `python-docx` skill 的 `add_picture()` 将 PNG 插入文档
5. 图片宽度常用 `Cm(15.5)` 或 `Inches(5.8)`，居中放置（`WD_ALIGN_PARAGRAPH.CENTER`）
6. 图片上方加编号标题行（`图1: ...`），字体 10pt，灰色

## Pitfalls

- **add_heading 失败**: 当源文档的样式系统与代码期望不一致时，`doc.add_heading(text, level=1)` 可能抛出 KeyError。使用安全的包装函数：
  ```python
  def add_heading_safe(doc, text, level=1):
      try:
          return doc.add_heading(text, level=level)
      except KeyError:
          p = doc.add_paragraph()
          run = p.add_run(text)
          run.bold = True
          run.font.size = Pt(16 if level==1 else 14)
          run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
          return p
  ```
- **East Asian font NOT set per-run** → Chinese text renders as boxes/乱码 on user's machine. Style-level `style.element.rPr.rFonts.set(qn('w:eastAsia'), ...)` is NOT sufficient. You must set the east-asia font on EACH `run._element` via XML manipulation (see `set_cn_font()` helper in Template Script). **This is the #1 cause of broken Chinese output.** Always use the `add_run()` wrapper, never bare `p.add_run()`.
- **Table column count mismatch** → `add_table(doc, headers, rows)` requires EVERY row in `rows` to have exactly `len(headers)` elements. Otherwise `cell = row.cells[ci]` throws `IndexError: tuple index out of range`. If you get this error, count columns per row: `[len(r) for r in rows]` vs `len(headers)`.
- **python-docx version matters**: `python-docx>=1.0.0` is recommended. Older versions (0.8.x) have different API for some features.
- **Table styling**: `Light Grid Accent 1` is the most reliable built-in style for professional tables. `Light Shading Accent 1` also works well for data tables.
- **Page break before sections**: Use `doc.add_page_break()` at the end of each major section, NOT at the start (avoids blank page at document beginning).
- **File path**: Save to `os.path.expanduser('~/filename.docx')` so the user can find it easily.
- **Verify output**: Always `ls -lh ~/filename.docx` after generation to confirm file was created and has non-zero size.
- **Font availability**: If you set a Chinese font that's not installed on this machine, the file will still render correctly on the user's machine (fonts are referenced, not embedded by default). For true portability, consider embedding fonts.
- **Paragraph spacing**: `doc.add_paragraph()` adds spacing after by default. For compact layouts, set `paragraph.paragraph_format.space_after = Pt(0)`.
- **Multi-page documents**: For documents with 5+ pages, add `doc.add_page_break()` between major sections and use a title page.

### Existing Document Pitfalls

- **Heading style KeyError**: When calling `doc.add_heading(text, level=1)` on an existing document opened with `Document('existing.docx')`, you may get `KeyError: "no style with name 'Heading 1'"`. This happens when the document's internal style table is incomplete or uses a different style ID format. Use a safe fallback:

  ```python
  def add_heading_safe(doc, text, level=1):
      style_name = f'Heading {level}'
      try:
          return doc.add_heading(text, level=level)
      except KeyError:
          p = doc.add_paragraph()
          try:
              p.style = doc.styles[style_name]
          except:
              pass
          run = p.add_run(text)
          run.bold = True
          run.font.size = Pt(16 if level == 1 else 14 if level == 2 else 12)
          run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
          return p
  ```

- **rPr is None when copying runs**: When copying cover page runs from one document to another with `nr._element.rPr`, the rPr element may be None. Always use `nr._element.get_or_add_rPr()` instead of direct access.

- **Document restructuring & Chinese renumbering**: When moving sections to the front of a document (e.g., diagrams to Ch1/Ch2), the original chapters must be renumbered. Build a chapter mapping dict:
  ```python
  ch_map = {
      '一、硬件架构': '三、硬件架构',
      '二、操作系统': '四、操作系统',
      ...
  }
  ```
  This user prefers architecture diagrams and flow diagrams to be the FIRST chapters (Ch1/Ch2), not appendices at the end. Diagrams are visual overviews that orient the reader before diving into detail.

- **Inserting diagrams from chromium-rendered PNGs**: When embedding architecture diagrams generated from SVG/HTML, use chromium headless for best fidelity (renders fonts, grid patterns, CSS properly). See `references/embed-architecture-diagrams.md` for the full workflow.

## Usage Example — Veterinary Report

For the 13-year-old Poodle case:
1. Searched web for veterinary references on seizures + tracheal collapse
2. Structured into 5 sections (Emergency, Differential Dx, Diagnostic Workup, Treatment, Summary)
3. Generated a 40KB Word document with table-formatted differentials, treatment protocols, and numbered bullet points
4. Delivered as `~/泰迪犬抽搐站立不稳诊断治疗思路.docx`

## Work Report Generation (工作日报/周报)

A multi-step workflow for generating structured Chinese work reports from Hermes session history. Use when the user asks for a 工作日报, 周报, or work summary report.

**日报 vs 周报区分：**
- **日报（每日）** — 内容结构由 `daily_report` skill 定义，必含 日常维护 和 项目部署 两个区段。用本技能生成 WORD 文档后交付。
- **周报/月报** — 本模板适用于从 session_history 聚合的周期性报告。

### Workflow

```
Step 1: Browse recent sessions → session_search() no args
Step 2: Search broadly → session_search(query="工作 项目 配置 开发 测试", sort="newest", limit=10)
Step 3: Read key sessions → session_search() with session_id for scroll/read mode
Step 4: Compile data → organize by date, extract key accomplishments
Step 5: Generate Word doc → python-docx with work report format
Step 6: Try platform delivery → send_message(), if fails use direct API fallback
```

### Standard 工作日报 Structure

| Section | Content | Format |
|---------|---------|--------|
| 一、总体概述 | High-level summary of the period | Paragraph |
| 二、详细工作内容 | By-date sub-sections (e.g. "6月4日（周四）") | 日期 heading → bullet list items |
| 三、系统架构总览 | Architecture/state table | Table(层级, 组件, 状态) with colored header |
| 四、配置更新记录 | Config changes during period | Table(配置项, 旧值, 新值) |
| 五、产出文件清单 | Files created/modified | Table(文件名, 大小, 说明) |
| 六、后续计划 | Next steps / roadmap | Bullet list |

### Script Shell

```python
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
style = doc.styles['Normal']
style.font.name = 'Arial'
style.font.size = Pt(11)

# Per-run Chinese font (REQUIRED — style-level alone causes garbled output)
def set_cn_font(run, cn_font='SimSun', en_font='Arial'):
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), cn_font)
    rFonts.set(qn('w:ascii'), en_font)
    rFonts.set(qn('w:hAnsi'), en_font)
    rFonts.set(qn('w:cs'), en_font)

def add_run(p, text, bold=False, size=None, color=None):
    run = p.add_run(text)
    run.bold = bold
    if size: run.font.size = Pt(size)
    if color: run.font.color.rgb = color
    set_cn_font(run)
    return run

# === Title ===
title = doc.add_heading('工作日报', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle = doc.add_paragraph('日期范围 | 主题')
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

# === Section 1: 总体概述 ===
doc.add_heading('一、总体概述', level=1)
doc.add_paragraph('...')

# === Section 2: 详细工作内容 ===
doc.add_heading('二、详细工作内容', level=1)
doc.add_heading('6月X日（周X）', level=2)
doc.add_paragraph('1. 任务标题', style='List Bullet')
doc.add_paragraph('2. 任务标题', style='List Bullet')

# === Section 3-5: Tables (use add_run for cell text) ===
table = doc.add_table(rows=1, cols=3)
table.style = 'Table Grid'
hdr = table.rows[0].cells
add_run(hdr[0].paragraphs[0], '列1', bold=True)
# ... add rows via table.add_row()

# === Save ===
output_path = os.path.expanduser('~/工作日报_YYYYMMDD.docx')
doc.save(output_path)
```

### Pitfalls

- **Session search coverage**: `session_search()` browse mode only shows 10 most recent sessions. To find specific dates, use `query=` with relevant keywords and `sort="newest"`.
- **Session data is self-reported**: Session content reflects what the agent did, not external verification. Cross-check file creation/modification where possible.
- **Chinese numbering**: Use Chinese numeral sections (一、二、三、四、五、六) for professional reports, not "1. / 2." numbering.
- **Table style**: `'Table Grid'` (not `'Light Grid Accent 1'`) works better for Chinese documents — cleaner lines.
- **File path convention**: Save to `/home/andymao/work-report-YYYYMMDD.docx` for consistency.
- **Platform delivery fallback**: If `send_message()` fails (rate limit, timeout, gateway offline):
  1. Try `send_message()` with text-only first (no MEDIA: attachment) to test basic connectivity
  2. If still failing, use direct Telegram API via curl through proxy: `source ~/.hermes/.env && curl -s --max-time 10 --proxy http://127.0.0.1:7897 -F "chat_id=$TELEGRAM_HOME_CHANNEL" -F "document=@/path/to/file.docx" -F "caption=..." "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendDocument"`
  3. Report the local file path to the user as fallback (`~/filename.docx`)
- **Cover page vertical centering**: Use `for _ in range(N): doc.add_paragraph()` for blank lines. N=6 is typical for A4 title pages.
- **Table header styling**: Use `set_cell_shading(cell, '1E3A5F')` with white text for dark headers, and alternating row colors (`'EDF2F7'` for light grey zebra stripes) for readability. This user's preferred header color is navy blue `1E3A5F` (not `0F172A`).
- **Version history table**: Always include a version change log table for architecture/spec documents.

## References

- [python-docx documentation](https://python-docx.readthedocs.io/)
- `references/font-setup.md` — detailed font configuration for CJK documents
- `references/embed-architecture-diagrams.md` — workflow for embedding SVG/PNG architecture diagrams into Word docs (cross-skill with architecture-diagram)
- `references/resume-generation.md` — generating professional resumes/CVs from system information + work history (outline, data sources, styling constants, verification)
