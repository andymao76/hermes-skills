# Embedding Architecture Diagrams in Word Documents

Workflow for combining `architecture-diagram` (SVG/HTML) with `python-docx` to produce Word documents containing dark-themed architecture and flow diagrams.

## Workflow

1. **Generate the diagram** — Create an SVG diagram using the `architecture-diagram` skill or inline SVG in a standalone HTML file. The diagram should use a dark theme (`#020617` background) for on-screen viewing.

2. **Render to PNG** — Convert the HTML/SVG to a raster image for Word embedding. Two options:

   **Option A: Chromium headless** (best fidelity — renders CSS, fonts, grid patterns):
   ```bash
   google-chrome-stable --headless --no-sandbox --disable-gpu \
     --screenshot=output.png --window-size=WIDTH,HEIGHT \
     file:///path/to/diagram.html
   ```
   Use `--window-size` matching the SVG `viewBox` plus ~40px padding. SVG viewBox 1100x880 -> window-size 1150x960.

   **Option B: CairoSVG** (lighter, but needs background rect):
   ```python
   import cairosvg, re
   svg = open('diagram.svg').read()
   svg = re.sub(r'(<svg[^>]*>)', r'\1\n<rect width="100%" height="100%" fill="#020617"/>', svg, count=1)
   cairosvg.svg2png(bytestring=svg.encode(), write_to='output.png',
                    output_width=2600, output_height=2000)
   ```

3. **Embed into Word document** — Use `python-docx` to append the PNG:
   ```python
   from docx import Document
   from docx.shared import Inches, Cm
   from docx.enum.text import WD_ALIGN_PARAGRAPH

   doc = Document('existing.docx')
   doc.add_page_break()

   # Section heading
   doc.add_heading('一、系统架构图', level=1)
   # Caption
   p = doc.add_paragraph()
   p.alignment = WD_ALIGN_PARAGRAPH.CENTER
   run = p.add_run('图1: 架构总览')
   run.bold = True
   run.font.color.rgb = RGBColor(0x47, 0x56, 0x69)
   # Image
   p2 = doc.add_paragraph()
   p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
   p2.add_run().add_picture('output.png', width=Inches(5.8))

   doc.save('output.docx')
   ```

## Known Pitfalls

### Heading 1 KeyError on existing documents
When calling `doc.add_heading(text, level=1)` on an existing document, you may get `KeyError: "no style with name 'Heading 1'"`. Use this safe fallback:

```python
def add_heading_safe(doc, text, level=1):
    try:
        return doc.add_heading(text, level=level)
    except KeyError:
        p = doc.add_paragraph()
        try:
            p.style = doc.styles[f'Heading {level}']
        except:
            pass
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(16 if level == 1 else 14)
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
        return p
```

### rPr None when copying runs between documents
When copying cover page runs from one Document to another, `run._element.rPr` may be None. Use `nr._element.get_or_add_rPr()` instead.

### Document restructuring
This user prefers architecture diagrams to be FIRST (Chapter 1/2), not as appendices. When restructuring, build a chapter mapping dict for Chinese renumbering:
```python
ch_map = {
    '一、硬件架构': '三、硬件架构',
    '二、操作系统': '四、操作系统',
}
```

## Best Practices

- **Image width**: 5.8 inches (~14.7cm) fits A4 portrait with 2.5cm margins.
- **Caption style**: Bold + centered + slate-gray (#475669) for Chinese consistency.
- **Versioning**: Append diagrams to existing documents as V1.1 (minor bump) or V2.0 if restructuring (major bump).
- **Dark vs light**: Dark-themed SVGs render well on screen. For print/Word, consider converting to light theme using `architecture-diagram` skill's `references/light-theme-conversion.md`.

## Session Reference

Developed 2026-06-11 for Smartbrain system architecture (rhino01). Architecture diagram: 6 layers, dark theme, 1150x960 PNG. Business flow diagram: 5 steps with split/merge, 1150x640 PNG. Both embedded in 10-chapter document after restructuring (diagrams moved to front).
