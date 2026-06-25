# 油价走势图生成指南

用户偏好可视化金融数据图表（如 WTI 原油走势图）。使用 Python + matplotlib 生成暗色 GitHub 主题风格的 PNG 图表。

## 数据来源

推荐使用 **Investing.com** 的历史数据页面获取完整日线数据：
- https://www.investing.com/commodities/crude-oil-historical-data
- 包含近一个月的每日开盘/最高/最低/收盘/成交量数据

备选数据源：
- Open-Meteo（免费，无API key，但无原油价格数据）
- Trading Economics（zh.tradingeconomics.com/commodity/crude-oil）
- Yahoo Finance

## 脚本

已有脚本：`/home/andymao/scripts/oil_chart.py`

## 图表生成步骤

### 1. 获取数据

用 `web_extract` 从 Investing.com 历史数据页面提取最近一个月的数据，包含：
- Date / Price（收盘价）/ Open / High / Low / Vol. / Change%

### 2. Python 图表脚本要点

```python
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

# CJK 字体查找（关键！避免中文乱码）
cjk_font = None
for fname in fm.fontManager.ttflist:
    if 'WenQuanYi' in fname.name or ('CJK' in fname.name and 'JP' in fname.name):
        cjk_font = fname.name
        break
if not cjk_font:
    for fname in fm.fontManager.ttflist:
        if 'Noto Sans CJK' in fname.name:
            cjk_font = fname.name
            break
if cjk_font:
    plt.rcParams['font.sans-serif'] = [cjk_font, 'DejaVu Sans']
    plt.rcParams['font.family'] = 'sans-serif'

# 暗色主题
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor('#0d1117')  # GitHub 暗色背景

# 线图和渐变填充
ax.plot(dates, prices, color='#e06c75', linewidth=2.5, zorder=3)
ax.fill_between(dates, prices, min(prices) - 5, alpha=0.15, color='#e06c75', zorder=1)

# 关键点标注（起点/最高点/当前点）
ax.annotate(f'Peak: ${peak_price:.2f}', xy=(peak_date, peak_price),
            xytext=(peak_date, peak_price + 6), fontsize=10, color='#98c379',
            fontweight='bold', ha='center',
            arrowprops=dict(arrowstyle='->', color='#98c379', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0d1117',
                      edgecolor='#98c379', alpha=0.8))

# 汇总信息框（期初/期末/涨跌/最高/最低）
summary_text = (f"期初: ${start_price:.2f}  →  期末: ${current_price:.2f}\n"
                f"涨跌: {change:+.2f}  ({change_pct:+.2f}%)\n"
                f"最高: ${peak_price:.2f}  最低: ${min(prices):.2f}")
ax.text(0.02, 0.97, summary_text, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', color='#e6edf3',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#161b22',
                  edgecolor='#30363d', alpha=0.9))

# 输出
plt.savefig('/home/andymao/scripts/wti_oil_chart.png', dpi=150,
            facecolor='#0d1117', bbox_inches='tight')
```

### 3. 发送到消息平台

图表生成后，在响应中包含：
```
MEDIA:/home/andymao/scripts/wti_oil_chart.png
```

Feishu/Telegram/Discord 网关自动识别 `MEDIA:` 前缀并上传为原生图片。

### 4. 附带数据分析

发送图表后，附上结构化数据表格：
- 当前价格、今日涨跌%、近一月涨跌%、52周范围、日内区间
- 近期波动原因（如美伊和平协议、OPEC 决策等）
- 关键节点时间线（阶段高点、暴跌事件、反弹等）

## 系统要求

- 系统安装 CJK 中文字体：`fonts-noto-cjk`（已装于本机）
- Python 包：`matplotlib`、`numpy`
- 无需 API key（数据自行采集）
