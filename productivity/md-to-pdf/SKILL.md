---
name: md-to-pdf
category: productivity
description: Markdown 转 PDF 的方法和最佳实践，解决中文渲染问题。处理 md→docx→pdf 完整工作流。
---

# Markdown → PDF 转换（中文支持）

## 问题背景

使用 Chromium headless、wkhtmltopdf、weasyprint 等工具将含中文的 Markdown 转 PDF 时，常出现中文空白/方框问题。原因是这些 WebKit 引擎对中文字体（尤其 TTC/OTF 格式）支持不足，或 Snap 沙箱隔离了系统字体目录。

## 解决思路

### 方案一：md → docx → pdf（最可靠，无需 sudo）

需要 pandoc 和 LibreOffice（系统默认已装）。

```bash
# 1. Pandoc 转 DOCX
pandoc input.md -f markdown -t docx -o output.docx

# 2. LibreOffice 后台导出 PDF
libreoffice --headless --convert-to pdf output.docx --outdir ./
```

- 依赖：`pandoc` + `libreoffice`
- 优点：原生支持中文字体渲染，无字体缺失问题
- 缺点：需要 LibreOffice（较大，但 Ubuntu 桌面版自带）

### 方案二：md → html → pdf（无需 LibreOffice，用 wkhtmltopdf）

```bash
# 1. Pandoc 转 HTML
pandoc input.md -f markdown -t html5 -o output.html

# 2. 用 wkhtmltopdf 转 PDF（需 TTF 字体）
wkhtmltopdf --encoding UTF-8 --page-size A4 \
  --enable-local-file-access output.html output.pdf
```

- ⚠️ wkhtmltopdf 0.12.6 基于旧版 WebKit，对 TTC 字体支持差
- 需用 TTF 格式中文字体（如 Noto Sans CJK SC 的 TTF 版）
- 不推荐用于含 SVG 架构图/图表的文档

### 方案三：HTML → Chrome headless → PDF（含中文/图表，推荐用于复杂排版）

使用 `google-chrome-stable`（非 Snap 版，Snap 版沙箱隔离字体），直接打印 HTML 页面为 PDF。
Skia/PDF 引擎原生支持 OpenType/TrueType 字体嵌入，适合含 SVG 图表、表格、多栏布局的文档。

```bash
google-chrome-stable --headless --disable-gpu \
  --disable-dev-shm-usage --no-pdf-header-footer \
  --print-to-pdf=output.pdf input.html
```

**HTML 布局要点（直接手写 HTML，而非 Pandoc 转）：**
- `@page { size: A4; margin: ... }` — 设置 A4 页面和页边距
- `page-break-after: always` — 每页/每章自动分页
- 字体用 `font-family: 'Noto Sans CJK SC', sans-serif;` — 直接使用系统已安装的 CJK 字体
- SVG 图表用 `<svg>` 内嵌，设置 `viewBox` 缩放、`width` 固定 A4 内宽

**验证字体嵌入：**
```bash
pdfinfo output.pdf | grep -E 'Pages|Page size'
pdffonts output.pdf | head -10
```
确认 `emb=yes` 且 `sub=yes` 表示字体已完整嵌入（NotoSansCJKsc-Regular 和 NotoSerifCJKsc-Bold 已验证）。

**适用场景对比：**

| 场景 | Chrome headless | XeLaTeX | LibreOffice |
|------|----------------|---------|-------------|
| 纯文本排版 | ✅ | ✅ 最佳 | ✅ |
| 含 SVG 架构图/流程图 | ✅ 最佳 | ❌ 困难 | ✅ |
| 表格/多栏布局 | ✅ | ✅ | ✅ |
| 颜色/渐变背景 | ✅ 最佳 | ❌ 有限 | ✅ |
| 字体嵌入 | ✅ Noto/OTF | ✅ TeX | ✅ 系统 |
| 需要 sudo 安装 | ❌ 不需要 | ✅ 需 texlive | ✅ 需 libreoffice |

### 方案四：md → pdf（最优雅，需要 sudo）

```bash
# 先安装 xelatex 和中文宏包
sudo apt install texlive-xetex texlive-lang-chinese
```bash
# 一步到位（推荐参数，已在实战验证）
pandoc input.md \
  -o output.pdf \
  --pdf-engine=xelatex \
  -V mainfont='Noto Sans CJK SC' \
  -V monofont='DejaVu Sans Mono' \
  -V documentclass=report \
  -V geometry:margin=2.5cm \
  -V colorlinks=true \
  -V toc=false \
  -V CJKmainfont='Noto Sans CJK SC'
```

- 依赖：`pandoc` + `texlive-xetex` + `texlive-fonts-extra`（提供 DejaVu 等符号字体）
- 优点：一步到位，排版专业，PDF 体积小（约 LibreOffice 方案的 1/3）
- 缺点：需 sudo 安装 TeX Live（约 200MB）
- 代码块 ASCII 画图符号（`│` `▼` `├` `─`）由 DejaVu Sans Mono 覆盖，emoji（`✅`）暂不支持但不受影响

## 验证 PDF 中文是否正常

不要用二进制搜索（如 `.encode('utf-8') in data`），因为 LibreOffice/xelatex 生成的 PDF 会使用 CID 编码压缩中文字符，不以明文 UTF-8 出现。

正确验证方法：

```bash
# 使用 pdftotext 提取纯文本验证
pdftotext output.pdf - | grep "你的中文关键词"
```

## 常用参数

### pandoc 转 docx

```bash
pandoc input.md \
  -f markdown \
  -t docx \
  --metadata title="文档标题" \
  --reference-doc=template.docx  # 可选：使用自定义模板
  -o output.docx
```

### libreoffice 转 pdf

```bash
# 后台批量转换
libreoffice --headless --convert-to pdf \
  input.docx \
  --outdir ./output_dir/

# 或直接打开后手动导出
libreoffice input.docx
# 文件 → 导出为 PDF
```

### pandoc + xelatex（推荐，排版专业、体积小）

```bash
# 完整参数（已在 2026-06-12 实战验证）
pandoc input.md \
  -o output.pdf \
  --pdf-engine=xelatex \
  -V mainfont='Noto Sans CJK SC' \
  -V monofont='DejaVu Sans Mono' \
  -V documentclass=report \
  -V geometry:margin=2.5cm \
  -V colorlinks=true \
  -V toc=false \
  -V CJKmainfont='Noto Sans CJK SC' \
  -V fontsize=11pt \
  -V linestretch=1.3
```

实测参数说明：
- `fontsize=11pt` — 比默认 10pt 更易读
- `linestretch=1.3` — 1.3 倍行距，适合多段落报告
- `colorlinks=true` — 链接带颜色（PDF 内可点击）
- `monofont='DejaVu Sans Mono'` — 代码块等宽字体，覆盖 ASCII 画图符号（│ ▼ ├ ─）

## 验证 PDF 中文是否正常

```bash
# 提取全部中文内容确认
pdftotext output.pdf - | head -50

# 或搜索特定关键词
pdftotext output.pdf - | grep "中文关键词"
```

> **不要**用二进制搜索（`b'中文'.encode() in data`）— xelatex 生成的 PDF 用 CID 编码压缩中文字符，不以明文 UTF-8 出现。pdftotext 是唯一可靠的验证方法。

## 故障排除

| 现象 | 原因 | 解决 |
|------|------|------|
| PDF 中文为空白/方框 | 中文字体未嵌入 | 用 LibreOffice 方案（方案一） |
| wkhtmltopdf 中文缺失 | 旧版 WebKit 不支持 TTC | 改用 LibreOffice 或 xelatex |
| Chromium --print-to-pdf 中文缺失 | Snap 沙箱隔离字体 | 直接用方案一/方案三 |
| 二进制搜索找不到中文关键词 | CID 编码压缩 | 用 pdftotext 验证 |
| LibreOffice 未安装 | 最小化安装场景 | `sudo apt install libreoffice`（约 200MB） |
| **xelatex 报 `Missing character: There is no ⭐ (U+2B50)`** | 中文字体不含 Emoji 字符 | 不影响排版，Emoji 位置显示为空白。去掉 Markdown 中 Emoji 即可。常见缺失字符：⭐🔴🟡🟢✅ |
| **xelatex 报 `fontspec error: "font-not-found"`** | 指定的字体名称系统未安装 | 用 `fc-list :lang=zh` 确认可用字体，或改用**方案一**（docx⇒pdf，不依赖字体名） |
