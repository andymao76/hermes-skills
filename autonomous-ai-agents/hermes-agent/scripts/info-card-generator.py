#!/usr/bin/env python3
"""
参考脚本：用 Pillow 生成信息图长图并通过微信发送。

典型用法（在 agent 会话中）：
  1. python3 info-card-generator.py  → 输出 PNG 到 OUTPUT
  2. send_message(target="weixin", message="MEDIA:/path/to/output.png")

依赖：
  - Pillow: sudo apt install python3-pil 或 pip install Pillow
  - 中文字体: sudo apt install fonts-noto-cjk

配色方案（深色主题）：
  BG=(14,22,40) 深蓝黑背景
  CARD_BG=(22,34,58) 卡片底色
  ACCENT=(56,132,255) 蓝色强调
  ACCENT2=(0,200,117) 绿色
  ACCENT3=(255,170,0) 金色
  ACCENT4=(255,80,80) 红色

可自定义：
  - sections 数据（标题 + 要点列表）
  - 每个 section 的 accent 颜色
  - 字体大小、卡片圆角、行高
"""

from PIL import Image, ImageDraw, ImageFont

OUTPUT = "/home/andymao/info-card.png"
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

W = 1080
PADDING = 60
LINE_HEIGHT = 52
FONT_SIZE = 30
FONT_SIZE_TITLE = 40
FONT_SIZE_H1 = 34
FONT_SIZE_SMALL = 26

BG = (14, 22, 40)
CARD_BG = (22, 34, 58)
ACCENT = (56, 132, 255)
ACCENT2 = (0, 200, 117)
ACCENT3 = (255, 170, 0)
ACCENT4 = (255, 80, 80)
WHITE = (230, 240, 255)
GRAY = (150, 165, 195)
LIGHT_BLUE = (180, 210, 255)


def load_font(size, bold=False):
    try:
        path = FONT_BOLD_PATH if bold else FONT_PATH
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def draw_rounded_rect(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_text_wrap(draw, text, x, y, font, color=WHITE, max_w=None, center=False):
    if max_w is None:
        max_w = W - 2 * PADDING - 20
    lines = []
    line = ""
    for ch in text:
        test = line + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_w and line:
            lines.append(line)
            line = ch
        else:
            line = test
    if line:
        lines.append(line)
    for i, l in enumerate(lines):
        if center:
            bbox = draw.textbbox((0, 0), l, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((x + (max_w - tw) // 2, y + i * LINE_HEIGHT), l, font=font, fill=color)
        else:
            draw.text((x, y + i * LINE_HEIGHT), l, font=font, fill=color)
    return len(lines)


def generate_card(title, subtitle, sections, output_path=OUTPUT):
    font = load_font(FONT_SIZE)
    font_title = load_font(FONT_SIZE_TITLE, bold=True)
    font_h1 = load_font(FONT_SIZE_H1, bold=True)
    font_small = load_font(FONT_SIZE_SMALL)

    y_pos = PADDING + 60 + 40 + 40
    for sec in sections:
        y_pos += 50
        for item in sec["items"]:
            y_pos += LINE_HEIGHT * (len(item) // 30 + 1)
        y_pos += 40 + 30
    y_pos += PADDING
    H = y_pos

    img = Image.new("RGB", (W, int(H)), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING

    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), title, font=font_title, fill=WHITE)
    y += 65

    bbox = draw.textbbox((0, 0), subtitle, font=font_small)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), subtitle, font=font_small, fill=GRAY)
    y += 50

    draw.line([(PADDING, y), (W - PADDING, y)], fill=ACCENT, width=2)
    y += 40

    for sec in sections:
        card_y0 = y
        card_h = 20
        for item in sec["items"]:
            card_h += LINE_HEIGHT * (len(item) // 30 + 1)
        card_h += 30

        draw_rounded_rect(draw, (PADDING, y, W - PADDING, y + card_h), 16, CARD_BG)
        draw.rounded_rectangle((PADDING, y, PADDING + 8, y + card_h), 8, fill=sec["accent"])
        y += 15

        bbox = draw.textbbox((0, 0), sec["title"], font=font_h1)
        draw.text((PADDING + 30, y), sec["title"], font=font_h1, fill=sec["accent"])
        y += 45

        for item in sec["items"]:
            draw.ellipse((PADDING + 30, y + 12, PADDING + 38, y + 20), fill=LIGHT_BLUE)
            nl = draw_text_wrap(draw, item, PADDING + 50, y, font, WHITE, max_w=W - 2 * PADDING - 70)
            y += LINE_HEIGHT * nl

        y = card_y0 + card_h + 20

    img.save(output_path, "PNG")
    return output_path


if __name__ == "__main__":
    # 使用示例
    sections = [
        {"title": "示例章节一", "accent": ACCENT, "items": ["示例要点1", "示例要点2"]},
        {"title": "示例章节二", "accent": ACCENT2, "items": ["示例要点3", "示例要点4", "示例要点5"]},
    ]
    generate_card("标题", "副标题", sections)
    print(f"图片已保存: {OUTPUT}")
