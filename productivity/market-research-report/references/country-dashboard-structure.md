# Country / Geopolitical Dashboard — HTML Structure Pattern

Generated from the Sudan 2026 session. Use this as a reference when building a country-situation research dashboard.

## Template Architecture

```
hero-header (gradient title + date badge)
  └── stat-cards-row (6 cards, color-coded by severity)
  └── timeline (left-vertical, chronological events)
  └── chart-grid (2-column)
      ├── displacement bar chart
      └── food insecurity bar chart
  └── info-card-grid (4-column)
      ├── warring parties (with .tag classes)
      ├── political landscape
      ├── humanitarian disaster
      └── regional spillover
  └── chart-grid (2-column, economic)
      ├── GDP growth line chart
      ├── inflation line chart
      ├── fiscal deficit bar chart
      └── GDP PPP bar chart
  └── info-card-grid (economy details)
      ├── gold production
      ├── macro indicators
      └── industry structure
  └── radar chart (full-width, BTI scores)
  └── footer (sources)
```

## Key HTML Components

### 1. Stat Card
```html
<div class="stat-card danger">  <!-- .danger / .warn / .info / .ok -->
  <div class="stat-icon">⚔️</div>
  <div class="stat-value">3+ 年</div>
  <div class="stat-label">内战持续</div>
</div>
```

### 2. Timeline Item
```html
<div class="timeline-item">
  <div class="tl-date">2023年4月15日</div>
  <div class="tl-text">描述文字...</div>
</div>
```

### 3. Info Card with Tags
```html
<div class="info-card">
  <h4>⚔️ 交战方</h4>
  <ul>
    <li><span class="tag green">SAF</span> 苏丹武装部队...</li>
    <li><span class="tag red">RSF</span> 快速支援部队...</li>
  </ul>
</div>
```
Tag colors: .tag.red, .tag.orange, .tag.blue, .tag.green, .tag.yellow

### 4. Chart.js Config Patterns

**Bar chart** (displacement, hunger, fiscal):
```js
new Chart(canvas, {
  type: 'bar',
  data: {
    labels: ['A', 'B', 'C'],
    datasets: [{ data: [v1, v2, v3], backgroundColor: [cOrange, cRed, cBlue] }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, grid: { color: '#1a2840' } } }
  }
});
```

**Line chart** (GDP growth, inflation — time series):
```js
new Chart(canvas, {
  type: 'line',
  data: {
    labels: ['2022', '2023', '2024', '2025(e)', '2026(p)'],
    datasets: [{
      data: [-1.2, -12.0, -4.0, 0.6, 1.3],
      borderColor: '#c9a23c',
      backgroundColor: '#c9a23c33',
      fill: true, tension: 0.3, pointRadius: 5
    }]
  }
});
```

**Radar chart** (BTI / governance scores):
```js
new Chart(canvas, {
  type: 'radar',
  data: {
    labels: ['政治转型', '经济转型', '法治', '行政能力'],
    datasets: [{
      data: [1.63, 1.29, 1.2, 1.5],
      borderColor: '#c9a23c',
      backgroundColor: '#c9a23c33',
      pointBackgroundColor: '#c9a23c'
    }]
  },
  options: {
    scales: { r: { min: 0, max: 10, grid: { color: '#1a2840' } } }
  }
});
```

## Color Palette Constants
```js
const cGold = '#c9a23c';
const cGold2 = '#f5d77b';
const cRed = '#ff6b6b';
const cOrange = '#ffa94d';
const cGreen = '#69db7c';
const cBlue = '#74c0fc';
const cGrid = '#1a2840';
const cBg = '#111b28';
```

## Data Sources Table Pattern

Include a footer with authoritative sources:
```html
<div class="footer">
  数据来源: BTI Transformation Index 2026 · African Development Bank · IMF WEO ·
  CFR Global Conflict Tracker · UN OCHA · UNHCR · World Economics · Wikipedia
</div>
```

## Sudan 2026 Session Reference

- **File produced:** `/home/andymao/sudan-report.html` (23KB, standalone HTML)
- **Chart.js version used:** 4.4.1
- **Chrome launch:** `google-chrome --new-window --no-sandbox <file>` (sandbox fix: `sudo chmod 4755 /path/to/chrome-sandbox`)
- **Data sources consulted:** 30+ sources across 6 searches using web_search_plus with mode='research'
- **Note-to-KB path:** `~/knowledge/知识/国际/` if user later approves
