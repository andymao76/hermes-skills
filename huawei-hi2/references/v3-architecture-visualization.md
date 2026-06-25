# ETSI ASN.1 Assistant V3 架构可视化工作流

从 LI ASN.1 解码器源码生成可视化架构图的工作流。

## 输出产物

| 格式 | 文件 | 用途 |
|------|------|------|
| HTML | `v3_architecture.html` | 可交互架构图（浏览器打开） |
| SVG | `v3_architecture.svg` | 矢量图（可嵌入文档） |
| A4 PDF | `v3_architecture_a4.pdf` | 300dpi 打印/报告 |
| A4 PNG | `v3_architecture_a4.png` | 预览/微信分享 |

## 生成步骤

### 1. 创建架构图 HTML

使用 `architecture-diagram` skill 生成 dark-theme SVG 架构图 HTML。关键颜色方案：

| 层 | 语义色 | 用于 |
|--|--------|------|
| L1 Web | cyan-400 (#22d3ee) | 展示层组件 |
| L2 后处理 | orange-400 (#fb923c) | 解码后处理组件 |
| L3 解码引擎 | emerald-400 (#34d399) | 核心解码组件 |
| L4 规范管理 | violet-400 (#a78bfa) | Schema管理组件 |
| L5 文件资源 | rose-400 (#fb7185) | ASN.1 文件组件 |
| ★ 新增 | amber-400 (#fbbf24) | v3 新增项高亮 |

### 2. SVG 提取

```python
# 从 HTML 提取 SVG 元素，添加 XML 命名空间
svg = html[html.index("<svg "):html.index("</svg>")+6]
svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ...')
# 验证 XML 合法性
import xml.etree.ElementTree as ET
ET.parse(io.StringIO(full_svg))
```

### 3. A4 PDF/PNG 导出（Chromium HiDPI）

```bash
# 创建裸渲染 HTML（仅 SVG，无额外 CSS 布局）
# HiDPI 截图（3x 确保文字清晰）
google-chrome-stable --headless=new --no-sandbox --disable-gpu \\
  --window-size=1340,970 --force-device-scale-factor=3 \\
  --hide-scrollbars --screenshot=hidpi.png \\
  --default-background-color=020617 file:///render.html

# ImageMagick 缩放至 A4 横版 300dpi（3508x2480）
convert hidpi.png -resize 3508x2480 -density 300 \\
  -background "#020617" -gravity center -extent 3508x2480 \\
  -quality 100 output_a4.pdf

convert hidpi.png -resize 3508x2480 -density 300 \\
  -background "#020617" -gravity center -extent 3508x2480 \\
  -quality 100 output_a4.png
```

### SVG viewBox 与 A4 比例匹配

| SVG viewBox | 比例 | A4 横版 | 匹配度 |
|------------|------|---------|--------|
| 1280x920 | 1.39:1 | 3508x2480 (1.41:1) | 接近完美 ✅ |

## 注意事项

1. **Windows 文件残留**：从 PyInstaller EXE 提取的 `*.dll` / `*.pyd` 在 Linux 上无用，Python 3.12 内置模块替代
2. **SVG 颜色方案一致**：架构图颜色层与源码模块颜色应一致（Web=cyan, 解码=emerald 等）
3. **PDF 验收**：成品 >500KB，`pdfinfo` 显示单页 A4
