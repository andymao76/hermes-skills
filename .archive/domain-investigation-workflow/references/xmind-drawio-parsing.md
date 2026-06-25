# XMind / Draw.io File Parsing Reference

Knowledge from processing ~16 xmind and ~17 drawio files in a single session.

## XMind (.xmind)

XMind files are **zip archives** with two possible internal formats:

### Old Format (XMind 8)
- Contains `content.xml` with XML namespace `urn:xmind:xmap:xmlns:content:2.0`
- Topics are `<x:topic>` elements under `<x:sheet>/<x:topic>`
- Title in `<x:title>` sub-element
- Children in nested `<x:children>/<x:topics>/<x:topic>` chains

### New Format (XMind 2020+)
- Contains `content.json` — a JSON array, each element is a sheet
- Sheet structure: `{id, class, title, rootTopic: {id, title, children: {attached: [...]}}}`
- Children recursively under `children.attached[]`
- Both `attached` and `detached` child keys exist

### Warning Strings
Some xmind files start with a multi-language warning block:
```
This file can not be opened normally...
该文件无法正常打开...
```
This is **decorative** — the real content is still in content.json/xml inside the zip. Ignore the warning and parse normally.

## Draw.io (.drawio)

Draw.io files are **compressed XML** inside an `<mxfile>` envelope.

### Format Detection
- Check first 5 bytes
- `b'<mxfi'` = XML text format (less common for complex files)
- `b\\x62\\x14\\x23` (starts with `b#`) = binary/encrypted draw.io format, **cannot parse without password**

### XML Format Parsing
```xml
<mxfile host="..." modified="..." ...>
  <diagram id="..." name="...">
    <!-- Base64-compressed URL-encoded mxGraphModel XML -->
  </diagram>
</mxfile>
```

### Decompression Pipeline
```python
import base64, zlib
from urllib.parse import unquote
import re, html

# Extract content between <diagram> and </diagram>
m = re.search(r'<diagram[^>]*>(.*?)</diagram>', content, re.DOTALL)
compressed = m.group(1)

# Decode
raw = base64.b64decode(compressed)                    # base64
dec = zlib.decompress(raw, -zlib.MAX_WBITS)           # deflate (raw, no header)
xml_str = unquote(dec.decode('utf-8'))                # URL decode

# Extract text values from mxCell elements
vals = re.findall(r'value="([^"]*?)"', xml_str)
texts = [html.unescape(v) for v in vals if len(v) > 2]
```

### Common Pitfalls
- The entire diagram content is ONE LINE — `grep` won't find `mxCell` across line boundaries
- `re.DOTALL` is essential for multiline matching
- Some files use base64url encoding (`-` instead of `+`, `_` instead of `/`) — try both
- The decompression uses raw deflate (`-zlib.MAX_WBITS`), not zlib header format

## Visio (.vsd)

Use LibreOffice headless conversion pipeline:

```bash
libreoffice --headless --convert-to pdf input.vsd --outdir /tmp/converted/
pdftotext -layout output.pdf -
# Or for visual inspection:
libreoffice --headless --convert-to png input.vsd --outdir /tmp/converted/
```
