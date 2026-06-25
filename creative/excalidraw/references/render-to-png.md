# Rendering Excalidraw Files to PNG Images

For generating PNG raster images from `.excalidraw` files without a browser, use the `excalidraw-render` Python package.

## Installation

```bash
pip install excalidraw-render
```

Dependencies: `cairosvg`, `cairocffi`, `fontconfig`, `pillow`.

## Usage

```bash
# Basic PNG render
excalidraw-render diagram.excalidraw -o diagram.png

# SVG output
excalidraw-render diagram.excalidraw -f svg -o diagram.svg

# Batch
excalidraw-render ./diagrams/*.excalidraw
```

## Features

- Pure Python — no Node.js, no browser, no puppeteer
- Produces hand-drawn style (rough.js compatible rendering via cairo)
- Supports container-bound text, arrows, shapes, colors
- Output is a standard PNG at 1280×1024 default resolution

## Pitfalls

- The tool renders to a fixed DPI — text may appear larger/smaller than in the Excalidraw browser app
- **Chinese/CJK text rendering**: excalidraw-render (CairoSVG) does NOT handle Excalidraw's font-family fallback chain correctly for CJK text. Box-contained Chinese text will appear stacked/collapsed when rendered with CairoSVG — the font-family="Virgil, Segoe Print, Comic Sans MS, sans-serif" chain fails to resolve to a CJK-capable font. Fix: export to SVG, replace font-family in the SVG (see "rsvg-convert (for CJK)" section), then use `rsvg-convert` instead of excalidraw-render's built-in CairoSVG pipeline.
- Emoji in text is not supported by cairo rendering — use plain text only
- The hand-drawn look (roughness) is approximated via cairo stroke paths, not pixel-identical to the browser version
- For pixel-perfect output, use excalidraw.com's built-in export or a headless browser screenshot instead
- Run `fc-cache -fv` after installing fonts to ensure cairo finds them

## rsvg-convert (for CJK) — RECOMMENDED FIRST ATTEMPT

**When the diagram contains Chinese/CJK text, skip excalidraw-render's built-in PNG pipeline entirely.** CairoSVG does not resolve Excalidraw's Virgil→sans-serif font chain to a CJK-capable glyph — the result is stacked/collapsed characters. Always use this two-step SVG→PNG pipeline instead.

### A3 300dpi (print-ready)

```bash
excalidraw-render diagram.excalidraw -f svg -o diagram.svg
python3 -c "
with open('diagram.svg', 'r') as f:
    svg = f.read()
svg = svg.replace(
    'font-family=\"Virgil, Segoe Print, Comic Sans MS, sans-serif\"',
    'font-family=\"Noto Sans CJK SC, Noto Sans SC, sans-serif\"'
)
with open('diagram.svg', 'w') as f:
    f.write(svg)
"
rsvg-convert -w 3508 -h 4961 -o diagram.png diagram.svg
```

### Web-friendly (1680px width)

Same commands but with `-w 1680 -h 2420`.

### Sizing guidelines

| Intended Use | Width | Height | Command flags |
|-------------|-------|--------|--------------|
| A3 300dpi print | 3508 | 4961 | `-w 3508 -h 4961` |
| A2 300dpi print | 4961 | 7016 | `-w 4961 -h 7016` *(see note below)* |
| A4 300dpi print | 2480 | 3508 | `-w 2480 -h 3508` |
| Web / social media | 1680 | 2420 | `-w 1680 -h 2420` |
| Discord embed | 1280 | 1810 | `-w 1280 -h 1810` |

**A2 sizing note:** SVG content rarely fills a perfect A2 rectangle. Always compute the actual PNG dimensions from the SVG viewBox:

```bash
# Get SVG viewBox
grep -o 'viewBox="[^"]*"' diagram.svg
# viewBox="30 20 1520 1682"  →  SVG content is 1520×1682
# A2 at 300dpi = 4961×7016, but adjust height to match viewBox ratio:
# height = 4961 * 1682 / 1520 = 5489
rsvg-convert -w 4961 -h 5489 -o diagram.png diagram.svg
```

If the image exceeds Telegram's 4096px limit on one axis, resize:
```bash
python3 -c "
from PIL import Image
img = Image.open('diagram.png')
w, h = img.size
new_w = 3500
new_h = int(h * new_w / w)
img.resize((new_w, new_h), Image.LANCZOS).save('diagram_small.png', optimize=True)
"
```

Always match `rsvg-convert -w/-h` to the SVG's viewBox aspect ratio (check with `grep viewBox diagram.svg`). If the aspect ratio differs, the rendered image will be distorted.

### Post-render platform delivery

After rendering, send the PNG to the user's platforms:

```bash
# Telegram - image must be <4096px on BOTH axes
python3 -c "
from PIL import Image
img = Image.open('diagram.png')
if img.width > 4096 or img.height > 4096:
    w, h = img.size
    scale = min(4096/w, 4096/h)
    img.resize((int(w*scale), int(h*scale)), Image.LANCZOS).save('diagram_tg.png', optimize=True)
    print('Resized for Telegram')
"
# Send via send_message with MEDIA: tag
# Discord accepts up to 25MB, no size concern
# WeChat has rate limits ~1 msg/10s — batch sends may fail with
# "Weixin send failed: iLink sendmessage rate limited"
```

Telegram photo dimension limit: **4096px on either axis**. If exceeded, the send will return `Photo_invalid_dimensions` and the message will send without the image. Always pre-check with PIL and resize if needed.

Discord: no practical dimension limit. Send original high-res.

WeChat (Weixin): rate-limited to approximately 1 message per 8-10 seconds. Back-to-back sends (e.g. same image to 3 platforms) will hit "iLink sendmessage rate limited". Add a 10s delay between WeChat sends or send WeChat last. The error is transient — retry after 10-15s. This rate limit resets on its own within seconds.

## Feature comparison table

| Method | Quality | Dependencies | Speed | CJK | Notes |
|--------|---------|-------------|-------|-----|-------|
| excalidraw-render output → **CairoSVG** | Good | Python, Cairo | Fast | ✅ Correct | **Best for CJK!** See below |
| SVG→rsvg-convert (font-family replaced) | Good | librsvg2-bin | Fast | ⚠️ Fragile | TTC font loading issues |
| **Pillow direct draw** (pure Python) | Acceptable | Pillow | Medium | ✅ Always | **Ultimate fallback** — never fails |
| Headless Chrome (Xvfb screenshot) | Pixel-perfect | Chromium, Xvfb | Slow | ✅ | Overkill for most uses |
| excalidraw.com export | Best | Browser | Manual | ✅ | Best for final publish |

### CJK Rendering — CRITICAL (2026-06-07 discovery)

**NONE of the SVG-based methods reliably render CJK text on Ubuntu 24.04.** Both CairoSVG and librsvg have fundamental issues with TTC (TrueType Collection) fonts — the system's `NotoSansCJK-Regular.ttc` cannot be loaded as a font-family even when the fontconfig name `"Noto Sans CJK SC"` is correctly specified. The result is invisible CJK text (user reports "框图内文字都没有").

**The ONLY reliably working pipeline for CJK on Ubuntu 24.04 is Pillow Direct Draw.** See the "Ultimate Fallback" section below.

**Attempt order for CJK diagrams (stop at first success):**

1. **SVG intermediate + CairoSVG** (may work for simple CJK, fails for dense):
   ```bash
   excalidraw-render diagram.excalidraw -f svg -o diagram.svg
   python3 -c "from cairosvg import svg2png; svg2png(bytestring=open('diagram.svg','rb').read(), write_to='diagram.png', output_width=3508, output_height=4230)"
   ```
   Verify: `python3 -c "from PIL import Image; img=Image.open('diagram.png'); dark=sum(1 for _,p in enumerate(img.crop((img.width//4,20,img.width*3//4,80)).getdata()) if p[0]<100); print('OK' if dark>0 else 'FAIL')"`

2. **If step 1 fails → Pillow Direct Draw** (guaranteed to work). See the dedicated section below.

**NEVER attempt `rsvg-convert` for CJK** — it is strictly worse than CairoSVG. It produces the same invisible CJK text but is slower.

**NEVER embed a TTF/OTF font directly into SVG** (via `@font-face src: url(data:font/...base64...)`) for librsvg — even with a correctly embedded Droid Sans Fallback TTF, librsvg produces invisible text on Ubuntu 24.04.

### Ultimate Fallback: Pillow Direct Draw (when SVG-based methods all fail)

When **all three** SVG-based methods fail (excalidraw-render PNG output has no visible text, rsvg-convert returns blank/transparent text, CairoSVG from SVG also produces invisible glyphs), resort to drawing the entire architecture diagram with Pillow from a Python script. This method never has font issues because it uses Pillow's own font rasterizer, which handles TTF (not TTC) fonts natively.

**Prerequisite: a TTF-based CJK font.** On Ubuntu 24.04, `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf` is the safest choice — it is a single-file TTF (not TTC) with full CJK coverage.

**Architecture of the fallback script:**

```python
from PIL import Image, ImageDraw, ImageFont

W, H = 3508, 4230  # A3 300dpi
img = Image.new('RGB', (W, H), 'white')
draw = ImageDraw.Draw(img)

font = ImageFont.truetype('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', size)

# Draw each section as a rounded rectangle + centered text
def draw_box(draw, x, y, w, h, bg, stroke, radius=20):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=bg, outline=stroke, width=3)

def draw_text_block(draw, x, y, w, h, text, font_size, color):
    font = get_font(font_size)
    lines = text.split('\\n')
    line_height = font_size * 1.4
    total_h = len(lines) * line_height
    start_y = y + (h - total_h) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = x + (w - tw) // 2
        ty = start_y + i * line_height
        draw.text((tx, ty), line, fill=color, font=font)

# ... define color tables, section positions, and call draw_box + draw_text_block for each section ...
img.save('/path/to/output.png', quality=95)
```

**Key design decisions:**
- Use `draw.rounded_rectangle` for boxes (Pillow 10.2+)
- Calculate `line_height = font_size * 1.4` for CJK text (CJK characters need more vertical space than Latin)
- For text-dense boxes (cron, skills), use fontSize=24–26 (at A3 300dpi) — this is larger than SVG fontSize equivalents because Pillow renders at physical resolution
- Use `draw.textbbox` for each line to properly center text horizontally
- Add `top_bottom_margin` = ~10px inside each box
- Arrows: use `draw.line([(x1,y1),(x2,y2)], fill=color, width=2)` — Pillow does NOT support `dash` parameter on `draw.line()` (throws TypeError on Ubuntu 24.04's Pillow 10.2.0)
- After saving the Pillow-rendered PNG, verify text rendering by sampling the title region: `box = img.crop((x1, y1, x2, y2)); dark = sum(1 for _, p in enumerate(box.getdata()) if p[0] < 100)`. If dark > 0, text rendered. Note that **dark pixel count (#1e1e1e = (30,30,30)) is a more reliable indicator than non-white count** — CJK-glyph anti-aliasing may produce gray pixels at edges that the non-white check counts as content even when the glyph is invisible.

**Test font rendering before full draw:**
```python
# Quick test to verify font supports CJK
test_img = Image.new('RGB', (500, 100), 'white')
dd = ImageDraw.Draw(test_img)
font = ImageFont.truetype('/path/to/font.ttf', 40)
dd.text((20, 20), '测试中文ABC', fill=(30,30,30), font=font)
test_img.save('/tmp/font_test.png')
# Check for non-white pixels (indicating glyphs were drawn):
dark = sum(1 for p in test_img.getdata() if p[0] < 100)
print(f'Dark pixels: {dark}')  # Should be > 0
```

**When to use:**
- After trying CairoSVG → SVG → CairoSVG → PNG and verifying title region has 0 dark pixels
- After trying rsvg-convert with font-family replacement and getting the same result
- User reports "框图内文字都没有" after you tried both SVG-based methods

**Do NOT use for quick previews** — the Pillow script takes 30–60s to run and must be written per-diagram. Always try the SVG pipelines first.

### Excalidraw-Native SVG Generation (alternative to PNG)

When the user has a reference Excalidraw SVG (`.svg` file exported directly from excalidraw.com with embedded Nunito WOFF2 font) and asks for a new diagram in the same style, **generate a new SVG directly** rather than going through the `.excalidraw` → `excalidraw-render` → SVG → PNG pipeline.

The reference SVG has these characteristics:
- `viewBox="0 0 ~1382 ~953"`, output `width="~2764" height="~1906"` (2x scale)
- Nunito font embedded via WOFF2 base64 `@font-face` in `<defs>`
- Each element wrapped in `<g transform="translate(x y) rotate(0)">`
- Rounded rectangles drawn as `<path>` with bezier control points (excalidraw's hand-drawn look)
- Text inside `<g>` groups with `font-family="Nunito, sans-serif, Segoe UI Emoji"`
- Arrow paths as `<path>` with `stroke-dasharray="8 6"` for dashed lines

**Workflow:**
1. Extract the `@font-face` CSS block from the reference SVG (the Nunito WOFF2 data)
2. Build the new SVG with the same structure: `<defs>` + `<style>` + background `<rect>` + grouped elements
3. Use the same viewBox proportions (adjust slightly for the new content's aspect ratio)
4. For each box: emit a `<path>` with the excalidraw-style bezier curve for rounded corners, then a `<g>` with the text
5. Save as `.svg` — can be opened in excalidraw.com for further editing, or viewed directly in any browser

**When to use this approach:**
- **User explicitly references an existing `.svg` file** as the desired output format/style
- The diagram is complex (50+ elements) and you need pixel-perfect rendering without the CairoSVG/librsvg font pipeline
- The final deliverable should be editable in excalidraw.com AND render correctly everywhere (browser, Discord, Telegram)

**When NOT to use:**
- User wants a `.excalidraw` file (use the JSON format) or a `.png` (use the render pipeline)
- The diagram is simple (<20 elements) — the `.excalidraw` JSON → render pipeline is faster

**Pitfalls:**
- The hand-drawn `<path>` bezier control points must be symmetric for proper rounded corners — mirror the existing reference SVG's control point pattern exactly
- Nunito font is Latin-only — CJK characters in the diagram will fall back to the system CJK font via `sans-serif`. This produces a visual mismatch between Latin (Nunito) and CJK (system font) text in the same diagram. Accept this trade-off — the alternative (Noto Sans CJK) breaks other rendering paths.
- Do NOT use `<rect rx="...">` — the excalidraw hand-drawn style uses path-based curves, not SVG's native `rx` attribute
- Each `<g>` must have a unique transform; two groups on the same coordinate will cause z-order confusion

### Excalidraw-Native SVG (alternative to .excalidraw + render)

When the user has a reference Excalidraw SVG with embedded Nunito WOFF2 font: extract the `@font-face` block and generate a new SVG directly (see the "Excalidraw-Native SVG Generation" section in the parent skill's SKILL.md). Key points:

- **viewBox must be computed from element bounds**. A formula: `viewBox="0 0 (maxX+30) (maxY+30)"` where maxX/maxY are the farthest x/y of all translated groups plus their widths/heights.
- **Output width/height = 2x viewBox**. E.g. `viewBox="0 0 1382 953"` → `width="2764" height="1906"`.
- **DO NOT use `<rect rx="...">`** for rounded rectangles. Excalidraw uses bezier paths. Mirror the reference SVG's control points exactly.
- **After generating, verify by opening in a browser** before delivery. On GNOME desktop: `DISPLAY=:0 firefox /path/to/file.html` (background the process).

### Verifying font rendering

After rendering, verify that text is not invisible:
```python
from PIL import Image
img = Image.open('diagram.png')
# Check title region for non-white pixels
box = img.crop((img.width//4, 20, img.width*3//4, 80))
non_white = sum(1 for _, p in enumerate(box.getdata()) if p != (255,255,255))
if non_white == 0:
    print('WARNING: Fonts not rendered — switch rendering method')
```
