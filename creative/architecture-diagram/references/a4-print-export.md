# A4 Print Export Reference

Full workflow for converting dark-themed architecture HTML/SVG diagrams to A4 300dpi printable PDF + PNG.

## Decision Matrix

| Diagram layout | A4 orientation | Target DPI | Canvas px |
|:---|---:|---:|---:|
| Single wide architecture (viewBox ~1340x1100) | Landscape | 300 | 3508x2480 |
| Single wide architecture (viewBox ~1100x880) | Landscape | 300 | 3508x2480 |
| Two SVGs stacked (arch + flow, ~1440px total) | Portrait | 300 | 2480x3508 |
| Very tall single diagram (>1200px) | Portrait | 200 | 1654x2339 |

## Step 1: Create Print-Optimized HTML

Copy the original diagram HTML and strip everything except the SVG. Remove info cards, footer, font loading, and extra CSS. Keep only the SVG element with its viewBox and preserveAspectRatio.

**CRITICAL: Use a bare-minimum HTML wrapper.** The full CSS layout from the diagram HTML can interfere with Chrome's headless rendering. Use:

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
<!-- SVG element with full content here, no extra HTML wrapping -->
</body>
</html>
```

This ensures the SVG fills the entire viewport without CSS layout interference.

**Landscape template (single wide SVG):**
```css
@page { size: A4 landscape; margin: 8mm; }
body { background: #020617; width: 297mm; height: 210mm; }
.container { width: 281mm; height: 194mm; }
```

**Portrait template (multi-diagram):**
```css
@page { size: A4; margin: 8mm; }
body { background: #020617; width: 210mm; height: 297mm; }
.container { width: 194mm; height: 281mm; display: flex; flex-direction: column; }
section { flex: 1; }
```

Set `preserveAspectRatio="xMidYMid meet"` on each `<svg>` element so resizing doesn't clip.

## Step 2: Chromium Headless HiDPI Screenshot (THE KEY TO QUALITY)

**⚠️ CRITICAL: Never take a low-res screenshot and upscale.** A plain screenshot at 2800x2100 upscaled to 3508x2480 (A4 300dpi) produces BLURRY results. The user will reject these.

Instead, use `--force-device-scale-factor=3` to render the SVG at 3x native resolution. Set the `--window-size` to approximately match the SVG viewBox aspect ratio:

```bash
# Landscape SVG (viewBox 1340x1100 ≈ 1.218:1 → window 1600x1350)
google-chrome-stable --headless=new --no-sandbox --disable-gpu \
  --window-size=1600,1350 \
  --force-device-scale-factor=3 \
  --hide-scrollbars \
  --screenshot=./hidpi.png --default-background-color=020617 \
  file://./minimal-render.html

# Portrait / tall multi-SVG layout (viewBox 1100x1440 total → window 1400x2000)
google-chrome-stable --headless=new --no-sandbox --disable-gpu \
  --window-size=1400,2000 \
  --force-device-scale-factor=3 \
  --hide-scrollbars \
  --screenshot=./hidpi.png --default-background-color=020617 \
  file://./minimal-render.html
```

Why `--force-device-scale-factor=3`? The SVG viewBox coordinates define the logical resolution. By rendering at 3x, a viewBox of 1340x1100 produces an effective 4020x3300 pixel canvas (~3.58 px per viewBox unit). This is crisp even after downscaling to 300dpi A4 (3508x2480 ≈ 2.19 px per viewBox unit = still sharply above 1x).

### Window size rules of thumb

| SVG viewBox | Window size | Effective @3x | Best for |
|:---|---:|---:|:---|
| 1340 x 1100 | 1600 x 1350 | 4800 x 4050 | Hermes (8-layer arch) |
| 1100 x 880 | 1400 x 1150 | 4200 x 3450 | Smartbrain (6-layer arch) |
| 1100 x 560 | 1400 x 750 | 4200 x 2250 | Single flow chart |
| Two SVGs stacked | 1400 x 2000 | 4200 x 6000 | Arch + flow on one page |

The window should be slightly larger than the viewBox to account for any title/label text above the SVG. The aspect ratio difference will produce letterboxing (black bars), which is handled by ImageMagick's `-extent` in the next step.

## Step 3: ImageMagick A4 DPI Resize

```bash
# Landscape 300dpi (from HiDPI PNG)
convert hidpi.png \
  -resize 3508x2480 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center -extent 3508x2480 \
  -quality 100 output-a4.pdf

convert hidpi.png \
  -resize 3508x2480 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center -extent 3508x2480 \
  -quality 100 output-a4.png

# Portrait 300dpi (from HiDPI PNG, two SVGs stacked)
convert hidpi.png \
  -resize x3508 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center \
  -extent 2480x3508 \
  -quality 100 output-a4.pdf

convert hidpi.png \
  -resize x3508 -density 300 -units PixelsPerInch \
  -background "#020617" -gravity center \
  -extent 2480x3508 \
  -quality 100 output-a4.png
```

**Key parameters explained:**
- `-resize 3508x2480` for landscape: fits image into A4 landscape frame (scales by the limiting dimension, adds black bars on the other axis)
- `-resize x3508` for portrait: fits by height, pads left/right to reach 2480px width
- `-background "#020617"`: keeps the letterboxing the same dark background color as the diagram
- `-gravity center`: centers the diagram within the A4 canvas
- `-extent 3508x2480`: expands the canvas to exact A4 dimensions with the background color filling the gaps

## Verification

```bash
identify output-a4.png    # PNG 3508x2480 8-bit sRGB (landscape) or 2480x3508 (portrait)
ls -lah output-a4.png     # Should be >500KB for acceptable quality; 800KB+ is excellent
pdfinfo output-a4.pdf      # single page, A4 page size
```

## Pitfalls

- **`--print-to-pdf` splits pages**: Chrome's native print-to-pdf often splits wide/tall SVGs across 2-4 pages. Always use the screenshot → ImageMagick pipeline instead.
- **`--hide-scrollbars` is essential**: Without it, scrollbars appear in the screenshot.
- **`--force-device-scale-factor` is the quality key**: Without it, the screenshot is at the window pixel resolution (e.g. 1600x1350), which when upscaled to A4 300dpi (3508x2480) produces blurry, pixelated text. The scale factor renders the SVG at higher pixel density natively.
- **Font rendering**: Google Fonts (JetBrains Mono) may not load in headless mode without network. The print-optimized HTML should omit the `fonts.googleapis.com` link — system monospace fallback is adequate for print.
- **Emoji rendering**: Chromium headless renders emoji correctly. No need to strip them for A4 export (unlike CairoSVG).
- **Final PNG file size <200KB**: Indicates poor quality. Re-render with a higher scale factor (4x instead of 3x) or larger window size.
- **ImageMagick `-quality`**: Use `-quality 100` for PNG output to avoid compression artifacts on the dark background. For PDF, `-quality 95` is sufficient since PDF supports lossless image embedding.
- **Multi-diagram layouts (two SVGs stacked)**: Create a single HTML with both SVGs, each sized via CSS `width: 100vw; height: Xvh;`. The screenshot captures both in one render. Use portrait orientation (2480x3508) for the A4 output.
