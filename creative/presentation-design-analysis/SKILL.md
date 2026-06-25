---
name: presentation-design-analysis
description: 分析 PPTX 等演示文件的设计手法——色彩系统、字体层级、卡片化布局、表格美化、数据可视化策略；以及基于设计系统程序化生成 PPTX 模板。反向工程已有设计成品，提取可复用的视觉原则。
category: creative
triggers:
  - '分析这个 PPT 的美化手法'
  - '这个 PPTX 是怎么做到这么好看的'
  - '研究这个演示文稿的设计系统'
  - '反向工程 PPTX 的视觉设计'
  - '学习这个 PPT 的排版配色技巧'
  - '生成这个风格的 PPTX 模板'
  - '根据设计系统生成演示文稿'
  - '程序化生成 PPTX 模板'
  - '把这套配色做成可复用的PPT模板'
---

# 演示文稿设计分析（Presentation Design Analysis）

## 概述
本技能覆盖从演示文件（PPTX）中系统性提取视觉设计原则的方法。核心思想：**不凭肉眼猜，用程序提取**。通过 python-pptx 对文件进行结构化分析，获取精确的字体、字号、色值、布局位置和形状属性，再归纳为设计原则。

---

## 一、环境准备

```bash
pip3 install --user --break-system-packages python-pptx
```

Python-pptx 1.0.2+ 支持读取：
- 所有形状的类型、位置（EMU → 英寸）、大小
- 文本字体、字号、颜色、粗斜体
- 形状填充色、边框色
- 表格结构及单元格样式
- 图片大小和格式
- XML 层面的阴影/发光/渐变（需额外解析）

---

## 二、分析工作流

### 第1步：获取基础信息
```python
from pptx import Presentation

prs = Presentation("path.pptx")
print(f"尺寸: {prs.slide_width/914400:.1f}\" x {prs.slide_height/914400:.1f}\"")
print(f"页数: {len(prs.slides)}")
```

### 第2步：提取主题/母版颜色
读取 XML 中的主题色和系统颜色：
```python
import re
xml = prs.slide_masters[0].element.xml
srgb = set(re.findall(r'srgbClr val="([^"]+)"', xml))
```

### 第3步：逐页分析形状、文本、填充
遍历每页，对每个形状提取：
- `shape.name`, `shape.shape_type`
- `shape.left/top/width/height`（EMU → 英寸：除以 914400）
- `shape.fill.type`, `shape.fill.fore_color.rgb`
- `shape.has_text_frame` → 段落 → runs → `run.font.size/name/bold/color.rgb`
- `shape.has_table` → 行数列数及每个单元格的文本和填充色

### 第4步：全局统计
- **字体使用频次**：`font_stats[font_name] += 1`
- **字号分布**：`font_stats[f"字号_{size/12700:.0f}pt"] += 1`
- **颜色使用频次**：区分文字色和填充色分别统计
- 根据频次推断：主字体、正文字号、标题字号、色值体系

### 第5步：归纳设计系统
从提取的数据中归纳出：

| 维度 | 分析点 |
|------|--------|
| 配色系统 | 语义色（每种色值对应的含义）、文本色阶、背景色 |
| 字号层级 | 标题→子标题→正文→表格的等比缩放关系 |
| 布局套路 | 卡片化、分栏提示卡、KPI 指标块 |
| 表格风格 | 表头色、交替行色、边框策略、对齐方式 |
| 可视化 | 是否使用图表插件 vs 手工绘制的标签/色块 |
| 装饰元素 | 标题装饰条、分隔线、标签块 |

---

## 三、关键技术细节

### EMU 单位换算
```
1 英寸 = 914400 EMU
1 pt = 12700 EMU
英寸 → 像素(96dpi): 英寸 * 96
字号 pt = font.size / 12700
```

### 形状类型判断
```python
shape.shape_type  # MSO_SHAPE_TYPE
# 1 = AUTO_SHAPE (文本框/矩形)
# 6 = GROUP (组合)
# 13 = PICTURE (图片)
# 19 = TABLE (表格)
```

### 填充分析注意事项
- 当 `fill.type is None` 表示无填充（透明）
- 获取填充色：`fill.fore_color.rgb` → `RGBColor` 对象，`str()` 转为十六进制
- 获取填充类型：`fill.type` → `MSO_FILL_TYPE.SOLID` / `GRADIENT` / `PICTURE` / `BLANK`
- **安全写法**：用 `try/except` 包裹 `fill.fore_color.rgb`，因为某些填充类型没有 foreground color

### 统计分析关键函数
```python
from collections import Counter
font_counter = Counter()
```

---

## 四、常见设计模式识别

### 模式1：KPI 卡片
特征：
- 白底圆角矩形（填充 #FFFFFF）
- 边框 #E5DED1 或 #D8C9B5（暖灰）
- 22pt 加粗大数字 + 9pt 标签 + 8pt 灰色说明
- 数字用语义色区分（橙/青/红/蓝）

### 模式2：分栏提示卡
特征：
- 有主题色的名称标签（如「核心判断」「风险红线」）
- 四种语义底色：浅橙/浅青/浅蓝/浅红
- 内文 10-11pt

### 模式3：表格表头
特征：
- 深色表头（#102A43 填充 + 白色字）
- 白色数据行 + 暖灰边框（#E3DACB）
- 无竖线，仅水平边框区分行
- 8-9pt 字号

### 模式4：标题区+装饰条
特征：
- 24pt 加粗深蓝黑标题
- 10pt 灰色副标题
- 橙色短装饰条（约 3.7mm 宽，填充语义橙色）

### 模式5：时间轴/甘特条
- 纯手工矩形排列
- 颜色从左到右从绿渐变为红
- 每个块内写里程碑文字

---

## 五、禁止纯黑原则

好的 PPT 视觉从不使用纯黑（#000000）作为文字色：
- 标题/标签：**#102A43**（深蓝黑，比纯黑柔和）
- 正文：**#25313B**（深灰蓝，主力文字色）
- 副标题/脚注：**#6C737C**（中灰色）
- 表格数据行文字：**#25313B**

---

## 六、生成统计报告的模板

```python
print(f"=== 基本信息 ===")
print(f"幻灯片尺寸: {prs.slide_width/914400:.1f}\" x {prs.slide_height/914400:.1f}\"")
print(f"总页数: {len(prs.slides)}")

print(f"=== 字体使用统计 ===")
for k, v in sorted(font_stats.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}次")

print(f"=== 颜色使用统计 ===")
for k, v in sorted(color_stats.items(), key=lambda x: -x[1])[:15]:
    print(f"  #{k}: {v}次")
```

---

## 七、从分析到生成：程序化模板构建（Template Generation）

分析设计系统之后，下一步是**用代码生成同样风格的 PPTX 模板**。核心方法是：把设计分析结果转化为**设计令牌（Design Tokens）+ 组件函数（Component Builders）+ 页面组合（Page Composition）** 三层结构。

### 7.1 设计令牌层（Design Tokens）

将分析出的设计规范定义为 Python 常量：

```python
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor

# ── 字体 ──
FONT_FAMILY = 'Noto Sans CJK SC'

# ── 文字色三阶 ──
COLOR_TITLE_BG     = RGBColor(0x10, 0x2A, 0x43)   # 深蓝黑 - 标题/表头
COLOR_BODY_TEXT    = RGBColor(0x25, 0x31, 0x3B)   # 正文
COLOR_MUTED_TEXT   = RGBColor(0x6C, 0x73, 0x7C)   # 次要信息

# ── 六语义色 ──
ORANGE  = RGBColor(0xE3, 0x6F, 0x2C)   # 核心洞察/行动
TEAL    = RGBColor(0x0E, 0x91, 0x8C)   # 正面/推荐
RED     = RGBColor(0xC7, 0x39, 0x2F)   # 风险/止损
BLUE    = RGBColor(0x2F, 0x80, 0xED)   # 中性/数据
GREEN   = RGBColor(0x2E, 0x7D, 0x32)   # 增长
GOLD    = RGBColor(0xF4, 0xB9, 0x42)   # 高亮/辅助

# ── 卡片底色 ──
CARD_ORANGE  = RGBColor(0xFF, 0xF0, 0xE5)   # 浅橙
CARD_TEAL    = RGBColor(0xE6, 0xF4, 0xEF)   # 浅青
CARD_BLUE    = RGBColor(0xE7, 0xF0, 0xFA)   # 浅蓝
CARD_RED     = RGBColor(0xFD, 0xEA, 0xEA)   # 浅红
CARD_WHITE   = RGBColor(0xFF, 0xFF, 0xFF)

# ── 边框色 ──
BORDER_LIGHT  = RGBColor(0xE5, 0xDE, 0xD1)
BORDER_TABLE  = RGBColor(0xE3, 0xDA, 0xCB)

# ── 字号层级（6档）─
SIZE_COVER_TITLE = Pt(34)
SIZE_PAGE_TITLE  = Pt(24)
SIZE_BIG_NUMBER  = Pt(22)
SIZE_SUB_TITLE   = Pt(15)
SIZE_SECTION     = Pt(16)
SIZE_BODY        = Pt(10)
SIZE_CAPTION     = Pt(9)
SIZE_TABLE       = Pt(8)

# ── 页面尺寸 (16:9) ──
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)
```

### 7.2 组件函数层（Component Builders）

将每个设计模式封装为可复用的函数：

| 组件函数 | 用途 | 关键参数 |
|---------|------|---------|
| `make_slide_with_title(prs, title, subtitle)` | 创建带标题+橙条装饰的标准页 | title, subtitle |
| `add_kpi_cards(slide, kpis, y_start)` | 一排 KPI 大数字卡片 | kpis = [(big_text, label, subtitle, accent_color), ...] |
| `add_info_card(slide, x, y, w, h, title, body, title_color, bg_color)` | 带语义色标题的提示卡片 | title_color/bg_color 决定语义类型 |
| `add_table(slide, x, y, w, h, headers, rows)` | 美化表格（深色表头+白行+无竖线） | headers, rows |
| `add_tag(slide, x, y, label, bg_color, value)` | 语义色小标签 | bg_color 决定语义，value 覆盖文本 |
| `add_rounded_rect(slide, x, y, w, h, fill, border_color)` | 通用圆角矩形 | 基础几何组件 |

**组件函数实现模板**（关键模式）：

```python
def make_slide_with_title(prs, title, subtitle=''):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    # 标题
    tb = _add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.8))
    ...
    # 橙色装饰条
    _add_rect(slide, Inches(0.8), Inches(1.35), Inches(0.5), Pt(4), ORANGE)
    return slide

def add_kpi_cards(slide, kpis, y_start=Inches(1.7)):
    """kpis: [(big_text, label, subtitle, accent_color), ...]"""
    card_w, card_h = Inches(2.8), Inches(1.2)
    ...
    for i, (big, label, sub, accent) in enumerate(kpis):
        card = _add_rounded_rect(slide, x, y_start, card_w, card_h,
                                  CARD_WHITE, BORDER_LIGHT)
        # 22pt 大数字 + 9pt 标签 + 8pt 说明
        ...
```

### 7.3 页面组合层（Page Composition）

用已定义的组件函数拼装页面，形成完整的演示文稿模板：

```python
def generate_template(output_path):
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # 封面
    slide = make_cover_slide(prs, ...)

    # 标准页面
    slide = make_slide_with_title(prs, '一页结论', '副标题')
    add_kpi_cards(slide, [...])
    add_info_card(slide, ..., title_color=ORANGE, bg_color=CARD_ORANGE)
    add_info_card(slide, ..., title_color=TEAL, bg_color=CARD_TEAL)

    # 表格页面
    slide = make_slide_with_title(prs, '数据看板', '子标题')
    add_table(slide, x, y, w, h, headers, rows)
    add_tag(slide, x, y, label, bg_color=ORANGE, value='+3.8%')

    # 时间轴页面（甘特条）
    slide = make_slide_with_title(prs, '止损时间轴', '子标题')
    for text, color, bg in phases:
        card = _add_rounded_rect(slide, x, y, bar_w, bar_h, bg, BORDER_MEDIUM)
        ...

    prs.save(output_path)
```

### 7.4 常见陷阱（Pitfalls）

1. **`RGBColor` 没有 `.red`/`.green`/`.blue` 属性**
   - ❌ `f'{color.red:02X}{color.green:02X}{color.blue:02X}'`
   - ✅ `str(color)` → `'E36F2C'`

2. **参数名冲突：`width` 既是位置参数也是关键词参数**
   - `_add_rounded_rect(slide, left, top, width, height, fill, border_color, border_width)`
   - ❌ `_add_rounded_rect(..., fill, width=Pt(2))` — `width` 作为位置参数在第3位已被传入
   - ✅ `_add_rounded_rect(..., fill, border_width=Pt(2))`

3. **python-pptx 的 `Presentation()` 默认尺寸不是 16:9**
   ```python
   prs = Presentation()
   prs.slide_width = Inches(13.33)   # 必须手动设置
   prs.slide_height = Inches(7.5)
   ```

4. **表格边框无法直接关闭**
   - 需要操作 XML 删除默认边框元素，或用 `table._tbl` 修改 `a:tblPr`
   - 或设置 `table.first_row` / `table.band_rows` 控制交替色

5. **字体设置对 PPTX 中的东亚文字**
   - 仅在 `run.font.name` 上设置字体会影响 ASCII，东亚文字需额外设 `run._element.rPr.rFont.set('{http://schemas.openxmlformats.org/drawingml/2006/main}ea', fontname)`
   - 最佳实践：在 `_set_font` 中统一处理

6. **封面背景**：将背景图片插入为全幅形状，再在图片上加等大半透明深色矩形做遮罩，文字放在遮罩之上

### 7.5 与分析方法论的关系

```
分析阶段（本技能 1-6 节）
  ↓ 提取设计系统
设计令牌 + 组件模式
  ↓ 编码实现
模板生成（本技能 7 节）
  ↓ 产出
可编辑的 .pptx 模板
```

完整的「分析→生成」闭环确保：程序生成的 PPTX 与原始分析对象在视觉语言上保持一致。

--- 

## 八、局限性
- 无法直接读取图表数据（Chart 对象需另外用 `chart_data` 提取）
- 动画和过渡效果不可解析
- 文本框中混排的不同样式需逐 run 提取
- 部分 PPT 使用「主题颜色」而非绝对色值，需要额外解析 XML
