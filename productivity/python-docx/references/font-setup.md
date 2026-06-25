# CJK Font Configuration for python-docx

## Core Pattern

The critical line that makes Chinese characters render correctly:

```python
from docx.oxml.ns import qn

style = doc.styles['Normal']
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
style.font.name = 'Arial'  # Latin fallback — keeps numbers/English in a sans-serif font
```

## Why This Is Needed

- `font.name` only sets the `w:ascii` / `w:hAnsi` attributes in the XML
- `qn('w:eastAsia')` sets the `w:eastAsia` attribute specifically for CJK characters
- Without the eastAsia setting, Chinese text renders as square boxes (`□`) or a fallback font on Chinese systems

## Recommended Fonts

| Font Name | Use Case | Notes |
|-----------|----------|-------|
| `微软雅黑` | Body text, general purpose | Modern, clean, most commonly expected |
| `宋体` | Formal documents, academic | Traditional serif, government standard |
| `黑体` | Headings, emphasis | Bold sans-serif, good for titles |
| `楷体` | Quotes, annotations | Script-style, casual |

## Per-Element Override

```python
run = paragraph.add_run('中文文本')
run.font.name = '黑体'
run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
```

## Verification

Best way to verify: open the generated `.docx` on a Chinese Windows/Mac system. If text renders correctly, font config is correct.

Alternatively, inspect the XML:

```python
from lxml import etree
import zipfile
with zipfile.ZipFile('output.docx', 'r') as z:
    xml = z.read('word/document.xml')
    root = etree.fromstring(xml)
    # Check for w:eastAsia attribute in rFonts elements
    for el in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts'):
        print(etree.tostring(el, pretty_print=True).decode())
```
