# Platform Delivery for Architecture Diagram PNGs

After rendering a diagram PNG, the user typically wants it sent to 3 platforms: Telegram, Discord, and WeChat. Each has specific constraints.

## Send Order (Critical for WeChat Rate Limits)

WeChat limits outgoing messages to approximately 1 per 8-10 seconds. Sending the same image to all 3 platforms in rapid succession will trigger:

```
Weixin send failed: iLink sendmessage rate limited
```

**Recommended send order:**
1. **Telegram first** — has the 4096px dimension limit (see below), so catch this early
2. **Discord second** — no dimension limit, always works
3. **WeChat last** — add a 10s delay before sending, or accept the rate limit and retry once

The WeChat rate limit is **transient** — retrying after 10-15s always succeeds.

## Telegram Dimension Limits

Telegram rejects photos with either axis exceeding **4096px** with:
```
Photo_invalid_dimensions
```

The message text is sent, but the image is silently dropped.

**Fix:** Pre-resize to 3500px on the longest axis:

```python
from PIL import Image
img = Image.open('diagram.png')
w, h = img.size
if max(w, h) > 3500:
    scale = 3500 / max(w, h)
    img.resize((int(w*scale), int(h*scale)), Image.LANCZOS).save('diagram_tg.png', optimize=True)
```

Or just always send a 3500px-wide version to Telegram:
```python
img = Image.open('diagram.png')
w, h = img.size
new_w = 3500
new_h = int(h * new_w / w)
img.resize((new_w, new_h), Image.LANCZOS).save('/tmp/arch_tg.png', optimize=True)
```

## Discord — No Limits

Discord accepts up to 25MB file size with no dimension restrictions. Send the original high-res PNG to Discord.

## A3/A2 PNG Dimension Reference

| Format | SVG viewBox | 300dpi PNG | Notes |
|--------|-------------|------------|-------|
| A3 | ~1190×1435 | 3508×4230 | Good for 5+ row diagrams |
| A2 | ~1520×1682 | 4961×5489 | Too tall for Telegram directly |
| Custom fit | Varies | 3508×~4200 | Compute: `h = 3508 * svgH / svgW` |

When rendering for A3/A2, always compute the actual PNG dimensions from the SVG viewBox ratio rather than assuming fixed values:

```bash
grep -o 'viewBox="[^"]*"' diagram.svg
# viewBox="10 15 1230 1475"  → content is 1230×1475
scale = 3508 / 1230
png_h = 1475 * scale  # = ~4200
rsvg-convert -w 3508 -h 4200 -o diagram.png diagram.svg
# OR with CairoSVG:
python3 -c "from cairosvg import svg2png; svg2png(bytestring=open('diagram.svg','rb').read(), write_to='diagram.png', output_width=3508, output_height=4200)"
```
