# Relayout Excalidraw Elements for A3 / Print-Ready Canvas

When a user has an existing architecture diagram (50+ elements) and asks for print-ready output — "字体缩小，画布为A3，充满画布" — the Excalidraw JSON must be rewritten with new coordinates for every element.

**DO NOT** try to fix text overlap by increasing font sizes or scaling the output PNG. The fix is a full coordinate remap of the `.excalidraw` JSON.

## Canvas Strategy

| Intended output | SVG viewBox | Canvas units | Row layout | Aspect ratio |
|----------------|-------------|--------------|------------|--------------|
| A3 300dpi | ~850×1370 | A3 ≈ 1:1.414 | 3–4 rows × 2 cols | ~1:1.6 |
| A2 300dpi | ~1520×1682 | A2 ≈ 1:1.414 | 4 rows × 2 cols (wider) | ~1:1.1 (wider than A3) |
| A4 300dpi | ~600×850 | A4 ≈ 1:1.414 | 2–3 rows × 2 cols | ~1:1.42 |
| Wide slide (16:9) | ~960×540 | 16:9 | 2 rows × flexible cols | ~1.78:1 |

### A2 vs A3 Layout Differences

A2 is both wider and taller than A3. The extra width means:
- Left column can stay ~620px (up from 430px) — more room for MCP grid items
- Right column grows to ~860px — fits wider text boxes for storage/knowledge sections
- Legend can be a **single horizontal row** (6 items side-by-side) instead of stacked vertically — saves ~200px of vertical space
- 4 rows of content fit comfortably (vs 3 rows in A3) with 25–35px gaps between all blocks

### Font sizes per canvas size

| Element type | Original (unconstrained) | A3 | A2 |
|-------------|-------------------------|---|----|
| Main title | 28 | 22 | 24 |
| Section headers | 20 | 16 | 17 |
| Box-contained body | 16 | 13 | 14 |
| Text-dense boxes (cron/table) | 14 | 11–12 | 12 |
| Small annotation | 14 | 11 | 12 |

## Element Coordinate Remapping Technique

The core approach is a Python script that:

1. **Reads the existing `.excalidraw` JSON**
2. **Assigns new y positions** to each element via a lookup dict (keyed by element `id`)
3. **Assigns new x/w/h** for elements in each column
4. **Rewrites arrow bindings** to match new element positions

### Key Implementation Pattern

```python
import json

with open('diagram.excalidraw', 'r') as f:
    doc = json.load(f)

elements = doc['elements']

# Define A3 canvas: 850 × 1370 SVG units
# Left column: x=50, w=430  |  Right column: x=520, w=480

# Y-position map: one entry per logical row
y_map = {
    'title': 40,            # Large title
    'subtitle': 75,         # Subtitle line
    'section_headers': 120,  # All section headers
    # ... per-element entries ...
}

for el in elements:
    eid = el.get('id', '')

    if eid in ('t_title',):
        el['x'] = CANVAS_W // 2 - 300
        el['y'] = y_map['title']
        el['fontSize'] = 22   # Reduced from original 28

    elif eid in ('r_provider', 'r_gateway', 'r_skills', 'r_cron'):
        el['x'] = 50
        el['y'] = y_map[eid]
        el['width'] = 430
        el['height'] = <calculated_height>

    elif eid in ('t_provider', 't_gateway', 't_skills', 't_cron'):
        el['x'] = 55
        el['y'] = y_map[eid] + 5
        el['width'] = 420
        el['height'] = <calculated_height>
        el['fontSize'] = 12

    # ... continue for all elements ...

# Arrow endpoint rebinding is critical — update x/y/points/startBinding/endBinding
# for every arrow element to match the new shape positions.

doc['elements'] = elements  # Preserve original z-order
with open('diagram_a3.excalidraw', 'w') as f:
    json.dump(doc, f, ensure_ascii=False, indent=2)
```

## Box Height Calculation — CRITICAL TO GET RIGHT

When relayout involves text-dense boxes (Cron jobs, Skills list, knowledge base), **calculate the required box height before writing the layout script**. If the box is too small, text will overflow and become invisible in the rendered PNG.

### Formula

```python
required_height = line_count * (fontSize + baseline_padding) + top_bottom_margin
```

Where:
- `line_count` = number of lines in the text (split by `\n`)
- `fontSize` = the HTML5/accepted font size for that text element
- `baseline_padding` = ~4–5px (the gap between lines that Excalidraw's autoResize adds)
- `top_bottom_margin` = ~10px (5px top + 5px bottom inset)

### Quick Reference

| Text | Lines | FontSize | min box height | safe box height |
|------|-------|----------|----------------|-----------------|
| Cron jobs (6 items) | 15 | 11 | 15*(11+5)+10 = 250 | 280 |
| Skills list (9 items) | 12 | 12 | 12*(12+5)+10 = 214 | 240 |
| Knowledge base | 8 | 11 | 8*(11+5)+10 = 138 | 150 |
| Gateway adapter list | 8 | 13 | 8*(13+5)+10 = 154 | 170 |

### Verification Step

After running the relayout script, independently verify box sizes in Python:
```python
for el in elements:
    eid = el.get('id', '')
    if eid.startswith('r_') and el.get('type') == 'rectangle':
        # Find the corresponding text element
        for t in elements:
            if t.get('containerId') == eid:
                lines = t.get('text', '').split('\\n')
                fs = t.get('fontSize', 14)
                needed = len(lines) * (fs + 5) + 10
                actual = el.get('height', 0)
                if needed > actual:
                    print(f'WARNING: {eid} needs {needed}px but has {actual}px')
```

### Overlap Detection

Always run a bounding-box overlap check after relayout:

```python
rects = []
for el in elements:
    if el.get('type') == 'rectangle':
        rects.append((el['id'], el['x'], el['y'],
                      el['x']+el['width'], el['y']+el['height']))

for i, (id1, x1, y1, x1e, y1e) in enumerate(rects):
    for j, (id2, x2, y2, x2e, y2e) in enumerate(rects):
        if i >= j: continue
        ox = max(0, min(x1e, x2e) - max(x1, x2))
        oy = max(0, min(y1e, y2e) - max(y1, y2))
        if ox > 0 and oy > 0:
            print(f'OVERLAP: {id1} + {id2} overlap={ox}x{oy}')
```

If overlap ≥ 1px in both axes, fix by increasing the gap between rows or shifting one box.

### Post-Render Feedback: "框太小" / "没有包含所有文字"

If the user reports text overflow:
1. Calculate `required_height` per the formula above
2. Increase the box's `height` and the contained text's `height` in the `.excalidraw` JSON
3. Shift all subsequent elements (below the enlarged box) downward by `(new_height - old_height)`
4. Also shift the legend and any element visually below the affected area
5. Re-render via SVG→rsvg-convert

### Post-Render Feedback: "框图内文字都没有"

If the user reports that box text is entirely invisible in the PNG:
- **POSSIBLE CAUSE 1**: The SVG-based render pipeline (CairoSVG or rsvg-convert) failed to rasterize CJK glyphs. Verify with `PIL` pixel check on the title region. If `non_white == 0`, switch to the "Pillow Direct Draw" fallback in `references/render-to-png.md`.
- **POSSIBLE CAUSE 2**: The text color is too close to the box background color (e.g. `#1971c2` dark blue on `#a5d8ff` light blue). This is actually a *contrast* issue, not an *invisible* issue — the text IS there but hard to read. Verify with the dark-pixel count (`p[0] < 40`) instead of non-white count. If text exists but is low-contrast, either darken the text color or lighten the background.
- **POSSIBLE CAUSE 3**: box height < required text height, causing CairoSVG to clip the text. Check the box height vs `required_height` formula. Even if Excalidraw's autoResize handles overflow in-browser, CairoSVG may not respect the same overflow rules.

## Legend Layout

When you need a legend for 6+ color-coded categories on an A3/A2 canvas:

- **A3 canvas** (~850 wide): Place legend at bottom left, stack items vertically (6 items × 30px each = 180px + title). This fits in the left column.
- **A2 canvas** (~1520 wide): Place legend as a **single horizontal row** at the bottom, 6 items × ~200px each = 1200px (fits in 1520px width). This saves ~150px of vertical space compared to stacking.
- **Font size**: 12–13 for A3, 12–14 for A2.
- Legend box: 30×22px color rectangle + text label to its right.
- Use the same color palette as the diagram sections for consistency.
- Position legend below the lowest content box row, with 50–70px gap.

## Font Size Guidelines for Dense Diagrams

| Element type | Original size | A3 print-reduced size |
|-------------|--------------|----------------------|
| Main title | 28 | 22 |
| Section headers | 20 | 16 |
| Box-contained body | 16 | 13 |
| Text-dense boxes (cron/table) | 14 | 11–12 |
| Small annotation | 14 | 11 |

## Pitfalls

- **Don't use `scale` / `transform` on the SVG** — it makes fonts illegible. Remap each element's coordinates individually.
- **Arrow binding rebinding** is the most fragile part. Update `startBinding.elementId`, `endBinding.elementId`, `fixedPoint`, and the arrow's `x`/`y`/`points` metadata. Excalidraw ignores arrows whose bindings point to missing element IDs.
- **Preserve element z-order** — the array order IS the draw order. Background zones first, then shapes, then their bound text, then arrows.
- **All `text` elements** in the new layout need `fontSize` explicitly set — auto-sizing doesn't re-calculate for text in containers.
- **`originalText`** must match `text` on every text element or Excalidraw will reset content on load.
- **MCP sub-grid within a column**: when a section (like MCP) has 6 boxes, split into 2 columns of 3. Use `mx = col_x + subcol_index * (subcol_width + gap)`. The subcol_width = (column_width - gap) // 2 to fit exactly.
- **Never rely on hardcoded byte offsets** in the inflated data after decryption — always find `{` position for JSON start.
- **Test the resulting A3 `.excalidraw` file** by opening at excalidraw.com before rendering to PNG — visual verification catches coordinate errors faster than re-rendering.
- **Avoid hardcoded vertical positions** — compute them from a shared base offset so shifting one row doesn't cascade into manual edits of 20+ element y values.
- **WeChat rate limiting**: Sending images to WeChat triggers ~1 msg/8-10s rate limit. When batch-sending to 3 platforms (Telegram/Discord/WeChat), the WeChat send will fail with "iLink sendmessage rate limited". Always send WeChat LAST in the batch, and if it fails, wait 10-15s before retrying. The rate limit resets on its own within seconds. Do NOT retry more than 3 times.
- **Do NOT send raw `.excalidraw` files via send_message MEDIA:** on Telegram, these files do not render as inline previews. Always convert to PNG first. For Discord and WeChat, `.excalidraw` files may be sent as documents alongside the PNG, but the PNG is the primary deliverable.
- **When user provides a reference `.svg`** exported directly from excalidraw.com: the user wants the NEW diagram in the SAME format (Nunito font embedded, `<g transform>` per element, hand-drawn `<path>` for boxes). Do NOT go through the `.excalidraw` JSON → excalidraw-render → SVG pipeline. Generate the SVG directly to match the reference format (see `references/render-to-png.md` section "Excalidraw-Native SVG Generation").
- **Keep track of which diagram version is which**: after 5+ iterations (v1 CairoSVG, v2 rsvg-convert, v3 A2 relayout, v4 CairoSVG A3, v5 Pillow, v6 direct SVG), the user will expect clear version tracking. Name output files with a consistent scheme: `diagram_v1.png`, `diagram_v2.excalidraw`, etc. The final SVG should replace the reference file's filename scheme (e.g. `Hermes-2026-06-07-architecture.svg` for a new architecture diagram generated on that date).

## Full Example

See `/home/andymao/excalidraw_exported.excalidraw` (65 elements, exported from encrypted share link) and `/home/andymao/system_architecture_a3.excalidraw` (same content remapped to A3 canvas) for a production-grade reference.

The A3 remap script from this session is at the bottom of `references/relayout-for-print.md` in the conversation history (session 2026-06-07).
