# Multi-SVG HTML Extraction Script

When an HTML file contains two or more SVG elements (e.g., architecture diagram + flow chart stacked vertically), extract each to a standalone SVG file.

## Python Script

```python
import re

INPUT_HTML = "input.html"
SVG_PREFIX = "output"

with open(INPUT_HTML) as f:
    html = f.read()

svgs = re.findall(r'<svg[^>]*>.*?</svg>', html, re.DOTALL)
print(f"Found {len(svgs)} SVG(s)")

for i, svg_block in enumerate(svgs):
    vb = re.search(r'viewBox="([^"]+)"', svg_block)
    vb_str = vb.group(1) if vb else "unknown"
    name = {0: "architecture", 1: "flow"}.get(i, f"diagram-{i+1}")

    if 'xmlns="http://www.w3.org/2000/svg"' not in svg_block:
        svg_block = svg_block.replace(
            '<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ')
    if 'background-color:#020617' not in svg_block:
        svg_block = svg_block.replace(
            '<svg ', '<svg style="background-color:#020617;" ')

    def escape_bare_amp(m):
        a = m.group(0)
        if a in ('&amp;', '&lt;', '&gt;', '&quot;', '&apos;') or a.startswith('&#'):
            return a
        return '&amp;'
    svg_block = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', escape_bare_amp, svg_block)

    final = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_block
    out_path = f"{SVG_PREFIX}-{name}.svg"
    with open(out_path, "w") as f:
        f.write(final)

    try:
        import xml.etree.ElementTree as ET
        import io
        ET.parse(io.StringIO(final))
        print(f"  {out_path}  (viewBox={vb_str}, {len(final)} bytes, valid XML)")
    except Exception as e:
        print(f"  {out_path}  XML ERROR: {e}")
```

## Usage

```bash
python3 extract-svgs.py
# Produces: output-architecture.svg, output-flow.svg
```

## Verification

```bash
file output-*.svg
grep -c '</svg>' output-*.svg   # Each should have exactly 1
```

## Known Issues

- If HTML uses nested SVGs (SVG inside SVG), use XML parser instead:
  ```python
  from xml.etree import ElementTree as ET
  tree = ET.parse(INPUT_HTML)
  root = tree.getroot()
  for svg_elem in root.iter('{http://www.w3.org/2000/svg}svg'):
      pass
  ```
- Always verify with `file` and `grep -c '</svg>'` after extraction
