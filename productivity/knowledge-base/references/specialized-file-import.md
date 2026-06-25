# 特殊格式文件导入知识库

> XMind(.xmind)、drawio(.drawio)、Visio(.vsd) 格式的知识库导入方法

---

## XMind 脑图 (.xmind)

XMind 文件实际上是一个 ZIP 压缩包，内部包含 XML 或 JSON 格式的内容。

### 格式检测

```python
import zipfile
with zipfile.ZipFile('file.xmind') as z:
    print(z.namelist())
    # 旧版 XMind 8: content.xml (XML格式)
    # 新版 XMind 2020+: content.json (JSON格式)
    # 有时两种同时存在
```

### 解析 content.xml（旧版格式）

```python
import xml.etree.ElementTree as ET
ns = {'x': 'urn:xmind:xmap:xmlns:content:2.0'}
root = ET.fromstring(xml_content)
# 递归提取 x:topic 中的 x:title 即可
```

### 解析 content.json（新版格式）

```python
# 结构: [{ "id": "...", "class": "...", "title": "...",
#          "rootTopic": { "id": "...", "title": "...",
#            "children": { "attached": [ {...} ] } } }]
# children 的 key 是 "attached"（非 "children"）
# 递归提取每个节点的 title 即可
```

### 注意事项

- 校验 `content.json` 中的 `rootTopic.children.attached` 列表
- 深度限制 6-8 层即可，脑图通常不会更深
- 提取后用 `html.unescape()` 解码 HTML 实体
- 导入后创建 YAML frontmatter，tags 包含脑图的核心主题

## drawio 流程图 (.drawio)

drawio 文件是纯文本 XML 格式，但内容可能经过 base64+zlib 压缩编码。

### 格式结构

```xml
<mxfile host="..." modified="..." ...>
  <diagram id="xxx" name="xxx">
    压缩内容或XML内容
  </diagram>
</mxfile>
```

### base64+zlib 解压

```python
import re, base64, zlib
from urllib.parse import unquote

m = re.search(r'<diagram[^>]*>(.*?)</diagram>', content, re.DOTALL)
compressed = m.group(1)

if compressed.startswith('<'):  # 未压缩
    xml_str = compressed
else:
    raw = base64.b64decode(compressed)
    dec = zlib.decompress(raw, -zlib.MAX_WBITS)  # deflate raw
    xml_str = unquote(dec.decode('utf-8'))
```

### 提取文本内容

drawio 内容以 mxGraphModel 格式存储，文本框在 `<mxCell value="..." ...>` 的 `value` 属性中：

```python
vals = re.findall(r'value="([^"]*?)"', xml_str)
decoded = [html.unescape(v) for v in vals if len(v) > 1]
```

### 二进制加密格式（无法自行解析）

部分 drawio 文件以 `b#eE` 开头（十六进制 `62 23 65 45`），这是 draw.io 的加密保存格式，**无密码无法解析**。

检测方法：`xxd -p -l1 file.drawio` 如果返回 `62` 即为加密格式。

处理方式：询问用户是否有密码，无则删除。

## Visio 图表 (.vsd/.vsdx)

### 旧版 .vsd（Binary 格式）

```bash
# LibreOffice 可以转换 .vsd → PDF → PNG
libreoffice --headless --convert-to pdf input.vsd --outdir /tmp/
libreoffice --headless --convert-to png input.vsd --outdir /tmp/

# 从 PDF 提取文本
pdftotext -layout input.pdf output.txt
```

### 新版 .vsdx（基于 XML，同 .docx/.pptx 的 OOXML 格式）

可以直接读取内部 XML 提取文本。

## 导入步骤

1. 转换/提取文本
2. 创建目标 `.md` 文件，含 YAML frontmatter（title, tags, links, created, source）
3. ASCII 时序图或表格化展示流程
4. 放入 `~/knowledge/research/<主题>/`
5. `enzyme refresh` 更新语义索引
