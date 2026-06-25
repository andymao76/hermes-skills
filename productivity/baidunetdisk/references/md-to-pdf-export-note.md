# Markdown → PDF 导出注意事项（Ubuntu 24.04 Wayland）

## 已知问题

以下工具在 Ubuntu 24.04 Wayland 环境下**无法生成含中文的PDF**：

| 工具 | 原因 |
|------|------|
| **Chromium snap** (`--headless --print-to-pdf`) | snap 沙箱隔离限制字体访问，PDF 生成白页无文字 |
| **wkhtmltopdf 0.12.6** | 基于旧版 WebKit (Qt)，不支持 OTF/TTC 字体格式 |
| **WeasyPrint** (纯Python) | 同样不能解析系统已安装的 CJK TTC 字体 |

## 唯一确认可靠方案

```bash
# 1. Markdown → DOCX（保留全部格式）
pandoc report.md -f markdown -t docx -o report.docx

# 2. DOCX → PDF（LibreOffice 原生支持中文字体）
libreoffice --headless --convert-to pdf report.docx --outdir ./
```

## PDF 验证方法

LibreOffice 生成的 PDF 使用 CID 编码嵌入中文，不能用二进制方法查找 UTF-8 字符串：

```bash
# ✅ 正确验证方式
pdftotext report.pdf - | grep "目标关键词"

# ❌ 错误验证方式（PDF中文为CID编码，非明文UTF-8）
grep -a "中文" report.pdf   # 可能找不到
```

## 备用方案：直接保留 DOCX 格式

如果 PDF 的要求只是为了可读性，DOCX 格式同样可用 LibreOffice 打开查看且中文正常。
