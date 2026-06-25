# Markdown → PDF Rendering Reference

## Pipeline A: Markdown → Pandoc → HTML → PDF (general documents)

```
input.md → [pandoc] → /tmp/output.html → [inject CSS] → [chromium headless] → output.pdf
```

## Pipeline B: HTML-first design → A4 PDF (diagrams, tables, structured reports)

```
design.html → [chrome headless --print-to-pdf] → output.pdf
```

Use Pipeline B when the document has complex layout — inline SVG diagrams, detailed tables,
color-coded sections, page breaks per topic, or anything that requires precise visual structure
beyond what pure markdown + pandoc can produce. The HTML is the source of truth; the PDF is
one output format.

### Key CSS for Multi-page A4

```html
<style>
  @page {
    size: A4 portrait;
    margin: 18mm 16mm 20mm 16mm;
    @bottom-center { content: "第 " counter(page) " 页"; font-size: 9pt; color: #666; }
  }

  .page {
    page-break-after: always;
    page-break-inside: avoid;
    min-height: 100vh;
  }
  .page:last-child { page-break-after: auto; }
</style>
```

### Diagram Wrapping (prevent SVG from breaking across pages)

```css
.diagram-wrap {
  page-break-inside: avoid;
  /* border, padding, background for visual framing */
}
```

### Table Wrapping

```css
table { page-break-inside: avoid; }
```

### Font Family for CJK PDF (system fonts Chrome can embed)

```css
font-family: 'Noto Sans CJK SC', 'Source Han Sans SC', 'PingFang SC', sans-serif;
```

Chrome's `--print-to-pdf` embeds OpenType/CID fonts natively — no font configuration needed
for system fonts. Verify with:

```bash
pdffonts output.pdf | grep -E "emb|sub"
# All CJK fonts should show emb=yes, sub=yes
```

### Light Theme for Print

Screen-oriented diagrams (dark theme) must be converted to light theme for PDF — black backgrounds
waste toner and look poor on paper. Color mappings:

| Screen | Print PDF |
|--------|-----------|
| `#0d1117` (bg) | `#fafbfc` or `#fff` |
| `#58a6ff` (blue stroke) | `#1f6feb` |
| `#3fb950` (green stroke) | `#1a7f37` |
| `#f0883e` (orange stroke) | `#c0651a` |
| `#c9d1d9` (text) | `#1a1a2e` or `#333` |
| `#8b949e` (dim text) | `#666` |
| `#161b22` (box bg) | `#f6f8fa` |
| `#30363d` (border) | `#d0d7de` |

### SVG Adjustments for Print

- Increase font sizes by 1-2pt vs screen — print is higher DPI
- Use solid fills instead of semi-transparent for box backgrounds
- Arrow strokes should be at least 1.5px for visibility at A4 scale
- Keep `viewBox` aspect ratio fitting by using `width="750"` on `<svg>` within diagram-wraps
- Use labeled arrows (e.g. `<text>` next to `<line>`) with interface names for technical diagrams

### Chrome Headless PDF Command

```bash
google-chrome-stable --headless --disable-gpu --disable-dev-shm-usage \
  --no-pdf-header-footer \
  --print-to-pdf=/home/andymao/output.pdf \
  file:///home/andymao/input.html
```

Flags explained:
- `--no-pdf-header-footer`: Removes Chrome's built-in date/URL footer
- `--disable-dev-shm-usage`: Avoids shared memory issues
- `--print-to-pdf=<path>`: Path must be writable; output goes directly to A4

### Verification

```bash
# Page count, size, metadata
pdfinfo <file.pdf>

# Font embedding check (all CJK fonts must show emb=yes, sub=yes)
pdffonts <file.pdf>

# Content extraction spot-check
pdftotext <file.pdf> - | head -10

# File size sanity
ls -lah <file.pdf>
```