# 程序化 PPTX 模板生成 — 快速入门

## 完整工作示例

以下是一个最小可运行 Python 脚本，生成带设计系统的 6 页 PPTX 模板。

```python
#!/usr/bin/env python3
"""模板生成最小示例 — 1 页封面 + 5 种典型页面布局"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from lxml import etree
from pptx.oxml.ns import qn

# ── 设计令牌 ──
FONT = 'Noto Sans CJK SC'
TITLE_CLR  = RGBColor(0x10, 0x2A, 0x43)
BODY_CLR   = RGBColor(0x25, 0x31, 0x3B)
MUTED_CLR  = RGBColor(0x6C, 0x73, 0x7C)
ORANGE     = RGBColor(0xE3, 0x6F, 0x2C)
TEAL       = RGBColor(0x0E, 0x91, 0x8C)
RED        = RGBColor(0xC7, 0x39, 0x2F)
BLUE       = RGBColor(0x2F, 0x80, 0xED)
CARD_O     = RGBColor(0xFF, 0xF0, 0xE5)   # 浅橙
CARD_T     = RGBColor(0xE6, 0xF4, 0xEF)   # 浅青
CARD_R     = RGBColor(0xFD, 0xEA, 0xEA)   # 浅红
CARD_W     = RGBColor(0xFF, 0xFF, 0xFF)
BORDER     = RGBColor(0xE5, 0xDE, 0xD1)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# ── 辅助函数 ──
def set_font(run, size=Pt(10), bold=False, color=BODY_CLR):
    run.font.name = FONT
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = color

def tb(slide, x, y, w, h):
    """快捷文本框"""
    txBox = slide.shapes.add_textbox(x, y, w, h)
    txBox.text_frame.word_wrap = True
    return txBox

def add_para(tf, text, size=Pt(10), bold=False, color=BODY_CLR, align=PP_ALIGN.LEFT, space_after=Pt(2)):
    p = tf.add_paragraph()
    p.alignment = align
    p.space_after = space_after
    r = p.add_run(); r.text = text
    set_font(r, size=size, bold=bold, color=color)
    return p

def rect(slide, x, y, w, h, fill, border=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if border:
        set_border(sh, border)
    else:
        sh.line.fill.background()
    return sh

def set_border(shape, color, width=Pt(0.8)):
    spPr = shape._element.find(qn('a:spPr'))
    ln = etree.SubElement(spPr, qn('a:ln')) if spPr.find(qn('a:ln')) is None else spPr.find(qn('a:ln'))
    ln.set('w', str(int(width)))
    sf = ln.find(qn('a:solidFill'))
    if sf is None: sf = etree.SubElement(ln, qn('a:solidFill'))
    sc = sf.find(qn('a:srgbClr'))
    if sc is None: sc = etree.SubElement(sf, qn('a:srgbClr'))
    sc.set('val', str(color))

def title_slide(prs, title, subtitle=''):
    """创建带橙色装饰条的标准页"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    t = tb(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.8))
    r = t.text_frame.paragraphs[0].add_run(); r.text = title
    set_font(r, size=Pt(24), bold=True, color=TITLE_CLR)
    if subtitle:
        t2 = tb(slide, Inches(0.8), Inches(1.05), Inches(11), Inches(0.35))
        r2 = t2.text_frame.paragraphs[0].add_run(); r2.text = subtitle
        set_font(r2, size=Pt(10), color=MUTED_CLR)
    rect(slide, Inches(0.8), Inches(1.35), Inches(0.5), Pt(4), ORANGE)
    return slide

# ── 模板生成 ──
def generate(path):
    prs = Presentation()
    prs.slide_width = SLIDE_W; prs.slide_height = SLIDE_H

    # 第1页：封面
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, SLIDE_W, SLIDE_H, TITLE_CLR)
    t = tb(slide, Inches(1), Inches(2), Inches(11), Inches(1.5))
    r = t.text_frame.paragraphs[0].add_run(); r.text = '分析报告标题'
    set_font(r, size=Pt(34), bold=True, color=CARD_W)
    add_para(t.text_frame, '副标题', size=Pt(15), bold=True, color=RGBColor(0xEB,0xD8,0xBE))
    # 三个 KPI
    for i, (num, lab, col) in enumerate([('¥1,000','保本日营收',ORANGE),('20-25','客单价',TEAL),('100天','止损窗口',BLUE)]):
        x = Inches(1) + i * Inches(3.8)
        c = rect(slide, x, Inches(4.5), Inches(3.2), Inches(1.2), CARD_W)
        t2 = tb(slide, x+Inches(0.15), Inches(4.6), Inches(2.9), Inches(0.5))
        r2 = t2.text_frame.paragraphs[0].add_run(); r2.text = num
        set_font(r2, size=Pt(22), bold=True, color=col)
        t3 = tb(slide, x+Inches(0.15), Inches(5.1), Inches(2.9), Inches(0.3))
        r3 = t3.text_frame.paragraphs[0].add_run(); r3.text = lab
        set_font(r3, size=Pt(9), bold=True, color=TITLE_CLR)

    # 第2页：结论页 — 3张提示卡
    slide = title_slide(prs, '一页结论', '核心洞察概览')
    for i, (tt, body, tc, bg) in enumerate([
        ('核心判断', '核心判断内容填写在这里', ORANGE, CARD_O),
        ('可盈利条件', '正面条件内容填写在这里', TEAL, CARD_T),
        ('不可做的情况', '风险警告内容填写在这里', RED, CARD_R),
    ]):
        x = Inches(0.8) + i * Inches(4.1)
        c = rect(slide, x, Inches(2.0), Inches(3.7), Inches(4.0), bg, BORDER)
        t = tb(slide, x+Inches(0.15), Inches(2.1), Inches(3.4), Inches(0.4))
        r = t.text_frame.paragraphs[0].add_run(); r.text = tt
        set_font(r, size=Pt(15), bold=True, color=tc)
        t2 = tb(slide, x+Inches(0.15), Inches(2.6), Inches(3.4), Inches(3.2))
        r2 = t2.text_frame.paragraphs[0].add_run(); r2.text = body
        set_font(r2, size=Pt(10), color=BODY_CLR)

    # 第3页：表格页
    slide = title_slide(prs, '数据看板', '行业的各项核心指标')
    tbl = slide.shapes.add_table(4, 3, Inches(0.8), Inches(2.0), Inches(7.0), Inches(2.0)).table
    for ci, h in enumerate(['指标', '数值', '趋势']):
        c = tbl.cell(0, ci); c.text = h
        c.fill.solid(); c.fill.fore_color.rgb = TITLE_CLR
        for r in c.text_frame.paragraphs:
            r.alignment = PP_ALIGN.CENTER
            for run in r.runs:
                set_font(run, size=Pt(9), bold=True, color=CARD_W)
    for ri, row in enumerate([['日均销售额','16,115','高位震荡'],['客单价','29.6','持平'],['翻台率','3.4','维稳']]):
        for ci, txt in enumerate(row):
            c = tbl.cell(ri+1, ci); c.text = txt
            c.fill.solid(); c.fill.fore_color.rgb = CARD_W
            for r in c.text_frame.paragraphs:
                r.alignment = PP_ALIGN.CENTER
                for run in r.runs:
                    set_font(run, size=Pt(8), color=BODY_CLR)

    # 第4页：时间轴（甘特条）
    slide = title_slide(prs, '止损时间轴', '止损是保护现金流的纪律')
    phases = [('试营业\n1-30天', TEAL), ('调产品\n31-60天', TEAL),
              ('看复购\n61-90天', ORANGE), ('看现金流\n91-120天', ORANGE),
              ('硬止损\n第6个月', RED)]
    bar_w, bar_gap = Inches(2.0), Inches(0.3)
    for i, (text, clr) in enumerate(phases):
        x = Inches(0.8) + i*(bar_w+bar_gap)
        c = rect(slide, x, Inches(1.8), bar_w, Inches(1.8),
                 RGBColor(0xF5,0xF0,0xEB), clr)
        t = tb(slide, x+Inches(0.1), Inches(1.95), bar_w-Inches(0.2), Inches(1.5))
        for li, line in enumerate(text.split('\n')):
            if li == 0:
                r = t.text_frame.paragraphs[0].add_run(); r.text = line
                set_font(r, size=Pt(11), bold=True, color=BODY_CLR)
            else:
                add_para(t.text_frame, line, size=Pt(9), color=MUTED_CLR)

    prs.save(path)
    return path

if __name__ == '__main__':
    import os
    p = generate(os.path.expanduser('~/Desktop/快速模板示例.pptx'))
    print(f'✅ 模板已生成: {p}')
    print('打开后替换文字即可使用')
```

## 使用步骤

1. 将以上代码保存为 `.py` 文件
2. 运行：`python3 文件名.py`
3. 打开生成的 PPTX，替换文字内容

## 常见修改

- **改颜色**：修改 `ORANGE` / `TEAL` / `RED` 等顶层常量的 RGB 值
- **改字体**：修改 `FONT = 'Noto Sans CJK SC'` 为你需要的字体名
- **改页面尺寸**：修改 `SLIDE_W` 和 `SLIDE_H`
- **增加新页面**：调用 `title_slide(prs, '标题', '副标题')` 后接组件代码

## 完整设计系统色值表

| 名称 | 色值 | 用途 |
|------|------|------|
| TITLE_CLR | #102A43 | 标题/表头文字 |
| BODY_CLR | #25313B | 正文文字 |
| MUTED_CLR | #6C737C | 次要信息 |
| ORANGE | #E36F2C | 核心洞察 |
| TEAL | #0E918C | 正面/可行 |
| RED | #C7392F | 风险/止损 |
| BLUE | #2F80ED | 中性/数据 |
| GREEN | #2E7D32 | 增长指标 |
| GOLD | #F4B942 | 高亮/辅助 |
| CARD_W | #FFFFFF | 白色卡片 |
| CARD_O | #FFF0E5 | 浅橙卡片(洞察) |
| CARD_T | #E6F4EF | 浅青卡片(正面) |
| CARD_B | #E7F0FA | 浅蓝卡片(数据) |
| CARD_R | #FDEAEA | 浅红卡片(风险) |
| BORDER | #E5DED1 | 卡片边框 |
