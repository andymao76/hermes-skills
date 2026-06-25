# Informational HTML Infographic Creation

When researching a non-technical topic (health, pet care, guides, etc.) and presenting results as a visual HTML chart:

## Workflow

1. **Research the topic** via web_search / web_extract
2. **Create a self-contained HTML file** with inline CSS (no JS, no external deps except Google Fonts)
3. **Design system for informational charts:**
   - Dark theme (`background: #0f172a`, text `#e2e8f0`)
   - Noto Sans SC for Chinese text from Google Fonts
   - CSS Grid for card layouts (`.grid-2`, `.grid-3`, `.grid-4`)
   - Cards with `rgba(30,41,59,0.6)` background + `rgba(148,163,184,0.12)` border
   - Color-coded tags/sections for different severity or stages
   - Timelines with `::before` pseudo-elements for vertical progress bars
   - Tables with hover effects for data comparison
   - Stat cards with large numbers (`.stat-number`) and color coding
4. **Save to HTML file** (e.g. `~/topic-guide.html`)
5. **Open in Chrome:** `xdg-open ~/topic-guide.html`
6. **Save structured knowledge** to `~/knowledge/` as a markdown file

## Example Components

### Gradient Header
```css
.header {
  background: linear-gradient(135deg, rgba(244,63,94,0.08), rgba(139,92,246,0.08));
  border: 1px solid rgba(244,63,94,0.2);
  border-radius: 16px;
}
.header h1 {
  background: linear-gradient(135deg, #f43f5e, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Stat Cards
```html
<div class="card" style="text-align:center;">
  <div class="stat-number cyan">50%+</div>
  <div class="stat-label">6岁以上患病率</div>
</div>
```
Colors: `cyan` (#22d3ee), `emerald` (#34d399), `amber` (#fbbf24), `rose` (#f43f5e).

### Tag Badges
- Severity/Stage tags: background at 0.15 opacity with matching border
  ```css
  .tag-stage-b2 { background:rgba(251,191,36,0.15); color:#fbbf24; }
  .tag-stage-c { background:rgba(251,146,60,0.15); color:#fb923c; }
  .tag-stage-d { background:rgba(244,63,94,0.15); color:#f43f5e; }
  ```

### Vertical Timeline
```css
.timeline::before {
  background: linear-gradient(to bottom, #22d3ee, #34d399, #fbbf24, #fb923c, #f43f5e);
}
```
Each timeline item has its own colored dot (nth-child selector).

### Checklist Items
- `✓ ` prefix (green) for ✅ items
- `⚠ ` prefix (amber) for warnings
- `✗ ` prefix (rose) for ❌ items

## When to Use vs architecture-diagram
- **Use architecture-diagram** for: software architecture, cloud infra, network topology, system design (SVG-based)
- **Use this HTML infographic approach** for: health/medical guides, comparison charts, educational content, policy/guideline summaries, anything with cards/tables rather than boxes-and-arrows

## Output
- Single self-contained `.html` file in `~/`
- Knowledge entry saved to `~/knowledge/` under appropriate category
- Open in Chrome immediately after creation
