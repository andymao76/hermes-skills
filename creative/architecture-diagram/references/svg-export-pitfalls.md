# SVG 导出常见陷阱与解决方案

## 1. 提取 SVG 的正确方法

从 `.html` 提取 SVG 时，**不要**使用 `read_file` + `execute_code`。
原因：`read_file` 的输出带行号前缀（如 `89|      <svg>`），会破坏 XML。

### 方法 A：写脚本文件再执行（推荐）

当 Python 代码中包含 `&`、`&amp;` 等 shell 敏感字符时，**不要使用 heredoc**，因为 terminal 工具会把 `&` 解释为后台运行符。此时改用写文件再执行：

```bash
# 1. 写脚本文件
cat > /tmp/extract_svg.py << 'EOF'
with open("INPUT.html", "r") as f:
    html = f.read()
start = html.index("<svg ")
end = html.index("</svg>") + len("</svg>")
svg = html[start:end]
with open("OUTPUT.svg", "w") as f:
    f.write(svg)
EOF

# 2. 执行
python3 /tmp/extract_svg.py
```

### 方法 B：terminal + heredoc（仅当代码不含 & 时）

```bash
python3 << 'PYEOF'
with open("INPUT.html", "r") as f:
    html = f.read()
start = html.index("<svg ")
end = html.index("</svg>") + len("</svg>")
svg = html[start:end]
full = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg
with open("OUTPUT.svg", "w") as f:
    f.write(full)
PYEOF
```

**⚠️ 关键陷阱：** Python 代码中含 `&amp;` 或 `&` 字符时，terminal 工具的 shell 解析器会将其解释为后台操作符。解决方法：用方法 A（先写 .py 文件再执行）。

## 2. XML 中必须转义的特殊字符

SVG 是 XML 格式，文本内容中以下字符必须转义：

| 字符 | 转义 | 场景 |
|:---|:---|:---|
| `&` | `&amp;` | `供应商 & 代理` → `供应商 &amp; 代理` |
| `<` | `&lt;` | 少见 |
| `>` | `&gt;` | 少见 |
| `"` | `&quot;` | 少见 |

**检查方法：** 提取 SVG 后，用 XML 解析验证：
```bash
python3 -c "import xml.etree.ElementTree as ET, io
ET.parse(io.StringIO(open('OUTPUT.svg').read()))
print('XML valid')"
```

## 3. 独立 SVG 的头三行规范

```svg
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1180 880"
     style="background-color:#020617;">
```

缺失 `xmlns` → 浏览器提示 "This XML file does not appear to have any style information"
缺失 `style` → 深色主题 SVG 显示在白底上，文字不可见

## 4. Tools 的行号污染问题

`execute_code` 中的 `read_file` 返回格式为 `LINE_NUM|CONTENT`，不能直接用于 XML 提取。
推荐直接用 terminal + heredoc 方案。

## 5. CairoSVG 不读取 CSS background-color

SVG 的 `style="background-color:#XXXXXX;"` 属性在浏览器中正常工作，但 cairosvg 会**完全忽略**它。

**修复：** 渲染前在 `<svg>` 标签后插入显式背景矩形：
```python
svg_body = re.sub(r'(<svg[^>]*>)', r'\1\n<rect width="100%" height="100%" fill="#020617" />', svg_body, count=1)
```

## 6. Emoji 和 Unicode 符号在 CairoSVG 中渲染为 Tofu

CairoSVG 基于系统字体渲染，无法处理 Emoji 和 Unicode 特殊符号。这些在浏览器中正常，但在 PNG 中会变成 tofu 方块 (☒)。

**修复：** 渲染 PNG 前从 SVG 文本中清除所有 emoji 和特殊符号。

## 7. 多个 SVG 根元素拼接（Extra content at the end of the document）

**现象：** 浏览器打开 SVG 时报告 `error on line N at column 1: Extra content at the end of the document`，且只渲染到第一个错误位置。

**根因：** HTML 文件中包含多个独立的 `<svg>...</svg>` 块（架构图 + 流程图拼接）。提取时使用了 `html.rindex("</svg>")` 而非 `html.index("</svg>")`，错误地包含了两个完整的 SVG 元素。XML 只允许一个根元素。

**修复 1 — 只提取第一个 SVG：**
```python
start = html.index("<svg ")
end = html.index("</svg>") + len("</svg>")
```

**修复 2 — 分段提取为多个文件：**
```python
import re
blocks = re.findall(r'<svg[^>]*>.*?</svg>', html, re.DOTALL)
for i, svg in enumerate(blocks):
    with open(f"output_{i+1}.svg", "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n{svg}')
```

**预防：** 提取前先计数：`svg_count = html.count("<svg ")`。如果 > 1，按修复 2 分段提取。

## 8. 生成后验证列表

1. `file OUTPUT.svg` → 应显示 "SVG Scalable Vector Graphics image"
2. XML 解析验证无报错
3. 无未转义的 `&`
4. 以 `<?xml` 开头，有 `xmlns=`
5. HTML 中 `<svg` 出现次数与预期图表数一致