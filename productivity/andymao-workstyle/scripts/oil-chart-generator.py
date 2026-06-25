#!/usr/bin/env python3
"""Generate WTI crude oil price trend chart with dark GitHub theme.

Usage:
    python3 oil-chart-generator.py

Requires:
    - matplotlib, numpy
    - fonts-noto-cjk (for Chinese text)

Output:
    /home/andymao/scripts/wti_oil_chart.png
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from datetime import datetime
import numpy as np

# === CONFIG: Edit this data block ===
# Data format: ("YYYY-MM-DD", closing_price)
DATA = [
    ("2026-05-11", 98.07),
    ("2026-05-12", 102.18),
    ("2026-05-13", 101.02),
    ("2026-05-14", 101.17),
    ("2026-05-15", 105.42),
    ("2026-05-18", 108.66),
    ("2026-05-19", 107.77),
    ("2026-05-20", 98.26),
    ("2026-05-21", 96.35),
    ("2026-05-22", 96.60),
    ("2026-05-26", 93.89),
    ("2026-05-27", 88.68),
    ("2026-05-28", 88.90),
    ("2026-05-29", 87.36),
    ("2026-06-01", 92.16),
    ("2026-06-02", 93.76),
    ("2026-06-03", 96.02),
    ("2026-06-04", 93.04),
    ("2026-06-05", 90.54),
    ("2026-06-08", 91.30),
    ("2026-06-09", 88.20),
    ("2026-06-10", 90.03),
    ("2026-06-11", 86.07),
    ("2026-06-12", 84.69),
]

OUTPUT_PATH = '/home/andymao/scripts/wti_oil_chart.png'
CHART_TITLE = 'WTI 原油期货价格走势'
Y_LABEL = '价格（美元/桶）'
X_LABEL = '日期'
# ===============================

# CJK font
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
else:
    print("Warning: No CJK font found, Chinese chars may not display")

# Parse data
dates = [datetime.strptime(d[0], "%Y-%m-%d") for d in DATA]
prices = [d[1] for d in DATA]

# Dark theme
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

# Line with gradient fill
ax.plot(dates, prices, color='#e06c75', linewidth=2.5, zorder=3)
ax.fill_between(dates, prices, min(prices) - 5, alpha=0.15, color='#e06c75', zorder=1)

# Markers
ax.scatter(dates, prices, color='#e06c75', s=40, zorder=4,
           edgecolors='#0d1117', linewidth=0.5)

# Annotations
start_price = prices[0]
peak_idx = np.argmax(prices)
peak_price = prices[peak_idx]
peak_date = dates[peak_idx]
current_price = prices[-1]
current_date = dates[-1]

# Peak
ax.annotate(f'Peak: ${peak_price:.2f}\n{peak_date.strftime("%m/%d")}',
            xy=(peak_date, peak_price),
            xytext=(peak_date, peak_price + 6),
            fontsize=10, color='#98c379', fontweight='bold', ha='center',
            arrowprops=dict(arrowstyle='->', color='#98c379', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0d1117',
                      edgecolor='#98c379', alpha=0.8))

# Current
ax.annotate(f'${current_price:.2f}\n{current_date.strftime("%m/%d")}',
            xy=(current_date, current_price),
            xytext=(current_date, current_price - 7),
            fontsize=11, color='#e06c75', fontweight='bold', ha='center',
            arrowprops=dict(arrowstyle='->', color='#e06c75', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0d1117',
                      edgecolor='#e06c75', alpha=0.8))

# Start
ax.annotate(f'Start: ${start_price:.2f}',
            xy=(dates[0], start_price),
            xytext=(dates[0], start_price - 7),
            fontsize=9, color='#56b6c2', fontweight='bold', ha='center',
            arrowprops=dict(arrowstyle='->', color='#56b6c2', lw=1),
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#0d1117',
                      edgecolor='#56b6c2', alpha=0.8))

# Grid
ax.grid(True, alpha=0.15, linestyle='--', linewidth=0.5)

# Axis
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
ax.set_ylim(min(prices) - 10, max(prices) + 10)
ax.set_xlim(dates[0], dates[-1])

# Labels
ax.set_title(CHART_TITLE, fontsize=18, color='#e6edf3', fontweight='bold', pad=20)
ax.set_ylabel(Y_LABEL, fontsize=12, color='#8b949e')
ax.set_xlabel(X_LABEL, fontsize=12, color='#8b949e')

# Summary box
change = current_price - start_price
change_pct = (change / start_price) * 100
summary = (f"期初: ${start_price:.2f}  →  期末: ${current_price:.2f}\n"
           f"涨跌: {change:+.2f}  ({change_pct:+.2f}%)\n"
           f"最高: ${peak_price:.2f}  最低: ${min(prices):.2f}")
ax.text(0.02, 0.97, summary, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', color='#e6edf3',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#161b22',
                  edgecolor='#30363d', alpha=0.9))

# Spines
for spine in ax.spines.values():
    spine.set_color('#30363d')

plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150, facecolor='#0d1117', bbox_inches='tight')
plt.close()
print(f"Chart saved to {OUTPUT_PATH}")
