---
name: excalidraw
description: "Hand-drawn Excalidraw JSON diagrams (arch, flow, seq)."
version: 1.3.0
author: Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Excalidraw, Diagrams, Flowcharts, Architecture, Visualization, JSON]
    related_skills: [architecture-diagram]
---

# Excalidraw Diagram Skill

Create diagrams by writing standard Excalidraw element JSON and saving as `.excalidraw` files. These files can be drag-and-dropped onto [excalidraw.com](https://excalidraw.com) for viewing and editing. No accounts, no API keys, no rendering libraries -- just JSON.

## When to use

Generate `.excalidraw` files for architecture diagrams, flowcharts, sequence diagrams, concept maps, and more. Files can be opened at excalidraw.com or uploaded for shareable links.

## Workflow

1. **Load this skill** (you already did)
2. **Write the elements JSON** -- an array of Excalidraw element objects
3. **Save the file** using `write_file` to create a `.excalidraw` file
4. **Optionally upload** for a shareable link using `scripts/upload.py` via `terminal`

### Saving a Diagram

Wrap your elements array in the standard `.excalidraw` envelope and save with `write_file`:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "hermes-agent",
  "elements": [ ...your elements array here... ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  }
}
```

Save to any path, e.g. `~/diagrams/my_diagram.excalidraw`.

### Uploading for a Shareable Link

Run the upload script (located in this skill's `scripts/` directory) via terminal:

```bash
python skills/diagramming/excalidraw/scripts/upload.py ~/diagrams/my_diagram.excalidraw
```

This uploads to excalidraw.com (no account needed) and prints a shareable URL. Requires the `cryptography` pip package (`pip install cryptography`).

### Rendering to PNG (CLI) — CJK-Aware Pipeline

**CairoSVG (used by excalidraw-render) does NOT correctly render CJK text on Ubuntu 24.04.** The font-family chain `"Virgil, Segoe Print, Comic Sans MS, sans-serif"` resolves to system `sans-serif` which uses TTC fonts (Noto Sans CJK SC) that CairoSVG cannot load — producing invisible text. The working pipeline is the SVG intermediate + CairoSVG conversion:

```bash
pip install excalidraw-render
excalidraw-render diagram.excalidraw -f svg -o diagram.svg
python3 -c "
from cairosvg import svg2png
with open('diagram.svg') as f: svg = f.read()
svg2png(bytestring=svg.encode('utf-8'), write_to='diagram.png',
        output_width=3508, output_height=4230)
"
```

**ALWAYS verify font rendering after conversion:**
```python
from PIL import Image
img = Image.open('diagram.png')
box = img.crop((img.width//4, 20, img.width*3//4, 80))
dark = sum(1 for _, p in enumerate(box.getdata()) if p[0] < 100)
if dark == 0:
    print('WARNING: Fonts not rendered — switch to Pillow Direct Draw')
```

For higher resolution / A3 print output, see `references/render-to-png.md`.

**Do NOT use `excalidraw-render`'s direct PNG output** for CJK diagrams — it skips the SVG intermediate and produces 0px fonts on Ubuntu 24.04.

**Do NOT attempt `rsvg-convert` for CJK** — librsvg on Ubuntu 24.04 has TTC font loading issues that produce invisible text even with correct font-family names.

**Ultimate fallback: Pillow Direct Draw.** When both SVG-based methods fail (user reports "框图内文字都没有"), use the Pillow Python script approach documented in `references/render-to-png.md` under the "Pillow Direct Draw" section. Uses `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf` (TTF, not TTC) — never fails for CJK but requires a per-diagram script (~100 lines of Python).

### Importing from an Encrypted Share Link

When a user provides an Excalidraw share URL like `https://excalidraw.com/#json=<docID>,<key>`, use the reusable script:

```bash
node scripts/decrypt-share-link.js <docID> <keyB64> > diagram.excalidraw
```

The script handles the full pipeline: API fetch > AES-GCM decrypt > pako inflate > JSON extraction. See `references/decrypt-share-link.md` for the protocol details.

### Platform Delivery of Rendered PNGs

After rendering, send the PNG to the user's platforms. Watch for:

- **Telegram**: photo dimension limit is 4096px on EITHER axis. Exceed it -> `Photo_invalid_dimensions`. Pre-resize with PIL.
- **Discord**: no dimension limit. Send original high-res PNG.
- **WeChat**: rate-limited to ~1 msg/8-10s. Batch sends across 3 platforms hit "iLink sendmessage rate limited". Send WeChat last or add 10s delay. This error is transient -- retry after 10-15s.

See `references/render-to-png.md` for resize commands and exact limits.

---

## Element Format Reference

### Required Fields (all elements)
`type`, `id` (unique string), `x`, `y`, `width`, `height`

### Defaults (skip these -- they're applied automatically)
- `strokeColor`: `"#1e1e1e"`
- `backgroundColor`: `"transparent"`
- `fillStyle`: `"solid"`
- `strokeWidth`: `2`
- `roughness`: `1` (hand-drawn look)
- `opacity`: `100`

Canvas background is white.

### Element Types

**Rectangle**:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 100 }
```
- `roundness: { "type": 3 }` for rounded corners
- `backgroundColor: "#a5d8ff"`, `fillStyle: "solid"` for filled

**Ellipse**:
```json
{ "type": "ellipse", "id": "e1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Diamond**:
```json
{ "type": "diamond", "id": "d1", "x": 100, "y": 100, "width": 150, "height": 150 }
```

**Labeled shape (container binding)** -- create a text element bound to the shape:

> **WARNING:** Do NOT use `"label": { "text": "..." }` on shapes. This is NOT a valid
> Excalidraw property and will be silently ignored, producing blank shapes. You MUST
> use the container binding approach below.

The shape needs `boundElements` listing the text, and the text needs `containerId` pointing back:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": { "type": 3 }, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{ "id": "t_r1", "type": "text" }] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```
- Works on rectangle, ellipse, diamond
- Text is auto-centered by Excalidraw when `containerId` is set
- The text `x`/`y`/`width`/`height` are approximate -- Excalidraw recalculates them on load
- `originalText` should match `text`
- Always include `fontFamily: 1` (Virgil/hand-drawn font)

**Labeled arrow** -- same container binding approach:
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow",
  "boundElements": [{ "id": "t_a1", "type": "text" }] },
{ "type": "text", "id": "t_a1", "x": 370, "y": 130, "width": 60, "height": 20,
  "text": "connects", "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "a1", "originalText": "connects", "autoResize": true }
```

**Standalone text** (titles and annotations only -- no container):
```json
{ "type": "text", "id": "t1", "x": 150, "y": 138, "text": "Hello", "fontSize": 20,
  "fontFamily": 1, "strokeColor": "#1e1e1e", "originalText": "Hello", "autoResize": true }
```
- `x` is the LEFT edge. To center at position `cx`: `x = cx - (text.length * fontSize * 0.5) / 2`
- Do NOT rely on `textAlign` or `width` for positioning

**Arrow**:
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 200, "height": 0,
  "points": [[0,0],[200,0]], "endArrowhead": "arrow" }
```
- `points`: `[dx, dy]` offsets from element `x`, `y`
- `endArrowhead`: `null` | `"arrow"` | `"bar"` | `"dot"` | `"triangle"` | `"triangle_outline"` | `"chevron"` | `"half_triangle"` | `"half_circle"` | `"circle"` | `"line_arrow"` | `"diamond"` | `"square"` | `"crow"` | `"barb"` | `"spear_head"`
- `strokeStyle`: `"solid"` (default) | `"dashed"` | `"dotted"`

### Arrow Bindings (connect arrows to shapes)

```json
{
  "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": { "elementId": "r1", "fixedPoint": [1, 0.5] },
  "endBinding": { "elementId": "r2", "fixedPoint": [0, 0.5] }
}
```

`fixedPoint` coordinates: `top=[0.5,0]`, `bottom=[0.5,1]`, `left=[0,0.5]`, `right=[1,0.5]`

### Drawing Order (z-order)
- Array order = z-order (first = back, last = front)
- Emit progressively: background zones -> shape -> its bound text -> its arrows -> next shape
- BAD: all rectangles, then all texts, then all arrows
- GOOD: bg_zone -> shape1 -> text_for_shape1 -> arrow1 -> arrow_label_text -> shape2 -> text_for_shape2 -> ...
- Always place the bound text element immediately after its container shape

### Sizing Guidelines

**Font sizes (standard diagrams, <20 elements):**
- Minimum `fontSize`: **20** for titles and headings
- Minimum `fontSize`: **16** for body text, labels, descriptions
- Minimum `fontSize`: **14** for secondary annotations only (sparingly)

**Font sizes (dense diagrams, 50+ elements / system-architecture style):**
- Titles: **22** (one per diagram)
- Section headers: **16**
- Box-contained body text: **12-13**
- Cron/table/text-dense boxes: **11**
- Smaller fonts are expected when fitting many sections onto one canvas (A3, A2, etc.)
- When using fontSize < 14, verify rendering via `references/render-to-png.md`
- If user reports text overlap/stacking, the fix is NOT larger fonts -- use CairoSVG or Pillow fallback
- Minimum practical fontSize for A3/A2 dense diagrams: **11**
- Minimum fontSize for CairoSVG rendering: **14** (below this, CJK text becomes illegible)

**Element sizes:**
- Minimum shape size: 120x60 for labeled rectangles/ellipses
- Leave 20-30px gaps between elements minimum (standard)
- Prefer fewer, larger elements over many tiny ones
- For dense system-architecture diagrams (A3/A2 canvas, 50+ elements): elements can be as small as 55x45 with font 11-12

### Color Palette

See `references/colors.md` for full color tables. Quick reference:

| Use | Fill Color | Hex |
|-----|-----------|-----|
| Primary / Input | Light Blue | `#a5d8ff` |
| Success / Output | Light Green | `#b2f2bb` |
| Warning / External | Light Orange | `#ffd8a8` |
| Processing / Special | Light Purple | `#d0bfff` |
| Error / Critical | Light Red | `#ffc9c9` |
| Notes / Decisions | Light Yellow | `#fff3bf` |
| Storage / Data | Light Teal | `#c3fae8` |

### Tips
- Use the color palette consistently across the diagram
- **Text contrast is CRITICAL** -- never use light gray on white backgrounds. Minimum text color on white: `#757575`
- Do NOT use emoji in text -- they don't render in Excalidraw's font
- For dark mode diagrams, see `references/dark-mode.md`
- For larger examples, see `references/examples.md`
- For decrypting encrypted share links (`#json=<docID>,<key>`), see `references/decrypt-share-link.md`
- For rendering to PNG (especially CJK text), see `references/render-to-png.md`
- For user-requested print-layout corrections ("字体缩小，画布为A3，充满画布"), see `references/relayout-for-print.md`
- For platform delivery quirks (Telegram 4096px limit, WeChat rate limiting), see `references/platform-delivery.md`

## Print-Ready Layout Workflow

When the user asks for an A3/print-ready version of an existing diagram, follow this sequence:

1. **Generate a fresh `.excalidraw` file** via a Python script that repositions all elements onto an A3-proportion canvas (~850 SVG units wide, ~1370 tall, roughly 1:1.6). See `references/relayout-for-print.md` for the exact element-mapping technique.
2. **Calculate box heights** for text-dense boxes using the formula in `references/relayout-for-print.md` (lines × (fontSize + 5) + 10). Underestimating is the #1 cause of user-visible clipping.
3. **Verify no overlaps** with the bounding-box intersection check in `references/relayout-for-print.md`.
4. **Render to PNG** via `references/render-to-png.md` -- prefer CairoSVG from SVG, fall back to Pillow direct draw if fonts are invisible.
5. **Verify font rendering** by sampling the title region with PIL and checking for non-white pixels.
6. **Send the resulting PNG** to the user's platforms with `send_message` + MEDIA: tag. Pre-resize for Telegram's 4096px limit.

## Excalidraw-Native SVG Generation

When the user provides a reference Excalidraw SVG (exported from excalidraw.com, with embedded Nunito WOFF2 font) and says "参考...svg 的风格", **generate a new SVG directly** rather than going through .excalidraw JSON + render.

### When to use

- User provides or references an `.svg` file and wants the same style
- The diagram has 20+ elements and the deliverable should render correctly everywhere (browser, Discord, Telegram) without the font rendering pipeline
- The output should be editable by dragging into excalidraw.com

### When NOT to use

- User wants `.excalidraw` JSON (for further AI editing) → use the JSON format
- User wants PNG → use the render pipeline in `references/render-to-png.md`
- The diagram is small (<10 elements) → .excalidraw JSON is faster

### Reference SVG structure

```xml
<?xml version="1.0" standalone="no"?>
<svg viewBox="0 0 ~1382 ~953" width="~2764" height="~1906">
  <defs>
    <style class="style-fonts">
      @font-face { font-family: Nunito; src: url(data:font/woff2;base64,...); }
    </style>
  </defs>
  <rect x="0" y="0" width="1382" height="953" fill="#ffffff"/>
  <!-- each element in its own <g> -->
  <g transform="translate(x y) rotate(0)">
    <path d="M32 0 C103.8 -1.8, ... Z"...  <!-- rounded rect via bezier path -->
  </g>
  <g transform="translate(x y) rotate(0)">
    <text x="0" y="15.3" font-family="Nunito,..." font-size="16px" ...>text</text>
  </g>
</svg>
```

### Key rules

- **Extract the `@font-face { ... }` block** from the reference SVG and reuse it verbatim -- it contains the Nunito WOFF2 base64 data. DO NOT hardcode font data.
- **Rounded rectangles** use excalidraw's bezier path format (NOT `<rect rx="...">`). Mirror the control-point pattern from the reference SVG exactly:
  - Fill path: `M{r} 0 C{r*2.5} -1.5 ... Z`
  - Both fill and stroke paths are separate `<path>` elements inside one `<g>`
- **Each element** gets its own `<g transform="translate(x y) rotate(0)">`
- **Text elements** use `font-family="Nunito, sans-serif, Segoe UI Emoji"` and `style="white-space: pre;" direction="ltr" dominant-baseline="alphabetic"`
- **Multi-line text**: each line is a separate `<text>` element inside the same `<g>`, with `y` incremented by `fontSize × 1.4` per line
- **Arrows**: simple SVG `<path>` with `d="M{x1} {y1} L{x2} {y2}"` and `stroke-dasharray="8 6"` for dashed lines

### CJK text note

Nunito is a Latin-only font. CJK characters in the diagram fall back to `sans-serif` (system font). This creates a visual style mismatch between Latin (Nunito rounded) and CJK (system sans). Accept this -- the alternative (embedding a CJK font) produces a 16+MB SVG.

### Pitfalls

- **viewBox vs actual content**: Always compute the SVG's viewBox from the actual element bounds (min/max x/y of all groups) and add 30px padding. A tight viewBox clips content; a loose one wastes space.
- **Text y-position**: Excalidraw text uses `dominant-baseline="alphabetic"`. The y-coordinate is ~0.954 × fontSize above the baseline. In your Python generator, compute `y = container_y + fontSize * 0.75`.
- **Path symmetry**: The excalidraw bezier control points must be symmetric for visual consistency. Mirror the existing pattern exactly -- never hand-write bezier control points.
- **DO NOT hardcode Nunito font data**: Always extract from the reference SVG. The font data changes across excalidraw versions. If no reference SVG exists, fall back to `.excalidraw` JSON mode.
- **Save as `.svg`**: The generated SVG can be opened directly in excalidraw.com for further editing, or viewed in any browser. Save to a path like `~/Hermes-architecture.svg`.
- **Test in browser**: After generating, open the SVG in a browser to verify rendering before delivering. Use `DISPLAY=:0 firefox file:///tmp/review.html` if on a desktop with X display.
