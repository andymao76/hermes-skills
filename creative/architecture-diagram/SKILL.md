---
name: architecture-diagram
description: "SVG architecture/cloud/infra diagrams as HTML. Supports dark and light themes."
version: 1.1.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [concept-diagrams, excalidraw]
---

# Architecture Diagram Skill

Generate professional technical architecture diagrams as standalone HTML files with inline SVG graphics. Supports both dark and light (sky-blue) themes. No external tools, no API keys, no rendering libraries — just write the HTML file and open it in a browser.

## Scope

**Best suited for:**
- Software system architecture (frontend / backend / database layers)
- Cloud infrastructure (VPC, regions, subnets, managed services)
- Microservice / service-mesh topology
- Database + API map, deployment diagrams
- Anything with a tech-infra subject that fits a dark, grid-backed aesthetic

**Look elsewhere first for:**
- Physics, chemistry, math, biology, or other scientific subjects
- Physical objects (vehicles, hardware, anatomy, cross-sections)
- Floor plans, narrative journeys, educational / textbook-style visuals
- Hand-drawn whiteboard sketches (consider `excalidraw`)
- Animated explainers (consider an animation skill)

If a more specialized skill is available for the subject, prefer that. If none fits, this skill can also serve as a general SVG diagram fallback — the output will just carry the dark tech aesthetic described below.

Based on [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT).

## Workflow

1. User describes their system architecture (components, connections, technologies)
2. Generate the HTML file following the design system below
3. Save with `write_file` to a `.html` file (e.g. `~/architecture-diagram.html`)
4. User opens in any browser — works offline, no dependencies

### Output Location

Save diagrams to a user-specified path, or default to the current working directory:
```
./[project-name]-architecture.html
```

### Version Numbering Convention

Every knowledge graph/schematic SVG produced for this user must carry a version number in the subtitle and an implicit version history:
- **Major version +1** (e.g. V4.x → V5.0): Fundamental architecture changes — adding/removing entire layers, overhauling vendor rows, adopting a new technology generation, topology restructuring. **架构大改升大版本。**
- **Minor version +1** (e.g. V5.0 → V5.1): Cosmetic or content fixes — title corrections, label updates, connection line adjustments, color/theme changes, version badge updates, date bumps. **每次生成版本迭代一次小版本** — every regeneration that changes visible content is at least a minor bump.
- **No version bump**: Rendering fixes only (SVG export, background rect, emoji striping) that don't change visible information
- Format: `V<major>.<minor>` in the version badge (e.g. `V5.1`)
- The user expects versions to be tracked across sessions. When updating a prior diagram, **always read the existing version from the HTML file first**, apply the correct increment, and explicitly note `Vx.y → Vx.y+1` (or `Vx.y → Vx+1.0`) in your response.
- **Current version as of 2026-06-17:** V5.1 — update this sentence each time the diagram version changes.

### SVG Export (preferred output format)

This user prefers saving the diagram as a standalone SVG file for reuse and embedding. After generating the HTML file, extract the SVG and save it as a `.svg` file.

**IMPORTANT:** Do NOT use `execute_code()` with `read_file()` for SVG extraction — `read_file` adds line-number prefixes (`89|      <svg>`) that corrupt the XML. Use `terminal()` with a Python heredoc instead:

```bash
python3 << 'PYEOF'
INPUT = "INPUT.html"
OUTPUT = "OUTPUT.svg"

with open(INPUT) as f:
    html = f.read()

start = html.index("<svg ")
end = html.index("</svg>") + len("</svg>")
svg_block = html[start:end]

**CRITICAL #1: Add xmlns only if not already present**
# Without xmlns the browser shows "This XML file does not appear to have any style information"
# But the HTML template already has xmlns on its <svg> tag, so blindly adding a second
# one causes "duplicate attribute" XML parse error.
if 'xmlns=' not in svg_block[:200]:
    svg_block = svg_block.replace(
        '<svg ',
        '<svg xmlns="http://www.w3.org/2000/svg" style="background-color:#020617;" '
    )
else:
    # xmlns already exists — just add the style attribute
    svg_block = svg_block.replace(
        '<svg ',
        '<svg style="background-color:#020617;" '
    )

# CRITICAL #2: Replace any bare & with &amp; in text content
# SVG is XML — bare & (e.g. "存储 & 知识库层") causes parse error
import re
def escape_amp(m):
    # Skip if already escaped or an XML entity
    if m.group(0) in ('&amp;', '&lt;', '&gt;', '&quot;', '&apos;') or m.group(0).startswith('&#'):
        return m.group(0)
    return '&amp;'

# Check for unescaped & in text content (not in attribute values or tags)
svg_block = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', escape_amp, svg_block)

full = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_block

with open(OUTPUT, "w") as f:
    f.write(full)

# Verify XML well-formedness
try:
    import xml.etree.ElementTree as ET
    import io
    ET.parse(io.StringIO(full))
    print(f"✓ SVG exported: {OUTPUT} ({len(full)} bytes, valid XML)")
except Exception as e:
    print(f"✗ XML ERROR: {e}")
PYEOF
```

**Critical SVG XML rules:**
1. **Check for existing `xmlns` before adding.** The HTML template already has `xmlns` on its `<svg>` tag. Adding a second one causes `"duplicate attribute"` XML parse error. Use the conditional approach shown above: `if 'xmlns=' not in svg_block[:200]:` before inserting.
2. **Always use `rindex('<svg ')` not `index('<svg ')` when the HTML has multiple SVG elements** (e.g. diagram card + inline icons). `rindex` finds the last (correct) occurrence. For multi-SVG HTML files (architecture + flow chart stacked), use `re.findall(r'<svg[^>]*>.*?</svg>', html, re.DOTALL)` and extract each independently.
3. Always add an explicit background rect as the first child of `<svg>` — for dark theme: `fill="#0f172a"`, for light theme: `fill="#e0f2fe"`. Extracted SVGs don't inherit CSS body background.
4. Always escape `&` to `&amp;` — bare `&` causes XML parse error (common in Chinese text like "2G/3G & 4G/VoLTE")
5. **Pitfall: `&` in Python regex triggers shell backgrounding in heredoc.** When the extraction script's regex contains `&(?!amp;|...)`, the terminal tool may reject the command because it sees `&` + process. Workaround: use `\x00AMP\x00` placeholder trick (replace `&amp;` → placeholder before regex, restore after), or write the script to a `.py` file with `write_file` and run via `python3 <file>` instead of inline heredoc.
6. Verify with `file OUTPUT.svg` (should say "SVG Scalable Vector Graphics image")
7. **Visual verification:** Render to PNG with CairoSVG and sample key text regions with Pillow to confirm text is visible against the dark background (≥5% non-white pixels). See `references/visual-verification.md` for the full script.

### PNG Export (CairoSVG)

For platforms that need raster images (WeChat, presentations), render the SVG to PNG with cairosvg. **Critical pitfall:** cairosvg does NOT honor the CSS `style="background-color:..."` attribute on the `<svg>` element. Without an explicit background rect, backgrounds render as transparent — dark diagrams show as black-on-black in image viewers, and light diagrams show as no-background artifacts.

**Always insert a background rect as the first child of `<svg>` before rendering:**

```python
# Insert before rendering
svg_body = re.sub(
    r'(<svg[^>]*>)',
    r'\1\n<rect width="100%" height="100%" fill="#ffffff" />',
    svg_body, count=1
)
# For dark theme: fill="#020617"
# For light theme: fill="#ffffff"
```

Then render:
```bash
python3 << 'PYEOF'
import cairosvg
cairosvg.svg2png(url="input.svg", write_to="output.png",
                 output_width=2600, output_height=2000)
PYEOF
```

### PNG Export (Chromium Headless — for Word Document Embedding)

When the diagram needs to be embedded in a Word document (.docx), use Chromium headless instead of CairoSVG. Chromium properly renders Google Fonts, CSS grid patterns, emoji characters, and SVG markers — things CairoSVG struggles with.

```bash
# Create a standalone HTML file with the SVG + CSS, then render:
google-chrome-stable --headless --no-sandbox --disable-gpu \
  --screenshot=output.png --window-size=WIDTH,HEIGHT \
  file:///path/to/diagram.html
```

Set `--window-size` to match the SVG `viewBox` plus ~40px padding (e.g., viewBox 1100x880 → 1150x960). For multi-diagram documents, create separate HTML files per diagram and render each independently.

This skill pairs with `python-docx` for Word document generation. See `references/embed-architecture-diagrams.md` in the `python-docx` skill for the full docx embedding workflow.

**Document placement preference**: This user prefers architecture and business flow diagrams to be placed FIRST in documents (Chapter 1/2), not as appendices. The visual overview orients the reader before detailed specification.

### Light Theme Conversion

For light-themed variants of dark diagrams (user request: "改为浅色"), see `references/light-theme-conversion.md` for the complete transformation pipeline. The conversion touches every color: background, grid, text fills, box fills, layer fills, and subtitle colors. A Python script performs all substitutions in one pass.

### Reference Files

- `templates/template.html` — Full HTML template with CSS and SVG examples
- `references/layout-calculations.md` — Mathematical formulas for uniform box distribution
- `references/svg-export-pitfalls.md` — XML escaping, emoji rendering, cairosvg background rect, and extraction gotchas
- `references/visual-verification.md` — CairoSVG + Pillow verification for both dark and light themes
- `references/light-theme-conversion.md` — Complete dark→light color mapping and transformation script
- `references/svg-coordinate-shift.md` — Fix overlapping Layer labels and boxes by bulk-shifting SVG Y coordinates (with real-world example)
- `references/docx-embed-workflow.md` — Embedding SVG→PNG screenshots into Word documents via chromium headless + python-docx
- `references/flow-chart-layout-pitfalls.md` — 流程图布局避坑：决策菱形 + 侧分支 + 下游步骤的坐标计算和重叠预防
- `references/multi-svg-extraction.md` — Python script for extracting each SVGs from multi-SVG HTML files, with XML validation

### Multi-SVG concatenation pitfall

When an HTML file contains **two or more SVG elements** (e.g., architecture diagram + flow chart stacked vertically), the SVG extraction approach of `html.index("<svg ") ... html.index("</svg>")` captures only the FIRST SVG. The extracted .svg file contains a trailing `</svg>` immediately followed by `<svg>` ... which is invalid XML and causes:

```
This page contains the following errors:
error on line N at column 1: Extra content at the end of the document
```

**Fix options (in order of preference):**
1. **For PDF export:** Use the HTML file directly — Chrome handles multiple SVGs correctly in HTML context
2. **For standalone SVG:** Extract each SVG to separate files by finding start/end for each independently (use `re.findall(r'<svg[^>]*>.*?</svg>', html, re.DOTALL)`)
3. **For user review:** Open the HTML file (not the SVG extract) — HTML is the canonical source for multi-diagram documents. This avoids the XML parse error entirely.
4. **For manual review flow:** After extracting individual SVGs, verify XML well-formedness with `xml.etree.ElementTree.parse()` before opening in Chrome

### Manual review workflow

This user requires a **human-in-the-loop review** before final output delivery:

1. Generate preview → open in Chrome via `terminal(background=true)`
2. Wait for user's verbal approval
3. Only then extract SVG, generate PDF, or deliver to platforms
4. If user rejects, stop and ask for direction before trying alternatives

**Do NOT** auto-retry with different settings after a rejection — ask what they want changed.

Always do both the SVG export step and visual verification automatically — don't stop at the HTML file. Deliver both:

```text
[project-name]-architecture.html   (the editable source)
[project-name]-architecture.svg    (the standalone SVG vector file)
```

### PDF Export (Multi-Size, for Printing & Document Embedding)

**Paper size selection guide:**

SVG viewBox size determines which paper fits best:

| SVG viewBox | Recommended paper | Chrome flag |
|-------------|------------------|-------------|
| ≤1000×800 | A4 portrait (210×297mm) | `--paper-width=210 --paper-height=297` |
| ≤1300×1100 | A3 landscape (420×297mm) | `--paper-width=420 --paper-height=297` |
| ≤1600×1400 | A2 landscape (594×420mm) | `--paper-width=594 --paper-height=420` |
| Larger / stacked SVGs | A2 landscape or custom | Increase as needed |

**Quick method (Chrome `--print-to-pdf`):** When the user doesn't need 300dpi precision and just wants a clean single-page PDF, use Chrome headless print-to-pdf directly:

```bash
# A4 landscape (default - fits most diagrams)
google-chrome-stable --headless=new --no-sandbox --disable-gpu \
  --print-to-pdf=output.pdf \
  --print-to-pdf-no-header \
  --paper-width=210 --paper-height=297 \
  --no-margins \
  file:///path/to/diagram.html

# A3 landscape (for wide architecture diagrams, viewBox ~1340x1100)
google-chrome-stable --headless=new --no-sandbox --disable-gpu \
  --print-to-pdf=output-a3.pdf \
  --print-to-pdf-no-header \
  --paper-width=420 --paper-height=297 \
  --no-margins \
  file:///path/to/diagram.html

# A2 landscape (for extra large diagrams with multiple SVGs)
google-chrome-stable --headless=new --no-sandbox --disable-gpu \
  --print-to-pdf=output-a2.pdf \
  --print-to-pdf-no-header \
  --paper-width=594 --paper-height=420 \
  --no-margins \
  file:///path/to/diagram.html
```

Produces a clean PDF (~600KB) in one command. No ImageMagick, no HiDPI screenshot, no resize.

**Workflow rule: preview before output.** This user requires a human review step:
1. Generate a preview PDF with the candidate paper size to `/tmp/` (not the final path)
2. Open it in Chrome: `google-chrome-stable --new-window --no-sandbox file:///tmp/preview.pdf &`
3. Wait for user to review and approve the size/layout
4. Only copy to the final path and deliver after user confirmation

**IMPORTANT: Avoid iterative PDF paper-size guessing.** If the user rejects the first paper size, do NOT generate a second PDF of a different size and wait for another rejection. Instead:
- **Stop generating PDFs immediately** after the first rejection
- **Open the HTML file directly in Chrome** for review — HTML handles multiple nested SVGs properly and avoids the multi-SVG concatenation bug in standalone SVG extraction
- Ask the user: "Let me open the HTML file directly for review — you can zoom/pan freely to see if the content is complete, then tell me what paper size to use"
- Only after the user confirms via HTML review, extract SVG and generate PDF with the specified paper size
- This avoids the costly trial-and-error cycle of A4→A3→A2 landscape→A2 portrait→A1 landscape→SVG that wastes time and frustrates the user

> **Paper size decision helper:** For multi-SVG diagrams (architecture + flow chart), the combined height often exceeds A4/A3. Ask the user what size works for them (A2 landscape or larger) rather than guessing iteratively.

**HiDPI method (300dpi, for print-quality):**

When the user asks for A4 printable output, a simple `--print-to-pdf` often breaks diagrams across multiple pages (especially wide or tall SVGs) or produces soft/blurry output. Use a **two-stage workflow with HiDPI rendering** to get crisp 300dpi output.

**Stage 1: Create a bare-minimum render HTML**

Copy the SVG from the full diagram HTML into a stripped-down HTML that has no CSS layout, no info cards, no footer, and no Google Fonts link. The SVG should fill the viewport directly:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #020617; }
  svg { width: 100vw; height: 100vh; display: block; }
</style>
</head>
<body>
<!-- SVG element with full content here -->
</body>
</html>
```

Key rules:
- **Bare HTML only**: No extra containers, no title bars, no info cards. The SVG fills the whole viewport.
- **Landscape A4** (3508x2480) for wide architecture diagrams (viewBox ~1340x1100)
- **Portrait A4** (2480x3508) for tall multi-diagram layouts (two SVGs stacked)
- Keep `preserveAspectRatio="xMidYMid meet"` on `<svg>` to fit without clipping
- **Multi-diagram:** Create a single HTML with both SVGs, each sized via CSS `height: 50vh` or `height: 58vh / 42vh`

**Stage 2: Export via HiDPI Chromium screenshot → ImageMagick A4 resize**

**CRITICAL: Use `--force-device-scale-factor=3` to render at 3x native resolution.** A plain screenshot at 2800x2100 (no scale factor) upscaled to 3508x2480 produces blurry text — the user will reject it. The scale factor renders the SVG at pixel density 3× the window size, producing a crisp native render that looks sharp even after downscaling to 300dpi.

```bash
# 1) HiDPI screenshot (3x scale, window ≈ viewBox aspect ratio)
google-chrome-stable --headless=new --no-sandbox --disable-gpu \
  --window-size=1600,1350 \
  --force-device-scale-factor=3 \
  --hide-scrollbars \
  --screenshot=./hidpi.png --default-background-color=020617 \
  file://./bare-render.html

# 2) Resize to exact A4 300dpi dimensions
# A4 Landscape: 3508x2480 px @ 300dpi
convert ./hidpi.png \
  -resize 3508x2480 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center -extent 3508x2480 \
  -quality 100 ./output-a4.pdf

convert ./hidpi.png \
  -resize 3508x2480 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center -extent 3508x2480 \
  -quality 100 ./output-a4.png

# A4 Portrait:  2480x3508 px @ 300dpi
convert ./hidpi.png \
  -resize x3508 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center \
  -extent 2480x3508 \
  -quality 100 ./output-a4.pdf

convert ./hidpi.png \
  -resize x3508 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center \
  -extent 2480x3508 \
  -quality 100 ./output-a4.png
```

**Window size guide by SVG viewBox:**
- 1340x1100 → 1600x1350 @3x → 4800x4050px (Hermes 8-layer arch)
- 1100x880 → 1400x1150 @3x → 4200x3450px (6-layer arch)
- Two SVGs stacked → 1400x2000 @3x → 4200x6000px (arch + flow)

Always deliver both `.pdf` and `.png` outputs when the user asks for A4 printable exports. Verify with:
```bash
identify output-a4.png       # should show 3508x2480 or 2480x3508
ls -lah output-a4.png        # should be >500KB; <200KB = blurry, re-render
pdfinfo output-a4.pdf         # single page, A4 page size
```

See `references/a4-print-export.md` for the complete worked example with a full pitfall table.

### Preview

After saving, suggest the user open it:
```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## Design System & Visual Language

### Color Palette (Semantic Mapping)

Use specific `rgba` fills and hex strokes to categorize components:

| Component Type | Fill (rgba) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **Backend** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **Database** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/Cloud** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **Security** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **External** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

### Color Theme Preferences (Iterative — User Eventually Prefers Dark)

This user went through several background color iterations before settling on the final choice. When the user asks to change the background color:

1. **Make the change directly in the HTML** — update body background, SVG background rect, and grid stroke color
2. **Extract the SVG** from the updated HTML
3. **Open the SVG in Chrome** for review via `terminal(background=true)`
4. **Wait for explicit approval** before proceeding to PDF

**Final settled preference (2026-06-17): Dark navy background**

| Component | Value | Purpose |
|-----------|-------|---------|
| body background | `#0f172a` | Dark navy, not pure black |
| SVG background rect | `<rect width="100%" height="100%" fill="#0f172a" />` | Must be explicit — not inherited from CSS |
| Grid stroke | `#1e293b` | Subtle grid on dark background |
| body text | `#e2e8f0` | Light slate for readability |
| Card backgrounds | `rgba(15, 23, 42, 0.5)` | Semi-transparent dark cards |
| Card borders | `#1e293b` | Matches grid stroke |
| Section-title accent | `#22d3ee` | Cyan accent on dark |
| Subtitle text | `#94a3b8` | Muted secondary |
| Footer text | `#475569` | Subtle footer |

**Theme-switching guide:** When the user asks "改成浅色" or "改成深色":

| Context | Dark theme value | Light theme value |
|---------|-----------------|-------------------|
| body background | `#0f172a` | `#e0f2fe` |
| body text color | `#e2e8f0` | `#1e293b` |
| SVG grid stroke | `#1e293b` | `#bae6fd` |
| SVG bg rect fill | `#0f172a` | `#e0f2fe` |
| Card background | `rgba(15,23,42,0.5)` | `#ffffff` |
| Card border | `#1e293b` | `#bae6fd` |
| Section-title accent | `#22d3ee` | `#0284c7` |
| Subtitle text | `#94a3b8` | `#475569` |
| Footer text | `#475569` | `#94a3b8` |

**IMPORTANT:** After each color change, re-extract the SVG from the updated HTML — do not manually edit the SVG file. The HTML is the canonical source; the SVG is derived.

### User Preference: PDF Preview Workflow

This user has a strict workflow for PDF generation:

1. **Generate SVG first** — produce standalone SVG files (not PDF) for review
2. **Open in Chrome** — use `terminal(background=true)` to open the SVG
3. **Wait for explicit approval** — user says "looks good" or similar
4. **Only then** generate the PDF with Chrome `--print-to-pdf`

**IMPORTANT: Do NOT generate multiple PDFs of different paper sizes iteratively.** If the first PDF size is rejected:
- Stop generating PDFs
- Ask the user to specify the paper size explicitly
- Generate one PDF with exactly that size
- Do not auto-guess or try alternatives without being asked

**PDF paper sizes tested with this user's diagrams (SVG viewBox ~1340×1100):**
- A4 (210×297mm) → content clipped (too small)
- A3 landscape (420×297mm) → content clipped
- A2 landscape (594×420mm) → content clipped
- A2 portrait (420×594mm) → content clipped
- A1 landscape (841×594mm) → may fit, user preferred SVG review first
- Note: Multi-SVG HTML files (architecture + flow chart stacked) need larger paper than single-SVG diagrams

**Recommended starting size for this user's multi-SVG diagrams:** Ask explicitly before generating. Do not guess.

### Typography & Background
- **Font:** JetBrains Mono (Monospace), loaded from Google Fonts
- **Sizes:** 12px (Names), 9px (Sublabels), 8px (Annotations), 7px (Tiny labels)
- **Background (Dark):** Slate-950 (`#020617`) with a subtle 40px grid (`stroke="#1e293b"`)
- **Background (Light):** Sky-50 (`#e0f2fe`) with a subtle 40px grid (`stroke="#bae6fd"`)
- **SVG background rect:** Always add an explicit `<rect>` fill for the background color before the grid pattern. Without it, extracted SVGs (not HTML) have transparent backgrounds, causing text to render on whatever the viewer's default background is.

```svg
<!-- Background Grid Pattern (Light Blue) -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#bae6fd" stroke-width="0.5"/>
</pattern>
```

### Emoji Icons and Unicode Symbols

Emojis and special Unicode symbols improve visual scanning in HTML but **will render as tofu blocks (☒) when converted to PNG via CairoSVG**. CairoSVG relies on system fonts and cannot render emoji glyphs, regional indicators (flags), or symbols from the MiscSymbols block.

**Problematic characters known to fail:**
| Character | Code | Renders as | In SVG text |
|:---|:---|:---|:---|
| 🤖 🌐 🧠 🐘 🔴 📚 📋 🚪 🌉 🔶 ☁️ ⚙️ ⌨️ 🎮 ⏰ | Emoji blocks | ☒ | Any `<text>` |
| 🇨🇳 🇺🇸 | Regional indicators | ☒☒ | Flag labels |
| ⌨ (U+2328) | Misc Technical | ☒ | "CLI 终端" prefix |
| ⏰ (U+23F0) | Misc Technical | ☒ | "定时任务" prefix |

**Decision matrix:**

| Deliverable format | Emoji OK? | What to do |
|:---|:---|:---|
| HTML only (browser) | ✅ Yes | Add emojis freely — browsers render them natively |
| SVG + PNG via CairoSVG | ❌ No | Strip ALL emoji and Unicode symbols before rendering PNG |
| SVG standalone (no PNG) | ⚠️ Partial | Depends on viewer — browsers OK, image viewers fail |

**Stripping approach** (see `references/light-theme-conversion.md` for the full transformation script):
1. Remove with regex: `[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0000200D\U0000FE0F]`
2. Replace individually: `⌨` → ``, `⏰` → ``, `🇨🇳` → `CN`
3. Verify final cleanliness with `python3 -c "..."` scanning for `[^\x00-\x7F\u4e00-\u9fff...]`

**For diagrams that will be shared as PNG** (WeChat, presentations), omit emoji from the HTML source so no stripping is needed.

## Technical Implementation Details

### Component Rendering
Components are rounded rectangles (`rx="6"`) with 1.5px strokes. To prevent arrows from showing through semi-transparent fills, use a **double-rect masking technique**:
1. Draw an opaque background rect (`#0f172a`)
2. Draw the semi-transparent styled rect on top

### Connection Rules
- **Z-Order:** Draw arrows *early* in the SVG (after the grid) so they render behind component boxes
- **Arrowheads:** Defined via SVG markers
- **Security Flows:** Use dashed lines in rose color (`#fb7185`)
- **Boundaries:**
  - *Security Groups:* Dashed (`4,4`), rose color
  - *Regions:* Large dashed (`8,4`), amber color, `rx="12"`

### Spacing & Layout Logic
- **Standard Height:** 60px (Services); 80-120px (Large components)
- **Vertical Gap:** Minimum 40px between components
- **Message Buses:** Must be placed *in the gap* between services, not overlapping them
- **Legend Placement:** **CRITICAL.** Must be placed outside all boundary boxes. Calculate the lowest Y-coordinate of all boundaries and place the legend at least 20px below it.

### Critical: Check Vertical Overlap of Decision Diamonds

Decision diamonds (`<polygon>`) extend both above AND below their center point. Unlike `<rect>` elements where `y` is the top edge, a diamond centered at (cx, cy) spans from `cy - height/2` to `cy + height/2`. This often causes **invisible vertical overlap** with boxes placed on the same Y row to the left or right.

**Rule:** When placing boxes on the same Y row as a diamond's "No" path (the downward exit), the box's Y range must be entirely below the diamond's bottom point.

**Formula:**
```
diamond_bottom = diamond_cy + diamond_height/2
box_top = diamond_bottom + min_gap    # min_gap ≥ 20px
```

**Multi-element verification checklist after layout:**
1. Every `<rect>` top Y > every diamond's bottom Y in the same column
2. Every diamond's left/right point does not overlap text boxes on the same row
3. Every `<text>` label is positioned within its parent rect/polygon
4. Arrows from diamond sides do not pass through adjacent boxes

**Never guess box positions inside a dashed boundary by eye.** Always use the mathematical formula to guarantee equal spacing. When the user adjusts a boundary box's dimensions, **recalculate all inner box positions** from the formula — do not just nudge them.

Given boundary at `x_b` with `width_b`, and N inner boxes each `width_i`:

```
total_gap = width_b - (N × width_i)
gap = total_gap / (N + 1)          ← same gap before first and after last box
box_x[k] = x_b + gap + k × (width_i + gap)    for k = 0 .. N-1
```

After positioning, verify: right edge of last box + gap ≈ x_b + width_b.

**All boxes in the same row must have identical width**, otherwise equal spacing is impossible.

For multi-row layouts, apply the formula independently per row. See `references/layout-calculations.md` for worked examples and a pitfall table.

**CRITICAL verification step after ANY boundary or box dimension change:** recalculate ALL inner box x-positions from scratch using the formula above. Do not just shift one box — an incremental nudge breaks the uniform spacing for the entire row.

## Document Structure

The generated HTML file follows a four-part layout:
1. **Header:** Title with a pulsing dot indicator and subtitle
2. **Main SVG:** The diagram contained within a rounded border card
3. **Summary Cards:** A grid of three cards below the diagram for high-level details
4. **Footer:** Minimal metadata

### Info Card Pattern
```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

### Version Badge & Subtitle

For versioned diagrams, add a badge and host/subtitle line next to the title:

```html
<span class="version-badge">V3.1</span>
```
```css
.version-badge {
  display: inline-block;
  background: rgba(34, 211, 238, 0.15);
  color: #22d3ee;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(34, 211, 238, 0.3);
  margin-left: 0.75rem;
}
```

The subtitle (`<p class="subtitle">`) should carry hostname/hardware info (CPU, RAM, disk) to anchor the diagram to a specific environment.

### Multi-row Arrow Colors

When components span distinct semantic layers, give each layer's arrows a matching color. Define separate arrowhead markers per color:

```svg
<marker id="arrowhead-emerald" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
  <polygon points="0 0, 10 3.5, 0 7" fill="#34d399" />
</marker>
```

Standard arrow colors by layer:
- Platform → Core: `#34d399` (emerald)
- Core → Provider: `#fb923c` (orange)
- Core → Storage: `#a78bfa` (violet, dashed)
- Developer → Agent: `#22d3ee` (cyan, dashed)

### Emoji Icons in SVG Text Labels

Add emoji to component text labels for scannability — especially useful for Chinese-language diagrams where emoji + CJK text improves scanning speed. Add filter for legend emphasis:

```svg
<filter id="glow">
  <feGaussianBlur stdDeviation="2" result="blur"/>
  <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
```

### SVG viewBox Sizing

For complex diagrams with 3+ layers, start with `viewBox="0 0 1180 820"` to ensure everything fits. The viewBox should cover the thickest vertical column. For tight diagrams (2 layers), `viewBox="0 0 1000 680"` is adequate. Always test by checking `min-width` on the SVG wrapper.

### 流程图 (Flow Chart) 特殊注意事项

当绘制含决策菱形的流程图时，**下游步骤必须放在菱形下方，不可放在菱形右侧同一行**，否则会和菱形侧分支重叠。参见 `references/flow-chart-layout-pitfalls.md` 获取详细坐标计算示例和避坑清单。

### Delivery to Platforms

After generating the diagram files, the user may ask to send them to messaging platforms. How to deliver:

- **Telegram / Discord / WeChat**: Use `send_message()` with MEDIA: path. Send to the correct platform target (not `origin` — that fails).
  ```
  send_message(target='telegram', message='Description text\\nMEDIA:/path/to/diagram.png')
  ```
- **Feishu (飞书) — PDF files**: Use the Feishu Open API upload-and-send workflow (the `send_message` tool is NOT available in CLI mode). Two-step:
  1. Upload PDF: Get tenant_access_token → POST to `https://open.feishu.cn/open-apis/im/v1/files` with `file_type: "pdf"`
  2. Send file message: POST to `https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id` with `msg_type: "file"` and `content: {"file_key": "..."}`
  3. The home channel open_id is in `FEISHU_HOME_CHANNEL` in `.env`
  4. Example script available in `feishu-openapi` skill's `scripts/feishu_client.py` (supports `upload-file` command). For PDFs, write a short Python script directly — the feishu_client.py helper may not have a `send-file` command.
- **Multiple platforms in one request**: Call `send_message()` separately per platform, not all at once.
- **HTML vs SVG vs PNG**: Prefer PNG for messaging platforms (rendered reliably). HTML/SVG may not display inline — only PNG renders as native image.
- **Chrome preview**: When asked to "open with Chrome", use `terminal(background=True)` to launch the browser without blocking:
  ```
  /snap/bin/chromium --no-sandbox --new-window file:///path/to/diagram.html
  ```
- **Screenshot**: For quick sharing, use Chromium headless screenshot in addition to SVG export:
  ```
  /snap/bin/chromium --headless --no-sandbox --disable-gpu \\
    --screenshot=/path/to/output.png --window-size=1400,1080 \\
    file:///path/to/diagram.html
  ```

## Output Requirements
- **Single File:** One self-contained `.html` file
- **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts)
- **No JavaScript:** Use pure CSS for any animations (like pulsing dots)
- **Compatibility:** Must render correctly in any modern web browser
- **Footer Attribution:** Always include `使用 architecture-diagram skill + SVG 绘制` in the footer line to make diagram provenance clear when shared externally.
- **Dual Output:** Always deliver both `.html` (editable source) + `.svg` (standalone vector) files. Do not stop at just the HTML.

## Template Reference

Load the full HTML template for the exact structure, CSS, and SVG component examples:

```
skill_view(name="architecture-diagram", file_path="templates/template.html")
```

The template contains working examples of every component type (frontend, backend, database, cloud, security), arrow styles (standard, dashed, curved), security groups, region boundaries, and the legend — use it as your structural reference when generating diagrams.
