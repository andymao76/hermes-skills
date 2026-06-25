# 视觉渲染验证

生成架构图后，使用 CairoSVG 渲染 + Pillow 采样验证文字可见性。

## 为什么需要这一步

XML 验证（`ET.parse`）只能检查 XML 格式是否正确，无法发现以下问题：
- 文字颜色与背景色过于接近导致不可见
- 字体回退问题导致中文字符渲染为方块
- Emoji/特殊 Unicode 渲染为 tofu 方块 (☒)
- CairoSVG 忽略 `style="background-color:..."` 导致背景透明
- 布局重叠导致文字被遮挡

## 前置：背景 rect

**CairoSVG 不会读取 SVG 的 `style="background-color:..."` 属性**。渲染前必须在 SVG 内插入显式背景矩形：

```python
svg_body = re.sub(
    r'(<svg[^>]*>)',
    r'\1\n<rect width="100%" height="100%" fill="#XXXXXX" />',
    svg_body, count=1
)
# 深色主题: fill="#020617"
# 浅色主题: fill="#ffffff"
```

## 验证步骤

### 1. 渲染 PNG

```bash
python3 << 'PYEOF'
import cairosvg
cairosvg.svg2png(url="architecture.svg", write_to="architecture.png",
                 output_width=2600, output_height=2000)
print("PNG rendered")
PYEOF
```

### 2. 验证背景（四角采样）

无论是深色还是浅色主题，四个角落必须一致显示背景色：

```python
from PIL import Image
img = Image.open("architecture.png")

# Dark theme: corners should be near-black
# Light theme: corners should be near-white
corners = [
    (0, 0), (img.size[0]-100, 0),
    (0, img.size[1]-100), (img.size[0]-100, img.size[1]-100)
]

# Light theme check (target: white background)
for (x, y) in corners:
    crop = img.crop((x, y, x+100, y+100))
    pixels = list(crop.getdata())
    white_pct = sum(1 for p in pixels if p[0] > 245 and p[1] > 245 and p[2] > 245) / len(pixels) * 100
    print(f"  Corner ({x},{y}): {white_pct:.1f}% white {'OK' if white_pct > 85 else 'ISSUE — background not rendering!'}")

# Dark theme check (target: dark background)
for (x, y) in corners:
    crop = img.crop((x, y, x+100, y+100))
    pixels = list(crop.getdata())
    dark_pct = sum(1 for p in pixels if p[0] < 20 and p[1] < 20 and p[2] < 20) / len(pixels) * 100
    print(f"  Corner ({x},{y}): {dark_pct:.1f}% dark {'OK' if dark_pct > 85 else 'ISSUE'}")
```

### 3. 采样关键文本区域

选择标题、各层标签、核心组件名等关键位置，裁剪后检测文字像素比例。

**深色主题：** 文字是白色/亮色，检测「非黑色」像素比例。
**浅色主题：** 文字是深色，检测「深色」像素比例。

```python
# 浅色主题 — 检测深色像素（文字）
samples_light = {
    "title":     (100, 60, 1100, 120),   # (x1, y1, x2, y2) 像素坐标
    "layer1":    (100, 200, 500, 250),
}

for name, (x1, y1, x2, y2) in samples_light.items():
    crop = img.crop((x1, y1, x2, y2))
    pixels = list(crop.getdata())
    dark = sum(1 for p in pixels if p[0] < 80 and p[1] < 80 and p[2] < 80)
    ratio = dark / len(pixels) * 100
    print(f"  {name}: {ratio:.2f}% dark pixels — {'TEXT PRESENT' if ratio > 0.1 else 'TEXT MISSING!'}")

# 深色主题 — 检测亮色像素（文字）
samples_dark = {
    "title":     (590, 48, 80, 20),       # (x, y, w, h) in viewBox coords
    "layer1":    (260, 288, 100, 20),
}

scale_x = img.width / 1180.0   # viewBox width
scale_y = img.height / 880.0   # viewBox height

for name, (x, y, w, h) in samples_dark.items():
    rx, ry = int(x * scale_x), int(y * scale_y)
    rw, rh = int(w * scale_x), int(h * scale_y)
    crop = img.crop((rx, ry, rx+rw, ry+rh))
    pixels = list(crop.getdata())
    non_dark = sum(1 for p in pixels if p[0] > 200 or p[1] > 200 or p[2] > 200)
    ratio = non_dark / len(pixels) * 100
    print(f"  {name}: {ratio:.1f}% — {'OK' if ratio > 5 else 'PROBLEM'}")
```

### 4. Emoji / Tofu 方块检测

CairoSVG 无法渲染 emoji 和部分 Unicode 符号，会在文本位置显示为空白方块：

```python
# Emoji 渲染为 tofu 通常产生均匀亮度值的灰色方块
# 采样 emoji 预期位置的像素，如果出现异常的均匀灰色块则说明渲染失败
# 更简单的方法：渲染前确保 SVG 中已清除所有 emoji
import re
with open("architecture.svg") as f:
    svg = f.read()
emoji_pat = re.compile(
    "[\U0001F000-\U0001FFFF\U0000FE00-\U0000FEFF\U00002600-\U000027BF]+",
    flags=re.UNICODE)
if emoji_pat.search(svg):
    print("WARNING: Emoji characters detected in SVG — will render as tofu in PNG!")
else:
    print("OK: No emoji characters in SVG")
```

## 判定标准

| 检查项 | 深色主题阈值 | 浅色主题阈值 | 不通过时的对策 |
|:---|:---|:---|:---|
| 背景角采样 | ≥85% dark (#000-#141414) | ≥85% white (#F5-#FFF) | 插入背景 rect 重新渲染 |
| 文字可见性 | ≥5% 非暗像素 | ≥0.1% 深色像素 | 检查 fill 颜色是否与背景对比度足够 |
| Emoji 残留 | 0 个 emoji 字符 | 0 个 emoji 字符 | 用 regex 清理后重新渲染 |
| Tofu 方块 | 视觉检查无 ☒ | 视觉检查无 ☒ | 清理特殊 Unicode 后重新渲染 |

**注意：** 浅色主题的文字检测阈值设为 0.1% 而非 5%，因为深色文字在白色背景上占比极小（文字笔画极细，一屏文字可能只占区域的 0.1-2%）。

## 依赖

```bash
pip install cairosvg Pillow
```

CairoSVG 依赖系统级 `libcairo2`（Ubuntu 通常已预装）。
