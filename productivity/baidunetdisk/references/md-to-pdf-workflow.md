# Markdown → PDF 导出工作流

将 Markdown 文档导出为 PDF（含中文渲染）。

## 工具链

```
Markdown ──pandoc──▶ HTML ──chromium──▶ PDF
                         │
                    注入 CSS 样式
                    (字体/表格/代码块)
```

## 步骤

### 1. Pandoc 转 HTML

```bash
pandoc input.md -f markdown -t html5 -o output.html
```

### 2. 注入 CSS（中文优化）

```html
<style>
body { font-family: 'Noto Sans SC', 'Source Han Sans CN', sans-serif;
       max-width: 900px; margin: 0 auto; padding: 40px 50px;
       font-size: 14px; line-height: 1.7; color: #1a1a1a; }
h2 { border-bottom: 2px solid #2c5f8a; padding-bottom: 4px; color: #1a3a5c; }
pre { background: #f5f5f5; border-left: 3px solid #2c5f8a;
      padding: 10px 14px; font-size: 12px; }
table { width: 100%; border-collapse: collapse; }
th { background: #2c5f8a; color: #fff; }
</style>
```

替换 `</head>` 位置注入即可。

### 3. Chromium Headless → PDF

```bash
chromium --headless --disable-gpu --no-sandbox \
  --print-to-pdf=/path/to/output.pdf \
  "file:///path/to/output.html"
```

### 注意事项

1. **chromium 路径**：snap 版本是 `/snap/bin/chromium`，apt 版本是 `chromium-browser`
2. **文件路径**：chromium snap 对 `~` 和 `$HOME` 不解析，必须使用绝对路径
3. **输出路径**：`--print-to-pdf` 支持 `/home/user/Documents/file.pdf`，`/tmp/` 也可
4. **URL 参数**：chromium 的 `file://` URL 路径中不能有中文，需先复制到无中文路径
5. **非 snap 备选**：`wkhtmltopdf` 更轻量但中文渲染差（缺字体 fallback），不推荐
