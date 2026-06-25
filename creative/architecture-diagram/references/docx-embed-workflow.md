# SVG 嵌入 DOCX 工作流

当用户要求将系统架构图/业务流程图添加到 Word 文档时，使用以下工作流：

## 步骤

1. **生成 SVGs** — 用 architecture-diagram skill 分别创建架构图和流程图 HTML，每个文件一个 SVG，独立的 viewBox
2. **渲染为 PNG** — 用 chromium headless 截图：
   ```bash
   google-chrome-stable --headless --no-sandbox --disable-gpu \
     --screenshot=arch.png --window-size=1150,960 \
     file:///path/to/arch.html
   google-chrome-stable --headless --no-sandbox --disable-gpu \
     --screenshot=flow.png --window-size=1150,640 \
     file:///path/to/flow.html
   ```
3. **嵌入 DOCX** — 用 python-docx 的 `add_picture(png_path, width=Cm(15.5))` 插入
4. **居中 + 标题** — 图片居中（`WD_ALIGN_PARAGRAPH.CENTER`），上方加标注行（`图1: ...`）

## 关键参数

| 项 | 架构图 | 流程图 |
|---|--------|--------|
| viewBox | 1100×880~920 | 1100×560~600 |
| window-size | 1150×960 | 1150×640 |
| DOCX 图片宽度 | Cm(15.5) / Inches(5.8) | 同上 |

## 文档结构偏好

该用户的文档章节顺序固定为：
- 封面 → 版本历史 → **第一章：系统架构图** → **第二章：业务流程图** → 文字章节（三~十）
