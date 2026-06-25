---
name: "market-research-report"
title: "Research Dashboard & Report Generator"
description: "生成多城市/多行业对比分析 或 国别/地缘政治主题研究报告的HTML可视化仪表盘，支持搜索→提取→可视化→浏览器打开全流程"
triggers:
  - 对比分析
  - 对比报告
  - 数据对比报告
  - 薪资对比
  - 市场调研报告
  - 数据对比
  - 美化输出
  - 图表报告
  - 收费对比
  - 价格对比
  - 国别分析
  - 国家分析
  - 政治经济
  - 局势报告
  - 研究报告
  - country research
  - geopolitical dashboard
---

# Market Research & Comparison Report Generator

Generates beautiful HTML comparison reports for multi-region salary / industry / market data. Handles the end-to-end workflow: search → extract → visualize → open in browser.

## When to Use

Activate when the user asks for:
- Cross-region salary comparisons (e.g. "对比分析全国，江苏，南京市，镇江市，苏州市，上海市外贸商务人员薪资")
- Industry / market research spanning multiple cities or regions
- "美化图表输出，生成后打开浏览器" (beautified chart output, open in browser)
- Any request involving data collection + visual report generation

## Required Input

- The regions/cities to compare (e.g. 全国, 上海, 南京, 苏州, 镇江)
- The target industry/profession (e.g. 外贸业务员, 调酒师, 桶装水品牌)
- Any specific data points needed (salary, certificates, rankings, etc.)

## Workflow

### Step 1: Data Collection
Use `web_search_plus` for each region/query combination. Do NOT combine all regions into one query — search each one separately:

```
# For each target city/region, make targeted queries:
# 1. General salary query per city
web_search_plus(query=f"{city} {profession} 工资 月薪 2025 2026")
# 2. Specific data from jobui.com (职友集) — best source for salary distributions
web_search_plus(query=f"{city} {profession} 平均工资 职友集 2025")
# 3. Additional dimensions (certifications, trends, etc.)
web_search_plus(query=f"{profession} 职业资格 证书 要求 2025")
```

**Key data sources (in priority order):**
- 职友集 (jobui.com) — salary distribution data with percentiles
- BOSS直聘 (zhipin.com) — current job postings with salary ranges
- 猎聘 (liepin.com) — mid-to-senior level salary data
- Indeed (cn.indeed.com) — national averages
- 任仕达薪酬指南 — professional salary reports (PDF)

### Step 2: Extract Key Metrics
For each city, extract:
- Average monthly salary
- Salary distribution range (e.g. 60.2% of positions in ¥6-15K)
- Year-over-year change
- Requirements (education, experience, certifications)
- Industry-specific characteristics

### Step 3: Build HTML Report

**Theme selection:**
- **Dark theme** (`#0a0e17` background) — default for complex multi-section reports
- **Light theme** (`#f5f7fa` background) — use when user says "浅色背景" or requests easy printing. Lighter, more approachable for simple comparison reports.

**Template structure:**
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <!-- Google Fonts: Noto Sans SC / PingFang SC -->
  <!-- Chart.js CDN: https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js -->
  <!-- Choose theme: dark (#0a0e17) or light (#f5f7fa) -->
</head>
<body>
  <!-- 1. Header: gradient title + date + meta -->
  <!-- 2. Stat cards (grid-3): key numbers in summary cards -->
  <!-- 3. Bar chart section: Chart.js bar charts for categorical comparison -->
  <!-- 4. Comparison bar rows: horizontal percentage-width bars for total cost comparison -->
  <!-- 5. Detail tables: structured data per category -->
  <!-- 6. Information boxes: green(positive)/orange(warning)/red(alert) -->
  <!-- 7. Insights & action recommendations -->
</body>
</html>
```

**Visual Components (reusable patterns):**

A. **Stat cards (grid-3)** — Key summary numbers at the top
```html
<div class="grid-3">
  <div class="card stat-card">
    <div class="stat-number">840</div>
    <div class="stat-label">医院实付（元）</div>
    <div class="info-box">明细解释</div>
  </div>
  ...
</div>
```

B. **Chart.js bar chart** — For categorical data comparison (e.g. prices across channels)
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<div class="chart-container" style="height:300px;">
  <canvas id="chartXxx"></canvas>
</div>
<script>
new Chart(document.getElementById('chartXxx'), {
  type: 'bar',
  data: {
    labels: ['医院', '京东', '淘宝', '国产'],
    datasets: [{
      label: '单片价格（元）',
      data: [20, 3.4, 1.8, 1.2],
      backgroundColor: ['#e17055', '#fdcb6e', '#00b894', '#74b9ff'],
      borderRadius: 4, barThickness: 40,
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, grid: { color: '#f0f2f5' } },
      x: { grid: { display: false } } }
  }
});
</script>
```

C. **Comparison bar rows** — For total-cost comparison (one bar per option)
```html
<div class="comp-row">
  <div class="comp-label">🏥 医院</div>
  <div class="comp-bar-wrap">
    <div class="comp-bar hospital" style="width:100%;">840 元</div>
  </div>
</div>
<div class="comp-row">
  <div class="comp-label">🛒 淘宝</div>
  <div class="comp-bar-wrap">
    <div class="comp-bar online" style="width:20%;">~170 元</div>
  </div>
</div>
```

D. **Info boxes** — Key alerts/suggestions
```html
<div class="info-box green"> ← or .orange / .red
  <strong>💡 建议</strong>：文字内容...
</div>
```

**Light theme CSS variables:**
```css
body { background: #f5f7fa; color: #2d3436; }
.card { background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #eef1f5; }
.card-header { border-bottom: 2px solid #f0f2f5; }
.info-box { background: #f8f9fd; border-left: 4px solid #667eea; }
.stat-number { color: #667eea; }
.highlight { color: #e17055; }
.comp-bar.hospital { background: linear-gradient(90deg, #e17055, #d63031); }
.comp-bar.online { background: linear-gradient(90deg, #00b894, #00cec9); }
```

**Dark theme CSS variables (existing):**
```css
body { background: #0a0e17; color: #e0e0e0; }
.card { background: linear-gradient(135deg, #111827, #1a2332); }
table th { background: #0d1520; color: #f0c040; }
```

### Step 4: Open in Browser

```bash
xdg-open "/home/andymao/temp-picture/报告标题.html"
```

### Step 5: Save to Knowledge Base

After the user approves, save structured data as a markdown note:

1. Determine the right category directory under `~/knowledge/` (e.g. `03_RESOURCES/宠物医疗/`, `03_RESOURCES/市场调研/`, `知识/国际/`)
2. Write a structured markdown note with YAML frontmatter (tags, created date), data tables, and wikilinks to related notes
3. Run `cd ~/knowledge && enzyme refresh` to update the semantic index

## Output

- **HTML file**: Saved to `/home/andymao/temp-picture/<标题>.html`
- **Browser**: Automatically opened via `xdg-open` or `google-chrome --new-window --no-sandbox`
- **Optional**: PNG screenshot via Chromium headless for sharing
- **Knowledge base**: Structured .md note in `~/knowledge/` (if user approves)

## Pitfalls (Market Comparison Reports)

1. **Do NOT query all regions in one search call** — each city needs its own search for meaningful data.
2. **职友集 (jobui.com) data is the most structured** — look for percentage distributions like "70.3%岗位拿¥8-15K".
3. **Employment data may conflict between platforms** — when sources disagree, note both and pick the most authoritative (jobui > liepin > zhipin).
4. **HTML file paths must be absolute** when using `xdg-open` or `google-chrome`.
5. **Google Fonts requires internet** — verify the machine can reach fonts.googleapis.com, or fall back to system fonts (e.g. `-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei'`).
6. **Chart.js CDN requires internet** — if offline, fall back to pure CSS bar charts instead of Chart.js bars.
7. **Do NOT hardcode salary numbers** — they must come from actual search results.
8. **For comparison tables, use `<table>` with left-aligned labels** — this is the user's preferred format.
9. **Light theme should be default for simple price/cost comparison reports** — reserve dark theme for complex multi-section deep-dive reports.

---

## Alternate Workflow C: WeChat/Telegram Summary (absorbed from research-to-wechat)

For lightweight research that doesn't need an HTML dashboard — send a structured Chinese summary directly to WeChat or Telegram.

### Workflow

**1. Multi-source search** — Chinese + English parallel:
```python
web_search(query="关键词", limit=5)
web_search(query="site:zhihu.com <主题>")  # 中文社区深度讨论
web_extract(urls=["最有价值的链接"])
```

**2. Format as structured summary:**
```
📡 / 📊 标题
━━━━━━━━━━━━━━━━━━━
一、板块标题
━━━━━━━━━━━━━━━━━━━
内容要点，清晰分段

┌──────────────┬──────────────┐
│ 表格内容      │ 用于对比     │
└──────────────┴──────────────┘
```

Format rules: Chinese simplified, emoji section markers, `━━━` dividers, tables and numbered lists, ~3000-5000 chars for WeChat readability.

**3. Send to platform:**
```python
send_message(message="...内容...", target="weixin")    # WeChat
send_message(message="...内容...", target="telegram")  # Telegram
```

Use `MEDIA:/path/to/image.png` prefix to send images as native attachments.

### News Hotspot Query

For daily news, use multi-source cross-query:
```python
web_search(query="今日热点新闻 YYYY年M月D日", limit=8)
web_search(query="today breaking news June D YYYY", limit=5)
web_search(query="微博热搜 今日热点 YYYY年M月D日")
```

Format with emoji categories: 🌍国际 / 🇨🇳财经 / 💻科技 / 🎬娱乐 / 🔥热搜. One-sentence summaries per item, max ~2500 chars.

### Paywalled News Strategy

For paywalled sites (NYT, WSJ, FT):
1. **RSS** (most reliable): `rss.nytimes.com/services/xml/rss/nyt/HomePage.xml`
2. **Archive/mirror**: pressreader.com, web.archive.org
3. **Social media aggregation**: X.com search `site:nytimes.com today`
4. **Free sources**: UN News (`news.un.org/en`) — no restrictions

See `references/paywalled-news-rss-feeds.md` and `references/unbiased-news-sources.md`.

### Platform Notes

- WeChat rate limit: iLink bot has rate limit — wait 15-30s between messages
- Telegram supports Markdown, longer messages (4096+ chars)
- `MEDIA:` prefix works on Telegram/WeChat/Discord as native image attachment

### Domain Investigation (File Import)

When studying files in a directory for knowledge base import:
- **XMind**: parse with `zipfile.ZipFile` → extract `content.xml`/`content.json`
- **Draw.io**: base64 decode → zlib decompress → XML parse
- **Visio**: `libreoffice --headless --convert-to pdf` → `pdftotext`
- **Word**: `pandoc <file>.docx -t markdown`
- **pcap**: Python for structured decoding
- **ZIP**: `unzip -O gbk` for Chinese encoding

See `references/domain-investigation-reference.md` for full parsing pipelines.

---

## Alternate Workflow B: Country / Geopolitical Situation Dashboard

Use this variant when the user asks for a **country-level political, economic, and humanitarian analysis** (e.g. "搜索整理苏丹当前政治经济状况" or "国际热点地区分析"). The data sources and chart layout differ from market comparisons.

### Step 1: Multi-Source International Research

Search across diverse categories in parallel — political, economic, humanitarian, and timeline. Use `web_search_plus` with `mode='research'` for broader coverage:

```python
# Run these in parallel via delegate_task or execute_code:
searches = [
  # Political / conflict
  f"Sudan civil war 2025 2026 SAF RSF conflict status",
  # Economic
  f"Sudan economy GDP inflation 2025 2026 crisis",
  # Humanitarian
  f"Sudan humanitarian crisis displacement hunger 2025 2026",
  # Wikipedia / background
  f"Wikipedia Sudan politics government",
  # Chinese sources (for CN-language user)
  f"苏丹 政治 经济 2025 2026 战乱",
]
```

**Key data sources (geopolitical, in priority order):**
- **BTI Transformation Index** (bti-project.org) — comprehensive political AND economic transformation scores (1-10), ranks out of 137 countries
- **African Development Bank / IMF WEO** (imf.org) — GDP growth, inflation, fiscal balance, current account forecasts
- **CFR Global Conflict Tracker** (cfr.org) — conflict timeline, actors, regional spillover
- **UN OCHA / UNHCR** (unocha.org, data.unhcr.org) — displacement numbers, food insecurity, humanitarian needs
- **Wikipedia** (en.wikipedia.org) — country background, demographics, government structure
- **World Economics** (worldeconomics.com) — GDP PPP estimates with informal economy adjustment
- **AI Jazeera / BBC / Reuters** — current reporting on conflict developments
- **联合国新闻 / 新华网** — Chinese-language UN and Xinhua coverage for CN user context

### Step 2: Extract Key Metrics

Extract these data categories:

| Category | Key Metrics |
|----------|------------|
| Conflict | Duration, parties, casualties, territorial control % |
| Displacement | IDPs, refugees, total displaced |
| Humanitarian | People in need, food insecurity, famine zones, health/education collapse |
| Economic | GDP (nominal & PPP), GDP growth, inflation, fiscal deficit, gold production |
| Rankings | BTI scores, governance indexes, global rankings |

### Step 3: Build HTML Dashboard

**Always use dark theme** (`#0a0e17` background) for geopolitical dashboards — it gives the serious/authoritative tone these reports need.

**Dashboard template structure (distinct from market reports):**

```
┌──────────────────────────────────────────────┐
│        HERO HEADER                          │
│  Gradient gold title + date badge           │
├──────────────────────────────────────────────┤
│        STAT CARDS ROW (grid-6)              │
│  6 key numbers in danger/warn/info colors   │
├──────────────────────────────────────────────┤
│        TIMELINE (left-aligned)               │
│  Chronological event sequence with dots     │
├──────┬───────────────────────────────────────┤
│CHART │ CHART                                │
│ ROW  │ ROW (2-column Chart.js grid)         │
├──────┴───────────────────────────────────────┤
│        INFO CARDS GRID (4-column)            │
│  Warring parties / Politics / Humanitarian   │
│  Regional spillover — with color tags       │
├──────┬───────────────────────────────────────┤
│CHART │ CHART (economic data)                │
│ ROW  │ ROW                                   │
├──────┴───────────────────────────────────────┤
│        INFO CARDS GRID (economy details)     │
├──────────────────────────────────────────────┤
│        BTI RADAR CHART (full-width)          │
├──────────────────────────────────────────────┤
│        FOOTER with sources                   │
└──────────────────────────────────────────────┘
```

**Chart types used in geopolitical dashboards:**

| Chart | Type | Data |
|-------|------|------|
| Displacement | Bar | IDPs vs refugees vs total |
| Food Insecurity | Bar | Time series (2023→2026p) |
| GDP Growth | Line | Multi-year with projections |
| Inflation | Line | Multi-year trajectory |
| Fiscal Balance | Bar | Annual deficit % of GDP |
| GDP PPP | Bar | Current vs projected |
| BTI Scores | Radar | 6-8 governance dimensions |

**Color palette for geopolitical charts:**
```css
/* Dark theme constants */
:root {
  --bg: #0a0e17;
  --card-bg: #111b28;
  --border: #1a2840;
  --gold: #c9a23c;
  --gold-light: #f5d77b;
  --red: #ff6b6b;
  --orange: #ffa94d;
  --green: #69db7c;
  --blue: #74c0fc;
  --text: #e0e6ed;
  --text-muted: #7a8a9a;
}
```

**Chrome opening** — use `--no-sandbox` flag if sandbox binary not configured:
```bash
google-chrome --new-window --no-sandbox "/path/to/report.html"
```

### Step 4 (optional): Save to Knowledge Base

Determine the right `~/knowledge/` subdirectory (e.g. `知识/国际/苏丹/`) and write a structured .md note with YAML frontmatter, key data tables, and source links. Run `enzyme refresh` after.

## Pitfalls (country dashboard specific)

1. **Search in parallel** — independent data categories (politics, economy, humanitarian) can be searched simultaneously via execute_code or delegate_task.
2. **Wikipedia is blocked by web_extract** — use web_search_plus + web_extract from multiple mirror sources instead; the snippet data is usually sufficient.
3. **BTI reports are dense** — focus on the Executive Summary, Key Indicators table (Status Index, Governance Index, Political/Economic Transformation), and the per-indicator scores.
4. **Data may conflict between sources** — when IMF says 0.6% GDP growth and BMI says 1.9%, note both and state which source each comes from.
5. **Gold/commodity data** is the most current economic indicator in conflict zones — if official GDP data is stale, gold production figures may be the freshest signal.
6. **Chinese sources (新华/联合国新闻)** are useful for CN-user-facing reports but often lag 2-4 weeks behind English sources.
7. **Chrome sandbox** — if `--no-sandbox` is needed, open with that flag; to fix permanently: `sudo chmod 4755 /path/to/chrome-sandbox`.

## Related Files

- `references/foreign-trade-salary-data.md` — detailed salary data from the foreign trade comparison session
- `references/pet-hospital-cost-comparison.md` — pet hospital cost comparison data
- `references/country-dashboard-structure.md` — HTML structure pattern for geopolitical/country situation dashboards (timeline format, radar/line chart configs, info-card layout, stat card grid)
- `references/matplotlib-chinese-font-setup.md` — Chinese font setup for matplotlib on Ubuntu (Noto Sans CJK SC TTC registration, font cache clearing)
