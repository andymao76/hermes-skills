# Wikipedia API for Cron Job Content

## Why Not web_extract

The `web_extract` tool blocks Wikipedia URLs with `"Blocked: URL targets a private or internal network address"`. The `browser_navigate` tool also times out on Wikipedia. Use the **Wikipedia API directly** via curl or Python urllib.

## API Endpoints

### Featured Article

```bash
curl -s "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles=Wikipedia:Today%27s_featured_article/June_8,_2026&format=json"
```

Date format: `Month_DD,_YYYY` (e.g. `June_8,_2026`). The featured article for today is at this URL.

### On This Day (Events, Births, Deaths)

```bash
# Section 2 = Events
curl -s "https://en.wikipedia.org/w/api.php?action=parse&page=June_8&prop=text&section=2&format=json"

# Section 3 = Births
curl -s "https://en.wikipedia.org/w/api.php?action=parse&page=June_8&prop=text&section=3&format=json"

# Section 4 = Deaths
curl -s "https://en.wikipedia.org/w/api.php?action=parse&page=June_8&prop=text&section=4&format=json"
```

### Chinese Wikipedia

```bash
# 优良条目
curl -s "https://zh.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles=Wikipedia:%E4%BC%98%E8%89%AF%E6%9D%A1%E7%9B%AE/2026%E5%B9%B46%E6%9C%888%E6%97%A5&format=json"

# 历史上的今天（6月8日页面）
curl -s "https://zh.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&titles=6%E6%9C%888%E6%97%A5&format=json"
```

## Processing with Python

```python
import json, urllib.request, re

def fetch_wikipedia_section(page: str, section: int = 2) -> list:
    """Fetch list items from a Wikipedia date page section."""
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={page}&prop=text&section={section}&format=json"
    with urllib.request.urlopen(url, timeout=10) as resp:
        d = json.loads(resp.read())
    html = d.get('parse', {}).get('text', {}).get('*', '')
    items = re.findall(r'<li>(.*?)</li>', html)
    result = []
    for item in items[:15]:
        text = re.sub(r'<[^>]+>', '', item)
        # Clean HTML entities
        text = text.replace('&#8211;', '—').replace('&#91;', '[').replace('&#93;', ']')
        result.append(text)
    return result

def fetch_featured_article(date_str: str) -> str:
    """Fetch today's featured article text."""
    title = f"Wikipedia:Today%27s_featured_article/{date_str}"
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title}&format=json"
    with urllib.request.urlopen(url, timeout=10) as resp:
        d = json.loads(resp.read())
    for pid, page in d.get('query', {}).get('pages', {}).items():
        if pid != '-1':
            return page.get('extract', '')
    return ""
```

## URL Encoding

Wikipedia page titles with special characters need URL encoding:
- `'` (apostrophe) → `%27` (e.g. `Today's` → `Today%27s`)
- Spaces → `_` or `%20`
- Chinese characters → percent-encoded UTF-8 (Python's `urllib.parse.quote()` handles this)

## Rate Limits

Wikipedia API has aggressive rate limiting. If you get HTTP 429, wait at least 5 seconds before retrying. For cron jobs, a single API call per section is sufficient — avoid loops.

## HTML Cleanup Needed

The `parse` action returns HTML. Common entities to clean:
- `&#8211;` → `—` (em dash)
- `&#91;n&#93;` → `[n]` (reference markers)
- `<b>...</b>` → bold markers
- `<a href="...">text</a>` → keep text, strip link

## Cron Job Delivery Format

```markdown
📖 维基百科今日精选 — 2026年6月8日

🌟 特色条目：[Title]
[1-2 paragraph summary]

📅 历史上的今天（6月8日）
• 218年 — ...
• 452年 — ...

👤 今日出生
• ...

⚰️ 今日逝世
• ...

📡 来源：维基百科
```

Keep the delivery concise (aim for under 2000 chars for Telegram/Discord/WeChat compatibility).
