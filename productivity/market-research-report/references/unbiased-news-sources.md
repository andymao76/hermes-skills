# 可靠无限制新闻源（无 paywall / 反爬限制）

以下新闻站点可用 web_extract 直接抓取，无需 RSS 或付费订阅。

## 国际新闻

| 来源 | URL | 说明 |
|------|-----|------|
| **UN News** | `news.un.org/en` | 联合国官方新闻，无任何限制，内容权威且全面 |
| **BBC News** | `bbc.com/news` | 免费，反爬较宽松 |
| **The Guardian** | `theguardian.com` | 免费，无 paywall |
| **Reuters** | `reuters.com` | 免费，RSS 可用 |
| **Associated Press** | `apnews.com` | 免费，反爬少 |
| **Al Jazeera** | `aljazeera.com` | 免费 |
| **France 24** | `france24.com` | 免费 |
| **DW (Deutsche Welle)** | `dw.com` | 免费，多语种 |

## 有 paywall 但 RSS 可用的

| 来源 | RSS Feed | 说明 |
|------|----------|------|
| **NYT** | `rss.nytimes.com/services/xml/rss/nyt/HomePage.xml` | web_extract/browser 全封，RSS 可 |
| **WSJ** | `feeds.wsj.com/xml/rss/3_7085.xml` | 同上 |
| **Washington Post** | `feeds.washingtonpost.com/rss/world` | 同上 |
| **Financial Times** | `www.ft.com/world?format=rss` | 同上 |

## UN News 使用特点

- **web_extract 完全可用** — 返回完整结构化内容，图文清晰
- **无需任何认证**
- **覆盖全球热点**：中东、乌克兰、非洲、气候、人权等
- **内容深度**：不仅新闻摘要，还有专题报道、访谈、背景分析
- **多语种**：阿拉伯语、中文、英语、法语、俄语、西班牙语等
- **适合作为国际新闻基准源**，与其他付费源交叉验证

典型抓取方式：
```python
web_extract(urls=["https://news.un.org/en"])
web_extract(urls=["https://news.un.org/en/news"])  # 完整列表页
```
