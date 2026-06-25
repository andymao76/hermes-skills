---
name: pptx
description: "Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |
| python-pptx pitfalls | Read [references/python-pptx-pitfalls.md](references/python-pptx-pitfalls.md) |
| Create from scratch (python-pptx) | Read [python-pptx.md](python-pptx.md) below |

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for pptxgenjs (Node.js) details.**

### Alternative: python-pptx

If pptxgenjs is not installed, use `pip install python-pptx` instead. python-pptx is pure Python and doesn't require Node.js.

**Key differences from pptxgenjs:**
- `from pptx import Presentation` instead of `require("pptxgenjs")`
- Dimensions in `Inches()`, `Pt()`, `Emu()` — not raw floats
- `slide.shapes.add_textbox()` for text, not `slide.addText()`
- Colors are `RGBColor(0xFF, 0x00, 0x00)` not `"FF0000"`
- No hex-color `#` prefix issues (uses RGBColor objects)
- Shadow requires manual set (not all object types support it natively)
- Tables use `slide.shapes.add_table()`, not `slide.addTable()`
- `slide.background.fill.solid()` then `fill.fore_color.rgb = color`

**When to use python-pptx:**
- pptxgenjs is not installed (saves ~50MB npm install)
- You need to read/edit existing .pptx files (python-pptx can modify)
- The slide design is simple to moderate (cards, text, tables, shapes)

**When to stick with pptxgenjs:**
- Need charts, complex master slides, or rich formatting
- Many slides with consistent layouts (slide masters)
- The user specifically wants pptxgenjs output

---

## Creating from Scratch (python-pptx)

**Use when pptxgenjs is not installed** (python-pptx is usually pre-installed or easy to install). Write a Python script to a temp file, then run it.

### Quick-setup pattern

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.33)   # 16:9 widescreen
prs.slide_height = Inches(7.5)

slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

# Background fill
bg = slide.background.fill
bg.solid()
bg.fore_color.rgb = RGBColor(0x06, 0x5A, 0x82)

# Rectangle shapes
shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.5), Inches(5), Inches(3))
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
shape.line.fill.background()  # No border

# Text boxes
txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(8), Inches(1))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Hello World"
p.font.size = Pt(36)
p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
p.font.bold = True
p.font.name = 'Arial'
p.alignment = PP_ALIGN.CENTER

# Multi-line text
p2 = tf.add_paragraph()
p2.text = "Subtitle"
p2.font.size = Pt(18)
p2.font.color.rgb = RGBColor(0xCA, 0xDC, 0xFC)

# Bullet list helper (reusable pattern)
def add_bullet_list(slide, left, top, width, height, items, font_size=14, color=DARK_TEXT, spacing=Pt(6)):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = 'Calibri'
        p.space_after = spacing

prs.save("output.pptx")
```

### Key differences from pptxgenjs

| Aspect | pptxgenjs | python-pptx |
|--------|-----------|-------------|
| Hex colors | `"FF0000"` (no #) | `RGBColor(0xFF, 0x00, 0x00)` |
| Units | Inches as floats | Use `Inches(1.5)` or `Emu(914400)` |
| Shadow | Native support | `shape.shadow.inherit = False` to disable; limited native shadow control |
| Text frames | Rich text arrays with `breakLine: true` | `tf.add_paragraph()` for multi-line |
| Shapes | `pres.shapes.RECTANGLE` | `MSO_SHAPE.RECTANGLE` |
| Charts | Built-in chart engine | Requires `python-pptx-charts` or manual XML |

### Common pitfalls

- **Colors**: Use `RGBColor(0xFF, 0x00, 0x00)` — never pass a 6-char hex string. Python-pptx uses integer RGB tuples, not hex strings.
- **Border off**: Always call `shape.line.fill.background()` unless you want a visible border.
- **No shadow by default**: Python-pptx has limited shadow support. Set `shape.shadow.inherit = False` to suppress inherited template shadows.
- **Text overflow**: Text boxes don't auto-grow. Set generous `h` values and use `tf.word_wrap = True`.
- **Write file first**: Always write the script to a `.py` file (e.g. `/tmp/create_pptx.py`) then run it via `terminal()`. Putting long scripts inline in terminal heredocs may trigger security filters.

### When to use python-pptx vs pptxgenjs

| Scenario | Recommended | Reason |
|----------|-------------|--------|
| Need icons, complex shadows, native charts | **pptxgenjs** | Richer feature set |
| python-pptx already installed, quick slides | **python-pptx** | No npm install needed |
| No Node.js available | **python-pptx** | Python-only environment |
| Script needs to run headless on server | **python-pptx** | Fewer runtime dependencies |
| Need detailed visual control (shapes, cards, overlays) | **python-pptx** | Good shape library |

---

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Visual QA with text-only models

When your active model does NOT support vision (e.g. DeepSeek, text-only models), `vision_analyze` will fail. Do NOT retry with the same approach. Instead:

1. **Content QA first**: `python -m markitdown output.pptx` to verify all text is present, correct, and in right order.
2. **Check for placeholder text**: `python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum"`
3. **Slide count**: `python -m markitdown output.pptx | grep 'Slide number' | wc -l`
4. **Subagent QA**: If you have a vision-capable subagent model configured, delegate QA. Otherwise, content-only QA via `markitdown` is acceptable — python-pptx's deterministic shapes rarely produce layout bugs.

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Dependencies

| Tool | Purpose | Install |
|------|---------|---------|
| `markitdown[pptx]` | Text extraction | `pip install "markitdown[pptx]"` |
| `python-pptx` | Creating/editing slides (fallback) | `pip install python-pptx` |
| `Pillow` | Thumbnail grids | `pip install Pillow` |
| `pptxgenjs` | Creating from scratch (primary, richer features) | `npm install -g pptxgenjs` |
| LibreOffice (`soffice`) | PDF conversion | Auto-configured for sandboxed environments via `scripts/office/soffice.py` |
| Poppler (`pdftoppm`) | PDF to images | System package |

**Note:** If generating from scratch, try `python-pptx` first (no npm install needed). Only install `pptxgenjs` if you need charts, complex shadows, or icons.

---
