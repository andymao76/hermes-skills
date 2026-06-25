# Dark → Light Theme Conversion

将 architecture-diagram skill 生成的深色主题 SVG 转换为浅色主题的完整流程。

## 何时使用

用户要求 "把深色改为浅色"、"白色背景"、"浅色底"、"浅蓝色背景"、"地层浅蓝色" 时。

## 用户首选配色（andymao）

This user's preferred light theme palette (expressed via requests for "地层浅蓝色背景"):

| 元素 | 颜色 |
|:---|:---|
| 页面背景 (body) | `#e0f2fe` (浅天蓝) |
| 卡片背景 | `#ffffff` |
| 标题颜色 | `#1e293b` |
| 灰色文字 | `#475569` |
| 明细文字 | `#64748b` |
| SVG 网格线条 | `#bae6fd` |
| SVG 文字 (原 white) | `#1e293b` |
| SVG 灰色文字 (原 #94a3b8) | `#475569` |

Apply this palette when the user asks for a light or sky-blue background. For generic "white background" requests, fall back to the standard light theme below.

## 标准浅色主题

## 一、HTML CSS 修改

```css
/* body */
background: #020617  →  background: #f8fafc
color: white         →  color: #0f172a

/* diagram-container */
background: rgba(15, 23, 42, 0.5)  →  background: #ffffff
border: 1px solid #1e293b          →  border: 1px solid #e2e8f0

/* subtitle */
color: #94a3b8  →  color: #475569

/* card text */
.card ul { color: #94a3b8 }       →  color: #475569
.card li strong { color: #e2e8f0 } →  color: #334155

/* footer */
color: #475569  →  color: #64748b
```

## 二、SVG 颜色映射

| 元素 | 深色值 | 浅色值 |
|:---|:---|:---|
| 网格填充 | `url(#grid)` / `#020617` | `#ffffff` |
| 网格线 stroke | `#1e293b` | `#e2e8f0` |
| 文字 fill | `white` | `#0f172a` |
| 灰色文字 fill | `#94a3b8` | `#475569` |
| 背景 rect fill | `#020617` | `#ffffff` |

### 盒模型填充 (暗→亮)

| 原值 | 替换值 |
|:---|:---|
| `rgba(15,23,42,0.8)` | `rgba(248,250,252,0.95)` |
| `rgba(30,41,59,0.5)` | `rgba(226,232,240,0.8)` |
| `rgba(30,41,59,0.15)` | `rgba(226,232,240,0.5)` |
| `rgba(15,23,42,0.3)` | `rgba(241,245,249,0.7)` |
| `rgba(30,41,59,0.1)` | `rgba(226,232,240,0.4)` |

### 层级着色 (降低不透明度)

| 原值 | 替换值 |
|:---|:---|
| `rgba(8,51,68,0.12)` | `rgba(8,145,178,0.08)` |
| `rgba(8,51,68,0.4)` | `rgba(8,145,178,0.18)` |
| `rgba(6,78,59,0.08)` | `rgba(5,150,105,0.08)` |
| `rgba(6,78,59,0.4)` | `rgba(5,150,105,0.18)` |
| `rgba(120,53,15,0.08)` | `rgba(217,119,6,0.08)` |
| `rgba(120,53,15,0.3)` | `rgba(217,119,6,0.15)` |
| `rgba(76,29,149,0.08)` | `rgba(124,58,237,0.08)` |
| `rgba(76,29,149,0.35)` | `rgba(124,58,237,0.15)` |
| `rgba(76,29,149,0.4)` | `rgba(124,58,237,0.18)` |
| `rgba(136,19,55,0.35)` | `rgba(225,29,72,0.15)` |

## 三、Emoji 清理（必做）

cairosvg 无法渲染 emoji 和部分 Unicode 符号，转换到浅色主题后必须清理：

```python
import re

# 1. Emoji + 变体选择符
emoji_pat = re.compile(
    "[\U0001F000-\U0001FFFF\U0000FE00-\U0000FEFF\U00002600-\U000027BF"
    "\U000020D0-\U000020FF]+", flags=re.UNICODE)
svg_body = emoji_pat.sub("", svg_body)

# 2. 逐个替换已知问题字符
char_map = {
    "\u2328": "",    # ⌨ KEYBOARD
    "\u23f0": "",    # ⏰ ALARM CLOCK
    "\U0001f1e8\U0001f1f3": "CN ",  # 🇨🇳 → CN
    "\u2192": "->",  # →
    "\u2194": "<->", # ↔
    "\u2248": "~",   # ≈
    "\u2264": "<=",  # ≤
    "\u2014": "-",   # —
    "\ufe0f": "",    # 变体选择符
}
for old, new in char_map.items():
    svg_body = svg_body.replace(old, new)

# 3. 验证无残留
bad = set()
for m in re.finditer(r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\n\r\t /.,:;()<>=+\-*#&%@!\$'"'"'"\[\]{}|\\^~`_?\u00B7\u2014\u2192\u2194\u2248\u2264]', svg_body):
    bad.add(m.group())
if bad:
    print(f"REMAINING: {[f'U+{ord(c):04X}' for c in sorted(bad)]}")
```

## 四、背景 rect 插入

```python
svg_body = re.sub(
    r'(<svg[^>]*>)',
    r'\1\n<rect width="100%" height="100%" fill="#ffffff" />',
    svg_body, count=1
)
```

## 五、完整一键脚本

```python
#!/usr/bin/env python3
"""Dark SVG → Light SVG (no emoji, white bg, dark text) in one pass."""
import re, io, os

DARK_SVG = "architecture.svg"
LIGHT_SVG = "architecture-light.svg"

with open(DARK_SVG) as f:
    svg = f.read()

svg_body = svg.split("?>", 1)[-1].strip()

# Step 1: Strip emojis
emoji_pat = re.compile(
    "[\U0001F000-\U0001FFFF\U0000FE00-\U0000FEFF\U00002600-\U000027BF\U000020D0-\U000020FF]+",
    flags=re.UNICODE)
svg_body = emoji_pat.sub("", svg_body)

# Step 2: Replace known problem chars
for old, new in {
    "\u2328": "", "\u23f0": "", "\U0001f1e8\U0001f1f3": "CN ",
    "\u2192": "->", "\u2194": "<->", "\u2248": "~", "\u2264": "<=",
    "\u2014": "-", "\ufe0f": "",
}.items():
    svg_body = svg_body.replace(old, new)

# Step 3: Dark → Light color transformations
svg_body = svg_body.replace('fill="url(#grid)"', 'fill="#ffffff"')
svg_body = svg_body.replace('stroke="#1e293b" stroke-width="0.5"', 'stroke="#e2e8f0" stroke-width="0.5"')
svg_body = re.sub(r'fill="white"', 'fill="#0f172a"', svg_body)
svg_body = re.sub(r'fill="#94a3b8"', 'fill="#475569"', svg_body)

fills = [
    ('rgba(15,23,42,0.8)', 'rgba(248,250,252,0.95)'),
    ('rgba(30,41,59,0.5)', 'rgba(226,232,240,0.8)'),
    ('rgba(30,41,59,0.15)', 'rgba(226,232,240,0.5)'),
    ('rgba(15,23,42,0.3)', 'rgba(241,245,249,0.7)'),
    ('rgba(30,41,59,0.1)', 'rgba(226,232,240,0.4)'),
    ('rgba(8,51,68,0.12)', 'rgba(8,145,178,0.08)'),
    ('rgba(8,51,68,0.4)', 'rgba(8,145,178,0.18)'),
    ('rgba(6,78,59,0.08)', 'rgba(5,150,105,0.08)'),
    ('rgba(6,78,59,0.4)', 'rgba(5,150,105,0.18)'),
    ('rgba(120,53,15,0.08)', 'rgba(217,119,6,0.08)'),
    ('rgba(120,53,15,0.3)', 'rgba(217,119,6,0.15)'),
    ('rgba(76,29,149,0.08)', 'rgba(124,58,237,0.08)'),
    ('rgba(76,29,149,0.35)', 'rgba(124,58,237,0.15)'),
    ('rgba(76,29,149,0.4)', 'rgba(124,58,237,0.18)'),
    ('rgba(136,19,55,0.35)', 'rgba(225,29,72,0.15)'),
]
for old, new in fills:
    svg_body = svg_body.replace(old, new)

# Step 4: Insert white background rect
svg_body = re.sub(
    r'(<svg[^>]*>)',
    r'\1\n<rect width="100%" height="100%" fill="#ffffff" />',
    svg_body, count=1
)

if 'xmlns=' not in svg_body[:300]:
    svg_body = svg_body.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)

full = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_body

# Step 5: Validate XML
import xml.etree.ElementTree as ET
ET.parse(io.StringIO(full))

with open(LIGHT_SVG, "w") as f:
    f.write(full)
print(f"✓ Light SVG: {LIGHT_SVG} ({len(full)} bytes)")
```

## 六、验证清单

转换完成后：
1. ✅ XML 解析无报错
2. ✅ 四角采样 ≥90% 白色像素（确认背景不是透明）
3. ✅ 视觉验证：标题/层标签区存在深色像素（文字可见）
4. ✅ 视觉验证：无 tofu 方块（☒）
