# draw.io 文件解压参考

## 格式说明

draw.io（>=14.x）的 `.drawio` 文件使用 **三层编码**：

```
.diagram 标签内文本 → URL编码 + base64 + zlib deflate(原始格式)
              ↓
        原始 XML (mxGraphModel format)
```

## 解压代码

```python
import re, base64, zlib, urllib.parse

fname = 'diagram.drawio'
raw = open(fname, 'r', encoding='utf-8').read()

# Step 1: 提取 diagram 标签内容
m = re.search(r'<diagram[^>]*>(.*?)</diagram>', raw, re.DOTALL)
compressed = m.group(1).strip()

# Step 2: base64 解码
decoded = base64.b64decode(compressed)

# Step 3: zlib deflate (raw, wbits=-15)
xml_bytes = zlib.decompress(decoded, -15)

# Step 4: URL decode
text = urllib.parse.unquote(xml_bytes.decode('utf-8'))

# === 提取单元格值 ===
vals = re.findall(r'value="([^"]*)"', text)
for v in vals:
    # 解码 HTML 实体
    clean = v.replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&amp;', '&')
    clean = clean.replace('&#xa;', '\n').replace('<br>', ' | ')
    clean = re.sub(r'<[^>]+>', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if clean:
        print(f'  {clean}')

# === 提取连线 ===
cells = {}
for cell in re.finditer(r'<mxCell\s+([^>]*)/?>', text):
    attrs = cell.group(1)
    mid = re.search(r'id="([^"]*)"', attrs)
    mval = re.search(r'value="([^"]*)"', attrs)
    msrc = re.search(r'source="([^"]*)"', attrs)
    mtgt = re.search(r'target="([^"]*)"', attrs)
    vid = mid.group(1) if mid else ''
    vval = urllib.parse.unquote(mval.group(1)) if mval else ''
    src = msrc.group(1) if msrc else ''
    tgt = mtgt.group(1) if mtgt else ''
    # Clean value
    vval = vval.replace('&lt;', '<').replace('&gt;', '>')
    vval = re.sub(r'<[^>]+>', '', vval)
    vval = re.sub(r'\s+', ' ', vval).strip()
    cells[vid] = {'val': vval, 'src': src, 'tgt': tgt}

print('\n=== 连线关系 ===')
for cid, c in cells.items():
    if c['src'] and c['tgt']:
        sv = cells.get(c['src'], {}).get('val', '?')[:40]
        tv = cells.get(c['tgt'], {}).get('val', '?')[:40]
        print(f'  {sv}  -->  {tv}')
```

## 难点

- **wbits 参数**：draw.io 使用 raw deflate（无 zlib 头），必须传 `-15`。`15`（标准 zlib）或 `31`（gzip）都解不出
- **URL 编码**：解压后的 XML 是 URL 编码的，`%3C`=`<`、`%3E`=`>`、`%22`=`"`，需 `urllib.parse.unquote`
- **HTML 实体**：`value` 属性中的 `<font style="...">` 等 HTML 标签需用 `re.sub` 剥除
- **新旧格式**：早期 draw.io 可能用不同压缩方式，但 14.x 版本后统一为此格式
